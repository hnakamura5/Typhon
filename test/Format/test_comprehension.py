from .format_assertion_utils import assert_render_pipeline


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
        ccccccccccccccccccccccccccccccc,
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
