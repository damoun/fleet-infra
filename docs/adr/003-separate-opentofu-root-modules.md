# ADR-003: Separate OpenTofu root modules per provider

## Status

Accepted

## Context

The infrastructure is managed by multiple providers that serve different
purposes: Hetzner Cloud (VMs, networks), NetBird (VPN setup keys), and
Kubernetes (bootstrap secrets). Combining them into a single root module
would couple their lifecycles, require all credentials at once, and make
state files larger and riskier to manage.

## Decision

Use separate root modules per provider group:

| Module              | Providers          | Purpose                          |
|---------------------|--------------------|----------------------------------|
| `tofu/hetzner/`     | hcloud, talos      | Infrastructure + cluster bootstrap |
| `tofu/netbird/`     | netbird            | NetBird API setup keys           |
| `tofu/kubernetes/`  | kubernetes         | Bootstrap Kubernetes secrets     |

Cross-module data is shared via `terraform_remote_state` data sources.
Apply order: hetzner -> netbird -> kubernetes.

## Consequences

- Each module has independent state and can be applied in isolation.
- Credentials are scoped: only the hetzner module needs the Hetzner token,
  only netbird needs the NetBird PAT, etc.
- Cross-module dependencies are explicit via `terraform_remote_state`.
- Operators must apply modules in the correct order during initial bootstrap.
- Adding a new provider group means adding a new root module rather than
  expanding an existing one.
