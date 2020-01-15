#!/usr/bin/env bash

# Uses current directory to create tar and zip in the ansible subdirectory
# Set script to exit immediately on command error.
set -ex

rm -rf ansible/roles/app/files
mkdir -pv ansible/roles/app/files

rm -rf release_dependencies
mkdir release_dependencies

export PATH=${PATH}  # because otherwise pip doesnt have the PATH (due to black Jenkins magix), which it needs to configure/compile stuff

# TODO ideally use requirements.txt here for package that is sent to RVB / nexus
pip3.6 download -r requirements_debug.txt -d release_dependencies
# TODO replace the following line by a yum install in ansible as soon as RVB has a proper mod-wsgi yum package available
pip3.6 download mod-wsgi==4.5.17 -d release_dependencies

tar czf ansible/roles/app/files/release.tar.gz -X .zipignore .

cd ansible
rm -rf release_plus_ansible.zip
zip -q -r release_plus_ansible.zip ./

cd ..



