# Flux Framework + Usernetes

> This setup assumes a shared filesystem rooted in `/tmp`.

**IMPORTANT** we don't have a development environment for this yet, so it isn't finished.
The [aws setup](../aws) without a shared filesystem is testing and working, with more complete documentation in the README there.

## Setup

You'll want to first create the appropriate perilog and epilog scripts that will setup and teardown userspace
Kubernetes for a job. Here is an example for how to do that (and you only need to do this once) for a system
that has flux system configuration in `/etc/flux`. First, let's copy the script included here to
a file named "prolog" in `/etc/flux/system` and create a subdirectory for our prolog scripts.

```bash
mkdir -p /etc/flux/system/prolog.d /etc/flux/system/epilog.d
```

We assume you have cloned usernetes-python and are sitting at the root.
These top level scripts will be run, and execute those in `(epilog|prolog).d`
There is a script provided to install usernetes to where your system (root) will see it, along
with prolog/epilog scripts to your flux system configuration root, which defaults
to `/etc/flux/system`.

```bash
/bin/bash ./scripts/install-scripts.sh /etc/flux/system
```

For batch jobs that want to deploy and teardown. The last step is to configure your flux instance to allow prolog and epilog. Follow [steps two and three here](https://flux-framework.readthedocs.io/projects/flux-core/en/latest/guide/admin.html#adding-job-prolog-epilog-scripts) to edit the broker config.

## Usage

Anything that deploys a job with an epilog or prolog should work, and with one or more instances.

```bash
flux batch -N4 --setattr=attributes.user.usernetes=yes kubectl get pods
flux submit -N4 --setattr=attributes.user.usernetes=yes kubectl get pods
flux run -N4 --setattr=attributes.user.usernetes=yes kubectl get pods
```
