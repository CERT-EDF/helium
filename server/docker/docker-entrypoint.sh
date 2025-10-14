#!/usr/bin/env sh
set -e
# prepare data directory if needed
mkdir -p /data
if [ ! -d /data/generaptor/cache ]; then
    unzip /tpl/generaptor.zip -d /data
fi
# prepare configuration directory if needed
mkdir -p /conf
if [ ! -f /conf/helium.yml ]; then
    cp /tpl/helium.dist.yml /conf/helium.yml
fi
if [ ! -f /conf/constant.yml ]; then
    cp /tpl/constant.dist.yml /conf/constant.yml
fi
# prepare analyzer directory if needed
mkdir -p /analyzer
# exec depending on ROLE
case "${ROLE}" in
    server)
        exec /venv/bin/helium-server --config /conf/helium.yml
        ;;
    disk-usage)
        exec /venv/bin/helium-disk-usage --config /conf/helium.yml
        ;;
    synchronizer)
        exec /venv/bin/helium-synchronizer --config /conf/helium.yml
        ;;
    *)
        exec "$@"
        ;;
esac
