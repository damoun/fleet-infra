# Forgejo Break-Glass

Forgejo at `git.core.ams.damoun.casa` keeps pull mirrors of the GitHub repos. When GitHub is down, a mirror becomes the writable copy and Flux can sync from it. Normal operation never touches any of this.

Pushing over HTTPS needs a Forgejo access token, since accounts log in through Pocket ID. The `breakglass` local admin (password in `apps/base/forgejo/admin-secret.yaml`) covers the case where Pocket ID is down too.

Flux reads Forgejo with the `forgejo-pull` Secret in `flux-system` (`infrastructure/configs/forgejo-pull.yaml`): `damoun` plus a `read:repository` token named `flux-pull`. It sits unused until step 3.

## During the Outage

1. In Forgejo, open the repo, then Settings, Danger Zone, **Convert to regular repository**. This is one-way: the repo stops mirroring.
2. Add the remote and push your work there:
   ```bash
   git remote add forgejo https://git.core.ams.damoun.casa/damoun/fleet-infra.git
   ```
3. To let Flux deploy from Forgejo, point the sync at the in-cluster Service. Do it in Git first, otherwise `infra-configs` re-applies the GitHub URL from the last artifact:
   ```yaml
   # infrastructure/configs/flux-instance.yaml
   sync:
     url: http://forgejo-http.forgejo.svc.cluster.local:3000/damoun/fleet-infra.git
     pullSecret: forgejo-pull
   ```
   Commit and push to `forgejo`. Suspend `infra-configs` so it cannot re-apply the old artifact, patch the live object to match, and resume once Flux has fetched the Forgejo revision:
   ```bash
   flux --context admin@dapl-prd-hom-ams-core suspend kustomization infra-configs
   kubectl --context admin@dapl-prd-hom-ams-core -n flux-system patch fluxinstance flux --type merge \
     -p '{"spec":{"sync":{"url":"http://forgejo-http.forgejo.svc.cluster.local:3000/damoun/fleet-infra.git","pullSecret":"forgejo-pull"}}}'
   flux --context admin@dapl-prd-hom-ams-core get sources git flux-system
   flux --context admin@dapl-prd-hom-ams-core resume kustomization infra-configs
   ```
4. Keep working against `forgejo`.

## Recovery

1. Revert the sync change from step 3. If GitHub's `main` moved during the outage, merge `origin/main` first.
2. Push `main` to `origin`, then to `forgejo`. Flux reads the revert from Forgejo and switches back to GitHub, which already has the same commit.
3. Delete the converted repo in Forgejo and create the pull mirror again.
