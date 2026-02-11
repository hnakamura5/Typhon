from ..assertion_utils import (
    assert_parse,
    assert_transform_ast,
    assert_typh_code_match_unparse,
)

code_with_comp = """
var result = (with (let f = open("file.txt")) f.read())
"""
code_with_comp_result = """
result = __with_control
"""
code_with_comp_transformed = """
from typing import Final as _typh_bi_Final

def _typh_cc_m0_0():
    with open('file.txt') as f:
        f: _typh_bi_Final
        return f.read()
result = _typh_cc_m0_0()
"""


def test_with_comp():
    parsed = assert_parse(code_with_comp, code_with_comp_result)
    assert_transform_ast(parsed, code_with_comp_transformed)
    assert_typh_code_match_unparse(code_with_comp)


code_with_call_comp = """
def func(f: str -> str) {
    var name = "file.txt"
    var result = f(with (let file = open(name)) file.read())
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
from typing import Final as _typh_bi_Final

class _typh_ar_f1_1(_typh_bi_Protocol):

    def __call__(self, _typh_ar_f1_1_a0: str, /) -> str:
        ...

def func(f: _typh_ar_f1_1):
    name = 'file.txt'

    def _typh_cc_f1_0():
        with open(name) as file:
            file: _typh_bi_Final
            return file.read()
    result = f(_typh_cc_f1_0())
    return result
"""


def test_with_comp_in_call():
    parsed = assert_parse(code_with_call_comp, code_with_call_comp_result)
    assert_transform_ast(parsed, code_with_call_comp_transformed)
    assert_typh_code_match_unparse(code_with_call_comp)
