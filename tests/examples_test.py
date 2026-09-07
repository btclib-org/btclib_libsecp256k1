# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Every example in the documentation is executed.

An example nobody runs is documentation that stops being true silently,
and the README's own example was one, with nothing to notice if the call
it shows had changed shape.

`doctest` is used through the standard library rather than through
pytest's `--doctest-modules`, and the reason is what this package is.
`testpaths` is `tests`, and widening it to the package would collect the
*source* tree -- which is the right thing locally, where the extension
is an editable build of it, and the wrong thing in the wheel jobs, where
what has to be exercised is the module inside the installed wheel.
Importing the package by name gets whichever of the two is installed, on
every kind of wheel, which is the point.

The examples are therefore constrained to be deterministic: fixed keys,
and a verification rather than a signature wherever the value depends on
randomness that is not pinned.
"""

from __future__ import annotations

import doctest
import importlib
import inspect
import pkgutil
import re
import sys
from pathlib import Path
from typing import NoReturn

import pytest

import btclib_secp256k1

_ROOT = Path(__file__).parents[1]

# the subpackage whose examples need the flagged extension to run
_ZKP = f"{btclib_secp256k1.__name__}.zkp"

# `doctest`'s own `_EXAMPLE_RE` reads this as a prompt only at the start
# of a line, preceded by spaces; `[ \t]*` here is deliberately looser --
# it can flag a tab-indented line `doctest` would not -- so this errs
# toward finding more prompts rather than fewer, and anchoring it at all
# keeps a mention of the prompt in running prose from being read as one
_DOCTEST_PROMPT = re.compile(r"^[ \t]*>>> ", re.MULTILINE)


def _unimportable(name: str) -> NoReturn:
    """Refuse to enumerate a package that will not import.

    `walk_packages` catches the `ImportError` a package raises as it
    descends into it and, with no `onerror`, yields nothing from under
    it: the enumeration shrinks back to what `iter_modules` returns and
    the tests that read it pass on the modules that are left.

    Args:
        name: the dotted name that would not import.

    Raises:
        ImportError: always, carrying the name.
    """
    msg = f"{name} would not import, so nothing under it was enumerated"
    raise ImportError(msg)


def _modules() -> list[str]:
    """Every module of the installed package, the package itself included.

    `walk_packages` descends into `zkp`, where `iter_modules` stops at
    the top package's own children and leaves a docstring under a
    subpackage collected by nothing.

    Returns:
        The dotted names, sorted, read off the imported package rather
        than off the source tree: what is documented has to be what a
        user imports.
    """
    prefix = f"{btclib_secp256k1.__name__}."
    found = pkgutil.walk_packages(
        btclib_secp256k1.__path__, prefix, onerror=_unimportable
    )
    return sorted([btclib_secp256k1.__name__, *(info.name for info in found)])


def _needs_the_zkp_extension(name: str) -> bool:
    """Whether this module's examples need the flagged extension to run.

    Args:
        name: the dotted name of the module.

    Returns:
        Whether it is the `zkp` subpackage or a module under it.
    """
    return name == _ZKP or name.startswith(f"{_ZKP}.")


def _carries_a_doctest_prompt(name: str) -> bool:
    """Whether the module's own source text carries a doctest prompt.

    Read from the file on disk rather than from a list kept in this
    file, so a module gains or loses this the moment its source does,
    with nothing here to fall out of step with it: the population this
    guards is derived from the tree, never typed out by hand.

    This is a text-level check, not `doctest`'s own parser: it can
    answer `True` for a module `DocTestFinder` finds nothing reachable
    in -- a comment carrying a line-anchored prompt, or a nested
    function's docstring, which `DocTestFinder` does not descend into.
    It cannot answer `True` for a module that carries no `>>> ` anywhere
    in its source.

    Args:
        name: the dotted name of the module.

    Returns:
        Whether its source carries the doctest prompt.
    """
    try:
        source = inspect.getsource(importlib.import_module(name))
    except OSError:  # pragma: no cover -- a module with no source file
        return False
    return bool(_DOCTEST_PROMPT.search(source))


def _module_name(source_file: Path, root: Path, package: str) -> str:
    """Compute the dotted name `_modules()` would report for a source file.

    Args:
        source_file: a `.py` file under `root`.
        root: `package`'s own directory, holding its `__init__.py`.
        package: the top package's dotted name.

    Returns:
        The dotted name, matching `_modules()`'s own naming: `root`
        itself names `package`, and an `__init__.py` names the
        directory that holds it rather than adding a segment for
        itself.
    """
    parts = source_file.relative_to(root).with_suffix("").parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join([package, *parts])


def _modules_expected_from_the_source_tree() -> set[str]:
    """Every module the source tree declares that carries a doctest prompt.

    Read from `src/<package>` under the repository root -- present in
    every job that runs this suite, wheel or editable, because it is
    the checkout the suite itself runs from -- rather than from
    `btclib_secp256k1.__path__`, which is what `_modules()` reads and
    exactly what an enumeration defect stops reaching. Deriving the
    population `_modules()` ought to cover from a second source is what
    makes a name silently missing from `_modules()`'s own answer
    assertable, instead of invisible to a check that reads `_modules()`
    twice.

    Returns:
        The dotted names of every module whose own source carries a
        doctest prompt.
    """
    package = btclib_secp256k1.__name__
    root = _ROOT / "src" / package
    named = {path: _module_name(path, root, package) for path in root.rglob("*.py")}
    return {
        name
        for path, name in named.items()
        if _DOCTEST_PROMPT.search(path.read_text(encoding="utf-8"))
    }


def test_no_module_carrying_examples_is_missing_from_the_enumeration() -> None:
    """Require every module the source tree carries examples in to be found.

    `test_the_examples_of_a_module_run` is parametrized once, at
    collection time, from `_modules()` itself: a name `_modules()` does
    not return gets no test case at all, so nothing above asserts
    anything about it -- the shape `walk_packages` replacing
    `iter_modules` closed for one regression and not for any other.
    This test derives the expected population independently, from the
    source tree rather than from `_modules()`, so a name it drops is
    what fails here instead of what neither test above can see.

    `Path.rglob` on a directory that does not exist yields nothing and
    raises nothing, so a missing or relocated `src/` would leave
    `expected` empty, the set difference below empty too, and this test
    passing having read nothing. Two tests further down this file guard
    their own populations against exactly that shape already; `expected`
    is required to be non-empty first, for the same reason.
    """
    expected = _modules_expected_from_the_source_tree()
    assert expected, (
        f"{_ROOT / 'src' / btclib_secp256k1.__name__} carries no module"
        " with a doctest prompt: the source tree was not read"
    )
    missing = expected - set(_modules())
    assert not missing, (
        f"{sorted(missing)} carry a doctest prompt in source but"
        " _modules() does not report them"
    )


@pytest.mark.parametrize(
    "name",
    [
        pytest.param(
            name, marks=[pytest.mark.zkp] if _needs_the_zkp_extension(name) else []
        )
        for name in _modules()
    ],
)
def test_the_examples_of_a_module_run(name: str) -> None:
    """Run the doctests of one module, and require that none failed.

    A module under `zkp` carries the `zkp` marker `-m zkp` selects and
    an `importorskip` that skips it where `BTCLIB_LIBSECP256K1_ZKP`
    built no extension for its examples to call into: the same pair the
    test modules under `tests/` use, and `pyproject.toml`'s comment on
    the marker says why one does not stand for the other.

    Where the module's own source carries a doctest prompt, `attempted`
    is required to be positive too: a module can stay in `_modules()`
    while `DocTestFinder` stops reaching its docstrings, and a total of
    zero examples passes `results.failed == 0` exactly as a module that
    never carried one does.

    Args:
        name: the dotted name of the module.
    """
    if _needs_the_zkp_extension(name):
        pytest.importorskip("_btclib_secp256k1_zkp")
    results = doctest.testmod(importlib.import_module(name))
    assert results.failed == 0, (
        f"{results.failed} of {results.attempted} examples failed in {name};"
        " the captured output above is what doctest reported"
    )
    if _carries_a_doctest_prompt(name):
        assert results.attempted > 0, (
            f"{name}'s source carries a doctest prompt, but doctest"
            " attempted none of it"
        )


def test_the_package_carries_examples_at_all() -> None:
    """Guard the test above against passing on a package with no examples.

    The examples are parsed and not run: the test above skips a module
    under `zkp` on an unflagged build, and running its examples here
    would be running what that skip refused. `DocTestFinder` is what
    `doctest.testmod` finds them with, so what it counts is what a
    flagged run attempts.
    """
    finder = doctest.DocTestFinder()
    examples = sum(
        len(parsed.examples)
        for name in _modules()
        for parsed in finder.find(importlib.import_module(name))
    )
    assert examples > 0, "no module of the package carries a doctest any more"


class _RefusesEveryImport:
    """A meta-path finder that refuses whatever it is asked for.

    It stands in front of `sys.meta_path` for one call of `_modules()`,
    which imports exactly one thing: the subpackage `walk_packages`
    descends into.
    """

    def find_spec(self, fullname: str, *_args: object) -> NoReturn:
        """Refuse `fullname`.

        Args:
            fullname: the dotted name the import system is resolving.
            _args: the `path` and `target` the import system passes
                positionally, which a refusal does not read.

        Raises:
            ImportError: always, the way a missing extension would.
        """
        msg = f"{fullname} refused"
        raise ImportError(msg)


def test_a_subpackage_that_will_not_import_stops_the_enumeration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Require that `_modules()` raises rather than returning fewer names.

    A `walk_packages` with no `onerror` answers here with what
    `iter_modules` answers -- the subpackage, and nothing under it --
    and the tests above then pass over an enumeration that lost the
    modules this file exists to reach. The finder is what puts the
    subpackage in that state: `sys.modules` is where an import already
    made would otherwise be found.

    Args:
        monkeypatch: undoes both changes to the interpreter's own state.
    """
    monkeypatch.delitem(sys.modules, _ZKP, raising=False)
    monkeypatch.setattr(sys, "meta_path", [_RefusesEveryImport(), *sys.meta_path])
    with pytest.raises(ImportError, match=_ZKP):
        _modules()


def test_the_readme_examples_run() -> None:
    """Run the quickstart, which is the README's own examples.

    The README is the documentation of this package, and the quickstart
    is the page a reader arriving from `pip install` lands on: it is
    executed here for the same reason the docstrings are.
    """
    results = doctest.testfile(
        str(_ROOT / "README.md"), module_relative=False, verbose=False
    )
    assert results.attempted > 0, "the README carries no doctest any more"
    assert results.failed == 0, (
        f"{results.failed} of {results.attempted} README examples failed;"
        " the captured output above is what doctest reported"
    )
