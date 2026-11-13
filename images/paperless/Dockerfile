FROM ghcr.io/paperless-ngx/paperless-ngx:3.4.2@sha256:d704e84f88300eb6ab001ab15720a2330ff99169cf9f94d6b8fcc44b63a84c84

# The image ships eng, fra, deu, ita and spa only; PAPERLESS_OCR_LANGUAGES
# installs more at startup, which needs root.
RUN apt-get update \
    && apt-get upgrade --yes \
    && apt-get install --yes --no-install-recommends tesseract-ocr-nld \
    && rm -rf /var/lib/apt/lists/*

# Fixed releases of Python packages the base image pins.
RUN pip install --no-cache-dir nltk==3.10.4 oauthlib==4.0.1

# Started as the image's paperless user, s6 skips its root-only init steps.
USER 1000:1000
