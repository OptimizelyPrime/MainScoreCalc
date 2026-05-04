import esprima

def analyze_javascript_code(source_code):
    tree = esprima.parseScript(source_code, loc=True)
    parser = JavaScriptParser(source_code)
    parser.visit(tree)
    total_decision_points = (
        sum(parser.function_decision_points.values())
        if parser.function_decision_points
        else parser.decision_points
    )
    return (
        parser.operators,
        parser.operands,
        total_decision_points,
        parser.function_decision_points,
        parser.function_operators,
        parser.function_operands,
        parser.function_line_counts,
    )

class JavaScriptParser:
    def __init__(self, source_code):
        self.source_code = source_code
        self.operators = []
        self.operands = []
        self.decision_points = 0
        self.function_decision_points = {}
        self.function_operators = {}
        self.function_operands = {}
        self.function_line_counts = {}
        self.current_function = None

    def visit(self, node):
        if not node:
            return

        # Handle lists of nodes
        if isinstance(node, list):
            for item in node:
                self.visit(item)
            return

        # Ensure node is a valid esprima node
        if not isinstance(node, esprima.nodes.Node):
            return

        node_type = node.type
        method_name = f"visit_{node_type}"
        visitor = getattr(self, method_name, self.generic_visit)
        visitor(node)

    def generic_visit(self, node):
        for key, value in vars(node).items():
            if key != 'type' and value is not None:
                if isinstance(value, esprima.nodes.Node):
                    self.visit(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, esprima.nodes.Node):
                            self.visit(item)

    def visit_FunctionDeclaration(self, node):
        prev_function = self.current_function
        self.current_function = node.id.name

        prev_decision_points = self.decision_points
        prev_operators = self.operators
        prev_operands = self.operands
        self.decision_points = 0
        self.operators = []
        self.operands = []

        self.visit(node.body)

        self.function_decision_points[self.current_function] = self.decision_points + 1
        self.function_operators[self.current_function] = list(self.operators)
        self.function_operands[self.current_function] = list(self.operands)

        lines = node.loc.end.line - node.loc.start.line + 1
        self.function_line_counts[self.current_function] = lines

        self.decision_points = prev_decision_points
        self.operators = prev_operators
        self.operands = prev_operands
        self.current_function = prev_function

    def visit_ArrowFunctionExpression(self, node):
        # This is a simplified handler for arrow functions.
        # It doesn't set a function name, so it's treated as part of the enclosing scope.
        self.visit(node.body)

    def visit_IfStatement(self, node):
        self.decision_points += 1
        self.visit(node.test)
        self.visit(node.consequent)
        self.visit(node.alternate)

    def visit_ForStatement(self, node):
        self.decision_points += 1
        self.visit(node.init)
        self.visit(node.test)
        self.visit(node.update)
        self.visit(node.body)

    def visit_ForInStatement(self, node):
        self.decision_points += 1
        self.visit(node.left)
        self.visit(node.right)
        self.visit(node.body)

    def visit_ForOfStatement(self, node):
        self.decision_points += 1
        self.visit(node.left)
        self.visit(node.right)
        self.visit(node.body)

    def visit_WhileStatement(self, node):
        self.decision_points += 1
        self.visit(node.test)
        self.visit(node.body)

    def visit_DoWhileStatement(self, node):
        self.decision_points += 1
        self.visit(node.body)
        self.visit(node.test)

    def visit_SwitchStatement(self, node):
        self.decision_points += len(node.cases)
        self.visit(node.discriminant)
        for case in node.cases:
            self.visit(case)

    def visit_CatchClause(self, node):
        self.decision_points += 1
        self.visit(node.param)
        self.visit(node.body)

    def visit_ConditionalExpression(self, node):
        self.decision_points += 1
        self.visit(node.test)
        self.visit(node.consequent)
        self.visit(node.alternate)

    def visit_BinaryExpression(self, node):
        self.operators.append(node.operator)
        self.visit(node.left)
        self.visit(node.right)

    def visit_UnaryExpression(self, node):
        self.operators.append(node.operator)
        self.visit(node.argument)

    def visit_AssignmentExpression(self, node):
        self.operators.append(node.operator)
        self.visit(node.left)
        self.visit(node.right)

    def visit_UpdateExpression(self, node):
        self.operators.append(node.operator)
        self.visit(node.argument)

    def visit_LogicalExpression(self, node):
        self.operators.append(node.operator)
        self.visit(node.left)
        self.visit(node.right)

    def visit_Identifier(self, node):
        self.operands.append(node.name)

    def visit_Literal(self, node):
        self.operands.append(node.value)

    def visit_VariableDeclarator(self, node):
        if node.init:
            self.operators.append("=")
        self.visit(node.id)
        self.visit(node.init)

    def visit_CallExpression(self, node):
        self.operands.append(node.callee.name if hasattr(node.callee, 'name') else 'call')
        self.visit(node.arguments)
