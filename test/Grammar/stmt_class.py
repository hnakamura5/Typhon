from .assertion_utils import assert_ast_equals, show_token, assert_token

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
    field: int;
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
