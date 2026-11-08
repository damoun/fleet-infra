FROM nousresearch/hermes-agent:v0.22.7@sha256:e6d81ae52ebf6a43efa529701405509f20054ba818f179ddd748bed4f8af584c

# The browser tools that drive the camofox pod left Hermes core for the camofox
# catalog plugin, which Hermes would otherwise clone into the home at runtime.
# Bake it into the bundled plugin dir at the commit the base image's catalog
# pins; the build fails once the catalog moves to another commit.
ARG CAMOFOX_PLUGIN_SHA=1138f25c8b7b5a8fb882b3161e248f29abbd1a46
ADD https://github.com/NousResearch/hermes-official-plugins.git#${CAMOFOX_PLUGIN_SHA}:camofox /opt/hermes/plugins/camofox
RUN grep -qx "sha: ${CAMOFOX_PLUGIN_SHA}" /opt/hermes/plugin-catalog/camofox.yaml \
    && rm -rf /opt/hermes/plugins/camofox/tests

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

# The pod runs Hermes directly as the image's hermes user, bypassing the s6
# init that needs root.
USER 10000:10000
