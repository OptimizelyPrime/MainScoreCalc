import unittest
from src.maintainability_analyzer.parsers.java_parser import analyze_java_code
class TestJavaParser(unittest.TestCase):
    def test_analyze_java_code(self):
        code = (
            "class Factorial {\n"
            "    public static int factorial(int n) {\n"
            "        if (n == 0) {\n"
            "            return 1;\n"
            "        } else {\n"
            "            return n * factorial(n - 1);\n"
            "        }\n"
            "    }\n"
            "}\n"
        )
        operators, operands, total_decision_points, method_decision_points, method_operators, method_operands = analyze_java_code(code)

        print('DEBUG analyze_java_code:', operators, operands, total_decision_points, method_decision_points, method_operators, method_operands)

        # Check per-method metrics only
        self.assertIn('factorial', method_decision_points)
        self.assertEqual(method_decision_points['factorial'], 2)
        self.assertIn('factorial', method_operators)
        self.assertIn('factorial', method_operands)
        self.assertIn('==', method_operators['factorial'])
        self.assertIn('*', method_operators['factorial'])
        self.assertIn('-', method_operators['factorial'])
        self.assertIn('factorial', method_operands['factorial'])
        self.assertIn('n', method_operands['factorial'])

if __name__ == "__main__":
    unittest.main()
