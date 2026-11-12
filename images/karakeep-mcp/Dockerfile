FROM docker.io/library/node:22-bookworm-slim@sha256:e9f565d32859f0cbfb52125eafe8be39390f24dac302dc3cdf566e8ba3ab21ee

# Karakeep's MCP server only speaks stdio; supergateway serves it as
# Streamable HTTP on :8000/mcp.
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts --no-audit --no-fund \
    && npm cache clean --force

USER 1000:1000
EXPOSE 8000
ENTRYPOINT ["/app/node_modules/.bin/supergateway", \
    "--stdio", "/app/node_modules/.bin/karakeep-mcp", \
    "--outputTransport", "streamableHttp", "--stateful", "--sessionTimeout", "900000", \
    "--port", "8000", "--healthEndpoint", "/healthz"]
