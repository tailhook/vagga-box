import os

from vagga_box.config import get_config


def test_read_mixins():
    cwd = os.getcwd()
    try:
        os.chdir('tests/mixins1')
        assert get_config()[1] == {
            'containers': {
                'first_mixin': None,
                'nested': None,
                'nested1': None,
            },
            'commands': {
                'root': {'container': 'x', 'run': 'y'},
            },
            'mixins': ['first_mixin.yaml', 'dir/nested_mixins.yaml'],
        }
    finally:
        os.chdir(cwd)
