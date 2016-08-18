import os
import sys
import json
import time
import shlex
import logging
import subprocess

from . import config
from . import virtualbox
from . import runtime
from . import arguments
from . import settings


log = logging.getLogger(__name__)


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

    virtualbox.init_vm()

    vagga.storage_volume = find_volume(vagga)

    setting['auto-apply-sysctl'] = True

    ignores = []
    for v in vagga.ignore_list:
        ignores.append('-ignore')
        ignores.append('Path ' + v)

    print("Syncing files...", file=sys.stderr)
    sync_start = time.time()
    subprocess.check_call([
        'unison', '.',
        'socket://127.0.0.1:7767/' + vagga.storage_volume,
        '-batch', # '-silent',
        '-ignore', 'Path .vagga',
        ] + ignores)
    print("Files synced in", time.time() - sync_start, "seconds",
          file=sys.stderr)

    code = subprocess.run([
        'ssh', 'user@127.0.0.1', '-p', '7022',
        '-i', os.path.join(os.path.dirname(__file__), 'id_rsa'), '-t',
        '-o', 'StrictHostKeyChecking no',
        'bash', '-c',
        '"cd /vagga/{}; vagga {}"'.format(
            vagga.storage_volume,
            shlex.quote(' '.join(map(shlex.quote, sys.argv[1:]))))])

    sys.exit(code)

