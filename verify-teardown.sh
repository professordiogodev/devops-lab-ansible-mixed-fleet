#!/usr/bin/env bash
# Proves the lab left nothing on your machine. Run with: ./verify-teardown.sh
set -u
cd "$(dirname "$0")"
pass=0; failn=0
check() { local d="$1"; shift; if "$@" >/dev/null 2>&1; then echo "PASS  $d"; pass=$((pass+1)); else echo "FAIL  $d"; failn=$((failn+1)); fi; }
check "no container labelled lab=ansible-mixed-fleet" bash -c '[ -z "$(docker ps -aq --filter label=lab=ansible-mixed-fleet)" ]'
check "no network labelled lab=ansible-mixed-fleet" bash -c '[ -z "$(docker network ls -q --filter label=lab=ansible-mixed-fleet)" ]'
check "the server images are gone" bash -c '! docker image inspect fleet-ubuntu:lab && ! docker image inspect fleet-debian:lab'
check "the generated SSH keys are gone" bash -c '[ ! -d keys ]'
echo
if [ "$failn" -eq 0 ]; then echo "TEARDOWN VERIFIED ($pass/$pass) on this machine"; else echo "NOT CLEAN: $failn leftover(s). Remove them and run this again."; fi
exit "$failn"
