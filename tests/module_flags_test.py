# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Each extension's module flags name every module its submodule defines.

`scripts/cffi_build.py` passes `-DSECP256K1_ENABLE_MODULE_*` for the
modules it wants, and `configure`'s own parameter docstring calls that
list explicit "rather than left to upstream's own defaults, which are
not part of its API". A list of `ON` alone does not make it so: a module
upstream defaults `ON` is built whether or not this repository asked for
it, so the property holds only while the list mentions *every* module
the submodule defines, `OFF` included. That is what is checked here.

It went wrong once, which is why there is a check rather than a comment:
the secp256k1-zkp re-pin brought in a `silentpayments` this repository
does not declare to cffi, upstream defaults it `ON`, and the flagged
extension carried its object code with nothing red anywhere
(btclib-org/btclib-secp256k1#792). What fails now is the next one --
the sync that adds a module -- at the commit that moves the pin, which
is when somebody is in a position to decide `ON` or `OFF`.

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

# the module half of a flag, whichever value it carries: an OFF names the
# module as deliberately as an ON does, and it is the OFF that this file
# exists to keep in the list
_FLAG = re.compile(r"^-DSECP256K1_ENABLE_MODULE_([A-Z0-9_]+)=(?:ON|OFF)$")


def _configured() -> dict[str, tuple[str, frozenset[str]]]:
    """Read each extension class's submodule and the modules its flags name.

    Every `self.configure(...)` call in the file is taken, so a third
    extension is read and parametrized without being named here.
    `test_both_extensions_were_read` below does name the two, that being
    what makes an empty result a failure rather than a pass, and is the
    one assertion a third extension moves.

    Returns:
        The class name of each extension that configures a submodule,
        against that submodule's directory name and the set of modules
        its `module_flags` mention.
    """
    tree = ast.parse(_BUILD.read_text(encoding="utf-8"))
    found: dict[str, tuple[str, frozenset[str]]] = {}
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
            flags = ast.literal_eval(keywords["module_flags"])
            named = {m[1] for f in flags if (m := _FLAG.match(f))}
            found[node.name] = (
                ast.literal_eval(keywords["submodule"]),
                frozenset(named),
            )
    return found


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
    for _submodule, named in CONFIGURED.values():
        assert named


def test_the_option_pattern_matches_a_module_both_submodules_define() -> None:
    """Check `_OPTION` against a module neither submodule can lack.

    The other half of the control above, and the half that cannot be got
    from the comparison itself: `schnorrsig` is wrapped out of both
    libraries, so a pattern answering nothing for it has stopped reading
    `CMakeLists.txt` rather than found a submodule that dropped it.
    """
    for submodule, _named in CONFIGURED.values():
        assert "SCHNORRSIG" in _defined(submodule)


@pytest.mark.parametrize("extension", sorted(CONFIGURED))
def test_the_flags_name_every_module_the_submodule_defines(extension: str) -> None:
    """Check that no module is left to whatever upstream defaults it to.

    Args:
        extension: the class name of the extension being checked.
    """
    submodule, named = CONFIGURED[extension]
    assert named == _defined(submodule)
