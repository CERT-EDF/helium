# =============================================================================
# FUSION DIRECTIVES
# =============================================================================
# fusion:image=cert-edf/helium-be-plaso
# fusion:package=edf-fusion
# fusion:package=generaptor
# fusion:package=edf-helium-core
# fusion:package=edf-helium-server
# =============================================================================
# BUILD IMAGE
# =============================================================================
FROM ubuntu:24.04 AS build
# ------------------------------------------------------------------------------
# ENVIRONMENT
# ------------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------
# COPY PRE-BUILT PACKAGES (OPTIONAL)
# -----------------------------------------------------------------------------
#COPY pkg /pkg
# ------------------------------------------------------------------------------
# HELIUM PLASO ANALYZER
# ------------------------------------------------------------------------------
RUN apt update && \
    apt install --yes build-essential nano pkg-config python3 python3-dev python3-venv && \
    python3 -m venv /venv && \
    /venv/bin/python -m pip install uv && \
    /venv/bin/uv pip install --python /venv/bin/python plaso
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
FROM ubuntu:24.04 AS production
# -----------------------------------------------------------------------------
# FINAL SETUP
# -----------------------------------------------------------------------------
RUN apt update && \
    apt install --yes python3 && \
    mkdir -p /analyzer/plaso && \
    ln -s /venv/bin/log2timeline /analyzer/plaso/log2timeline
# -----------------------------------------------------------------------------
# COPY FROM BUILD IMAGE
# -----------------------------------------------------------------------------
COPY --from=build /venv /venv
# ------------------------------------------------------------------------------
# ENTRYPOINT
# ------------------------------------------------------------------------------
COPY analyzer.py /analyzer.py
COPY --chmod=755 docker-entrypoint.sh /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
