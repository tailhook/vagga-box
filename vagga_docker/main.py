import os
import sys
import json
import logging
import docker

from . import config
from . import storage
from . import runtime
from . import arguments
from . import settings


log = logging.getLogger(__name__)


def main():

    logging.basicConfig(
        # TODO(tailhook) should we use RUST_LOG like in original vagga?
        level=os.environ.get('VAGGA_LOG', 'WARNING'))

    path, cfg, suffix = config.get_config()
    args = arguments.parse_args()

    setting = settings.parse_all(path)

    vagga = runtime.Vagga(path, cfg, args)
    cli = docker.from_env(assert_hostname=False)

    if not vagga.vagga_dir.exists():
        vagga.vagga_dir.mkdir()

    vagga.storage_volume = storage.get_volume(vagga, cli)
    ports = ["--publish={0}:{0}".format(port)
             for port in vagga.exposed_ports()]

    setting['auto-apply-sysctl'] = True

    command_line = [
        "docker", "run",
        "--volume={}:/work".format(vagga.base),
        "--volume={}:/work/.vagga".format(vagga.storage_volume),
        "--workdir=/work/{}".format(suffix),
        "--privileged",
        "--interactive",
        "--tty",
        "--rm",
        "--env=VAGGA_SETTINGS=" + json.dumps(setting),
        ] + ports + [
        "tailhook/vagga:v0.6.1-44-gc32f05e",
        "/vagga/vagga",
        "--ignore-owner-check", # this is needed on linux only
        ] + sys.argv[1:]
    log.info("Docker command-line: %r", command_line)
    # This don't work on Windows. We may figure out a better way
    os.execvp("docker", command_line)


