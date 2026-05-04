"""Shared parser return types.

Every language parser returns a :class:`ParserResult` containing a file-level
:class:`Scope`, a dict of class-level :class:`Scope` objects, and a dict of
function/method-level :class:`Scope` objects.

A :class:`Scope` is the mutable working state a parser accumulates as it walks
the AST; it is later converted to :class:`ScopeMetrics` by
:func:`scope_to_metrics` for serialization.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..metrics import (
    ComplexityMetrics,
    HalsteadMetrics,
    RawMetrics,
    ScopeMetrics,
    StructuralMetrics,
)


@dataclass
class Scope:
    """Mutable working state for one scope as a parser walks the AST."""

    name: str = ""
    kind: str = "function"  # "file" | "class" | "function"
    start_line: int | None = None
    end_line: int | None = None

    operators: list = field(default_factory=list)
    operands: list = field(default_factory=list)

    cyclomatic: int = 1
    cognitive: int = 0

    max_nesting_depth: int = 0
    statement_count: int = 0
    parameter_count: int | None = None
    return_count: int | None = None

    # For class scopes: names of methods declared directly inside.
    method_names: list = field(default_factory=list)

    raw: RawMetrics | None = None


@dataclass
class ParserResult:
    language: str
    file: Scope
    classes: dict = field(default_factory=dict)    # {class_name: Scope}
    functions: dict = field(default_factory=dict)  # {func_name: Scope}


def scope_to_metrics(scope: Scope) -> ScopeMetrics:
    return ScopeMetrics(
        raw=scope.raw if scope.raw is not None else RawMetrics(),
        halstead=HalsteadMetrics(
            operators=list(scope.operators),
            operands=list(scope.operands),
        ),
        complexity=ComplexityMetrics(
            cyclomatic=scope.cyclomatic,
            cognitive=scope.cognitive,
        ),
        structural=StructuralMetrics(
            max_nesting_depth=scope.max_nesting_depth,
            statement_count=scope.statement_count,
            parameter_count=scope.parameter_count,
            return_count=scope.return_count,
        ),
    )
