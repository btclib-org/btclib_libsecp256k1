import _btclib_libsecp256k1

ctx = _btclib_libsecp256k1.lib.secp256k1_context_create(257)


def verify(msg_bytes, pubkey_bytes, signature_bytes):
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
