FROM nousresearch/hermes-agent:v0.22.5@sha256:9c5561579f3ffdf333401797094ac3a743738d6c25d40f4331c7bf77b694238d

# The browser tools need agent-browser, which the published image leaves out,
# and lazy installs are off at runtime. A sealed image (manifest.json present)
# sends PM installs to $HERMES_HOME/tools, the /opt/data volume, where build
# output is discarded; hide the manifest for this step so agent-browser lands
# in the image store next to chromium. PM rewrites facts.json root-only; restore
# the base image's mode so the runtime user can read the store index.
# The version and tarball sha256 come from the base release's pm/lock.json.
RUN mv /opt/hermes/manifest.json /tmp/manifest.json \
    && python3 -c 'from pm import ensure; ensure("agent-browser", explicit=True)' \
    && mv /tmp/manifest.json /opt/hermes/manifest.json \
    && chmod 0644 /opt/hermes/tools/facts.json

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
