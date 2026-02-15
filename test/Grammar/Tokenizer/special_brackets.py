from ..assertion_utils import (
    show_token,
    assert_parse,
    TokenizerAsserter,
)
from Typhon.Grammar.typhon_ast import (
    is_record_literal,
)
from tokenize import NAME, OP, NEWLINE, ENDMARKER, NUMBER, STRING
import ast

record_literal_code = """
{|x = 1, y = '2'|}
"""
record_literal_result = """
__record_literal
"""


def test_record_literal():
    show_token(record_literal_code)
    ta = TokenizerAsserter(record_literal_code)
    ta.next(OP, "{|")  # Start of record literal.
    ta.next(NAME, "x")
    ta.next(OP, "=")
    ta.next(NUMBER, "1")
    ta.next(OP, ",")
    ta.next(NAME, "y")
    ta.next(OP, "=")
    ta.next(STRING, "'2'")
    ta.next(OP, "|}")  # End of record literal.
    ta.next(NEWLINE, "\n")
    ta.next(ENDMARKER, "")
    parsed = assert_parse(record_literal_code, record_literal_result)
    expr_stmt = parsed.body[0]
    assert isinstance(expr_stmt, ast.Expr)
    name = expr_stmt.value
    assert isinstance(name, ast.Name)
    assert is_record_literal(name)
