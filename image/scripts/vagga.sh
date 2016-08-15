#!/bin/sh -ex

mkdir /home/user/.ssh
echo ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC4s++fCkUFUVJAGWv5St/V5CFsga0ElLxYtQGKEHy2HfPom8Im+PM28q3d8NBCXt7GDRLjQg8K/vBMge8VBJ68N76B0WDG9A/Nx6HID7LASOUAAig+YgnkJBQm8rTo3yqlKkDMx65OqtC09bG9FrsIpgDTaEt+mCl+lkvk7fkORZw77kNMx6W768cMXSEvaV6f3BfgAUVw6PjrUh4EPtnbvIRSFw9BLPS8LJHTW8zY2ctrn5rCoDLmtozn0FmTTi9h3Px+OIwgTx4k+PGLCBYich6VVSD2KyWPcM13feI5BjVc2yNSoWpYm7klsTMMANUjIqiR9rlNe/6esVS0bowl vagga insecure public key > /home/user/.ssh/authorized_keys
chown -R user /home/user/.ssh
chmod -R go-rwsx /home/user/.ssh
chmod 0755 /home/user/.ssh
chmod 0644 /home/user/.ssh/authorized_keys

apk add virtualbox-guest-additions --update-cache --repository http://dl-3.alpinelinux.org/alpine/edge/testing/ --allow-untrusted

cd /tmp
wget http://files.zerogw.com/vagga/vagga-0.6.1-126-g07adc4b.tar.xz
tar -xJf vagga-0.6.1-126-g07adc4b.tar.xz
cd vagga
sudo ./install.sh

UNISON_VERSION=2.48.4
cd /tmp
sudo apk add --update alpine-sdk inotify-tools-dev
apk add ocaml --update-cache --repository http://dl-3.alpinelinux.org/alpine/edge/testing/ --allow-untrusted
curl -O http://www.seas.upenn.edu/~bcpierce/unison//download/releases/unison-$UNISON_VERSION/unison-$UNISON_VERSION.tar.gz
tar xzf unison-$UNISON_VERSION.tar.gz
cd unison-$UNISON_VERSION
make GLIBC_SUPPORT_INOTIFY=true UISTYLE=text INSTALLDIR=/bin NATIVE=true STATIC=true install
apk del ocaml inotify-tools-dev alpine-sdk
rm -rf /tmp/unison-$UNISON_VERSION.tar.gz /tmp/unison-$UNISON_VERSION /tmp/binunison* \

apk add nfs-utils
sudo mkdir /vagga
sudo chown user /vagga
mkdir /vagga/_cache
cat <<SETTINGS > /home/user/.vagga.yaml
cache-dir: /vagga/_cache
SETTINGS
cat <<NFS >> /etc/exports
/vagga *(rw,sync,all_squash,anonuid=1000,anongid=1000))
NFS
rc-update add nfs
rc-update add nfsmount
rc-update add netmount

rm -rf /var/cache/apk/*
