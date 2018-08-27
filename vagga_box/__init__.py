import os
import pathlib

BASE = pathlib.Path().home() / '.vagga'
KEY_PATH = BASE / 'id_rsa'
BASE_SSH_COMMAND = [
    'ssh',
    '-i', str(KEY_PATH),
    '-F', os.path.join(os.path.dirname(__file__), 'ssh_config'),
    'user@127.0.0.1',
]
# checking stdout as it's the most useful thing to redirect
BASE_SSH_TTY_COMMAND = BASE_SSH_COMMAND + (['-t'] if os.isatty(1) else [])
BASE_SSH_COMMAND_QUIET = BASE_SSH_COMMAND + ['-o LogLevel=QUIET']
