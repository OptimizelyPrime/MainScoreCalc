import re



def analyze_csharp_code(source_code):
    """
    Analyzes C# source code to extract operators, operands, and decision points.
    Also returns cyclomatic complexity per method (best effort, regex-based).
    """
    # Remove comments to avoid counting them
    code = re.sub(r'//.*', '', source_code)
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)

    # Define regular expressions for C# elements
    operators_regex = r'--|\+\+|&&|\|\||==|!=|<=|>=|\+=|-=|\*=|/=|%=|&=|\|=|\^=|<<=|>>=|[+\-*/%&|^!~<>=?]'
    keywords = {'if', 'for', 'while', 'case', 'catch', 'using', 'class', 'static', 'void', 'else', 'int', 'string', 'bool'}
    keyword_pattern = '|'.join(keywords)
    operands_regex = r'\b(?!' + keyword_pattern + r'\b)[a-zA-Z_][a-zA-Z0-9_]*\b|\b\d+\.?\d*\b|\"(?:\\.|[^"\\])*\"'
    decision_points_regex = r'\b(if|for|while|case|catch)\b|\?'

    # Find all matches for overall metrics
    operators = re.findall(operators_regex, code)
    operands = re.findall(operands_regex, code)
    decision_points = re.findall(decision_points_regex, code)
    operands = [op for op in operands if op and op not in keywords]

    # Per-method metrics (best effort)
    method_regex = re.compile(r'(?:public|private|protected|internal|static|virtual|override|sealed|async|\s)*[\w<>\[\]]+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*\{', re.MULTILINE)
    method_iter = list(method_regex.finditer(code))
    cyclomatic_by_method = {}
    method_operators = {}
    method_operands = {}
    for idx, match in enumerate(method_iter):
        method_name = match.group(1)
        start = match.end()
        if idx + 1 < len(method_iter):
            end = method_iter[idx + 1].start()
        else:
            end = len(code)
        method_body = code[start:end]
        # Count decision points in method body
        method_decision_points = re.findall(decision_points_regex, method_body)
        cyclomatic_by_method[method_name] = len(method_decision_points) + 1
        # Operators and operands in method body
        method_operators[method_name] = re.findall(operators_regex, method_body)
        ops = re.findall(operands_regex, method_body)
        method_operands[method_name] = [op for op in ops if op and op not in keywords]

    total_decision_points = sum(cyclomatic_by_method.values()) if cyclomatic_by_method else len(decision_points)
    # Return per-method operators/operands/decision_points for function-level metrics
    return (
        operators,
        operands,
        total_decision_points,
        cyclomatic_by_method,
        method_operators,
        method_operands,
    )
