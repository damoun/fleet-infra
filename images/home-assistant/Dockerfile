FROM ghcr.io/home-assistant/home-assistant:2026.11.2@sha256:493a07e8f6530fc640223f4a0a5248f20a61ca2f718bb1d31efbf08a2c5ea28f

RUN apk upgrade --no-cache

# Home Assistant only loads custom components from /config; the init container
# copies this into place on every start. Bump the checksum with the version.
# renovate: datasource=github-releases depName=christiaangoossens/hass-oidc-auth
ADD --checksum=sha256:e5badaaacaa63cfd6fe733924a05e76d75058836190398598fb24de57cd47ccd https://github.com/christiaangoossens/hass-oidc-auth/releases/download/v1.2.1/hass-oidc-auth.zip /tmp/auth_oidc.zip
RUN mkdir -p /opt/custom_components/auth_oidc \
    && unzip -q /tmp/auth_oidc.zip -d /opt/custom_components/auth_oidc \
    && rm /tmp/auth_oidc.zip
