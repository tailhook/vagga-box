import os

from vagga_box.config import get_config
from vagga_box.runtime import Vagga
from vagga_box.arguments import parse_args


def test_read_mixins():
    cwd = os.getcwd()
    try:
        os.chdir('tests/expose_ports')
        path, cfg, _ = get_config()

        vagga = Vagga(path, cfg, parse_args(['run']))
        print("VAGGA", vagga.run_commands)
        assert vagga.exposed_ports() \
            == frozenset([10, 20])

        vagga = Vagga(path, cfg, parse_args(['super']))
        assert vagga.exposed_ports() \
            == frozenset([110, 210, 220, 230])
    finally:
        os.chdir(cwd)
