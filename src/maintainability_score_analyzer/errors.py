"""Exception hierarchy for the maintainability analyzer.

Every error raised from the public ``analyze`` API (and the ``parse_<lang>``
helpers) is a subclass of :class:`AnalyzerError`, so callers can catch that one
class to handle any analyzer failure. The concrete subclasses also inherit
from stdlib exception types (``ValueError`` / ``ImportError``) to preserve
backwards compatibility with callers that catch those.
"""

from __future__ import annotations


class AnalyzerError(Exception):
    """Base class for all maintainability_analyzer errors."""


class UnsupportedLanguageError(AnalyzerError, ValueError):
    """Language is not supported or could not be inferred from a filepath."""


class ParseError(AnalyzerError, ValueError):
    """Source code could not be parsed by the selected language backend.

    Attributes:
        language: The language the parser was invoked for.
        line: 1-indexed line number of the first error, if known.
        column: 1-indexed column, if known.
    """

    def __init__(self, message, *, language, line=None, column=None):
        super().__init__(message)
        self.language = language
        self.line = line
        self.column = column


class BackendUnavailableError(AnalyzerError, ImportError):
    """An optional parser backend package is not installed."""
