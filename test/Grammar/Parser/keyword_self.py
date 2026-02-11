from ..assertion_utils import assert_parse, show_token, assert_transform_ast

def_self_code = """
class A {
    def f(x) {
        return self;
    }
}
var a = A();
"""
def_self_result = """
class A:

    def f(x):
        return self
a = A()
"""
def_self_transformed = """
class A:

    def f(self, x):
        return self
a = A()
"""


def test_def_self():
    parsed = assert_parse(def_self_code, def_self_result)
    assert_transform_ast(parsed, def_self_transformed)


async_def_self_code = """
class A {
    async def f(x) {
        return self;
    }
}
var a = A();
"""
async_def_self_result = """
class A:

    async def f(x):
        return self
a = A()
"""
async_def_self_transformed = """
class A:

    async def f(self, x):
        return self
a = A()
"""


def test_async_def_self():
    parsed = assert_parse(async_def_self_code, async_def_self_result)
    assert_transform_ast(parsed, async_def_self_transformed)


static_def_no_self_code = """
class A {
    static def f(x) {
        return x;
    }
}
"""
static_def_no_self_result = """
class A:

    def f(x):
        return x
"""
static_def_no_self_transformed = """
class A:

    def f(x):
        return x
"""


def test_static_def_no_self():
    parsed = assert_parse(static_def_no_self_code, static_def_no_self_result)
    assert_transform_ast(parsed, static_def_no_self_transformed)


func_literal_no_self_code = """
class A {
    var f = (x) => x + 1;
}
"""
func_literal_no_self_result = """
class A:
    f = lambda x: x + 1
"""
func_literal_no_self_transformed = """
class A:
    f = lambda x: x + 1
"""


def test_func_literal_no_self():
    parsed = assert_parse(func_literal_no_self_code, func_literal_no_self_result)
    assert_transform_ast(parsed, func_literal_no_self_transformed)


def_nested_self_no_code = """
class A {
    def f(x) {
        def g(y) {
            return self;
        }
    }
}
"""
def_nested_self_result = """
class A:

    def f(x):

        def g(y):
            return self
"""
def_nested_self_transformed = """
class A:

    def f(self, x):

        def g(y):
            return self
"""


def test_def_nested_self():
    parsed = assert_parse(def_nested_self_no_code, def_nested_self_result)
    assert_transform_ast(parsed, def_nested_self_transformed)


def_nested_class_self_code = """
class A {
    def f(x) {
        class B {
            def g(y) {
                return self;
            }
        }
    }
}
"""
def_nested_class_self_result = """
class A:

    def f(x):

        class B:

            def g(y):
                return self
"""
def_nested_class_self_transformed = """
class A:

    def f(self, x):

        class B:

            def g(self, y):
                return self
"""


def test_def_nested_class_self():
    parsed = assert_parse(def_nested_class_self_code, def_nested_class_self_result)
    assert_transform_ast(parsed, def_nested_class_self_transformed)
