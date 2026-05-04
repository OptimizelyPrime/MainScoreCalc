# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- **Install (editable) with deps**: `pip install -e .`
- **Run full test suite**: `pytest`
- **Run a single test**: `pytest tests/test_fixtures.py::test_python_fixture`
- **Lint (matches CI)**: `flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics`
- **CI matrix**: Python 3.11 and 3.12 on `ubuntu-latest` (see `.github/workflows/python-package.yml`).

## Architecture

Library-only package. Single public entry point: `analyze(source_code, language=None, filepath=None)` from `maintainability_analyzer`. Returns a nested dict with `language`, `file`, `classes`, and `functions` keys — see README for the full shape.

### Module layout

- `metrics.py` — dataclasses for each metric family (`RawMetrics`, `HalsteadMetrics`, `ComplexityMetrics`, `StructuralMetrics`) composed into `ScopeMetrics`. The maintainability-index formula lives on `ScopeMetrics.maintainability_index`.
- `parsers/base.py` — `Scope` (mutable per-scope working state a parser accumulates into) and `ParserResult` (the file/classes/functions triple each parser returns).
- `raw.py` — language-aware raw line counter. Takes a `CommentStyle` (`PYTHON` or `SLASH_STAR_SLASH_SLASH`) and returns `RawMetrics`. Used both for file-level counts and for per-scope counts via `slice_lines()`.
- `parsers/__init__.py` — public `analyze()`. Dispatches to the right language parser, attaches file-level raw metrics, serializes `ParserResult` → dict.
- `parsers/{python,java,cpp,csharp}_parser.py` — each exposes `parse_<lang>()` returning a `ParserResult` and a legacy `analyze_<lang>_code()` 6-tuple for existing per-parser tests.

### Per-parser walker pattern

Every parser uses the same shape: a `_Walker` class with a `_scope_stack` (file → class → function) and a `_nesting` stack. As the walker descends, **operators/operands/cyclomatic/cognitive/statement writes fan out to every scope on the stack**, so aggregation at file and class scope is free. Nesting depth increments on entry to decision/loop/catch nodes and decrements on exit.

### Parser backends

- `python_parser.py` — `ast.NodeVisitor`. Cleanest; subclass the visitor.
- `java_parser.py` — `javalang` AST, manual recursive child walk via `node.attrs`.
- `cpp_parser.py` — `libclang` cursors. Only walks cursors whose `location.file` matches the main TU file, so stdlib includes don't pollute results. Include paths are injected only when running on Linux (`_clang_args`); on Windows the parser works with simple fixtures that don't depend on stdlib.
- `csharp_parser.py` — `tree-sitter-c-sharp`. Full CST walk, not regex.

### Cognitive complexity rules (Sonar-style)

+1 for each if/else-if/for/while/do/switch-case/catch/ternary, **+1 extra per enclosing nesting level** for nested flow, +1 per `&&`/`||` sequence, +1 for explicit `else` branches, +1 for direct recursion (bare-name or `self.X()`/`cls.X()` calls).

### Gotchas

- On Windows, C/C++ code with unresolved `#include` directives will have function bodies silently dropped by libclang. Tests deliberately use stdlib-free fixtures (`tests/fixtures/sample.c`, `sample.cpp`) to avoid this. On Linux CI, the hardcoded include paths in `_clang_args` resolve these.
- `tree-sitter-c-sharp` returns `[row, column]` **0-indexed**; add 1 when storing as 1-indexed line numbers in `Scope.start_line` / `end_line`.
- The `analyze_<lang>_code()` 6-tuple functions are kept only because `tests/test_{python,java,cpp,csharp}_parser.py` imports them. New code should use `parse_<lang>()` which returns a `ParserResult`.
- Radon parity: the Python parser's cyclomatic-complexity numbers match `radon.complexity.cc_visit` exactly on the fixture. Raw-line counts differ slightly because radon subtracts full-line `#` comments from its `sloc`; we treat any non-blank line as `sloc`. See `tests/test_parity_radon.py`.
