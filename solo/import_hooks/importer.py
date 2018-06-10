import ast
from importlib._bootstrap import _init_module_attrs, ModuleSpec
from importlib.machinery import PathFinder, SourceFileLoader, SourcelessFileLoader
from importlib import util
from pathlib import Path
import os
from types import ModuleType

import sys
import struct
from typing import Optional, Sequence

from .hooks import apply_transformers


PY37 = sys.version_info >= (3, 7)


class MyLoader(SourceFileLoader):
    def create_module(self, spec: ModuleSpec):
        """ A method that returns the module object to use when importing a module.
        This method may return None, indicating that default module creation semantics should take place.
        https://docs.python.org/3/library/importlib.html#importlib.abc.Loader.create_module
        https://github.com/hylang/hy/blob/master/hy/importer.py
        """
        bytecode_path = Path(util.cache_from_source(spec.origin))
        module = None
        try:
            source_mtime = int(os.stat(spec.origin).st_mtime)
            with bytecode_path.open('rb') as f:
                # The first 4 bytes are the magic number for the version of Python
                # that compiled this bytecode.
                bytecode_magic = f.read(4)
                # Python 3.7 introduced a new flags entry in the header structure.
                if PY37:
                    f.read(4)
                # The next 4 bytes, interpreted as a little-endian 32-bit integer,
                # are the mtime of the corresponding source file.
                bytecode_mtime, = struct.unpack('<i', f.read(4))
        except (IOError, OSError):
            pass
        else:
            if bytecode_magic == util.MAGIC_NUMBER and bytecode_mtime >= source_mtime:
                # It's a cache hit. Load the byte-compiled version.
                # As of Python 3.6, imp.load_compiled still exists, but it's
                # deprecated. So let's use SourcelessFileLoader instead.
                module = (SourcelessFileLoader(spec.name, str(bytecode_path)).
                          create_module(spec.name))
        if not module:
            # It's a cache miss, so it will be loaded from source and executed in exec_module().
            # It will be
            module = ModuleType(spec.name)
            module = _init_module_attrs(spec, module, override=True)
        return module

    def exec_module(self, module: ModuleType):
        spec = module.__spec__
        with Path(spec.origin).open('rb') as f:
            source_ast = ast.parse(f.read(), spec.origin)

        source_ast = apply_transformers(source_ast)

        try:
            code = compile(source_ast, spec.origin, "exec")
        except (SyntaxError, ValueError):
            # raises SyntaxError if the compiled source is invalid,
            # and ValueError if the source contains null bytes.
            raise
        eval(code, module.__dict__)


class MyImporter(PathFinder):
    @classmethod
    def find_spec(cls, fullname: str, path: Optional[Sequence[str]] = None, target=None):
        if not fullname.startswith('solo'):
            # delegate to default importers
            return None
        spec = super(MyImporter, cls).find_spec(fullname, path, target)
        orig_loader = spec.loader
        new_loader = MyLoader(fullname=orig_loader.name,
                              path=orig_loader.path)
        spec.loader = new_loader
        return spec


def activate():
    sys.meta_path.insert(0, MyImporter)
