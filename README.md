# Maintainability Analyzer

A command-line tool to analyze source code files and calculate maintainability metrics.

## Features

This tool calculates the following metrics for a given source code file:

*   **Lines of Code:** The total number of lines in the file.
*   **Halstead Volume:** A metric that measures the complexity of a program.
*   **Cyclomatic Complexity:** A software metric used to indicate the complexity of a program.
*   **Maintainability Index:** A single value index that indicates the overall maintainability of the code.

## Installation

You can install the `maintainability-analyzer` using pip:

```bash
pip install .
```

## Usage

To analyze a file, run the `maintainability-analyzer` command, followed by the path to the file:

```bash
maintainability-analyzer path/to/your/code.py
```

The tool will output a JSON object containing the calculated metrics.

### Specify Language

You can also specify the programming language using the `-l` or `--language` flag:

```bash
maintainability-analyzer path/to/your/code.c -l c
```

If the language is not provided, the tool will try to guess it based on the file extension.

## Library Usage

You can also use `maintainability-analyzer` as a library in your Python code.

First, import the `analyze` function:

```python
from maintainability_analyzer import analyze
```

Then, call the a function with your source code and the language:

```python
source_code = """
def hello_world():
    print("Hello, World!")
"""

metrics = analyze(source_code, 'python')
print(metrics)
```

## Supported Languages

The following languages and file extensions are supported:

*   Python (`.py`)
*   C++ (`.cpp`, `.hpp`)
*   C (`.c`, `.h`)
*   Java (`.java`)
*   C# (`.cs`)
