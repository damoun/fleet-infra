#!/usr/bin/env bash
# Fails when the Gateway API CRDs and the Gateway API version Cilium is built against
# differ in major.minor. Cilium's Gateway controller only handles the API it compiles in.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

cilium=$(yq '.spec.chart.spec.version' infrastructure/controllers/cilium.yaml)
crds=$(sed -n 's/^ *# tag: *\(v[0-9][^[:space:]]*\)$/\1/p' infrastructure/sources/git-gateway-api.yaml)
# Cilium sometimes builds against a release candidate, e.g. v1.4.0-rc.2.
want=$(curl -fsSL "https://raw.githubusercontent.com/cilium/cilium/v$cilium/go.mod" |
	sed -n 's|^[[:space:]]*sigs.k8s.io/gateway-api \(v[0-9][^[:space:]]*\)$|\1|p')

if [ -z "$crds" ] || [ -z "$want" ]; then
	echo "could not read versions: crds='$crds' cilium go.mod='$want'" >&2
	exit 1
fi

echo "Cilium $cilium is built against Gateway API $want, CRDs are $crds"
if [ "$(echo "$crds" | cut -d. -f1,2)" != "$(echo "$want" | cut -d. -f1,2)" ]; then
	echo "Gateway API CRDs must match Cilium's major.minor: bump infrastructure/sources/git-gateway-api.yaml to $want" >&2
	exit 1
fi
