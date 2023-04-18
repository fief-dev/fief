#! /bin/bash

set -e

hatch env create
cp .env.dist .env
echo "ENCRYPTION_KEY=$(hatch run python -c "from cryptography.fernet import Fernet;print(Fernet.generate_key().decode('utf-8'), end='')")" >> .env
echo "FIEF_DOMAIN=${CODESPACE_NAME}-8000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}" >> .env
hatch run python -m fief.cli migrate

set +e
hatch run python -m fief.cli workspaces create-main
hatch run python -m fief.cli workspaces create-main-user --user-email anne@bretagne.duchy --user-password hermine1
set -e
