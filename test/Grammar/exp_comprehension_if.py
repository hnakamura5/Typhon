from ..assertion_utils import assert_ast_equals, assert_transform_equals


comp_if_code = """
let val = (if (True) 1 else 0)
"""
comp_if_result = """
val = 1 if True else 0
"""


def test_comp_if():
    assert_ast_equals(comp_if_code, comp_if_result)


comp_if_nested_code = """
let val = (if (True) 1 elif (False) (if (True) 2 else 3) else -1)
"""
comp_if_nested_result = """
val = 1 if True else (2 if True else 3) if False else -1
"""


def test_comp_if_nested():
    assert_ast_equals(comp_if_nested_code, comp_if_nested_result)


comp_if_then_only_code = """
let val = (if (True) 1)
"""
comp_if_then_only_result = """
val = 1 if True else None
"""


def test_comp_if_then_only():
    assert_ast_equals(comp_if_then_only_code, comp_if_then_only_result)
