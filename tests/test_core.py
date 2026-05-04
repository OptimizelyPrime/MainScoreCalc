import math
import unittest

from maintainability_analyzer import analyze
from maintainability_analyzer.metrics import (
    ComplexityMetrics,
    HalsteadMetrics,
    RawMetrics,
    ScopeMetrics,
    StructuralMetrics,
)


class TestScopeMetrics(unittest.TestCase):
    def test_empty_scope_is_fully_maintainable(self):
        s = ScopeMetrics()
        self.assertEqual(s.maintainability_index, 100.0)

    def test_maintainability_index_bounded(self):
        s = ScopeMetrics(
            raw=RawMetrics(loc=20, sloc=18, lloc=18, comments=0, multi=0, blank=2),
            halstead=HalsteadMetrics(
                operators=["=", "+", "*", "if"],
                operands=["a", "b", "c", "d", "1"],
            ),
            complexity=ComplexityMetrics(cyclomatic=2),
            structural=StructuralMetrics(),
        )
        mi = s.maintainability_index
        self.assertGreaterEqual(mi, 0)
        self.assertLessEqual(mi, 100)
        self.assertFalse(math.isnan(mi))


class TestAnalyzePythonShape(unittest.TestCase):
    def test_returns_new_nested_shape(self):
        src = "def foo():\n    return 1\n"
        result = analyze(src, language="python")
        self.assertEqual(result["language"], "python")
        self.assertIn("file", result)
        self.assertIn("classes", result)
        self.assertIn("functions", result)
        self.assertIn("foo", result["functions"])

        func = result["functions"]["foo"]
        for key in ("raw", "halstead", "complexity", "structural", "maintainability_index"):
            self.assertIn(key, func)

    def test_file_raw_counts_populated(self):
        src = "# hello\ndef foo():\n    return 1\n\n"
        raw = analyze(src, language="python")["file"]["raw"]
        self.assertEqual(raw["loc"], 4)
        self.assertEqual(raw["comments"], 1)
        self.assertEqual(raw["blank"], 1)
        self.assertGreater(raw["sloc"], 0)


if __name__ == "__main__":
    unittest.main()
