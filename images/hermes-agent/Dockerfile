FROM nousresearch/hermes-agent:v0.23.0@sha256:adb7890916de63245523492be8f68f9d2095fecbec4e2a6dab7960381f0fc002

# Catalog plugins Hermes would otherwise clone into the home at runtime: the
# browser tools that drive the camofox pod, and delegation to named profiles.
# Bake them into the bundled plugin dir at the commits the base image's catalog
# pins, so a base image bump carries them. A pyproject only declares
# dependencies the venv already has; Hermes would still count the plugin as a
# venv member and warn at every start that the sealed venv needs a rebuild, so
# the build checks each dependency against the venv and drops the file.
RUN set -eu; \
    for name in camofox advanced-delegation; do \
      catalog=/opt/hermes/plugin-catalog/$name.yaml; \
      repo=$(sed -n 's/^repo: //p' "$catalog"); \
      sha=$(sed -n 's/^sha: //p' "$catalog"); \
      subdir=$(sed -n 's/^subdir: //p' "$catalog"); \
      echo "$sha" | grep -qxE '[0-9a-f]{40}'; \
      git init -q /tmp/plugin; \
      git -C /tmp/plugin fetch -q --depth 1 "$repo" "$sha"; \
      git -C /tmp/plugin -c advice.detachedHead=false checkout -q FETCH_HEAD; \
      cp -r "/tmp/plugin/$subdir" "/opt/hermes/plugins/$name"; \
      if [ -f "/opt/hermes/plugins/$name/pyproject.toml" ]; then \
        /opt/hermes/.venv/bin/python -c 'import sys, tomllib; from importlib.metadata import version; from packaging.requirements import Requirement; reqs = [Requirement(s) for s in tomllib.load(open(sys.argv[1], "rb"))["project"].get("dependencies", [])]; bad = [str(r) for r in reqs if not r.specifier.contains(version(r.name), prereleases=True)]; sys.exit(f"venv does not satisfy {bad}" if bad else 0)' "/opt/hermes/plugins/$name/pyproject.toml"; \
      fi; \
      rm -rf "/opt/hermes/plugins/$name/tests" "/opt/hermes/plugins/$name/pyproject.toml" /tmp/plugin; \
      echo "$name plugin: $repo@$sha"; \
    done

# Push notifications for the Hermex app: hooks seal each preview with a key only
# the phone holds before posting it to the relay. Hermes loads bundled platform
# plugins lazily, which would leave the hooks unregistered, so the init installs
# this copy as a user plugin; one copy serves every profile.
# renovate: datasource=git-refs depName=https://github.com/uzairansaruzi/hermex-push tag=main
ADD https://github.com/uzairansaruzi/hermex-push.git#2da6f660bb86e9470ea56c85dc554aba45ce7fdf /tmp/hermex-push
RUN set -eu; \
    /opt/hermes/.venv/bin/python -c 'import sys, tomllib; from importlib.metadata import version; from packaging.requirements import Requirement; reqs = [Requirement(s) for s in tomllib.load(open(sys.argv[1], "rb"))["project"].get("dependencies", [])]; bad = [str(r) for r in reqs if not r.specifier.contains(version(r.name), prereleases=True)]; sys.exit(f"venv does not satisfy {bad}" if bad else 0)' /tmp/hermex-push/plugin/pyproject.toml; \
    cp -r /tmp/hermex-push/plugin /opt/hermex-push; \
    rm -rf /opt/hermex-push/hermex_push_tests /opt/hermex-push/pyproject.toml /tmp/hermex-push

# browser_exec runs model-written Python in the gateway through the Browser Use
# harness. Config keeps it off; removing the harness leaves nothing to run even
# if a stale session still dispatches it. Hermes only imports it lazily.
RUN rm -rf /opt/hermes/.venv/lib/python3.*/site-packages/browser_harness \
        /opt/hermes/.venv/lib/python3.*/site-packages/browser_harness-*.dist-info \
        /opt/hermes/.venv/bin/browser-harness \
        /opt/hermes/.venv/bin/browser-harness-mcp

RUN apt-get update \
    && apt-get upgrade --yes \
    && rm -rf /var/lib/apt/lists/*

# The pod runs Hermes directly as the image's hermes user, bypassing the s6
# init that needs root.
USER 10000:10000
