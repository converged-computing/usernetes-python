#!/bin/bash

# Bring up user-space Kubernetes in a non-shared filesystem (AWS)
# Variables to add:
# 1. Runtime (e.g., docker vs. podman)
# 2. Prolog currently stuck at "found join command" and then no output

# Keep a copy of usernetes you control for users to use - you likely will want to change this
usernetes_template=/home/ubuntu/usernetes

# We need to get the user id to run commands on their behalf
# user_uid=$(flux job info $FLUX_JOB_ID eventlog | grep submit | jq .context.userid)
# FLUX_JOB_USER_ID
user_id=$(id -nu ${FLUX_JOB_USERID})

echo "PATH is $PATH and FLUX_JOB_ID is $FLUX_JOB_ID, running as $(whoami) on behalf of ${user_id}"

# The user is required to set an attribute to indicate wanting usernetes
run_usernetes=$(flux job info $FLUX_JOB_ID jobspec | jq -r .attributes.user.usernetes)
if [ "${run_usernetes}" == "" ] || [ "${run_usernetes}" == "null" ]; then
    echo "User does not want to deploy User-space Kubernetes"
    exit 0
fi
echo "User has indicated wanting to deploy User-space Kubernetes"

# Get the kvs for the job so we can set metadata there
kvs_path=$(flux job id --to=kvs ${FLUX_JOB_ID})

# Get the nodelist from the jobid
# nodes=$(flux job info $FLUX_JOB_ID R | jq -r .execution.nodelist[0])
nodes=$(flux hostlist ${FLUX_JOB_ID})
echo "Found nodes ${nodes} in Job ${FLUX_JOB_ID}"

# Count the nodes (including control plane)
count=$(flux getattr size)
worker_count=$(flux hostlist -x $(hostname) --count local)
echo "Found ${count} total nodes, and ${worker_count} not including the control plane"

# Get the lead broker (control plane) and worker ids
lead_broker=$(flux hostlist -n 0 local)
rank=$(hostname)
echo "The lead broker is ${lead_broker}"

# We need a predictable way to name a usernetes root.
tmpdir=$(dirname $(mktemp -u))
jobid=$(echo ${FLUX_JOB_ID} | tr '[:upper:]' '[:lower:]')
usernetes_root=${tmpdir}/usernetes-${jobid}
echo "Usernetes will be staged in ${usernetes_root}"

# I am not assuming this is shared across nodes
flux kvs put ${kvs_path}.usernetes=yes
flux kvs put ${kvs_path}.usernetes_root=${usernetes_root}

# This is for the user
sudo -u ${user_id} flux kvs put ${kvs_path}.user.usernetes_root=${usernetes_root}

# If we don't remove the created tmpdir, it will copy inside of it
rm -rf $usernetes_root
cp -R $usernetes_template $usernetes_root
chown -R $user_id $usernetes_root

# Use the tmpdir name to generate an archive name
usernetes_uid=$(basename $usernetes_root)
archive_name=${usernetes_uid}-join-command
echo "Archive name for sharing join-command is ${archive_name}"

# Ensure the network is not up
network_name=${usernetes_uid}_default
sudo -u ${user_id} docker network rm ${network_name} || true

# Debug mode - we sleep here
debug_mode=$(flux job info $FLUX_JOB_ID jobspec | jq -r .attributes.user.usernetes_debug)
if [ "${debug_mode}" != "null" ]; then
    echo "Entering debug mode for ${usernetes_root}, sleeping infinity"
    sleep infinity
fi

# Do all orchestration from control plane. This uses the docker-compose.yaml provided by usernetes
# The two scripts handle orchestration of waiting for the other.
if [ "${rank}" == "${lead_broker}" ]; then
    # The main difference between here and the shared filesystem is that we need to run in serial,
    # distribute the join-command, and wait for the correct number of instance names to show up
    sudo -u ${user_id} usernetes --develop start-control-plane --workdir $usernetes_root --worker-count ${worker_count} --serial
    flux archive create --name ${archive_name} --directory $usernetes_root join-command
    flux exec -x 0 flux archive extract --name ${archive_name} --directory $usernetes_root

    # Wait for workers - this needs to equal the worker count. We do this because
    # the filesystem is not shared, which is how the wait-workers command works
    while true; do
        echo "Checking for ${worker_count} workers to be ready..."
        ready_count=$(flux kvs dir ${kvs_path}.usernetes_ready | wc -l)
        sleep 5
        if [ "${ready_count}" == "${worker_count}" ]; then
            echo "⭐ ${ready_count} workers are ready."
            break
        fi
    done

    # One last sync is needed
    sudo -u ${user_id} make -C $usernetes_root sync-external-ip
else
    # We don't need to do anything special here, it will still wait for the join command
    sudo -u ${user_id} usernetes start-worker --workdir $usernetes_root
    # When this command finishes, the worker is as ready as it can be.
    # Add this to the ready kvs directory.
    broker_rank=$(flux getattr rank)
    flux kvs put ${kvs_path}.usernetes_ready.${broker_rank}=yes
fi
export KUBECONFIG=$usernetes_root/kubeconfig
