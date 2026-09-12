# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
# SPDX-License-Identifier: MIT

"""Strip mypy/ruff suppression comments so the new checker can see the real errors.

We are moving from mypy to ty (``.tools/venv/bin/ty check src``).  The
``# type: ignore[...]`` codes in this codebase are mypy codes that ty does not
understand, and the ``# noqa: XXX###`` codes hide the ruff errors we now want to
work through one by one.

The rewrite is *comment-only*.  Sources are tokenized, so a lookalike inside a
string or docstring is never touched and no code is reformatted.  When a
suppression shares its comment with prose (``# noqa: BLE001 # we want to catch
all exceptions here``) the prose survives, because the reasoning behind the
suppression is exactly what whoever fixes the error needs.  Pass
``--drop-explanations`` to throw the whole comment away instead.

Only directives are removed; ``# pragma: no cover`` and friends are left alone.

Run with ``--diff`` first, then ``ruff check``, ``ruff format`` and
``.tools/venv/bin/ty check src`` to pick up the fallout.
"""

from __future__ import annotations

import argparse
import difflib
import io
import re
import sys
import tokenize
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from collections.abc import Iterator

#: A suppression directive inside a comment: mypy's ``type: ignore``, optionally
#: followed by a code list, or ruff's ``noqa`` with an optional code list.  The
#: look-behind keeps us off identifiers that merely end in these words, and the
#: code list is optional because a bare ``noqa`` is a blanket suppression.
DIRECTIVE_RE = re.compile(
    r"""
    (?<![A-Za-z0-9_-])
    (?:
        type:\s*ignore (?: \s*\[ [^\]]* \] )?
      |
        noqa (?: \s*:\s* [A-Za-z]+[0-9]+ (?: \s*,\s* [A-Za-z]+[0-9]+ )* )?
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)

#: File-level whole-file pragma.  It carries no information beyond the
#: suppression itself, so the entire comment goes.
FILE_PRAGMA_RE = re.compile(r"^#\s*(?:ruff|flake8)\s*:\s*noqa\b", re.IGNORECASE)

#: Everything a directive may be preceded by inside a comment and still "own"
#: the comment's opening hash: just hashes and whitespace.
LEAD_IN_RE = re.compile(r"[\s#]*")

#: One or more linter codes at the head of surviving prose (``PLR0913 - too many
#: arguments``).  The code itself went away with the directive, so saying it
#: again explains nothing.
LEADING_CODE_RE = re.compile(r"^(?:[A-Z]{1,4}[0-9]{3,4}\b[\s,]*[-:]?\s*)+")

#: Dashes/colons left dangling where a code used to sit in front of the prose.
LEADING_PUNCTUATION_RE = re.compile(r"^[-:\s]+")

#: Directory names never descended into when walking a tree (dot-prefixed
#: directories such as ``.venv`` are skipped as well).
SKIP_DIRS = frozenset({"__pycache__", "node_modules"})


class Options(NamedTuple):
    """What to remove and how to treat the text around it."""

    type_ignore: bool = True
    noqa: bool = True
    keep_explanations: bool = True


def _wanted(directive: str, opts: Options) -> bool:
    """Tell whether *directive* (as matched) should be removed under *opts*."""
    return opts.noqa if directive.lower().startswith("noqa") else opts.type_ignore


def directive_spans(comment: str, opts: Options) -> list[tuple[int, int]]:
    """Return the spans of suppressions to remove from a single comment."""
    if FILE_PRAGMA_RE.match(comment):
        return [(0, len(comment))]
    return [match.span() for match in DIRECTIVE_RE.finditer(comment) if _wanted(match.group(0), opts)]


def strip_comment(comment: str, opts: Options) -> str | None:
    """Remove suppressions from *comment*.

    :returns: The rewritten comment, ``None`` when nothing is left of it, or
        *comment* unchanged when it holds no suppression.
    """
    spans = directive_spans(comment, opts)
    if not spans:
        return comment

    head = comment[: spans[0][0]]
    owns_hash = LEAD_IN_RE.fullmatch(head) is not None

    if not opts.keep_explanations:
        return None if owns_hash else re.sub(r"[\s#]+\Z", "", head) or None

    remainder = comment
    for start, end in reversed(spans):
        remainder = remainder[:start] + remainder[end:]

    if owns_hash:
        # The removed directive owned the comment's opening hash, so whatever
        # survives (a second comment, or plain prose) needs a fresh one.
        body = _prose(remainder)
        return f"# {body}" if body else None

    return re.sub(r"[\s#]+\Z", "", remainder) or None


def _prose(text: str) -> str:
    """Normalize the text that survives a directive removal.

    Turns ``"  # PLR0913 - too many arguments"`` into ``"too many arguments"``:
    the hash and the repeated code go, the human reasoning stays.
    """
    body = re.sub(r"^[\s#]+", "", text).rstrip()
    body = LEADING_CODE_RE.sub("", body)
    return LEADING_PUNCTUATION_RE.sub("", body)


def strip_source(text: str, opts: Options) -> tuple[str, int]:
    """Remove suppressions from the Python source *text*.

    :returns: A ``(new_text, directives_removed)`` tuple.
    :raises SyntaxError: If *text* cannot be tokenized.
    """
    lines = text.splitlines(keepends=True)
    replacements: dict[int, str | None] = {}
    removed = 0

    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type != tokenize.COMMENT:
            continue
        new_comment = strip_comment(token.string, opts)
        if new_comment == token.string:
            continue
        removed += len(directive_spans(token.string, opts))

        row = token.start[0]
        line = lines[row - 1]
        body = line.removesuffix("\n")
        eol = line[len(body) :]
        code = body[: token.start[1]]

        if new_comment is None:
            # Nothing to attach the comment to any more: drop the whole physical
            # line if it held only the comment, else just the comment.
            replacements[row] = None if not code.strip() else code.rstrip() + eol
        else:
            replacements[row] = code + new_comment + eol

    if not replacements:
        return text, 0

    # A replacement of None means the physical line held nothing but the
    # suppression, so the line itself goes.
    new_text = "".join(
        line if row not in replacements else (replacements[row] or "") for row, line in enumerate(lines, 1)
    )
    _assert_still_parses(new_text)
    return new_text, removed


def _assert_still_parses(text: str) -> None:
    """Guard against a rewrite that broke the file's token stream."""
    try:
        list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (SyntaxError, tokenize.TokenError, IndentationError) as exc:
        msg = f"rewriting would break this file ({exc}); leaving it untouched"
        raise SyntaxError(msg) from exc


def python_files(paths: list[str]) -> Iterator[Path]:
    """Yield the ``*.py`` files under *paths*, skipping vendored/hidden trees."""
    seen: set[Path] = set()
    for raw in paths:
        root = Path(raw)
        candidates = [root] if root.is_file() else sorted(root.rglob("*.py"))
        for path in candidates:
            if not path.is_file() or path.suffix != ".py":
                continue
            if any(part in SKIP_DIRS or part.startswith(".") for part in path.parts[:-1]):
                continue
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                yield path


def process(path: Path, opts: Options) -> tuple[str, str, int]:
    """Rewrite one file.

    :returns: ``(old_text, new_text, directives_removed)``; unchanged files
        report ``0`` and an identical ``new_text``.
    """
    old_text = path.read_text(encoding="utf-8")
    try:
        return (old_text, *strip_source(old_text, opts))
    except (SyntaxError, tokenize.TokenError, UnicodeDecodeError) as exc:
        _write(f"skipped {path}: {exc}\n")
        return old_text, old_text, 0


def unified_diff(path: Path, old_text: str, new_text: str) -> str:
    """Return a unified diff for a rewritten file."""
    return "".join(
        difflib.unified_diff(
            old_text.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            fromfile=f"a/{path.as_posix()}",
            tofile=f"b/{path.as_posix()}",
        )
    )


def _write(text: str) -> None:
    sys.stdout.write(text)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="strip_suppressions.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python tools/strip_suppressions.py --diff\n"
            "  python tools/strip_suppressions.py\n"
            "  python tools/strip_suppressions.py --only type-ignore\n"
            "  python tools/strip_suppressions.py --drop-explanations src/oarepo_model\n"
        ),
    )
    parser.add_argument(
        "paths", nargs="*", default=["src", "tests"], help="files or directories to clean (default: src tests)"
    )
    parser.add_argument(
        "--only", choices=("type-ignore", "noqa"), help="restrict the rewrite to one kind of suppression"
    )
    parser.add_argument(
        "--drop-explanations",
        action="store_true",
        help="drop the whole comment instead of keeping prose written next to the suppression",
    )
    parser.add_argument("--diff", action="store_true", help="print a unified diff and change nothing")
    parser.add_argument("-q", "--quiet", action="store_true", help="only report the totals")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point: rewrite the requested paths and report what happened."""
    args = parse_args(argv)
    opts = Options(
        type_ignore=args.only in (None, "type-ignore"),
        noqa=args.only in (None, "noqa"),
        keep_explanations=not args.drop_explanations,
    )

    for raw in args.paths:
        if not Path(raw).exists():
            _write(f"error: no such file or directory: {raw}\n")
            return 2

    total_files = total_directives = 0
    for path in python_files(args.paths):
        old_text, new_text, removed = process(path, opts)
        if not removed:
            continue
        total_files += 1
        total_directives += removed
        if args.diff:
            _write(unified_diff(path, old_text, new_text))
        else:
            path.write_text(new_text, encoding="utf-8")
        if not args.quiet:
            _write(f"{'would clean' if args.diff else 'cleaned'} {path.as_posix()} ({removed})\n")

    verb = "would remove" if args.diff else "removed"
    _write(f"\n{verb} {total_directives} suppression(s) from {total_files} file(s)\n")
    if total_files and not args.diff:
        _write("next: ruff check --fix && ruff format && .tools/venv/bin/ty check src\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
