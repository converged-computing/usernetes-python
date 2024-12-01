# These functions for environment and attributes assume
# being in a flux instance, and also assume it is created
# in the user temporary directory.
import os
import tempfile

import usernetes.utils as utils


class InstanceAttributes:
    def __init__(self):
        self.jobid = get_jobid()
        self.uid = f"usernetes-{self.jobid.lower()}"
        self.root = os.path.join(tempfile.gettempdir(), self.uid)

    @property
    def kubeconfig(self):
        return os.path.join(self.root, "kubeconfig")

    @property
    def workdir(self):
        return self.root


def get_jobid():
    """
    Get the job id, first from an attribute then environ.

    This assumes flux, but arguably we can add other managers
    or they can export a similar identifier.
    """
    # This only works in batch (not run/submit)
    result = utils.run_command(["flux", "getattr", "jobid"])
    if result["return_code"] == 0 and result["message"] is not None:
        jobid = result["message"].strip()
    else:
        # Run/submit should have the envar
        jobid = os.environ.get("FLUX_JOB_ID")
    if jobid is None:
        # Fall back to Slurm
        jobid = os.environ.get("SLURM_JOB_ID")
    if jobid is None:
        raise ValueError("Cannot derive jobid to interact with.")
    return jobid
