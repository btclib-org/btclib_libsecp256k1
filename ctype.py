# ctypes_test.py
import ctypes
import pathlib

libname = pathlib.Path().absolute() / "secp256k1" / ".libs" / "libsecp256k1.so"
c_lib = ctypes.CDLL(libname)
