class Calculator {
public:
    Calculator() : total(0) {}

    int add(int a, int b) {
        int result = a + b;
        total += result;
        return result;
    }

    int factorial(int n) {
        if (n <= 0) return 1;
        return n * factorial(n - 1);
    }

    int sum_positive(int* values, int len) {
        int sum = 0;
        for (int i = 0; i < len; i++) {
            if (values[i] > 0) {
                sum += values[i];
            }
        }
        return sum;
    }

private:
    int total;
};
