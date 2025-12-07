from ..assertion_utils import (
    assert_ast_equals,
    assert_ast_type,
    assert_transform_equals,
    assert_typh_code_match_unparse,
)
import ast
from ....src.Typhon.Grammar.typhon_ast import is_var, is_let


code_with = """
with (let f = open(name)) {
    line = f.readline();
}
"""
result_with = """
with open(name) as f:
    line = f.readline()
"""


def test_stmt_with():
    parsed = assert_ast_equals(code_with, result_with)
    with_stmt = assert_ast_type(parsed.body[0], ast.With)
    assert len(with_stmt.items) == 1
    item = with_stmt.items[0]
    assert is_let(item)


code_with_var = """
with (var f = open(name)) {
    line = f.readline();
}
"""
result_with_var = """
with open(name) as f:
    line = f.readline()
"""


def test_stmt_with_var():
    parsed = assert_ast_equals(code_with_var, result_with_var)
    with_stmt = assert_ast_type(parsed.body[0], ast.With)
    assert len(with_stmt.items) == 1
    item = with_stmt.items[0]
    assert is_var(item)


code_with_multi_let = """
with (let f = open(name), g = open(name2)) {
    line = f.readline();
    line2 = g.readline();
}
"""
result_with_multi_let = """
with open(name) as f, open(name2) as g:
    line = f.readline()
    line2 = g.readline()
"""


def test_stmt_with_multi_let():
    parsed = assert_ast_equals(code_with_multi_let, result_with_multi_let)
    with_stmt = assert_ast_type(parsed.body[0], ast.With)
    assert len(with_stmt.items) == 2
    item1, item2 = with_stmt.items
    assert is_let(item1)
    assert is_let(item2)


code_async_with = """
async with (let f = open(name), g = open(name2)) {
    line = f.readline();
    line2 = g.readline();
    line3 = h.readline();
}
"""
result_async_with = """
async with open(name) as f, open(name2) as g:
    line = f.readline()
    line2 = g.readline()
    line3 = h.readline()
"""


def test_stmt_async_with():
    parsed = assert_ast_equals(code_async_with, result_async_with)
    with_stmt = assert_ast_type(parsed.body[0], ast.AsyncWith)
    assert len(with_stmt.items) == 2
    item1, item2 = with_stmt.items
    assert is_let(item1)
    assert is_let(item2)


code_inline_with = """
if (True) {
    with var f1 = open('file1.txt');
    let x = f1.readline();
    with let f2 = open('file2.txt');
    let y = f2.readline();
}
print('a')
"""
result_inline_with = """
if True:
    with open('file1.txt') as f1:
    x = f1.readline()
    with open('file2.txt') as f2:
    y = f2.readline()
print('a')
"""
result_inline_with_transformed = """
if True:
    with open('file1.txt') as _typh_vr_m0_0_f1:
        _typh_cn_m0_1_x = _typh_vr_m0_0_f1.readline()
        with open('file2.txt') as _typh_cn_m0_2_f2:
            _typh_cn_m0_3_y = _typh_cn_m0_2_f2.readline()
print('a')
"""


def test_stmt_inline_with():
    parsed = assert_ast_equals(code_inline_with, result_inline_with)
    assert_transform_equals(parsed, result_inline_with_transformed)
    assert_typh_code_match_unparse(code_inline_with)
