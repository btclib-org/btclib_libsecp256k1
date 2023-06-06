# Copyright (C) The btclib developers
#
# This file is part of btclib. It is subject to the license terms in the
# LICENSE file found in the top-level directory of this distribution.
#
# No part of btclib including this file, may be copied, modified, propagated,
# or distributed except according to the terms contained in the LICENSE file.

import sys

from setuptools import setup  # type: ignore

setup(cffi_modules=[] if "egg_info" in sys.argv else ["scripts/cffi_build.py:ffi"])
