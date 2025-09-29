from ..assertion_utils import (
    assert_ast_equals,
    show_token,
    assert_token,
    assert_ast_transform,
)

class_code = """
class MyClass {
    def method(self) {
        return;
    }
}
"""
class_result = """
class MyClass:

    def method(self):
        return
"""


def test_stmt_class():
    assert_ast_equals(class_code, class_result)


class_inherit_code = """
class MyClass(BaseClass) {
    var field: int;
    def method(self, x: int) -> int {
        return x + self.field;
    }
}
"""
class_inherit_result = """
class MyClass(BaseClass):
    field: int

    def method(self, x: int) -> int:
        return x + self.field
"""


def test_stmt_class_inherit():
    assert_ast_equals(class_inherit_code, class_inherit_result)


class_generic_code = """
class MyClass[T](T) {
    def method(self, x: T) -> T {
        return x;
    }
}
"""
class_generic_result = """
class MyClass[T](T):

    def method(self, x: T) -> T:
        return x
"""


def test_stmt_class_generic():
    assert_ast_equals(class_generic_code, class_generic_result)


class_member_code = """
class MyClass {
    var field: int = 10;
    let const_field: str = "hello";

    def method() {
        print(self.field);
        print(self.const_field);
    }
}
"""
class_member_result = """
class MyClass:
    field: int = 10
    const_field: str = 'hello'

    def method():
        print(self.field)
        print(self.const_field)
"""
class_member_transformed = """
from typing import Final as _typh_bi_Final

class MyClass:
    field: int = 10
    const_field: _typh_bi_Final[str] = 'hello'

    def method(self):
        print(self.field)
        print(self.const_field)
"""


def test_stmt_class_member():
    assert_ast_equals(class_member_code, class_member_result)
    assert_ast_transform(class_member_code, class_member_transformed)
