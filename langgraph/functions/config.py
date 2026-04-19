from functions.bash import run_bash
from functions.math import calculate_math_expression
from functions.web import search


def get_local_tools():
    return [
        run_bash,
        calculate_math_expression,
        search,
    ]
