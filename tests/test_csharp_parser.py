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
        (
            operators,
            operands,
            total_decision_points,
            method_decision_points,
            method_operators,
            method_operands,
            method_line_counts,
        ) = analyze_csharp_code(source_code)

        print('DEBUG analyze_csharp_code:', operators, operands, total_decision_points, method_decision_points, method_operators, method_operands, method_line_counts)

        # Check per-method metrics only
        self.assertIn('Main', method_decision_points)
        self.assertEqual(method_decision_points['Main'], 3)  # 2 decision points + 1
        self.assertEqual(3, total_decision_points)
        self.assertIn('Main', method_operators)
        self.assertIn('Main', method_operands)
        for op in ['=', '>', '<', '++']:
            self.assertIn(op, method_operators['Main'])
        for operand in ['a', 'b', 'i', '10']:
            self.assertIn(operand, method_operands['Main'])
        self.assertIn('Main', method_line_counts)
        self.assertGreater(method_line_counts['Main'], 0)

if __name__ == "__main__":
    unittest.main()
