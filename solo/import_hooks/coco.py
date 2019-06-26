
# Copyright 2018 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

import sys
import os
import imp
import re
import struct
import marshal
import ast
from coconut.convenience import parse as coco_parse
from ._compat import PY3, PY37, MAGIC, builtins, long_type, wr_long


def ast_compile(ast, filename, mode):
    """Compile AST.
    Like Python's compile, but with some special flags."""
    return compile(ast, filename, mode)


def import_buffer_to_python_ast(buf):
    """Import content from buf and return a Hy AST."""
    return ast.parse(coco_parse(buf, 'exec'))


def import_file_to_python_ast(fpath):
    """Import content from fpath and return a Hy AST."""
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            buf = f.read()
        # Strip the shebang line, if there is one.
        return import_buffer_to_python_ast(buf)
    except IOError:
        raise Exception('Some IO Error')


def import_file_to_ast(fpath, module_name):
    """Import content from fpath and return a Python AST."""
    return import_file_to_python_ast(fpath)


def import_file_to_module(module_name, fpath, loader=None):
    """Import Coconut source from fpath and put it into a Python module.
    If there's an up-to-date byte-compiled version of this module, load that
    instead. Otherwise, byte-compile the module once we're done loading it, if
    we can.
    Return the module."""

    module = None

    bytecode_path = get_bytecode_path(fpath)
    try:
        source_mtime = int(os.stat(fpath).st_mtime)
        with open(bytecode_path, 'rb') as bc_f:
            # The first 4 bytes are the magic number for the version of Python
            # that compiled this bytecode.
            bytecode_magic = bc_f.read(4)
            # Python 3.7 introduced a new flags entry in the header structure.
            if PY37:
                bc_f.read(4)
            # The next 4 bytes, interpreted as a little-endian 32-bit integer,
            # are the mtime of the corresponding source file.
            bytecode_mtime, = struct.unpack('<i', bc_f.read(4))
    except (IOError, OSError):
        pass
    else:
        if bytecode_magic == MAGIC and bytecode_mtime >= source_mtime:
            # It's a cache hit. Load the byte-compiled version.
            # As of Python 3.6, imp.load_compiled still exists, but it's
            # deprecated. So let's use SourcelessFileLoader instead.
            from importlib.machinery import SourcelessFileLoader
            module = (SourcelessFileLoader(module_name, bytecode_path).
                      load_module(module_name))

    if not module:
        # It's a cache miss, so load from source.
        sys.modules[module_name] = None
        try:
            _ast = import_file_to_ast(fpath, module_name)
            module = imp.new_module(module_name)
            module.__file__ = os.path.normpath(fpath)
            code = ast_compile(_ast, fpath, "exec")
            if not os.environ.get('PYTHONDONTWRITEBYTECODE'):
                try:
                    write_code_as_pyc(fpath, code)
                except (IOError, OSError):
                    # We failed to save the bytecode, probably because of a
                    # permissions issue. The user only asked to import the
                    # file, so don't bug them about it.
                    pass
            eval(code, module.__dict__)
        except Exception:
            sys.modules.pop(module_name, None)
            raise
        sys.modules[module_name] = module
        module.__name__ = module_name

    module.__file__ = os.path.normpath(fpath)
    if loader:
        module.__loader__ = loader
    if is_package(module_name):
        module.__path__ = []
        module.__package__ = module_name
    else:
        module.__package__ = module_name.rpartition('.')[0]

    return module


def write_code_as_pyc(fname, code):
    st = os.stat(fname)
    timestamp = long_type(st.st_mtime)

    cfile = get_bytecode_path(fname)
    try:
        os.makedirs(os.path.dirname(cfile))
    except (IOError, OSError):
        pass

    with builtins.open(cfile, 'wb') as fc:
        fc.write(MAGIC)
        if PY37:
            # With PEP 552, the header structure has a new flags field
            # that we need to fill in. All zeros preserve the legacy
            # behaviour, but should we implement reproducible builds,
            # this is where we'd add the information.
            wr_long(fc, 0)
        wr_long(fc, timestamp)
        if PY3:
            wr_long(fc, st.st_size)
        marshal.dump(code, fc)


class CoconutLoader:
    def __init__(self, path):
        self.path = path

    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]

        if not self.path:
            return

        return import_file_to_module(fullname, self.path, self)


class CoconutImporter:
    def find_on_path(self, fullname):
        fls = ["%s/__init__.coco", "%s.coco"]
        dirpath = "/".join(fullname.split("."))

        for pth in sys.path:
            pth = os.path.abspath(pth)
            for fp in fls:
                composed_path = fp % ("%s/%s" % (pth, dirpath))
                if os.path.exists(composed_path):
                    return composed_path

    def find_module(self, fullname, path=None):
        path = self.find_on_path(fullname)
        if path:
            return CoconutLoader(path)


CoconutImporter()


def is_package(module_name):
    mpath = os.path.join(*module_name.split("."))
    for path in map(os.path.abspath, sys.path):
        is_pkg = (
            os.path.exists(os.path.join(path, mpath, "__init__.py")) or
            os.path.exists(os.path.join(path, mpath, "__init__.coco"))
        )
        if is_pkg:
            return True
    return False


def get_bytecode_path(source_path):
    if PY3:
        import importlib.util
        return importlib.util.cache_from_source(source_path)
    elif hasattr(imp, "cache_from_source"):
        return imp.cache_from_source(source_path)
    else:
        # If source_path has a file extension, replace it with ".pyc".
        # Otherwise, just append ".pyc".
        d, f = os.path.split(source_path)
        return os.path.join(d, re.sub(r"(?:\.[^.]+)?\Z", ".pyc", f))
