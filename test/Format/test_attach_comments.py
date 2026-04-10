import ast

from Typhon.Format.attach_comments import attach_comments
from Typhon.Grammar.parser import parse_string
from Typhon.Grammar.typhon_ast import (
    get_dangling_comments,
    get_leading_comments,
    get_trailing_comments,
)


def _parse_and_attach(source: str) -> ast.Module:
    module = parse_string(source, mode="exec")
    assert isinstance(module, ast.Module)
    attach_comments(module)
    return module


def _find_stmt(module: ast.Module, index: int) -> ast.stmt:
    return module.body[index]


# ---------------------------------------------------------------------------
# Leading comments
# ---------------------------------------------------------------------------


def test_leading_comment_before_first_stmt():
    module = _parse_and_attach("# header\nlet x = 1\n")
    stmt = _find_stmt(module, 0)
    leading = get_leading_comments(stmt)
    assert len(leading) == 1
    assert leading[0].string == "# header"


def test_multiple_leading_comments():
    module = _parse_and_attach("# first\n# second\nlet x = 1\n")
    stmt = _find_stmt(module, 0)
    leading = get_leading_comments(stmt)
    assert len(leading) == 2
    assert leading[0].string == "# first"
    assert leading[1].string == "# second"


def test_leading_comment_between_stmts():
    module = _parse_and_attach("let x = 1\n# between\nlet y = 2\n")
    first = _find_stmt(module, 0)
    second = _find_stmt(module, 1)
    assert get_leading_comments(first) == []
    leading = get_leading_comments(second)
    assert len(leading) == 1
    assert leading[0].string == "# between"


def test_leading_comment_inside_function_body():
    module = _parse_and_attach("def f() {\n    # inside\n    let x = 1\n}\n")
    func_def = _find_stmt(module, 0)
    assert isinstance(func_def, ast.FunctionDef)
    inner_stmt = func_def.body[0]
    leading = get_leading_comments(inner_stmt)
    assert len(leading) == 1
    assert leading[0].string == "# inside"


# ---------------------------------------------------------------------------
# Trailing comments
# ---------------------------------------------------------------------------


def test_trailing_comment_same_line():
    module = _parse_and_attach("let x = 1 # after\n")
    stmt = _find_stmt(module, 0)
    trailing = get_trailing_comments(stmt)
    assert len(trailing) == 1
    assert trailing[0].string == "# after"


def test_trailing_on_innermost_stmt():
    module = _parse_and_attach("let x = 1 # after x\nlet y = 2 # after y\n")
    first = _find_stmt(module, 0)
    second = _find_stmt(module, 1)
    t1 = get_trailing_comments(first)
    t2 = get_trailing_comments(second)
    assert len(t1) == 1
    assert t1[0].string == "# after x"
    assert len(t2) == 1
    assert t2[0].string == "# after y"


# ---------------------------------------------------------------------------
# Dangling comments
# ---------------------------------------------------------------------------


def test_dangling_comment_eof():
    module = _parse_and_attach("let x = 1\n# end\n")
    dangling = get_dangling_comments(module)
    assert len(dangling) == 1
    assert dangling[0].string == "# end"


def test_dangling_comment_only_comment():
    module = _parse_and_attach("# only\n")
    dangling = get_dangling_comments(module)
    assert len(dangling) == 1
    assert dangling[0].string == "# only"


def test_dangling_comment_empty_function_body():
    module = _parse_and_attach("def f() {\n    # only a comment\n}\n")
    func_def = _find_stmt(module, 0)
    assert isinstance(func_def, ast.FunctionDef)
    # The comment is dangling inside the function or its empty-body Pass
    # Check that it appears somewhere as dangling
    found = False
    for node in ast.walk(func_def):
        if get_dangling_comments(node):
            found = True
            assert get_dangling_comments(node)[0].string == "# only a comment"
            break
    assert found


def test_dangling_comment_end_of_block():
    module = _parse_and_attach("def f() {\n    let x = 1\n    # end of body\n}\n")
    func_def = _find_stmt(module, 0)
    assert isinstance(func_def, ast.FunctionDef)
    dangling = get_dangling_comments(func_def)
    assert len(dangling) == 1
    assert dangling[0].string == "# end of body"


# ---------------------------------------------------------------------------
# Mixed scenarios
# ---------------------------------------------------------------------------


def test_mixed_leading_and_trailing():
    source = "# header\nlet x = 1 # inline\n# mid\nlet y = 2 # after y\n"
    module = _parse_and_attach(source)
    first = _find_stmt(module, 0)
    second = _find_stmt(module, 1)

    assert len(get_leading_comments(first)) == 1
    assert get_leading_comments(first)[0].string == "# header"
    assert len(get_trailing_comments(first)) == 1
    assert get_trailing_comments(first)[0].string == "# inline"

    assert len(get_leading_comments(second)) == 1
    assert get_leading_comments(second)[0].string == "# mid"
    assert len(get_trailing_comments(second)) == 1
    assert get_trailing_comments(second)[0].string == "# after y"


def test_block_comment_as_leading():
    module = _parse_and_attach("#( block comment )#\nlet x = 1\n")
    stmt = _find_stmt(module, 0)
    leading = get_leading_comments(stmt)
    assert len(leading) == 1
    assert "#(" in leading[0].string or "block comment" in leading[0].string


def test_no_comments_leaves_empty():
    module = _parse_and_attach("let x = 1\nlet y = 2\n")
    for node in ast.walk(module):
        assert get_leading_comments(node) == []
        assert get_trailing_comments(node) == []
        assert get_dangling_comments(node) == []


def test_no_tokens_does_nothing():
    """Module without lossless token info should not crash."""
    module = ast.Module(body=[], type_ignores=[])
    attach_comments(module)
    assert get_dangling_comments(module) == []
