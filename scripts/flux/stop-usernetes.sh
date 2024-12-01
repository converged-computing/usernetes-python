#!/bin/bash

echo "The current path is $PATH"
echo "The FLUX_JOB_ID is $FLUX_JOB_ID"

# The user is required to set an attribute to indicate wanting usernetes
run_usernetes=`flux job info $FLUX_JOB_ID jobspec | jq -r .attributes.user.usernetes`
if [ "${run_usernetes}" == "" ] || [ "${run_usernetes}" == "null" ]; then
    echo "User does not want to deploy User-space Kubernetes"
    exit 0
fi

echo "User has indicated User-space Kubernetes deployment"

# Get the kvs for the job so we can set metadata there
kvs_path=$(flux job id --to=kvs ${FLUX_JOB_ID})
usernetes_root=$(flux kvs get ${kvs_path}.usernetes_root)

# Bring the cluster down, and it doesn't matter what the node name is (same command for all)
usernetes --develop down --workdir $usernetes_root
if [  $? -eq 0 ]; then
   echo "Successfully brought down User-space Kubernetes, and doing final clean up"
   # This can also be done with usernetes clean --all
   # We assume a shared filesystem and issue this just once
   rm -rf $usernetes_root
else
   echo "Issue bringing down User-space Kubernetes, root left at ${usernetes_root}"
fi
