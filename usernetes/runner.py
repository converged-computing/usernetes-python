import os
import shutil
import time
from pathlib import Path

import usernetes.utils as utils
from usernetes.config import ComposeConfig
from usernetes.logger import logger


class UsernetesRunner:
    """
    A Usernetes Runner will run usernetes via docker compose.

    We do this easily by using the docker python SDK. Note that
    we don't have an equivalent to "docker compose render"
    """

    def __init__(
        self,
        container_engine="docker",
        workdir=None,
        wait_seconds=5,
        compose_file="docker-compose.yaml",
    ):
        """
        Create a new transformer backend, accepting any options type.

        Validation of transformers is done by the registry
        """
        # Set and validate the working directory
        self.compose_file = compose_file
        self.set_workdir(workdir)
        self.compose = ComposeConfig(container_engine)
        # Break buffer time between running commands
        self.sleep = wait_seconds
        # Prepare a filesystem cache for workers to indicate readiness
        self.prepare_worker_cache()

    @property
    def usernetes_uid(self):
        """
        The uid for different assets (network, node) can be assembled
        from the basename of the working directory. E.g.,

           node: usernetes-7fnptyat-node
        network: usernetes-7fnptyat_default
        """
        return os.path.basename(self.workdir)

    def set_workdir(self, workdir):
        """
        Set and validate that the working directory exists.

        It must be populated with a usernetes clone or release, and have
        docker-compose.yaml.
        """
        self.workdir = workdir or os.getcwd()
        if not os.path.exists(self.workdir):
            raise ValueError(f"Working directory with usernetes {self.workdir} does not exist.")

        # This assumes usernetes has a docker-compose.yaml
        compose_file = os.path.join(self.workdir, self.compose_file)
        if not os.path.exists(compose_file):
            raise ValueError(f"{self.compose_file} does not exist in {self.workdir}.")

    def prepare_worker_cache(self):
        """
        This can be improved upon, but we need to sync external ips on the control
        plane after workers are ready. To do that, we prepare a directory where
        they will write their hostnames. The lead thus needs to know how many workers
        to expect. This should be created by the control plane, brought up first.
        """
        self.worker_cache = os.path.join(self.workdir, "worker-ready-cache")
        if not os.path.exists(self.worker_cache):
            logger.debug(f"Creating worker cache {self.worker_cache}")
            os.makedirs(self.worker_cache)

    def start_control_plane(self, worker_count, serial=False):
        """
        Start the usernetes control plane.

        This currently starts with the working directory as specified by
        the user. In practice, it makes sense for an admin to clone usernetes
        and stage this in a temporary location. The worker count is needed to
        determine when all workers are ready for a final sync.
        """
        self.up()
        # Note this was originally 10
        time.sleep(self.sleep)
        self.kubeadm_init()
        time.sleep(self.sleep)
        self.install_flannel()

        # Generate <self.workdir>/kubeconfig and join-command
        # As soon as this is generated, workers will start preparing
        self.ensure_kubeconfig()
        self.join_command()

        # We don't print anything because it's printed in the interface for the user
        # Serial mode usually means we need to manually move the join-command before
        # we issue the final sync to the external ips.
        if serial:
            logger.debug("Running in serial mode, returning early")
            return

        # Next, we need the workers to ready, and we sync the external IP once more
        self.wait_for_workers(worker_count)
        self.sync_external_ip()

    def clean(self, cache_only=True, keep_nodes=False):
        """
        Clean removes the usernetes root and all assets, unless cache only is
        set to true, in which case we just remove the worker cache. It also
        stops and removes the nodes, assuming we want to re-create them later.
        """
        # You can't remove everything but ask to keep nodes
        if not cache_only and keep_nodes:
            raise ValueError("To keep nodes, you must not delete the working directory.")
        if os.path.exists(self.worker_cache):
            logger.debug(f"Cleaning up worker cache {self.worker_cache}")
            shutil.rmtree(self.worker_cache)
        if cache_only:
            return
        if os.path.exists(self.workdir):
            logger.debug(f"Cleaning up usernetes root {self.workdir}")
            shutil.rmtree(self.workdir)
        if keep_nodes:
            return

        # Final cleanup of node (stop and remove) and network.
        self.cleanup_node()

    def cleanup_node(self):
        """
        Cleanup the node, including stop/remove of the image and network.
        """
        self.stop()
        # This is rm, not rmi
        self.remove()
        self.remove_network()

    def wait_for_workers(self, worker_count):
        """
        Wait for workers to indicate ready by writing their hostname
        """
        while True:
            print(f"Waiting for {worker_count} workers to be ready...")
            time.sleep(self.sleep)
            count = len(os.listdir(self.worker_cache))

            # The workers are ready, break from waiting
            if count == worker_count:
                print(f"⭐ Workers (N={worker_count}) are ready!")
                time.sleep(self.sleep)
                break

    def wait_for_control_plane(self):
        """
        Wait for the control plane to be ready.

        This is indicated by the presence of the join-command in the usernetes
        root. It is the responsibility of the executor / control plane to get it
        there. For shared filesystems, this should not be an issue.
        """
        join_command = os.path.join(self.workdir, "join-command")
        while True:
            print(f"Waiting for join-command in {self.workdir}...")
            time.sleep(self.sleep)
            if os.path.exists(join_command):
                print(f"⭐ Found join-command in {self.workdir}!")
                return

    def start_worker(self):
        """
        Start a usernetes worker (kubelet)
        """
        self.up()
        self.wait_for_control_plane()
        self.kubeadm_join()

        # Indicate we are ready!
        ready_path = os.path.join(
            self.worker_cache, f"{self.compose.usernetes_node_name}.ready.txt"
        )
        Path(ready_path).touch()

    @property
    def kubeconfig(self):
        """
        Path to the kubeconfig in the working directory
        """
        kubeconfig = os.path.join(self.workdir, "kubeconfig")
        os.environ["KUBECONFIG"] = kubeconfig
        os.putenv("KUBECONFIG", kubeconfig)
        return kubeconfig

    def ensure_kubeconfig(self):
        """
        Generate kubeconfig locally
        """
        if os.path.exists(self.kubeconfig):
            return
        # This will generate "kubeconfig" in self.workdir
        self.run_command(["make", "kubeconfig"])

    def join_command(self):
        """
        Generate the join-command (should be run by control plane)

        @echo "# Copy the 'join-command' file to another host, and run the following commands:"
            @echo "# On the other host (the new worker):"
            @echo "#   make kubeadm-join"
            @echo "# On this host (the control plane):"
            @echo "#   make sync-external-ip"
        """
        # kubeadm token create --print-join-command | tr -d '\r'
        self.run_command(["make", "join-command"])

    def run_command(self, command, do_check=True, success_code=0, quiet=False, allow_fail=False):
        """
        Wrapper to utils.run_command, and assumed in the working directory.

        I was originally re-creating the usernetes logic, but this is easier
        to maintain (less likely to break when the logic changes).
        """
        with utils.workdir(self.workdir):
            logger.debug(" ".join(command))
            result = utils.run_command(command, stream=True, envars=self.envars)

        # Assume we don't need to return the return code
        # can change if needed
        if do_check and result["return_code"] != success_code:
            # Allow to fail
            if not allow_fail:
                command = " ".join(command)
                raise ValueError(f"Issue running {command}: {result['return_code']}")
            msg = f"{command} ({result['return_code']})"
            print("Warning: issue running {msg} but allow fail is true.")
        response = result["message"]
        if response is not None and not quiet:
            print(response)
        return response

    def kubeadm_init(self):
        """
        kubeadm init
        """
        # $(NODE_SHELL) sh -euc "envsubst </usernetes/kubeadm-config.yaml >/tmp/kubeadm-config.yaml"
        # $(NODE_SHELL) kubeadm init --config /tmp/kubeadm-config.yaml --skip-token-print
        self.run_command(["make", "kubeadm-init"])

    def sync_external_ip(self):
        self.run_command(["make", "sync-external-ip"])

    def kubeadm_join(self):
        """
        kubeadm join
        """
        self.run_command(["make", "kubeadm-join"])

    def kubeadm_reset(self):
        """
        kubeadm reset
        """
        self.run_command(["make", "kubeadm-reset"])

    def install_flannel(self):
        """
        Install flannel networking fabric
        """
        self.run_command(["make", "install-flannel"])

    def get_pods(self):
        """
        Get pods with kubectl
        """
        utils.run_command(["kubectl", "get", "pods", "-A"], envars={"KUBECONFIG": self.kubeconfig})

    def debug(self):
        """
            @echo '# Debug'
            @echo 'make logs'
        @echo 'make shell'
            @echo 'make kubeadm-reset'
            @echo 'make down-v'
        @echo 'kubectl taint nodes --all node-role.kubernetes.io/control-plane-'
        """
        self.run_command(["make", "debug"])

    @property
    def envars(self):
        if not hasattr(self, self._envars):
            # Set (and get) needed environment variables
            self._envars = self.compose.set_build_environment()
        return self._envars

    def up(self):
        """
        Run docker-compose up, always with detached.
        """
        with utils.workdir(self.workdir):
            self.compose.check()

            # $(COMPOSE) up --build -d
            self.run_command(["make", "up"])

    def down(self, verbose=True):
        """
        Run docker-compose down.
        """
        if verbose:
            return self.run_command(["make", "down"])
        return self.run_command(["make", "down-v"])

    def stop(self, allow_fail=True):
        """
        Run docker stop - not supported in the Makefile
        """
        node = f"{self.usernetes_uid}-node-1"
        self.run_command(["docker", "stop", node], allow_fail=allow_fail)

    def remove_image(self, allow_fail=True):
        """
        Remove the node image.
        """
        node = f"{self.usernetes_uid}-node-1"
        self.run_command(["docker", "rmi", node], allow_fail=allow_fail)

    def remove_network(self, allow_fail=False):
        """
        Remove the node image.
        """
        network = f"{self.usernetes_uid}_default"
        self.run_command(["docker", "network", "rm", network], allow_fail=allow_fail)

    def remove(self):
        """
        Remove the node, and the network.
        """
        node = f"{self.usernetes_uid}-node"
        self.run_command(["docker", "rm", node])

    def logs(self):
        """
        Get logs from journalctl
        """
        self.run_command(["make", "logs"])

    def shell(self):
        """
        Execute a shell to the container.
        """
        with utils.workdir(self.workdir):
            os.system("make shell")
