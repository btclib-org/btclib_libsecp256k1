import secrets
from typing import Optional, Union

from . import ffi, lib

ctx = lib.secp256k1_context_create(769)


def mult(prvkey: Union[bytes, int]) -> bytes:

    if isinstance(prvkey, int):
        prvkey_bytes = prvkey.to_bytes(32, "big")
    else:
        prvkey_bytes = prvkey

    pubkey = ffi.new("secp256k1_pubkey *")
    lib.secp256k1_ec_pubkey_create(ctx, pubkey, prvkey_bytes)

    output = ffi.new("char[65]")
    length = ffi.new("size_t *", 65)

    lib.secp256k1_ec_pubkey_serialize(ctx, output, length, pubkey, 2)

    r = ffi.unpack(output, 65).hex()

    return (int(r[2:66], 16), int(r[66:130], 16))