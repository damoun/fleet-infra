# NetBird Internal DNS

## Naming Convention

Pattern: `<service>.<cluster>.<location>.damoun.internal`

| Segment    | Description                            | Examples              |
| ---------- | -------------------------------------- | --------------------- |
| `service`  | Service name                           | `kube`, `api`, `db`   |
| `cluster`  | Cluster role                           | `app`, `data`, `mgmt` |
| `location` | Site identifier (city/datacenter code) | `fsn`, `nbg`, `ams`   |

### Examples

| FQDN                            | Description                        |
| ------------------------------- | ---------------------------------- |
| `kube.app.fsn.damoun.internal`  | Kube API, app cluster, Falkenstein |
| `kube.data.nbg.damoun.internal` | Kube API, data cluster, Nuremberg  |
| `kube.app.ams.damoun.internal`  | Kube API, app cluster, Amsterdam   |

## Architecture

### DNS Zone

A NetBird Custom DNS Zone (`damoun.internal`) is configured via Terraform in `tofu/netbird/`.
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

The NBResource `address` field uses direct IPs (e.g., `172.16.16.7/32`) instead of hostnames because:

- macOS mDNS intercepts `.local` domains, breaking resolution of `*.svc.cluster.local` addresses
- Direct IP routing through NetBird avoids DNS resolution entirely at the network resource level
- DNS names (`kube.app.fsn.damoun.internal`) are provided separately via NetBird Custom DNS Zones
