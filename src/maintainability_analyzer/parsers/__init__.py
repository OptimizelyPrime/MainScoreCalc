"""Public ``analyze`` entry point.

All language parsers return a :class:`ParserResult`. This module attaches
file-level raw line metrics and serializes to the documented nested shape.
"""

from __future__ import annotations

from ..errors import (
    AnalyzerError,
    BackendUnavailableError,
    ParseError,
    UnsupportedLanguageError,
)
from ..raw import CommentStyle, count_raw_lines
from ..utils import EXTENSION_MAP, SUPPORTED_LANGUAGES, guess_language
from .base import ParserResult, scope_to_metrics


# Import each language parser lazily-at-module-load, but tolerate a missing
# optional backend so importing ``maintainability_analyzer`` doesn't fail just
# because (say) ``javalang`` isn't installed. The dispatcher below surfaces a
# BackendUnavailableError with an install hint when the caller asks for a
# language whose backend failed to import.
_BACKEND_IMPORT_ERRORS: dict[str, ImportError] = {}

try:
    from .python_parser import analyze_python_code, parse_python
except ImportError as e:  # pragma: no cover - stdlib ast is always present
    parse_python = analyze_python_code = None  # type: ignore[assignment]
    _BACKEND_IMPORT_ERRORS["python"] = e

try:
    from .cpp_parser import analyze_cpp_code, parse_cpp
except ImportError as e:
    parse_cpp = analyze_cpp_code = None  # type: ignore[assignment]
    _BACKEND_IMPORT_ERRORS["cpp"] = e
    _BACKEND_IMPORT_ERRORS["c"] = e

try:
    from .java_parser import analyze_java_code, parse_java
except ImportError as e:
    parse_java = analyze_java_code = None  # type: ignore[assignment]
    _BACKEND_IMPORT_ERRORS["java"] = e

try:
    from .csharp_parser import analyze_csharp_code, parse_csharp
except ImportError as e:
    parse_csharp = analyze_csharp_code = None  # type: ignore[assignment]
    _BACKEND_IMPORT_ERRORS["csharp"] = e


_COMMENT_STYLE = {
    "python": CommentStyle.PYTHON,
    "c": CommentStyle.SLASH_STAR_SLASH_SLASH,
    "cpp": CommentStyle.SLASH_STAR_SLASH_SLASH,
    "java": CommentStyle.SLASH_STAR_SLASH_SLASH,
    "csharp": CommentStyle.SLASH_STAR_SLASH_SLASH,
}

_BACKEND_INSTALL_HINTS = {
    "cpp": "pip install libclang",
    "c": "pip install libclang",
    "java": "pip install javalang",
    "csharp": "pip install tree-sitter tree-sitter-c-sharp",
}


def analyze(source_code, language=None, filepath=None):
    """Analyze source code and return a structured metrics dict.

    See README for the full output shape.
    """
    if not isinstance(source_code, str):
        raise TypeError(
            f"analyze() source_code must be str, got {type(source_code).__name__}"
        )

    language = _resolve_language(language, filepath)
    _require_backend(language)

    try:
        if language == "python":
            result = parse_python(source_code)
        elif language in ("cpp", "c"):
            result = parse_cpp(source_code, lang=language)
        elif language == "java":
            result = parse_java(source_code)
        elif language == "csharp":
            result = parse_csharp(source_code)
    except AnalyzerError:
        raise
    except SyntaxError as e:
        # Python's ast.parse.
        raise ParseError(
            f"{language}: syntax error at line {e.lineno}, column {e.offset}: {e.msg}",
            language=language,
            line=e.lineno,
            column=e.offset,
        ) from e
    except Exception as e:
        raise _wrap_backend_exception(e, language) from e

    result.file.raw = count_raw_lines(source_code, _COMMENT_STYLE[language])
    return _serialize(result)


def _resolve_language(language, filepath):
    if language is not None:
        if language not in SUPPORTED_LANGUAGES:
            raise UnsupportedLanguageError(
                f"Unsupported language {language!r}. "
                f"Supported: {', '.join(SUPPORTED_LANGUAGES)}."
            )
        return language
    if filepath is None:
        raise UnsupportedLanguageError(
            "analyze() requires either language=<name> or filepath=<path>; "
            "both were None."
        )
    guessed = guess_language(filepath)
    if guessed is None:
        exts = ", ".join(sorted(EXTENSION_MAP.keys()))
        raise UnsupportedLanguageError(
            f"Could not infer language from filepath {filepath!r}. "
            f"Supported extensions: {exts}."
        )
    return guessed


def _require_backend(language):
    if language in _BACKEND_IMPORT_ERRORS:
        hint = _BACKEND_INSTALL_HINTS.get(language, "")
        msg = f"Parser backend for {language!r} is not available."
        if hint:
            msg += f" Install with: {hint}"
        raise BackendUnavailableError(msg) from _BACKEND_IMPORT_ERRORS[language]


def _wrap_backend_exception(exc, language):
    """Translate a backend-specific parse exception into :class:`ParseError`.

    Keeps the backend import out of this module — we inspect the exception's
    class name / module to decide whether it's a known parse failure.
    """
    cls = type(exc)
    module = getattr(cls, "__module__", "") or ""
    name = cls.__name__

    line = getattr(exc, "lineno", None)
    column = getattr(exc, "offset", None)
    # javalang encodes the offending token in `.at` (a (line, column) tuple
    # or a Token with .position on newer versions).
    at = getattr(exc, "at", None)
    if at is not None and line is None:
        pos = getattr(at, "position", None)
        if pos is not None:
            line = getattr(pos, "line", None)
            column = getattr(pos, "column", None)

    description = getattr(exc, "description", None) or str(exc) or name

    if module.startswith("javalang"):
        return ParseError(
            f"{language}: parse error: {description}",
            language=language,
            line=line,
            column=column,
        )

    # Unknown exception — still wrap as ParseError so callers can catch a
    # consistent type, but pass through the original message verbatim.
    return ParseError(
        f"{language}: parse error: {description}",
        language=language,
        line=line,
        column=column,
    )


def _serialize(result: ParserResult) -> dict:
    out = {
        "language": result.language,
        "file": scope_to_metrics(result.file).to_dict(is_function=False),
        "classes": {},
        "functions": {},
    }
    for cname, cscope in result.classes.items():
        cdict = scope_to_metrics(cscope).to_dict(is_function=False)
        cdict["methods"] = list(cscope.method_names)
        out["classes"][cname] = cdict
    for fname, fscope in result.functions.items():
        out["functions"][fname] = scope_to_metrics(fscope).to_dict(is_function=True)
    return out


__all__ = [
    "analyze",
    "ParserResult",
    "analyze_python_code",
    "analyze_java_code",
    "analyze_cpp_code",
    "analyze_csharp_code",
    "parse_python",
    "parse_java",
    "parse_cpp",
    "parse_csharp",
]
