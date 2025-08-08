import re

def analyze_csharp_code(source_code):
    """
    Analyzes C# source code to extract operators, operands, and decision points.
    This is a simplified parser and may not cover all C# syntax.
    """
    # Remove comments to avoid counting them
    source_code = re.sub(r'//.*', '', source_code)
    source_code = re.sub(r'/\*.*?\*/', '', source_code, flags=re.DOTALL)

    # Define regular expressions for C# elements
    operators_regex = r'--|\+\+|&&|\|\||==|!=|<=|>=|\+=|-=|\*=|/=|%=|&=|\|=|\^=|<<=|>>=|[+\-*/%&|^!~<>=?]'

    # More specific regex for identifiers, excluding keywords that are decision points
    keywords = {'if', 'for', 'while', 'case', 'catch', 'using', 'class', 'static', 'void', 'else', 'int', 'string', 'bool'}

    # Operands: identifiers, numbers, and strings
    keyword_pattern = '|'.join(keywords)
    operands_regex = r'\b(?!' + keyword_pattern + r'\b)[a-zA-Z_][a-zA-Z0-9_]*\b|\b\d+\.?\d*\b|\"(?:\\.|[^"\\])*\"'

    decision_points_regex = r'\b(if|for|while|case|catch)\b|\?'

    # Find all matches
    operators = re.findall(operators_regex, source_code)
    operands = re.findall(operands_regex, source_code)
    decision_points = re.findall(decision_points_regex, source_code)

    # Filter out keywords from operands
    operands = [op for op in operands if op and op not in keywords]

    return operators, operands, len(decision_points)
