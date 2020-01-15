#!/bin/bash

set -ex
CUR_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export DHK_DIR="$( cd ${CUR_DIR}/.. && pwd )"

# services=("esbmock:latest" "mdillon/postgis:9.4")
serices = ()

set +e
for service in "${services[@]}"
do
    echo "Pulling service: $service"
    docker pull www.docker-registry.vastgoed.ictu:5000/${service}
done
set -e

export BUILD_NUMBER=$(printenv BUILD_NUMBER)
export DHK_BUILD_DOCKER_TAG=$(git rev-parse --short HEAD)-${BUILD_NUMBER}

docker-compose -f ${CUR_DIR}/docker-compose-build.yml build
docker-compose -f ${CUR_DIR}/docker-compose-jenkins.yml --project-name ${REST_API_BUILD_DOCKER_TAG} ${@:-up -d}