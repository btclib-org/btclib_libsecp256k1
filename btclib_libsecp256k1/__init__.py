"""
Pure python cffi bindings to libsecp256k1: https://github.com/bitcoin-core/secp256k1
"""


import pathlib

import _btclib_libsecp256k1  # type: ignore
import dsa  # type: ignore
import mult  # type: ignore
import ssa  # type: ignore

ffi = _btclib_libsecp256k1.ffi
if "lib" in dir(_btclib_libsecp256k1):
    lib = _btclib_libsecp256k1.lib
else:
    path = pathlib.Path(_btclib_libsecp256k1.__file__).parent / "btclib_libsecp256k1"
    suffixes = [".dll", ".so", ".dylib"]
    for file in path.iterdir():
        if file.stem == "libsecp256k1" and file.suffix in suffixes:
            lib = ffi.dlopen(str(file))
            break

__all__ = ["dsa", "ssa", "mult"]
