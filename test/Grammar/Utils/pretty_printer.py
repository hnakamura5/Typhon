import ast

from Typhon.Grammar.pretty_printer import pretty_print_expr
from Typhon.Grammar.parser import parse_type
from Typhon.Grammar.typhon_ast import (
    get_empty_pos_attributes,
    make_arrow_type,
    make_record_literal,
    make_record_type,
)


def _name(id: str) -> ast.Name:
    pos = get_empty_pos_attributes()
    return ast.Name(id=id, ctx=ast.Load(), **pos)


def _arg(name: str, annotation: ast.expr | None) -> ast.arg:
    pos = get_empty_pos_attributes()
    return ast.arg(arg=name, annotation=annotation, **pos)


def test_pretty_print_expr_function_type_arrow():
    pos = get_empty_pos_attributes()
    node = make_arrow_type(
        args=[_arg("x", _name("int"))],
        star_etc=(_arg("args", _name("str")), _arg("kw", _name("bool"))),
        returns=ast.Constant(value=None, **pos),
        **pos,
    )

    assert pretty_print_expr(node) == "(x: int, *args: str, **kw: bool) -> None"


def test_pretty_print_expr_record_literal():
    pos = get_empty_pos_attributes()
    node = make_record_literal(
        fields=[
            (_name("a"), _name("int"), ast.Constant(value=1, **pos)),
            (_name("b"), None, ast.Constant(value="x", **pos)),
        ],
        **pos,
    )

    assert pretty_print_expr(node) == "{| a: int = 1, b = 'x' |}"


def test_pretty_print_expr_record_type():
    pos = get_empty_pos_attributes()
    node = make_record_type(
        fields=[
            (_name("x"), _name("int")),
            (_name("y"), _name("str")),
        ],
        **pos,
    )

    assert pretty_print_expr(node) == "{| x: int, y: str |}"


def test_pretty_print_expr_fallback_matches_unparse():
    node = parse_type("A | B")

    assert pretty_print_expr(node) == ast.unparse(node)


def test_pretty_print_expr_list_type_abbrev():
    node = parse_type("list[int]")

    assert pretty_print_expr(node) == "[int]"


def test_pretty_print_expr_tuple_type_abbrev():
    node = parse_type("tuple[str]")

    assert pretty_print_expr(node) == "(str)"


def test_pretty_print_expr_tuple_type_abbrev_multiple_elements():
    node = parse_type("tuple[str, int]")

    assert pretty_print_expr(node) == "(str, int)"


def test_pretty_print_expr_optional_type_abbrev():
    node = parse_type("T | None")

    assert pretty_print_expr(node) == "T?"


def test_pretty_print_expr_optional_type_abbrev_none_left():
    node = parse_type("None | T")

    assert pretty_print_expr(node) == "T?"


def test_pretty_print_comlex_expr_fallback():
    node = parse_type("tuple[list[T | None], int | str] | None")

    assert pretty_print_expr(node) == "([T?], int | str)?"


def test_pretty_print_complex_type_with_multiple_abbreviations_roundtrip_like():
    src = "tuple[list[T | None], tuple[str, int] | None] | None"
    node = parse_type(src)

    pretty = pretty_print_expr(node)
    assert pretty == "([T?], (str, int)?)?"


def test_parse_type_and_pretty_print_complex_abbrev():
    node = parse_type("tuple[list[T | None], tuple[str, int] | None] | None")

    assert pretty_print_expr(node) == "([T?], (str, int)?)?"


def test_parse_type_and_pretty_print_type_abbrevs():
    node = parse_type("tuple[list[int | None], tuple[str, int]]")

    assert pretty_print_expr(node) == "([int?], (str, int))"
