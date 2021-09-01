import btclib_libsecp256k1.dsa
import btclib_libsecp256k1.ssa
import coincurve
import btclib.ecc.dsa
import btclib.ecc.ssa
from btclib.hashes import reduce_to_hlen
from btclib.to_pub_key import pub_keyinfo_from_prv_key
import time

prvkey = 1

pubkey_bytes = pub_keyinfo_from_prv_key(prvkey)[0]
msg_bytes = reduce_to_hlen("Satoshi Nakamoto".encode())
dsa_signature_bytes = btclib.ecc.dsa.sign_(msg_bytes, prvkey).serialize()
ssa_signature_bytes = btclib.ecc.ssa.sign_(msg_bytes, prvkey).serialize()


def dsa_btclib():
    assert btclib.ecc.dsa.verify_(msg_bytes, pubkey_bytes, dsa_signature_bytes)


def ssa_btclib():
    assert btclib.ecc.ssa.verify_(msg_bytes, pubkey_bytes, ssa_signature_bytes)


def dsa_coincurve():
    assert coincurve.PublicKey(pubkey_bytes).verify(
        dsa_signature_bytes, msg_bytes, None
    )


def dsa_libsecp256k1():
    assert btclib_libsecp256k1.dsa.verify(msg_bytes, pubkey_bytes, dsa_signature_bytes)


def ssa_libsecp256k1():
    assert btclib_libsecp256k1.ssa.verify(msg_bytes, pubkey_bytes, ssa_signature_bytes)


def benchmark(func, mult=1):
    start = time.time()
    for x in range(100 * mult):
        func()
    end = time.time()
    print(f"{func.__name__}:", (end - start) / mult)


benchmark(dsa_btclib)
benchmark(dsa_coincurve, 100)
benchmark(dsa_libsecp256k1, 100)
benchmark(ssa_btclib)
benchmark(ssa_libsecp256k1, 100)
