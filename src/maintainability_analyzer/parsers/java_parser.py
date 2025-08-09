import javalang


class JavaParser:
    def __init__(self):
        self.operators = []
        self.operands = []
        self.decision_points = 0
        self.visited_nodes = set()
        self.method_decision_points = {}  # {method_name: decision_points}
        self.method_operators = {}  # {method_name: [operators]}
        self.method_operands = {}   # {method_name: [operands]}
        self.current_method = None

    def traverse(self, node):
        if node in self.visited_nodes:
            return
        self.visited_nodes.add(node)

        if isinstance(node, javalang.tree.MethodDeclaration):
            self.operands.append(node.name)
            prev_method = self.current_method
            self.current_method = node.name
            prev_decision_points = self.decision_points
            prev_operators = self.operators
            prev_operands = self.operands
            self.decision_points = 0
            self.operators = []
            self.operands = []
            # Visit method body
            for attr_name in dir(node):
                if not attr_name.startswith('_'):
                    attr = getattr(node, attr_name)
                    if isinstance(attr, list):
                        for item in attr:
                            if isinstance(item, javalang.tokenizer.JavaToken):
                                continue
                            if isinstance(item, javalang.tree.Node):
                                self.traverse(item)
                    elif isinstance(attr, javalang.tree.Node):
                        self.traverse(attr)
            # Store result (+1 for method itself)
            self.method_decision_points[node.name] = self.decision_points + 1
            self.method_operators[node.name] = list(self.operators)
            self.method_operands[node.name] = list(self.operands)
            self.decision_points = prev_decision_points
            self.operators = prev_operators
            self.operands = prev_operands
            self.current_method = prev_method
            return

        if isinstance(node, javalang.tree.BinaryOperation):
            self.operators.append(node.operator)
        elif isinstance(node, javalang.tree.VariableDeclarator):
            self.operands.append(node.name)
        elif isinstance(node, javalang.tree.MethodInvocation):
            self.operands.append(node.member)
        elif isinstance(node, javalang.tree.Literal):
            self.operands.append(node.value)
        elif isinstance(node, javalang.tree.MemberReference):
            self.operands.append(node.member)
        elif isinstance(node, javalang.tree.FormalParameter):
            self.operands.append(node.name)

        if isinstance(node, (javalang.tree.IfStatement, javalang.tree.ForStatement, javalang.tree.WhileStatement, javalang.tree.DoStatement, javalang.tree.SwitchStatementCase, javalang.tree.CatchClause)):
            self.decision_points += 1

        # Traverse children for non-method nodes
        for attr_name in dir(node):
            if not attr_name.startswith('_'):
                attr = getattr(node, attr_name)
                if isinstance(attr, list):
                    for item in attr:
                        if isinstance(item, javalang.tokenizer.JavaToken):
                            continue
                        if isinstance(item, javalang.tree.Node):
                            self.traverse(item)
                elif isinstance(attr, javalang.tree.Node):
                    self.traverse(attr)


def analyze_java_code(source_code):
    tree = javalang.parse.parse(source_code)
    parser = JavaParser()
    parser.traverse(tree)
    total_decision_points = sum(parser.method_decision_points.values()) if parser.method_decision_points else parser.decision_points
    # Return per-method operators/operands/decision_points for function-level metrics
    return (
        parser.operators,
        parser.operands,
        total_decision_points,
        parser.method_decision_points,
        parser.method_operators,
        parser.method_operands,
    )
