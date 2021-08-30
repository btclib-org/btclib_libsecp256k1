import cffi
import glob
import os

for file in glob.glob("_btclib_libsecp256k1.*"):
    os.remove(file)

ffi = cffi.FFI()

code = """
typedef struct secp256k1_context_struct secp256k1_context;

secp256k1_context* secp256k1_context_create(
    unsigned int flags
);
"""
ffi.cdef(code)

ffi.set_source(
    "_btclib_libsecp256k1",
    '#include "secp256k1.h"',
    extra_objects=["libsecp256k1.so.0"],
    # include_dirs=[include_dir.as_posix()],
    # libraries=["secp256k1"],
    # library_dirs=[shared_dir.as_posix()]
    # libraries=["stddef"],
    extra_link_args=["-Wl,-rpath,."],
)

ffi.compile(verbose=True)

import _btclib_libsecp256k1
