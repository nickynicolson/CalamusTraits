#!/usr/bin/env bash
set -e

mkdir -p ~/.ssh
echo "$HPC_SSH_ID_RSA" > ~/.ssh/id_rsa
chmod 600 ~/.ssh/id_rsa

# Avoid host authenticity prompt
echo -e "Host *\n  StrictHostKeyChecking no\n" > ~/.ssh/config

# Start ssh-agent
eval "$(ssh-agent -s)"

# Add the key, passing the passphrase
# -k disables passphrase prompt, and we feed it via stdin
ssh-add ~/.ssh/id_rsa <<< "$HPC_SSH_ID_RSA_PASSPHRASE"
