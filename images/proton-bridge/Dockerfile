FROM golang:1.26.7-trixie@sha256:978084e7adea0904b6d76cbc9afcb9baeed6ee170eecdc8866566aaa9f22ad0c AS build

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libcbor-dev \
        libfido2-dev \
        libsecret-1-dev \
        libssl-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

# renovate: datasource=github-tags depName=ProtonMail/proton-bridge tag=v3.27.1
ADD https://github.com/ProtonMail/proton-bridge.git#43b9237786204a0215abfd4dcc51ee7bb92f52d4 /src
WORKDIR /src

# The headless binary only, without the Makefile's self-updating launcher.
ENV GOTOOLCHAIN=local CGO_ENABLED=1 CGO_LDFLAGS="-lfido2 -lcbor -lssl -lcrypto"
RUN (cd utils && bash credits.sh bridge) \
    && version=$(sed -n 's/^BRIDGE_APP_VERSION?=//p' Makefile) \
    && go build -trimpath \
        -ldflags "-X github.com/ProtonMail/proton-bridge/v3/internal/constants.Version=${version} -X 'github.com/ProtonMail/proton-bridge/v3/internal/constants.FullAppName=Proton Mail Bridge'" \
        -o /out/bridge ./cmd/Desktop-Bridge

FROM debian:trixie-slim@sha256:8aa5a7bf5a1955bddbe7d74fcdd0b91ab30e74362a8b73af672b0481b35b44a0

# pass and gnupg hold the vault key; socat exposes the loopback-only IMAP port.
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        gnupg \
        libfido2-1 \
        libsecret-1-0 \
        pass \
        socat \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /out/bridge /usr/local/bin/bridge

USER 1000:1000
