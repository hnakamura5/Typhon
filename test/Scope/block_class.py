from ..assertion_utils import assert_ast_transform


block_class_code = """
class A {
    def f() {
        let A = 10;
        print(A);
    }
}
let a = A();
"""
block_class_result = """
class A:

    def f(self):
        _typh_cn_f2_0_A = 10
        print(_typh_cn_f2_0_A)
a = A()
"""


def test_block_class():
    assert_ast_transform(block_class_code, block_class_result)


block_class_nested_code = """
class A {
    class B {
        def f() {
            let A = 10;
            print(A);
        }
    }
    def g() {
        let b = B();
        let B = 20;
        print(B);
    }
}
let a = A();
a.g();
"""
block_class_nested_result = """
class A:

    class B:

        def f(self):
            _typh_cn_f3_0_A = 10
            print(_typh_cn_f3_0_A)

    def g(self):
        b = B()
        _typh_cn_f4_0_B = 20
        print(_typh_cn_f4_0_B)
a = A()
a.g()
"""


def test_block_class_nested():
    assert_ast_transform(block_class_nested_code, block_class_nested_result)


block_class_not_renamed_code = """
var x: int = 10;
class A {
    let x:int
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
    assert_ast_transform(block_class_not_renamed_code, block_class_not_renamed_result)
