from __future__ import print_function, unicode_literals, absolute_import
import logging
import os
import re
from collections import deque
import compdb.complementer.headerdb
import compdb.utils
from compdb.models import CompilationDatabaseInterface
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError
logger = logging.getLogger(__name__)

class IncludeDirective(object):
    __slots__ = ['header_name', 'is_angled', 'search_path', 'source_file', 'source_is_main_file']

    def __init__(self, header_name, is_angled, search_path, source_file, source_is_main_file):
        self.header_name = header_name
        self.is_angled = is_angled
        self.search_path = search_path
        self.source_file = source_file
        self.source_is_main_file = source_is_main_file

class Preprocessor(object):

    def __init__(self):
        self.callbacks = []
        self._processed = set()

    def register_include_callback(self, cb):
        self.callbacks.append(cb)

    def preprocess(self, compile_command):
        pass

    def _iter_includes(self, path):
        try:
            with open(path, 'rb') as istream:
                include_pattern = re.compile(b'\\s*#\\s*include\\s+(?P<quote>["<])(?P<filename>.+?)[">]')
                for b_line in istream:
                    b_match = re.match(include_pattern, b_line)
                    if not b_match:
                        continue
                    u_quote = b_match.group('quote').decode('ascii')
                    b_filename = b_match.group('filename')
                    try:
                        u_filename = b_filename.decode('utf-8')
                    except UnicodeDecodeError:
                        u_filename = b_filename.decode('latin-1')
                    yield (u_quote, u_filename)
        except FileNotFoundError as exc:
            logger.warning('%s', exc)

    def _iter_search_paths(self, is_angled, search_paths, includer):
        if not is_angled:
            yield os.path.dirname(includer)
        for search_path in search_paths:
            yield search_path

    def _resolve_search_path(self, header_name, is_angled, search_paths, includer):
        for search_path in self._iter_search_paths(is_angled, search_paths, includer):
            if os.path.isfile(os.path.join(search_path, header_name)):
                return search_path

class IncludedByDatabase(CompilationDatabaseInterface):
    """Represent included-by relationship of headers

A graph represented implemented as an adjacent list.

See also https://www.python.org/doc/essays/graphs/
"""

    def __init__(self, graph, database):
        self.graph = graph
        self.database = database
        self.__db_index = None

    def __repr__(self):
        return '<IncludedByGraph: graph = {}, database = {}>'.format(self.graph, self.database)

    def __str__(self):
        return self.__repr__()

    def _bfs_walk_from(self, path):
        to_visit = deque((path,))
        visited = {path}
        depth_checkpoint = path
        depth = 0
        while True:
            try:
                node = to_visit.popleft()
            except IndexError:
                return
            if node == depth_checkpoint:
                depth_checkpoint = None
                depth += 1
            for adjacent_node in self.graph.get(node, []):
                if adjacent_node in visited:
                    continue
                yield (adjacent_node, depth)
                visited.add(adjacent_node)
                to_visit.append(adjacent_node)
                if not depth_checkpoint:
                    depth_checkpoint = adjacent_node

    @property
    def _db_index(self):
        if self.__db_index is None:
            self.__db_index = frozenset(self.database.get_all_files())
        return self.__db_index

    def _find_best(self, path):
        best = None
        best_score = None
        last_depth = 0
        for includer, depth in self._bfs_walk_from(path):
            if depth != last_depth and best:
                break
            if includer not in self._db_index:
                continue
            score = compdb.complementer.headerdb.score_other_file(path, includer)
            if best_score is None or score > best_score:
                best_score = score
                best = includer
        return best

    def get_compile_commands(self, path):
        best = self._find_best(path)
        if best:
            for compile_command in self.database.get_compile_commands(best):
                yield compdb.complementer.headerdb.derive_compile_command(path, compile_command)
                break

    def get_all_files(self):
        return iter(self.graph.keys())

    def all_files_unique(self):
        return True

    def get_all_compile_commands(self):
        for file in self.get_all_files():
            for compile_command in self.get_compile_commands(file):
                yield compile_command

class IncludedByGraphFiller(object):

    def __init__(self, included_by_graph, database):
        self.included_by_graph = included_by_graph
        self.database = database
        self.db_files = None

    def include_callback(self, include_directive):
        pass

    def add(self, includee, includer):
        try:
            lst = self.included_by_graph[includee]
            if includer not in lst:
                lst.append(includer)
        except KeyError:
            self.included_by_graph[includee] = [includer]

class IncludeIndexBuilder(object):

    def build(self, database):
        pass