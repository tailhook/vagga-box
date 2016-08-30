import os
import sys
import time
import errno
import fcntl
import shlex
import shutil
import signal
import logging
from contextlib import contextmanager
import subprocess

from . import BASE, KEY_PATH

log = logging.getLogger(__name__)
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'ssh_config')


def clean_local_dir():
    dir = BASE / 'unison'
    if dir.exists():
        shutil.rmtree(str(dir))


def _unison_cli(vagga):

    ignores = []
    for v in vagga.ignore_list:
        ignores.append('-ignore')
        ignores.append('Path ' + v)

    sync_start = time.time()
    unison_dir = BASE / 'unison'
    if not unison_dir.exists():
        unison_dir.mkdir()
    env = os.environ.copy()
    env.update({
        "UNISON": str(unison_dir),
    })
    cmdline = [
        'unison', '.',
        'ssh://user@localhost//vagga/' + vagga.storage_volume,
        '-sshargs',
            ' -i ' + str(KEY_PATH) +
            ' -F ' + CONFIG_FILE,
        '-batch',# '-silent',
        '-prefer', '.',
        '-ignore', 'Path .vagga',
        ] + ignores
    return cmdline, env


def openlock(path):
    # unfortunately this combination of flags doesn't have string
    # representation
    fd = os.open(str(path), os.O_CREAT|os.O_RDWR)
    return os.fdopen(fd, 'rb+')


def background_run(cmdline, env, logfile):
    log = open(str(logfile), 'wb')
    pro = subprocess.Popen(cmdline, env=env,
        stdin=subprocess.DEVNULL, stdout=log, stderr=log,
        preexec_fn=lambda: signal.signal(signal.SIGHUP, signal.SIG_IGN))
    return pro.pid


@contextmanager
def start_sync(vagga):
    lockfilename = vagga.vagga_dir / '.unison-lock'
    while True:
        lockfile = openlock(lockfilename)
        lock = fcntl.lockf(lockfile, fcntl.LOCK_SH)
        try:
            lockfile.seek(0)
            pid = int(lockfile.read().strip())
            os.kill(pid, 0)
        except (ValueError, OSError) as e:
            fcntl.lockf(lockfile, fcntl.LOCK_UN)
            try:
                fcntl.lockf(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                if (isinstance(e, OSError) and e.errno == errno.ESRCH or
                        isinstance(e, ValueError)):
                    # there is a file and it's locked but no such process
                    lockfilename.unlink()
                continue
            else:
                cmdline, env = _unison_cli(vagga)

                start_time = time.time()
                log.info("Syncing files...")
                subprocess.check_call(cmdline, env=env)
                log.info("Synced in %.1f sec", time.time() - start_time)

                pid = background_run(cmdline + ['-repeat=watch'],
                    env=env, logfile=vagga.vagga_dir / '.unison-log')

                lockfile.seek(0)
                lockfile.write(str(pid).encode('ascii'))
                lockfile.flush()
            finally:
                fcntl.lockf(lockfile, fcntl.LOCK_UN)
            fcntl.lockf(lockfile, fcntl.LOCK_SH)
            break
        else:
            break

    try:
        yield
    finally:
        fcntl.lockf(lockfile, fcntl.LOCK_UN)
        lockfile = openlock(lockfilename)
        try:
            fcntl.lockf(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            pass # locked by someone else, don't do anything
        else:
            try:
                lockfile.seek(0)
                os.kill(int(lockfile.read()), signal.SIGTERM)
            except (ValueError, OSError) as e:
                log.info("Error when killing unison %r", e)
