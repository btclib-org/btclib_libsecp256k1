import glob
import os
import pathlib
import re
import subprocess
import sys
from subprocess import PIPE, Popen

import cffi

secp256k1_dir = pathlib.Path(__file__).parent.resolve() / "secp256k1"
libs_dir = secp256k1_dir / ".libs"
include_dir = secp256k1_dir / "include"

patterns = ("*.o", "*.so", "*.obj", "*.dll", "*.exp", "*.lib")
for file_pattern in patterns:
    for file in glob.glob(file_pattern):
        os.remove(file)

subprocess.call(["bash", "autogen.sh"], cwd=secp256k1_dir)
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
for x in sys.argv:
    if x.startswith("--plat-name="):
        if x.strip("--plat-name=") == "win_amd64":
            command.append("--host=x86_64-w64-mingw32")
subprocess.call(command, cwd=secp256k1_dir)
subprocess.call(["make"], cwd=secp256k1_dir)

ffi = cffi.FFI()

headers = ["secp256k1.h", "secp256k1_schnorrsig.h"]

ffi_header = ""
for h in headers:
    location = secp256k1_dir / "include" / h
    ffi_header += f'#include "{location.as_posix()}"' + "\n"

command = "gcc -P -E -".split()
p = Popen(command, stdin=PIPE, stdout=PIPE)
definitions = p.communicate(input=ffi_header.encode())[0].decode()
definitions = re.sub(" __.*;", ";", definitions)
definitions = re.sub("__.*\)\) ", "", definitions)
definitions = "\n".join(definitions.splitlines()[7:])
ffi.cdef(definitions)


ffi.set_source(
    "_btclib_libsecp256k1",
    ffi_header,
    libraries=["secp256k1"],
    library_dirs=[libs_dir.as_posix()],
)

ffi.compile(verbose=True)

if __name__ == "__main__":
    import benchmark