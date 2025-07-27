import ast
from ...src.Grammar.parser import parse_string

# code = """
# def func() {
#     return
# }
# """
code = """
def func():
    return

"""

result = """
def func():
    return

"""


def test_stmt_def():
    parsed = parse_string(code, mode="exec")
    assert isinstance(parsed, ast.Module)
    assert ast.unparse(parsed) == result.strip()
