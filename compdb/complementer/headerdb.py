from __future__ import print_function, unicode_literals, absolute_import
import os
import re
from compdb.backend.memory import InMemoryCompilationDatabase
from compdb.complementer import ComplementerInterface
from compdb.models import CompileCommand

def sanitize_compile_options(compile_command):
    pass

def mimic_path_relativity(path, other, default_dir):
    """If 'other' file is relative, make 'path' relative, otherwise make it
    absolute.

    """
    if os.path.isabs(other):
        return os.path.join(default_dir, path)
    if os.path.isabs(path):
        return os.path.relpath(path, default_dir)
    return path

def derive_compile_command(header_file, reference):
    pass

def get_file_includes(path):
    """Returns a tuple of (quote, filename).

    Quote is one of double quote mark '"' or opening angle bracket '<'.
    """
    includes = []
    with open(path, 'rb') as istream:
        include_pattern = re.compile(b'\\s*#\\s*include\\s+(?P<quote>["<])(?P<filename>.+?)[">]')
        for b_line in istream:
            b_match = re.match(include_pattern, b_line)
            if b_match:
                u_quote = b_match.group('quote').decode('ascii')
                try:
                    u_filename = b_match.group('filename').decode('utf-8')
                except UnicodeDecodeError:
                    u_filename = b_match.group('filename').decode('latin-1')
                includes.append((u_quote, u_filename))
    return includes

def extract_include_dirs(compile_command):
    pass

def get_implicit_header_search_path(compile_command):
    return os.path.dirname(os.path.join(compile_command.directory, compile_command.file))
SUBWORD_SEPARATORS_RE = re.compile('[^A-Za-z0-9]')
SUBWORD_CAMEL_SPLIT_RE = re.compile('\n.+?                          # capture text instead of discarding (#1)\n(\n  (?:(?<=[a-z0-9]))          # non-capturing positive lookbehind assertion\n  (?=[A-Z])                  # match first uppercase letter without consuming\n|\n  (?<=[A-Z])                 # an upper char should prefix\n  (?=[A-Z][a-z0-9])          # an upper char, lookahead assertion: does not\n                             # consume the char\n|\n$                            # ignore capture text #1\n)', re.VERBOSE)

def subword_split(name):
    """Split name into subword.

    Split camelCase, lowercase_underscore, and alike into an array of word.

    Subword is the vocabulary stolen from Emacs subword-mode:
    https://www.gnu.org/software/emacs/manual/html_node/ccmode/Subword-Movement.html

    """
    words = []
    for camel_subname in re.split(SUBWORD_SEPARATORS_RE, name):
        matches = re.finditer(SUBWORD_CAMEL_SPLIT_RE, camel_subname)
        words.extend([m.group(0) for m in matches])
    return words

def lcsubstring_length(a, b):
    """Find the length of the longuest contiguous subsequence of subwords.

    The name is a bit of a misnomer.

    """
    pass

def score_other_file(a, b):
    """Score the similarity of the given file to the other file.

    Paths are expected absolute and normalized.
    Note that the score can be a negative value.
    """
    pass

class _Data(object):
    __slots__ = ['score', 'compile_command', 'db_idx']

    def __init__(self, score=0, compile_command=None, db_idx=-1):
        self.score = score
        if compile_command is None:
            self.compile_command = {}
        else:
            self.compile_command = compile_command
        self.db_idx = db_idx

def _make_headerdb1(compile_commands_iter, db_files, db_idx, header_mapping):
    for compile_command in compile_commands_iter:
        implicit_search_path = get_implicit_header_search_path(compile_command)
        header_search_paths = extract_include_dirs(compile_command)
        src_file = compile_command.normfile
        for quote, filename in get_file_includes(src_file):
            header_abspath = None
            if quote == '"':
                candidate = os.path.normpath(os.path.join(implicit_search_path, filename))
                if os.path.isfile(candidate):
                    header_abspath = candidate
            if not header_abspath:
                for search_path in header_search_paths:
                    candidate = os.path.normpath(os.path.join(search_path, filename))
                    if os.path.isfile(candidate):
                        header_abspath = candidate
                        break
                else:
                    continue
            norm_abspath = os.path.normpath(header_abspath)
            if norm_abspath in db_files:
                continue
            score = score_other_file(src_file, norm_abspath)
            try:
                data = header_mapping[norm_abspath]
            except KeyError:
                data = _Data(score=score - 1)
                header_mapping[norm_abspath] = data
            if score > data.score:
                data.score = score
                data.compile_command = derive_compile_command(norm_abspath, compile_command)
                data.db_idx = db_idx

def make_headerdb(layers):
    pass

class Complementer(ComplementerInterface):

    def complement(self, layers):
        return make_headerdb(layers)