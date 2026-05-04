int factorial(int n) {
    if (n <= 0) {
        return 1;
    }
    return n * factorial(n - 1);
}

int sum_positive(int *values, int len) {
    int total = 0;
    for (int i = 0; i < len; i++) {
        if (values[i] > 0) {
            total += values[i];
        }
    }
    return total;
}

int main(void) {
    int vals[3] = {1, -2, 3};
    return sum_positive(vals, 3) + factorial(4);
}
