#!/usr/bin/env bash

# uses INVENTORY_CLAUSE and RESET_DB_CLAUSE environment variables and the file ansible/release_plus_ansible.zip
# Set script to exit immediately on command error.
set -ex

rm -rf unzipped_release_package
mkdir unzipped_release_package
cd unzipped_release_package
unzip -q ../ansible/release_plus_ansible.zip

ansible-playbook -i ${INVENTORY_CLAUSE} install_all_webservices.yml ${RESET_DB_CLAUSE}

cd ..

