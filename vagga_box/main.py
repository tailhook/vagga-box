import os
import sys
import json
import time
import shlex
import logging
import subprocess

from . import BASE
from . import config
from . import virtualbox
from . import runtime
from . import arguments
from . import settings
from . import unison


log = logging.getLogger(__name__)
BASE_SSH_COMMAND = [
    'ssh', 'user@127.0.0.1', '-p', '7022',
    '-i', os.path.join(os.path.dirname(__file__), 'id_rsa'), '-t',
    '-o', 'StrictHostKeyChecking no',
    '-o', 'CheckHostIP no',
    '-o', 'SendEnv VAGGA_*'
]


def find_volume(vagga):
    vol_file = vagga.vagga_dir / '.virtualbox-volume'
    if vol_file.exists():
        return vol_file.open('rt').read().strip()
    raise NotImplementedError()


def main():

    logging.basicConfig(
        # TODO(tailhook) should we use RUST_LOG like in original vagga?
        level=os.environ.get('VAGGA_LOG', 'WARNING'))

    path, cfg, suffix = config.get_config()
    args = arguments.parse_args()

    setting = settings.parse_all(path)

    vagga = runtime.Vagga(path, cfg, args)

    if not vagga.vagga_dir.exists():
        vagga.vagga_dir.mkdir()

    vm = virtualbox.init_vm(new_storage_callback=unison.clean_local_dir)

    vagga.storage_volume = find_volume(vagga)

    setting['auto-apply-sysctl'] = True

    unison.sync_files(vagga)

    env = os.environ.copy()
    env.update({
        'VAGGA_VOLUME': vagga.storage_volume,
        # TODO(tailhook) move me
        'VAGGA_RESOLV_CONF': open('/etc/resolv.conf').read(),
    })

    if sys.argv[1:2] == ['_box_ssh']:
        result = subprocess.run(
            BASE_SSH_COMMAND + sys.argv[2:],
            env=env)
    else:
        with virtualbox.expose_ports(vm, vagga.exposed_ports()):
            result = subprocess.run(
                BASE_SSH_COMMAND + [
                '-q',
                '/usr/local/bin/vagga-ssh.sh',
                ] + sys.argv[1:],
                env=env)

    sys.exit(result.returncode)

