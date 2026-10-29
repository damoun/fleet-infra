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

# Hand the listed container env vars (proxy, CA, dummy tokens) to SSH sessions.
# sshd keeps only the first SetEnv line, so all pairs go on one.
pairs=""
for name in ${SSH_SETENV:-}; do
	case "$name" in *[!A-Za-z0-9_]*) continue ;; esac
	eval "value=\${$name:-}"
	if [ -n "$value" ]; then
		pairs="$pairs \"$name=$value\""
	fi
done
if [ -n "$pairs" ]; then
	echo "SetEnv$pairs" >/run/sshd/env.conf
else
	: >/run/sshd/env.conf
fi

/usr/local/bin/idle-wipe.sh &

exec /usr/sbin/sshd -D -e -f /etc/ssh/sshd_config
