from __future__ import print_function, unicode_literals, absolute_import
import codecs
import contextlib
import itertools
import os
import re
import sys
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

def empty_iterator_wrap(iterator):
    try:
        first = next(iterator)
    except StopIteration:
        return (True, None)
    return (False, itertools.chain([first], iterator))

@contextlib.contextmanager
def suppress(*exceptions):
    """Context manager to suppress specified exceptions
         with suppress(OSError):
             os.remove(somefile)
    """
    try:
        yield
    except exceptions:
        pass

def re_fullmatch(regex, string, flags=0):
    """Emulate python-3.4 re.fullmatch()."""
    return re.match('(?:' + regex + ')\\Z', string, flags=flags)

def stdout_unicode_writer():
    pass

def get_friendly_path(path):
    pass

def logical_abspath(p):
    """Same as os.path.abspath,
    but use the logical current working to expand relative paths.
    """
    pass

def locate_dominating_file(name, start_dir=os.curdir):
    pass