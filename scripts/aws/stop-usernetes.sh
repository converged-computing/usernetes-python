#!/bin/bash

# TODO we need different activity based on batch or submit, batch
# seems to be seeing the same network?

echo "The current path is $PATH"
echo "The FLUX_JOB_ID is $FLUX_JOB_ID"

# The user is required to set an attribute to indicate wanting usernetes
run_usernetes=$(flux job info $FLUX_JOB_ID jobspec | jq -r .attributes.user.usernetes)
if [ "${run_usernetes}" == "" ] || [ "${run_usernetes}" == "null" ]; then
    echo "User does not want to deploy User-space Kubernetes"
    exit 0
fi

# We need to get the user id to run commands on their behalf
user_uid=$(flux job info $FLUX_JOB_ID eventlog | grep submit | jq .context.userid)
user_id=$(id -nu ${user_uid})
echo "User ${user_id} has indicated User-space Kubernetes deployment"

# Get the kvs for the job so we can set metadata there
kvs_path=$(flux job id --to=kvs ${FLUX_JOB_ID})
usernetes_root=$(flux kvs get ${kvs_path}.usernetes_root)

# QUESTION: do we need to cleanup the kvs directory for the jobid?
flux usernetes top-level --clearkvs ${kvs_path}.usernetes || true

# Bring the cluster down, and it doesn't matter what the node name is (same command for all)
sudo -u ${user_id} usernetes --develop down --workdir $usernetes_root
if [  $? -eq 0 ]; then
   echo "Successfully brought down User-space Kubernetes for $(hostname), and doing final clean up"
   # This can also be done with usernetes clean --all
   # We assume a shared filesystem and issue this just once
   # TODO test the clean without root (and see if containers AND filesystem cleans up)
   sudo -u ${user_id} usernetes --develop clean --workdir $usernetes_root
   rm -rf ${usernetes_root}
else
   echo "Issue bringing down User-space Kubernetes, root left at ${usernetes_root}"
fi
