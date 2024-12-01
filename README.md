# usernetes (python)

> Python SDK and client to deploy user space Kubernetes (usernetes)

[![PyPI version](https://badge.fury.io/py/usernetes.svg)](https://badge.fury.io/py/usernetes)

This is a library in Python to easily deploy [Usernetes](https://github.com/rootless-containers/usernetes).
It is implemented in Python anticipating being used by Flux Framework, which has the most feature rich SDK
written in Python. Note that I haven't added support for other container runtimes (e.g., nerdctl) yet
since I'm just adding core functionality, but this would be easy to do.

🚧 Under Development 🚧

## Orchestration

The following setups are available:

- [flux-framework](scripts/flux): assumes a shared filesystem
- [aws](scripts/aws): (with Flux, assuming no shared filesystem) is coming soon!

See the logic in [scripts/flux/start-usernetes.sh](scripts/flux/start-usernetes.sh) and [scripts/flux/stop-usernetes.sh](scripts/flux/stop-usernetes.sh) for logic to bring up and down a cluster. For Flux, these are intending to be run as perilog and epilog scripts, before and after a batch job, respectively, and given that a particular environment variable is set. If you add a set of scripts (and instructions) for your environment, please open a pull request here to add code and instructions!

*This library has not been fully tested yet, waiting for development environments!*

## License

HPCIC DevTools is distributed under the terms of the MIT license.
All new contributions must be made under this license.

See [LICENSE](https://github.com/converged-computing/cloud-select/blob/main/LICENSE),
[COPYRIGHT](https://github.com/converged-computing/cloud-select/blob/main/COPYRIGHT), and
[NOTICE](https://github.com/converged-computing/cloud-select/blob/main/NOTICE) for details.

SPDX-License-Identifier: (MIT)

LLNL-CODE- 842614
