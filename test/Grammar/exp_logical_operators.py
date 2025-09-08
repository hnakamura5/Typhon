from ..assertion_utils import assert_ast_equals, show_token


and_code = """
let a = True && False;
"""
and_result = """
a = True and False
"""


def test_and():
    show_token(and_code)
    assert_ast_equals(and_code, and_result)


or_code = """
let a = True || False;
"""
or_result = """
a = True or False
"""


def test_or():
    assert_ast_equals(or_code, or_result)


not_code = """
let a = !True;
"""
not_result = """
a = not True
"""


def test_not():
    assert_ast_equals(not_code, not_result)


is_code = """
let a = x is y;
"""
is_result = """
a = x is y
"""


def test_is():
    assert_ast_equals(is_code, is_result)


is_not_code = """
let a = x is not y;
"""
is_not_result = """
a = x is not y
"""


def test_is_not():
    assert_ast_equals(is_not_code, is_not_result)


in_code = """
let a = x in y;
"""
in_result = """
a = x in y
"""


def test_in():
    assert_ast_equals(in_code, in_result)


not_in_code = """
let a = x not in y;
"""
not_in_result = """
a = x not in y
"""


def test_not_in():
    assert_ast_equals(not_in_code, not_in_result)
