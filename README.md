# Maintainability Analyzer

A command-line tool to analyze source code files and calculate maintainability metrics.

```

## Usage

## Using as an Importable Module

You can use `maintainability-analyzer` as a Python library in your own code after installing it:

```python
# Import the analyze function from the installed package
from maintainability_analyzer.core import analyze

# Example 1: Analyze Python code by specifying the language
source_code = """

```bash
maintainability-analyzer path/to/your/code.c -l c
metrics = analyze(source_code, language='python')
print(metrics)

# Example 2: Analyze code and let the tool guess the language from the file extension
source_code = "int main() { return 0; }"
metrics = analyze(source_code, filepath='main.cpp')
print(metrics)
```

The `analyze` function returns a dictionary with the calculated metrics. You can specify the language directly or let the tool infer it from the file extension using the `filepath` argument.
```

If the language is not provided, the tool will try to guess it based on the file extension.

## Library Usage

You can also use `maintainability-analyzer` as a library in your Python code.

First, import the `analyze` function:

```python
from maintainability_analyzer import analyze
```

Then, call the function with your source code. You can either specify the language explicitly, or provide a filepath to let the tool guess the language from the file extension.

**Example 1: Specifying the language**
```python
source_code = """
def hello_world():
    print("Hello, World!")
"""

metrics = analyze(source_code, language='python')
print(metrics)
```

**Example 2: Guessing the language from the filepath**
```python
source_code = "int main() { return 0; }"

metrics = analyze(source_code, filepath='main.cpp')
print(metrics)
```

## Supported Languages

The following languages and file extensions are supported:

*   Python (`.py`)
*   C++ (`.cpp`, `.hpp`)
*   C (`.c`, `.h`)
*   Java (`.java`)
*   C# (`.cs`)
