# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Each extension's module flags name and turn on the right modules.

`scripts/cffi_build.py` passes `-DSECP256K1_ENABLE_MODULE_*` for the
modules it wants, and `configure`'s own parameter docstring calls that
list explicit "rather than left to upstream's own defaults, which are
not part of its API". A list of `ON` alone does not make it so: a module
upstream defaults `ON` is built whether or not this repository asked for
it, so the property holds only while the list mentions *every* module
the submodule defines, `OFF` included. That is the first half checked
here.

It went wrong once, which is why there is a check rather than a comment:
the secp256k1-zkp re-pin brought in a `silentpayments` this repository
does not declare to cffi, upstream defaults it `ON`, and the flagged
extension carried its object code with nothing red anywhere
(btclib-org/btclib-secp256k1#792). The first half above reads a flag's
*name*, so it stays green whichever value that name carries: flipping a
module's own `=ON`/`=OFF` back to what #792 was filed against left every
test in this file passing (btclib-org/btclib-secp256k1#807). The second
half below reads the value against what the same `configure()` call
wraps into the cdef -- `headers` and `module_flags` already say the same
thing twice, a header naming a module this repository reads entry
points from and a flag naming one CMake builds, so a module turned `ON`
with no header of its own is a decision nothing here has recorded, and a
header with its flag not `ON` builds the extension without the very
module it wraps. `_ON_WITHOUT_A_HEADER` below is where that decision is
recorded once there is one to make; both extensions read empty there
today, because every module either extension turns on has a header
wrapping it.

The flags are read out of the syntax tree rather than by importing
`scripts/cffi_build.py`: constructing either extension runs
`FFIExtension.__init__`, whose first act is `clean()`, and that removes
the built artifacts the rest of this suite is running against. The
CMake options are read as text, upstream's `CMakeLists.txt` being no
Python.

`_defined` reads each vendored submodule's `CMakeLists.txt` from the
repository root, so a checkout without the submodules fails these tests
rather than skipping them. That is why `test.yml`'s `suite-sdist` job
checks them out although its own install reads neither: an assertion
that stands down where its input is missing is the shape this file
exists against.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).parents[1]
_BUILD = _ROOT / "scripts" / "cffi_build.py"

# `option(SECP256K1_ENABLE_MODULE_ECDH "Enable ECDH module." ON)` -- the
# `option(` prefix is what tells a definition from the summary block at
# the end of the same file, which interpolates every one of these names
# again inside a `message()`
_OPTION = re.compile(r"option\(SECP256K1_ENABLE_MODULE_([A-Z0-9_]+)[\s)]")

# the module half of a flag and the value it carries: an OFF names the
# module as deliberately as an ON does, and it is the OFF that this file
# exists to keep in the list -- the value is what _on() below reads and
# _named() below discards, so that both live beside one another instead
# of two patterns silently drifting apart
_FLAG = re.compile(r"^-DSECP256K1_ENABLE_MODULE_([A-Z0-9_]+)=(ON|OFF)$")

# a header's own module name, cffi's cdef being derived from exactly
# this list -- `secp256k1.h` itself carries no trailing `_<module>` and
# so never matches, which is what keeps it out of every set below
_HEADER = re.compile(r"^secp256k1_([a-z0-9_]+)\.h$")

# a module turned ON with no header wrapping it: compiled into the
# library without cffi declaring any of its entry points. That is a
# legitimate shape -- a module needed only as another module's internal
# dependency, with no entry point of its own to wrap -- so it is
# recorded here rather than left to pass silently: an extension turning
# a module ON with nothing wrapping it meets an assertion naming that
# module, not a green suite, until an entry is added here and says why.
_ON_WITHOUT_A_HEADER: dict[str, frozenset[str]] = {
    "Secp256k1CFFIExtension": frozenset(),
    "Secp256k1ZkpCFFIExtension": frozenset(),
}


def _configured() -> dict[str, tuple[str, tuple[str, ...], tuple[str, ...]]]:
    """Read each extension class's submodule, headers and module flags.

    Every `self.configure(...)` call in the file is taken, so a third
    extension is read and parametrized without being named here.
    `test_both_extensions_were_read` below does name the two, that being
    what makes an empty result a failure rather than a pass, and is the
    one assertion a third extension moves.

    Returns:
        The class name of each extension that configures a submodule,
        against that submodule's directory name, the `headers` list and
        the `module_flags` list the same call passes, both as written.
    """
    tree = ast.parse(_BUILD.read_text(encoding="utf-8"))
    found: dict[str, tuple[str, tuple[str, ...], tuple[str, ...]]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for call in ast.walk(node):
            if not (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Attribute)
                and call.func.attr == "configure"
            ):
                continue
            keywords = {k.arg: k.value for k in call.keywords}
            found[node.name] = (
                ast.literal_eval(keywords["submodule"]),
                tuple(ast.literal_eval(keywords["headers"])),
                tuple(ast.literal_eval(keywords["module_flags"])),
            )
    return found


def _named(flags: tuple[str, ...]) -> frozenset[str]:
    """Read the module names a flags list mentions, whichever value carried."""
    return frozenset(m[1] for f in flags if (m := _FLAG.match(f)))


def _on(flags: tuple[str, ...]) -> frozenset[str]:
    """Read the module names a flags list turns ON."""
    return frozenset(m[1] for f in flags if (m := _FLAG.match(f)) and m[2] == "ON")


def _wrapped(headers: tuple[str, ...]) -> frozenset[str]:
    """Read the module names a headers list wraps into the cdef."""
    return frozenset(m[1].upper() for h in headers if (m := _HEADER.match(h)))


def _defined(submodule: str) -> frozenset[str]:
    """Read the module options a vendored submodule's CMake defines.

    Args:
        submodule: the submodule's directory name under the repository
            root.

    Returns:
        Every module `CMakeLists.txt` declares an option for.
    """
    text = (_ROOT / submodule / "CMakeLists.txt").read_text(encoding="utf-8")
    return frozenset(_OPTION.findall(text))


CONFIGURED = _configured()


def test_both_extensions_were_read() -> None:
    """Check the syntax-tree walk found the extensions and their flags.

    The positive control for `_FLAG` and for the walk together: with
    either broken every set below is empty, and an empty set equals an
    empty set, so the comparison this file exists for would pass on a
    reader that read nothing.
    """
    assert set(CONFIGURED) == {
        "Secp256k1CFFIExtension",
        "Secp256k1ZkpCFFIExtension",
    }
    for _submodule, _headers, flags in CONFIGURED.values():
        assert _named(flags)


def test_the_option_pattern_matches_a_module_both_submodules_define() -> None:
    """Check `_OPTION` against a module neither submodule can lack.

    The other half of the control above, and the half that cannot be got
    from the comparison itself: `schnorrsig` is wrapped out of both
    libraries, so a pattern answering nothing for it has stopped reading
    `CMakeLists.txt` rather than found a submodule that dropped it.
    """
    for submodule, _headers, _flags in CONFIGURED.values():
        assert "SCHNORRSIG" in _defined(submodule)


@pytest.mark.parametrize("extension", sorted(CONFIGURED))
def test_the_flags_name_every_module_the_submodule_defines(extension: str) -> None:
    """Check that no module is left to whatever upstream defaults it to.

    Args:
        extension: the class name of the extension being checked.
    """
    submodule, _headers, flags = CONFIGURED[extension]
    assert _named(flags) == _defined(submodule)


@pytest.mark.parametrize("extension", sorted(CONFIGURED))
def test_every_wrapped_module_is_turned_on(extension: str) -> None:
    """Check a header in the cdef is not built from upstream's own default.

    A header wrapped into the cdef whose own flag is not `ON` -- left
    `OFF`, or missing from the list the previous test already guards --
    builds the extension without the very module its own header
    advertises.

    Args:
        extension: the class name of the extension being checked.
    """
    _submodule, headers, flags = CONFIGURED[extension]
    assert _wrapped(headers) <= _on(flags)


@pytest.mark.parametrize("extension", sorted(CONFIGURED))
def test_every_module_turned_on_is_wrapped_or_recorded(extension: str) -> None:
    """Check a flag's value, not only its name, against what the cdef wraps.

    `test_the_flags_name_every_module_the_submodule_defines` above reads
    a flag's name and is blind to which value it carries, so it stays
    green where a module is turned back `ON` with nothing wrapping it --
    #792's own mistake. A module turned `ON` here either has a header of
    its own in the same `configure()` call or is named in
    `_ON_WITHOUT_A_HEADER` above, so a flag flipped without either fails
    on the commit that flips it.

    Args:
        extension: the class name of the extension being checked.
    """
    _submodule, headers, flags = CONFIGURED[extension]
    recorded = _ON_WITHOUT_A_HEADER.get(extension, frozenset())
    assert _on(flags) - _wrapped(headers) == recorded
