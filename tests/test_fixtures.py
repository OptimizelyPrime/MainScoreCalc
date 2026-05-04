"""End-to-end tests against the sample fixtures for each language.

These assert the new output shape is emitted consistently across all four
parser backends and that the shared Calculator / factorial / sum_positive
structure produces sensible per-metric-family values.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from maintainability_analyzer import analyze


FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _assert_shape(result: dict, expected_language: str):
    assert result["language"] == expected_language
    assert set(result.keys()) == {"language", "file", "classes", "functions"}

    for key in ("raw", "halstead", "complexity", "structural", "maintainability_index"):
        assert key in result["file"], f"missing file.{key}"
    for key in ("loc", "sloc", "lloc", "comments", "multi", "blank", "comment_ratio"):
        assert key in result["file"]["raw"]
    assert "cyclomatic" in result["file"]["complexity"]
    assert "cognitive" in result["file"]["complexity"]

    for fname, f in result["functions"].items():
        for key in ("raw", "halstead", "complexity", "structural", "maintainability_index"):
            assert key in f, f"function {fname} missing {key}"
        s = f["structural"]
        for key in ("max_nesting_depth", "statement_count", "parameter_count", "return_count"):
            assert key in s, f"function {fname} missing structural.{key}"


def test_python_fixture():
    result = analyze(_load("sample.py"), language="python")
    _assert_shape(result, "python")

    assert "Calculator" in result["classes"]
    assert set(result["classes"]["Calculator"]["methods"]) == {
        "__init__", "add", "factorial", "sum_positive",
    }
    assert "classify" in result["functions"]

    factorial = result["functions"]["factorial"]
    assert factorial["complexity"]["cyclomatic"] == 3   # two ifs + function
    assert factorial["complexity"]["cognitive"] >= 3    # two ifs + self-recursion
    assert factorial["structural"]["return_count"] == 2
    assert factorial["structural"]["parameter_count"] == 2  # self + n

    classify = result["functions"]["classify"]
    # 3 elif chain = 4 decision points
    assert classify["complexity"]["cyclomatic"] == 4


def test_java_fixture():
    result = analyze(_load("sample.java"), language="java")
    _assert_shape(result, "java")
    assert "Calculator" in result["classes"]
    assert "factorial" in result["functions"]
    fact = result["functions"]["factorial"]
    assert fact["complexity"]["cyclomatic"] == 2
    assert fact["structural"]["return_count"] == 2


def test_cpp_fixture():
    result = analyze(_load("sample.cpp"), language="cpp")
    _assert_shape(result, "cpp")
    assert "Calculator" in result["classes"]
    assert "factorial" in result["functions"]
    assert "sum_positive" in result["functions"]
    sp = result["functions"]["sum_positive"]
    # for + nested if = cyclomatic 3
    assert sp["complexity"]["cyclomatic"] == 3


def test_c_fixture():
    result = analyze(_load("sample.c"), language="c")
    _assert_shape(result, "c")
    # Free functions only — no classes in C.
    assert result["classes"] == {}
    assert "factorial" in result["functions"]
    assert "sum_positive" in result["functions"]
    assert "main" in result["functions"]


def test_csharp_fixture():
    result = analyze(_load("sample.cs"), language="csharp")
    _assert_shape(result, "csharp")
    assert "Calculator" in result["classes"]
    # Constructor + Add + Factorial + SumPositive
    methods = set(result["classes"]["Calculator"]["methods"])
    assert {"Add", "Factorial", "SumPositive"} <= methods
    fact = result["functions"]["Factorial"]
    assert fact["complexity"]["cyclomatic"] == 2
    assert fact["structural"]["return_count"] == 2


def test_file_raw_counts_nonzero_across_languages():
    for lang, filename in [
        ("python", "sample.py"),
        ("java", "sample.java"),
        ("cpp", "sample.cpp"),
        ("c", "sample.c"),
        ("csharp", "sample.cs"),
    ]:
        r = analyze(_load(filename), language=lang)
        raw = r["file"]["raw"]
        assert raw["loc"] > 0, f"{lang}: loc should be > 0"
        assert raw["sloc"] > 0, f"{lang}: sloc should be > 0"
