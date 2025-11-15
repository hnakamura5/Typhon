from ..assertion_utils import (
    assert_ast_equals,
    assert_transform_equals,
    assert_typh_code_match_unparse,
)


comp_try_code = """
let val = (try 1/0 except (ZeroDivisionError as e) 0);
"""

comp_try_result = """
val = __try_comp
"""
comp_try_transformed = """
def _typh_cc_m0_0():
    try:
        return 1 / 0
    except ZeroDivisionError as e:
        return 0
val = _typh_cc_m0_0()
"""


def test_comp_try():
    parsed = assert_ast_equals(comp_try_code, comp_try_result)
    # No transformation is done for try comprehension
    assert_transform_equals(parsed, comp_try_transformed)
    assert_typh_code_match_unparse(comp_try_code)


comp_try_none_code = """
def f(x, y) {
    return (try x / y);
}
"""
comp_try_none_result = """
def f(x, y):
    return __try_comp
"""
comp_try_none_transformed = """
def f(x, y):

    def _typh_cc_f1_0():
        try:
            return x / y
        except:
            return None
    return _typh_cc_f1_0()
"""


def test_comp_try_none():
    parsed = assert_ast_equals(comp_try_none_code, comp_try_none_result)
    assert_transform_equals(parsed, comp_try_none_transformed)
    assert_typh_code_match_unparse(comp_try_none_code)


comp_try_many_code = """
def f(x, y) {
    return (try x / y
            except (ZeroDivisionError as e)
                0
            except (TypeError as e)
                -1
            except
                42)
}
"""
comp_try_many_result = """
def f(x, y):
    return __try_comp
"""
comp_try_many_transformed = """
def f(x, y):

    def _typh_cc_f1_0():
        try:
            return x / y
        except ZeroDivisionError as e:
            return 0
        except TypeError as e:
            return -1
        except:
            return 42
    return _typh_cc_f1_0()
"""


def test_comp_try_many():
    parsed = assert_ast_equals(comp_try_many_code, comp_try_many_result)
    assert_transform_equals(parsed, comp_try_many_transformed)
    assert_typh_code_match_unparse(comp_try_many_code)
