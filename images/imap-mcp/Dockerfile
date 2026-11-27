# imap-mcp requires Node 24; karakeep-mcp stays on 22.
FROM docker.io/library/node:24.22.3-bookworm-slim@sha256:873f586f3794f52281bd039bf02c048a0be08fde619338f9941bad1eb6b34530

# imap-mcp only speaks stdio; supergateway serves it as Streamable HTTP on
# :8000/mcp. The npm package carries SLSA provenance from its release tag.
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts --no-audit --no-fund \
    && npm cache clean --force \
    && rm -rf /usr/local/lib/node_modules/npm /usr/local/bin/npm /usr/local/bin/npx

USER 1000:1000
EXPOSE 8000
# supergateway's default level logs every message in full, mail included.
ENTRYPOINT ["/app/node_modules/.bin/supergateway", \
    "--stdio", "/app/node_modules/.bin/imap-mcp", \
    "--outputTransport", "streamableHttp", "--stateful", "--sessionTimeout", "900000", \
    "--port", "8000", "--healthEndpoint", "/healthz", "--logLevel", "none"]
