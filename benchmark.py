# Copyright (C) The btclib developers
#
# This file is part of btclib. It is subject to the license terms in the
# LICENSE file found in the top-level directory of this distribution.
#
# No part of btclib including this file, may be copied, modified, propagated,
# or distributed except according to the terms contained in the LICENSE file.

from __future__ import annotations

import time
from typing import Callable

import coincurve
from btclib.ecc import dsa, ssa  # type: ignore
from btclib.hashes import reduce_to_hlen  # type: ignore
from btclib.to_pub_key import pub_keyinfo_from_prv_key  # type: ignore

import btclib_libsecp256k1.dsa
import btclib_libsecp256k1.ssa

prvkey = 1
pubkey = pub_keyinfo_from_prv_key(prvkey)[0]
msg = reduce_to_hlen(b"Satoshi Nakamoto")
dsa_sig = btclib_libsecp256k1.dsa.sign(msg, prvkey)
ssa_sig = btclib_libsecp256k1.ssa.sign(msg, prvkey)

# [B101:assert_used] Use of assert detected. The enclosed code will be
# removed when compiling to optimised byte code.
# https://bandit.readthedocs.io/en/1.7.4/plugins/b101_assert_used.html


def dsa_btclib() -> None:
    assert dsa.verify_(msg, pubkey, dsa_sig)  # nosec B101


def ssa_btclib() -> None:
    assert ssa.verify_(msg, pubkey, ssa_sig)  # nosec B101


def dsa_coincurve() -> None:
    assert coincurve.PublicKey(pubkey).verify(dsa_sig, msg, None)  # nosec B101


def dsa_libsecp256k1() -> None:
    assert btclib_libsecp256k1.dsa.verify(msg, pubkey, dsa_sig)  # nosec B101


def ssa_libsecp256k1() -> None:
    assert btclib_libsecp256k1.ssa.verify(msg, pubkey, ssa_sig)  # nosec B101


def benchmark(func: Callable[[], None], mult: int = 1) -> None:
    start = time.time()
    for _ in range(100 * mult):
        func()
    end = time.time()
    print(f"{func.__name__:<17}: {((end - start) / mult):.6f}")


benchmark(dsa_btclib, 100)
benchmark(dsa_coincurve, 100)
benchmark(dsa_libsecp256k1, 100)
benchmark(ssa_btclib, 100)
benchmark(ssa_libsecp256k1, 100)
