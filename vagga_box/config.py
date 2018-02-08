import os
import sys
import pathlib
import yaml


class FancyLoader(yaml.Loader):
    pass


def generic_object(loader, suffix, node):
    if isinstance(node, yaml.ScalarNode):
        constructor = loader.__class__.construct_scalar
    elif isinstance(node, yaml.SequenceNode):
        constructor = loader.__class__.construct_sequence
    elif isinstance(node, yaml.MappingNode):
        constructor = loader.__class__.construct_mapping
    else:
        raise ValueError(node)
    # TODO(tailhook) wrap into some object?
    return constructor(loader, node)


yaml.add_multi_constructor('!', generic_object, Loader=FancyLoader)

def load(f):
    return yaml.load(f, Loader=FancyLoader)


def find_config():
    path = pathlib.Path(os.getcwd())
    suffix = pathlib.Path("")
    while str(path) != path.root:
        vagga = path / 'vagga.yaml'
        if vagga.exists():
            return path, vagga, suffix
        suffix = path.parts[-1] / suffix
        path = path.parent
    raise RuntimeError("No vagga.yaml found in path {!r}".format(path))


def read_mixins(base_filename, mixin_list, dest):
    for subpath in mixin_list:
        filename = base_filename.parent / subpath
        try:
            with filename.open('rb') as file:
                data = load(file)
        except Exception as e:
            print("Error reading mixin {}: {}".format(filename, e),
                file=sys.stderr)
        for name, val in data.get('containers', {}).items():
            if name not in dest['containers']:
                dest['containers'][name] = val
        for name, val in data.get('commands', {}).items():
            if name not in dest['commands']:
                dest['commands'][name] = val
        read_mixins(filename, data.get('mixins', ()), dest)


def get_config():
    dir, vagga, suffix = find_config()
    with vagga.open('rb') as file:
        data = load(file)
    mix = {'containers': {}, 'commands': {}}
    read_mixins(vagga, data.get('mixins', ()), mix)
    mix['containers'].update(data.get('containers', {}))
    data['containers'] = mix['containers']
    mix['commands'].update(data.get('commands', {}))
    data['commands'] = mix['commands']

    return dir, data, suffix
