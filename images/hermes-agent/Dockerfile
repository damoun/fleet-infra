FROM nousresearch/hermes-agent:v0.23.0@sha256:adb7890916de63245523492be8f68f9d2095fecbec4e2a6dab7960381f0fc002

# The browser tools that drive the camofox pod left Hermes core for the camofox
# catalog plugin, which Hermes would otherwise clone into the home at runtime.
# Bake it into the bundled plugin dir at the commit the base image's catalog
# pins, so a base image bump carries the plugin with it. Its pyproject only
# declares dependencies the venv already has; Hermes would still count it as a
# venv member and warn at every start that the sealed venv needs a rebuild, so
# the build checks each dependency against the venv and drops the file.
RUN set -eu; \
    catalog=/opt/hermes/plugin-catalog/camofox.yaml; \
    repo=$(sed -n 's/^repo: //p' "$catalog"); \
    sha=$(sed -n 's/^sha: //p' "$catalog"); \
    subdir=$(sed -n 's/^subdir: //p' "$catalog"); \
    echo "$sha" | grep -qxE '[0-9a-f]{40}'; \
    git init -q /tmp/plugin; \
    git -C /tmp/plugin fetch -q --depth 1 "$repo" "$sha"; \
    git -C /tmp/plugin -c advice.detachedHead=false checkout -q FETCH_HEAD; \
    cp -r "/tmp/plugin/$subdir" /opt/hermes/plugins/camofox; \
    /opt/hermes/.venv/bin/python -c 'import sys, tomllib; from importlib.metadata import version; from packaging.requirements import Requirement; reqs = [Requirement(s) for s in tomllib.load(open(sys.argv[1], "rb"))["project"].get("dependencies", [])]; bad = [str(r) for r in reqs if not r.specifier.contains(version(r.name), prereleases=True)]; sys.exit(f"venv does not satisfy {bad}" if bad else 0)' /opt/hermes/plugins/camofox/pyproject.toml; \
    rm -rf /opt/hermes/plugins/camofox/tests /opt/hermes/plugins/camofox/pyproject.toml /tmp/plugin; \
    echo "camofox plugin: $repo@$sha"

# browser_exec runs model-written Python in the gateway through the Browser Use
# harness. Config keeps it off; removing the harness leaves nothing to run even
# if a stale session still dispatches it. Hermes only imports it lazily.
RUN rm -rf /opt/hermes/.venv/lib/python3.*/site-packages/browser_harness \
        /opt/hermes/.venv/lib/python3.*/site-packages/browser_harness-*.dist-info \
        /opt/hermes/.venv/bin/browser-harness \
        /opt/hermes/.venv/bin/browser-harness-mcp

# signal-cli runs in its own pod and cannot open the gateway's file paths;
# send attachments as data URIs. The script fails the build if the adapter
# code it rewrites has moved.
COPY signal-data-uri.py /tmp/signal-data-uri.py
RUN python3 /tmp/signal-data-uri.py /opt/hermes/plugins/platforms/signal/adapter.py \
    && rm /tmp/signal-data-uri.py

RUN apt-get update \
    && apt-get upgrade --yes \
    && rm -rf /var/lib/apt/lists/*

# The pod runs Hermes directly as the image's hermes user, bypassing the s6
# init that needs root.
USER 10000:10000
