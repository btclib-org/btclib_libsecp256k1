# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""No sdist `exclude` entry matches a file a submodule tracks.

check-sdist (henryiii/check-sdist) compares the sdist hatchling builds
against `git ls-files --cached --recurse-submodules`, and its hatchling
plugin then subtracts from that comparison whatever
`[tool.hatch.build.targets.sdist]`'s own `exclude` list matches
(`check_sdist/backends/hatchling.py`'s `git_only_excludes`, called
unconditionally inside `compare()` at v1.6.0, regardless of
`[tool.check-sdist]`'s `mode`). That subtraction is deliberate for some
of the list's entries -- `/COPYRIGHT` is a tracked file this repository
excludes from the sdist on purpose, for the reason its own comment
gives, and check-sdist staying quiet about it is correct -- and it is
also what makes the loss #655 describes invisible: most of the list's
entries name a local `./autogen.sh && ./configure` run's own droppings,
files that exist on no clone until those commands are run, so a stale
entry matches nothing there and check-sdist stays quiet correctly too.
An entry that instead matches a file a *submodule* tracks -- a directory
written where a file was meant, a name that also matches something
committed -- drops that file from the sdist the same silent way, and
nothing here is meant to (btclib-org/btclib-secp256k1#655).

This hook is what catches that case without also catching `/COPYRIGHT`'s
deliberate one: it matches the exclude list, with the same
`pathspec.GitIgnoreSpec` matching that plugin uses, against only the
tracked files living inside a submodule -- `.gitmodules`' own paths,
read the way `check_submodules_checked_out.py` already reads them,
rather than every file `git ls-files --cached --recurse-submodules`
answers -- and fails on a nonempty intersection there. Scoped that way
because the loss this hook exists for is specific to the submodule
entries: `/COPYRIGHT`, `/build`, `/dist`, `/wheelhouse` and the rest of
the list above `secp256k1/src/btclib_default_callbacks.c` are this
repository's own stable, deliberately-curated exclusions and are not
rewritten at every pin bump the way the submodule blocks below them
are -- which is also where the risk #655 names actually lives. An
unscoped match catches `/COPYRIGHT` as well, correctly, this list being
written to match it: that is why the scope is the submodule paths, and
what the scope leaves uncaught -- a wrong entry naming one of this
repository's own tracked files -- is btclib-org/btclib-secp256k1#770.

It fires only where an entry matches a file that is *currently tracked*
inside a submodule, so an entry naming a local build's own debris, which
is untracked, leaves it quiet: the failure this hook exists to catch is
a pin bump that widens or misnames an entry into a submodule's tracked
territory, not the ordinary case the list was written for. That
asymmetry is also why `[tool.check-sdist]`'s `mode = "all"` -- one of
the two other answers #655 named and did not choose between -- is not
this one: `mode` decides what `compare()` treats as "git" (`git ls-files`
under `"git"`, every file on disk under `"all"`), but `git_only_excludes`
runs after that choice and unconditionally either way, so it subtracts
the same tracked file under both -- measured against
`check_sdist/__main__.py`'s own `compare()`, `mode` never reaches that
call at all. The third, an upstream request that the plugin report what
it subtracts, remains open against henryiii/check-sdist and would retire
this hook if it landed; nothing here depends on it landing.

Regex rather than `tomllib` for the exclude list: the floor here is
3.10, and `tomllib` is 3.11 -- `tests/copyright_test.py`'s own module
docstring gives the same reason for the same choice.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pathspec

# resolved once, the same way check_submodule_pin.py's own _GIT is: a
# bare "git" in a subprocess list is what S607 is about
_GIT = shutil.which("git") or "git"

_ROOT = Path(__file__).resolve().parents[2]

# the sdist target's own table, up to the next top-level table header (or
# the end of the file): scoped so that [tool.ruff]'s and [tool.mypy]'s
# own "exclude = [" arrays elsewhere in pyproject.toml are never in reach
_TARGET_SECTION = "[tool.hatch.build.targets.sdist]"
_EXCLUDE_OPEN_RE = re.compile(r"^exclude\s*=\s*\[(?P<rest>.*)$")
# one TOML basic string, alone on its line, with the trailing comma this
# array writes on every entry: no backslash, so an escape this walk
# would hand on unprocessed is refused rather than read wrongly
_ENTRY_RE = re.compile(r'^"(?P<pattern>[^"\\]*)",$')

# .gitmodules is git's own config format: one "path = ..." line per
# submodule, indented under its "[submodule ...]" header -- the same
# pattern check_submodules_checked_out.py already reads it with
_SUBMODULE_PATH_RE = re.compile(r"^\s*path\s*=\s*(\S+)\s*$", re.MULTILINE)


def sdist_exclude_patterns(pyproject_toml: str) -> list[str] | None:
    """Return `[tool.hatch.build.targets.sdist]`'s `exclude` list.

    A line-based walk rather than one regex spanning the whole array: a
    comment inside the array is free to hold a `]` of its own (this
    file's own comments cite `[tool.check-sdist]`, brackets included),
    which a single "up to the next `]`" pattern would stop at instead of
    the array's real close. Reading line by line and trusting only a
    line that is *exactly* `]` -- this table's own closing convention --
    to end the array is what keeps such a comment from being mistaken
    for the end.

    The rest of that convention is read just as literally: the array
    opens on a line ending in `[`, and every entry is one double-quoted
    string with a trailing comma, alone on its line, with blank lines
    and whole-line comments free to sit between entries. Anything else
    is refused rather than answered, a walk this simple seeing not
    *less* of another shape but something else. Read rather than
    refused, an inline `exclude = ["a", "b"]` would never leave the
    array, harvesting every double-quoted string down to the next lone
    `]` out of tables it never entered; a `]` carrying a trailing
    comment leaves it inside the array the same way; a single-quoted
    entry offers no double-quoted run to find and would drop out; and a
    comment sharing a line with an entry would add whatever *it* quotes.
    Each of those is a different pattern set, and a caller matching one
    reports nothing wrong about a list it never read.

    Args:
        pyproject_toml: the file's text.

    Returns:
        The list, in the order it is written; an empty one where the
        table or the key is absent -- the same fallback check-sdist's
        own hatchling plugin (`git_only_excludes`) uses, so this reads
        the identical question it answers; or None where the array is
        outside the shape above, which is a check that cannot answer
        rather than a check that passes.
    """
    in_target_section = False
    in_array = False
    patterns: list[str] = []
    for line in pyproject_toml.splitlines():
        stripped = line.strip()
        if in_array:
            if stripped == "]":
                return patterns
            if not stripped or stripped.startswith("#"):
                continue
            entry = _ENTRY_RE.match(stripped)
            if entry is None:
                return None
            patterns.append(entry.group("pattern"))
            continue
        if stripped.startswith("["):
            in_target_section = stripped == _TARGET_SECTION
        elif in_target_section:
            opened = _EXCLUDE_OPEN_RE.match(stripped)
            if opened is not None:
                if opened.group("rest"):
                    return None
                in_array = True
    return None if in_array else patterns


def submodule_paths(gitmodules: str) -> list[str]:
    """Return every submodule path `.gitmodules` names.

    Args:
        gitmodules: the text of `.gitmodules`.

    Returns:
        The paths, in the order `.gitmodules` lists them. Empty where
        the text names none.
    """
    return _SUBMODULE_PATH_RE.findall(gitmodules)


def tracked_files(root: Path) -> list[str] | None:
    """Return every file `git` tracks at `root`, submodules recursed into.

    Args:
        root: the repository's root.

    Returns:
        The paths `git ls-files` prints, one per element, or None where
        git exited non-zero.
    """
    result = subprocess.run(  # noqa: S603
        [_GIT, "ls-files", "--cached", "--recurse-submodules"],
        cwd=root,
        capture_output=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.splitlines()


def submodule_tracked_files(files: list[str], submodules: list[str]) -> list[str]:
    """Return which of `files` live inside one of `submodules`.

    This is the narrowing that keeps `/COPYRIGHT` -- a tracked file this
    repository's own exclude list drops from the sdist on purpose --
    out of what `excluded_tracked_files` below is asked about: it is a
    root-level file, so no `submodules` prefix matches it.

    Args:
        files: the tracked files to filter.
        submodules: the submodule paths to keep, as `.gitmodules` names
            them -- `submodule_paths`' own return value.

    Returns:
        The files whose path starts with one of `submodules` followed by
        a `/`, so that a submodule named `secp256k1` does not also match
        a same-prefixed sibling path no `.gitmodules` entry names.
    """
    prefixes = tuple(f"{path}/" for path in submodules)
    return [f for f in files if f.startswith(prefixes)]


def excluded_tracked_files(exclude: list[str], files: list[str]) -> list[str]:
    """Return which of `files` the gitignore-style `exclude` list matches.

    The same call check-sdist's own hatchling plugin makes
    (`check_sdist.backends._base.pathspec_filter`, via
    `check_sdist.backends.hatchling.HatchlingBackend.git_only_excludes`),
    against the tracked files that call silently drops from what
    check-sdist would otherwise report missing: a match here is exactly
    that drop.

    Args:
        exclude: the exclude list.
        files: the tracked files to check it against.

    Returns:
        The matching paths, sorted.
    """
    spec = pathspec.GitIgnoreSpec.from_lines(exclude)
    return sorted(f for f in files if spec.match_file(f))


def main() -> int:
    """Fail where an exclude entry matches a file a submodule tracks.

    Returns:
        0 where no entry matches a submodule-tracked file (including
        where the exclude list, the submodule list, or their
        intersection is empty, each of which matches nothing by
        construction), 1 where any entry does, where the exclude array
        is outside the shape `sdist_exclude_patterns` reads, or where
        `git ls-files` itself failed.
    """
    pyproject_toml = (_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    exclude = sdist_exclude_patterns(pyproject_toml)
    if exclude is None:
        print(
            "[tool.hatch.build.targets.sdist]'s exclude array is outside what"
            " this check reads: the array opens on a line ending in [, every"
            " entry is one double-quoted string with a trailing comma alone on"
            " its line, and the array closes on a line reading only ]. Any"
            " other shape is read as a different set of patterns, which is why"
            " this fails rather than answering"
            " (btclib-org/btclib-secp256k1#655)",
            file=sys.stderr,
        )
        return 1

    gitmodules = _ROOT / ".gitmodules"
    submodules = (
        submodule_paths(gitmodules.read_text(encoding="utf-8"))
        if gitmodules.exists()
        else []
    )

    files = tracked_files(_ROOT)
    if files is None:
        print("git ls-files --cached --recurse-submodules failed", file=sys.stderr)
        return 1

    submodule_files = submodule_tracked_files(files, submodules)
    caught = excluded_tracked_files(exclude, submodule_files)
    if caught:
        for path in caught:
            print(
                f"{path} is tracked by a submodule and matches "
                "[tool.hatch.build.targets.sdist]'s exclude list: check-sdist"
                " does not see it leave the sdist, its hatchling plugin reading"
                " that very list and subtracting what it matches from the"
                " tracked files it would otherwise report missing"
                " (btclib-org/btclib-secp256k1#655)",
                file=sys.stderr,
            )
        return 1

    print("no sdist exclude entry matches a submodule-tracked file")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
