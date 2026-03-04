# ADR-006: Hetzner-native NTP and DNS

## Status

Accepted

## Context

Talos nodes need NTP for time synchronization and DNS for name resolution.
Using public services (e.g., `pool.ntp.org`, `1.1.1.1`) adds external
dependencies and higher latency compared to Hetzner's own infrastructure
services that are available to all Hetzner Cloud VMs.

## Decision

Configure Talos machine config to use Hetzner-native services:

**NTP servers:**
- `ntp1.hetzner.de`
- `ntp2.hetzner.com`
- `ntp3.hetzner.net`

**DNS resolvers:**
- `185.12.64.1`
- `185.12.64.2`

These are Hetzner's anycast recursive resolvers, available from within the
Hetzner network.

## Consequences

- Lower latency for time sync and DNS resolution (same datacenter network).
- No external dependency for basic infrastructure services.
- If the cluster is migrated away from Hetzner, these values must be updated
  in the Talos machine config.
