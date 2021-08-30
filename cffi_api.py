import cffi
import pathlib
import sys
import os
import re
import glob
import subprocess

on_win = sys.platform.startswith("win")

"""Remove any built objects"""
patterns = ("*.o", "*.so", "*.obj", "*.dll", "*.exp", "*.lib", "cffi_example*")
for file_pattern in patterns:
    for file in glob.glob(file_pattern):
        os.remove(file)

subprocess.call("./autogen.sh".split(), cwd="secp256k1")
command = "./configure --enable-experimental --enable-module-schnorrsig"
subprocess.call(command.split(), cwd="secp256k1")
subprocess.call("make".split(), cwd="secp256k1")

ffi = cffi.FFI()

secp256k1 = pathlib.Path().resolve() / "secp256k1"
include_dir = secp256k1 / "include"
h_file_name = include_dir / "secp256k1.h"
shared_dir = secp256k1 / ".libs"
shared_lib = shared_dir / "libsecp256k1.so"
shared_lib2 = shared_dir / "libsecp256k1.so.0"

# with open(h_file_name) as h_file:
#     lns = h_file.read().splitlines()
#     flt = filter(lambda ln: not re.match(r" *#", ln), lns)
#     flt = map(lambda ln: ln.replace("EXPORT_SYMBOL ", ""), flt)
#     ffi.cdef(str("\n").join(flt))
#     # ffi.cdef(str("\n").join(lns))

code = """
typedef struct secp256k1_context_struct secp256k1_context;

secp256k1_context* secp256k1_context_create(
    unsigned int flags
);
"""
ffi.cdef(code)

ffi.set_source(
    "btclib_libsecp256k1",
    f'#include "{h_file_name.as_posix()}"',
    # extra_objects=[shared_lib.as_posix(), shared_lib2.as_posix()],
    # include_dirs=[include_dir.as_posix()],
    # libraries=["secp256k1"],
    # library_dirs=[shared_dir.as_posix()]
    # libraries=["stddef"],
)

ffi.compile(verbose=True)
