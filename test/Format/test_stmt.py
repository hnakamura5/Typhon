from .format_assertion_utils import assert_render_pipeline


code_if_block = """
if (a) { b } else { c }
"""
result_if_block = """
if (a) {
    b
} else {
    c
}
"""


def test_format_if_block_newline_format():
    assert_render_pipeline(code_if_block, result_if_block)


code_if_let_block = """
if (let x = foo()) { use(x) }
"""
result_if_let_block = """
if (let x = foo()) {
    use(x)
}
"""


def test_format_if_let_block_format():
    assert_render_pipeline(code_if_let_block, result_if_let_block)


code_if_let_cond = """
if (let x =foo(); x\n>\n0) { use(x) }
"""
result_if_let_cond = """
if (let x = foo(); x > 0) {
    use(x)
}
"""


def test_format_if_let_cond_format():
    assert_render_pipeline(code_if_let_cond, result_if_let_cond)


code_let_else = """
let x = foo() else { raise error() }
let x2 = foo() else { raise error() }
"""
result_let_else = """
let x = foo() else {
    raise error()
}
let x2 = foo() else {
    raise error()
}
"""


def test_format_let_else_format():
    assert_render_pipeline(code_let_else, result_let_else)


code_while_let = """
while (let x = foo()) { use(x) }
"""
result_while_let = """
while (let x = foo()) {
    use(x)
}
"""


def test_format_while_let_format():
    assert_render_pipeline(code_while_let, result_while_let)


code_function_block = """
def f(x: int) -> int { let x = x + 1; return x }
"""
result_function_block = """
def f(x: int) -> int {
    let x = x + 1
    return x
}
"""


def test_format_function_block_newline_format():
    assert_render_pipeline(code_function_block, result_function_block)


code_function_empty_block = """
def f(x: int) -> None {}
"""
result_function_empty_block = """
def f(x: int) -> None {}
"""


def test_format_function_empty_block_newline_format():
    assert_render_pipeline(code_function_empty_block, result_function_empty_block)


code_class_block = """
class C { let x = 1 }
"""
result_class_block = """
class C {
    let x = 1
}
"""


def test_format_class_block_newline_format():
    assert_render_pipeline(code_class_block, result_class_block)


code_match_with_attributes_pattern = """
match (x) { case ({.a, .b = c}) { ok } case (_) { fail } }
"""
result_match_with_attributes_pattern = """
match (x) {
    case ({.a, .b = c}) {
        ok
    }
    case (_) {
        fail
    }
}
"""


def test_format_match_with_attributes_pattern():
    assert_render_pipeline(
        code_match_with_attributes_pattern, result_match_with_attributes_pattern
    )


code_match_with_or_as_pattern = """
match (value) { case (x | y as both) { ok } }
"""
result_match_with_or_as_pattern = """
match (value) {
    case (x | y as both) {
        ok
    }
}
"""


def test_format_match_with_or_as_pattern():
    assert_render_pipeline(
        code_match_with_or_as_pattern, result_match_with_or_as_pattern
    )


code_match_with_sequence_pattern = """
match (value) { case ([head, tail]) { seq } }
"""
result_match_with_sequence_pattern = """
match (value) {
    case ([head, tail]) {
        seq
    }
}
"""


def test_format_match_with_sequence_pattern():
    assert_render_pipeline(
        code_match_with_sequence_pattern, result_match_with_sequence_pattern
    )


code_match_with_mapping_pattern = """
match (value) { case ({1: m1, 2: m2, **rest}) { map } }
"""
result_match_with_mapping_pattern = """
match (value) {
    case ({1: m1, 2: m2, **rest}) {
        map
    }
}
"""


def test_format_match_with_mapping_pattern():
    assert_render_pipeline(
        code_match_with_mapping_pattern, result_match_with_mapping_pattern
    )


code_match_with_class_pattern = """
match (value) { case (Point(item, x = axis)) { cls } }
"""
result_match_with_class_pattern = """
match (value) {
    case (Point(item, x = axis)) {
        cls
    }
}
"""


def test_format_match_with_class_pattern():
    assert_render_pipeline(
        code_match_with_class_pattern, result_match_with_class_pattern
    )


code_augassign_break_after_operator = """
aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa += bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
"""
result_augassign_break_after_operator = """
aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa +=
    bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
"""


def test_format_augassign_break_after_operator_indents_once():
    assert_render_pipeline(
        code_augassign_break_after_operator, result_augassign_break_after_operator
    )


code_import = """
import aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa, bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb as cccccccccccccccccccccccccccccccccccccccc, dddddddddddddddddddddddddddddddddddddddd
"""
result_import = """
import aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa,
       bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb as cccccccccccccccccccccccccccccccccccccccc,
       dddddddddddddddddddddddddddddddddddddddd
"""


def test_format_import_alignment():
    assert_render_pipeline(code_import, result_import)


code_import_from = """
from pkg.subpkg.module import aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa, bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb as cccccccccccccccccccccccccccccccccccccccc, dddddddddddddddddddddddddddddddddddddddd
"""
result_import_from = """
from pkg.subpkg.module import aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa,
                              bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb as cccccccccccccccccccccccccccccccccccccccc,
                              dddddddddddddddddddddddddddddddddddddddd
"""


def test_format_import_from_alignment():
    assert_render_pipeline(code_import_from, result_import_from)


code_import_from_parent = """
from ....pkg.subpkg.module import aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa, bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb as cccccccccccccccccccccccccccccccccccccccc, dddddddddddddddddddddddddddddddddddddddd
"""
result_import_from_parent = """
from ....pkg.subpkg.module import aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa,
                                  bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb as cccccccccccccccccccccccccccccccccccccccc,
                                  dddddddddddddddddddddddddddddddddddddddd
"""


def test_format_import_from_parent_alignment():
    assert_render_pipeline(code_import_from_parent, result_import_from_parent)


code_yield_and_yield_from = """
def gen() { yield 1;yield from [2,3] }
"""
result_yield_and_yield_from = """
def gen() {
    yield 1
    yield from [2, 3]
}
"""


def test_format_yield_and_yield_from():
    assert_render_pipeline(code_yield_and_yield_from, result_yield_and_yield_from)


code_await = """
async def f(x: int) -> int { return await g(x) }
"""
result_await = """
async def f(x: int) -> int {
    return await g(x)
}
"""


def test_format_await():
    assert_render_pipeline(code_await, result_await)


code_try_except_star = """
try { raise TypeError } except*(TypeError as e) { handle(e) }
"""
result_try_except_star = """
try {
    raise TypeError
} except* (TypeError as e) {
    handle(e)
}
"""


def test_format_try_except_star():
    assert_render_pipeline(code_try_except_star, result_try_except_star)


code_try_except_star_finally = """
try { risky() } except*(ValueError as e) { handle(e) } finally { cleanup() }
"""
result_try_except_star_finally = """
try {
    risky()
} except* (ValueError as e) {
    handle(e)
} finally {
    cleanup()
}
"""


def test_format_try_except_star_finally():
    assert_render_pipeline(code_try_except_star_finally, result_try_except_star_finally)


code_class_type_params = """
class Box[T] { let value: T = value }
"""
result_class_type_params = """
class Box[T] {
    let value: T = value
}
"""


def test_format_class_type_params():
    assert_render_pipeline(code_class_type_params, result_class_type_params)


code_class_type_params_with_bound = """
class Container[T: int] { let value: T = value }
"""
result_class_type_params_with_bound = """
class Container[T: int] {
    let value: T = value
}
"""


def test_format_class_type_params_with_bound():
    assert_render_pipeline(
        code_class_type_params_with_bound, result_class_type_params_with_bound
    )


code_class_type_params_with_base = """
class MyList[T](list) { let x = 1 }
"""
result_class_type_params_with_base = """
class MyList[T](list) {
    let x = 1
}
"""


def test_format_class_type_params_with_base():
    assert_render_pipeline(
        code_class_type_params_with_base, result_class_type_params_with_base
    )


code_func_type_params = """
def identity[T](x: T) -> T { return x }
"""
result_func_type_params = """
def identity[T](x: T) -> T {
    return x
}
"""


def test_format_func_type_params():
    assert_render_pipeline(code_func_type_params, result_func_type_params)


code_func_type_params_multiple = """
def pair[T, U](a: T, b: U) -> tuple { return (a, b) }
"""
result_func_type_params_multiple = """
def pair[T, U](a: T, b: U) -> tuple {
    return (a, b)
}
"""


def test_format_func_type_params_multiple():
    assert_render_pipeline(
        code_func_type_params_multiple, result_func_type_params_multiple
    )


code_func_typevar_tuple = """
def foo[*Ts]() -> None {}
"""
result_func_typevar_tuple = """
def foo[*Ts]() -> None {}
"""


def test_format_func_typevar_tuple():
    assert_render_pipeline(code_func_typevar_tuple, result_func_typevar_tuple)


code_func_paramspec = """
def decorator[**P](f: P) -> P { return f }
"""
result_func_paramspec = """
def decorator[**P](f: P) -> P {
    return f
}
"""


def test_format_func_paramspec():
    assert_render_pipeline(code_func_paramspec, result_func_paramspec)


code_func_type_param_long = """
def long_type_param[Taaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa, Tbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb: int](x: Taaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa, y: Tbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb) -> Taaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa { return x }
"""
result_func_type_param_long = """
def long_type_param[
    Taaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa,
    Tbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb: int
](
    x: Taaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa,
    y: Tbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
) -> Taaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa {
    return x
}
"""


def test_format_func_type_param_long():
    assert_render_pipeline(code_func_type_param_long, result_func_type_param_long)
