"""Metric dataclasses for the maintainability analyzer.

These dataclasses are the shared currency between parsers and the public
``analyze`` API. Parsers populate a :class:`Scope` (see ``parsers.base``) and
then convert it into a :class:`ScopeMetrics` for serialization.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class RawMetrics:
    loc: int = 0
    sloc: int = 0
    lloc: int = 0
    comments: int = 0
    multi: int = 0
    blank: int = 0

    @property
    def comment_ratio(self) -> float:
        return (self.comments / self.sloc) if self.sloc else 0.0

    def to_dict(self) -> dict:
        return {
            "loc": self.loc,
            "sloc": self.sloc,
            "lloc": self.lloc,
            "comments": self.comments,
            "multi": self.multi,
            "blank": self.blank,
            "comment_ratio": self.comment_ratio,
        }


@dataclass
class HalsteadMetrics:
    operators: list = field(default_factory=list)
    operands: list = field(default_factory=list)

    @property
    def volume(self) -> float:
        if not self.operators and not self.operands:
            return 0.0
        vocabulary = len(set(self.operators)) + len(set(self.operands))
        length = len(self.operators) + len(self.operands)
        if vocabulary == 0:
            return 0.0
        return length * math.log2(vocabulary)

    def to_dict(self) -> dict:
        return {"volume": self.volume}


@dataclass
class ComplexityMetrics:
    cyclomatic: int = 1
    cognitive: int = 0

    def to_dict(self) -> dict:
        return {"cyclomatic": self.cyclomatic, "cognitive": self.cognitive}


@dataclass
class StructuralMetrics:
    max_nesting_depth: int = 0
    statement_count: int = 0
    parameter_count: int | None = None
    return_count: int | None = None

    def to_dict(self, include_function_only: bool = True) -> dict:
        out = {
            "max_nesting_depth": self.max_nesting_depth,
            "statement_count": self.statement_count,
        }
        if include_function_only:
            if self.parameter_count is not None:
                out["parameter_count"] = self.parameter_count
            if self.return_count is not None:
                out["return_count"] = self.return_count
        return out


@dataclass
class ScopeMetrics:
    """Combined metrics for one scope (file, class, or function)."""

    raw: RawMetrics = field(default_factory=RawMetrics)
    halstead: HalsteadMetrics = field(default_factory=HalsteadMetrics)
    complexity: ComplexityMetrics = field(default_factory=ComplexityMetrics)
    structural: StructuralMetrics = field(default_factory=StructuralMetrics)

    @property
    def maintainability_index(self) -> float:
        """Standard 171-based MI, normalized to 0-100."""
        volume = self.halstead.volume
        if volume <= 0:
            return 100.0
        loc = max(self.raw.loc, 1)
        mi = (
            171
            - 5.2 * math.log(volume)
            - 0.23 * self.complexity.cyclomatic
            - 16.2 * math.log(loc)
        )
        return max(0.0, mi * 100 / 171)

    def to_dict(self, is_function: bool = True) -> dict:
        return {
            "raw": self.raw.to_dict(),
            "halstead": self.halstead.to_dict(),
            "complexity": self.complexity.to_dict(),
            "structural": self.structural.to_dict(include_function_only=is_function),
            "maintainability_index": self.maintainability_index,
        }


def aggregate_halstead(parts: Iterable[HalsteadMetrics]) -> HalsteadMetrics:
    merged = HalsteadMetrics()
    for p in parts:
        merged.operators.extend(p.operators)
        merged.operands.extend(p.operands)
    return merged


def aggregate_complexity(parts: Iterable[ComplexityMetrics]) -> ComplexityMetrics:
    parts = list(parts)
    if not parts:
        return ComplexityMetrics(cyclomatic=1, cognitive=0)
    return ComplexityMetrics(
        cyclomatic=sum(p.cyclomatic for p in parts),
        cognitive=sum(p.cognitive for p in parts),
    )


def aggregate_structural(parts: Iterable[StructuralMetrics]) -> StructuralMetrics:
    parts = list(parts)
    if not parts:
        return StructuralMetrics()
    return StructuralMetrics(
        max_nesting_depth=max(p.max_nesting_depth for p in parts),
        statement_count=sum(p.statement_count for p in parts),
    )
