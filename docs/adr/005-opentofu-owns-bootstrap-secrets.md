# ADR-005: OpenTofu owns bootstrap secrets

## Status

Accepted

## Context

Some Kubernetes secrets must exist before FluxCD can reconcile for the first
time. For example, the `sops-age` secret (SOPS decryption key) and the
`netbird-setup-key` secret (NetBird VPN enrollment) are both required by
HelmReleases or Kustomizations that Flux manages. Without these secrets,
Flux reconciliation fails on the first run.

## Decision

OpenTofu manages secrets that must exist before FluxCD's first reconciliation:

| Secret              | Namespace     | Purpose                        |
|---------------------|---------------|--------------------------------|
| `sops-age`          | `flux-system` | SOPS age private key for Flux  |
| `netbird-setup-key` | `netbird`     | NetBird agent enrollment key   |

All other application secrets are managed by FluxCD via SOPS-encrypted
manifests committed to git.

**Boundary rule:** if a secret must exist before the first Flux reconciliation,
it belongs in OpenTofu. Otherwise, it belongs in a SOPS-encrypted manifest
in git.

## Consequences

- Bootstrap secrets are applied deterministically via `tofu apply` before
  Flux starts reconciling.
- Secret values live in OpenTofu state (which must be encrypted at rest).
- Adding a new bootstrap secret means modifying the `tofu/kubernetes/` module.
- Application-level secrets follow the standard SOPS workflow and do not
  require OpenTofu changes.
