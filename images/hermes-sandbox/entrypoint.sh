#!/bin/sh
set -eu

# sshd rejects host keys readable by anyone but their owner, and mounted
# Secret files are root-owned. Copy a provided key so it stays stable across
# restarts; otherwise generate one. /run/sshd is writable, / is not.
key=/run/sshd/ssh_host_ed25519_key
if [ -f /etc/ssh/host/ssh_host_ed25519_key ]; then
	install -m 0600 /etc/ssh/host/ssh_host_ed25519_key "$key"
elif [ ! -f "$key" ]; then
	ssh-keygen -q -t ed25519 -N '' -f "$key"
fi

exec /usr/sbin/sshd -D -e -f /etc/ssh/sshd_config
