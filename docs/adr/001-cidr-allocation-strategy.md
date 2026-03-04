# ADR-001: CIDR allocation strategy

## Status

Accepted

## Context

The cluster needs non-overlapping CIDR ranges for nodes, pods, and services.
Many common ranges collide with corporate VPNs (`10.0.0.0/8`), Docker defaults
(`172.17.0.0/16` through `172.31.0.0/16`), and home networks (`192.168.0.0/16`).

We need a predictable allocation that avoids these collisions and leaves room
for future growth.

## Decision

All cluster networks are allocated under `172.16.0.0/12`, carved into `/20` or
`/16` blocks:

| Network          | CIDR              | Purpose             |
|------------------|-------------------|---------------------|
| Hetzner nodes    | `172.16.16.0/20`  | Node subnet         |
| Pod CIDR         | `172.20.0.0/16`   | Cilium pod network  |
| Service CIDR     | `172.24.0.0/16`   | Kubernetes services |

The node subnet (`172.16.16.0/24`) is further scoped inside the `/20` VPC
range to allow adding subnets later without re-addressing.

## Consequences

- Avoids collision with the most common private ranges used by VPNs, Docker,
  and home routers.
- All ranges fit inside `172.16.0.0/12`, making firewall rules and route
  summaries straightforward.
- Pod and service CIDRs are baked into Talos machine config at bootstrap;
  changing them later requires a full cluster rebuild.
