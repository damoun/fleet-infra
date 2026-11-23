# imap-mcp requires Node 24; karakeep-mcp stays on 22.
FROM docker.io/library/node:24-bookworm-slim@sha256:dc26ae92c9fb15cf6b1d63e20f0944b2efe0f115b20e00be48fb23fceb061c54

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
