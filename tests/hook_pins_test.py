# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""A hook's pins are what `uv.lock` resolves, wherever it resolves them.

The type gate runs in an environment of its own: `.pre-commit-config.yaml`
gives the mirror a `rev` and a list of `additional_dependencies`, and
pre-commit builds that environment once and keeps it. The editor cannot
use it -- this package is a compiled extension and the import does not
resolve where nothing built one -- so what the editor reads is the
project environment instead, and the two are the same mypy only while the
two declarations say the same thing.

Nothing made them say it. `.pre-commit-config.yaml` records that they are
"moved by hand, with the lint and test groups of uv.lock", which is a
procedure rather than a check, and section 4 of the organization standard
names that second declaration as the price of this branch. This module is
what turns the procedure into a red test: a `uv lock` that moves one of
these and a hand that does not follow is the whole of what it catches,
and it is silent -- both environments still build, and mypy still passes
in each, against different versions.

That procedure is about a hand-moved pin rather than about mypy, so every
`additional_dependencies` pin in the file is read here and asserted
against the lock wherever the lock resolves its package
(btclib-org/btclib-secp256k1#779). Where it does not, the pin is the only
declaration there is and nothing can disagree with it: `uv.lock` resolves
neither `shellcheck-py` nor `typos`, each being a tool installed for one
hook and declared by no dependency group, and a pin absent from the lock
is left alone rather than failed. The mypy block keeps the stronger
reading of the two, `test_every_mypy_pin_is_one_the_lock_resolves` below
requiring each of its pins to be in the lock at all: they are what the
checked files import, and the project installs those.

Parsed rather than loaded. `uv.lock` is toml and the floor here is 3.10,
where `tomllib` is not yet in the standard library, which is the reason
`copyright_test.py` beside this one reads pyproject.toml the same way;
`.pre-commit-config.yaml` is yaml and no group here carries a parser for
it. Three shapes are narrow enough to match: a `[[package]]` table with a
name and a version, and the two this file writes an
`additional_dependencies` value in -- a bracketed list on the key's own
line, and `- ` items indented under it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / ".pre-commit-config.yaml"
_LOCK = _ROOT / "uv.lock"

# the mypy hook's block, from its repo line to the next hook's: what
# `test_every_mypy_pin_is_one_the_lock_resolves` reads is that hook's and
# not another's, `shellcheck-py` being pinned one hook over
_MYPY_BLOCK = re.compile(
    r"^  - repo: https://github\.com/pre-commit/mirrors-mypy\n(.*?)(?=^  - repo: )",
    re.MULTILINE | re.DOTALL,
)
_REV = re.compile(r"^    rev: v?(?P<version>[0-9][0-9a-z.]*)\s*$", re.MULTILINE)
# an additional_dependencies key and whatever shares its line: nothing,
# where the requirements are the "- " items indented under it
_KEY = re.compile(r"^(?P<indent> *)additional_dependencies:(?P<inline>.*)$")
# a requirement naming one version, as against the floors and the marker
# gates [build-system]'s own requires are copied into this file as
_PIN = re.compile(r"^(?P<name>[A-Za-z0-9_.-]+)==(?P<version>[^\s;]+)$")


def _unquoted(item: str) -> str:
    """Return `item` without the pair of quotes yaml wrote it in.

    A pair, rather than any quote at either end: a requirement whose
    marker quotes a version -- `python_version<"3.13"` -- is written
    inside single quotes, and stripping quote characters wherever they
    fall takes the marker's closing one with them.

    Args:
        item: one requirement, as the file writes it.

    Returns:
        The requirement.
    """
    quoted = len(item) > 1 and item[0] == item[-1] and item[0] in "\"'"
    return item[1:-1] if quoted else item


def _flow(value: str) -> list[str]:
    """Return the requirements of a value written on the key's own line.

    Args:
        value: what follows the key, stripped.

    Returns:
        The requirements, unquoted; empty where the value is not a
        bracketed list, which is a shape this walk does not read.
    """
    if not (value.startswith("[") and value.endswith("]")):
        return []
    items = (_unquoted(item.strip()) for item in value[1:-1].split(","))
    return [item for item in items if item]


def _items(lines: list[str], indent: int) -> list[str]:
    """Return the "- " items indented deeper than `indent`.

    A comment between two items is read through, the mypy block writing
    one; anything else -- a blank line, a line at the key's own
    indentation or shallower, a line that is no item -- ends the value,
    since what follows it belongs to something other than this key.

    Args:
        lines: the lines after the key's own.
        indent: the key's indentation.

    Returns:
        The requirements, unquoted.
    """
    found: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or len(line) - len(line.lstrip(" ")) <= indent:
            break
        if stripped.startswith("#"):
            continue
        if not stripped.startswith("- "):
            break
        found.append(_unquoted(stripped[2:].strip()))
    return found


def _values(text: str) -> list[list[str]]:
    """Return the requirements of every `additional_dependencies` key.

    Args:
        text: the configuration, or a block of it.

    Returns:
        One list per key, in the order the keys are written.
    """
    lines = text.splitlines()
    return [
        _flow(key["inline"].strip())
        if key["inline"].strip()
        else _items(lines[index + 1 :], len(key["indent"]))
        for index, line in enumerate(lines)
        if (key := _KEY.match(line)) is not None
    ]


def _pins(values: list[list[str]]) -> tuple[tuple[str, str], ...]:
    """Return the `name==version` requirements among `values`.

    Args:
        values: the requirement lists to read.

    Returns:
        The pairs, sorted and without repetition -- two hooks pinning
        one package at one version ask the lock one question, and at two
        versions ask it two.
    """
    found = {
        (pin["name"], pin["version"])
        for value in values
        for requirement in value
        if (pin := _PIN.match(requirement)) is not None
    }
    return tuple(sorted(found))


def _locked(name: str) -> str | None:
    """Return the version `uv.lock` resolves for `name`, or None."""
    pattern = re.compile(
        rf'^name = "{re.escape(name)}"\nversion = "(?P<version>[^"]+)"$',
        re.MULTILINE,
    )
    match = pattern.search(_LOCK.read_text(encoding="utf-8"))
    return match["version"] if match else None


def _block() -> str:
    """Return the mypy hook's block of `.pre-commit-config.yaml`."""
    match = _MYPY_BLOCK.search(_CONFIG.read_text(encoding="utf-8"))
    assert match, "no mirrors-mypy hook in .pre-commit-config.yaml"
    return match[1]


_BLOCK = _block()
_MYPY_PINS = _pins(_values(_BLOCK))
_VALUES = _values(_CONFIG.read_text(encoding="utf-8"))
_PINS = tuple(pin for pin in _pins(_VALUES) if _locked(pin[0]) is not None)


def test_the_hook_block_was_read() -> None:
    """A block that parsed to nothing satisfies every check below.

    The patterns are anchored on an indentation `.pre-commit-config
    .yaml` happens to use, so a reformat that changed it would leave the
    pins unread and the assertions quantifying over nothing.
    """
    assert _MYPY_PINS, "the mirrors-mypy hook lists no pinned additional_dependencies"


def test_every_additional_dependencies_key_was_read() -> None:
    """A key whose value the walk cannot read is the same silence, hook-wide.

    `test_the_hook_block_was_read` above covers the mypy block alone,
    and a value written in a third shape would be read as a key
    declaring nothing: the pins under it would go unasserted with every
    parametrisation below still green.
    """
    assert _VALUES, "no additional_dependencies key in .pre-commit-config.yaml"
    assert all(_VALUES), "an additional_dependencies key read as declaring nothing"


def test_a_value_that_is_not_a_bracketed_list_reads_as_nothing() -> None:
    """A shape the walk does not read is nothing, never a partial answer.

    `test_every_additional_dependencies_key_was_read` above is what
    turns that nothing into a failure, and it can only do so because
    the walk declines rather than salvaging what it recognizes.
    """
    assert _flow("{pathspec: 1.1.1}") == []
    assert _flow('["pathspec==1.1.1", typos==1.49.0]') == [
        "pathspec==1.1.1",
        "typos==1.49.0",
    ]


def test_a_block_value_ends_at_the_first_line_that_is_not_an_item() -> None:
    """A comment between two items is read through; anything else is not.

    The mypy hook writes such a comment. What follows a hook's items is
    another key of that hook, or the next hook at a shallower
    indentation, and neither declares a requirement -- so a line that is
    no item ends the value where it stands rather than being skipped
    the way a comment is.
    """
    lines = [
        "          - cffi==2.1.1",
        "          # why the next one carries a version",
        "          - pathspec==1.1.1",
        "          this line is no item",
        "          - unreachable==9.9",
    ]

    assert _items(lines, 8) == ["cffi==2.1.1", "pathspec==1.1.1"]


def test_a_block_value_running_to_the_end_of_the_text_is_read_whole() -> None:
    """The last key of the text has no following line to stop at."""
    assert _items(["          - cffi==2.1.1"], 8) == ["cffi==2.1.1"]


def test_a_quoted_requirement_keeps_the_quotes_inside_its_marker() -> None:
    """Only the pair yaml wrote goes, so a marker's own quotes survive.

    `[build-system]`'s requires are copied into this file verbatim, and
    each marker-gated one is single-quoted around a double-quoted
    version; stripping quote characters wherever they fall would take
    the marker's closing one and answer a requirement the file does not
    hold.
    """
    assert _flow("""['cffi>=1.6; python_version<"3.13"']""") == [
        'cffi>=1.6; python_version<"3.13"'
    ]


def test_the_rev_is_the_locked_mypy() -> None:
    """The isolated environment's mypy and the project's are one version.

    They have to be: the editor reads the project's, the gate reads the
    hook's, and a developer told the two disagree learns it from a
    finding one reports and the other does not.
    """
    rev = _REV.search(_BLOCK)
    assert rev, "the mirrors-mypy hook declares no rev"
    assert rev["version"] == _locked("mypy"), (
        f"the hook pins mypy {rev['version']} where uv.lock resolves {_locked('mypy')}"
    )


@pytest.mark.parametrize("name, version", _MYPY_PINS, ids=lambda v: v)
def test_every_mypy_pin_is_one_the_lock_resolves(name: str, version: str) -> None:
    """The mypy hook installs what the checked files import, and so does uv."""
    assert _locked(name) is not None, (
        f"the mypy hook pins {name}=={version} and uv.lock resolves no"
        f" {name}: it is not one of the packages the lock keeps level"
    )


@pytest.mark.parametrize("name, version", _PINS, ids=lambda v: v)
def test_every_pin_is_the_locked_version(name: str, version: str) -> None:
    """Each pinned package the project also installs is the one version."""
    assert version == _locked(name), (
        f"a hook pins {name}=={version} where uv.lock resolves {_locked(name)}"
    )
