from ..assertion_utils import (
    assert_ast_equals,
    assert_transform_equals,
    assert_typh_code_match_unparse,
)

code_with_comp = """
let result = (with (let f = open("file.txt")) f.read())
"""
code_with_comp_result = """
result = __with_control
"""
code_with_comp_transformed = """
def _typh_cc_m0_0():
    with open('file.txt') as f:
        return f.read()
result = _typh_cc_m0_0()
"""


def test_with_comp():
    parsed = assert_ast_equals(code_with_comp, code_with_comp_result)
    assert_transform_equals(parsed, code_with_comp_transformed)
    assert_typh_code_match_unparse(code_with_comp)


code_with_call_comp = """
def func(f: str -> str) {
    let name = "file.txt"
    let result = f(with (let file = open(name)) file.read())
    return result
}
"""
code_with_call_comp_result = """
def func(f: __arrow_type):
    name = 'file.txt'
    result = f(__with_control)
    return result
"""
code_with_call_comp_transformed = """
from typing import Protocol as _typh_bi_Protocol

class _typh_ar_f1_1(_typh_bi_Protocol):

    def __call__(self, _typh_ar_f1_1_a0: str, /) -> str:
        ...

def func(f: _typh_ar_f1_1):
    name = 'file.txt'

    def _typh_cc_f1_0():
        with open(name) as file:
            return file.read()
    result = f(_typh_cc_f1_0())
    return result
"""


def test_with_comp_in_call():
    parsed = assert_ast_equals(code_with_call_comp, code_with_call_comp_result)
    assert_transform_equals(parsed, code_with_call_comp_transformed)
    assert_typh_code_match_unparse(code_with_call_comp)
