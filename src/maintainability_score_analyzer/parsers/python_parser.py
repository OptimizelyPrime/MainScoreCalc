"""Python parser.

Walks the AST with :class:`ast.NodeVisitor` and produces a
:class:`ParserResult` with file / class / function scopes. Captures the four
metric families: raw, Halstead operators/operands, cyclomatic + cognitive
complexity, and structural (params, returns, depth, statements).
"""

from __future__ import annotations

import ast

from ..metrics import HalsteadMetrics
from ..raw import CommentStyle, count_raw_lines, slice_lines
from .base import ParserResult, Scope


_DECISION_NODES = (
    ast.If, ast.For, ast.While, ast.With, ast.Assert, ast.ExceptHandler,
    ast.AsyncFor, ast.AsyncWith, ast.IfExp,
)


class _Walker(ast.NodeVisitor):
    def __init__(self, source: str):
        self.source = source
        self.file = Scope(name="<file>", kind="file")
        self.classes: dict[str, Scope] = {}
        self.functions: dict[str, Scope] = {}

        # Stack of scopes currently being collected into. Each entry is a Scope.
        # All operators/operands/decision-points written go into every scope on
        # the stack (function + enclosing class + file).
        self._scope_stack: list[Scope] = [self.file]

        # Nesting depth for cognitive complexity and max_nesting_depth. Tracked
        # per-function: incremented when we enter a decision/loop/except body.
        self._nesting: list[int] = [0]

        # Function-name stack for recursion detection.
        self._current_func_names: list[str] = []

    # -- helpers ---------------------------------------------------------

    def _push_function(self, node):
        # Determine source span.
        start = getattr(node, "lineno", None)
        end = getattr(node, "end_lineno", None)
        scope = Scope(
            name=node.name,
            kind="function",
            start_line=start,
            end_line=end,
            parameter_count=_count_params(node),
            return_count=0,
        )
        self.functions[node.name] = scope
        # Record method membership on the enclosing class, if any.
        for enclosing in reversed(self._scope_stack):
            if enclosing.kind == "class":
                enclosing.method_names.append(node.name)
                break
        self._scope_stack.append(scope)
        self._nesting.append(0)
        self._current_func_names.append(node.name)

    def _pop_function(self):
        scope = self._scope_stack.pop()
        self._nesting.pop()
        self._current_func_names.pop()
        # Set scope's raw metrics from its source slice.
        if scope.start_line and scope.end_line:
            sub = slice_lines(self.source, scope.start_line, scope.end_line)
            scope.raw = count_raw_lines(sub, CommentStyle.PYTHON)

    def _push_class(self, node):
        start = getattr(node, "lineno", None)
        end = getattr(node, "end_lineno", None)
        scope = Scope(name=node.name, kind="class", start_line=start, end_line=end)
        self.classes[node.name] = scope
        self._scope_stack.append(scope)
        self._nesting.append(0)

    def _pop_class(self):
        scope = self._scope_stack.pop()
        self._nesting.pop()
        if scope.start_line and scope.end_line:
            sub = slice_lines(self.source, scope.start_line, scope.end_line)
            scope.raw = count_raw_lines(sub, CommentStyle.PYTHON)

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

    def _current_nesting(self) -> int:
        return self._nesting[-1] if self._nesting else 0

    def _bump_statements(self, n: int = 1):
        for s in self._scope_stack:
            s.statement_count += n

    def _record_depth(self):
        depth = self._current_nesting()
        for s in self._scope_stack:
            if depth > s.max_nesting_depth:
                s.max_nesting_depth = depth

    # -- visitors --------------------------------------------------------

    def visit_Module(self, node):
        for stmt in node.body:
            self.visit(stmt)

    def visit_ClassDef(self, node):
        self._push_class(node)
        try:
            for stmt in node.body:
                self.visit(stmt)
        finally:
            self._pop_class()

    def visit_FunctionDef(self, node):
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node):
        self._visit_function(node)

    def _visit_function(self, node):
        self._push_function(node)
        try:
            for stmt in node.body:
                self.visit(stmt)
        finally:
            self._pop_function()

    # Expression / statement tracking ------------------------------------

    def visit_BinOp(self, node):
        self._add_operator(type(node.op).__name__)
        self.generic_visit(node)

    def visit_UnaryOp(self, node):
        self._add_operator(type(node.op).__name__)
        self.generic_visit(node)

    def visit_Compare(self, node):
        for op in node.ops:
            self._add_operator(type(op).__name__)
        self.generic_visit(node)

    def visit_Assign(self, node):
        self._add_operator("=")
        self._bump_statements()
        self.generic_visit(node)

    def visit_AugAssign(self, node):
        self._add_operator(type(node.op).__name__)
        self._bump_statements()
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        self._add_operator("=")
        self._bump_statements()
        self.generic_visit(node)

    def visit_Return(self, node):
        self._bump_statements()
        # Bump return_count on the nearest enclosing function.
        for s in reversed(self._scope_stack):
            if s.kind == "function":
                s.return_count = (s.return_count or 0) + 1
                break
        self.generic_visit(node)

    def visit_Expr(self, node):
        self._bump_statements()
        self.generic_visit(node)

    def visit_Raise(self, node):
        self._bump_statements()
        self.generic_visit(node)

    def visit_Name(self, node):
        self._add_operand(node.id)

    def visit_Constant(self, node):
        self._add_operand(node.value)

    def visit_Call(self, node):
        # Direct recursion: self-call by name or self.<method>()/cls.<method>().
        if self._current_func_names:
            current = self._current_func_names[-1]
            func = node.func
            is_recursive = (
                isinstance(func, ast.Name) and func.id == current
            ) or (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id in ("self", "cls")
                and func.attr == current
            )
            if is_recursive:
                self._bump_cognitive(1)
        self.generic_visit(node)

    # Control flow --------------------------------------------------------

    def visit_If(self, node):
        self._flow_block(node, has_else=bool(node.orelse))

    def visit_For(self, node):
        self._flow_block(node)

    def visit_AsyncFor(self, node):
        self._flow_block(node)

    def visit_While(self, node):
        self._flow_block(node)

    def visit_With(self, node):
        # `with` is a decision point in the legacy parser; keep that behavior.
        self._flow_block(node, is_loop_or_cond=True, cognitive_weight=0)

    def visit_AsyncWith(self, node):
        self._flow_block(node, is_loop_or_cond=True, cognitive_weight=0)

    def visit_Assert(self, node):
        self._bump_cyclomatic()
        self._bump_statements()
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        self._flow_block(node)

    def visit_Try(self, node):
        self._bump_statements()
        for stmt in node.body:
            self.visit(stmt)
        for h in node.handlers:
            self.visit(h)
        for stmt in node.orelse:
            self.visit(stmt)
        for stmt in node.finalbody:
            self.visit(stmt)

    def visit_IfExp(self, node):
        # Ternary — +1 cyclomatic, +1 cognitive (no nesting bonus).
        self._bump_cyclomatic()
        self._bump_cognitive(1 + self._current_nesting())
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        # +1 per additional operator (chains of and/or).
        n_extra = max(0, len(node.values) - 1)
        self._bump_cyclomatic(n_extra)
        # Cognitive: +1 per sequence of homogeneous boolean ops.
        self._bump_cognitive(1)
        self.generic_visit(node)

    # Helper ----------------------------------------------------------------

    def _flow_block(self, node, has_else: bool = False,
                    is_loop_or_cond: bool = False, cognitive_weight: int = 1):
        self._bump_cyclomatic()
        self._bump_statements()
        depth = self._current_nesting()
        if cognitive_weight:
            # Sonar: +1 + nesting for nested flow.
            self._bump_cognitive(cognitive_weight + depth)
        if has_else:
            self._bump_cognitive(1)
        # Enter nested scope.
        self._nesting[-1] += 1
        self._record_depth()
        try:
            for child in _body_children(node):
                self.visit(child)
        finally:
            self._nesting[-1] -= 1


def _body_children(node):
    """Yield child nodes that form the body/else of a control-flow node."""
    for attr in ("test", "iter", "target"):
        if hasattr(node, attr):
            val = getattr(node, attr)
            if val is not None and isinstance(val, ast.AST):
                yield val
    for attr in ("body", "orelse", "handlers", "finalbody", "items"):
        if hasattr(node, attr):
            for item in getattr(node, attr) or []:
                if isinstance(item, ast.AST):
                    yield item
    for attr in ("type", "name", "msg"):
        if hasattr(node, attr):
            val = getattr(node, attr)
            if isinstance(val, ast.AST):
                yield val


def _count_params(node) -> int:
    args = node.args
    return (
        len(args.posonlyargs)
        + len(args.args)
        + len(args.kwonlyargs)
        + (1 if args.vararg else 0)
        + (1 if args.kwarg else 0)
    )


def parse_python(source_code: str) -> ParserResult:
    tree = ast.parse(source_code)
    w = _Walker(source_code)
    w.visit(tree)
    return ParserResult(
        language="python",
        file=w.file,
        classes=w.classes,
        functions=w.functions,
    )


def analyze_python_code(source_code):
    """Legacy 6-tuple interface retained for existing tests.

    New callers should use :func:`parse_python` which returns a
    :class:`ParserResult`.
    """
    result = parse_python(source_code)
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
