import ast

from Typhon.Grammar.parser import parse_string
from Typhon.SourceMap.datatype import Pos, Range
from Typhon.SourceMap.source_ast_cache import SourceAstCache


def _build_cache(source: str) -> SourceAstCache:
    parsed = parse_string(source)
    assert isinstance(parsed, ast.Module)
    return SourceAstCache(parsed, source, "<string>")


code_stmt_if = """
def left_func(x: int) -> int {
    var y = 0;
    for (let i in range(x)) {
        if (i % 2 == 0) {
            y += i;
        }
    }
    return y;
}
"""


def test_source_ast_cache_position_stmt_and_expr():
    cache = _build_cache(code_stmt_if)

    stmt = cache.source_pos_to_stmt(Pos(5, 14))
    assert isinstance(stmt, ast.AugAssign)
    stmt_range = Range.from_ast_node(stmt)
    assert stmt_range is not None
    assert stmt_range.of_string(code_stmt_if) == "y += i"

    expr = cache.source_pos_to_expr(Pos(4, 12))
    assert isinstance(expr, ast.Name)
    expr_range = Range.from_ast_node(expr)
    assert expr_range is not None
    assert expr_range.of_string(code_stmt_if) == "i"


def test_source_ast_cache_range_expr_and_stmt():
    cache = _build_cache(code_stmt_if)

    expr = cache.source_range_to_expr(Range(Pos(4, 12), Pos(4, 17)))
    assert isinstance(expr, ast.BinOp)
    expr_range = Range.from_ast_node(expr)
    assert expr_range is not None
    assert expr_range.of_string(code_stmt_if) == "i % 2"

    stmt = cache.source_range_to_stmt(Range(Pos(8, 4), Pos(8, 12)))
    assert isinstance(stmt, ast.Return)
    stmt_range = Range.from_ast_node(stmt)
    assert stmt_range is not None
    assert stmt_range.of_string(code_stmt_if) == "return y"


code_nested_access = """
def left_func(value: A?) {
    return value?.field[0]
}
"""


def test_source_ast_cache_range_source_code_and_end_pos():
    cache = _build_cache(code_nested_access)

    expr = cache.source_range_to_expr(Range(Pos(2, 11), Pos(2, 26)))
    assert expr is not None
    expr_range = Range.from_ast_node(expr)
    assert expr_range is not None
    assert cache.source_range_to_source_code(expr_range) == "value?.field[0]"
    assert cache.source_code_end_pos() == Pos(3, 1)


code_stmt_if_let = """
def left_func(opt_x: int?, opt_y: int?) -> int {
    if (let x = opt_x, y = opt_y; x > 0) {
        return x + 1;
    } else {
        return 0;
    }
}
"""


def test_source_ast_cache_if_let_stmt_and_expr():
    cache = _build_cache(code_stmt_if_let)

    stmt = cache.source_pos_to_stmt(Pos(2, 12))
    assert isinstance(stmt, ast.If)
    stmt_range = Range.from_ast_node(stmt)
    assert stmt_range is not None
    assert stmt_range == Range(Pos(2, 4), Pos(6, 5))  # the whole if-else statement

    expr = cache.source_range_to_expr(Range(Pos(2, 34), Pos(2, 39)))
    assert isinstance(expr, ast.Compare)
    expr_range = Range.from_ast_node(expr)
    assert expr_range is not None
    assert expr_range.of_string(code_stmt_if_let) == "x > 0"

    inner_stmt = cache.source_pos_to_stmt(Pos(3, 15))
    assert isinstance(inner_stmt, ast.Return)
    inner_stmt_range = Range.from_ast_node(inner_stmt)
    assert inner_stmt_range is not None
    assert inner_stmt_range.of_string(code_stmt_if_let) == "return x + 1"


code_stmt_let_else = """
def left_func(opt_x: int?) -> int {
    let x = opt_x else {
        return 0
    }
    return x + 1
}
"""


def test_source_ast_cache_let_else_stmt_and_expr():
    cache = _build_cache(code_stmt_let_else)

    stmt = cache.source_pos_to_stmt(Pos(2, 8))
    assert isinstance(stmt, ast.Match)
    stmt_range = Range.from_ast_node(stmt)
    assert stmt_range is not None
    assert stmt_range == Range(Pos(2, 4), Pos(4, 5))  # the whole let-else statement

    expr = cache.source_range_to_expr(Range(Pos(5, 11), Pos(5, 16)))
    assert isinstance(expr, ast.BinOp)
    expr_range = Range.from_ast_node(expr)
    assert expr_range is not None
    assert expr_range.of_string(code_stmt_let_else) == "x + 1"

    else_stmt = cache.source_pos_to_stmt(Pos(3, 15))
    assert isinstance(else_stmt, ast.Return)
    else_stmt_range = Range.from_ast_node(else_stmt)
    assert else_stmt_range is not None
    assert else_stmt_range.of_string(code_stmt_let_else) == "return 0"
