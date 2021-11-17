import pathlib
import platform
import site

import _btclib_libsecp256k1

ffi = _btclib_libsecp256k1.ffi
if platform.system() == "Windows":
    path = pathlib.Path(site.getsitepackages()[-1]).parent.parent / "dll"
    dll = path / "libsecp256k1-0.dll"
    lib = ffi.dlopen(str(dll))
else:
    lib = _btclib_libsecp256k1.lib
