from ..assertion_utils import (
    show_token,
    assert_ast_equals,
    TokenizerAsserter,
    assert_ast_transform,
)
from ...src.Typhon.Grammar.typhon_ast import (
    OPTIONAL_QUESTION,
)
from tokenize import NAME, OP, NEWLINE, ENDMARKER, NUMBER
import ast

pipe_operator_code = """
def func(x: int) -> int {
    return x |> (x) => x * 2
             |> (x) => x + 1
}
"""
pipe_operator_result = """
def func(x: int) -> int:
    return (lambda x: (lambda x: x + 1)(x * 2))(x)
"""


def test_pipe_operator():
    show_token(pipe_operator_code)
    ta = TokenizerAsserter(pipe_operator_code)
    ta.next(NAME, "def")
    ta.next(NAME, "func")
    ta.next(OP, "(")
    ta.next(NAME, "x")
    ta.next(OP, ":")
    ta.next(NAME, "int")
    ta.next(OP, ")")
    ta.next(OP, "->")
    ta.next(NAME, "int")
    ta.next(OP, "{")
    ta.next(NAME, "return")
    ta.next(NAME, "x")
    ta.next(OP, "|>")  # This is pipe operator.
    ta.next(OP, "(")
    ta.next(NAME, "x")
    ta.next(OP, ")")
    ta.next(OP, "=>")
    ta.next(NAME, "x")
    ta.next(OP, "*")
    ta.next(NUMBER, "2")
    ta.next(OP, "|>")  # This is pipe operator.
    ta.next(OP, "(")
    ta.next(NAME, "x")
    ta.next(OP, ")")
    ta.next(OP, "=>")
    ta.next(NAME, "x")
    ta.next(OP, "+")
    ta.next(NUMBER, "1")
    ta.next(OP, "}")
    ta.next(NEWLINE, "\n")
    ta.next(ENDMARKER, "")
    assert_ast_equals(pipe_operator_code, pipe_operator_result)


optional_pipe_operator_code = """
def func(x: int?) -> int? {
    return x ?|> (x) => x * 2
             ?|> (x) => x + 1
}
"""
optional_pipe_operator_result = """
def func(x: (int,)) -> (int,):
    return (lambda x: (lambda x: x + 1)(x * 2))(x)
"""


def test_optional_pipe_operator():
    show_token(optional_pipe_operator_code)
    ta = TokenizerAsserter(optional_pipe_operator_code)
    ta.next(NAME, "def")
    ta.next(NAME, "func")
    ta.next(OP, "(")
    ta.next(NAME, "x")
    ta.next(OP, ":")
    ta.next(NAME, "int")
    ta.next(NAME, OPTIONAL_QUESTION)
    ta.next(OP, ")")
    ta.next(OP, "->")
    ta.next(NAME, "int")
    ta.next(NAME, OPTIONAL_QUESTION)
    ta.next(OP, "{")
    ta.next(NAME, "return")
    ta.next(NAME, "x")
    ta.next(OP, "?|>")  # This is optional pipe operator.
    ta.next(OP, "(")
    ta.next(NAME, "x")
    ta.next(OP, ")")
    ta.next(OP, "=>")
    ta.next(NAME, "x")
    ta.next(OP, "*")
    ta.next(NUMBER, "2")
    ta.next(OP, "?|>")  # This is optional pipe operator.
    ta.next(OP, "(")
    ta.next(NAME, "x")
    ta.next(OP, ")")
    ta.next(OP, "=>")
    ta.next(NAME, "x")
    ta.next(OP, "+")
    ta.next(NUMBER, "1")
    ta.next(OP, "}")
    ta.next(NEWLINE, "\n")
    ta.next(ENDMARKER, "")
    assert_ast_equals(optional_pipe_operator_code, optional_pipe_operator_result)
