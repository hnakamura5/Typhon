from ..assertion_utils import (
    assert_parse,
    assert_ast_type,
    assert_transform,
    assert_parse_error_recovery,
    Range,
    Pos,
    with_parser_verbose,
)
from src.Typhon.Grammar.typhon_ast import is_var, is_let
import ast
from src.Typhon.Driver.debugging import set_debug_verbose

code_for = """
for (let i in range(10)) {
    print(i);
}
"""
result_for = """
for i in range(10):
    print(i)
"""


def test_stmt_for():
    parsed = assert_parse(code_for, result_for)
    for_stmt = assert_ast_type(parsed.body[0], ast.For)
    assert is_let(for_stmt)


code_async_for = """
async for (let i in async_range(10)) {
    await f(i);
}
"""
result_async_for = """
async for i in async_range(10):
    await f(i)
"""


def test_stmt_async_for():
    parsed = assert_parse(code_async_for, result_async_for)
    async_for_stmt = assert_ast_type(parsed.body[0], ast.AsyncFor)
    assert is_let(async_for_stmt)


code_for_typed = """
for (var i: int in range(10)) {
    print(i);
}
"""
# TODO: Type annotation as type_comment
result_for_typed = """
for i in range(10):
    print(i)
"""
transformed_for_typed = """
for _typh_vr_m0_0_i in range(10):
    _typh_vr_m0_0_i: int
    print(_typh_vr_m0_0_i)
"""


def test_stmt_for_typed():
    parsed = assert_parse(code_for_typed, result_for_typed)
    for_stmt = assert_ast_type(parsed.body[0], ast.For)
    assert is_var(for_stmt)
    assert_transform(code_for_typed, transformed_for_typed)


code_for_unpack = """
for (let (a, b) in [(1, 1.0), (2, 2.0)]) {
    print(a);
    print(b);
}
"""
result_for_unpack = """
for _typh_anonymous_0 in [(1, 1.0), (2, 2.0)]:
    if True:
        match _typh_anonymous_0:
            case [a, b]:
                print(a)
                print(b)
            case _:# type: ignore[all]
                raise TypeError
"""


def test_stmt_for_unpack():
    parsed = assert_parse(code_for_unpack, result_for_unpack)
    for_stmt = assert_ast_type(parsed.body[0], ast.For)
    assert is_let(for_stmt)


code_for_unpack_annot = """
for (let (a:int, b:float) in [(1, 1.0), (2, 2.0)]) {
    print(a);
    print(b);
}
"""
result_for_unpack_annot = """
from typing import Final as _typh_bi_Final
for _typh_vr_m0_0_ in [(1, 1.0), (2, 2.0)]:
    _typh_vr_m0_0_: _typh_bi_Final
    match _typh_vr_m0_0_:
        case tuple([_typh_cn_m0_1_a, _typh_cn_m0_2_b]):
            _typh_cn_m0_1_a: _typh_bi_Final[int]
            _typh_cn_m0_2_b: _typh_bi_Final[float]
            print(_typh_cn_m0_1_a)
            print(_typh_cn_m0_2_b)
        case _:# type: ignore[all]
            raise TypeError
"""


def test_stmt_for_unpack_annot():
    assert_transform(code_for_unpack_annot, result_for_unpack_annot)


code_for_parenless = """
for let (a, b) in [(1, 1.0), (2, 2.0)] {
    print(a);
    print(b);
}
"""
result_for_parenless = """
for _typh_anonymous_0 in [(1, 1.0), (2, 2.0)]:
    if True:
        match _typh_anonymous_0:
            case [a, b]:
                print(a)
                print(b)
            case _:# type: ignore[all]
                raise TypeError
"""


def test_stmt_for_parenless_recovery():
    assert_parse_error_recovery(
        code_for_parenless,
        result_for_parenless,
        [
            ("expected '('", Range(Pos(1, 3), Pos(1, 4))),
            ("expected ')'", Range(Pos(1, 38), Pos(1, 39))),
        ],
    )


code_for_lack = """
for range(10) {
    print(i);
}
"""
result_for_lack = """
for _typh_anonymous_0 in ...:
    if True:
        match _typh_anonymous_0:
            case range(10):
                print(i)
            case _:# type: ignore[all]
                raise TypeError
"""


def test_stmt_for_lack():
    with with_parser_verbose(True):
        assert_parse_error_recovery(
            code_for_lack,
            result_for_lack,
            [
                ("expected '('", Range(Pos(1, 3), Pos(1, 4))),
                ("expected 'let/var'", Range(Pos(1, 4), Pos(1, 5))),
                ("expected 'in'", Range(Pos(1, 13), Pos(1, 14))),
                ("expected expression", Range(Pos(1, 14), Pos(1, 15))),
                ("expected ')'", Range(Pos(1, 15), Pos(1, 16))),
            ],
        )
