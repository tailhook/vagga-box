#!/bin/sh
if [ "\$(cat /etc/resolv.conf)" != "\$VAGGA_RESOLV_CONF" ]; then
    echo "\$VAGGA_RESOLV_CONF" | sudo tee /etc/resolv.conf > /dev/null
fi
cd "/vagga/\$VAGGA_VOLUME"
exec vagga "\$@"
