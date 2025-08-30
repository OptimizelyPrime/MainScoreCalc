# AGENTS.md

This document provides instructions for AI agents working with this repository.

## Project Overview

This project is a command-line tool that analyzes source code files to calculate maintainability metrics. It computes the Maintainability Index (MI) on a 0–100 scale using the standard formula that considers Halstead volume, cyclomatic complexity, and lines of code.

The tool supports multiple programming languages through a parser-based architecture. For each language, a dedicated parser extracts metrics, which are then used to calculate the final score.

## Getting Started

To get started, you need to install the project dependencies.

1.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## How to Run Tests

The project uses Python's built-in `unittest` framework for testing. To run the tests, use the following command:

```bash
python -m unittest discover -s tests
```

This command will automatically discover and run all tests in the `tests` directory.

## How to Add a New Language

To add support for a new language, follow these steps:

1.  **Create a new parser**:
    -   Create a new file in `src/maintainability_score_analyzer/parsers/` named `<language>_parser.py`.
    -   Implement a parser class that extracts the necessary metrics (operators, operands, and decision points). You can refer to the existing parsers (e.g., `python_parser.py`) for examples.

2.  **Integrate the parser**:
    -   In `src/maintainability_score_analyzer/__init__.py`, import your new parser.
    -   Add a new entry to the `LANGUAGE_PARSERS` dictionary to map the language name and file extensions to your parser.

3.  **Add tests**:
    -   Create a new test file in the `tests/` directory named `test_<language>_parser.py`.
    -   Add unit tests to verify that your parser correctly analyzes code for the new language.

## Code Style

This project follows the standard PEP 8 style guide for Python code. Please ensure your contributions adhere to these guidelines.

You can use a linter like `flake8` to check your code for compliance:
```bash
pip install flake8
flake8 src tests
```
