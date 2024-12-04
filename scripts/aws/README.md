# Flux Framework + Usernetes on AWS

This setup has two means to deploy

- On the level of the [system instance](#system-instance) (ideal for experiments)
- With a [batch job](#batch-job) (to emulate HPC)

The main difference with the second point and an actual HPC system is that we don't assume a shared filesystem here.

## System Instance

#### TLDR

Don't want to read stuff? Here is the whole thing for a system instance level install.

```bash
usernetes_root=/home/ubuntu/usernetes

# Get the count of worker nodes (minus the lead broker) - you could also just know this :)
nodes=$(flux hostlist -x $(hostname) local)
counter=(${nodes//","/ })
count=${#counter[@]}

# Start the control plane and generate the join-command
usernetes start-control-plane --workdir $usernetes_root --worker-count ${count} --serial

# Share the join-command with the workers
flux archive create --name join-command --directory $usernetes_root join-command
flux exec -x 0 flux archive extract --name join-command --directory $usernetes_root
flux exec -x 0 usernetes start-worker --workdir $usernetes_root

# Go to town!
make -C $usernetes_root sync-external-ip
export KUBECONFIG=/home/ubuntu/usernetes/kubeconfig
kubectl get nodes
```

#### Details

The deployment of the system instance is fairly easy - it's going to be starting the control plane, sharing the join-command, and then using flux to exec a command to the workers to do the same.

```bash
usernetes_root=/home/ubuntu/usernetes

# Get the count of worker nodes (minus the lead broker) - you could also just know this :)
nodes=$(flux hostlist -x $(hostname) local)
counter=(${nodes//","/ })
count=${#counter[@]}
```

Next we are going to deploy the control plane to the lead broker. We will tell it to deploy in `--serial`, meaning it won't wait for worker nodes to be ready before issuing the last command. We will be issuing the command to deploy the workers, and then the last command to sync.

```bash
usernetes start-control-plane --workdir $usernetes_root --worker-count ${count} --serial
```

Now let's create an archive for our join-command, and use flux exec with flux archive to distribute it.

```bash
flux archive create --name join-command --directory $usernetes_root join-command
flux exec -x 0 flux archive extract --name join-command --directory $usernetes_root
```

Now bring up the worker nodes in the same fashion.

```bash
flux exec -x 0 usernetes start-worker --workdir $usernetes_root
```

Finally, run the last sync command.

```bash
make -C $usernetes_root sync-external-ip
```

Export the kubeconfig, and interact with your cluster.

```bash
export KUBECONFIG=/home/ubuntu/usernetes/kubeconfig
kubectl get nodes
```
```console
NAME                      STATUS   ROLES           AGE     VERSION
u7s-i-0831eed34c13e747e   Ready    control-plane   19m     v1.31.0
u7s-i-0ac10f9b787d6a349   Ready    <none>          5m26s   v1.31.0
```

You're in business! User-space Kubernetes is deployed to the system instance. Go nuts. 🥜

## Batch Job

This requires a bit more setup.

> This setup assumes a shared filesystem rooted in `/tmp`.

### Setup

This setup requires perilog and epilog scripts that will setup and teardown userspace
Kubernetes for a job. We have provided a set of scripts for doing that, and you need to
provide the prefix to your flux install.

```bash
git clone https://github.com/converged-computing/usernetes-python
cd usernetes-python
python3 -m pip install -e .

# Update the path to usernetes in the (start/stop)-usernetes.sh prolog scripts!
# /etc/flux/system is the default, so you can also remove it if you are using that.
./scripts/install-scripts.sh /etc/flux/system
```

The last step is to configure your flux instance to allow prolog and epilog. Follow [steps two and three here](https://flux-framework.readthedocs.io/projects/flux-core/en/latest/guide/admin.html#adding-job-prolog-epilog-scripts) to edit the broker config. And then see [usage](#usage) for how to submit jobs.

### Usage

#### Testing Usernetes

Here are some helpful commands for using usernetes to get metadata in jobs, either as just the value (attr) or as an export (env). These might go in a batch script, and I'm showing them with flux run so they will function (they rely on either `flux getattr jobid` or an environment variable for a job, which will work for slurm or flux.

```bash
flux run -N1 usernetes env kubeconfig
flux run -N1 usernetes attr kubeconfig
flux run -N1 usernetes env workdir
flux run -N1 usernetes attr workdir
```

#### Batch Job

Anything that deploys a job with an epilog or prolog should work, and with one or more instances. Here is a batch script to create on all nodes:

```bash
#!/bin/bash

# This only works given non-shared filesystem
# Only rank 0 (lead) will write the kubeconfig
kubeconfig=$(usernetes attr kubeconfig)
echo "The kubeconfig is ${kubeconfig}"

# The working directory defaults to $TMPDIR/usernetes-<jobid>
workdir=$(usernetes attr workdir)
echo "The working directory is ${workdir}"
ls $workdir

# Allow worker node to switch from NotReady to Ready
sleep 10
if [ -f ${kubeconfig} ]; then
   echo "Found kubeconfig at $kubeconfig"
   KUBECONFIG=$kubeconfig kubectl get nodes
fi
```

Note that we can use the trick to check for the kubeconfig file here because without a shared filesystem, it will
only exist on the lead broker (control plane). If you have a shared filesystem, you are going to run that command N times,
on the control plane and all works. More realistically, you'd probably create a service, and then use it.

```bash
#!/bin/bash

kubeconfig=$(usernetes attr kubeconfig)
if [ -f ${kubeconfig} ]; then
   KUBECONFIG=$kubeconfig kubectl apply -f machine-learning-thing.yaml
fi

flux run -N 2 python more-machine-learning.py
```

#### Run or Submit

Run or submit works in a similar way! Let's use the same (or a streamlined) version of the batch.sh script above:

```bash
#!/bin/bash

kubeconfig=$(usernetes attr kubeconfig)
# Allow worker node to switch from NotReady to Ready
sleep 10
if [ -f ${kubeconfig} ]; then
   echo "Found kubeconfig at $kubeconfig"
   KUBECONFIG=$kubeconfig kubectl get nodes
fi
```

And then run!

```bash
flux run -N2 --setattr=attributes.user.usernetes=yes batch.sh
```
```console
flux-job: ƒ2QT1HSJy5 started                                                                                                                                                           00:00:50
Found kubeconfig at /tmp/usernetes-ƒ2qt1hsjy5/kubeconfig
NAME                      STATUS   ROLES           AGE   VERSION
u7s-i-07a51ff87feea61f4   Ready    control-plane   30s   v1.31.2
u7s-i-0ece5bc9f1d6a38e6   Ready    <none>          18s   v1.31.2
```

#### Debugging

For any submission means, if you want to debug (meaning creating the setup without allowing the prolog to exit) you can do:

```bash
flux batch -N2 --setattr=attributes.user.usernetes=yes --setattr=attributes.user.usernetes_debug=yes batch.sh
```

You'll need to cleanup on your own:

```bash
docker ps
docker stop <container>
docker rm <container>

docker network ls
docker network rm <network>
```

If you need to debug, look at `flux dmesg`. Here is what we see when a job is cleaning up:

```console
...
2024-12-04T02:11:13.353874Z job-manager.info[0]: ƒ2QT1HSJy5: epilog: i-0ece5bc9f1d6a38e6 (rank 1): stdout:  Container usernetes-2qt1hsjy5-node-1  Stopping
2024-12-04T02:11:13.355078Z job-manager.info[0]: ƒ2QT1HSJy5: epilog: i-07a51ff87feea61f4 (rank 0): stdout:  Container usernetes-2qt1hsjy5-node-1  Stopping
2024-12-04T02:11:13.794493Z job-manager.info[0]: ƒ2QT1HSJy5: epilog: i-0ece5bc9f1d6a38e6 (rank 1): stdout:  Container usernetes-2qt1hsjy5-node-1  Stopped
2024-12-04T02:11:13.794523Z job-manager.info[0]: ƒ2QT1HSJy5: epilog: i-0ece5bc9f1d6a38e6 (rank 1): stdout:  Container usernetes-2qt1hsjy5-node-1  Removing
2024-12-04T02:11:13.805416Z job-manager.info[0]: ƒ2QT1HSJy5: epilog: i-0ece5bc9f1d6a38e6 (rank 1): stdout:  Container usernetes-2qt1hsjy5-node-1  Removed
2024-12-04T02:11:13.806014Z job-manager.info[0]: ƒ2QT1HSJy5: epilog: i-0ece5bc9f1d6a38e6 (rank 1): stdout:  Network usernetes-2qt1hsjy5_default  Removing
2024-12-04T02:11:13.949181Z job-manager.info[0]: ƒ2QT1HSJy5: epilog: i-0ece5bc9f1d6a38e6 (rank 1): stdout:  Network usernetes-2qt1hsjy5_default  Removed
2024-12-04T02:11:13.966901Z job-manager.info[0]: ƒ2QT1HSJy5: epilog: i-0ece5bc9f1d6a38e6 (rank 1): stdout: Successfully brought down User-space Kubernetes for i-0ece5bc9f1d6a38e6, and doing final clean up
2024-12-04T02:11:18.858445Z job-manager.info[0]: ƒ2QT1HSJy5: epilog: i-07a51ff87feea61f4 (rank 0): stdout:  Container usernetes-2qt1hsjy5-node-1  Stopped
2024-12-04T02:11:18.858475Z job-manager.info[0]: ƒ2QT1HSJy5: epilog: i-07a51ff87feea61f4 (rank 0): stdout:  Container usernetes-2qt1hsjy5-node-1  Removing
2024-12-04T02:11:18.875432Z job-manager.info[0]: ƒ2QT1HSJy5: epilog: i-07a51ff87feea61f4 (rank 0): stdout:  Container usernetes-2qt1hsjy5-node-1  Removed
2024-12-04T02:11:18.876034Z job-manager.info[0]: ƒ2QT1HSJy5: epilog: i-07a51ff87feea61f4 (rank 0): stdout:  Network usernetes-2qt1hsjy5_default  Removing
2024-12-04T02:11:19.042701Z job-manager.info[0]: ƒ2QT1HSJy5: epilog: i-07a51ff87feea61f4 (rank 0): stdout:  Network usernetes-2qt1hsjy5_default  Removed
2024-12-04T02:11:19.060123Z job-manager.info[0]: ƒ2QT1HSJy5: epilog: i-07a51ff87feea61f4 (rank 0): stdout: Successfully brought down User-space Kubernetes for i-07a51ff87feea61f4, and doing final clean up
2024-12-04T02:11:19.144581Z sched-simple.debug[0]: free: rank[0-1]/core[0-15] ƒ2QT1HSJy5 (final)
```

### Issues / Features

 - We should add the container runtime to specify (e.g., docker vs. podman)
 - It's problematic asking for tasks (e.g., `flux run -N2 -n 32 --setattr=attributes.user.usernetes=yes kubectl get pods`) as 32 instances will be started.
 - We need to tweak the network namespace, assuming users need to share ports, run more than one, etc.
