FROM debian:trixie-slim@sha256:a72b4433de1cf7d6bae0c4cee74d0547f58601a643b3375f070c51600d63b6b2

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        git \
        jq \
        less \
        openssh-server \
        procps \
        python3 \
        python3-pymupdf \
        python3-pypdf \
        python3-reportlab \
        python3-venv \
        ripgrep \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 10001 --create-home --shell /bin/bash agent

# Skill dependencies Debian doesn't package, hash-pinned. The venv also sees the
# apt packages above, and the skills call `python`, so its interpreter goes on
# the default SSH PATH through /usr/local/bin. Wrappers, not symlinks: Python
# only detects the venv from the path it is invoked through.
COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv --system-site-packages /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt \
    && for name in python python3; do \
        printf '#!/bin/sh\nexec /opt/venv/bin/python "$@"\n' >/usr/local/bin/$name \
        && chmod 0755 /usr/local/bin/$name; \
    done

COPY sshd_config /etc/ssh/sshd_config
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY idle-wipe.sh /usr/local/bin/idle-wipe.sh

USER 10001
WORKDIR /home/agent
EXPOSE 2222
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
