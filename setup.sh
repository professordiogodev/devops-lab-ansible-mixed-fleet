#!/usr/bin/env bash
# Builds two server images (Ubuntu 24.04 and Debian 12) and starts four servers. Run: ./setup.sh
set -u
cd "$(dirname "$0")"
LAB=ansible-mixed-fleet
for c in docker ssh-keygen; do command -v "$c" >/dev/null || { echo "$c is not installed or not on PATH"; exit 1; }; done
docker info >/dev/null 2>&1 || { echo "Docker is not running."; exit 1; }
if docker ps -a --filter label=lab=$LAB -q | grep -q .; then echo "The lab is already set up. Run ./teardown.sh first to start over."; exit 1; fi
for port in 2231 2232 2233 2234; do
  if (exec 3<>"/dev/tcp/127.0.0.1/$port") 2>/dev/null; then echo "Port $port is in use on your machine. Free it first."; exit 1; fi
done
echo "Building the server images (first run takes a few minutes)..."
docker build -q -t fleet-ubuntu:lab --build-arg BASE=ubuntu:24.04 servers >/dev/null || { echo "ubuntu image build failed"; exit 1; }
docker build -q -t fleet-debian:lab --build-arg BASE=debian:12 servers >/dev/null || { echo "debian image build failed"; exit 1; }
mkdir -p keys
[ -f keys/id_ed25519 ] || ssh-keygen -q -t ed25519 -N '' -C ansible-lab -f keys/id_ed25519
chmod 600 keys/id_ed25519
docker network create --label lab=$LAB mf-net >/dev/null
start() { # name image sshport
  docker run -d --name "$1" --hostname "$1" --label lab=$LAB --network mf-net --privileged --cgroupns=host --tmpfs /run --tmpfs /run/lock \
    -p "127.0.0.1:$3:22" "$2" >/dev/null || { echo "could not start $1"; exit 1; }
}
start mf-u1 fleet-ubuntu:lab 2231
start mf-u2 fleet-ubuntu:lab 2232
start mf-d1 fleet-debian:lab 2233
start mf-d2 fleet-debian:lab 2234
for name in mf-u1 mf-u2 mf-d1 mf-d2; do
  n=0
  until docker exec "$name" systemctl is-active ssh >/dev/null 2>&1; do n=$((n+1)); [ $n -gt 60 ] && { echo "$name did not boot"; exit 1; }; sleep 1; done
  docker exec "$name" sh -c 'mkdir -p /home/deploy/.ssh && chmod 700 /home/deploy/.ssh'
  docker cp keys/id_ed25519.pub "$name:/home/deploy/.ssh/authorized_keys"
  docker exec "$name" sh -c 'chown -R deploy:deploy /home/deploy/.ssh && chmod 600 /home/deploy/.ssh/authorized_keys'
done
cat <<TXT

Four fresh servers are running. Nothing is installed on them.

  mf-u1  Ubuntu 24.04   ssh 127.0.0.1 port 2231
  mf-u2  Ubuntu 24.04   ssh 127.0.0.1 port 2232
  mf-d1  Debian 12      ssh 127.0.0.1 port 2233
  mf-d2  Debian 12      ssh 127.0.0.1 port 2234

  user: deploy (passwordless sudo)    key: keys/id_ed25519    inventory: inventory.ini (provided)
Try:  ansible fleet -m ping
TXT
