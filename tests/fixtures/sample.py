"""Sample Python module for parity and fixture-based tests."""


class Calculator:
    """A basic calculator with history."""

    def __init__(self):
        self.history = []

    def add(self, a, b):
        result = a + b
        self.history.append(("add", a, b, result))
        return result

    def factorial(self, n):
        if n < 0:
            raise ValueError("negative")
        if n == 0:
            return 1
        return n * self.factorial(n - 1)

    def sum_positive(self, values):
        total = 0
        for v in values:
            if v > 0:
                total += v
            else:
                continue
        return total


def classify(score):
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    else:
        return "F"
