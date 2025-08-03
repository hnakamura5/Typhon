import ast
from ...src.Grammar.parser import parse_string

code_empty_if = """
if True {
}
"""

result_empty_if = """
if True:
    pass
"""


def test_stmt_if_empty():
    parsed = parse_string(code_empty_if, mode="exec", verbose=True)
    assert isinstance(parsed, ast.Module)
    assert ast.unparse(parsed) == result_empty_if.strip()


code_if_else = """
if True {
} elif False {
  return 0;
} else {
}
"""

result_if_else = """
if True:
    pass
elif False:
    return 0
else:
    pass
"""


def test_stmt_if_else():
    parsed = parse_string(code_if_else, mode="exec", verbose=True)
    assert isinstance(parsed, ast.Module)
    assert ast.unparse(parsed) == result_if_else.strip()


code_if_nested = """
if True {
    if (False) {
        return 1;
    } elif True {
        return 2;
    }
    return 3;
} else {
    return 4;
}
"""

result_if_nested = """
if True:
    if False:
        return 1
    elif True:
        return 2
    return 3
else:
    return 4
"""


def test_stmt_if_nested():
    parsed = parse_string(code_if_nested, mode="exec", verbose=True)
    assert isinstance(parsed, ast.Module)
    assert ast.unparse(parsed) == result_if_nested.strip()
