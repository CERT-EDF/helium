# =============================================================================
# FUSION DIRECTIVES
# =============================================================================
# fusion:image=cert-edf/helium-be-plasma
# fusion:package=generaptor
# fusion:package=edf-plasma-core
# fusion:package=edf-plasma-dissectors
# fusion:package=edf-plasma-cli
# fusion:package=edf-fusion
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
# HELIUM PLASMA ANALYZER
# ------------------------------------------------------------------------------
RUN apt update && \
    apt install --yes build-essential libmagic-dev libsystemd-dev pkg-config python3 python3-dev python3-venv && \
    python3 -m venv /venv && \
    /venv/bin/python -m pip install uv
# -----------------------------------------------------------------------------
# SETUP FUSION PACKAGES (PROD)
# -----------------------------------------------------------------------------
RUN /venv/bin/uv pip install --python /venv/bin/python edf-helium-server edf-plasma-dissectors[binary,linux,windows,pcap,memdump] edf-plasma-cli
# -----------------------------------------------------------------------------
# SETUP FUSION PACKAGES (DEV)
# -----------------------------------------------------------------------------
#COPY pkg /pkg
#RUN /venv/bin/uv pip install --python /venv/bin/python --pre --find-links /pkg edf-helium-server edf-plasma-dissectors[binary,linux,windows,pcap,memdump] edf-plasma-cli
# =============================================================================
# PRODUCTION IMAGE
# =============================================================================
FROM ubuntu:24.04 AS production
# -----------------------------------------------------------------------------
# FINAL SETUP
# -----------------------------------------------------------------------------
RUN apt update && \
    apt install --yes libmagic1t64 libsystemd0 python3 && \
    mkdir -p /analyzer/plasma && \
    ln -s /venv/bin/plasma /analyzer/plasma/plasma
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
