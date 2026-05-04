# AGENTS.md

This document provides instructions for AI agents working with this repository.

## Project Overview

This project is a Python library that analyzes source code files to calculate
maintainability metrics. It computes the Maintainability Index (MI) on a 0–100
scale using the standard formula that considers Halstead volume, cyclomatic
complexity, cognitive complexity, and lines of code.

The library supports multiple programming languages through a parser-based
architecture. Each language parser walks its AST and populates `Scope` objects,
which are converted to `ScopeMetrics` and serialized by the public `analyze()`
entry point in `src/maintainability_score_analyzer/parsers/__init__.py`.

The public package name is `maintainability_score_analyzer`. A thin
`maintainability_analyzer` re-export shim exists in
`src/maintainability_analyzer/__init__.py` for backwards compatibility.

## Getting Started

Install in editable mode with all dependencies:

```bash
pip install -e .
```

## How to Run Tests

The project uses `pytest`:

```bash
pytest
```

To run a single test:

```bash
pytest tests/test_fixtures.py::test_python_fixture
```

To lint (matches CI):

```bash
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

## How to Add a New Language

To add support for a new language, follow these steps:

1. **Create a new parser**:
   - Create `src/maintainability_score_analyzer/parsers/<language>_parser.py`.
   - Implement a `_Walker`-style class that walks the AST and fans out
     operators/operands/cyclomatic/cognitive/statement writes to every active
     scope on a `_scope_stack` (file → class → function). See the existing
     parsers (e.g., `python_parser.py`) for the pattern.
   - Expose two functions:
     - `parse_<lang>(source_code) -> ParserResult` — used by `analyze()`.
     - `analyze_<lang>_code(source_code) -> tuple` — legacy 6-tuple kept only
       for existing per-parser tests.

2. **Register the extension mapping**:
   - In `src/maintainability_score_analyzer/utils.py`, add the file
     extension(s) to `EXTENSION_MAP` so `analyze(filepath=...)` can infer the
     language.

3. **Wire the parser into `analyze()`**:
   - In `src/maintainability_score_analyzer/parsers/__init__.py`:
     - Import `parse_<lang>` and `analyze_<lang>_code` inside a `try/except
       ImportError` block (pattern already used for all other languages).
     - Add the language key to `_COMMENT_STYLE`.
     - Add an install hint to `_BACKEND_INSTALL_HINTS`.
     - Add a dispatch branch in the `analyze()` function body.

4. **Add tests**:
   - Create `tests/test_<language>_parser.py` with unit tests that exercise
     both `parse_<lang>()` and `analyze_<lang>_code()`.

## Existing Parsers

| Language   | Parser file            | Backend              | Status in `analyze()` |
|------------|------------------------|----------------------|-----------------------|
| Python     | `python_parser.py`     | stdlib `ast`         | Supported             |
| Java       | `java_parser.py`       | `javalang`           | Supported             |
| C / C++    | `cpp_parser.py`        | `libclang`           | Supported             |
| C#         | `csharp_parser.py`     | `tree-sitter-c-sharp`| Supported             |
| JavaScript | `javascript_parser.py` | `esprima`            | **Not yet wired in**  |

The JavaScript parser pre-dates the `ParserResult` architecture. It exposes
`analyze_javascript_code()` returning a legacy 7-tuple, and does not follow the
`_Walker` / `_scope_stack` pattern. It will need to be refactored before it can
be registered with `analyze()`.

## Code Style

This project follows PEP 8. Use `flake8` to check compliance:

```bash
flake8 src tests
```
