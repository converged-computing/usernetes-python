import time

from python_on_whales import DockerClient

join_template = """
#!/bin/bash
set -eux -o pipefail
echo "$(HOST_IP)  $(NODE_NAME)" >/etc/hosts.u7s
echo "cat /etc/hosts.u7s" >> /etc/hosts
"""


class UsernetesRunner:
    """
    A Usernetes Runner will run usernetes via docker compose.

    We do this easily by using the docker python SDK. Note that
    we don't have an equivalent to "docker compose render"
    """

    def __init__(self, compose_file=None, container_engine="docker", workdir=None, wait_seconds=5):
        """
        Create a new transformer backend, accepting any options type.

        Validation of transformers is done by the registry
        """
        self.compose = ComposeConfig(container_engine)
        self.compose_file = compose_file or "docker-compose.yaml"
        self.docker = DockerClient(compose_files=[self.compose_file])
        self.workdir = workdir
        # Break buffer time between running commands
        self.sleep = wait_seconds

    def start_control_plane(self):
        """
        Start the usernetes control plane.

        Note that this would currently start with the working directory as the
        one that this is installed to. This is not ideal, but just for development.
        We eventually want a throw-away clone, or clone to a user home or similar.
        """
        self.up()
        # Note this was originally 10
        time.sleep(self.sleep)
        self.kubeadm_init()
        time.sleep(self.sleep)
        self.install_flannel()
        print("TODO: need to export kubeconfig somehow, have function below return path")
        # export KUBECONFIG=/home/ubuntu/usernetes/kubeconfig
        import IPython

        IPython.embed()
        self.kubeconfig()
        self.join_command()
        # Probably don't want to do that
        # echo "export KUBECONFIG=/home/ubuntu/usernetes/kubeconfig" >> ~/.bashrc

    def start_worker(self):
        """
        Start a usernetes worker (kubelet)
        """
        self.up()
        # Note this was originally 10
        time.sleep(self.sleep)
        self.kubeadm_join()

    def kubeconfig(self):
        """
        Generate kubeconfig locally
        """
        conf = self.execute(
            ["sed", "-e", '"s/$(NODE_NAME)/127.0.0.1/g"', "/etc/kubernetes/admin.conf"]
        )
        # TODO save to kubeconfig
        print(conf)
        import IPython

        IPython.embed()
        print("Run the following:")
        print("  export KUBECONFIG=$(pwd)/kubeconfig")

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
        out = self.execute(["kubeadm", "token", "create", "--print-join-command"])
        print(out)
        print("Parse out and add to last line of template")
        import IPython

        IPython.embed()
        # Assumes running from where called from
        utils.write_file(join_template, "join-command", executable=True)

    def kubeadm_init(self):
        """
        kubeadm init
        """
        print("Test kubeadm init")
        import IPython

        IPython.embed()
        # $(NODE_SHELL) sh -euc "envsubst </usernetes/kubeadm-config.yaml >/tmp/kubeadm-config.yaml"
        self.execute(
            ["sh", "-euc", '"envsubst </usernetes/kubeadm-config.yaml >/tmp/kubeadm-config.yaml"']
        )
        # $(NODE_SHELL) kubeadm init --config /tmp/kubeadm-config.yaml --skip-token-print
        self.execute(
            ["kubeadm", "init", "--config", "/tmp/kubeadm-config.yaml", "--skip-token-print"]
        )
        self.sync_external_ip()

    def sync_external_ip(self):
        self.execute(["bash", "/usernetes/Makefile.d/sync-external-ip.sh"])

    def kubeadm_join(self):
        """
        kubeadm join
        """
        print("Test kubeadm join")
        import IPython

        IPython.embed()
        self.execute(
            ["sh", "-euc", '"envsubst </usernetes/kubeadm-config.yaml >/tmp/kubeadm-config.yaml"']
        )
        # This should be followed by sync-external-ip on the control plane
        self.execute(["bash", "/usernetes/join-command"])

    def kubeadm_reset(self):
        """
        kubeadm reset
        """
        self.execute(["kubeadm", "reset", "--force"])

    def install_flannel(self):
        """
        Install flannel networking fabric
        """
        self.execute(
            [
                "kubectl",
                "apply",
                "-f",
                "https://github.com/flannel-io/flannel/releases/download/v0.25.5/kube-flannel.yml",
            ]
        )

    def bootstrap(self):
        """
        @echo '# Bootstrap a cluster'
            @echo 'make up'
            @echo 'make kubeadm-init'
        @echo 'make install-flannel'
        """
        self.up()
        self.kubeadm_init()
        self.install_flannel()

    def kubectl(self):
        """
            @echo '# Enable kubectl'
            @echo 'make kubeconfig'
            @echo 'export KUBECONFIG=$$(pwd)/kubeconfig'
        @echo 'kubectl get pods -A'
        """
        self.kubeconfig()
        path = os.path.join(os.getcwd(), "kubeconfig")
        utils.run_command(["kubectl", "get", "pods", "-A"], envars={"KUBECONFIG": path})

    def multi_host(self):
        """
            @echo '# Multi-host'
            @echo 'make join-command'
            @echo 'scp join-command another-host:~/usernetes'
            @echo 'ssh another-host make -C ~/usernetes up kubeadm-join'
            @echo 'make sync-external-ip'

        Note that flux can be used for this step.
        """
        pass

    def debug(self):
        """
            @echo '# Debug'
            @echo 'make logs'
        @echo 'make shell'
            @echo 'make kubeadm-reset'
            @echo 'make down-v'
        @echo 'kubectl taint nodes --all node-role.kubernetes.io/control-plane-'
        """
        pass

    def up(self):
        """
        Run docker-compose up, always with detached.
        """
        self.compose.check()
        with utils.workdir(self.workdir):
            # $(COMPOSE) up --build -d
            self.docker.compose.up(build=True, detach=True)

    def down(self, verbose=False):
        """
        Run docker-compose up, always with detached.
        """
        with utils.workdir(self.workdir):
            self.docker.compose.down(quiet=not verbose)

    def shell(self):
        """
        Get logs from journalctl
        """
        self.execute(["journalctl", "--follow", '--since="1 day ago"'])

    def shell(self):
        """
        Execute a shell to the container.
        """
        self.execute(["bash"])

    def execute(self, command):
        """
        Get an interactive node shell
        """
        with utils.workdir(self.workdir):
            return self.docker.compose.execute(
                self.compose.node_service_name, command, detach=False, envs=self.compose.envars
            )
