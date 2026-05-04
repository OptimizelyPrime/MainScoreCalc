"""Language-aware raw line counting.

Produces :class:`RawMetrics` from source text given a comment style. The same
routine is used for file-level counts and for per-scope counts by slicing the
source to the scope's line range first (see :func:`slice_lines`).
"""

from __future__ import annotations

from enum import Enum

from .metrics import RawMetrics


class CommentStyle(Enum):
    PYTHON = "python"                         # # line comments, ''' or \"\"\" triple strings
    SLASH_STAR_SLASH_SLASH = "c_family"       # // and /* ... */


def slice_lines(source: str, start_line: int | None, end_line: int | None) -> str:
    """1-indexed inclusive line slice. Returns full source if bounds are None."""
    if start_line is None and end_line is None:
        return source
    lines = source.splitlines(keepends=True)
    s = (start_line - 1) if start_line else 0
    e = end_line if end_line else len(lines)
    s = max(0, s)
    e = min(len(lines), e)
    return "".join(lines[s:e])


def count_raw_lines(source: str, style: CommentStyle) -> RawMetrics:
    if style == CommentStyle.PYTHON:
        return _count_python(source)
    return _count_c_family(source)


def _count_python(source: str) -> RawMetrics:
    lines = source.splitlines()
    loc = len(lines)
    blank = 0
    comments = 0
    multi = 0
    sloc = 0
    lloc = 0

    in_triple = False
    triple_delim = ""
    for raw_line in lines:
        line = raw_line.rstrip("\r")
        stripped = line.strip()

        if in_triple:
            multi += 1
            if triple_delim in stripped:
                in_triple = False
                triple_delim = ""
            continue

        if not stripped:
            blank += 1
            continue

        # Opening of a triple-quoted string that spans lines.
        for delim in ('"""', "'''"):
            if stripped.startswith(delim):
                rest = stripped[3:]
                if delim in rest:
                    # single-line triple string — treat as multi (docstring-like)
                    multi += 1
                    sloc += 1
                    break
                in_triple = True
                triple_delim = delim
                multi += 1
                break
        else:
            if stripped.startswith("#"):
                comments += 1
                sloc += 1
            else:
                sloc += 1
                lloc += _logical_lines(stripped)
            continue
        # If the for/else fell through on a triple-string opening, we already counted.

    return RawMetrics(loc=loc, sloc=sloc, lloc=lloc, comments=comments, multi=multi, blank=blank)


def _logical_lines(stripped: str) -> int:
    """Best-effort logical-line count for a Python source line.

    Splits on top-level ``;`` separators that are outside strings. This matches
    radon's behavior closely enough for typical code.
    """
    count = 1
    in_str = None
    i = 0
    while i < len(stripped):
        ch = stripped[i]
        if in_str:
            if ch == "\\":
                i += 2
                continue
            if ch == in_str:
                in_str = None
        else:
            if ch in ('"', "'"):
                in_str = ch
            elif ch == "#":
                break
            elif ch == ";":
                # Only count if something follows
                rest = stripped[i + 1 :].strip()
                if rest and not rest.startswith("#"):
                    count += 1
        i += 1
    return count


def _count_c_family(source: str) -> RawMetrics:
    lines = source.splitlines()
    loc = len(lines)
    blank = 0
    comments = 0
    multi = 0
    sloc = 0
    lloc = 0

    in_block = False
    for raw_line in lines:
        line = raw_line.rstrip("\r")
        stripped = line.strip()

        if in_block:
            multi += 1
            if "*/" in stripped:
                in_block = False
            continue

        if not stripped:
            blank += 1
            continue

        if stripped.startswith("//"):
            comments += 1
            sloc += 1
            continue

        if stripped.startswith("/*"):
            if "*/" in stripped[2:]:
                comments += 1
                sloc += 1
            else:
                in_block = True
                multi += 1
            continue

        sloc += 1
        lloc += _c_logical_lines(stripped)

    return RawMetrics(loc=loc, sloc=sloc, lloc=lloc, comments=comments, multi=multi, blank=blank)


def _c_logical_lines(stripped: str) -> int:
    """Count top-level ``;`` occurrences outside strings/chars as logical statements."""
    count = 0
    in_str = None
    i = 0
    saw_code = False
    while i < len(stripped):
        ch = stripped[i]
        if in_str:
            if ch == "\\":
                i += 2
                continue
            if ch == in_str:
                in_str = None
            i += 1
            continue
        if ch in ('"', "'"):
            in_str = ch
            saw_code = True
        elif ch == "/" and i + 1 < len(stripped) and stripped[i + 1] == "/":
            break
        elif ch == ";":
            count += 1
        elif not ch.isspace():
            saw_code = True
        i += 1
    if count == 0 and saw_code:
        return 1
    return count
