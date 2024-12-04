#!/bin/bash

kubeconfig=$(usernetes attr kubeconfig)
# Allow worker node to switch from NotReady to Ready
sleep 10
if [ -f ${kubeconfig} ]; then
   echo "Found kubeconfig at $kubeconfig"
   KUBECONFIG=$kubeconfig kubectl get nodes
fi
