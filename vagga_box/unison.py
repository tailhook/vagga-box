import os
import sys
import time
import shutil
import subprocess


from . import BASE


def clean_local_dir():
    shutil.rmtree(str(BASE / 'unison'))


def sync_files(vagga):

    ignores = []
    for v in vagga.ignore_list:
        ignores.append('-ignore')
        ignores.append('Path ' + v)

    print("Syncing files...", file=sys.stderr)
    sync_start = time.time()
    unison_dir = BASE / 'unison'
    if not unison_dir.exists():
        unison_dir.mkdir()
    env = os.environ.copy()
    env.update({
        "UNISON": str(unison_dir),
    })
    subprocess.check_call([
        'unison', '.',
        'socket://127.0.0.1:7767/' + vagga.storage_volume,
        '-batch', '-silent',
        '-ignore', 'Path .vagga',
        ] + ignores,
        env=env)
    print("Files synced in", time.time() - sync_start, "seconds",
          file=sys.stderr)

