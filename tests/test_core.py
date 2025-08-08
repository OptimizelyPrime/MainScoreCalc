import unittest
from src.maintainability_analyzer.core import Metrics

class TestCore(unittest.TestCase):
    def test_calculate_maintainability_index(self):
        # These are example values, not from a real code snippet
        operators = ['=', '+', '*', 'if']
        operands = ['a', 'b', 'c', 'd', '1']
        decision_points = 1

        metrics = Metrics("a = b + c * d\nif a > 1:\n    pass")
        metrics.analyze(operators, operands, decision_points)

        # The exact value is not important here, just that it's a number between 0 and 100
        self.assertGreaterEqual(metrics.maintainability_index, 0)
        self.assertLessEqual(metrics.maintainability_index, 100)

if __name__ == "__main__":
    unittest.main()
