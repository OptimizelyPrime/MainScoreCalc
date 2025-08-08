import javalang

class JavaParser:
    def __init__(self):
        self.operators = []
        self.operands = []
        self.decision_points = 0
        self.visited_nodes = set()

    def traverse(self, node):
        if node in self.visited_nodes:
            return
        self.visited_nodes.add(node)

        if isinstance(node, javalang.tree.BinaryOperation):
            self.operators.append(node.operator)
        elif isinstance(node, javalang.tree.MethodDeclaration):
            self.operands.append(node.name)
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

        # The javalang tree is a bit awkward to traverse.
        # We need to check for attributes that are lists of nodes or single nodes.
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

    return parser.operators, parser.operands, parser.decision_points
