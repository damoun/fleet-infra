#!/bin/sh
# Wipe the workspace once Hermes has been idle, so each working session starts
# clean. Hermes holds its SSH connection for five minutes after the last
# command, so no sshd-session process means nobody is using the sandbox.
set -u

idle=${SANDBOX_IDLE_SECONDS:-1800}
interval=${SANDBOX_IDLE_CHECK_SECONDS:-60}
last=$(date +%s)
wiped=0

while sleep "$interval"; do
	now=$(date +%s)
	if pgrep -x 'sshd-session|sshd-auth' >/dev/null; then
		last=$now
		wiped=0
		continue
	fi
	if [ "$wiped" -eq 1 ] || [ $((now - last)) -lt "$idle" ]; then
		continue
	fi

	# Leftover agent processes: everything this user runs except sshd and
	# this watchdog (with its own sleep children).
	keep=" $$ $(pgrep -P $$ | tr '\n' ' ') "
	for pid in $(pgrep -u "$(id -u)" -v -x sshd); do
		case "$keep" in *" $pid "*) continue ;; esac
		kill -TERM "$pid" 2>/dev/null
	done
	sleep 2
	for pid in $(pgrep -u "$(id -u)" -v -x sshd); do
		case "$keep" in *" $pid "*) continue ;; esac
		kill -KILL "$pid" 2>/dev/null
	done

	find /home/agent /tmp -mindepth 1 -delete 2>/dev/null
	echo "sandbox: idle for ${idle}s, workspace wiped"
	wiped=1
done
