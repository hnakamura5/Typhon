from ..assertion_utils import (
    assert_parse,
    show_token,
    assert_token,
    assert_transform,
    assert_parse_error_recovery,
    Range,
    Pos,
    with_parser_verbose,
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
    assert_parse(class_code, class_result)


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
    assert_parse(class_inherit_code, class_inherit_result)


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
    assert_parse(class_generic_code, class_generic_result)


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
    assert_parse(class_member_code, class_member_result)
    assert_transform(class_member_code, class_member_transformed)


class_nameless_code = """
class {
    def method(self) {
        return;
    }
}
"""
class_nameless_recover = """
class _typh_invalid_name:

    def method(self):
        return
"""


def test_stmt_class_nameless():
    assert_parse_error_recovery(
        class_nameless_code,
        class_nameless_recover,
        [("expected class name", Range(Pos(1, 5), Pos(1, 6)))],
    )


class_base_parenless_code = """
class C (Base {
}
"""
class_base_parenless_recover = """
class C(Base):
    pass
"""


def test_stmt_class_base_parenless():
    assert_parse_error_recovery(
        class_base_parenless_code,
        class_base_parenless_recover,
        [
            ("expected ')'", Range(Pos(1, 13), Pos(1, 14))),
        ],
    )


class_braceless_code = """
class MyClass {
    def method(self) {
        return;
    }
"""
class_braceless_recover = """
class MyClass:

    def method(self):
        return
"""


def test_stmt_class_braceless():
    assert_parse_error_recovery(
        class_braceless_code,
        class_braceless_recover,
        [("expected '}'", Range(Pos(4, 5), Pos(4, 6)))],
    )
