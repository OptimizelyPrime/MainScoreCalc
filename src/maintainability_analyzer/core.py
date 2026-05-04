"""Core re-exports.

The old ``core.Metrics`` class was a flat bag of numbers mutated by each parser.
It has been superseded by :class:`~maintainability_analyzer.metrics.ScopeMetrics`,
which composes the four metric families (raw / halstead / complexity /
structural) and computes the maintainability index from them.

This module exists so existing imports of ``core.ScopeMetrics`` etc. continue
to work.
"""

from .metrics import (
    ComplexityMetrics,
    HalsteadMetrics,
    RawMetrics,
    ScopeMetrics,
    StructuralMetrics,
)

__all__ = [
    "ComplexityMetrics",
    "HalsteadMetrics",
    "RawMetrics",
    "ScopeMetrics",
    "StructuralMetrics",
]
