import ast

from Typhon.Format.doc_render import render_doc_to_string
from Typhon.Format.print_to_doc import print_to_doc
from Typhon.Grammar.parser import parse_string


def _parse_module(source: str) -> ast.Module:
    parsed = parse_string(source, mode="exec")
    assert isinstance(parsed, ast.Module)
    return parsed


def _render_source(source: str) -> str:
    module = _parse_module(source)
    return render_doc_to_string(print_to_doc(module))


def _mess_up_source(source: str) -> str:
    # Between some keywords, space cannot be replaced with newline.
    elts = source.split()
    result: list[str] = []
    for i, elt in enumerate(elts):
        next_elt = elts[i + 1] if i + 1 < len(elts) else ""
        if elt in ["return", "yield", "raise", "as", "from", "type"] or next_elt in {
            "import",
            "from",
        }:
            result.append(elt + "  ")
        else:
            result.append(elt + " \n  ")
    return "".join(result)


def assert_render_pipeline(source: str, expected: str) -> None:
    result = _render_source(source)
    assert result == expected.strip(), f"Expected:\n{expected}\n\nGot:\n{result}"
    round_tripped = _render_source(result)
    assert round_tripped.strip() == expected.strip(), (
        f"Round trip failed. Expected:\n{expected}\n\nGot:\n{round_tripped}"
    )
    messed_up = _mess_up_source(source)
    result_from_messed_up = _render_source(messed_up)
    assert result_from_messed_up.strip() == expected.strip(), (
        f"Formatter did not normalize messed up source. Expected:\n{expected}\n\nGot:\n{result_from_messed_up}\n\nOriginal source:\n{source}\n\nOriginal messed up source:\n{messed_up}"
    )


code_constant = """
1_000
"""
result_constant = """
1_000
"""


def test_format_constant_preserves_raw_tokens():
    assert_render_pipeline(code_constant, result_constant)


code_expression = """
(1 + 2)
"""
result_expression = """
(1 + 2)
"""


def test_format_expression_keeps_paren_tokens():
    assert_render_pipeline(code_expression, result_expression)


code_binop_operator_leading_break = """
aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa + bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
"""

result_binop_operator_leading_break = """
aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
+ bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
"""


def test_format_binop_operator_leading_break():
    assert_render_pipeline(
        code_binop_operator_leading_break, result_binop_operator_leading_break
    )


code_call = """
f(1, x=2)
"""
result_call = """
f(1, x=2)
"""


def test_format_call_with_keywords():
    assert_render_pipeline(code_call, result_call)


code_loag_call = """
let x = f(aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa, aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa)
"""

result_long_call = """
let x = f(
    aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa,
    aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
)
"""


def test_format_long_call():
    assert_render_pipeline(code_loag_call, result_long_call)


code_assign_rhs_break_after_equal = """
let result = aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa + bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
"""

result_assign_rhs_break_after_equal = """
let result =
    aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
    + bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
"""


def test_format_assign_break_after_equal():
    assert_render_pipeline(
        code_assign_rhs_break_after_equal, result_assign_rhs_break_after_equal
    )


code_record_literal = """
{|x = 1, y: str = '2'|}
"""
result_record_literal = """
{|x = 1, y: str = '2'|}
"""


def test_format_record_literal():
    assert_render_pipeline(code_record_literal, result_record_literal)


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


code_function_literal_inline_return = """
let f = (x: int)=>x+1
"""
result_function_literal_inline_return = """
let f = (x: int) => x + 1
"""


def test_format_function_literal_inline_return():
    assert_render_pipeline(
        code_function_literal_inline_return, result_function_literal_inline_return
    )


code_function_literal_block = """
let f = (x: int) => { let y = x + 1; return y }
"""
result_function_literal_block = """
let f = (x: int) => {
    let y = x + 1
    return y
}
"""


def test_format_function_literal_block():
    assert_render_pipeline(code_function_literal_block, result_function_literal_block)


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


code_long_name_tuple = """
let aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa = (1, 2, 3)
"""
result_long_name_tuple = """
let aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa = (
    1,
    2,
    3
)
"""


def test_format_long_name_tuple():
    assert_render_pipeline(code_long_name_tuple, result_long_name_tuple)


code_long_name_list = """
let x= [aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa, bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb, ccccccccccccccccccccccccccccccc]
"""
result_long_name_list = """
let x = [
    aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa,
    bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb,
    ccccccccccccccccccccccccccccccc
]
"""


def test_format_long_name_list():
    assert_render_pipeline(code_long_name_list, result_long_name_list)


code_annassign_break_after_equal = """
let aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa: int = bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
"""
result_annassign_break_after_equal = """
let aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa: int =
    bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
"""


def test_format_annassign_break_after_equal_indents_once():
    assert_render_pipeline(
        code_annassign_break_after_equal, result_annassign_break_after_equal
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


code_attribute = """
let x = obj.attribute_name
"""
result_attribute = """
let x = obj.attribute_name
"""


def test_format_attribute():
    assert_render_pipeline(code_attribute, result_attribute)


code_attribute_long_wrap = """
let x = aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
"""
result_attribute_long_wrap = """
let x =
    aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
    .bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
"""


def test_format_attribute_long_wrap():
    assert_render_pipeline(code_attribute_long_wrap, result_attribute_long_wrap)


code_attribute_chain_long_wrap = """
let x = aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
"""
result_attribute_chain_long_wrap = """
let x =
    aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
    .bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
    .cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
"""


def test_format_attribute_chain_long_wrap():
    assert_render_pipeline(
        code_attribute_chain_long_wrap, result_attribute_chain_long_wrap
    )


code_method_chain_long_wrap = """
let vvvvvvvvvvvvvvvvvvvv = aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa(xxxxxxxxx, yyyyyyyyyy).bbbbbbbbbbbbbbbbbbbb(xxxxxxxxx, yyyyyyyyyy)?.ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc(xxxxxxxxx, yyyyyyyyyy)
"""
result_method_chain_long_wrap = """
let vvvvvvvvvvvvvvvvvvvv = aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa(
    xxxxxxxxx,
    yyyyyyyyyy
)
.bbbbbbbbbbbbbbbbbbbb(xxxxxxxxx, yyyyyyyyyy)
?.ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc(
    xxxxxxxxx,
    yyyyyyyyyy
)
"""


def test_format_method_chain_long_wrap():
    assert_render_pipeline(code_method_chain_long_wrap, result_method_chain_long_wrap)


code_if_comp = """
let x = (if (a)   b \n else   c)
"""
result_if_comp = """
let x = (if(a) b else c)
"""


def test_format_if_comp_format():
    assert_render_pipeline(code_if_comp, result_if_comp)


code_if_elif_comp = """
let x = (if (a)   b \n elif (c) d else   e)
"""
result_if_elif_comp = """
let x = (if(a) b elif(c) d else e)
"""


def test_format_if_elif_comp_format():
    assert_render_pipeline(code_if_elif_comp, result_if_elif_comp)


code_if_elif_comp_long = """
let x = (if (aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa) bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb elif (cccccccccccccccccccccccccccccccccccccccc) ddddddddddddddddddddddddddddddddddddddddd else eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee)
"""
result_if_elif_comp_long = """
let x = (if(aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa)
             bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
         elif(cccccccccccccccccccccccccccccccccccccccc)
             ddddddddddddddddddddddddddddddddddddddddd
         else
             eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee)
"""


def test_format_if_elif_comp_long_format():
    assert_render_pipeline(code_if_elif_comp_long, result_if_elif_comp_long)


code_gen_expr = """
let x = (for (let x in \nxs )  if (p(x))\n yield x)
"""
result_gen_expr = """
let x = (for(let x in xs) if(p(x)) yield x)
"""


def test_format_gen_expr_format():
    assert_render_pipeline(code_gen_expr, result_gen_expr)


code_gen_expr_long = """
let  xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx = (for (let x in xs) if (p(x)) yield x)
"""
result_gen_expr_long = """
let xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx = (for(let x in xs) if(p(x))
                                                          yield x)
"""


def test_format_gen_expr_long():
    assert_render_pipeline(code_gen_expr_long, result_gen_expr_long)


code_with_comp = """
let x = (with (resource) use_resource)
"""

result_with_comp = """
let x = (with(resource) use_resource)
"""


def test_format_with_comp():
    assert_render_pipeline(code_with_comp, result_with_comp)


code_with_comp_long = """
let xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  = (with (resource) use_resource)
"""
result_with_comp_long = """
let xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx = (with(resource)
                                                          use_resource)
"""


def test_format_with_comp_long():
    assert_render_pipeline(code_with_comp_long, result_with_comp_long)


code_let_comp = """
let x = (let y=\n1;y +1)
"""
result_let_comp = """
let x = (let y = 1; y + 1)
"""


def test_format_let_comp():
    assert_render_pipeline(code_let_comp, result_let_comp)


code_let_comp_pattern = """
let x = (let (a,b)=pair;a+b)
"""
result_let_comp_pattern = """
let x = (let (a, b) = pair; a + b)
"""


def test_format_let_comp_pattern():
    assert_render_pipeline(code_let_comp_pattern, result_let_comp_pattern)


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


code_type_alias = """
type Pair[T] = (T, T)
"""
result_type_alias = """
type Pair[T] = (T, T)
"""


def test_format_type_alias():
    assert_render_pipeline(code_type_alias, result_type_alias)


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


code_dict_set_slice_starred = """
let d = {"a":1, **m}
let s = {1,2,3}
let x = arr[1:10:2]
let y = [*xs,3]
"""
result_dict_set_slice_starred = """
let d = {"a": 1, **m}
let s = {1, 2, 3}
let x = arr[1:10:2]
let y = [*xs, 3]
"""


def test_format_dict_set_slice_starred():
    assert_render_pipeline(code_dict_set_slice_starred, result_dict_set_slice_starred)


code_fstring = """
let s = f"value={x}"
"""
result_fstring = """
let s = f"value={x}"
"""


def test_format_fstring():
    assert_render_pipeline(code_fstring, result_fstring)


code_fstring_long_expr = """
let s = f"value={very_long_function_name(aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa, bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb)}"
"""
result_fstring_long_expr = """
let s = f"value={very_long_function_name(
    aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa,
    bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
)}"
"""


def test_format_fstring_long_expr_wrap():
    assert_render_pipeline(code_fstring_long_expr, result_fstring_long_expr)


code_fstring_conversion = """
let s = f"debug={x!r}"
"""
result_fstring_conversion = """
let s = f"debug={x!r}"
"""


def test_format_fstring_conversion_r():
    assert_render_pipeline(code_fstring_conversion, result_fstring_conversion)


# TryStar (except*) tests
# -----------------------

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


# Type parameters tests
# ---------------------

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


code_type_alias_bound = """
type Vector[T: int] = list[T]
"""
result_type_alias_bound = """
type Vector[T: int] = list[T]
"""


def test_format_type_alias_bound():
    assert_render_pipeline(code_type_alias_bound, result_type_alias_bound)


code_nested_expr = """
let x = ([aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa, bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb, ccccccccccccccccccccccccccccccc], foo(aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa, bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb, ccccccccccccccccccccccccccccccc), (if (aaaaaaaaaaaaaaaaaaaaa) bbbbbbbbbbbbbbbbbbbb else ccccccccccccccccccccccccccccccc), [for (let yyyyyyyyyyyyyyyyy in zzzzzzzzzzzzzzzzzzzzzz) if (p(y)) yield yyyyyyyyyyyyyyyyy])
"""
result_nested_expr = """
let x = (
    [
        aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa,
        bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb,
        ccccccccccccccccccccccccccccccc
    ],
    foo(
        aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa,
        bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb,
        ccccccccccccccccccccccccccccccc
    ),
    (if(aaaaaaaaaaaaaaaaaaaaa)
         bbbbbbbbbbbbbbbbbbbb
     else
         ccccccccccccccccccccccccccccccc),
    [for(let yyyyyyyyyyyyyyyyy in zzzzzzzzzzzzzzzzzzzzzz) if(p(y))
         yield yyyyyyyyyyyyyyyyy]
)
"""


def test_format_nested_expr():
    assert_render_pipeline(code_nested_expr, result_nested_expr)
