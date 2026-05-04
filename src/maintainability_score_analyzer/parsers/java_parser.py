"""Java parser.

Uses :mod:`javalang` to build the AST, then recursively walks each node's
children (via attribute introspection) with explicit scope + nesting tracking.
Produces a :class:`ParserResult` with class/interface/enum scopes at the class
level and method/constructor scopes at the function level.
"""

from __future__ import annotations

import javalang

from ..raw import CommentStyle, count_raw_lines, slice_lines
from .base import ParserResult, Scope


_DECISION_TYPES = (
    javalang.tree.IfStatement,
    javalang.tree.ForStatement,
    javalang.tree.WhileStatement,
    javalang.tree.DoStatement,
    javalang.tree.SwitchStatementCase,
    javalang.tree.CatchClause,
    javalang.tree.TernaryExpression,
)
_LOOP_TYPES = (
    javalang.tree.ForStatement,
    javalang.tree.WhileStatement,
    javalang.tree.DoStatement,
)
_CLASS_TYPES = (
    javalang.tree.ClassDeclaration,
    javalang.tree.InterfaceDeclaration,
    javalang.tree.EnumDeclaration,
)


def _iter_children(node):
    """Yield AST children of a javalang node.

    Skips tokens and leaf primitives. This mirrors the recursion used by the
    legacy parser's ``traverse`` but is explicit and re-entrant.
    """
    for attr_name in getattr(node, "attrs", ()):
        val = getattr(node, attr_name, None)
        if isinstance(val, list):
            for item in val:
                if isinstance(item, javalang.tree.Node):
                    yield item
        elif isinstance(val, javalang.tree.Node):
            yield val


class _Walker:
    def __init__(self, source: str):
        self.source = source
        self.file = Scope(name="<file>", kind="file")
        self.classes: dict[str, Scope] = {}
        self.functions: dict[str, Scope] = {}
        self._scope_stack: list[Scope] = [self.file]
        self._nesting: list[int] = [0]
        self._current_func_names: list[str] = []

    # -- helpers ---------------------------------------------------------

    def _add_operator(self, op):
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

    def _line_range(self, node):
        """Extract (start, end) line numbers from a javalang node if available."""
        start = getattr(node, "position", None)
        start_line = start.line if start else None
        return start_line, None

    def _find_end_line(self, start_line: int) -> int | None:
        """Find the closing brace of the block starting at start_line via brace matching."""
        lines = self.source.splitlines()
        depth = 0
        found_open = False
        for i, line in enumerate(lines[start_line - 1:], start=start_line):
            for ch in line:
                if ch == '{':
                    depth += 1
                    found_open = True
                elif ch == '}':
                    depth -= 1
                    if found_open and depth == 0:
                        return i
        return None

    def _scope_raw(self, scope: Scope):
        if scope.start_line and scope.end_line:
            sub = slice_lines(self.source, scope.start_line, scope.end_line)
            scope.raw = count_raw_lines(sub, CommentStyle.SLASH_STAR_SLASH_SLASH)

    # -- top-level -------------------------------------------------------

    def walk(self, tree):
        for child in _iter_children(tree):
            self._visit(child)

    def _visit(self, node):
        if isinstance(node, _CLASS_TYPES):
            self._visit_class(node)
            return
        if isinstance(node, (javalang.tree.MethodDeclaration,
                             javalang.tree.ConstructorDeclaration)):
            self._visit_method(node)
            return

        # Expressions / statements
        if isinstance(node, javalang.tree.BinaryOperation):
            self._add_operator(node.operator)
            # Boolean operators for cognitive complexity.
            if node.operator in ("&&", "||"):
                self._bump_cognitive(1)
                self._bump_cyclomatic(1)
        elif isinstance(node, javalang.tree.VariableDeclarator):
            self._add_operand(node.name)
        elif isinstance(node, javalang.tree.MethodInvocation):
            self._add_operand(node.member)
            if self._current_func_names and node.member == self._current_func_names[-1]:
                self._bump_cognitive(1)
        elif isinstance(node, javalang.tree.Literal):
            self._add_operand(node.value)
        elif isinstance(node, javalang.tree.MemberReference):
            self._add_operand(node.member)
        elif isinstance(node, javalang.tree.FormalParameter):
            self._add_operand(node.name)
        elif isinstance(node, javalang.tree.ReturnStatement):
            self._bump_statements()
            for s in reversed(self._scope_stack):
                if s.kind == "function":
                    s.return_count = (s.return_count or 0) + 1
                    break
        elif isinstance(node, javalang.tree.Statement):
            self._bump_statements()

        # Decision / flow
        if isinstance(node, _DECISION_TYPES):
            self._bump_cyclomatic(1)
            # Nested flow gets +1 + nesting cognitive weight.
            depth = self._nesting[-1]
            self._bump_cognitive(1 + depth)
            self._nesting[-1] += 1
            self._record_depth()
            try:
                for child in _iter_children(node):
                    self._visit(child)
            finally:
                self._nesting[-1] -= 1
            # Explicit else branch adds +1 cognitive.
            if isinstance(node, javalang.tree.IfStatement) and node.else_statement:
                self._bump_cognitive(1)
            return

        for child in _iter_children(node):
            self._visit(child)

    # -- scope enter/exit ------------------------------------------------

    def _visit_class(self, node):
        start, end = self._line_range(node)
        scope = Scope(name=node.name, kind="class", start_line=start, end_line=end)
        self.classes[node.name] = scope
        self._scope_stack.append(scope)
        self._nesting.append(0)
        try:
            for child in _iter_children(node):
                self._visit(child)
        finally:
            self._scope_stack.pop()
            self._nesting.pop()
            self._scope_raw(scope)

    def _visit_method(self, node):
        start, end = self._line_range(node)
        params = getattr(node, "parameters", None) or []
        scope = Scope(
            name=node.name,
            kind="function",
            start_line=start,
            end_line=end,
            parameter_count=len(params),
            return_count=0,
        )
        self.functions[node.name] = scope
        for enclosing in reversed(self._scope_stack):
            if enclosing.kind == "class":
                enclosing.method_names.append(node.name)
                break
        # Method name is an operand on the enclosing scopes (legacy behavior).
        self._add_operand(node.name)
        self._scope_stack.append(scope)
        self._nesting.append(0)
        self._current_func_names.append(node.name)
        try:
            for child in _iter_children(node):
                self._visit(child)
        finally:
            self._scope_stack.pop()
            self._nesting.pop()
            self._current_func_names.pop()
            if scope.start_line and scope.end_line is None:
                scope.end_line = self._find_end_line(scope.start_line)
            self._scope_raw(scope)


def parse_java(source_code: str) -> ParserResult:
    tree = javalang.parse.parse(source_code)
    w = _Walker(source_code)
    w.walk(tree)
    return ParserResult(
        language="java",
        file=w.file,
        classes=w.classes,
        functions=w.functions,
    )


def analyze_java_code(source_code):
    """Legacy 7-tuple interface kept for existing tests."""
    result = parse_java(source_code)
    file = result.file
    per_func_dp = {n: s.cyclomatic for n, s in result.functions.items()}
    per_func_ops = {n: list(s.operators) for n, s in result.functions.items()}
    per_func_opr = {n: list(s.operands) for n, s in result.functions.items()}
    per_func_lc = {n: (s.raw.loc if s.raw else 0) for n, s in result.functions.items()}
    total_dp = sum(per_func_dp.values()) if per_func_dp else file.cyclomatic
    return (
        list(file.operators),
        list(file.operands),
        total_dp,
        per_func_dp,
        per_func_ops,
        per_func_opr,
        per_func_lc,
    )
