FROM docker.io/library/node:24.22.3-bookworm-slim@sha256:873f586f3794f52281bd039bf02c048a0be08fde619338f9941bad1eb6b34530

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
