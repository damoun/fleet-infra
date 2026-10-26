# Kubernetes Hardening

Where `dapl-prd-hom-ams-core` stands against the NSA/CISA Kubernetes Hardening Guide and the ANSSI container recommendations. Talos covers a lot of the node layer by default, so this only lists what the repo decides.

## In Place

### Pod security

| Control                                                                                        | Where                                                                                                                             |
| ---------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| PSA `restricted` (enforce, audit, warn) on `cert-manager`, `cnpg-system`, `default`, `edge`, `id`, `o11y` | `infrastructure/controllers/namespace-*.yaml`, `infrastructure/configs/namespace-edge.yaml`, `apps/base/pocket-id/namespace.yaml` |
| PSA `restricted` on `kubelet-serving-cert-approver`                                            | upstream manifest                                                                                                                 |
| Images pinned by digest, denied otherwise (Talos control-plane tags excepted in `kube-system`) | `infrastructure/prereqs/vap-image-digest.yaml`                                                                                    |
| Memory limits on every container outside `kube-system`, denied otherwise                       | `infrastructure/prereqs/vap-memory-limits.yaml`                                                                                   |
| Chart without securityContext values patched to `restricted`                                   | `infrastructure/controllers/cert-manager-webhook-bunny.yaml` (postRenderer)                                                       |
| No service account token where the API is not used                                             | `apps/base/pocket-id/deployment.yaml`                                                                                             |

Both admission policies run as `[Deny, Audit]`.

### Network separation

| Control                                                                                    | Where                                              |
| ------------------------------------------------------------------------------------------ | -------------------------------------------------- |
| Default deny for every pod outside `kube-system`, egress limited to DNS and the API server | `infrastructure/prereqs/ccnp-default-deny.yaml`    |
| Per-workload allow rules                                                                   | `netpol-*.yaml`, `apps/base/pocket-id/netpol.yaml` |
| Pod-to-pod encryption with WireGuard                                                       | `infrastructure/controllers/cilium.yaml`           |
| No public ingress, everything through NetBird                                              | [netbird-dns.md](netbird-dns.md)                   |
| Gateway `gw` accepts routes only from `flux-system`, `id`, `o11y`                          | `infrastructure/configs/gateway-gw.yaml`           |

### Supply chain

| Control                                            | Where                               |
| -------------------------------------------------- | ----------------------------------- |
| Cosign keyless verification on every OCIRepository | `infrastructure/sources/oci-*.yaml` |
| Git sources pinned by commit                       | `infrastructure/sources/git-*.yaml` |
| Trivy scans every running image and the manifests  | `.github/workflows/trivy.yml`       |

The bunny chart is signed by the shared `upcloud-tools/gha-actions` workflow. Flux can only match the certificate subject, which names that workflow and not the calling repo. So the signature proves the chart came from a full-SHA-pinned run of that workflow, and the `ghcr.io/aardbol` namespace plus the digest pin do the rest.

Every image the cluster runs follows from a version pinned in the repo. Flux-managed images are written out as `tag@sha256`. Cilium and the Flux controllers come from their pinned chart and distribution versions, which pin by digest. The Talos control plane runs Talos's tags for `kubernetes_version`. `.github/scripts/images.sh` derives the full list for Trivy.

### Threat detection

Falco runs on every node with the modern eBPF driver and its default rules (`infrastructure/controllers/falco.yaml`). Events go to stdout as JSON, vlagent ships them to VictoriaLogs, and the `FalcoEvent` VMRule pages through Alertmanager for Warning and above. Notice events stay in VictoriaLogs.

### Node

Secure Boot with a UKI, TPM-sealed LUKS2 on STATE and EPHEMERAL, and LUKS2 on worker data volumes (`tofu/baremetal/main.tf`).

## Accepted Exceptions

| What                                                                          | Why                                                                                                               |
| ----------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `netbird` is `privileged`                                                     | `rtr` runs as root with NET_ADMIN, NET_RAW and BPF. Kubernetes only makes added capabilities effective for UID 0. |
| `o11y-node` is `privileged`                                                   | node-exporter and vlagent read the host.                                                                          |
| `falco` is `privileged`                                                       | The eBPF probe needs privileged access to the host kernel.                                                         |
| `local-path-storage` is `privileged`                                          | Helper pods use hostPath and keep DAC_OVERRIDE and FOWNER for teardown.                                           |
| `kube-system` has no PSA and no default deny                                  | Talos exempts it. Cilium, CoreDNS and the control plane live there.                                               |
| `flux-system` keeps the Talos default (enforce `baseline`, warn `restricted`) | tofu and flux-operator already co-own the namespace. A third owner through Flux would risk pruning it.            |

## Deferred

These need `tofu/baremetal` or bigger changes, and are not done yet:

- API server audit policy, and shipping `/var/log/audit/kube` off the nodes.
- Explicit kubelet hardening (`readOnlyPort`, `protectKernelDefaults`, `seccompDefault`, TLS ciphers) instead of relying on Talos defaults.
- Talos host firewall for apid, kubelet and etcd. Today they are reachable from all of VLAN 40.
- OIDC for kubectl. Admin access is a shared client certificate.
- `w-ofph` and `w-jsai` encrypt with the nodeID key provider (TPM 1.2 only), which does not protect against physical access.
- `tofu/baremetal` state, which holds machine secrets, the talosconfig and the admin kubeconfig, is unencrypted on disk.
- Flux multi-tenancy lockdown. The controllers run as cluster-admin and nothing impersonates a narrower service account.
