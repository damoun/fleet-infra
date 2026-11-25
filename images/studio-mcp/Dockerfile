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
# Brand display font (SIL OFL, licence shipped alongside), pinned to a google/fonts commit with
# no Renovate tracking: it is static. Ship it unmodified; subsetting would need a renamed font.
ADD --chmod=644 --checksum=sha256:f5b641c45c69d772ee4eda687bc9fda411d5cad6b0b45371491da4580cbc8d59 https://raw.githubusercontent.com/google/fonts/90abd17b4f97671435798b6147b698aa9087612f/ofl/lilitaone/LilitaOne-Regular.ttf /usr/local/share/fonts/lilitaone/LilitaOne-Regular.ttf
ADD --chmod=644 --checksum=sha256:255d5debbb80eb2ea762644311f266a279e8778f00156655a516e2b7781a63e1 https://raw.githubusercontent.com/google/fonts/90abd17b4f97671435798b6147b698aa9087612f/ofl/lilitaone/OFL.txt /usr/local/share/fonts/lilitaone/OFL.txt
# ADD creates the directory root-only; uid 1000 must traverse it.
RUN chmod 755 /usr/local/share/fonts/lilitaone
COPY --from=build /app/.venv /app/.venv
COPY src /app/src
ENV PATH=/app/.venv/bin:$PATH PYTHONPATH=/app/src PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
USER 1000:1000
EXPOSE 8000
ENTRYPOINT ["python", "-m", "studio_mcp.server"]
