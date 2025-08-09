from .core import Metrics
from .parsers.python_parser import analyze_python_code
from .parsers.cpp_parser import analyze_cpp_code
from .parsers.java_parser import analyze_java_code
from .parsers.csharp_parser import analyze_csharp_code
from .utils import guess_language

def analyze(source_code, language=None, filepath=None):
    """
    Analyzes the given source code for maintainability metrics.
    :param source_code: The source code to analyze.
    :param language: The programming language of the source code.
                     If not provided, it will be guessed from the filepath.
    :param filepath: The path to the source code file. Used to guess the language if not provided.
    :return: A dictionary with the calculated metrics.
    """
    if language is None:
        if filepath is None:
            raise ValueError("Must provide either language or filepath.")
        language = guess_language(filepath)
        if language is None:
            raise ValueError(f"Could not guess language from file extension of {filepath}")

    per_function_cyclomatic = None
    if language == 'python':
        operators, operands, decision_points, per_function_cyclomatic = analyze_python_code(source_code)
    elif language in ['cpp', 'c']:
        operators, operands, decision_points, per_function_cyclomatic = analyze_cpp_code(source_code, lang=language)
    elif language == 'java':
        operators, operands, decision_points, per_function_cyclomatic = analyze_java_code(source_code)
    elif language == 'csharp':
        operators, operands, decision_points, per_function_cyclomatic = analyze_csharp_code(source_code)
    else:
        raise ValueError(f"Unsupported language: {language}")

    metrics = Metrics(source_code)
    result = metrics.analyze(operators, operands, decision_points)
    if per_function_cyclomatic is not None:
        result["cyclomatic_complexity_by_function"] = per_function_cyclomatic
    return result
