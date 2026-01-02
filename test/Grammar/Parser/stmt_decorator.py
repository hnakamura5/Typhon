from ..assertion_utils import (
    assert_parse,
    assert_transform_ast,
    with_parser_verbose,
)

decorator_func_code = """
from decorators import decorator, another_decorator

@decorator(
    "arg1",
    "arg2"
)
@another_decorator
def f(x: int) -> int {
    return x + 1
}
"""
decorator_func_result = """
from decorators import decorator, another_decorator

@decorator('arg1', 'arg2')
@another_decorator
def f(x: int) -> int:
    return x + 1
"""
decorator_func_transformed = """
from decorators import decorator, another_decorator

@decorator('arg1', 'arg2')
@another_decorator
def f(x: int) -> int:
    return x + 1
"""


def test_decorator_func():
    parsed = assert_parse(decorator_func_code, decorator_func_result)
    assert_transform_ast(parsed, decorator_func_transformed)


decorator_class_code = """
from decorators import class_decorator, another_class_decorator

@another_class_decorator
@class_decorator(
    "class_arg1",
    "class_arg2"
)
class MyClass {
}
"""
decorator_class_result = """
from decorators import class_decorator, another_class_decorator

@another_class_decorator
@class_decorator('class_arg1', 'class_arg2')
class MyClass:
    pass
"""
decorator_class_transformed = """
from decorators import class_decorator, another_class_decorator

@another_class_decorator
@class_decorator('class_arg1', 'class_arg2')
class MyClass:
    pass
"""


def test_decorator_class():
    parsed = assert_parse(decorator_class_code, decorator_class_result)
    assert_transform_ast(parsed, decorator_class_transformed)
