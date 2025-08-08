from clang import cindex

# You might need to set this to the location of libclang.so if it's not in your system's path
# cindex.Config.set_library_file('/usr/lib/x86_64-linux-gnu/libclang-18.so.1')

class CPPParser:
    def __init__(self):
        self.operators = []
        self.operands = []
        self.decision_points = 0

    def traverse(self, node):
        if node.kind in [cindex.CursorKind.BINARY_OPERATOR, cindex.CursorKind.UNARY_OPERATOR, cindex.CursorKind.COMPOUND_ASSIGNMENT_OPERATOR]:
            # To get the actual operator, we can look at the tokens
            tokens = node.get_tokens()
            for token in tokens:
                if token.spelling in ['+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>=', '&&', '||', '!', '&', '|', '^', '=', '+=', '-=', '*=', '/=', '%=']:
                    self.operators.append(token.spelling)
                    break # Only take the first operator token we find
        elif node.kind.is_declaration() or node.kind.is_reference():
            self.operands.append(node.spelling)
        elif node.kind in [cindex.CursorKind.INTEGER_LITERAL, cindex.CursorKind.FLOATING_LITERAL, cindex.CursorKind.IMAGINARY_LITERAL, cindex.CursorKind.STRING_LITERAL, cindex.CursorKind.CHARACTER_LITERAL]:
            self.operands.append(node.spelling)

        if node.kind in [cindex.CursorKind.IF_STMT, cindex.CursorKind.FOR_STMT, cindex.CursorKind.WHILE_STMT, cindex.CursorKind.DO_STMT, cindex.CursorKind.CASE_STMT, cindex.CursorKind.DEFAULT_STMT, cindex.CursorKind.CXX_FOR_RANGE_STMT, cindex.CursorKind.CXX_CATCH_STMT]:
            self.decision_points += 1

        for child in node.get_children():
            self.traverse(child)

def analyze_cpp_code(source_code, lang='cpp'):
    index = cindex.Index.create()
    unsaved_files = [('tmp.cpp' if lang == 'cpp' else 'tmp.c', source_code)]
    tu = index.parse('tmp.cpp' if lang == 'cpp' else 'tmp.c', unsaved_files=unsaved_files)

    parser = CPPParser()
    parser.traverse(tu.cursor)

    return parser.operators, parser.operands, parser.decision_points
