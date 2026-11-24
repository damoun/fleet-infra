FROM docker.io/library/node:24-bookworm-slim@sha256:dc26ae92c9fb15cf6b1d63e20f0944b2efe0f115b20e00be48fb23fceb061c54

# The filesystem server only speaks stdio; supergateway serves it as Streamable
# HTTP on :8000/notes/mcp, started without a shell from supergateway.json.
WORKDIR /app
COPY package.json package-lock.json supergateway.json ./
RUN npm ci --omit=dev --ignore-scripts --no-audit --no-fund \
    && npm cache clean --force \
    && rm -rf /usr/local/lib/node_modules/npm /usr/local/bin/npm /usr/local/bin/npx

# The uid that owns the synced vault files.
USER 10001:10001
EXPOSE 8000
ENTRYPOINT ["/app/node_modules/.bin/supergateway", "--config", "/app/supergateway.json"]
