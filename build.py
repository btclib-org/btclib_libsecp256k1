import cffi
import pathlib
import sys
import os
import re
import glob
import subprocess
from subprocess import Popen, PIPE

on_win = sys.platform.startswith("win")

"""Remove any built objects"""
patterns = ("*.o", "*.so", "*.obj", "*.dll", "*.exp", "*.lib", "cffi_example*")
for file_pattern in patterns:
    for file in glob.glob(file_pattern):
        os.remove(file)

subprocess.call("./autogen.sh".split(), cwd="secp256k1")
command = "./configure --disable-tests --disable-benchmark --enable-experimental --enable-module-schnorrsig"
subprocess.call(command.split(), cwd="secp256k1")
subprocess.call("make".split(), cwd="secp256k1")

ffi = cffi.FFI()

headers = ["secp256k1_schnorrsig.h"]

ffi_header = ""
for h in headers:
    ffi_header += f'#include "secp256k1/include/{h}"' + "\n"

command = "gcc -P -E -".split()
p = Popen(command, stdin=PIPE, stdout=PIPE)
definitions = p.communicate(input=ffi_header.encode())[0].decode()
definitions = re.sub(" __.*;", ";", definitions)
definitions = re.sub("__.*\)\) ", "", definitions)
definitions = "\n".join(definitions.splitlines()[7:])
ffi.cdef(definitions)


ffi.set_source(
    "btclib_libsecp256k1",
    ffi_header,
    extra_objects=["secp256k1/.libs/libsecp256k1.so"],
    # include_dirs=[include_dir.as_posix()],
    # libraries=["secp256k1"],
    # library_dirs=["secp256k1/.libs/"],
    # libraries=["stddef"],
    extra_link_args=["-Wl,-rpath,secp256k1/.libs/"],
)

ffi.compile(verbose=True)
