# =============================================================================
# FUSION DIRECTIVES
# =============================================================================
# fusion:image=cert-edf/helium-be-yara
# fusion:package=edf-fusion
# fusion:package=generaptor
# fusion:package=edf-helium-core
# fusion:package=edf-helium-server
# =============================================================================
# BUILD IMAGE
# =============================================================================
FROM python:3.12-alpine AS build
# ------------------------------------------------------------------------------
# ENVIRONMENT
# ------------------------------------------------------------------------------
ENV YARA_RULES_URL=https://github.com/Yara-Rules/rules/archive/refs/heads/master.zip
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
    curl -L -o /tpl/yara-rules.zip ${YARA_RULES_URL}
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
FROM python:3.12-alpine AS production
# -----------------------------------------------------------------------------
# FINAL SETUP
# -----------------------------------------------------------------------------
RUN apk add unzip yara && \
    mkdir -p /analyzer/yara && \
    ln -s /usr/bin/yara /analyzer/yara/yara
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
