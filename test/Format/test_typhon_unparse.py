import ast

from Typhon.Format.typhon_unparse import typhon_unparse
from Typhon.Grammar.parser import parse_string
from Typhon.Grammar.typhon_ast import set_control_comprehension_def


def _parse_module(source: str) -> ast.Module:
    parsed = parse_string(source, mode="exec")
    assert isinstance(parsed, ast.Module)
    return parsed


def _assert_roundtrip_equal(source: str, unparsed: str) -> None:
    first = typhon_unparse(_parse_module(source))
    assert first.strip() == unparsed.strip(), f"Roundtrip failed: {first} != {unparsed}"
    second = typhon_unparse(_parse_module(first))
    assert first == second


def test_unparse_declaration_and_logical_ops():
    source = """
let a = 1, b: int = 2
if (a > 0 && !False) {
    a += 1
}
"""
    unparsed = """
let a = 1, b: int = 2
if (((a > 0) && (!False))) {
    a += 1
}
"""
    _assert_roundtrip_equal(source, unparsed)


def test_unparse_optional_and_coalescing():
    source = """
a?.b?(1)?[0] ?? c
x?
y!
"""
    unparsed = """
a?.b?(1)?[0] ?? c
x?
y!
"""
    _assert_roundtrip_equal(source, unparsed)


def test_unparse_if_let_let_else_while_let():
    source = """
if (let x = foo()) {
    use(x)
}
let [a, b] = pair() else {
    return
}
while (let y = next_item()) {
    use(y)
}
"""
    unparsed = """
if (let x = foo()) {
    use(x)
}
let [a, b] = pair() else {
    return
}
while (let y = next_item()) {
    use(y)
}
"""
    _assert_roundtrip_equal(source, unparsed)


def test_unparse_static_function_and_class():
    source = """
class Math {
    static def add(x: int, y: int) -> int {
        return x + y
    }
}
"""
    unparsed = """
class Math {
    static def add(x: int, y: int) -> int {
        return (x + y)
    }
}
"""
    _assert_roundtrip_equal(source, unparsed)


def test_unparse_with_statement():
    source = """
with (let f: File = open(path)) {
    data = f.read()
}
"""
    unparsed = """
with (let f: File = open(path)) {
    data = f.read()
}
"""
    _assert_roundtrip_equal(source, unparsed)


def test_unparse_match_statement():
    source = """
match (value) {
    case (Point(x = x, y = y)) {
        out = x
    }
    case (_) {
        out = 0
    }
}
"""
    unparsed = """
match (value) {
    case (Point(x = x, y = y)) {
        out = x
    }
    case (_) {
        out = 0
    }
}
"""
    _assert_roundtrip_equal(source, unparsed)


def test_unparse_try_statement():
    source = """
try {
    run()
} except (ValueError) {
    handle()
} finally {
    cleanup()
}
"""
    unparsed = """
try {
    run()
} except (ValueError) {
    handle()
} finally {
    cleanup()
}
"""
    _assert_roundtrip_equal(source, unparsed)


def test_unparse_additional_expressions():
    source = """
let tup = (1, 2, 3)
let d = {"a": 1, "b": 2}
let s = {1, 2, 3}
let z = (a + b) * (c - d)
let c = a?.b?(1)?[0] ?? fallback
assert z > 0, "bad"
"""
    unparsed = """
let tup = (1, 2, 3)
let d = {"a": 1, "b": 2}
let s = {1, 2, 3}
let z = ((a + b) * (c - d))
let c = a?.b?(1)?[0] ?? fallback
assert (z > 0), "bad"
"""
    _assert_roundtrip_equal(source, unparsed)


def test_unparse_control_comprehensions_source_syntax():
    source = """
let v1 = (with (let f = open("x")) f.read())
let v2 = (try 1/0 except (ZeroDivisionError as e) 0)
let v3 = (match (p) case (Point(a, b)) a + b)
let v4 = (let x = 1, y = 2; x + y)
let v5 = (while (True) yield 1)
"""
    unparsed = """
let v1 = (with (let f = open("x")) f.read())
let v2 = (try (1 / 0) except (ZeroDivisionError as e) 0 )
let v3 = (match (p) case (Point(a, b)) (a + b) )
let v4 = (let x = 1, y = 2; (x + y))
let v5 = (while (True) yield 1)
"""
    _assert_roundtrip_equal(source, unparsed)


def test_unparse_nested_control_comprehensions_source_syntax():
    source = """
let v1 = (with (let f = open("x")) (try f.read() except (Exception as e) ""))
let v2 = (try (match (p) case (Point(a, b)) a + b) except (Exception as e) 0)
let v3 = (let x = 1; (with (let f = open("x")) f.read()))
let v4 = (let x = 1; (while (x > 0) yield x))
let v5 = (with (let f = open("x")) (while (True) yield f.read()))
"""
    unparsed = """
let v1 = (with (let f = open("x")) (try f.read() except (Exception as e) "" ))
let v2 = (try (match (p) case (Point(a, b)) (a + b) ) except (Exception as e) 0 )
let v3 = (let x = 1; (with (let f = open("x")) f.read()))
let v4 = (let x = 1; (while ((x > 0)) yield x))
let v5 = (with (let f = open("x")) (while (True) yield f.read()))
"""
    _assert_roundtrip_equal(source, unparsed)


def test_unparse_control_comprehension_invalid_shape_raises_error():
    control_name = ast.Name(id="__bad_control", ctx=ast.Load())
    control_func = ast.FunctionDef(
        name="__bad_control",
        args=ast.arguments(
            posonlyargs=[],
            args=[],
            vararg=None,
            kwonlyargs=[],
            kw_defaults=[],
            kwarg=None,
            defaults=[],
        ),
        body=[ast.Pass()],
        decorator_list=[],
    )
    set_control_comprehension_def(control_name, control_func)
    module = ast.Module(
        body=[
            ast.Assign(targets=[ast.Name(id="x", ctx=ast.Store())], value=control_name)
        ],
        type_ignores=[],
    )
    try:
        typhon_unparse(module)
    except ValueError:
        return
    assert False, "Expected ValueError for unsupported control comprehension shape"
