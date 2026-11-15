# Forgejo Break-Glass

Forgejo at `git.core.ams.damoun.casa` keeps pull mirrors of the GitHub repos. When GitHub is down, a mirror becomes the writable copy and Flux can sync from it. Normal operation never touches any of this.

Pushing over HTTPS needs a Forgejo access token, since accounts log in through Pocket ID. The `breakglass` local admin (password in `apps/base/forgejo/admin-secret.yaml`) covers the case where Pocket ID is down too.

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
   Commit, push to `forgejo`, then patch the live object to match:
   ```bash
   kubectl --context admin@dapl-prd-hom-ams-core -n flux-system patch fluxinstance flux --type merge \
     -p '{"spec":{"sync":{"url":"http://forgejo-http.forgejo.svc.cluster.local:3000/damoun/fleet-infra.git","pullSecret":"forgejo-pull"}}}'
   ```
4. Keep working against `forgejo`.

## Recovery

1. Revert the sync change from step 3. If GitHub's `main` moved during the outage, merge `origin/main` first.
2. Push `main` to `origin`, then to `forgejo`. Flux reads the revert from Forgejo and switches back to GitHub, which already has the same commit.
3. Delete the converted repo in Forgejo and create the pull mirror again.
