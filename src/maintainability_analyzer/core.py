import math

class Metrics:
    def __init__(self, source_code):
        self.source_code = source_code
        self.lines_of_code = 0
        self.halstead_volume = 0
        self.cyclomatic_complexity = 0
        self.maintainability_index = 0

    def calculate_lines_of_code(self):
        self.lines_of_code = len(self.source_code.splitlines())

    def calculate_halstead_volume(self, operators, operands):
        if not operators and not operands:
            self.halstead_volume = 0
            return

        num_unique_operators = len(set(operators))
        num_unique_operands = len(set(operands))
        num_total_operators = len(operators)
        num_total_operands = len(operands)

        vocabulary = num_unique_operators + num_unique_operands
        length = num_total_operators + num_total_operands

        if vocabulary == 0:
            self.halstead_volume = 0
        else:
            self.halstead_volume = length * math.log2(vocabulary)

    def calculate_cyclomatic_complexity(self, decision_points):
        self.cyclomatic_complexity = decision_points + 1

    def calculate_maintainability_index(self):
        if self.halstead_volume <= 0:
            # Avoid math domain error with log(0)
            # A Halstead Volume of 0 indicates no code, so maintainability is high.
            self.maintainability_index = 100
            return

        # Apply a piecewise penalty for lines of code
        if self.lines_of_code <= 20:
            loc_penalty = 0
        elif self.lines_of_code <= 100:
            weight = (self.lines_of_code - 20) / 80
            loc_penalty = 16.2 * weight * math.log(self.lines_of_code)
        else:
            # Maximum penalty reached at 100 lines
            loc_penalty = 16.2 * math.log(100)

        mi = 171 - 5.2 * math.log(self.halstead_volume) - 0.23 * self.cyclomatic_complexity - loc_penalty
        self.maintainability_index = max(0, mi * 100 / 171)

    def analyze(self, operators, operands, decision_points):
        self.calculate_lines_of_code()
        self.calculate_halstead_volume(operators, operands)
        self.calculate_cyclomatic_complexity(decision_points)
        self.calculate_maintainability_index()

        return {
            "lines_of_code": self.lines_of_code,
            "halstead_volume": self.halstead_volume,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "maintainability_index": self.maintainability_index,
        }
