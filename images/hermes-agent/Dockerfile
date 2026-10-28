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
