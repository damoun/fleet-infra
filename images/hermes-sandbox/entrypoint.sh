#!/bin/sh
set -eu

# Host key lives on a writable volume; the root filesystem is read-only.
if [ ! -f /run/sshd/ssh_host_ed25519_key ]; then
	ssh-keygen -q -t ed25519 -N '' -f /run/sshd/ssh_host_ed25519_key
fi

exec /usr/sbin/sshd -D -e -f /etc/ssh/sshd_config
