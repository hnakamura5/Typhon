from ..assertion_utils import (
    show_token,
    assert_parse,
    TokenizerAsserter,
    assert_transform,
    AllTokenAsserter,
)
from src.Typhon.Grammar.typhon_ast import (
    OPTIONAL_QUESTION,
    FORCE_UNWRAP,
    is_optional,
    is_optional_question,
    is_coalescing,
)
from tokenize import NAME, OP, NEWLINE, ENDMARKER, NUMBER
import ast


optional_chain_code = """
def func(x: list[int]?) -> int? {
    return x ?.count(42)
}
"""
optional_chain_result = """
def func(x: (list[int],)) -> (int,):
    return x.count(42)
"""


def test_optional_chain():
    show_token(optional_chain_code)
    ta = TokenizerAsserter(optional_chain_code)
    ta.next(NAME, "def")
    ta.next(NAME, "func")
    ta.next(OP, "(")
    ta.next(NAME, "x")
    ta.next(OP, ":")
    ta.next(NAME, "list")
    ta.next(OP, "[")
    ta.next(NAME, "int")
    ta.next(OP, "]")
    ta.next(NAME, OPTIONAL_QUESTION)
    ta.next(OP, ")")
    ta.next(OP, "->")
    ta.next(NAME, "int")
    ta.next(NAME, OPTIONAL_QUESTION)
    ta.next(OP, "{")
    ta.next(NAME, "return")
    ta.next(NAME, "x")
    ta.next(OP, "?.")  # This is optional one.
    ta.next(NAME, "count")
    ta.next(OP, "(")
    ta.next(NUMBER, "42")
    ta.next(OP, ")")
    ta.next(OP, "}")
    ta.next(NEWLINE, "\n")
    ta.next(ENDMARKER, "")
    parsed = assert_parse(optional_chain_code, optional_chain_result)
    func = parsed.body[0]
    assert isinstance(func, ast.FunctionDef)
    arg_x = func.args.args[0].annotation
    assert isinstance(arg_x, ast.expr) and is_optional_question(arg_x)


optional_coalesce_code = """
def func(x: int?) -> int {
    return x ?? 0
}
"""
optional_coalesce_result = """
def func(x: (int,)) -> int:
    return (x, 0)
"""


def test_optional_coalesce():
    show_token(optional_coalesce_code)
    ta = TokenizerAsserter(optional_coalesce_code)
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
    ta.next(OP, "{")
    ta.next(NAME, "return")
    ta.next(NAME, "x")
    ta.next(OP, "??")  # This is optional coalesce operator.
    ta.next(NUMBER, "0")
    ta.next(OP, "}")
    ta.next(NEWLINE, "\n")
    ta.next(ENDMARKER, "")
    parsed = assert_parse(optional_coalesce_code, optional_coalesce_result)
    func = parsed.body[0]
    assert isinstance(func, ast.FunctionDef)
    arg_x = func.args.args[0].annotation
    assert isinstance(arg_x, ast.expr) and is_optional_question(arg_x)
    return_stmt = func.body[0]
    assert isinstance(return_stmt, ast.Return)
    assert isinstance(return_stmt.value, ast.Tuple)
    assert is_coalescing(return_stmt.value)


optional_call_code = """
def func(f: ((int) -> int?)?) -> int? {
    return f?(42);
}
"""
optional_call_result = """
def func(f: (__arrow_type,)) -> (int,):
    return f(42)
"""


def test_optional_call():
    show_token(optional_call_code)
    ta = TokenizerAsserter(optional_call_code)
    ta.next(NAME, "def")
    ta.next(NAME, "func")
    ta.next(OP, "(")
    ta.next(NAME, "f")
    ta.next(OP, ":")
    ta.next(OP, "(")
    ta.next(OP, "(")
    ta.next(NAME, "int")
    ta.next(OP, ")")
    ta.next(OP, "->")
    ta.next(NAME, "int")
    ta.next(NAME, OPTIONAL_QUESTION)
    ta.next(OP, ")")
    ta.next(NAME, OPTIONAL_QUESTION)
    ta.next(OP, ")")
    ta.next(OP, "->")
    ta.next(NAME, "int")
    ta.next(NAME, OPTIONAL_QUESTION)
    ta.next(OP, "{")
    ta.next(NAME, "return")
    ta.next(NAME, "f")
    ta.next(OP, "?(")  # This is optional call.
    ta.next(NUMBER, "42")
    ta.next(OP, ")")
    ta.next(OP, ";")
    ta.next(OP, "}")
    ta.next(NEWLINE, "\n")
    ta.next(ENDMARKER, "")
    parsed = assert_parse(optional_call_code, optional_call_result)
    func = parsed.body[0]
    assert isinstance(func, ast.FunctionDef)
    arg_x = func.args.args[0].annotation
    assert isinstance(arg_x, ast.expr) and is_optional_question(arg_x)
    return_stmt = func.body[0]
    assert isinstance(return_stmt, ast.Return)
    assert isinstance(return_stmt.value, ast.Call)
    assert is_optional(return_stmt.value)


optional_subscript_code = """
def func(a: list[int]?) -> int? {
    return a?[0];
}
"""
optional_subscript_result = """
def func(a: (list[int],)) -> (int,):
    return a[0]
"""


def test_optional_subscript():
    show_token(optional_subscript_code)
    ta = TokenizerAsserter(optional_subscript_code)
    ta.next(NAME, "def")
    ta.next(NAME, "func")
    ta.next(OP, "(")
    ta.next(NAME, "a")
    ta.next(OP, ":")
    ta.next(NAME, "list")
    ta.next(OP, "[")
    ta.next(NAME, "int")
    ta.next(OP, "]")
    ta.next(NAME, OPTIONAL_QUESTION)
    ta.next(OP, ")")
    ta.next(OP, "->")
    ta.next(NAME, "int")
    ta.next(NAME, OPTIONAL_QUESTION)
    ta.next(OP, "{")
    ta.next(NAME, "return")
    ta.next(NAME, "a")
    ta.next(OP, "?[")  # This is optional subscript.
    ta.next(NUMBER, "0")
    ta.next(OP, "]")
    ta.next(OP, ";")
    ta.next(OP, "}")
    ta.next(NEWLINE, "\n")
    ta.next(ENDMARKER, "")
    parsed = assert_parse(optional_subscript_code, optional_subscript_result)
    func = parsed.body[0]
    assert isinstance(func, ast.FunctionDef)
    arg_x = func.args.args[0].annotation
    assert isinstance(arg_x, ast.expr) and is_optional_question(arg_x)
    return_stmt = func.body[0]
    assert isinstance(return_stmt, ast.Return)
    assert isinstance(return_stmt.value, ast.Subscript)
    assert is_optional(return_stmt.value)
    aa = AllTokenAsserter(optional_subscript_code)
    aa.assert_length(24)
    aa.next(NAME, "def")
    aa.next(NAME, "func")
    aa.next(OP, "(")
    aa.next(NAME, "a")
    aa.next(OP, ":")
    aa.next(NAME, "list")
    aa.next(OP, "[")
    aa.next(NAME, "int")
    aa.next(OP, "]")
    aa.next(NAME, OPTIONAL_QUESTION)
    aa.next(OP, ")")
    aa.next(OP, "->")
    aa.next(NAME, "int")
    aa.next(NAME, OPTIONAL_QUESTION)
    aa.next(OP, "{")
    aa.next(NAME, "return")
    aa.next(NAME, "a")
    aa.next(OP, "?[")  # This is optional subscript.
    aa.next(NUMBER, "0")
    aa.next(OP, "]")
    aa.next(OP, ";")
    aa.next(OP, "}")
    aa.next(NEWLINE, "\n")
    aa.next(ENDMARKER, "")
