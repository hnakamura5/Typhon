from ..assertion_utils import assert_parse, assert_parse_first_error


tuple_code = """
x = (1, 2, 3);
"""
assign_result = """
x = (1, 2, 3)
"""


def test_exp_tuple():
    assert_parse(tuple_code, assign_result)


# Parentheses are necessary in Typhon.
tuple_error_code = """
x = 1, 2, 3;
"""


def test_exp_tuple_error():
    assert_parse_first_error(tuple_error_code)
