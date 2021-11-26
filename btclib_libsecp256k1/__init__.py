import pathlib
import platform

import _btclib_libsecp256k1

ffi = _btclib_libsecp256k1.ffi
if "lib" in dir(_btclib_libsecp256k1):
    lib = _btclib_libsecp256k1.lib
else:
    path = pathlib.Path(_btclib_libsecp256k1.__file__).parent / "btclib_libsecp256k1"
    ext = ".dll" if platform.system() == "Windows" else ".so"
    dll = path / ("libsecp256k1" + ext)
    lib = ffi.dlopen(str(dll))
