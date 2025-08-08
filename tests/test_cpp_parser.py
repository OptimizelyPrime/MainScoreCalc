import unittest
from src.maintainability_analyzer.parsers.cpp_parser import analyze_cpp_code

class TestCPPParser(unittest.TestCase):
    def test_analyze_cpp_code(self):
        code = """
int factorial(int n) {
    if (n == 0) {
        return 1;
    } else {
        return n * factorial(n - 1);
    }
}
"""
        operators, operands, decision_points = analyze_cpp_code(code, lang='cpp')

        self.assertIn("==", operators)
        self.assertIn("*", operators)
        self.assertIn("-", operators)
        self.assertIn("factorial", operands)
        self.assertIn("n", operands)
        self.assertEqual(decision_points, 1)

if __name__ == "__main__":
    unittest.main()
