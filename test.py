import btclib_libsecp256k1.dsa
import btclib_libsecp256k1.ssa
from btclib_libsecp256k1 import ffi, lib


def test_sign_and_verify():
    prvkey = 1
    pubkey_bytes = b"\x02y\xbef~\xf9\xdc\xbb\xacU\xa0b\x95\xce\x87\x0b\x07\x02\x9b\xfc\xdb-\xce(\xd9Y\xf2\x81[\x16\xf8\x17\x98"
    msg_bytes = b"\xa0\xdce\xff\xcay\x98s\xcb\xea\n\xc2t\x01[\x95&P]\xaa\xae\xd3\x85\x15T%\xf73w\x04\x88>"

    dsa_signature_bytes = btclib_libsecp256k1.dsa.sign(msg_bytes, prvkey)
    assert btclib_libsecp256k1.dsa.verify(msg_bytes, pubkey_bytes, dsa_signature_bytes)

    ssa_signature_bytes = btclib_libsecp256k1.ssa.sign(msg_bytes, prvkey)
    assert btclib_libsecp256k1.ssa.verify(msg_bytes, pubkey_bytes, ssa_signature_bytes)


def test_safe_abort():
    lib.secp256k1_ecdsa_sign(
        lib.secp256k1_context_create(769),
        ffi.new("secp256k1_ecdsa_signature *"),
        b"0" * 32,
        ffi.NULL,
        ffi.NULL,
        b"0" * 32,
    )
