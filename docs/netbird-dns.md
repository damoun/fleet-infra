# NetBird Private Access

Every ingress to `dapl-prd-hom-ams-core` goes through NetBird, including from the home LAN. Private names exist only in NetBird DNS; public DNS has nothing for them.

## Naming Convention

Pattern: `<service>.<cluster>.<location>.<domain>`, every label we choose at most 4 characters.

| Name                            | Resolves to   | Target                                          |
| ------------------------------- | ------------- | ----------------------------------------------- |
| `*.core.ams.damoun.casa`        | `172.28.0.10` | Cilium Gateway `gw` (namespace `edge`)          |
| `kube.core.ams.damoun.internal` | `172.24.0.1`  | `kubernetes` Service (kube-apiserver), port 443 |

`damoun.casa` is a public domain, so services get Let's Encrypt certificates (DNS-01 through Bunny, wildcard `*.core.ams.damoun.casa`). The kube API keeps `damoun.internal`, which is in the Talos certSANs.

## Architecture

```
NetBird client ── NetBird DNS (A records) ── WireGuard ── rtr pods (netbird ns) ── 172.28.0.10:443 → Gateway gw → HTTPRoutes
                                                                                └─ 172.24.0.1:443  → kube-apiserver
```

- `172.28.0.10` comes from the Cilium LB pool `priv` (`172.28.0.0/28`), selected by the label `lb.damoun.casa/pool: priv`. The LAN pool and the L2 announcement policy exclude that label, so the VIP is never announced on VLAN 40 and only in-cluster clients (the routers) reach it.
- Routing peers are plain NetBird clients (Deployment `rtr`, 2 replicas) joining with a reusable, ephemeral setup key. Each pod is a new peer; dead ones drop out on their own.

## IaC Mapping

| Resource                                        | Managed By             | Location                                                              |
| ----------------------------------------------- | ---------------------- | --------------------------------------------------------------------- |
| Groups, policies, network, resources, setup key | OpenTofu via Spacelift | `damoun/terraform` `stacks/netbird`                                   |
| DNS zones and records                           | OpenTofu via Spacelift | `damoun/terraform` `stacks/netbird/dns.tf`                            |
| CAA on `damoun.casa`                            | OpenTofu via Spacelift | `damoun/terraform` `stacks/bunny-dns`                                 |
| Routing peers, setup key Secret, network policy | Flux                   | `infrastructure/controllers/netbird-rtr*.yaml`, `netpol-netbird.yaml` |
| LB pool `priv`, L2 policy                       | Flux                   | `infrastructure/prereqs/`                                             |
| Gateway `gw`, wildcard Certificate              | Flux                   | `infrastructure/configs/`                                             |

## Adding a service

Attach an `HTTPRoute` to `gw` (namespace `edge`) with a hostname under `*.core.ams.damoun.casa`. No DNS change is needed. Once default-deny is enforced, the backend also needs an ingress allow from entity `ingress`.
