#!/usr/bin/env sh
set -e
# exec
case "${ROLE}" in
    analyzer)
        exec /venv/bin/python /analyzer.py --config /conf/helium.yml
        ;;
    *)
        exec "$@"
        ;;
esac
