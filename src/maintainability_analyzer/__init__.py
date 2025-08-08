from .core import Metrics
from .parsers.python_parser import analyze_python_code
from .parsers.cpp_parser import analyze_cpp_code
from .parsers.java_parser import analyze_java_code

def analyze(source_code, language):
    """
    Analyzes the given source code for maintainability metrics.

    :param source_code: The source code to analyze.
    :param language: The programming language of the source code.
                     Supported languages are 'python', 'cpp', 'c', 'java'.
    :return: A dictionary with the calculated metrics.
    """
    if language == 'python':
        operators, operands, decision_points = analyze_python_code(source_code)
    elif language in ['cpp', 'c']:
        operators, operands, decision_points = analyze_cpp_code(source_code, lang=language)
    elif language == 'java':
        operators, operands, decision_points = analyze_java_code(source_code)
    else:
        raise ValueError(f"Unsupported language: {language}")

    metrics = Metrics(source_code)
    return metrics.analyze(operators, operands, decision_points)
