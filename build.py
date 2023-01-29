# Copyright (C) The btclib developers
#
# This file is part of btclib. It is subject to the license terms in the
# LICENSE file found in the top-level directory of this distribution.
#
# No part of btclib including this file, may be copied, modified, propagated,
# or distributed except according to the terms contained in the LICENSE file.

import glob
import os
import pathlib
import platform
import re
import shutil

# [B404:blacklist] Consider possible security implications associated with the subprocess module.
# https://bandit.readthedocs.io/en/1.7.4/blacklists/blacklist_imports.html#b404-import-subprocess
import subprocess  # nosec B404
import sys
from subprocess import PIPE, Popen  # nosec B404

import cffi

windows = "--plat-name=win_amd64" in sys.argv or platform.system() == "Windows"
static = bool(not windows and pathlib.Path(".git").exists())
static = static and os.environ.get("BTCLIB_LIBSECP256K1_DYNAMIC", "false") != "true"
secp256k1_dir = pathlib.Path(__file__).parent.resolve() / "secp256k1"
libs_dir = secp256k1_dir / ".libs"
include_dir = secp256k1_dir / "include"
filename = "_btclib_libsecp256k1"
libraries = ["secp256k1"]
library_dirs = [libs_dir.as_posix()]
headers = ["secp256k1.h", "secp256k1_extrakeys.h", "secp256k1_schnorrsig.h"]


# [B603:subprocess_without_shell_equals_true] subprocess call - check for execution of untrusted input.
# https://bandit.readthedocs.io/en/1.7.4/plugins/b603_subprocess_without_shell_equals_true.html

# [B607:start_process_with_partial_path] Starting a process with a partial executable path
# https://bandit.readthedocs.io/en/1.7.4/plugins/b607_start_process_with_partial_path.html


def clean() -> None:
    subprocess.call(["git", "reset", "--hard"], cwd=secp256k1_dir)  # nosec B603 B607
    subprocess.call(["git", "clean", "-fxd"], cwd=secp256k1_dir)  # nosec B603 B607
    if (secp256k1_dir / ".libs").exists():
        subprocess.call(["make", "clean"], cwd=secp256k1_dir)  # nosec B603 B607
    for pattern in ["_btclib_libsecp256k1.*", "btclib_libsecp256k1/libsecp256k1.*"]:
        for file in glob.glob(pattern):
            os.remove(file)


def build_c() -> None:
    subprocess.call(["bash", "autogen.sh"], cwd=secp256k1_dir)  # nosec B603 B607
    with open(secp256k1_dir / "Makefile.am", "a") as f:
        f.write("\nLDFLAGS = -no-undefined\n")
    command = [
        "bash",
        "configure",
        "--disable-tests",
        "--disable-benchmark",
        "--enable-experimental",
        "--enable-module-schnorrsig",
        "--enable-external-default-callbacks",
        "--with-pic",
    ]
    if windows:
        command.append("--host=x86_64-w64-mingw32")
    if static:
        command.append("--disable-shared")
    subprocess.call(command, cwd=secp256k1_dir)  # nosec B603

    # add source for safe callback
    with open(secp256k1_dir / "src" / "secp256k1.c", "a") as f:
        f.write(
            """
        void secp256k1_default_illegal_callback_fn(const char* str, void* data) {
        }
        void secp256k1_default_error_callback_fn(const char* str, void* data) {
        }
        """
        )

    subprocess.call(["make"], cwd=secp256k1_dir)  # nosec B603 B607
    subprocess.call(["git", "reset", "--hard"], cwd=secp256k1_dir)  # nosec B603 B607
    if not static:
        for file in libs_dir.iterdir():
            print(file)
            if file.suffix not in [".dll", ".so", ".dylib"]:
                continue
            new = f"libsecp256k1{file.suffix}"
            shutil.copy(file, str(pathlib.Path("btclib_libsecp256k1") / new))
            break


def generate_def():
    ffi_header = ""
    for h in headers:
        location = secp256k1_dir / "include" / h
        with open(location) as f:
            ffi_header += f.read() + "\n"

    ffi_header = re.sub(r"#include .*", "", ffi_header)

    command = "gcc -P -E -D SECP256K1_BUILD  -".split()
    with Popen(command, stdin=PIPE, stdout=PIPE) as p:  # nosec B603
        definitions = p.communicate(input=ffi_header.encode())[0].decode()
        definitions = definitions.replace(
            '__attribute__ ((visibility ("default")))', ""
        )
        definitions = definitions.replace(
            "__attribute__ ((__warn_unused_result__))", ""
        )
        return ffi_header, definitions


def create_cffi(static):
    clean()
    build_c()
    ffi = cffi.FFI()
    ffi_header, definitions = generate_def()
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
