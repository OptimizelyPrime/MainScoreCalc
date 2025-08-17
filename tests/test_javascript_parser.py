import unittest
from src.maintainability_analyzer.parsers.javascript_parser import analyze_javascript_code

class TestJavaScriptParser(unittest.TestCase):
    def test_analyze_javascript_code(self):
        code = """
        function factorial(n) {
            if (n === 0) {
                return 1;
            } else {
                return n * factorial(n - 1);
            }
        }
        """
        (
            operators,
            operands,
            total_decision_points,
            function_decision_points,
            function_operators,
            function_operands,
            function_line_counts,
        ) = analyze_javascript_code(code)

        self.assertIn('factorial', function_decision_points)
        self.assertEqual(function_decision_points['factorial'], 2)
        self.assertIn('factorial', function_operators)
        self.assertIn('factorial', function_operands)
        self.assertIn('===', function_operators['factorial'])
        self.assertIn('-', function_operators['factorial'])
        self.assertIn('*', function_operators['factorial'])
        self.assertIn('factorial', function_operands['factorial'])
        self.assertIn('n', function_operands['factorial'])
        self.assertIn(0, function_operands['factorial'])
        self.assertIn(1, function_operands['factorial'])
        self.assertIn('factorial', function_line_counts)
        self.assertEqual(function_line_counts['factorial'], 7)

if __name__ == "__main__":
    unittest.main()
