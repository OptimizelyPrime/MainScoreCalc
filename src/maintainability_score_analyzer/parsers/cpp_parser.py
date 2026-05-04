"""C / C++ parser using libclang.

Walks cursors recursively with explicit scope + nesting tracking. Produces a
:class:`ParserResult` with class/struct scopes and function/method scopes.

The Linux-specific include paths from the legacy parser are kept inside
:func:`_clang_args` — they are only passed when running on Linux so Windows
users are not forced to have them resolve.
"""

from __future__ import annotations

import sys

from clang import cindex

from ..errors import ParseError
from ..raw import CommentStyle, count_raw_lines, slice_lines
from .base import ParserResult, Scope


_FUNC_KINDS = (
    cindex.CursorKind.FUNCTION_DECL,
    cindex.CursorKind.CXX_METHOD,
    cindex.CursorKind.CONSTRUCTOR,
    cindex.CursorKind.DESTRUCTOR,
    cindex.CursorKind.FUNCTION_TEMPLATE,
)
_CLASS_KINDS = (
    cindex.CursorKind.CLASS_DECL,
    cindex.CursorKind.STRUCT_DECL,
    cindex.CursorKind.CLASS_TEMPLATE,
)
_DECISION_KINDS = (
    cindex.CursorKind.IF_STMT,
    cindex.CursorKind.FOR_STMT,
    cindex.CursorKind.WHILE_STMT,
    cindex.CursorKind.DO_STMT,
    cindex.CursorKind.CASE_STMT,
    cindex.CursorKind.DEFAULT_STMT,
    cindex.CursorKind.CXX_FOR_RANGE_STMT,
    cindex.CursorKind.CXX_CATCH_STMT,
    cindex.CursorKind.CONDITIONAL_OPERATOR,
)
_OPERATOR_TOKENS = {
    "+", "-", "*", "/", "%",
    "==", "!=", "<", ">", "<=", ">=",
    "&&", "||", "!",
    "&", "|", "^", "~",
    "=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=",
    "<<", ">>", "<<=", ">>=",
    "++", "--",
}


def _clang_args(lang: str) -> list[str]:
    if lang == "cpp" and sys.platform.startswith("linux"):
        return [
            "-std=c++11",
            "-I/usr/include/c++/13",
            "-I/usr/include/x86_64-linux-gnu/c++/13",
            "-I/usr/include/c++/13/backward",
            "-I/usr/lib/llvm-18/lib/clang/18/include",
            "-I/usr/local/include",
            "-I/usr/include/x86_64-linux-gnu",
            "-I/usr/include",
        ]
    if lang == "cpp":
        return ["-std=c++11"]
    return []


class _Walker:
    def __init__(self, source: str):
        self.source = source
        self.file = Scope(name="<file>", kind="file")
        self.classes: dict[str, Scope] = {}
        self.functions: dict[str, Scope] = {}
        self._scope_stack: list[Scope] = [self.file]
        self._nesting: list[int] = [0]
        self._current_func_names: list[str] = []

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

    # -- main traversal --------------------------------------------------

    def walk(self, cursor):
        for child in cursor.get_children():
            self._visit(child)

    def _visit(self, cursor):
        kind = cursor.kind

        if kind in _FUNC_KINDS and cursor.is_definition():
            self._visit_function(cursor)
            return
        if kind in _CLASS_KINDS and cursor.is_definition():
            self._visit_class(cursor)
            return

        if kind in (cindex.CursorKind.BINARY_OPERATOR,
                    cindex.CursorKind.UNARY_OPERATOR,
                    cindex.CursorKind.COMPOUND_ASSIGNMENT_OPERATOR):
            for token in cursor.get_tokens():
                if token.spelling in _OPERATOR_TOKENS:
                    self._add_operator(token.spelling)
                    if token.spelling in ("&&", "||"):
                        self._bump_cognitive(1)
                        self._bump_cyclomatic(1)
                    break
        elif kind.is_declaration() or kind.is_reference():
            if cursor.spelling:
                self._add_operand(cursor.spelling)
        elif kind in (cindex.CursorKind.INTEGER_LITERAL,
                      cindex.CursorKind.FLOATING_LITERAL,
                      cindex.CursorKind.IMAGINARY_LITERAL,
                      cindex.CursorKind.STRING_LITERAL,
                      cindex.CursorKind.CHARACTER_LITERAL):
            if cursor.spelling:
                self._add_operand(cursor.spelling)
        elif kind == cindex.CursorKind.CALL_EXPR:
            target = cursor.spelling
            for ch in cursor.get_children():
                if ch.kind == cindex.CursorKind.DECL_REF_EXPR and ch.spelling:
                    target = ch.spelling
                    break
            if target:
                self._add_operand(target)
                if self._current_func_names and target == self._current_func_names[-1]:
                    self._bump_cognitive(1)

        if kind == cindex.CursorKind.RETURN_STMT:
            self._bump_statements()
            for s in reversed(self._scope_stack):
                if s.kind == "function":
                    s.return_count = (s.return_count or 0) + 1
                    break
        elif kind == cindex.CursorKind.DECL_STMT:
            self._bump_statements()

        if kind in _DECISION_KINDS:
            self._bump_cyclomatic(1)
            depth = self._nesting[-1]
            self._bump_cognitive(1 + depth)
            self._nesting[-1] += 1
            self._record_depth()
            try:
                for child in cursor.get_children():
                    self._visit(child)
            finally:
                self._nesting[-1] -= 1
            return

        for child in cursor.get_children():
            self._visit(child)

    def _visit_function(self, cursor):
        start_line = cursor.extent.start.line
        end_line = cursor.extent.end.line
        params = [c for c in cursor.get_children()
                  if c.kind == cindex.CursorKind.PARM_DECL]
        scope = Scope(
            name=cursor.spelling,
            kind="function",
            start_line=start_line,
            end_line=end_line,
            parameter_count=len(params),
            return_count=0,
        )
        self.functions[cursor.spelling] = scope
        for enclosing in reversed(self._scope_stack):
            if enclosing.kind == "class":
                enclosing.method_names.append(cursor.spelling)
                break
        self._scope_stack.append(scope)
        self._nesting.append(0)
        self._current_func_names.append(cursor.spelling)
        try:
            for child in cursor.get_children():
                self._visit(child)
        finally:
            self._scope_stack.pop()
            self._nesting.pop()
            self._current_func_names.pop()
            self._scope_raw(scope)

    def _visit_class(self, cursor):
        start_line = cursor.extent.start.line
        end_line = cursor.extent.end.line
        scope = Scope(
            name=cursor.spelling or "<anonymous>",
            kind="class",
            start_line=start_line,
            end_line=end_line,
        )
        self.classes[scope.name] = scope
        self._scope_stack.append(scope)
        self._nesting.append(0)
        try:
            for child in cursor.get_children():
                self._visit(child)
        finally:
            self._scope_stack.pop()
            self._nesting.pop()
            self._scope_raw(scope)

    def _scope_raw(self, scope: Scope):
        if scope.start_line and scope.end_line:
            sub = slice_lines(self.source, scope.start_line, scope.end_line)
            scope.raw = count_raw_lines(sub, CommentStyle.SLASH_STAR_SLASH_SLASH)


def parse_cpp(source_code: str, lang: str = "cpp") -> ParserResult:
    index = cindex.Index.create()
    filename = "tmp.cpp" if lang == "cpp" else "tmp.c"
    tu = index.parse(filename, args=_clang_args(lang),
                     unsaved_files=[(filename, source_code)])
    # Surface fatal / error diagnostics from the source itself. Warnings (e.g.
    # missing stdlib headers on Windows) are still tolerated — we care about
    # diagnostics whose file is the main TU, which rules out header-level
    # issues inside included files.
    errors = [
        d for d in tu.diagnostics
        if d.severity >= cindex.Diagnostic.Error
        and d.location.file is not None
        and d.location.file.name == filename
    ]
    if errors:
        first = errors[0]
        count = len(errors)
        prefix = f"{count} parse errors, first" if count > 1 else "parse error"
        raise ParseError(
            f"{lang}: {prefix} at line {first.location.line}, "
            f"column {first.location.column}: {first.spelling}",
            language=lang,
            line=first.location.line,
            column=first.location.column,
        )
    w = _Walker(source_code)
    # Only walk cursors from the main translation unit — otherwise stdlib
    # headers pulled in via #include pollute the results with hundreds of
    # internal function definitions.
    for child in tu.cursor.get_children():
        if child.location.file is None or child.location.file.name == filename:
            w._visit(child)
    return ParserResult(
        language=lang,
        file=w.file,
        classes=w.classes,
        functions=w.functions,
    )


def analyze_cpp_code(source_code, lang="cpp"):
    """Legacy 7-tuple interface kept for existing tests."""
    result = parse_cpp(source_code, lang=lang)
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
