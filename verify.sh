#!/usr/bin/env bash
# Runs your playbook and inspects the four servers. Run with: ./verify.sh
cd "$(dirname "$0")" || exit 1
command -v ansible-playbook >/dev/null || { echo "Ansible is not installed." >&2; exit 1; }
[ -f keys/id_ed25519 ] || { echo "Run ./setup.sh first." >&2; exit 1; }
exec python3 .lab/fleetcheck.py
