from ..assertion_utils import assert_ast_equals, assert_ast_type, assert_ast_transform
from ....src.Typhon.Grammar.typhon_ast import is_var, is_let
import ast
from ....src.Typhon.Driver.debugging import set_debug_verbose

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
    parsed = assert_ast_equals(code_for, result_for)
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
    parsed = assert_ast_equals(code_async_for, result_async_for)
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


def test_stmt_for_typed():
    parsed = assert_ast_equals(code_for_typed, result_for_typed)
    for_stmt = assert_ast_type(parsed.body[0], ast.For)
    assert is_var(for_stmt)


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
            case _:
                raise TypeError
"""


def test_stmt_for_unpack():
    parsed = assert_ast_equals(code_for_unpack, result_for_unpack)
    for_stmt = assert_ast_type(parsed.body[0], ast.For)
    assert is_let(for_stmt)


code_for_unpack_annot = """
for (let (a:int, b:float) in [(1, 1.0), (2, 2.0)]) {
    print(a);
    print(b);
}
"""
result_for_unpack_annot = """
for _typh_vr_m0_0_ in [(1, 1.0), (2, 2.0)]:
    _typh_cn_m0_1_a: int
    _typh_cn_m0_2_b: float
    match _typh_vr_m0_0_:
        case [_typh_cn_m0_1_a, _typh_cn_m0_2_b]:
            pass
        case _:
            raise TypeError
"""


def test_stmt_for_unpack_annot():
    assert_ast_transform(code_for_unpack_annot, result_for_unpack_annot)
