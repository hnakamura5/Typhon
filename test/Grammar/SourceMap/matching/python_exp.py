from ...assertion_utils import assert_ast_match_unparse_code


def test_match_python_arithmetic():
    def left_func(x: int, y: int) -> int:
        return (x + y) * (x - y) // (x % y)

    assert_ast_match_unparse_code(left_func)


def test_match_list_comprehension():
    def left_func(n: int) -> list[int]:
        return [x * 2 for x in range(n) if x % 2 == 0]

    assert_ast_match_unparse_code(left_func)


def test_match_dict_comprehension():
    def left_func(n: int) -> dict[int, int]:
        return {x: x * x for x in range(n) if x % 2 != 0}

    assert_ast_match_unparse_code(left_func)


def test_match_f_string():
    def left_func(name: str, age: int) -> str:
        return f"My name is {name} and I am {age} years old."

    assert_ast_match_unparse_code(left_func)
