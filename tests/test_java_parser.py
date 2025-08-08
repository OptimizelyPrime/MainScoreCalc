import unittest
from src.maintainability_analyzer.parsers.java_parser import analyze_java_code

class TestJavaParser(unittest.TestCase):
    def test_analyze_java_code(self):
        code = """
class Factorial {
    public static int factorial(int n) {
        if (n == 0) {
            return 1;
        } else {
            return n * factorial(n - 1);
        }
    }
}
"""
        operators, operands, decision_points = analyze_java_code(code)

        self.assertIn("==", operators)
        self.assertIn("*", operators)
        self.assertIn("-", operators)
        self.assertIn("factorial", operands)
        self.assertIn("n", operands)
        self.assertEqual(decision_points, 1)

if __name__ == "__main__":
    unittest.main()
