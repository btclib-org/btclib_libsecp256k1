#!/usr/bin/env python3

# Copyright (C) 2020-2021 The btclib developers
#
# This file is part of btclib. It is subject to the license terms in the
# LICENSE file found in the top-level directory of this distribution.
#
# No part of btclib including this file, may be copied, modified, propagated,
# or distributed except according to the terms contained in the LICENSE file.

__name__ = "btclib_libsecp256k1"
__version__ = "0.0.1"
__author__ = "Giacomo Caroni"
__author_email__ = "giacomo.caironi@gmail.com"
__copyright__ = "Copyright (C) 2021 Giacomo Caironi"
__license__ = "MIT License"

import _btclib_libsecp256k1
import platform
import site
import pathlib

ffi = _btclib_libsecp256k1.ffi
if platform.system() == "Windows":
    path = pathlib.Path(site.getsitepackages()[-1]).parent.parent / "dll"
    dll = path / "libsecp256k1-0.dll"
    lib = ffi.dlopen(str(dll))
else:
    lib = _btclib_libsecp256k1.lib
