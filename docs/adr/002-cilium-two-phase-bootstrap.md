# ADR-002: Cilium two-phase bootstrap

## Status

Accepted

## Context

Talos Linux ships without a default CNI. Pods (including FluxCD) cannot
schedule until a CNI is installed. FluxCD itself is deployed as pods, creating
a chicken-and-egg problem: Flux cannot install Cilium because Flux needs Cilium
to run.

## Decision

Bootstrap Cilium in two phases:

1. **Day-0 (manual):** Run `cilium install` from a local workstation against
   the freshly provisioned cluster. This gets the CNI running so that pods can
   schedule.

2. **Day-2 (FluxCD):** A `HelmRelease` in `infrastructure/controllers/`
   adopts the existing Cilium installation and manages its lifecycle going
   forward (upgrades, value changes).

Talos-specific capabilities are set in the HelmRelease values to satisfy
Cilium's requirements on Talos (e.g., `securityContext.capabilities`
for the agent DaemonSet).

## Consequences

- The cluster is functional immediately after day-0 without waiting for a full
  GitOps reconciliation loop.
- FluxCD takes ownership of Cilium on its first reconciliation, so manual
  drift is corrected automatically.
- A manual step is required during initial cluster provisioning; this is
  documented in the bootstrap procedure.
- Cilium version must be kept in sync between the CLI install and the
  HelmRelease to avoid unexpected upgrades on first Flux reconciliation.
