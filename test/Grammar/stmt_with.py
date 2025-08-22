from .assertion_utils import assert_ast_equals, assert_ast_type
import ast
from ...src.Grammar.typhon_ast import is_let, is_const


code_with = """
with (const f = open(name)) {
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
    assert is_const(item)


code_with_let = """
with (let f = open(name)) {
    line = f.readline();
}
"""
result_with_let = """
with open(name) as f:
    line = f.readline()
"""


def test_stmt_with_let():
    parsed = assert_ast_equals(code_with_let, result_with_let)
    with_stmt = assert_ast_type(parsed.body[0], ast.With)
    assert len(with_stmt.items) == 1
    item = with_stmt.items[0]
    assert is_let(item)


code_with_multi_const = """
with (const f = open(name), g = open(name2)) {
    line = f.readline();
    line2 = g.readline();
}
"""
result_with_multi_const = """
with open(name) as f, open(name2) as g:
    line = f.readline()
    line2 = g.readline()
"""


def test_stmt_with_multi_const():
    parsed = assert_ast_equals(code_with_multi_const, result_with_multi_const)
    with_stmt = assert_ast_type(parsed.body[0], ast.With)
    assert len(with_stmt.items) == 2
    item1, item2 = with_stmt.items
    assert is_const(item1)
    assert is_const(item2)


code_with_multi_decl = """
with (const f = open(name), g = open(name2); let h = open(name3)) {
    line = f.readline();
    line2 = g.readline();
    line3 = h.readline();
}
"""
result_with_multi_decl = """
with open(name) as f, open(name2) as g, open(name3) as h:
    line = f.readline()
    line2 = g.readline()
    line3 = h.readline()
"""


def test_stmt_with_multi_decl():
    parsed = assert_ast_equals(code_with_multi_decl, result_with_multi_decl)
    with_stmt = assert_ast_type(parsed.body[0], ast.With)
    assert len(with_stmt.items) == 3
    item1, item2, item3 = with_stmt.items
    assert is_const(item1)
    assert is_const(item2)
    assert is_let(item3)


code_async_with = """
async with (const f = open(name), g = open(name2); let h = open(name3)) {
    line = f.readline();
    line2 = g.readline();
    line3 = h.readline();
}
"""
result_async_with = """
async with open(name) as f, open(name2) as g, open(name3) as h:
    line = f.readline()
    line2 = g.readline()
    line3 = h.readline()
"""


def test_stmt_async_with():
    parsed = assert_ast_equals(code_async_with, result_async_with)
    with_stmt = assert_ast_type(parsed.body[0], ast.AsyncWith)
    assert len(with_stmt.items) == 3
    item1, item2, item3 = with_stmt.items
    assert is_const(item1)
    assert is_const(item2)
    assert is_let(item3)
