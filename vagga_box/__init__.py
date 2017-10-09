import os
import pathlib

BASE = pathlib.Path().home() / '.vagga'
KEY_PATH = BASE / 'id_rsa'
BASE_SSH_COMMAND = [
    'ssh', '-t',
    '-i', str(KEY_PATH),
    '-F', os.path.join(os.path.dirname(__file__), 'ssh_config'),
    'user@127.0.0.1',
]
BASE_SSH_COMMAND_QUIET = BASE_SSH_COMMAND + ['-o LogLevel=QUIET']
