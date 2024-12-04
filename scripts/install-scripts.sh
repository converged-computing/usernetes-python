#!/bin/bash

here=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Install scripts to flux root. Requires sudo
flux_system_root=${1:-/etc/flux/system}
echo "Flux install root is ${flux_system_root}, cancel in 3 seconds if wrong."
sleep 3

# Important! The path for the prolog runner is /usr/sbin:/usr/bin:/sbin:/bin
sudo cp $(which usernetes) /usr/bin/usernetes

# Setup prolog/epilog
mkdir -p ${flux_system_root}/prolog.d ${flux_system_root}/epilog.d
sudo cp ${here}/shared/prolog.sh ${flux_system_root}/prolog
sudo cp ${here}/shared/epilog.sh ${flux_system_root}/epilog
sudo cp ${here}/aws/start-usernetes.sh ${flux_system_root}/prolog.d/start-usernetes.sh
sudo cp ${here}/aws/stop-usernetes.sh ${flux_system_root}/epilog.d/stop-usernetes.sh

# These are for the control plane and others
sudo chmod +x ${flux_system_root}/epilog ${flux_system_root}/prolog ${flux_system_root}/*/*.sh
