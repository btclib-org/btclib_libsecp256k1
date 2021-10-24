import secrets

import _btclib_libsecp256k1

ctx = _btclib_libsecp256k1.lib.secp256k1_context_create(769)


def sign(msg_bytes, prvkey):

    if isinstance(prvkey, int):
        prvkey_bytes = prvkey.to_bytes(32, "big")
    else:
        prvkey_bytes = prvkey

    keypair = _btclib_libsecp256k1.ffi.new("secp256k1_keypair *")
    _btclib_libsecp256k1.lib.secp256k1_keypair_create(ctx, keypair, prvkey_bytes)

    sig = _btclib_libsecp256k1.ffi.new("char[64]")

    if _btclib_libsecp256k1.lib.secp256k1_schnorrsig_sign(
        ctx, sig, msg_bytes, keypair, secrets.token_bytes(32)
    ):
        return _btclib_libsecp256k1.ffi.unpack(sig, 64)
    return 0


def verify(msg_bytes, pubkey_bytes, signature_bytes):

    if len(pubkey_bytes) == 32:
        pubkey_bytes = b"\x02" + pubkey_bytes

    pubkey = _btclib_libsecp256k1.ffi.new("secp256k1_pubkey *")
    _btclib_libsecp256k1.lib.secp256k1_ec_pubkey_parse(
        ctx, pubkey, pubkey_bytes, len(pubkey_bytes)
    )

    xonly_pubkey = _btclib_libsecp256k1.ffi.new("secp256k1_xonly_pubkey *")
    _btclib_libsecp256k1.lib.secp256k1_xonly_pubkey_from_pubkey(
        ctx, xonly_pubkey, _btclib_libsecp256k1.ffi.new("int *"), pubkey
    )

    return _btclib_libsecp256k1.lib.secp256k1_schnorrsig_verify(
        ctx, signature_bytes, msg_bytes, len(msg_bytes), xonly_pubkey
    )
