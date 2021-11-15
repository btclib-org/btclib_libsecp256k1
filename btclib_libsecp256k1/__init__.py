#!/usr/bin/env python3

# Copyright (C) 2020-2021 The btclib developers
#
# This file is part of btclib. It is subject to the license terms in the
# LICENSE file found in the top-level directory of this distribution.
#
# No part of btclib including this file, may be copied, modified, propagated,
# or distributed except according to the terms contained in the LICENSE file.

name = "btclib_libsecp256k1"
__version__ = "0.0.1"
__author__ = "The btclib developers"
__author_email__ = "devs@btclib.org"
__copyright__ = "Copyright (C) 2021 The btclib developers"
__license__ = "MIT License"

import _btclib_libsecp256k1

ffi = _btclib_libsecp256k1.ffi
lib = _btclib_libsecp256k1.lib
