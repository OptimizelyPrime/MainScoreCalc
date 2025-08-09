import unittest
import sys
import os

# Add src to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from maintainability_analyzer.parsers.csharp_parser import analyze_csharp_code

class TestCSharpParser(unittest.TestCase):
    def test_analyze_csharp_code(self):
        source_code = """
using System;

class Program
{
    static void Main()
    {
        int a = 10;
        int b = 20;
        if (a > b)
        {
            Console.WriteLine("a is greater than b");
        }
        else
        {
            Console.WriteLine("b is greater than or equal to a");
        }
        for (int i = 0; i < 10; i++)
        {
            a++;
        }
    }
}
"""
        operators, operands, decision_points, cyclomatic_by_func = analyze_csharp_code(source_code)

        expected_operators = ['=', '=', '>', '=', '<', '++', '++']
        expected_operands = [
            'System', 'Program', 'Main', 'a', '10', 'b', '20', 'a', 'b',
            'Console', 'WriteLine', '"a is greater than b"', 'Console', 'WriteLine',
            '"b is greater than or equal to a"', 'i', '0', 'i', '10', 'i', 'a'
        ]

        # Sort for comparison, as order doesn't matter for Halstead metrics
        self.assertCountEqual(expected_operators, operators)
        self.assertCountEqual(expected_operands, operands)
        self.assertIn('Main', cyclomatic_by_func)
        self.assertEqual(cyclomatic_by_func['Main'], 3)  # 2 decision points + 1
        self.assertEqual(3, decision_points)

if __name__ == "__main__":
    unittest.main()
