import secrets

import _btclib_libsecp256k1

ctx = _btclib_libsecp256k1.lib.secp256k1_context_create(769)


def sign(msg_bytes, prvkey):

    if isinstance(prvkey, int):
        prvkey_bytes = prvkey.to_bytes(32, "big")
    else:
        prvkey_bytes = prvkey

    sig = _btclib_libsecp256k1.ffi.new("secp256k1_ecdsa_signature *")
    null = _btclib_libsecp256k1.ffi.NULL
    sig_bytes = _btclib_libsecp256k1.ffi.new("char[73]")
    length = _btclib_libsecp256k1.ffi.new("size_t *", 73)

    if not _btclib_libsecp256k1.lib.secp256k1_ecdsa_sign(
        ctx, sig, msg_bytes, prvkey_bytes, null, secrets.token_bytes(32)
    ):
        return 0
    if not _btclib_libsecp256k1.lib.secp256k1_ecdsa_signature_serialize_der(
        ctx, sig_bytes, length, sig
    ):
        return 0
    return _btclib_libsecp256k1.ffi.unpack(sig_bytes, length[0])


def verify(msg_bytes, pubkey_bytes, signature_bytes):
    signature = _btclib_libsecp256k1.ffi.new("secp256k1_ecdsa_signature *")
    _btclib_libsecp256k1.lib.secp256k1_ecdsa_signature_parse_der(
        ctx, signature, signature_bytes, len(signature_bytes)
    )

    pubkey = _btclib_libsecp256k1.ffi.new("secp256k1_pubkey *")
    _btclib_libsecp256k1.lib.secp256k1_ec_pubkey_parse(
        ctx, pubkey, pubkey_bytes, len(pubkey_bytes)
    )

    return _btclib_libsecp256k1.lib.secp256k1_ecdsa_verify(
        ctx, signature, msg_bytes, pubkey
    )
