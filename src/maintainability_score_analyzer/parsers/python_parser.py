import ast


class PythonParser(ast.NodeVisitor):
    def __init__(self, source_code):
        self.source_code = source_code
        self.operators = []
        self.operands = []
        self.decision_points = 0
        self.function_decision_points = {}  # {function_name: decision_points}
        self.function_operators = {}  # {function_name: [operators]}
        self.function_operands = {}   # {function_name: [operands]}
        # Track only the number of lines per function, not the lines themselves
        self.function_line_counts = {}  # {function_name: line_count}
        self.current_function = None

    def visit_BinOp(self, node):
        self.operators.append(type(node.op).__name__)
        self.visit(node.left)
        self.visit(node.right)
        return node

    def visit_Compare(self, node):
        for op in node.ops:
            self.operators.append(type(op).__name__)
        self.visit(node.left)
        for comparator in node.comparators:
            self.visit(comparator)
        return node

    def visit_Assign(self, node):
        self.operators.append("=")
        for target in node.targets:
            self.visit(target)
        self.visit(node.value)
        return node

    def visit_AugAssign(self, node):
        self.operators.append(type(node.op).__name__)
        self.visit(node.target)
        self.visit(node.value)
        return node

    def visit_Name(self, node):
        self.operands.append(node.id)
        return node

    def visit_Constant(self, node):
        self.operands.append(node.value)
        return node

    def visit_Num(self, node): # For older python versions
        self.operands.append(node.n)
        return node

    def visit_Str(self, node): # For older python versions
        self.operands.append(node.s)
        return node

    def visit_FunctionDef(self, node):
        prev_function = self.current_function
        self.current_function = node.name
        # Save previous state, start new for this function
        prev_decision_points = self.decision_points
        prev_operators = self.operators
        prev_operands = self.operands
        self.decision_points = 0
        self.operators = []
        self.operands = []
        # Visit function body
        for stmt in node.body:
            self.visit(stmt)
        # Store result
        self.function_decision_points[node.name] = self.decision_points + 1  # +1 for function itself
        self.function_operators[node.name] = list(self.operators)
        self.function_operands[node.name] = list(self.operands)
        # Calculate lines of code for the function
        if hasattr(node, "end_lineno") and node.end_lineno is not None:
            lines = node.end_lineno - node.lineno + 1
        else:
            segment = ast.get_source_segment(self.source_code, node) or ""
            lines = len(segment.splitlines())
        # Only store the count to avoid returning source code lines
        self.function_line_counts[node.name] = lines
        # Restore previous state
        self.decision_points = prev_decision_points
        self.operators = prev_operators
        self.operands = prev_operands
        self.current_function = prev_function
        return node

    def visit_If(self, node):
        self.decision_points += 1
        self.visit(node.test)
        for item in node.body:
            self.visit(item)
        for item in node.orelse:
            self.visit(item)
        return node

    def visit_For(self, node):
        self.decision_points += 1
        self.visit(node.target)
        self.visit(node.iter)
        for item in node.body:
            self.visit(item)
        for item in node.orelse:
            self.visit(item)
        return node

    def visit_While(self, node):
        self.decision_points += 1
        self.visit(node.test)
        for item in node.body:
            self.visit(item)
        for item in node.orelse:
            self.visit(item)
        return node

    def visit_With(self, node):
        self.decision_points += 1
        for item in node.items:
            self.visit(item)
        for item in node.body:
            self.visit(item)
        return node

    def visit_Assert(self, node):
        self.decision_points += 1
        self.visit(node.test)
        if node.msg:
            self.visit(node.msg)
        return node

    def visit_ExceptHandler(self, node):
        self.decision_points += 1
        if node.type:
            self.visit(node.type)
        if node.name:
            self.visit(node.name)
        for item in node.body:
            self.visit(item)
        return node

    def visit_BoolOp(self, node):
        self.decision_points += len(node.values) - 1
        for value in node.values:
            self.visit(value)
        return node

def analyze_python_code(source_code):
    tree = ast.parse(source_code)
    parser = PythonParser(source_code)
    parser.visit(tree)
    # For backward compatibility, also return total decision points
    total_decision_points = (
        sum(parser.function_decision_points.values())
        if parser.function_decision_points
        else parser.decision_points
    )
    # Return per-function operators/operands/decision_points for function-level metrics
    return (
        parser.operators,
        parser.operands,
        total_decision_points,
        parser.function_decision_points,
        parser.function_operators,
        parser.function_operands,
        parser.function_line_counts,
    )
