# usernetes (python)

> Python SDK and client to deploy user space Kubernetes (usernetes)

[![PyPI version](https://badge.fury.io/py/usernetes.svg)](https://badge.fury.io/py/usernetes)

This is a library in Python to easily deploy [Usernetes](https://github.com/rootless-containers/usernetes).
It is implemented in Python anticipating being used by Flux Framework, which has the most feature rich SDK
written in Python. Note that I haven't added support for other container runtimes (e.g., nerdctl) yet
since I'm just adding core functionality, but this would be easy to do.

🚧 Under Development 🚧

*This library has not been tested yet, waiting for development environments!*

## TODO

I'm planning to get our testing environment first, and then continue work on this.
The main deployment question I have to run this in user space (under a batch job)
is what is the best way to provision the usernetes code. Whatever strategy we choose,
we want to pin a version (release) that we have tested. But our options are:

- use a submodule provided here (what I'm implemented now for testing)
- do a temporary / on the fly clone per job (takes time, but might be the best option)
- cache something in user's home (only one clone, but could lead to bugs with cleanup, etc.)

Likely I'll test our the current approach and then choose the second or third bullet. Note
that what is missing from the code here is the distribution mechanism for the join-command.
On an HPC cluster we have a shared filesystem (and we are good) but in cloud we need
a combination of flux archive and flux exec.

## License

HPCIC DevTools is distributed under the terms of the MIT license.
All new contributions must be made under this license.

See [LICENSE](https://github.com/converged-computing/cloud-select/blob/main/LICENSE),
[COPYRIGHT](https://github.com/converged-computing/cloud-select/blob/main/COPYRIGHT), and
[NOTICE](https://github.com/converged-computing/cloud-select/blob/main/NOTICE) for details.

SPDX-License-Identifier: (MIT)

LLNL-CODE- 842614
