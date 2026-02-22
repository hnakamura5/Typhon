from ...assertion_utils import assert_ast_match_unparse_code, assert_source_map_ident


def test_match_for_if():
    def left_func(x: int) -> int:
        y = 0
        for i in range(x):
            if i % 2 == 0:
                y += i
        return y

    assert_ast_match_unparse_code(left_func)
    assert_source_map_ident(left_func)


def test_match_nested_func():
    def left_func(x: int) -> int:
        def nested_func1(y: int) -> int:
            return y * 2

        def nested_func2(z: int) -> int:
            return z + 3

        return nested_func1(x) + nested_func2(x)

    assert_ast_match_unparse_code(left_func)
    assert_source_map_ident(left_func)


def test_match_class_with_method():
    class A:
        def method1(self, x: int) -> int:
            return x + 1

        def method2(self, y: int) -> int:
            return y * 2

    assert_ast_match_unparse_code(A)
    assert_ast_match_unparse_code(A.method1)
    assert_ast_match_unparse_code(A.method2)
    assert_source_map_ident(A)


def test_match_try_except():
    def left_func(x: int) -> int:
        try:
            return 10 // x
        except ZeroDivisionError:
            return 0

    assert_ast_match_unparse_code(left_func)
    assert_source_map_ident(left_func)


def test_match_with_statement():
    def left_func(file_path: str) -> str:
        with open(file_path, "r") as f:
            content = f.read()
        return content

    assert_ast_match_unparse_code(left_func)
    assert_source_map_ident(left_func)


def test_match_import_from():
    def left_func():
        from ...SourceMap.matching.python_exp import test_match_python_arithmetic

    assert_ast_match_unparse_code(left_func)
    assert_source_map_ident(left_func)


def test_match_return_type_annotation():
    def left_func(x: int):
        return x * 2

    assert_ast_match_unparse_code(left_func)
    assert_source_map_ident(left_func)
