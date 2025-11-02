from ..assertion_utils import (
    show_token,
    assert_ast_equals,
    TokenizerAsserter,
    assert_ast_transform,
)
from ....src.Typhon.Grammar.typhon_ast import OPTIONAL_QUESTION, FORCE_UNWRAP
from tokenize import NAME, OP, NEWLINE, ENDMARKER

code_postfix_op = """
let a: int? = None;
"""
# In AST, postfix `?` is represented as a tuple type with one element.
result_postfix_op = """
a: (int,) = None
"""
transformed_postfix_op = """
a: int | None = None
"""


def test_postfix_op():
    show_token(code_postfix_op)
    ta = TokenizerAsserter(code_postfix_op)
    ta.next(NAME, "let")
    ta.next(NAME, "a")
    ta.next(OP, ":")
    ta.next(NAME, "int")
    ta.next(NAME, OPTIONAL_QUESTION)
    ta.next(OP, "=")
    ta.next(NAME, "None")
    ta.next(OP, ";")
    ta.next(ENDMARKER, "")
    assert_ast_equals(code_postfix_op, result_postfix_op)
    assert_ast_transform(code_postfix_op, transformed_postfix_op)


code_postfix_op_unwrap = """
def unwrap(x: int?, y: int?) -> int {
    let z = x!
    return z * x!- y!;
}
"""
result_postfix_op_unwrap = """
def unwrap(x: (int,), y: (int,)) -> int:
    z = (x,)
    return z * (x,) - (y,)
"""


def test_postfix_op_unwrap():
    show_token(code_postfix_op_unwrap)
    ta = TokenizerAsserter(code_postfix_op_unwrap)
    ta.next(NAME, "def")
    ta.next(NAME, "unwrap")
    ta.next(OP, "(")
    ta.next(NAME, "x")
    ta.next(OP, ":")
    ta.next(NAME, "int")
    ta.next(NAME, OPTIONAL_QUESTION)
    ta.next(OP, ",")
    ta.next(NAME, "y")
    ta.next(OP, ":")
    ta.next(NAME, "int")
    ta.next(NAME, OPTIONAL_QUESTION)
    ta.next(OP, ")")
    ta.next(OP, "->")
    ta.next(NAME, "int")
    ta.next(OP, "{")
    ta.next(NAME, "let")
    ta.next(NAME, "z")
    ta.next(OP, "=")
    ta.next(NAME, "x")
    ta.next(NAME, FORCE_UNWRAP)
    ta.next(NEWLINE, "\n")  # Here is a NEWLINE as a delimiter
    ta.next(NAME, "return")
    ta.next(NAME, "z")
    ta.next(OP, "*")
    ta.next(NAME, "x")
    ta.next(NAME, FORCE_UNWRAP)
    ta.next(OP, "-")
    ta.next(NAME, "y")
    ta.next(NAME, FORCE_UNWRAP)
    ta.next(OP, ";")
    ta.next(OP, "}")
    assert_ast_equals(code_postfix_op_unwrap, result_postfix_op_unwrap)
