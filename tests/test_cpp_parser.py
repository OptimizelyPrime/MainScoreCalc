import unittest
from src.maintainability_analyzer.parsers.cpp_parser import analyze_cpp_code
class TestCPPParser(unittest.TestCase):
    def test_analyze_cpp_code(self):
        code = (
            "int factorial(int n) {\n"
            "    if (n == 0) {\n"
            "        return 1;\n"
            "    } else {\n"
            "        return n * factorial(n - 1);\n"
            "    }\n"
            "}\n"
        )
        (
            operators,
            operands,
            total_decision_points,
            function_decision_points,
            function_operators,
            function_operands,
            function_line_counts,
        ) = analyze_cpp_code(code, lang='cpp')

        print('DEBUG analyze_cpp_code:', operators, operands, total_decision_points, function_decision_points, function_operators, function_operands, function_line_counts)

        # Check per-function metrics only
        self.assertIn('factorial', function_decision_points)
        self.assertEqual(function_decision_points['factorial'], 2)
        self.assertIn('factorial', function_operators)
        self.assertIn('factorial', function_operands)
        self.assertIn('==', function_operators['factorial'])
        self.assertIn('*', function_operators['factorial'])
        self.assertIn('-', function_operators['factorial'])
        self.assertIn('factorial', function_operands['factorial'])
        self.assertIn('n', function_operands['factorial'])
        self.assertIn('factorial', function_line_counts)
        self.assertEqual(function_line_counts['factorial'], 7)

if __name__ == "__main__":
    unittest.main()
