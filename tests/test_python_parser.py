
import unittest
from src.maintainability_analyzer.parsers.python_parser import analyze_python_code

class TestPythonParser(unittest.TestCase):
    def test_analyze_python_code(self):
        code = (
            "def factorial(n):\n"
            "    if n == 0:\n"
            "        return 1\n"
            "    else:\n"
            "        return n * factorial(n - 1)\n"
        )
        (
            operators,
            operands,
            total_decision_points,
            function_decision_points,
            function_operators,
            function_operands,
            function_line_counts,
        ) = analyze_python_code(code)

        # Check per-function metrics only
        self.assertIn('factorial', function_decision_points)
        self.assertEqual(function_decision_points['factorial'], 2)
        self.assertIn('factorial', function_operators)
        self.assertIn('factorial', function_operands)
        self.assertIn('Eq', function_operators['factorial'])
        self.assertIn('Sub', function_operators['factorial'])
        self.assertIn('Mult', function_operators['factorial'])
        self.assertIn('factorial', function_operands['factorial'])
        self.assertIn('n', function_operands['factorial'])
        self.assertIn(0, function_operands['factorial'])
        self.assertIn(1, function_operands['factorial'])
        self.assertIn('factorial', function_line_counts)
        self.assertEqual(function_line_counts['factorial'], 5)

if __name__ == "__main__":
    unittest.main()
