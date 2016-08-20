#!/bin/sh -ex
HTTP_PREFIX="$(cat /tmp/http)"
export no_proxy="$(cat /tmp/no_proxy)"

mkdir /home/user/.ssh
echo ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC4s++fCkUFUVJAGWv5St/V5CFsga0ElLxYtQGKEHy2HfPom8Im+PM28q3d8NBCXt7GDRLjQg8K/vBMge8VBJ68N76B0WDG9A/Nx6HID7LASOUAAig+YgnkJBQm8rTo3yqlKkDMx65OqtC09bG9FrsIpgDTaEt+mCl+lkvk7fkORZw77kNMx6W768cMXSEvaV6f3BfgAUVw6PjrUh4EPtnbvIRSFw9BLPS8LJHTW8zY2ctrn5rCoDLmtozn0FmTTi9h3Px+OIwgTx4k+PGLCBYich6VVSD2KyWPcM13feI5BjVc2yNSoWpYm7klsTMMANUjIqiR9rlNe/6esVS0bowl vagga insecure public key > /home/user/.ssh/authorized_keys
chown -R user /home/user/.ssh
chmod -R go-rwsx /home/user/.ssh
chmod 0755 /home/user/.ssh
chmod 0644 /home/user/.ssh/authorized_keys

wget -O /bin/unison $HTTP_PREFIX/unison
chmod +x /bin/unison
wget -O /etc/init.d/unison $HTTP_PREFIX/unison.rc
chmod +x /etc/init.d/unison
rc-update add unison

apk add nfs-utils
mkdir /vagga
mkfs.ext4 /dev/sdb1
mount /dev/sdb1 /vagga
mkdir /vagga/.unison /vagga/.cache
chown user /vagga /vagga/.unison /vagga/.cache
wget -O /home/user/.vagga.yaml $HTTP_PREFIX/vagga.settings.yaml
mkdir -p /home/user/.local/bin
wget -O /home/user/.local/bin/vagga $HTTP_PREFIX/vagga.sh
chmod +x /home/user/.local/bin/vagga

wget -O /home/user/.local/bin/vagga-upgrade $HTTP_PREFIX/upgrade-vagga.sh
chmod +x /home/user/.local/bin/vagga-upgrade

cat <<NFS >> /etc/exports
/vagga *(rw,sync,no_subtree_check,all_squash,anonuid=1000,anongid=1000)
NFS
rc-update add nfs
rc-update add nfsmount
rc-update add netmount

apk add virtualbox-guest-additions --update-cache --repository http://dl-cdn.alpinelinux.org/alpine/edge/testing/
apk add shadow-uidmap --update-cache --repository http://dl-cdn.alpinelinux.org/alpine/edge/community/

cat <<SYSCTL > /etc/sysctl.d/01-vagga.conf
fs.inotify.max_user_watches=131072
SYSCTL
cat <<SUBUID > /etc/subuid
user:100000:165536
SUBUID
cat <<SUBGID > /etc/subgid
user:100000:165536
SUBGID
echo "PermitUserEnvironment yes" >> /etc/ssh/sshd_config


sync
