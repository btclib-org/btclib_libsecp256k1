# Copyright (C) The btclib developers
#
# This file is part of btclib. It is subject to the license terms in the
# LICENSE file found in the top-level directory of this distribution.
#
# No part of btclib including this file, may be copied, modified, propagated,
# or distributed except according to the terms contained in the LICENSE file.

import time
from typing import Any, Callable

import coincurve  # type: ignore
from btclib.ecc import dsa, ssa  # type: ignore
from btclib.hashes import reduce_to_hlen  # type: ignore
from btclib.to_pub_key import pub_keyinfo_from_prv_key  # type: ignore

import btclib_libsecp256k1.dsa
import btclib_libsecp256k1.ssa

prvkey = 1

pubkey_bytes = pub_keyinfo_from_prv_key(prvkey)[0]
msg_bytes = reduce_to_hlen(b"Satoshi Nakamoto")
dsa_signature_bytes = btclib_libsecp256k1.dsa.sign(msg_bytes, prvkey)
ssa_signature_bytes = btclib_libsecp256k1.ssa.sign(msg_bytes, prvkey)


def dsa_btclib() -> None:
    assert dsa.verify_(msg_bytes, pubkey_bytes, dsa_signature_bytes)


def ssa_btclib() -> None:
    assert ssa.verify_(msg_bytes, pubkey_bytes, ssa_signature_bytes)


def dsa_coincurve() -> None:
    assert coincurve.PublicKey(pubkey_bytes).verify(
        dsa_signature_bytes, msg_bytes, None
    )


def dsa_libsecp256k1() -> None:
    assert btclib_libsecp256k1.dsa.verify(msg_bytes, pubkey_bytes, dsa_signature_bytes)


def ssa_libsecp256k1() -> None:
    assert btclib_libsecp256k1.ssa.verify(msg_bytes, pubkey_bytes, ssa_signature_bytes)


def benchmark(func: Callable[[], Any], mult: int = 1) -> None:
    start = time.time()
    for _ in range(100 * mult):
        func()
    end = time.time()
    print(f"{func.__name__}:", (end - start) / mult)


benchmark(dsa_btclib, 100)
benchmark(dsa_coincurve, 100)
benchmark(dsa_libsecp256k1, 100)
benchmark(ssa_btclib, 100)
benchmark(ssa_libsecp256k1, 100)
