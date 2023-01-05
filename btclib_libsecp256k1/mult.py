# Copyright (C) The btclib developers
#
# This file is part of btclib. It is subject to the license terms in the
# LICENSE file found in the top-level directory of this distribution.
#
# No part of btclib including this file, may be copied, modified, propagated,
# or distributed except according to the terms contained in the LICENSE file.

"""Secp256k1 point multiplication."""

from __future__ import annotations

from . import ffi, lib

ctx = lib.secp256k1_context_create(769)


def mult(num: bytes | int) -> tuple[int, int]:
    """Multply the generator point."""

    num_bytes = num.to_bytes(32, "big") if isinstance(num, int) else num
    point = ffi.new("secp256k1_pubkey *")
    lib.secp256k1_ec_pubkey_create(ctx, point, num_bytes)

    output = ffi.new("char[65]")
    length = ffi.new("size_t *", 65)

    lib.secp256k1_ec_pubkey_serialize(ctx, output, length, point, 2)

    result = ffi.unpack(output, 65).hex()

    return (int(result[2:66], 16), int(result[66:130], 16))
