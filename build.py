import cffi
import pathlib
import os
import re
import glob
import subprocess
from subprocess import Popen, PIPE

secp256k1_dir = pathlib.Path(__file__).parent.resolve() / "secp256k1"
libs_dir = secp256k1_dir / ".libs"
include_dir = secp256k1_dir / "include"

patterns = ("*.o", "*.so", "*.obj", "*.dll", "*.exp", "*.lib", "cffi_example*")
for file_pattern in patterns:
    for file in glob.glob(file_pattern):
        os.remove(file)

subprocess.call(["./autogen.sh"], cwd=secp256k1_dir)
command = [
    "./configure",
    "--disable-shared",
    "--with-pic",
    " --disable-tests",
    " --disable-benchmark",
    " --enable-experimental",
    " --enable-module-schnorrsig",
]
subprocess.call(command, cwd=secp256k1_dir)
subprocess.call(["make"], cwd=secp256k1_dir)

ffi = cffi.FFI()

headers = ["secp256k1_schnorrsig.h"]

ffi_header = ""
for h in headers:
    location = secp256k1_dir / "include" / h
    ffi_header += f'#include "{location.as_posix()}"' + "\n"
# ffi_header += "#define PY_USE_BUNDLED"

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

if __name__ == "__main__":
    ffi.compile(verbose=True)
