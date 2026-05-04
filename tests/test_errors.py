"""Error-path tests for ``analyze``.

Covers every documented failure mode: unsupported-language dispatch, type
guards, and syntax errors in each of the five supported languages. Also
verifies backwards-compatibility with code that catches plain ``ValueError``.
"""

from __future__ import annotations

import pytest

from maintainability_analyzer import (
    AnalyzerError,
    ParseError,
    UnsupportedLanguageError,
    analyze,
)


# -- Dispatch errors ---------------------------------------------------------

def test_unsupported_language_lists_supported_options():
    with pytest.raises(UnsupportedLanguageError) as excinfo:
        analyze("", language="ruby")
    msg = str(excinfo.value)
    assert "ruby" in msg
    # Every supported language should appear in the message.
    for lang in ("python", "java", "csharp", "c", "cpp"):
        assert lang in msg


def test_missing_language_and_filepath_names_both_args():
    with pytest.raises(UnsupportedLanguageError) as excinfo:
        analyze("def x(): pass")
    msg = str(excinfo.value)
    assert "language" in msg and "filepath" in msg


def test_unknown_extension_lists_supported_extensions():
    with pytest.raises(UnsupportedLanguageError) as excinfo:
        analyze("", filepath="foo.xyz")
    msg = str(excinfo.value)
    assert "foo.xyz" in msg
    assert ".py" in msg and ".java" in msg


# -- Type guard --------------------------------------------------------------

def test_non_string_source_raises_typeerror():
    with pytest.raises(TypeError) as excinfo:
        analyze(b"def x(): pass", language="python")
    assert "bytes" in str(excinfo.value)


def test_none_source_raises_typeerror():
    with pytest.raises(TypeError):
        analyze(None, language="python")


# -- Syntax errors -----------------------------------------------------------

def test_python_syntax_error_includes_location():
    with pytest.raises(ParseError) as excinfo:
        analyze("def (\n", language="python")
    err = excinfo.value
    assert err.language == "python"
    assert err.line == 1
    assert err.column is not None
    assert "python" in str(err)


def test_java_syntax_error():
    with pytest.raises(ParseError) as excinfo:
        analyze("class {}", language="java")
    err = excinfo.value
    assert err.language == "java"
    assert "java" in str(err)


def test_csharp_syntax_error_includes_location():
    with pytest.raises(ParseError) as excinfo:
        analyze("class {", language="csharp")
    err = excinfo.value
    assert err.language == "csharp"
    assert err.line is not None and err.line >= 1


def test_c_syntax_error_includes_location():
    with pytest.raises(ParseError) as excinfo:
        analyze("int main() { return", language="c")
    err = excinfo.value
    assert err.language == "c"
    assert err.line is not None


def test_cpp_syntax_error_includes_location():
    with pytest.raises(ParseError) as excinfo:
        analyze("int main() {", language="cpp")
    err = excinfo.value
    assert err.language == "cpp"
    assert err.line is not None


# -- Backwards compatibility -------------------------------------------------

def test_unsupported_language_is_still_valueerror():
    """Pre-existing callers (and tests/test_api.py) catch ValueError."""
    with pytest.raises(ValueError):
        analyze("", language="ruby")


def test_parse_error_is_still_valueerror():
    with pytest.raises(ValueError):
        analyze("def (\n", language="python")


def test_all_errors_catchable_as_analyzer_error():
    with pytest.raises(AnalyzerError):
        analyze("", language="ruby")
    with pytest.raises(AnalyzerError):
        analyze("def (\n", language="python")
