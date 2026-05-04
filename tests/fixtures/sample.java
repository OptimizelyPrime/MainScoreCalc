public class Calculator {
    private int total;

    public Calculator() {
        this.total = 0;
    }

    public int add(int a, int b) {
        int result = a + b;
        total += result;
        return result;
    }

    public int factorial(int n) {
        if (n <= 0) {
            return 1;
        }
        return n * factorial(n - 1);
    }

    public int sumPositive(int[] values) {
        int sum = 0;
        for (int v : values) {
            if (v > 0) {
                sum += v;
            }
        }
        return sum;
    }
}
