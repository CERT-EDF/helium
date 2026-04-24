# =============================================================================
# FUSION DIRECTIVES
# =============================================================================
# fusion:image=cert-edf/helium-be-hayabusa
# fusion:package=generaptor
# fusion:package=edf-fusion
# fusion:package=edf-helium-core
# fusion:package=edf-helium-server
# =============================================================================
# ENV IMAGE
# =============================================================================
FROM python:3.12-alpine AS env
# ------------------------------------------------------------------------------
# ENVIRONMENT
# ------------------------------------------------------------------------------
ENV HAYABUSA_LIBC=musl
ENV HAYABUSA_VERSION=3.8.1
# =============================================================================
# BUILD IMAGE
# =============================================================================
FROM env AS build
# ------------------------------------------------------------------------------
# ENVIRONMENT
# ------------------------------------------------------------------------------
ENV HAYABUSA_URL=https://github.com/Yamato-Security/hayabusa/releases/download/v${HAYABUSA_VERSION}/hayabusa-${HAYABUSA_VERSION}-lin-x64-${HAYABUSA_LIBC}.zip
# -----------------------------------------------------------------------------
# COPY PRE-BUILT PACKAGES (OPTIONAL)
# -----------------------------------------------------------------------------
#COPY pkg /pkg
# ------------------------------------------------------------------------------
# SETUP VENV
# ------------------------------------------------------------------------------
RUN apk add build-base curl linux-headers && \
    python3 -m venv /venv && \
    /venv/bin/python -m pip install uv && \
    mkdir /tpl && \
    curl -L -o /tpl/hayabusa.zip ${HAYABUSA_URL}
# -----------------------------------------------------------------------------
# SETUP FUSION PACKAGES (PROD)
# -----------------------------------------------------------------------------
RUN /venv/bin/uv pip install --python /venv/bin/python edf-helium-server
# -----------------------------------------------------------------------------
# SETUP FUSION PACKAGES (DEV)
# -----------------------------------------------------------------------------
#COPY pkg /pkg
#RUN /venv/bin/uv pip install --python /venv/bin/python --pre --find-links /pkg edf-helium-server
# =============================================================================
# PRODUCTION IMAGE
# =============================================================================
FROM env AS production
# -----------------------------------------------------------------------------
# FINAL SETUP
# -----------------------------------------------------------------------------
RUN apk add unzip && \
    mkdir -p /analyzer/hayabusa && \
    ln -sf /analyzer/hayabusa/hayabusa-${HAYABUSA_VERSION}-lin-x64-${HAYABUSA_LIBC} /analyzer/hayabusa/hayabusa
# -----------------------------------------------------------------------------
# COPY FROM BUILD IMAGE
# -----------------------------------------------------------------------------
COPY --from=build /tpl /tpl
COPY --from=build /venv /venv
# ------------------------------------------------------------------------------
# ENTRYPOINT
# ------------------------------------------------------------------------------
COPY analyzer.py /analyzer.py
COPY --chmod=755 docker-entrypoint.sh /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
