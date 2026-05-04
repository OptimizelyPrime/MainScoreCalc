"""Sanity-check Python metrics against radon on the shared Python fixture.

Raw line counting and cyclomatic complexity should stay close to radon. MI is
intentionally not compared: our formula penalizes cognitive complexity in
addition to cyclomatic, so it diverges from radon's MI by design.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from maintainability_analyzer import analyze

radon_raw = pytest.importorskip("radon.raw")
radon_complexity = pytest.importorskip("radon.complexity")


FIXTURE = Path(__file__).parent / "fixtures" / "sample.py"


def test_loc_matches_radon_within_tolerance():
    src = FIXTURE.read_text(encoding="utf-8")
    ours = analyze(src, language="python")["file"]["raw"]
    theirs = radon_raw.analyze(src)

    # LOC should match exactly (both count physical lines).
    assert ours["loc"] == theirs.loc
    # Blank lines should also match.
    assert ours["blank"] == theirs.blank
    # Comments may differ by ~1 on edge cases; allow a small tolerance.
    assert abs(ours["comments"] - theirs.comments) <= 1
    # sloc may differ by up to a few lines: radon subtracts full-line `#`
    # comment lines from sloc, while we treat any non-blank line as sloc.
    assert abs(ours["sloc"] - theirs.sloc) <= 3


def test_cyclomatic_complexity_matches_radon():
    src = FIXTURE.read_text(encoding="utf-8")
    ours = analyze(src, language="python")

    blocks = radon_complexity.cc_visit(src)
    # Build {function_or_method_name: radon_cc}.
    radon_cc = {}
    for b in blocks:
        radon_cc[b.name] = b.complexity

    # For each top-level/method name radon reports, we should agree exactly.
    for name, cc in radon_cc.items():
        # radon uses dotted names for methods (e.g. Calculator.factorial).
        short = name.split(".")[-1]
        if short in ours["functions"]:
            assert ours["functions"][short]["complexity"]["cyclomatic"] == cc, (
                f"cyclomatic mismatch for {name}: ours="
                f"{ours['functions'][short]['complexity']['cyclomatic']} radon={cc}"
            )
