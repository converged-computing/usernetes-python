#!/bin/bash

echo "The current path is $PATH"
echo "The FLUX_JOB_ID is $FLUX_JOB_ID"

# Keep a copy of usernetes you control for users to use
# **You likely will want to change this.
usernetes_template=/home/ubuntu/usernetes

# The user is required to set an attribute to indicate wanting usernetes
run_usernetes=`flux job info $FLUX_JOB_ID jobspec | jq -r .attributes.user.usernetes`
if [ "${run_usernetes}" == "" ] || [ "${run_usernetes}" == "null" ]; then
    echo "User does not want to deploy User-space Kubernetes"
    exit 0
fi

echo "User has indicated wanting to deploy User-space Kubernetes"

# Get the kvs for the job so we can set metadata there
usernetes_root=$(mktemp -d -t usernetes-XXXXXX)
kvs_path=$(flux job id --to=kvs ${FLUX_JOB_ID})
flux kvs put ${kvs_path}.usernetes=yes
flux kvs put ${kvs_path}.usernetes_root=${usernetes_root}

# Get the nodelist from the jobid
nodes=$(flux job info $FLUX_JOB_ID R | jq -r .execution.nodelist[0])
echo "Found nodes ${nodes} in Job ${FLUX_JOB_ID}"

# Count the nodes (including control plane)
worker_count=$(flux hostlist -x $(hostname) --count local)
echo "Found ${count} total nodes, and ${worker_count} not including the control plane"

# Get the lead broker (control plane) and worker ids
lead_broker=$(echo "$nodes" | cut -d ',' -f 1)
rank=$(hostname)

# If we don't remove the created tmpdir, it will copy inside of it
# IMPORTANT: this directory needs to exist on the workers too
flux exec -r all rm -rf $usernetes_root
flux exec -r all cp -R $usernetes_template $usernetes_root
echo "Usernetes will be staged in ${usernetes_root}"

# Do all orchestration from control plane. This uses the docker-compose.yaml provided by usernetes
# The two scripts handle orchestration of waiting for the other.
if [ "${rank}" == "${lead_broker}" ]; then
    usernetes --develop start-control-plane --workdir $usernetes_root --worker-count ${worker_count}
else
    usernetes --develop start-worker --workdir $usernetes_root
fi
export KUBECONFIG=$usernetes_root/kubeconfig
