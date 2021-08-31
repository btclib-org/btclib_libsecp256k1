import btclib_libsecp256k1
import coincurve
from btclib.ecc import dsa, ssa
from btclib.hashes import reduce_to_hlen
from btclib.to_pub_key import pub_keyinfo_from_prv_key
import time

prvkey = 1

pubkey_bytes = pub_keyinfo_from_prv_key(prvkey)[0]
msg_bytes = reduce_to_hlen("Satoshi Nakamoto".encode())
dsa_signature_bytes = dsa.sign_(msg_bytes, prvkey).serialize()
ssa_signature_bytes = ssa.sign_(msg_bytes, prvkey).serialize()


def dsa_btclib():
    assert dsa.verify_(msg_bytes, pubkey_bytes, dsa_signature_bytes)


def ssa_btclib():
    assert ssa.verify_(msg_bytes, pubkey_bytes, ssa_signature_bytes)


def dsa_coincurve():
    assert coincurve.PublicKey(pubkey_bytes).verify(
        dsa_signature_bytes, msg_bytes, None
    )


ctx = btclib_libsecp256k1.lib.secp256k1_context_create(257)


def dsa_libsecp256k1():
    signature = btclib_libsecp256k1.ffi.new("secp256k1_ecdsa_signature *")
    btclib_libsecp256k1.lib.secp256k1_ecdsa_signature_parse_der(
        ctx, signature, dsa_signature_bytes, 71
    )

    pubkey = btclib_libsecp256k1.ffi.new("secp256k1_pubkey *")
    btclib_libsecp256k1.lib.secp256k1_ec_pubkey_parse(
        ctx, pubkey, pubkey_bytes, len(pubkey_bytes)
    )

    assert btclib_libsecp256k1.lib.secp256k1_ecdsa_verify(
        ctx, signature, msg_bytes, pubkey
    )


def ssa_libsecp256k1():
    pubkey = btclib_libsecp256k1.ffi.new("secp256k1_pubkey *")
    btclib_libsecp256k1.lib.secp256k1_ec_pubkey_parse(
        ctx, pubkey, pubkey_bytes, len(pubkey_bytes)
    )

    xonly_pubkey = btclib_libsecp256k1.ffi.new("secp256k1_xonly_pubkey *")
    btclib_libsecp256k1.lib.secp256k1_xonly_pubkey_from_pubkey(
        ctx, xonly_pubkey, btclib_libsecp256k1.ffi.new("int *"), pubkey
    )

    assert btclib_libsecp256k1.lib.secp256k1_schnorrsig_verify(
        ctx, ssa_signature_bytes, msg_bytes, len(msg_bytes), xonly_pubkey
    )


def benchmark(func, mult=1):
    start = time.time()
    for x in range(22 * 1000 * mult):
        func()
    end = time.time()
    print(f"{func.__name__}:", (end - start) / mult)


benchmark(dsa_btclib)
benchmark(dsa_coincurve, 100)
benchmark(dsa_libsecp256k1, 100)
benchmark(ssa_btclib)
benchmark(ssa_libsecp256k1, 100)
