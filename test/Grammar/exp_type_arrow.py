from .assertion_utils import assert_ast_equals, show_token

type_arrow_annot_code = """
x: (int) -> int;
"""
type_arrow_annot_result = """
x: arrow_type
"""


def test_type_arrow_annot():
    show_token(type_arrow_annot_code)
    assert_ast_equals(type_arrow_annot_code, type_arrow_annot_result)


type_arrow_param_annot_code = """
a: (x: int, y: str) -> int;
"""
type_arrow_param_annot_result = """
a: arrow_type
"""


def test_type_arrow_param_annot():
    show_token(type_arrow_param_annot_code)
    assert_ast_equals(type_arrow_param_annot_code, type_arrow_param_annot_result)


type_arrow_def_param_code = """
def h(x: int, f: (int) -> int) -> int {
    return f(x);
}
"""
type_arrow_def_param_result = """
def h(x: int, f: arrow_type) -> int:
    return f(x)
"""


def test_type_arrow_def_param():
    show_token(type_arrow_def_param_code)
    assert_ast_equals(type_arrow_def_param_code, type_arrow_def_param_result)


type_arrow_func_literal_code = """
f: (x: int) -> int = (x:int) -> int => {
    return x + 1;
};
"""
type_arrow_func_literal_result = """
f: arrow_type = temp
"""


def test_type_arrow_func_literal():
    show_token(type_arrow_func_literal_code)
    assert_ast_equals(type_arrow_func_literal_code, type_arrow_func_literal_result)
