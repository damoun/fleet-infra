#!/usr/bin/env bash
# Prints every container image the cluster runs, one per line, derived from the repo.
set -euo pipefail
talos_map="$(cd "$(dirname "$0")" && pwd)/talos-images.txt"
cd "$(git rev-parse --show-toplevel)"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
ref='[a-z0-9.-]+(/[a-z0-9._-]+)+:[A-Za-z0-9._-]+@sha256:[0-9a-f]{64}'

{
	# Full refs anywhere in the manifests, including patch strings.
	git ls-files '*.yaml' '*.yml' ':!.github' | xargs grep -hoE "$ref" || true

	# repository + tag pairs in HelmRelease values.
	git ls-files '*.yaml' '*.yml' ':!.github' | xargs yq -N '
    .. | select(tag == "!!map" and has("repository") and has("tag"))
    | select(.tag | test("@sha256:"))
    | ((.registry // "") | sub(".+", "${0}/")) + .repository + ":" + .tag'

	# Cilium images come from its chart, pinned by digest per chart version.
	hr=infrastructure/controllers/cilium.yaml
	yq '.spec.values' "$hr" >"$tmp/cilium-values.yaml"
	helm template cilium cilium \
		--repo "$(yq '.spec.url' infrastructure/sources/helm-cilium.yaml)" \
		--version "$(yq '.spec.chart.spec.version' "$hr")" \
		--namespace kube-system -f "$tmp/cilium-values.yaml" | grep -oE "$ref"

	# Flux controllers come from the flux-operator catalog for the pinned version.
	fi=infrastructure/configs/flux-instance.yaml
	variant=$(yq '.spec.distribution.variant // "upstream-alpine"' "$fi")
	curl -fsSL "https://raw.githubusercontent.com/controlplaneio-fluxcd/distribution/main/images/v$(yq '.spec.distribution.version' "$fi")/$variant.yaml" >"$tmp/flux.yaml"
	for c in $(yq '.spec.components[]' "$fi"); do
		yq ".images[] | select(.name | test(\"/$c\$\")) | .name + \":\" + .newTag + \"@\" + .digest" "$tmp/flux.yaml"
	done

	# Talos runs the control plane from tags derived from tofu/baremetal.
	vars=tofu/baremetal/variables.tf
	k8s=v$(sed -n '/variable "kubernetes_version"/,/}/s/.*default *= *"\(.*\)"/\1/p' "$vars")
	talos=$(sed -n '/variable "talos_version"/,/}/s/.*default *= *"\(.*\)"/\1/p' "$vars")
	for c in kube-apiserver kube-controller-manager kube-scheduler; do
		echo "registry.k8s.io/$c:$k8s"
	done
	echo "ghcr.io/siderolabs/kubelet:$k8s"
	talos_images=$(awk -v v="$talos" '$1 == v { $1 = ""; print }' "$talos_map")
	if [ -z "$talos_images" ]; then
		echo "talos $talos missing from $talos_map" >&2
		exit 1
	fi
	printf '%s\n' $talos_images
} | sort -u
