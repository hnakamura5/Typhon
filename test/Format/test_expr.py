from .format_assertion_utils import assert_render_pipeline


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


code_pipe_operator_leading_break = """
let x = aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa ?|> bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb |> cccccccccccccccccccccccccccccccccccccccccccc
"""
result_pipe_operator_leading_break = """
let x = aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        ?|> bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
        |> cccccccccccccccccccccccccccccccccccccccccccc
"""


def test_format_pipe_operator_leading_break():
    assert_render_pipeline(
        code_pipe_operator_leading_break, result_pipe_operator_leading_break
    )


code_call = """
f(1, x=2)
"""
result_call = """
f(1, x=2)
"""


def test_format_call_with_keywords():
    assert_render_pipeline(code_call, result_call)


code_call_with_trailing_comma = """
let x = f(1, 2,)
"""
result_call_with_trailing_comma = """
let x = f(
    1,
    2,
)
"""


def test_format_call_with_trailing_comma_forces_multiline():
    assert_render_pipeline(
        code_call_with_trailing_comma, result_call_with_trailing_comma
    )


code_call_with_kw_trailing_comma = """
let x = f(a=1, b=2,)
"""
result_call_with_kw_trailing_comma = """
let x = f(
    a=1,
    b=2,
)
"""


def test_format_call_with_kw_trailing_comma_forces_multiline():
    assert_render_pipeline(
        code_call_with_kw_trailing_comma, result_call_with_kw_trailing_comma
    )


code_list_with_trailing_comma = """
let x = [1,2,]
"""
result_list_with_trailing_comma = """
let x = [
    1,
    2,
]
"""


def test_format_list_with_trailing_comma():
    assert_render_pipeline(
        code_list_with_trailing_comma, result_list_with_trailing_comma
    )


code_tuple_with_trailing_comma = """
let x = (1,2,)
"""
result_tuple_with_trailing_comma = """
let x = (
    1,
    2,
)
"""


def test_format_tuple_with_trailing_comma():
    assert_render_pipeline(
        code_tuple_with_trailing_comma, result_tuple_with_trailing_comma
    )


code_set_with_trailing_comma = """
let x = {1,2,}
"""
result_set_with_trailing_comma = """
let x = {
    1,
    2,
}
"""


def test_format_set_with_trailing_comma():
    assert_render_pipeline(code_set_with_trailing_comma, result_set_with_trailing_comma)


code_dict_with_trailing_comma = """
let x = {"a":1, "b":2,}
"""
result_dict_with_trailing_comma = """
let x = {
    "a": 1,
    "b": 2,
}
"""


def test_format_dict_with_trailing_comma():
    assert_render_pipeline(
        code_dict_with_trailing_comma, result_dict_with_trailing_comma
    )


code_subscript_with_trailing_comma = """
let x = arr[1,2,]
"""
result_subscript_with_trailing_comma = """
let x =
    arr[
        1,
        2,
    ]
"""


def test_format_subscript_with_trailing_comma():
    assert_render_pipeline(
        code_subscript_with_trailing_comma,
        result_subscript_with_trailing_comma,
    )


code_tuple_subscript_with_trailing_comma = """
let x = arr[(1,2),]
"""
result_tuple_subscript_with_trailing_comma = """
let x =
    arr[
        (1, 2),
    ]
"""


def test_format_tuple_subscript_with_trailing_comma():
    assert_render_pipeline(
        code_tuple_subscript_with_trailing_comma,
        result_tuple_subscript_with_trailing_comma,
    )


code_record_literal_with_trailing_comma = """
let x = {|x=1, y=2,|}
"""
result_record_literal_with_trailing_comma = """
let x = {|
    x = 1,
    y = 2,
|}
"""


def test_format_record_literal_with_trailing_comma():
    assert_render_pipeline(
        code_record_literal_with_trailing_comma,
        result_record_literal_with_trailing_comma,
    )


code_record_type_with_trailing_comma = """
let x : {|x:int, y:int,|} = foo()
"""
result_record_type_with_trailing_comma = """
let x: {|
    x: int,
    y: int,
|} = foo()
"""


def test_format_record_type_with_trailing_comma():
    assert_render_pipeline(
        code_record_type_with_trailing_comma,
        result_record_type_with_trailing_comma,
    )


code_loag_call = """
let x = f(aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa, aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa)
"""

result_long_call = """
let x = f(
    aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa,
    aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa,
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


code_attribute = """
let x = obj.attribute_name
"""
result_attribute = """
let x = obj.attribute_name
"""


def test_format_attribute():
    assert_render_pipeline(code_attribute, result_attribute)


code_attribute_long_wrap = """
let x = aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb(x)
"""
result_attribute_long_wrap = """
let x = aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
.bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb(x)
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
    yyyyyyyyyy,
)
.bbbbbbbbbbbbbbbbbbbb(xxxxxxxxx, yyyyyyyyyy)
?.ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc(
    xxxxxxxxx,
    yyyyyyyyyy,
)
"""


def test_format_method_chain_long_wrap():
    assert_render_pipeline(code_method_chain_long_wrap, result_method_chain_long_wrap)


code_type_alias = """
type Pair[T] = (T, T)
"""
result_type_alias = """
type Pair[T] = (T, T)
"""


def test_format_type_alias():
    assert_render_pipeline(code_type_alias, result_type_alias)


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
    bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb,
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


code_type_alias_bound = """
type Vector[T: int] = list[T]
"""
result_type_alias_bound = """
type Vector[T: int] = list[T]
"""


def test_format_type_alias_bound():
    assert_render_pipeline(code_type_alias_bound, result_type_alias_bound)
