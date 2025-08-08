import unittest
from src.maintainability_analyzer import analyze

class TestApi(unittest.TestCase):
    def test_analyze_python(self):
        code = "def hello():\n    print('Hello, world!')"
        result = analyze(code, 'python')
        self.assertIn('maintainability_index', result)

    def test_analyze_cpp(self):
        code = "#include <iostream>\nint main() { std::cout << \"Hello, world!\"; return 0; }"
        result = analyze(code, 'cpp')
        self.assertIn('maintainability_index', result)

    def test_analyze_c(self):
        code = "#include <stdio.h>\nint main() { printf(\"Hello, world!\\n\"); return 0; }"
        result = analyze(code, 'c')
        self.assertIn('maintainability_index', result)

    def test_analyze_java(self):
        code = "class HelloWorld { public static void main(String[] args) { System.out.println(\"Hello, world!\"); } }"
        result = analyze(code, 'java')
        self.assertIn('maintainability_index', result)

if __name__ == "__main__":
    unittest.main()
