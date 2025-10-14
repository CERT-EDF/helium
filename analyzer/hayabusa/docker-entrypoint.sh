#!/usr/bin/env sh
set -e
# init if needed
mkdir -p /analyzer/hayabusa
if [ ! -f /analyzer/hayabusa/hayabusa-*-x64-* ]; then
    unzip -d /analyzer/hayabusa /tpl/hayabusa.zip 'hayabusa-*-lin-x64-*' 'config/*'
    chmod +x /analyzer/hayabusa/hayabusa-*-lin-x64-*
fi
mkdir -p /analyzer/hayabusa/rules
if [ -z "$(ls -A /analyzer/hayabusa/rules)" ]; then
    unzip -d /analyzer/hayabusa/rules /tpl/hayabusa.zip 'rules/*'
    mv /analyzer/hayabusa/rules/rules/* /analyzer/hayabusa/rules
    rm -rf /analyzer/hayabusa/rules/rules
fi
# exec
case "${ROLE}" in
    analyzer)
        exec /venv/bin/python /analyzer.py --config /conf/helium.yml
        ;;
    *)
        exec "$@"
        ;;
esac
