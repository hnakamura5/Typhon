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

def $anonymous1():
    with open('file.txt') as f:
        f: _typh_bi_Final
        return f.read()
result = $anonymous1()
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

class $func_type1(_typh_bi_Protocol):

    def __call__(self, $a0: str, /) -> str:
        ...

def func(f: $func_type1):
    name = 'file.txt'

    def $anonymous2():
        with open(name) as file:
            file: _typh_bi_Final
            return file.read()
    result = f($anonymous2())
    return result
"""


def test_with_comp_in_call():
    parsed = assert_parse(code_with_call_comp, code_with_call_comp_result)
    assert_transform_ast(parsed, code_with_call_comp_transformed)
    assert_typh_code_match_unparse(code_with_call_comp)
