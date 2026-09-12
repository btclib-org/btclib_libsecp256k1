# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""The interpreters this package claims are the ones it runs on.

One fact, declared three times: `requires-python` is the floor,
`Programming Language :: Python :: X.Y` is what PyPI shows whoever is
choosing the package, and the platform sentinels' own lists are what
actually runs. Nothing compared them, and the three drift in the
direction that is hardest to notice -- a classifier left behind when a
floor moves is a package advertising an interpreter its suite never
touches, and the person it misleads is not reading this repository.

The sentinels are where the interpreter set lives because that is where
the suite meets every interpreter: the merge gate runs one cell, on the
version `.python-version` pins, and `os-ubuntu.yml`'s header says why. Each
of the three carries the list in full, and each of their comments says
the other two carry the same one, so the list is read per file and the
three are required to agree: a version added to one and forgotten in
another is a difference between platforms, which is the one thing a
platform sweep is arranged so as not to have.

The organization standard's rule is that a library covers every Python
that is not out of support, so all three move together twice around each
October: one version leaves support as another is released. This module
does not know that calendar and does not try to -- python.org keeps it,
and a test that hard-coded a date would be one more thing to move. What
it holds is the weaker and checkable claim: whatever the three say, they
say the same thing.

Read with a regex rather than parsed. `tomllib` arrives in 3.11 and the
floor here is 3.10, which is the reason `copyright_test.py` reads
pyproject.toml the same way; a workflow is yaml and no group here
carries a parser for it.
"""

import re
from pathlib import Path

_ROOT = Path(__file__).parents[1]
_PYPROJECT = (_ROOT / "pyproject.toml").read_text(encoding="utf-8")
_SENTINELS = ("os-ubuntu.yml", "os-macos.yml", "os-windows.yml")
_WORKFLOWS = {
    name: (_ROOT / ".github/workflows" / name).read_text(encoding="utf-8")
    for name in _SENTINELS
}

# "3.10" out of `requires-python = ">=3.10"`, the floor and nothing else:
# an upper bound is not declared here and would be a different claim
_FLOOR = re.compile(r'^requires-python = ">=(?P<version>3\.\d+)"', re.MULTILINE)
# the per-version classifiers, not `:: 3` or `:: 3 :: Only`, which say
# something about the major version rather than about an interpreter
_CLASSIFIER = re.compile(
    r'^    "Programming Language :: Python :: (?P<version>3\.\d+)",$', re.MULTILINE
)
_PYPY_CLASSIFIER = "Programming Language :: Python :: Implementation :: PyPy"
# PyPI's free-threading classifiers, the bare one and its maturity levels
# alike: each is a claim about the code under a free-threaded build, and
# which is claimed is not this module's question
_FREE_THREADING_CLASSIFIER = re.compile(
    r'^    "Programming Language :: Python :: Free Threading(?: :: .+)?",$',
    re.MULTILINE,
)
# the `python-version` list of a sentinel's suite matrix. The key has to
# be alone on its line, which is what leaves out the `exclude:` entries
# below it: those spell the same key with a value beside it, and an
# excluded cell is an interpreter that cannot run on one image rather
# than one this package does not claim
_PYTHONS = re.compile(
    r'^        python-version:\n(?P<block>(?:^          - "\S+"\n)+)', re.MULTILINE
)
# the merge gate, and inside it the jobs a landing waits on: the
# aggregate's own `needs:` closure, which is what section 3 of the
# organization standard asks for. It declares a free-threading classifier
# where the gate exercises that build, a gate being what refuses the
# landing that breaks it, so an interpreter named only by a job nothing
# waits on is the "it passed somewhere" that section refuses. Reading the
# file whole is the alternative it names as rejected, and it answers the
# same here, every job of this workflow sitting in that closure; what it
# costs is the day one is moved out, which the file read cannot see
_GATE = _ROOT / ".github/workflows/test.yml"
# the aggregate, by the name a required context is keyed on, which is a
# job's `name:` and not its key
_AGGREGATE = "test: every job passed"
# comments go first, so that a sentence about a sentinel's free-threaded
# cell does not read as the gate running one
_COMMENT = re.compile(r"(?:^|\s)#.*$", re.MULTILINE)
# a job names in its own text the interpreter it runs, as
# `python-version: "3.14"` or `--python 3.14`, so a job's interpreters
# are read as tokens off that text rather than out of a matrix block:
# the gate's own header says it is one suite cell rather than a matrix. A
# free-threaded build named that way is a "3.14t" of the same shape. What
# a job leaves to cibuildwheel is outside this read: those identifiers
# come from `requires-python`, `enable` and `skip`, spelled `cp314t`
# rather than as a version in any file here (#867)
_INTERPRETER = re.compile(r"\b3\.\d+t?\b")
# `jobs:` and everything under it. The keys of `on:` sit at the indent a
# job key does, so a pattern that did not cut here would offer
# `pull_request` to the closure below as a job of the workflow
_JOBS = re.compile(r"^jobs:\n(?P<block>.*)\Z", re.MULTILINE | re.DOTALL)
# a job key at the one indent `jobs:` gives them, and everything it
# indents under. The block runs a space below a job attribute's own
# indent and takes a whitespace-only line, which is the slack that
# absorbs what dropping a comment leaves: `_COMMENT` takes the
# whitespace before the `#` with it, so a comment on a line of its own
# arrives here one space short of where it was written
_JOB = re.compile(
    r"^  (?P<key>[a-z0-9_-]+):\n(?P<block>(?:^ {3,}.*\n|^ *\n)*)", re.MULTILINE
)
# a job's own `name:`, at the indent its attributes take: a step's name
# is deeper and is not matched here. A block scalar reads as `>-`, which
# is no aggregate's name and needs no excluding
_NAME = re.compile(r'^    name: "?(?P<name>[^"\n]*?)"?$', re.MULTILINE)
# `needs:` in each of the three shapes this workflow writes it -- one job
# after the key, a flow list there, and a block list under it -- read as
# whatever follows the key on its own line plus the items below it
_NEEDS = re.compile(
    r"^    needs:(?P<inline>[^\n]*)\n(?P<items>(?:^      - \S+\n)*)", re.MULTILINE
)
_ITEM = re.compile(r"^      - (?P<key>\S+)$", re.MULTILINE)


def _versions(pattern: re.Pattern[str], text: str) -> tuple[str, ...]:
    """Return every `version` group `pattern` finds, in order."""
    return tuple(m["version"] for m in pattern.finditer(text))


def _jobs() -> dict[str, str]:
    """Return each job of the merge gate against its text, comments dropped."""
    jobs = _JOBS.search(_COMMENT.sub("", _GATE.read_text(encoding="utf-8")))
    assert jobs, f"{_GATE.name} declares no jobs"
    return {match["key"]: match["block"] for match in _JOB.finditer(jobs["block"])}


def _waits_on(block: str) -> list[str]:
    """Return the jobs one job's `needs:` names, in whichever shape."""
    needs = _NEEDS.search(block)
    if not needs:
        return []
    listed = needs["inline"].strip("[] ").replace(",", " ").split()
    return listed + _ITEM.findall(needs["items"])


def _closure(jobs: dict[str, str], key: str) -> set[str]:
    """Return `key` and every job it waits on, however deep."""
    found = {key}
    pending = [key]
    while pending:
        for name in _waits_on(jobs[pending.pop()]):
            if name not in found:
                found.add(name)
                pending.append(name)
    return found


def _gate_interpreters() -> tuple[str, ...]:
    """Return every interpreter the jobs the merge gate waits on name."""
    jobs = _jobs()
    keyed = {
        match["name"]: key
        for key, block in jobs.items()
        for match in _NAME.finditer(block)
    }
    assert _AGGREGATE in keyed, (
        f"{_GATE.name} carries no job named {_AGGREGATE!r}, which is the"
        " required check the closure is read from"
    )
    closure = _closure(jobs, keyed[_AGGREGATE])
    return tuple(
        sorted({v for key in closure for v in _INTERPRETER.findall(jobs[key])})
    )


def _matrix(text: str) -> tuple[str, ...]:
    """Return the interpreters one sentinel's suite matrix names, in order."""
    return tuple(
        line.strip().lstrip("- ").strip('"')
        for match in _PYTHONS.finditer(text)
        for line in match["block"].splitlines()
    )


_CLASSIFIED = _versions(_CLASSIFIER, _PYPROJECT)
_DECLARED = {name: _matrix(text) for name, text in _WORKFLOWS.items()}
# the list the classifier checks below quantify over: one file's, which
# the equality test makes all three. Any other way of combining them
# reports a version some sentinel carries, and the question those checks
# ask is about a version every sentinel runs
_MATRIX = _DECLARED[_SENTINELS[0]]
# the free-threaded build and PyPy are the same interpreter version as
# far as a classifier is concerned: "3.14t" is CPython 3.14, and
# "pypy-3.11" is what the PyPy classifier covers rather than a version
# of its own
_CPYTHON = tuple(sorted({v.rstrip("t") for v in _MATRIX if not v.startswith("pypy")}))


def test_the_three_declarations_were_read() -> None:
    """Each pattern found something, so the checks below quantify over it.

    A key renamed, a classifier reindented, a sentinel's matrix
    reindented: each would leave one of these empty and every comparison
    below trivially true.
    """
    assert _FLOOR.search(_PYPROJECT), "pyproject.toml declares no requires-python"
    assert _CLASSIFIED, "pyproject.toml declares no per-version Python classifier"
    unread = [name for name, declared in _DECLARED.items() if not declared]
    assert not unread, (
        f"declares no python-version list: {', '.join(unread)}."
        " A key renamed or a matrix reindented reads as an empty list"
    )


def test_the_three_sentinels_carry_the_same_interpreters() -> None:
    """The platform is the only thing that differs between the three.

    Each sentinel's matrix comment says the other two carry the same
    list; this is that sentence checked. Order included: the three are
    read side by side when one of them goes red, and a list in a
    different order is one a reader has to diff rather than compare.
    """
    reference, *others = _SENTINELS
    for name in others:
        assert _DECLARED[name] == _DECLARED[reference], (
            f"{name} runs {', '.join(_DECLARED[name])} where {reference} runs"
            f" {', '.join(_DECLARED[reference])}: an interpreter covered on"
            " one platform and not another is a gap no red cell reports"
        )


def test_the_floor_is_the_lowest_classifier() -> None:
    """`requires-python` and the classifiers name the same oldest Python."""
    floor = _FLOOR.search(_PYPROJECT)
    assert floor, "pyproject.toml declares no requires-python"
    lowest = min(_CLASSIFIED, key=lambda v: tuple(int(p) for p in v.split(".")))
    assert floor["version"] == lowest, (
        f"requires-python is >={floor['version']} and the lowest classifier"
        f" is {lowest}: one of the two was moved and the other was not"
    )


def test_every_classified_interpreter_is_in_the_matrix() -> None:
    """A version PyPI advertises is a version the suite runs."""
    unrun = [v for v in _CLASSIFIED if v not in _CPYTHON]
    assert not unrun, (
        f"classified and run by no platform sentinel: {', '.join(unrun)}."
        " PyPI shows a classifier to whoever is choosing this package"
    )


def test_every_matrix_interpreter_is_classified() -> None:
    """A version the suite runs is a version PyPI advertises."""
    unclassified = [v for v in _CPYTHON if v not in _CLASSIFIED]
    assert not unclassified, (
        f"run by a platform sentinel and not classified: {', '.join(unclassified)}"
    )


def test_pypy_is_classified_exactly_when_it_is_run() -> None:
    """The PyPy classifier is a claim about the matrix, not a decoration."""
    classified = _PYPY_CLASSIFIER in _PYPROJECT
    run = any(v.startswith("pypy") for v in _MATRIX)
    assert classified == run, (
        f"the PyPy classifier is {'present' if classified else 'absent'} and"
        f" the matrix {'runs' if run else 'does not run'} a PyPy interpreter"
    )


def test_free_threading_is_classified_exactly_when_the_gate_runs_it() -> None:
    """The free-threading classifier is a claim about the merge gate.

    The organization standard declares one where the gate exercises the
    free-threaded build: a gate refuses the landing that breaks that
    build, where a sentinel runs beside a landing and blocks nothing. So
    the second side here is the jobs the required check waits on and not
    `_MATRIX` -- the sentinels name "3.14t" as readily as the gate would,
    and a sentinel passing is the ground the standard declines.

    The aggregate's own job names no interpreter, so the assertion below
    is the `needs:` read's control as much as the pattern's: a read that
    matched nothing leaves the closure at that one job and this empty.
    """
    gate = _gate_interpreters()
    assert gate, "the jobs test.yml's gate waits on name no interpreter"
    classified = bool(_FREE_THREADING_CLASSIFIER.search(_PYPROJECT))
    run = [v for v in gate if v.endswith("t")]
    assert classified == bool(run), (
        f"the free-threading classifier is {'present' if classified else 'absent'}"
        f" and the jobs test.yml's gate waits on name"
        f" {', '.join(run) or 'no free-threaded interpreter'}"
    )
