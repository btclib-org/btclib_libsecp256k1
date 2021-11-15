import secrets

from . import ffi, lib

ctx = lib.secp256k1_context_create(769)


def sign(msg_bytes, prvkey):

    if isinstance(prvkey, int):
        prvkey_bytes = prvkey.to_bytes(32, "big")
    else:
        prvkey_bytes = prvkey

    keypair = ffi.new("secp256k1_keypair *")
    lib.secp256k1_keypair_create(ctx, keypair, prvkey_bytes)

    sig = ffi.new("char[64]")

    if lib.secp256k1_schnorrsig_sign(
        ctx, sig, msg_bytes, keypair, secrets.token_bytes(32)
    ):
        return ffi.unpack(sig, 64)
    return 0


def verify(msg_bytes, pubkey_bytes, signature_bytes):

    if len(pubkey_bytes) == 32:
        pubkey_bytes = b"\x02" + pubkey_bytes

    pubkey = ffi.new("secp256k1_pubkey *")
    lib.secp256k1_ec_pubkey_parse(ctx, pubkey, pubkey_bytes, len(pubkey_bytes))

    xonly_pubkey = ffi.new("secp256k1_xonly_pubkey *")
    lib.secp256k1_xonly_pubkey_from_pubkey(ctx, xonly_pubkey, ffi.new("int *"), pubkey)

    return lib.secp256k1_schnorrsig_verify(
        ctx, signature_bytes, msg_bytes, len(msg_bytes), xonly_pubkey
    )
