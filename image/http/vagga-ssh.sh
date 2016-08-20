#!/bin/sh -e
test -n "$VAGGA_RESOLV_CONF"
test -n "$VAGGA_VOLUME"
if [ "$(cat /etc/resolv.conf)" != "$VAGGA_RESOLV_CONF" ]; then
    echo "$VAGGA_RESOLV_CONF" | sudo tee /etc/resolv.conf > /dev/null
fi
cd "/vagga/$VAGGA_VOLUME"
exec vagga "$@"
