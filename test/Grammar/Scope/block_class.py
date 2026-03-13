from ..assertion_utils import assert_transform


block_class_code = """
class A {
    def f() {
        var A = 10;
        print(A);
    }
}
var a = A();
"""
block_class_result = """
class A:

    def f(self):
        $A1 = 10
        print($A1)
a = A()
"""


def test_block_class():
    assert_transform(block_class_code, block_class_result)


block_class_nested_code = """
class A {
    class B {
        def f() {
            var A = 10;
            print(A);
        }
    }
    def g() {
        var b = B();
        var B = 20;
        print(B);
    }
}
var a = A();
a.g();
"""
block_class_nested_result = """
class A:

    class B:

        def f(self):
            $A1 = 10
            print($A1)

    def g(self):
        b = B()
        $B1 = 20
        print($B1)
a = A()
a.g()
"""


def test_block_class_nested():
    assert_transform(block_class_nested_code, block_class_nested_result)


block_class_not_renamed_code = """
var x: int = 10;
class A {
    var x:int
    def f() {
        print(x);
    }
}
"""

block_class_not_renamed_result = """
x: int = 10

class A:
    x: int

    def f(self):
        print(x)
"""


def test_block_class_not_renamed():
    assert_transform(block_class_not_renamed_code, block_class_not_renamed_result)


block_class_const_to_property_code = """
class A {
    let x: int = 10;
    def f() {
        print(self.x);
    }
}
"""

block_class_const_to_property_result = """
from typing import Final as _typh_bi_Final

class A:
    x: _typh_bi_Final[int] = 10

    def f(self):
        print(self.x)
"""


def test_block_class_const_to_property():
    assert_transform(
        block_class_const_to_property_code, block_class_const_to_property_result
    )


block_class_const_nested_code = """
class A {
    let x: int = 10;
    class B {
        let x: int = 20;
        def g() {
            print(self.x);
        }
    }
    def f() {
        print(self.x);
    }
}
"""
block_class_const_nested_result = """
from typing import Final as _typh_bi_Final

class A:
    x: _typh_bi_Final[int] = 10

    class B:
        x: _typh_bi_Final[int] = 20

        def g(self):
            print(self.x)

    def f(self):
        print(self.x)
"""


def test_block_class_const_nested():
    assert_transform(block_class_const_nested_code, block_class_const_nested_result)
