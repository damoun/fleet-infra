FROM ghcr.io/astral-sh/uv:0.13.9@sha256:d3b601f0c7b118bc1753febf7c41cc80981df678445e0254284eecf84db79a7d AS uv

FROM docker.io/library/python:3.13-slim-bookworm@sha256:f0fa218d5b06f9b9235024fa061cde2cb141f726de52134471053d2d9b5324a3 AS build
COPY --from=uv /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

FROM docker.io/library/python:3.13-slim-bookworm@sha256:f0fa218d5b06f9b9235024fa061cde2cb141f726de52134471053d2d9b5324a3 AS typst
RUN apt-get update && apt-get install -y --no-install-recommends xz-utils \
    && rm -rf /var/lib/apt/lists/*
# renovate: datasource=github-releases depName=typst/typst
ADD --checksum=sha256:a6d077d0a95eed5a2eba715b2dae06be954f624ccbf85758a03f389ded33118c https://github.com/typst/typst/releases/download/v0.15.1/typst-x86_64-unknown-linux-musl.tar.xz /tmp/typst.tar.xz
RUN tar -xJf /tmp/typst.tar.xz --strip-components=1 -C /usr/local/bin typst-x86_64-unknown-linux-musl/typst

FROM docker.io/library/python:3.13-slim-bookworm@sha256:f0fa218d5b06f9b9235024fa061cde2cb141f726de52134471053d2d9b5324a3
# ffmpeg carries libzimg (zscale) for HDR tonemapping.
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg fonts-inter \
    && rm -rf /var/lib/apt/lists/*
COPY --from=typst /usr/local/bin/typst /usr/local/bin/typst
COPY --from=build /app/.venv /app/.venv
COPY src /app/src
ENV PATH=/app/.venv/bin:$PATH PYTHONPATH=/app/src PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    HOME=/tmp
WORKDIR /app
USER 1000:1000
EXPOSE 8000
ENTRYPOINT ["python", "-m", "studio_mcp.server"]
