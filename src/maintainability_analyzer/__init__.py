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

    def _function_metrics(decision_points, operators, operands, line_counts):
        function_metrics = {}
        for func in decision_points:
            metrics = Metrics("")
            # Store only the count of lines for each function
            metrics.lines_of_code = line_counts.get(func, 0)
            metrics.calculate_halstead_volume(operators[func], operands[func])
            metrics.calculate_cyclomatic_complexity(decision_points[func] - 1)
            metrics.calculate_maintainability_index()
            function_metrics[func] = {
                "lines_of_code": metrics.lines_of_code,
                "halstead_volume": metrics.halstead_volume,
                "cyclomatic_complexity": metrics.cyclomatic_complexity,
                "maintainability_index": metrics.maintainability_index,
            }
        return function_metrics

    if language == 'python':
        _, _, _, function_decision_points, function_operators, function_operands, function_line_counts = analyze_python_code(source_code)
        return _function_metrics(function_decision_points, function_operators, function_operands, function_line_counts)
    elif language in ['cpp', 'c']:
        (
            _,
            _,
            _,
            function_decision_points,
            function_operators,
            function_operands,
            function_line_counts,
        ) = analyze_cpp_code(source_code, lang=language)
        return _function_metrics(function_decision_points, function_operators, function_operands, function_line_counts)
    elif language == 'java':
        (
            _,
            _,
            _,
            method_decision_points,
            method_operators,
            method_operands,
            method_line_counts,
        ) = analyze_java_code(source_code)
        return _function_metrics(method_decision_points, method_operators, method_operands, method_line_counts)
    elif language == 'csharp':
        (
            _,
            _,
            _,
            method_decision_points,
            method_operators,
            method_operands,
            method_line_counts,
        ) = analyze_csharp_code(source_code)
        return _function_metrics(method_decision_points, method_operators, method_operands, method_line_counts)
    else:
        raise ValueError(f"Unsupported language: {language}")
