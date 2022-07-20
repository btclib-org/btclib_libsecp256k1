"""
Secp256k1 point multiplication
"""

from typing import Union

from . import ffi, lib

ctx = lib.secp256k1_context_create(769)


def mult(num: Union[bytes, int]) -> bytes:
    "Multply the generator point"

    if isinstance(num, int):
        num_bytes = num.to_bytes(32, "big")
    else:
        num_bytes = num

    point = ffi.new("secp256k1_pubkey *")
    lib.secp256k1_ec_pubkey_create(ctx, point, num_bytes)

    output = ffi.new("char[65]")
    length = ffi.new("size_t *", 65)

    lib.secp256k1_ec_pubkey_serialize(ctx, output, length, point, 2)

    result = ffi.unpack(output, 65).hex()

    return (int(result[2:66], 16), int(result[66:130], 16))
