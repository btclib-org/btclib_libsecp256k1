import _btclib_libsecp256k1

ctx = _btclib_libsecp256k1.lib.secp256k1_context_create(257)


def verify(msg_bytes, pubkey_bytes, signature_bytes):
    signature = _btclib_libsecp256k1.ffi.new("secp256k1_ecdsa_signature *")
    _btclib_libsecp256k1.lib.secp256k1_ecdsa_signature_parse_der(
        ctx, signature, signature_bytes, 71
    )

    pubkey = _btclib_libsecp256k1.ffi.new("secp256k1_pubkey *")
    _btclib_libsecp256k1.lib.secp256k1_ec_pubkey_parse(
        ctx, pubkey, pubkey_bytes, len(pubkey_bytes)
    )

    return _btclib_libsecp256k1.lib.secp256k1_ecdsa_verify(
        ctx, signature, msg_bytes, pubkey
    )
