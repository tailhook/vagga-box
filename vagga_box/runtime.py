class Vagga(object):

    def __init__(self, path, config, arguments):
        self.base = path
        self.vagga_dir = path / '.vagga'
        self.containers = config.get('containers', {})
        self.commands = config.get('commands', {})
        self.ignore_list = config.get('_ignore-dirs', [])
        self.arguments = arguments

        if arguments.command:
            self.run_commands = [arguments.command[0]]
        else:
            self.run_commands = arguments.run_multi or []

    def exposed_ports(self):
        return frozenset(_exposed_ports(self, self.run_commands))



def _exposed_ports(vagga, commands):
    for command in commands:
        cmd = vagga.commands.get(command, {})
        # allow expose ports in the command
        yield from _get_ports(cmd)
        # and in children commands (for supervise)
        for child in cmd.get('children', {}).values():
            yield from _get_ports(child)


def _get_ports(cmd):
    ports = cmd.get('_expose-ports', [])
    if not isinstance(ports, list):
        raise RuntimeError("the `_expose-ports` setting must be a list"
              "of integers, got {!r} instead".format(ports))
    yield from ports
