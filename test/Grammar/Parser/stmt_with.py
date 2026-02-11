from ..assertion_utils import (
    assert_parse,
    assert_ast_type,
    assert_transform_ast,
    assert_typh_code_match_unparse,
    assert_parse_error_recovery,
    Range,
    Pos,
    with_parser_verbose,
)
import ast
from src.Typhon.Grammar.typhon_ast import is_var, is_let
from src.Typhon.Driver.debugging import set_debug_verbose


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
    parsed = assert_parse(code_with, result_with)
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
    parsed = assert_parse(code_with_var, result_with_var)
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
    parsed = assert_parse(code_with_multi_let, result_with_multi_let)
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
    parsed = assert_parse(code_async_with, result_async_with)
    with_stmt = assert_ast_type(parsed.body[0], ast.AsyncWith)
    assert len(with_stmt.items) == 2
    item1, item2 = with_stmt.items
    assert is_let(item1)
    assert is_let(item2)


code_inline_with = """
def func() {
    with var f1 = open('file1.txt');
    let x = f1.readline();
    with let f2 = open('file2.txt');
    let y = f2.readline();
}
print('a')
"""
result_inline_with = """
def func():
    with open('file1.txt') as f1:
    x = f1.readline()
    with open('file2.txt') as f2:
    y = f2.readline()
print('a')
"""
result_inline_with_transformed = """
from typing import Final as _typh_bi_Final

def func():
    with open('file1.txt') as f1:
        x: _typh_bi_Final = f1.readline()
        with open('file2.txt') as f2:
            f2: _typh_bi_Final
            y: _typh_bi_Final = f2.readline()
print('a')
"""


def test_stmt_inline_with():
    parsed = assert_parse(code_inline_with, result_inline_with)
    assert_transform_ast(parsed, result_inline_with_transformed)
    assert_typh_code_match_unparse(code_inline_with)


with_parenless_code = """
with let f = open(name) {
    line = f.readline();
}
"""
with_parenless_result = """
with open(name) as f:
    line = f.readline()
"""


def test_stmt_with_parenless_recovery():
    assert_parse_error_recovery(
        with_parenless_code,
        with_parenless_result,
        [
            ("expected '('", Range(Pos(1, 4), Pos(1, 5))),
            ("expected ')'", Range(Pos(1, 23), Pos(1, 24))),
        ],
    )


with_braceless_code = """
with (let f = open(name)) {
    line = f.readline();
"""
with_braceless_result = """
with open(name) as f:
    line = f.readline()
"""


def test_stmt_with_braceless_recovery():
    assert_parse_error_recovery(
        with_braceless_code,
        with_braceless_result,
        [
            ("expected '}'", Range(Pos(2, 23), Pos(2, 24))),
        ],
    )


with_braceless_both_code = """
with (let f = open(name)) line = f.readline();
"""
with_braceless_both_result = """
with open(name) as f:
    line = f.readline()
"""


def test_stmt_with_braceless_both():
    assert_parse_error_recovery(
        with_braceless_both_code,
        with_braceless_both_result,
        [
            ("expected '{'", Range(Pos(1, 26), Pos(1, 27))),
            ("expected '}'", Range(Pos(1, 45), Pos(1, 46))),
        ],
    )
