#!/bin/sh

kubectl -n flux-system delete secret flux-system

flux bootstrap github \
  --owner=damoun \
  --repository=fleet-infra \
  --branch=main \
  --path=./clusters/cluster-1 \
  --personal
