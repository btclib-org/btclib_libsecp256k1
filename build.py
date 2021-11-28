import glob
import os
import pathlib
import platform
import re
import shutil
import subprocess
import sys
from subprocess import PIPE, Popen

import cffi

windows = False
if "--plat-name=win_amd64" in sys.argv or platform.system() == "Windows":
    windows = True
static = True
if windows or not pathlib.Path(".git").exists():
    static = False

secp256k1_dir = pathlib.Path(__file__).parent.resolve() / "secp256k1"
libs_dir = secp256k1_dir / ".libs"
include_dir = secp256k1_dir / "include"
filename = "_btclib_libsecp256k1"
libraries = ["secp256k1"]
library_dirs = [libs_dir.as_posix()]
headers = ["secp256k1.h", "secp256k1_schnorrsig.h"]


def clean():
    if (secp256k1_dir / ".libs").exists():
        subprocess.call(["make", "clean"], cwd=secp256k1_dir)
    for pattern in ["_btclib_libsecp256k1.*", "btclib_libsecp256k1/libsecp256k1.*"]:
        for file in glob.glob(pattern):
            os.remove(file)


def build_c():
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
    ]
    if windows:
        command.append("--host=x86_64-w64-mingw32")
    if static:
        command.append("--disable-shared")
    subprocess.call(command, cwd=secp256k1_dir)
    subprocess.call(["make"], cwd=secp256k1_dir)
    if not static:
        for file in libs_dir.iterdir():
            print(file)
            if file.suffix not in [".dll", ".so", ".dylib"]:
                continue
            new = "libsecp256k1" + file.suffix
            shutil.copy(file, str(pathlib.Path("btclib_libsecp256k1") / new))
            break


def generate_def(headers):
    ffi_header = ""
    for h in headers:
        location = secp256k1_dir / "include" / h
        ffi_header += f'#include "{location.as_posix()}"' + "\n"

    command = f"gcc -P -E -".split()
    p = Popen(command, stdin=PIPE, stdout=PIPE)
    definitions = p.communicate(input=ffi_header.encode())[0].decode()
    definitions = re.sub("#pragma[\s\S]*?typedef", "typedef", definitions)
    definitions = re.sub("__.*?__", "", definitions)
    definitions = re.sub("\(\(\)\)", "", definitions)
    definitions = re.sub("\(\(\([0-9]\)\)\)", "", definitions)
    definitions = re.sub("typedef [\s\S]*?max_align_t;", "", definitions)
    definitions = definitions.replace("\r", "")
    return ffi_header, definitions


def create_cffi(static):
    clean()
    build_c()
    ffi = cffi.FFI()
    ffi_header, definitions = generate_def(headers)
    ffi.cdef(definitions)
    if static:
        ffi.set_source(
            filename,
            ffi_header,
            libraries=libraries,
            library_dirs=library_dirs,
        )
    else:
        ffi.set_source(filename, None)
    return ffi


ffi = create_cffi(static)
if __name__ == "__main__":
    ffi.compile(verbose=True)
