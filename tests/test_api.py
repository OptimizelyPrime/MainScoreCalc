import unittest
from src.maintainability_analyzer import analyze

class TestApi(unittest.TestCase):
    def test_analyze_python(self):
        code = "def hello():\n    print('Hello, world!')"
        result = analyze(code, 'python')
        self.assertIsInstance(result, dict)
        self.assertTrue(any('maintainability_index' in v for v in result.values()))

    def test_analyze_cpp(self):
        code = "int main() { return 0; }"
        result = analyze(code, 'cpp')
        self.assertIsInstance(result, dict)
        self.assertTrue(any('maintainability_index' in v for v in result.values()))

    def test_analyze_c(self):
        code = "#include <stdio.h>\nint main() { printf(\"Hello, world!\\n\"); return 0; }"
        result = analyze(code, 'c')
        self.assertIsInstance(result, dict)
        self.assertTrue(any('maintainability_index' in v for v in result.values()))

    def test_analyze_java(self):
        code = "class HelloWorld { public static void main(String[] args) { System.out.println(\"Hello, world!\"); } }"
        result = analyze(code, 'java')
        self.assertIsInstance(result, dict)
        self.assertTrue(any('maintainability_index' in v for v in result.values()))

    def test_analyze_csharp(self):
        code = "namespace HelloWorld { class Hello { static void Main(string[] args) { System.Console.WriteLine(\"Hello, world!\"); } } }"
        result = analyze(code, 'csharp')
        self.assertIsInstance(result, dict)
        self.assertTrue(any('maintainability_index' in v for v in result.values()))

    def test_language_detection(self):
        code = "def hello():\n    print('Hello, world!')"
        result = analyze(code, filepath='test.py')
        self.assertIsInstance(result, dict)
        self.assertTrue(any('maintainability_index' in v for v in result.values()))

    def test_language_detection_unsupported(self):
        code = "echo 'Hello, world!'"
        with self.assertRaises(ValueError):
            analyze(code, filepath='test.sh')

    def test_language_detection_no_language_or_filepath(self):
        code = "def hello():\n    print('Hello, world!')"
        with self.assertRaises(ValueError):
            analyze(code)


if __name__ == "__main__":
    unittest.main()
