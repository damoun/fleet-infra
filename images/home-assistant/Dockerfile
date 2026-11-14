FROM ghcr.io/home-assistant/home-assistant:2026.11.0@sha256:c6c1ca9931036bf3a2c4cc088d8db25dfea3b33935a5ecc83c40349462e2f69e

RUN apk upgrade --no-cache

# Home Assistant only loads custom components from /config; the init container
# copies this into place on every start. Bump the checksum with the version.
# renovate: datasource=github-releases depName=christiaangoossens/hass-oidc-auth
ADD --checksum=sha256:e5badaaacaa63cfd6fe733924a05e76d75058836190398598fb24de57cd47ccd https://github.com/christiaangoossens/hass-oidc-auth/releases/download/v1.2.1/hass-oidc-auth.zip /tmp/auth_oidc.zip
RUN unzip -q /tmp/auth_oidc.zip -d /opt/custom_components/auth_oidc \
    && rm /tmp/auth_oidc.zip
