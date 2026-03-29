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


def test_render_pipeline_constant_preserves_raw_tokens():
    assert_render_pipeline(code_constant, result_constant)


code_expression = """
(1 + 2)
"""
result_expression = """
(1 + 2)
"""


def test_render_pipeline_expression_keeps_paren_tokens():
    assert_render_pipeline(code_expression, result_expression)


code_call = """
f(1, x=2)
"""
result_call = """
f(1, x=2)
"""


def test_render_pipeline_call_with_keywords():
    assert_render_pipeline(code_call, result_call)


code_record_literal = """
{|x = 1, y: str = '2'|}
"""
result_record_literal = """
{|x = 1, y: str = '2'|}
"""


def test_render_pipeline_record_literal():
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


def test_render_pipeline_if_block_newline_format():
    assert_render_pipeline(code_if_block, result_if_block)


code_function_block = """
def f(x: int) -> int { return x }
"""
result_function_block = """
def f(x: int) -> int {
    return x
}
"""


def test_render_pipeline_function_block_newline_format():
    assert_render_pipeline(code_function_block, result_function_block)


code_match_with_attributes_pattern = """
match (x) { case ({.a, .b = c}) { ok } }
"""
result_match_with_attributes_pattern = """
match (x) {
    case ({.a, .b = c}) {
        ok
    }
}
"""


def test_render_pipeline_match_with_attributes_pattern():
    assert_render_pipeline(
        code_match_with_attributes_pattern, result_match_with_attributes_pattern
    )


code_if_comp = """
let aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa = (if (a)   b else   c)
"""
result_if_comp = """
let aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa =
(if (a) b else c)
"""


def test_render_pipeline_if_comp_newline_format():
    assert_render_pipeline(code_if_comp, result_if_comp)
