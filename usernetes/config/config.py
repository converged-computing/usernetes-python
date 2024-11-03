import socket
import hashlib
import usernetes.utils as utils
from usernetes.logger import logger

here = os.path.dirname(__file__)
root = os.path.dirname(here)
src = os.path.join(root, "src")


class ComposeConfig:
    """
    A compose config will help to prepare for the execution of docker compose!
    """

    def __init__(
        self,
        container_engine=None,
        node_service_name="node",
        container_engine_type="docker",
        compose="compose",
    ):
        self._node_name = None
        self._node_subnet = None
        self.node_service_name = node_service_name
        self.container_engine = container_engine or "docker"
        self.container_engine_type = container_engine_type or "docker"
        self.compose = compose or "compose"
        self.bypass = bypass
        self.validate()

    @property
    def hostname(self):
        return socket.gethostname()

    def check(self):
        """
        Wrapper to check_preflight.
        """
        # Since this is complex, we just wrap the script
        script = os.path.join(src, "Makefile.d", "check-preflight.sh")

        # Ensure to export envars the script needs
        envars = {
            "CONTAINER_ENGINE": self.container_engine,
            "CONTAINER_ENGINE_TYPE": self.container_engine_type,
        }
        result = self.run_command(["/bin/bash", script])
        if result["return_code"] != 0:
            logger.exit("Issue with preflight.")

    @property
    def envars(self):
        """
        Return environment variables for interactive shell and other
        interactions.

        NODE_SHELL := $(COMPOSE) exec \
	    -e U7S_HOST_IP=$(U7S_HOST_IP) \
	    -e U7S_NODE_NAME=$(U7S_NODE_NAME) \
    	-e U7S_NODE_SUBNET=$(U7S_NODE_SUBNET) \
	    -e U7S_NODE_IP=$(U7S_NODE_IP) \
    	$(NODE_SERVICE_NAME)
        """
        return {
            "U7S_HOST_IP": self.usernetes_node_ip,
            "U7S_NODE_NAME": self.usernetes_node_name,
            "U7S_NODE_SUBNET": self.usernetes_node_subnet,
            "U7S_NODE_IP": self.usernetes_node_ip,
        }

    @property
    def node_name(self):
        if self._node_name is not None:
            return self._node_name
        self._node_name = f"u7s-{self.hostname}"
        return self.node_name

    @property
    def node_subnet(self):
        """
        Calculate the node subnet.
        """
        if self._node_subnet is not None:
            return self._node_subnet

        # Take the first two digits of the hexdigest
        hasher = hashlib.sha256()

        # We add a newline to mimic the command line variant
        # and get the same digest - otherwise they are different
        # NODE_SUBNET_ID=$((16#$(echo "${HOSTNAME}" | sha256sum | head -c2)))
        hasher.update((hostname + "\n").encode("utf-8"))
        digest = hasher.hexdigest()

        # Express the prefix in base 16 (e.g., $((16#<prefix>)))
        prefix = int(digest[0:2], 16)
        self._node_subnet = f"10.100.{prefix}.0/24"
        return self.node_subnet

    @property
    def usernetes_host_ip(self):
        """
        U7S_HOST_IP is the IP address of the physical host.
        Accessible from other hosts (convenience function)
        """
        return self.host_ip

    @property
    def usernetes_node_name(self):
        """
        U7S_NODE_NAME is the host name of the Kubernetes node running in Rootless Docker.
        Not accessible from other hosts.
        """
        return self.node_name

    @property
    def usernetes_node_subnet(self):
        """
        U7S_NODE_SUBNET is the subnet of the Kubernetes node running in Rootless Docker.
        Not accessible from other hosts.
        """
        return self.node_subnet

    @property
    def usernetes_node_ip(self):
        """
        # U7S_NODE_IP is the IP address of the Kubernetes node running in Rootless Docker.
        # Not accessible from other hosts.

        $(subset .0/24,.100,$(U7S_NODE_SUBNET))
        """
        return self.node_subnet.replace(".0/24", ".100")

    @property
    def host_ip():
        """
        Gets the host IP address
        """
        return socket.gethostbyname(self.hostname)
