"""
Pure python cffi bindings to libsecp256k1: https://github.com/bitcoin-core/secp256k1
"""

import pathlib

import _btclib_libsecp256k1  # type: ignore

ffi = _btclib_libsecp256k1.ffi
if "lib" in dir(_btclib_libsecp256k1):
    lib = _btclib_libsecp256k1.lib
else:
    path = pathlib.Path(_btclib_libsecp256k1.__file__).parent / "btclib_libsecp256k1"
    for file in path.iterdir():
        suffixes = [".dll", ".so", ".dylib"]
        if file.stem == "libsecp256k1" and file.suffix in suffixes:
            lib = ffi.dlopen(str(file))
            break
