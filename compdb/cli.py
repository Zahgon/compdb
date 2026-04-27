from __future__ import print_function, unicode_literals, absolute_import
import argparse
import io
import logging
import os
import sys
import compdb.backend.json
import compdb.includedb
import compdb.utils as utils
from compdb.__about__ import __prog__, __version__
from compdb.backend.json import JSONCompileCommandSerializer
from compdb.core import CompilationDatabase

class Config(object):

    def __init__(self):
        self.build_directory_patterns = []

    @property
    def compdb_dir(self):
        return utils.locate_dominating_file('compile_commands.json')

class Command(object):

    def execute(self, config, args):
        raise NotImplementedError

class HelpCommand(Command):
    name = 'help'
    help_short = 'show general or command help'

    def execute(self, config, argv):
        pass

class ListCommand(Command):
    name = 'list'
    help_short = 'list database entries'

    def execute(self, config, argv):
        pass

    def _make_database(self, config):
        backend_registry = BackendRegistry(config)
        database = CompilationDatabase()
        for database_cls in backend_registry.iter():
            database.register_backend(database_cls)
        try:
            if config.build_directory_patterns:
                database.add_directory_patterns(config.build_directory_patterns)
            else:
                database.add_directory(config.compdb_dir)
        except compdb.models.ProbeError as e:
            print('{} {}: error: invalid database(s): {}'.format(__prog__, self.name, e), file=sys.stderr)
            sys.exit(1)
        return database

    def _gen_results(self, database, included_by_database, args):
        if not args.files:
            yield (None, database.get_all_compile_commands(unique=args.unique))
            yield (None, included_by_database.get_all_compile_commands())
            return
        for file in args.files:
            compile_commands = database.get_compile_commands(file, unique=args.unique)
            is_empty, compile_commands = utils.empty_iterator_wrap(compile_commands)
            if is_empty:
                path = os.path.abspath(file)
                compile_commands = included_by_database.get_compile_commands(path)
            yield (file, compile_commands)

class VersionCommand(Command):
    name = 'version'
    help_short = 'display this version of {}'.format(__prog__)

    def execute(self, config, argv):
        pass

class CommandRegistry(object):

    def __init__(self, config):
        self.config = config

    def _builtins(self):
        return [HelpCommand, ListCommand, VersionCommand]

    def get(self, name):
        """Get command class by name."""
        for command in self._builtins():
            if command.name == name:
                return command
        raise KeyError(name)

    def iter_unique(self):
        """Iterate over the commands.

        The iteration is done in order: builtin commands first.
        Duplicates are removed.
        """
        for command in self._builtins():
            yield command

class BackendRegistry(object):

    def __init__(self, config):
        self.config = config

    def _builtins(self):
        return [compdb.backend.json.JSONCompilationDatabase]

    def iter(self):
        for backend in self._builtins():
            yield backend

def show_help(parser, command_registry):
    pass

def main(argv=None):
    pass
if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))