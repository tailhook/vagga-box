import os
import re
import sys
import json
import time
import shlex
import shutil
import logging
import subprocess

from . import BASE, KEY_PATH, BASE_SSH_COMMAND, BASE_SSH_COMMAND_QUIET
from . import BASE_SSH_TTY_COMMAND
from . import config
from . import virtualbox
from . import runtime
from . import arguments
from . import settings
from . import unison


log = logging.getLogger(__name__)
KEY_SOURCE = os.path.join(os.path.dirname(__file__), 'id_rsa')
VOLUME_RE = re.compile('^[a-zA-Z0-9_-]+$')
DEFAULT_RESOLV_CONF = """
# No resolv.conf could be read from the host system
nameserver 8.8.8.8
nameserver 8.8.4.4
"""

def check_key():
    if not KEY_PATH.exists():
        if not BASE.exists():
            BASE.mkdir()
        tmp = KEY_PATH.with_suffix('.tmp')
        shutil.copy(str(KEY_SOURCE), str(tmp))
        os.chmod(str(tmp), 0o600)
        os.rename(str(tmp), str(KEY_PATH))


def ide_hint():
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


def read_resolv_conf():
    try:
        with open('/etc/resolv.conf', 'rt') as f:
            data = f.read()
    except OSError as e:
        print("Warning: Error reading /etc/resolv.conf:", e, file=sys.stderr)
        data = None
    if not data:
        data = DEFAULT_RESOLV_CONF
    return data


def get_vagga_version():
    (stdout, stderr) = subprocess.Popen(
        BASE_SSH_COMMAND_QUIET + ['vagga --version'], stdout=subprocess.PIPE,
    ).communicate()
    return stdout.decode('utf-8').rstrip()


def main():

    logging.basicConfig(
        # TODO(tailhook) should we use RUST_LOG like in original vagga?
        level=os.environ.get('VAGGA_LOG', 'WARNING'))

    args = arguments.parse_args()
    check_key()

    if args.command[0:1] == ['_box']:
        # use real argparse here
        if args.command[1:2] == ['ssh']:
            returncode = subprocess.Popen(
                    BASE_SSH_TTY_COMMAND + args.command[2:],
                ).wait()
            return sys.exit(returncode)
        elif args.command[1:2] == ['up']:
            virtualbox.init_vm(new_storage_callback=unison.clean_local_dir)
            return sys.exit(0)
        elif args.command[1:2] == ['down']:
            virtualbox.stop_vm()
            return sys.exit(0)
        elif args.command[1:2] == ['upgrade_vagga']:
            print('Starting upgrade vagga. Current version:',
                  get_vagga_version())
            returncode = subprocess.Popen(
                    BASE_SSH_COMMAND_QUIET + ['/usr/local/bin/upgrade-vagga'],
                ).wait()
            if returncode == 0:
                print('Vagga successfully upgraded to', get_vagga_version())
                print('All OK!')
            else:
                print('Failed to upgrade vagga. Exit with status:', returncode,
                      file=sys.stderr)
            return sys.exit(returncode)
        elif args.command[1:2] == ['mount']:
            virtualbox.init_vm(new_storage_callback=unison.clean_local_dir)
            dir = BASE / 'remote'
            if not dir.exists():
                dir.mkdir()
            cmd = ['sudo', 'mount', '-t', 'nfs',
                   '-o', 'vers=4,resvport,port=7049',
                   '127.0.0.1:/vagga', str(dir)]
            print("Running", ' '.join(cmd), file=sys.stderr)
            if (dir / 'lost+found').exists():
                print("It looks like your volume is already mounted.",
                    file=sys.stderr)
                print("You only need to mount the volume once.",
                    file=sys.stderr)
                ide_hint()
                return sys.exit(1)
            returncode = subprocess.Popen(cmd).wait()
            if returncode == 0:
                ide_hint()
            return sys.exit(returncode)
        else:
            print("Unknown command", repr((args.command[1:2] or [''])[0]),
                  file=sys.stderr)
            print("Specify one of "
                  "`ssh`, `upgrade_vagga`, `mount`, `up`, 'down'",
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
        'VAGGA_RESOLV_CONF': read_resolv_conf(),
        'VAGGA_SETTINGS': json.dumps(setting),
    })

    with unison.start_sync(vagga):
        with virtualbox.expose_ports(vm, vagga.exposed_ports()):
            result = subprocess.Popen(
                    BASE_SSH_TTY_COMMAND + [
                    '-q',
                    '/usr/local/bin/vagga-ssh.sh',
                    ] + list(map(shlex.quote, sys.argv[1:])),
                    env=env,
                ).wait()

    sys.exit(result)

