FROM ghcr.io/astral-sh/uv:0.13.4@sha256:9f130421e930bfbdc563c00740466603f8723158e90297d07957c2294640262b AS uv

FROM docker.io/library/python:3.12-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df AS build
COPY --from=uv /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
ADD https://github.com/rldiao/mealie-mcp-server.git#86ebf379536cf2b3a07c2007798db02894c51f21 /app
WORKDIR /app
# Upstream uv.lock pins vulnerable versions.
RUN uv lock \
        --upgrade-package 'mcp==1.30.0' \
        --upgrade-package 'starlette==1.10.0' \
        --upgrade-package 'python-multipart==0.0.33' \
        --upgrade-package 'anyio==4.16.0' \
        --upgrade-package 'certifi==2026.10.23' \
    && uv sync --locked --no-dev

FROM docker.io/library/python:3.12-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df
COPY --from=build /app/.venv /app/.venv
COPY --from=build /app/src /app/src
ENV PATH=/app/.venv/bin:$PATH PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    MCP_TRANSPORT=streamable-http MCP_HOST=0.0.0.0 MCP_PORT=8765
WORKDIR /app
USER 1000:1000
EXPOSE 8765
ENTRYPOINT ["python", "src/server.py"]
