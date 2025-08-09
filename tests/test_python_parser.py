import unittest
from src.maintainability_analyzer.parsers.python_parser import analyze_python_code

class TestPythonParser(unittest.TestCase):
    def test_analyze_python_code(self):
        code = """
def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n - 1)
"""
        operators, operands, decision_points, cyclomatic_by_func = analyze_python_code(code)

        # This is a simplified check. A more thorough test would be needed for a real-world scenario.
        self.assertIn("Eq", operators)
        self.assertIn("Sub", operators)
        self.assertIn("Mult", operators)
        self.assertIn("factorial", operands)
        self.assertIn("n", operands)
        self.assertIn(0, operands)
        self.assertIn(1, operands)
        self.assertEqual(decision_points, 2)  # 1 function, 1 decision point, so 2
        self.assertIn('factorial', cyclomatic_by_func)
        self.assertEqual(cyclomatic_by_func['factorial'], 2)

if __name__ == "__main__":
    unittest.main()
