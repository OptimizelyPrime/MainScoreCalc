import ast


class PythonParser(ast.NodeVisitor):
    def __init__(self):
        self.operators = []
        self.operands = []
        self.decision_points = 0
        self.function_decision_points = {}  # {function_name: decision_points}
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
        # Save previous count, start new for this function
        prev_decision_points = self.decision_points
        self.decision_points = 0
        # Visit function body
        for stmt in node.body:
            self.visit(stmt)
        # Store result
        self.function_decision_points[node.name] = self.decision_points + 1  # +1 for function itself
        # Restore previous state
        self.decision_points = prev_decision_points
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
    parser = PythonParser()
    parser.visit(tree)
    # For backward compatibility, also return total decision points
    total_decision_points = sum(parser.function_decision_points.values()) if parser.function_decision_points else parser.decision_points
    return parser.operators, parser.operands, total_decision_points, parser.function_decision_points
