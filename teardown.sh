#!/usr/bin/env bash
# Removes the four servers, their network, the images and the generated files. Run with: ./teardown.sh
set -u
cd "$(dirname "$0")"
LAB=ansible-mixed-fleet
for c in $(docker ps -aq --filter label=lab=$LAB); do docker rm -f "$c" >/dev/null 2>&1; done
docker network rm mf-net >/dev/null 2>&1
docker image rm fleet-ubuntu:lab fleet-debian:lab >/dev/null 2>&1 && echo "removed the images"
rm -rf keys .ansible
echo "Now run ./verify-teardown.sh"
