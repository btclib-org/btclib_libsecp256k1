import secrets

from . import ffi, lib

ctx = lib.secp256k1_context_create(769)


def sign(msg_bytes, prvkey):

    if isinstance(prvkey, int):
        prvkey_bytes = prvkey.to_bytes(32, "big")
    else:
        prvkey_bytes = prvkey

    sig = ffi.new("secp256k1_ecdsa_signature *")
    null = ffi.NULL
    sig_bytes = ffi.new("char[73]")
    length = ffi.new("size_t *", 73)

    if not lib.secp256k1_ecdsa_sign(
        ctx, sig, msg_bytes, prvkey_bytes, null, secrets.token_bytes(32)
    ):
        return 0
    if not lib.secp256k1_ecdsa_signature_serialize_der(ctx, sig_bytes, length, sig):
        return 0
    return ffi.unpack(sig_bytes, length[0])


def verify(msg_bytes, pubkey_bytes, signature_bytes):
    signature = ffi.new("secp256k1_ecdsa_signature *")
    lib.secp256k1_ecdsa_signature_parse_der(
        ctx, signature, signature_bytes, len(signature_bytes)
    )

    pubkey = ffi.new("secp256k1_pubkey *")
    lib.secp256k1_ec_pubkey_parse(ctx, pubkey, pubkey_bytes, len(pubkey_bytes))

    return lib.secp256k1_ecdsa_verify(ctx, signature, msg_bytes, pubkey)
