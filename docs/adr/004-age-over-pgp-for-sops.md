# ADR-004: age over PGP for SOPS encryption

## Status

Accepted

## Context

The repository previously used PGP (GnuPG) for SOPS encryption. PGP requires
a GPG agent, keyring management, and a full GPG toolchain on every machine
that decrypts secrets. Talos Linux nodes do not ship GPG, and the FluxCD
SOPS controller recommends age as the simpler alternative.

The old PGP key (`8BC21F9620077AD4B9BD97EF5C350D68F61028B3`) was tied to the
retired home cluster and is no longer in use.

## Decision

Use [age](https://age-encryption.org/) instead of PGP for all SOPS-encrypted
secrets:

- Generate an age key pair locally with `age-keygen`.
- Store the private key (`AGE-SECRET-KEY-...`) in ProtonPass for disaster
  recovery.
- Provision the private key into the cluster as a Kubernetes secret
  (`sops-age` in `flux-system`) via OpenTofu.
- Configure FluxCD Kustomizations with `spec.decryption.provider: sops` and a
  `secretRef` pointing to `sops-age`.
- Update `.sops.yaml` to reference the age public key.

## Consequences

- No GPG toolchain required on developer machines or cluster nodes.
- Key management is a single file rather than a keyring.
- FluxCD decryption works out of the box on Talos without additional
  system packages.
- The old `.sops.pub.asc` PGP public key file is deleted.
- Existing SOPS-encrypted files (if any) must be re-encrypted with the new
  age key.
