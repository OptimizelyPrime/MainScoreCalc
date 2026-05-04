# Maintainability Analyzer

A Python library that computes source code maintainability metrics across
multiple languages. Reports raw line counts, Halstead volume, cyclomatic +
cognitive complexity, and structural metrics at file, class, and function
scope, then combines them into a 0–100 maintainability index.

## Installation

```bash
pip install maintainability-analyzer
```

Or from source:

```bash
pip install git+https://github.com/OptimizelyPrime/MainScoreCalc.git
```

## Usage

```python
from maintainability_analyzer import analyze

source_code = """
def hello():
    print("Hello, world!")
"""

metrics = analyze(source_code, language="python")
```

You can either specify `language` explicitly or pass a `filepath` and let the
language be inferred from the file extension:

```python
metrics = analyze(open("main.cpp").read(), filepath="main.cpp")
```

## Output

`analyze()` returns a dict with this shape:

```python
{
    "language": "python",
    "file": {
        "raw": {
            "loc": 12, "sloc": 10, "lloc": 8,
            "comments": 1, "multi": 0, "blank": 2,
            "comment_ratio": 0.1,
        },
        "halstead": {"volume": 38.0},
        "complexity": {"cyclomatic": 5, "cognitive": 4},
        "structural": {"max_nesting_depth": 2, "statement_count": 8},
        "maintainability_index": 71.2,
    },
    "classes": {
        "Calculator": {
            "raw": {...}, "halstead": {...}, "complexity": {...},
            "structural": {...}, "maintainability_index": 68.4,
            "methods": ["add", "factorial"],
        },
    },
    "functions": {
        "factorial": {
            "raw": {...}, "halstead": {...}, "complexity": {...},
            "structural": {
                "max_nesting_depth": 1, "statement_count": 3,
                "parameter_count": 2, "return_count": 2,
            },
            "maintainability_index": 82.6,
        },
    },
}
```

### Metric families

- **Raw** — physical / source / logical line counts, comments, multi-line
  string or block-comment lines, blank lines, and a derived comment ratio.
- **Halstead** — Halstead volume (the base for the maintainability index
  formula).
- **Complexity** — cyclomatic complexity (decision points + 1) and Sonar-style
  cognitive complexity (nesting-weighted, with +1 for direct recursion). Both
  feed into the maintainability index: `MI = 171 - 5.2·ln(V) - 0.23·cyclomatic
  - 0.15·cognitive - 16.2·ln(LOC)`, clamped and normalized to 0–100.
- **Structural** — per-function: parameter count, explicit `return` count,
  maximum nesting depth, and statement count. Aggregated to max / sum at
  class and file scope.

## Errors

`analyze()` raises subclasses of `AnalyzerError` on failure. Each is also a
subclass of a stdlib exception so existing `except ValueError:` / `except
ImportError:` handlers keep working.

| Exception | When |
|-----------|------|
| `UnsupportedLanguageError` (`ValueError`) | `language` is not one of the supported names, or `filepath` has an extension we don't recognize, or neither argument was provided. Message lists the valid options. |
| `ParseError` (`ValueError`) | The source code is syntactically invalid. Carries `language`, `line`, and `column` attributes. C/C++ and C# no longer silently return garbage metrics — malformed input raises this. |
| `BackendUnavailableError` (`ImportError`) | The optional parser package for the requested language isn't installed. Message includes a `pip install` hint. Importing `maintainability_analyzer` itself does not require every backend. |
| `TypeError` | `source_code` isn't a `str` (e.g. `bytes` was passed). |

All four are importable from the top-level package:

```python
from maintainability_analyzer import (
    analyze, AnalyzerError, ParseError,
    UnsupportedLanguageError, BackendUnavailableError,
)
```

## Supported Languages

| Language | Extension(s)    | Parser backend         |
|----------|-----------------|------------------------|
| Python   | `.py`           | stdlib `ast`           |
| Java     | `.java`         | `javalang`             |
| C        | `.c`, `.h`      | `libclang`             |
| C++      | `.cpp`, `.hpp`  | `libclang`             |
| C#       | `.cs`           | `tree-sitter-c-sharp`  |

## License

See `LICENSE.txt` (if present) or the project's GitHub page.
