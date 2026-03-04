# ADR-003: Separate OpenTofu root modules per provider

## Status

Accepted

## Context

The infrastructure is managed by multiple providers that serve different
purposes: Hetzner Cloud (VMs, networks), Talos (machine config, cluster
bootstrap), NetBird (VPN setup keys), and Kubernetes (bootstrap secrets).
Combining them into a single root module would couple their lifecycles,
require all credentials at once, and make state files larger and riskier
to manage.

The original `tofu/hetzner/` module bundled both `hcloud` and `talos`
providers. These have different lifecycles: infrastructure (servers, networks)
changes rarely, while Talos config (machine patches, upgrades) changes more
often. Separating them allows applying Talos changes without risking
infrastructure drift.

## Decision

Use one root module per provider:

| Module              | Provider           | Purpose                          |
|---------------------|--------------------|----------------------------------|
| `tofu/hetzner/`     | hcloud             | VMs, networks, firewalls, LB     |
| `tofu/talos/`       | talos              | Machine config, cluster bootstrap |
| `tofu/netbird/`     | netbird            | NetBird API setup keys           |
| `tofu/kubernetes/`  | kubernetes         | Bootstrap Kubernetes secrets     |

Cross-module data is shared via `terraform_remote_state` data sources.
Apply order: hetzner -> talos -> netbird -> kubernetes.

## Consequences

- Each module has independent state and can be applied in isolation.
- Credentials are scoped: only the hetzner module needs the Hetzner token,
  only netbird needs the NetBird PAT, etc.
- Talos upgrades and machine config changes do not touch infrastructure state.
- Cross-module dependencies are explicit via `terraform_remote_state`.
- Operators must apply modules in the correct order during initial bootstrap.
- Adding a new provider group means adding a new root module rather than
  expanding an existing one.
