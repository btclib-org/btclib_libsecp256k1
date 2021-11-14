import glob
import os
import pathlib
import re
import subprocess
import sys
from subprocess import PIPE, Popen
from sysconfig import get_paths

import cffi

windows = False
if "--plat-name=win-amd64" in sys.argv:
    windows = True

secp256k1_dir = pathlib.Path(__file__).parent.resolve() / "secp256k1"
libs_dir = secp256k1_dir / ".libs"
include_dir = secp256k1_dir / "include"
gcc = "gcc" if not windows else "x86_64-w64-mingw32-gcc"
filename = "_btclib_libsecp256k1"
libraries = ["secp256k1"]
library_dirs = [libs_dir.as_posix()]

patterns = ("*.o", "*.so", "*.obj", "*.dll", "*.exp", "*.lib")
for file_pattern in patterns:
    for file in glob.glob(file_pattern):
        os.remove(file)

subprocess.call(["bash", "autogen.sh"], cwd=secp256k1_dir)
with open(secp256k1_dir / "Makefile.am", "a") as f:
    f.write("\nLDFLAGS = -no-undefined\n")
command = [
    "bash",
    "configure",
    "--disable-tests",
    "--disable-benchmark",
    "--enable-experimental",
    "--enable-module-schnorrsig",
    "--with-pic",
    "--disable-shared",
]
if windows:
    command.append("--host=x86_64-w64-mingw32")
subprocess.call(command, cwd=secp256k1_dir)
subprocess.call(["make"], cwd=secp256k1_dir)

ffi = cffi.FFI()

headers = ["secp256k1.h", "secp256k1_schnorrsig.h"]

ffi_header = ""
for h in headers:
    location = secp256k1_dir / "include" / h
    ffi_header += f'#include "{location.as_posix()}"' + "\n"

command = f"{gcc} -P -E -".split()
p = Popen(command, stdin=PIPE, stdout=PIPE)
definitions = p.communicate(input=ffi_header.encode())[0].decode()
definitions = re.sub("#pragma[\s\S]*?typedef", "typedef", definitions)
definitions = re.sub("__.*?__", "", definitions)
definitions = re.sub("\(\(\)\)", "", definitions)
definitions = re.sub("\(\(\([0-9]\)\)\)", "", definitions)
definitions = re.sub("typedef [\s\S]*?max_align_t;", "", definitions)
definitions = definitions.replace("\r", "")
ffi.cdef(definitions)

ffi.set_source(filename, ffi_header, libraries=libraries, library_dirs=library_dirs)

ffi.compile(verbose=True)

