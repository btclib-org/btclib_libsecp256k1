import cffi
import pathlib
import re

ffi = cffi.FFI()


secp256k1 = pathlib.Path().resolve() / "secp256k1"
h_file_name = secp256k1 / "include" / "secp256k1.h"
shared_lib = secp256k1 / ".libs" / "libsecp256k1.so"


with open(h_file_name) as h_file:
    lns = h_file.read().splitlines()
    flt = filter(lambda ln: not re.match(r" *#", ln), lns)
    flt = map(lambda ln: ln.replace("EXPORT_SYMBOL ", ""), flt)
    ffi.cdef(str("\n").join(flt))
    # ffi.cdef(str("\n").join(lns))

ffi.set_source(
    "btclib_libsecp256k1",
    None,
    libraries=["secp256k1"],
    library_dirs=["secp256k1/.libs/"],
)

ffi.compile()
