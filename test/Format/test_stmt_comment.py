from .format_assertion_utils import assert_render_pipeline_comment_sensitive


code_leading_comment_inside_function = """
def f() {
    # body comment
    let x = 1
}
"""
result_leading_comment_inside_function = """
def f() {
    # body comment
    let x = 1
}
"""


def test_leading_comment_inside_function():
    assert_render_pipeline_comment_sensitive(
        code_leading_comment_inside_function,
        result_leading_comment_inside_function,
    )


code_trailing_comment_inside_function = """
def f() {
    let x = 1  # note
}
"""
result_trailing_comment_inside_function = """
def f() {
    let x = 1  # note
}
"""


def test_trailing_comment_inside_function():
    assert_render_pipeline_comment_sensitive(
        code_trailing_comment_inside_function,
        result_trailing_comment_inside_function,
    )


code_dangling_comment_in_empty_function = """
def f() {
    # todo
}
"""
result_dangling_comment_in_empty_function = """
def f() {
    # todo
}
"""


def test_dangling_comment_in_empty_function():
    assert_render_pipeline_comment_sensitive(
        code_dangling_comment_in_empty_function,
        result_dangling_comment_in_empty_function,
    )


code_leading_comment_before_function_def = """
# function note
def f() {
    pass
}
"""
result_leading_comment_before_function_def = """
# function note
def f() { pass }
"""


def test_leading_comment_before_function_def():
    assert_render_pipeline_comment_sensitive(
        code_leading_comment_before_function_def,
        result_leading_comment_before_function_def,
    )


code_trailing_comment_on_function_def = """
def f() {  # function trailing
    pass
}
"""
result_trailing_comment_on_function_def = """
def f() {
    # function trailing
    pass
}
"""


def test_trailing_comment_on_function_def():
    assert_render_pipeline_comment_sensitive(
        code_trailing_comment_on_function_def,
        result_trailing_comment_on_function_def,
    )


code_leading_comment_before_class_def = """
# class note
class C {
    pass
}
"""
result_leading_comment_before_class_def = """
# class note
class C { pass }
"""


def test_leading_comment_before_class_def():
    assert_render_pipeline_comment_sensitive(
        code_leading_comment_before_class_def,
        result_leading_comment_before_class_def,
    )


code_trailing_comment_on_class_def = """
class C {  # class trailing
    pass
}
"""
result_trailing_comment_on_class_def = """
class C {
    # class trailing
    pass
}
"""


def test_trailing_comment_on_class_def():
    assert_render_pipeline_comment_sensitive(
        code_trailing_comment_on_class_def,
        result_trailing_comment_on_class_def,
    )


code_class_bases_with_comments = """
class C(
    BaseA,  # base a
    #(base b)# BaseB,
) {
    pass
}
"""
result_class_bases_with_comments = """
class C(
    BaseA,  # base a
    #(base b)# BaseB,
) { pass }
"""


def test_class_bases_with_comments():
    assert_render_pipeline_comment_sensitive(
        code_class_bases_with_comments,
        result_class_bases_with_comments,
    )


code_function_params_with_comments = """
def f(
    a,  # first
    #(second)# b,
) {
    pass
}
"""
result_function_params_with_comments = """
def f(
    a,  # first
    #(second)# b
) { pass }
"""


def test_function_params_with_comments():
    assert_render_pipeline_comment_sensitive(
        code_function_params_with_comments,
        result_function_params_with_comments,
    )


code_class_type_params_with_comments = """
class Box[
    T,  # type t
    #(type u)# U,
] {
    pass
}
"""
result_class_type_params_with_comments = """
class Box[
    T,  # type t
    #(type u)# U,
] { pass }
"""


def test_class_type_params_with_comments():
    assert_render_pipeline_comment_sensitive(
        code_class_type_params_with_comments,
        result_class_type_params_with_comments,
    )


code_function_type_params_and_params_with_comments = """
def g[
    T,  # type t
    #(type u)# U,
](
    x,  # arg x
    #(arg y)# y,
) {
    pass
}
"""
result_function_type_params_and_params_with_comments = """
def g[
    T,  # type t
    #(type u)# U,
](
    x,  # arg x
    #(arg y)# y
) { pass }
"""


def test_function_type_params_and_params_with_comments():
    assert_render_pipeline_comment_sensitive(
        code_function_type_params_and_params_with_comments,
        result_function_type_params_and_params_with_comments,
    )


code_function_type_args_with_comments = """
type F = (
    a: int,  # first
    #(second)# b: str,
) -> bool
"""
result_function_type_args_with_comments = """
type F = (
    a: int,  # first
    #(second)# b: str
) -> bool
"""


def test_function_type_args_with_comments():
    assert_render_pipeline_comment_sensitive(
        code_function_type_args_with_comments,
        result_function_type_args_with_comments,
    )
