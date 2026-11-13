FROM ghcr.io/jo-inc/camofox-browser:1.18.1@sha256:cff2c1432b609bde9c9d0b91e5b924dae0799d3c7bc9d468c0bc949325beaf2a

USER root
RUN apt-get update \
    && apt-get upgrade --yes \
    && rm -rf /var/lib/apt/lists/*

# The base image keeps the Camoufox bundle under /root (0700), out of reach of
# a non-root user.
RUN mv /root/.cache/camoufox /opt/camoufox
ENV CAMOUFOX_EXECUTABLE=/opt/camoufox/camoufox-bin
USER 10001:10001
