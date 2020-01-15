#!/usr/bin/env bash

# uses BRANCH_NAME, BUILD_NUMBER and SPRINT_NUMBER environment variables and file ansible/release_plus_ansible.zip
# Set script to exit immediately on command error.
set -e

SAFE_BRANCH_NAME="$(echo ${BRANCH_NAME} | sed 's|/||g')"
echo ${SAFE_BRANCH_NAME}

NEXUS_RELEASE_TYPE='snapshots'
if [ ${SAFE_BRANCH_NAME} = "master" ]; then
   NEXUS_RELEASE_TYPE='releases'
fi

NEXUS_URL=http://www.nexus.vastgoed.ictu:8081/service/local/repositories/${NEXUS_RELEASE_TYPE}/content/harp/rest/0.${SPRINT_NUMBER}/${SAFE_BRANCH_NAME}/${BUILD_NUMBER}/release_plus_ansible.zip
echo ${NEXUS_URL}

#push ansible scripts + package to nexus
NEXUS_CREDENTIALS=admin:admin123
curl -v -u ${NEXUS_CREDENTIALS} --upload-file ansible/release_plus_ansible.zip ${NEXUS_URL}
echo "upload done"

