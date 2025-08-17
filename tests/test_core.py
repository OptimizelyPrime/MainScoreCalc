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

    def test_lines_of_code_penalty(self):
        operators = ['=']
        operands = ['1']

        small = Metrics('a=1\n' * 20)
        small.analyze(operators, operands, 0)

        medium = Metrics('a=1\n' * 40)
        medium.analyze(operators, operands, 0)

        large = Metrics('a=1\n' * 80)
        large.analyze(operators, operands, 0)

        self.assertGreater(small.maintainability_index, medium.maintainability_index)
        self.assertGreater(medium.maintainability_index, large.maintainability_index)

if __name__ == "__main__":
    unittest.main()
