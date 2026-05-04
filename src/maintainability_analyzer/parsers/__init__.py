"""Public ``analyze`` entry point.

All language parsers return a :class:`ParserResult`. This module attaches
file-level raw line metrics and serializes to the documented nested shape.
"""

from __future__ import annotations

from ..raw import CommentStyle, count_raw_lines
from ..utils import guess_language
from .base import ParserResult, scope_to_metrics
from .cpp_parser import analyze_cpp_code, parse_cpp
from .csharp_parser import analyze_csharp_code, parse_csharp
from .java_parser import analyze_java_code, parse_java
from .python_parser import analyze_python_code, parse_python


_COMMENT_STYLE = {
    "python": CommentStyle.PYTHON,
    "c": CommentStyle.SLASH_STAR_SLASH_SLASH,
    "cpp": CommentStyle.SLASH_STAR_SLASH_SLASH,
    "java": CommentStyle.SLASH_STAR_SLASH_SLASH,
    "csharp": CommentStyle.SLASH_STAR_SLASH_SLASH,
}


def analyze(source_code, language=None, filepath=None):
    """Analyze source code and return a structured metrics dict.

    See README for the full output shape.
    """
    if language is None:
        if filepath is None:
            raise ValueError("Must provide either language or filepath.")
        language = guess_language(filepath)
        if language is None:
            raise ValueError(f"Could not guess language from file extension of {filepath}")

    if language == "python":
        result = parse_python(source_code)
    elif language in ("cpp", "c"):
        result = parse_cpp(source_code, lang=language)
    elif language == "java":
        result = parse_java(source_code)
    elif language == "csharp":
        result = parse_csharp(source_code)
    else:
        raise ValueError(f"Unsupported language: {language}")

    result.file.raw = count_raw_lines(source_code, _COMMENT_STYLE[language])
    return _serialize(result)


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
