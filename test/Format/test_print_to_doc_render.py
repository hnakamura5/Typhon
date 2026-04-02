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


def assert_render_pipeline(source: str, expected: str) -> None:
    result = _render_source(source)
    assert result == expected.strip(), f"Expected:\n{expected}\n\nGot:\n{result}"


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
