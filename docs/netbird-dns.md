# NetBird Internal DNS

## Naming Convention

Pattern: `<service>.<cluster>.<location>.damoun.internal`

| Segment    | Description                            | Examples                |
| ---------- | -------------------------------------- | ----------------------- |
| `service`  | Service name                           | `kube`, `api`, `db`     |
| `cluster`  | Cluster role                           | `tools`, `data`, `mgmt` |
| `location` | Site identifier (city/datacenter code) | `fsn`, `nbg`, `ams`     |

### Examples

| FQDN                             | Description                          |
| -------------------------------- | ------------------------------------ |
| `kube.tools.fsn.damoun.internal` | Kube API, tools cluster, Falkenstein |
| `kube.data.nbg.damoun.internal`  | Kube API, data cluster, Nuremberg    |
| `kube.tools.ams.damoun.internal` | Kube API, tools cluster, Amsterdam   |

## Architecture

### DNS Zone

A NetBird Custom DNS Zone (`tools.fsn.damoun.internal`) is configured via Terraform in `tofu/netbird/`.
DNS records within this zone resolve through the NetBird network for all peers in the distribution groups.

### IaC Mapping

| Resource    | Managed By                       | Location                      |
| ----------- | -------------------------------- | ----------------------------- |
| NBResource  | Kubernetes CRD                   | `infrastructure/controllers/` |
| NBPolicy    | Kubernetes CRD                   | `infrastructure/controllers/` |
| NBGroup     | Kubernetes CRD                   | `infrastructure/controllers/` |
| DNS Zone    | Terraform (`netbird_dns_zone`)   | `tofu/netbird/`               |
| DNS Records | Terraform (`netbird_dns_record`) | `tofu/netbird/`               |

### Why Direct IPs in NBResource

The NBResource `address` field uses direct IPs (e.g., `172.16.16.5/32`) instead of hostnames because:

- macOS mDNS intercepts `.local` domains, breaking resolution of `*.svc.cluster.local` addresses
- Direct IP routing through NetBird avoids DNS resolution entirely at the network resource level
- DNS names (`kube.tools.fsn.damoun.internal`) are provided separately via NetBird Custom DNS Zones

### Round-Robin DNS

Three DNS A records point `kube.tools.fsn.damoun.internal` to the three control plane IPs (`172.16.16.5`, `172.16.16.6`, `172.16.16.7`), providing basic load distribution and redundancy.
