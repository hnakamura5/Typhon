import ast
import copy

from Typhon.Grammar.parser import parse_string
from Typhon.Grammar.unparse_custom import unparse_custom
from Typhon.LanguageServer.partial_reparse import _reparce_range_and_replace  # type: ignore[reportPrivateUsage]
from Typhon.SourceMap.ast_match_based_map import map_from_translated
from Typhon.SourceMap.datatype import Pos, Range
from Typhon.SourceMap.source_ast_cache import SourceAstCache
from Typhon.Transform.transform import transform

from test.Grammar.assertion_utils import assert_transform_ast


reparce_function_code = """
def func() {
    var a = 1
    return a
}

def reparse_func() {
    var a = 1
    return a + 1
}

def func2(x: int) {
    return x * 2
}
"""
reparse_function_part_replaced_code = """
def func() {
    var a = 1
    return a
}

def reparse_func() { # Here is replaced and change line.
    var b = 1
    return b - 1
}

def func2(x: int) {
    return x * 2
}
"""

reparce_function_transformed = """
def func():
    a = 1
    return a

def reparse_func():
    a = 1
    return a + 1

def func2(x: int):
    return x * 2
"""

reparce_function_part_replaced_transformed = """
def func():
    a = 1
    return a

def reparse_func():
    b = 1
    return b - 1

def func2(x: int):
    return x * 2
"""


def test_partial_reparse():
    original_ast = parse_string(reparce_function_code)
    assert isinstance(original_ast, ast.Module)
    ast_cache = SourceAstCache(
        original_ast,
        reparce_function_code,
        "<string>",
    )
    assert_transform_ast(original_ast, reparce_function_transformed)
    original_ast_transformed = copy.deepcopy(original_ast)
    transform(original_ast_transformed)
    unparsed = unparse_custom(original_ast_transformed)
    mapping = map_from_translated(
        original_ast_transformed, reparce_function_code, "<string>", unparsed
    )
    assert mapping is not None
    # " Note this is replacing original_ast_transformed.
    reparsed_ast_part_replaced = _reparce_range_and_replace(
        original_ast_transformed,
        reparse_function_part_replaced_code,
        Range(Pos(6, 5), Pos(6, 6)),
        ast_cache,
        mapping,
    )
    assert reparsed_ast_part_replaced is not None
    # Note again this is replacing original_ast_transformed.
    assert reparsed_ast_part_replaced is original_ast_transformed
    assert_transform_ast(
        reparsed_ast_part_replaced, reparce_function_part_replaced_transformed
    )
