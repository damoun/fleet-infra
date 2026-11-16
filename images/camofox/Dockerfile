FROM ghcr.io/jo-inc/camofox-browser:1.19.0@sha256:49f8e02f9fb0e191b406845482745efc72f835db06789e3a34e77a6ff1497046

USER root
RUN apt-get update \
    && apt-get upgrade --yes \
    && rm -rf /var/lib/apt/lists/*

# The base image keeps the Camoufox bundle under /root (0700), out of reach of
# a non-root user.
RUN mv /root/.cache/camoufox /opt/camoufox
ENV CAMOUFOX_EXECUTABLE=/opt/camoufox/camoufox-bin
USER 10001:10001
