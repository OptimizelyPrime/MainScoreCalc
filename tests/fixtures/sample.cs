using System;

namespace Sample
{
    public class Calculator
    {
        private int total;

        public Calculator()
        {
            total = 0;
        }

        public int Add(int a, int b)
        {
            int result = a + b;
            total += result;
            return result;
        }

        public int Factorial(int n)
        {
            if (n <= 0)
            {
                return 1;
            }
            return n * Factorial(n - 1);
        }

        public int SumPositive(int[] values)
        {
            int sum = 0;
            foreach (int v in values)
            {
                if (v > 0)
                {
                    sum += v;
                }
            }
            return sum;
        }
    }
}
