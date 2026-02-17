#!/bin/bash
set -e

DOCKER_GID=$(stat -c '%g' /var/run/docker.sock)

# If GID is 0 (root), just chmod the socket directly
if [ "${DOCKER_GID}" = "0" ]; then
    chmod 666 /var/run/docker.sock
else
    # Otherwise match the GID dynamically
    if ! getent group docker > /dev/null 2>&1; then
        groupadd -g ${DOCKER_GID} docker
    else
        groupmod -g ${DOCKER_GID} docker
    fi
    usermod -aG docker jenkins
fi

exec gosu jenkins /usr/local/bin/jenkins.sh "$@"