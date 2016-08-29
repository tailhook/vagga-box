import os
import re
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
    'ssh', '-t',
    '-i', os.path.join(os.path.dirname(__file__), 'id_rsa'),
    '-F', os.path.join(os.path.dirname(__file__), 'ssh_config'),
    'user@127.0.0.1',
]
VOLUME_RE = re.compile('^[a-zA-Z0-9_-]+$')


def find_volume(vagga):
    vol_file = vagga.vagga_dir / '.virtualbox-volume'
    if vol_file.exists():
        name = vol_file.open('rt').read().strip()
        if VOLUME_RE.match(name):
            return name
    basename = vagga.base.stem
    if not VOLUME_RE.match(basename):
        basename = 'unknown'
    name = subprocess.check_output(BASE_SSH_COMMAND +
        ['/usr/local/bin/find-volume.sh'], env={
            'VAGGA_PROJECT_NAME': basename,
        }).decode('ascii').strip()
    if not VOLUME_RE.match(name):
        raise RuntimeError("Command returned bad volume name {!r}"
                           .format(name))
    with vol_file.open('w') as f:
        f.write(name)
    return name


def main():

    logging.basicConfig(
        # TODO(tailhook) should we use RUST_LOG like in original vagga?
        level=os.environ.get('VAGGA_LOG', 'WARNING'))

    args = arguments.parse_args()

    if args.command[0:1] == ['_box']:
        # use real argparse here
        if args.command[1:2] == ['ssh']:
            returncode = subprocess.Popen(
                    BASE_SSH_COMMAND + args.command[2:],
                ).wait()
            return sys.exit(returncode)
        elif args.command[1:2] == ['upgrade_vagga']:
            returncode = subprocess.Popen(
                    BASE_SSH_COMMAND + ['/usr/local/bin/upgrade-vagga'],
                ).wait()
            return sys.exit(returncode)
        elif args.command[1:2] == ['mount']:
            dir = BASE / 'remote'
            if not dir.exists():
                dir.mkdir()
            cmd = ['sudo', 'mount', '-t', 'nfs',
                   '-o', 'vers=4,resvport,port=7049',
                   '127.0.0.1:/vagga', str(dir)]
            print("Running", ' '.join(cmd), file=sys.stderr)
            if (dir / 'lost+found').exists():
                print("Error looks like your volume is already mounted.",
                    file=sys.stderr)
                print("You only need to mount the volume once",
                    file=sys.stderr)
                return sys.exit(1)
            returncode = subprocess.Popen(cmd).wait()
            if returncode == 0:
                # TODO(tailhook) Simple heuristics, may be improved
                if os.path.exists('.vagga/.virtualbox-volume'):
                    with open('.vagga/.virtualbox-volume') as f:
                        volume = f.read().strip()
                    print("Now you can add "
                          "~/.vagga/remote/"+volume+
                              "/.vagga/<container-name>/dir "
                          "to the search paths of your IDE")
                else:
                    print("Now you can add "
                          "~/.vagga/remote/<project-name>"
                          "/.vagga/<container-name>/dir "
                          "to the search paths of your IDE")
                    print("<project-name> will be in "
                          "`.vagga/.virtualbox-volume` "
                          "after you run vagga command for the first time")
            return sys.exit(returncode)
        else:
            print("Unknown command", repr((args.command[1:2] or [''])[0]),
                  file=sys.stderr)
            print("Specify one of `ssh`, `upgrade_vagga`, `mount`",
                  file=sys.stderr)
            return sys.exit(1)


    path, cfg, suffix = config.get_config()

    setting = settings.parse_all(path)

    vagga = runtime.Vagga(path, cfg, args)

    if not vagga.vagga_dir.exists():
        vagga.vagga_dir.mkdir()

    vm = virtualbox.init_vm(new_storage_callback=unison.clean_local_dir)

    setting['auto-apply-sysctl'] = True

    vagga.storage_volume = find_volume(vagga)

    env = os.environ.copy()
    env.update({
        'VAGGA_VOLUME': vagga.storage_volume,
        # TODO(tailhook) move me
        'VAGGA_RESOLV_CONF': open('/etc/resolv.conf').read(),
    })

    with unison.start_sync(vagga):
        with virtualbox.expose_ports(vm, vagga.exposed_ports()):
            result = subprocess.Popen(
                    BASE_SSH_COMMAND + [
                    '-q',
                    '/usr/local/bin/vagga-ssh.sh',
                    ] + sys.argv[1:],
                    env=env,
                ).wait()

    sys.exit(result)

