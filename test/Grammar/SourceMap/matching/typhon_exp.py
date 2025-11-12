from ...assertion_utils import assert_code_match_unparse


code_exp_arithmetic = """
def left_func(x: int, y: int) -> int {
    return (x + y) * (x - y) // (x % y)
}
"""


def test_exp_arithmetic():
    assert_code_match_unparse(code_exp_arithmetic)


code_exp_list_comprehension = """
def left_func(n: int) -> list[int] {
    return [for (let x in range(n)) if (x % 2 == 0) yield x * 2]
}
"""


def test_exp_list_comprehension():
    assert_code_match_unparse(code_exp_list_comprehension)


code_exp_dict_comprehension = """
def left_func(n: int) -> dict[int, int] {
    return {for (let x in range(n)) if (x % 2 == 0) yield x: x * x}
}
"""


def test_exp_dict_comprehension():
    assert_code_match_unparse(code_exp_dict_comprehension)


code_exp_f_string = """
def left_func(name: str, age: int) -> str {
    return f"My name is {name} and I am {age} years old."
}
"""


def test_exp_f_string():
    assert_code_match_unparse(code_exp_f_string)


code_exp_nested_func_calls = """
def left_func(x: int) -> int {
    return max(min(x, 10), 0)
}
"""


def test_exp_nested_func_calls():
    assert_code_match_unparse(code_exp_nested_func_calls)


code_exp_pipe_placeholder = """
def left_func(x: [int]) -> int {
    return x |> filter(_ > 0, _) |> sum
}
"""


def test_exp_pipe_placeholder():
    assert_code_match_unparse(code_exp_pipe_placeholder)
