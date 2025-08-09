from clang import cindex


class CPPParser:
    def __init__(self):
        self.operators = []
        self.operands = []
        self.decision_points = 0
        self.function_decision_points = {}  # {function_name: decision_points}
        self.function_operators = {}  # {function_name: [operators]}
        self.function_operands = {}   # {function_name: [operands]}
        self.current_function = None

    def traverse(self, node):
        # Entering a function
        if node.kind in [cindex.CursorKind.FUNCTION_DECL, cindex.CursorKind.CXX_METHOD]:
            prev_function = self.current_function
            self.current_function = node.spelling
            prev_decision_points = self.decision_points
            prev_operators = self.operators
            prev_operands = self.operands
            self.decision_points = 0
            self.operators = []
            self.operands = []
            # Visit children (function body)
            for child in node.get_children():
                self.traverse(child)
            # Store result (+1 for function itself)
            self.function_decision_points[node.spelling] = self.decision_points + 1
            self.function_operators[node.spelling] = list(self.operators)
            self.function_operands[node.spelling] = list(self.operands)
            # Restore previous state
            self.decision_points = prev_decision_points
            self.operators = prev_operators
            self.operands = prev_operands
            self.current_function = prev_function
            return

        if node.kind in [cindex.CursorKind.BINARY_OPERATOR, cindex.CursorKind.UNARY_OPERATOR, cindex.CursorKind.COMPOUND_ASSIGNMENT_OPERATOR]:
            tokens = node.get_tokens()
            for token in tokens:
                if token.spelling in ['+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>=', '&&', '||', '!', '&', '|', '^', '=', '+=', '-=', '*=', '/=', '%=']:
                    self.operators.append(token.spelling)
                    break
        elif node.kind.is_declaration() or node.kind.is_reference():
            self.operands.append(node.spelling)
        elif node.kind in [cindex.CursorKind.INTEGER_LITERAL, cindex.CursorKind.FLOATING_LITERAL, cindex.CursorKind.IMAGINARY_LITERAL, cindex.CursorKind.STRING_LITERAL, cindex.CursorKind.CHARACTER_LITERAL]:
            self.operands.append(node.spelling)
        elif node.kind == cindex.CursorKind.CALL_EXPR:
            # Add the called function name to operands
            found = False
            for child in node.get_children():
                if child.kind == cindex.CursorKind.DECL_REF_EXPR:
                    if child.spelling:
                        self.operands.append(child.spelling)
                        found = True
            if not found:
                # Try to extract function name from tokens
                tokens = list(node.get_tokens())
                for i, token in enumerate(tokens):
                    # Look for identifier followed by '('
                    if token.kind.name == 'IDENTIFIER' and i + 1 < len(tokens) and tokens[i + 1].spelling == '(': 
                        self.operands.append(token.spelling)
                        break

        if node.kind in [cindex.CursorKind.IF_STMT, cindex.CursorKind.FOR_STMT, cindex.CursorKind.WHILE_STMT, cindex.CursorKind.DO_STMT, cindex.CursorKind.CASE_STMT, cindex.CursorKind.DEFAULT_STMT, cindex.CursorKind.CXX_FOR_RANGE_STMT, cindex.CursorKind.CXX_CATCH_STMT]:
            self.decision_points += 1

        for child in node.get_children():
            self.traverse(child)

def analyze_cpp_code(source_code, lang='cpp'):
    index = cindex.Index.create()
    unsaved_files = [('tmp.cpp' if lang == 'cpp' else 'tmp.c', source_code)]
    if lang == 'cpp':
        args = [
            '-std=c++11',
            '-I/usr/include/c++/13',
            '-I/usr/include/x86_64-linux-gnu/c++/13',
            '-I/usr/include/c++/13/backward',
            '-I/usr/lib/llvm-18/lib/clang/18/include',
            '-I/usr/local/include',
            '-I/usr/include/x86_64-linux-gnu',
            '-I/usr/include',
        ]
    else:
        args = []
    tu = index.parse('tmp.cpp' if lang == 'cpp' else 'tmp.c', args=args, unsaved_files=unsaved_files)

    if tu.diagnostics:
        for diag in tu.diagnostics:
            print(diag)

    parser = CPPParser()
    parser.traverse(tu.cursor)

    # For backward compatibility, also return total decision points
    total_decision_points = sum(parser.function_decision_points.values()) if parser.function_decision_points else parser.decision_points
    # Return per-function operators/operands/decision_points for function-level metrics
    return (
        parser.operators,
        parser.operands,
        total_decision_points,
        parser.function_decision_points,
        parser.function_operators,
        parser.function_operands,
    )
