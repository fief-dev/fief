#! /bin/bash

set -e

hatch env create
npm install

cp .env.dist .env
echo "ENCRYPTION_KEY=$(hatch run python -c "from cryptography.fernet import Fernet;print(Fernet.generate_key().decode('utf-8'), end='')")" >> .env
echo "FIEF_DOMAIN=${CODESPACE_NAME}-8000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}" >> .env
hatch run python -m fief.cli migrate

set +e
hatch run translations.compile
hatch run python -m fief.cli create-admin --user-email anne@bretagne.duchy --user-password herminetincture
set -e
