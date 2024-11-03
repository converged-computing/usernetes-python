__version__ = "0.0.0"
AUTHOR = "Vanessa Sochat"
AUTHOR_EMAIL = "vsoch@users.noreply.github.com"
NAME = "usernetes"
PACKAGE_URL = "https://github.com/converged-computing/usernetes-python"
KEYWORDS = "cluster, orchestration, user-space kubernetes, kubernetes, compose"
DESCRIPTION = "Python SDK for user-space Kubernetes 'usernetes'"
LICENSE = "LICENSE"

################################################################################
# Global requirements

INSTALL_REQUIRES = (("python-on-whales", {"min_version": None}),)

TESTS_REQUIRES = (("pytest", {"min_version": "4.6.2"}),)
INSTALL_REQUIRES_ALL = INSTALL_REQUIRES + TESTS_REQUIRES
