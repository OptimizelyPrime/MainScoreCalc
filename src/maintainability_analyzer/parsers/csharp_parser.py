"""C# parser backed by tree-sitter.

Replaces the legacy regex-only implementation. Uses the official
``tree-sitter-c-sharp`` grammar to build a concrete syntax tree, then walks it
with explicit scope + nesting tracking to produce a :class:`ParserResult`.
"""

from __future__ import annotations

from tree_sitter import Language, Parser
import tree_sitter_c_sharp as _tscs

from ..raw import CommentStyle, count_raw_lines, slice_lines
from .base import ParserResult, Scope


_LANGUAGE = Language(_tscs.language())
_PARSER = Parser(_LANGUAGE)


_CLASS_NODES = {
    "class_declaration",
    "struct_declaration",
    "interface_declaration",
    "enum_declaration",
    "record_declaration",
}
_FUNC_NODES = {
    "method_declaration",
    "constructor_declaration",
    "destructor_declaration",
    "local_function_statement",
    "operator_declaration",
    "conversion_operator_declaration",
}
_DECISION_NODES = {
    "if_statement",
    "for_statement",
    "for_each_statement",
    "while_statement",
    "do_statement",
    "switch_section",
    "case_switch_label",
    "catch_clause",
    "conditional_expression",  # ?: ternary
    "conditional_access_expression",  # ?.
}
_STATEMENT_NODES = {
    "local_declaration_statement",
    "expression_statement",
    "return_statement",
    "throw_statement",
    "yield_statement",
    "break_statement",
    "continue_statement",
}
_OPERATOR_SYMBOLS = {
    "+", "-", "*", "/", "%",
    "==", "!=", "<", ">", "<=", ">=",
    "&&", "||", "!",
    "&", "|", "^", "~",
    "=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=",
    "<<", ">>", "<<=", ">>=",
    "++", "--", "??", "?.",
}


class _Walker:
    def __init__(self, source: str):
        self.source = source
        self.source_bytes = source.encode("utf-8")
        self.file = Scope(name="<file>", kind="file")
        self.classes: dict[str, Scope] = {}
        self.functions: dict[str, Scope] = {}
        self._scope_stack: list[Scope] = [self.file]
        self._nesting: list[int] = [0]
        self._current_func_names: list[str] = []

    # -- helpers ---------------------------------------------------------

    def _text(self, node) -> str:
        return self.source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace")

    def _add_operator(self, op: str):
        for s in self._scope_stack:
            s.operators.append(op)

    def _add_operand(self, val):
        for s in self._scope_stack:
            s.operands.append(val)

    def _bump_cyclomatic(self, n: int = 1):
        for s in self._scope_stack:
            s.cyclomatic += n

    def _bump_cognitive(self, n: int):
        for s in self._scope_stack:
            s.cognitive += n

    def _bump_statements(self, n: int = 1):
        for s in self._scope_stack:
            s.statement_count += n

    def _record_depth(self):
        depth = self._nesting[-1]
        for s in self._scope_stack:
            if depth > s.max_nesting_depth:
                s.max_nesting_depth = depth

    def _scope_raw(self, scope: Scope):
        if scope.start_line and scope.end_line:
            sub = slice_lines(self.source, scope.start_line, scope.end_line)
            scope.raw = count_raw_lines(sub, CommentStyle.SLASH_STAR_SLASH_SLASH)

    def _named_child(self, node, field: str):
        """Return a named child field if present, else None."""
        return node.child_by_field_name(field)

    def _declared_name(self, node) -> str:
        name_node = self._named_child(node, "name")
        if name_node is not None:
            return self._text(name_node)
        # Fallback: first identifier child.
        for child in node.children:
            if child.type == "identifier":
                return self._text(child)
        return "<anonymous>"

    def _param_count(self, node) -> int:
        plist = self._named_child(node, "parameters")
        if plist is None:
            for child in node.children:
                if child.type == "parameter_list":
                    plist = child
                    break
        if plist is None:
            return 0
        return sum(1 for c in plist.children if c.type == "parameter")

    # -- traversal -------------------------------------------------------

    def walk(self, root):
        for child in root.children:
            self._visit(child)

    def _visit(self, node):
        t = node.type

        if t in _CLASS_NODES:
            self._visit_class(node)
            return
        if t in _FUNC_NODES:
            self._visit_function(node)
            return

        self._collect_tokens(node)

        if t in _STATEMENT_NODES:
            self._bump_statements()
            if t == "return_statement":
                for s in reversed(self._scope_stack):
                    if s.kind == "function":
                        s.return_count = (s.return_count or 0) + 1
                        break

        if t in _DECISION_NODES:
            self._bump_cyclomatic(1)
            depth = self._nesting[-1]
            self._bump_cognitive(1 + depth)
            self._nesting[-1] += 1
            self._record_depth()
            try:
                for child in node.children:
                    self._visit(child)
            finally:
                self._nesting[-1] -= 1
            if t == "if_statement":
                # Detect else branch (child with type 'else').
                for child in node.children:
                    if child.type == "else":
                        self._bump_cognitive(1)
                        break
            return

        for child in node.children:
            self._visit(child)

    def _collect_tokens(self, node):
        """Pull Halstead operators/operands from leaf tokens at this node only."""
        t = node.type

        if t == "binary_expression":
            op = self._named_child(node, "operator")
            if op is not None:
                sym = self._text(op)
                if sym in _OPERATOR_SYMBOLS:
                    self._add_operator(sym)
                    if sym in ("&&", "||"):
                        self._bump_cognitive(1)
                        self._bump_cyclomatic(1)
        elif t in ("assignment_expression",):
            op = self._named_child(node, "operator")
            if op is not None:
                sym = self._text(op)
                if sym in _OPERATOR_SYMBOLS:
                    self._add_operator(sym)
        elif t in ("prefix_unary_expression", "postfix_unary_expression"):
            for child in node.children:
                if child.type in _OPERATOR_SYMBOLS:
                    self._add_operator(child.type)
                    break
        elif t == "variable_declarator":
            name = self._named_child(node, "name")
            if name is not None:
                self._add_operand(self._text(name))
            # Capture the `=` initializer token as a Halstead operator.
            for child in node.children:
                if child.type == "=":
                    self._add_operator("=")
                    break
        elif t == "identifier":
            # Only count as operand if not a keyword-role child (we filter by parent below).
            parent = node.parent
            if parent is None or parent.type not in _CLASS_NODES and parent.type not in _FUNC_NODES:
                # Skip method/class name identifiers — they are captured as scope names.
                if parent is None or self._named_child(parent, "name") is not node:
                    self._add_operand(self._text(node))
        elif t in ("integer_literal", "real_literal", "string_literal",
                   "character_literal", "boolean_literal", "null_literal"):
            self._add_operand(self._text(node))
        elif t == "invocation_expression":
            func = self._named_child(node, "function")
            if func is not None:
                name = self._text(func).rsplit(".", 1)[-1]
                if self._current_func_names and name == self._current_func_names[-1]:
                    self._bump_cognitive(1)

    # -- scopes ---------------------------------------------------------

    def _visit_class(self, node):
        name = self._declared_name(node)
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        scope = Scope(name=name, kind="class",
                      start_line=start_line, end_line=end_line)
        self.classes[name] = scope
        self._scope_stack.append(scope)
        self._nesting.append(0)
        try:
            body = self._named_child(node, "body")
            children = body.children if body is not None else node.children
            for child in children:
                self._visit(child)
        finally:
            self._scope_stack.pop()
            self._nesting.pop()
            self._scope_raw(scope)

    def _visit_function(self, node):
        name = self._declared_name(node)
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        scope = Scope(
            name=name,
            kind="function",
            start_line=start_line,
            end_line=end_line,
            parameter_count=self._param_count(node),
            return_count=0,
        )
        self.functions[name] = scope
        for enclosing in reversed(self._scope_stack):
            if enclosing.kind == "class":
                enclosing.method_names.append(name)
                break
        self._scope_stack.append(scope)
        self._nesting.append(0)
        self._current_func_names.append(name)
        try:
            body = self._named_child(node, "body")
            children = body.children if body is not None else node.children
            for child in children:
                self._visit(child)
        finally:
            self._scope_stack.pop()
            self._nesting.pop()
            self._current_func_names.pop()
            self._scope_raw(scope)


def parse_csharp(source_code: str) -> ParserResult:
    tree = _PARSER.parse(source_code.encode("utf-8"))
    w = _Walker(source_code)
    w.walk(tree.root_node)
    return ParserResult(
        language="csharp",
        file=w.file,
        classes=w.classes,
        functions=w.functions,
    )


def analyze_csharp_code(source_code):
    """Legacy 6-tuple interface kept for existing tests."""
    result = parse_csharp(source_code)
    file = result.file
    per_func_dp = {n: s.cyclomatic for n, s in result.functions.items()}
    per_func_ops = {n: list(s.operators) for n, s in result.functions.items()}
    per_func_opr = {n: list(s.operands) for n, s in result.functions.items()}
    total_dp = sum(per_func_dp.values()) if per_func_dp else file.cyclomatic
    return (
        list(file.operators),
        list(file.operands),
        total_dp,
        per_func_dp,
        per_func_ops,
        per_func_opr,
    )
