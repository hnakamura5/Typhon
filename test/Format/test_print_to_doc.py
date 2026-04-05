import ast

from Typhon.Format.doc_datatype import (
    Align,
    AlignToAnchor,
    Anchor,
    BreakParent,
    Concat,
    Doc,
    Fill,
    Group,
    IfBreak,
    Indent,
    Line,
    LineMode,
    LineSuffix,
    LineSuffixBoundary,
    Nil,
    Text,
    Trim,
)
from Typhon.Format.print_to_doc import print_to_doc
from Typhon.Grammar.parser import parse_string
from Typhon.Driver.debugging import debug_verbose_print


# Pserdo rendering of Doc to string for testing purposes.
def _render_doc(doc: Doc) -> str:
    if isinstance(doc, Nil):
        return ""
    if isinstance(doc, Text):
        return doc.value
    if isinstance(doc, Line):
        if doc.mode == LineMode.SOFT:
            return ""
        if doc.mode == LineMode.LINE:
            return " "
        return "\n"
    if isinstance(doc, Concat):
        return "".join(_render_doc(part) for part in doc.parts)
    if isinstance(doc, Group):
        return _render_doc(doc.content)
    if isinstance(doc, Indent):
        return _render_doc(doc.content)
    if isinstance(doc, Align):
        return _render_doc(doc.content)
    if isinstance(doc, Anchor):
        return _render_doc(doc.content)
    if isinstance(doc, AlignToAnchor):
        return _render_doc(doc.content)
    if isinstance(doc, Fill):
        return _render_doc(Concat(parts=doc.parts))
    if isinstance(doc, IfBreak):
        branch = (
            doc.flat_contents if doc.flat_contents is not None else doc.break_contents
        )
        return _render_doc(branch) if branch is not None else ""
    if isinstance(doc, LineSuffix):
        return _render_doc(doc.content)
    if isinstance(doc, LineSuffixBoundary):
        return ""
    if isinstance(doc, BreakParent):
        return ""
    if isinstance(doc, Trim):
        return ""
    raise AssertionError(f"Unsupported Doc node: {type(doc)}")


def _parse_module(source: str) -> ast.Module:
    parsed = parse_string(source, mode="exec")
    assert isinstance(parsed, ast.Module)
    return parsed


def assert_rendered_doc_ident(source: str):
    module = _parse_module(source)
    doc = print_to_doc(module)
    assert _render_doc(doc) == source


def assert_rendered_doc_equal(source: str, expected: str):
    module = _parse_module(source)
    doc = print_to_doc(module)
    assert _render_doc(doc) == expected


def test_translate_constant_preserves_raw_tokens():
    assert_rendered_doc_ident("1_000")


def test_translate_group_expr_preserves_wrapper_paren_tokens():
    assert_rendered_doc_ident("(1 + 2)")


def test_translate_module_statements_with_newline_separator():
    assert_rendered_doc_ident("a\nb")


def test_translate_call_with_keyword_argument():
    assert_rendered_doc_ident("f(1, x=2)")


def test_translate_record_literal_doc():
    assert_rendered_doc_ident("{|x = 1, y: str = '2'|}")


def test_translate_record_type_doc():
    assert_rendered_doc_ident("def f(x: {|id: int, name: str|}) { pass }")


def test_translate_list_comprehension_doc():
    assert_rendered_doc_ident("[for(var x: int in xs) if(x > 0) yield x]")


def test_translate_dict_comprehension_doc():
    assert_rendered_doc_ident("{async for(var k in ks) yield k: v}")


def test_translate_if_stmt_to_typhon_style_block_doc():
    assert_rendered_doc_equal("if (a) { b } else { c }", "if (a) {\nb\n} else {\nc\n}")


def test_translate_class_stmt_to_typhon_style_block_doc():
    assert_rendered_doc_ident("class C { pass }")


def test_translate_function_stmt_to_typhon_style_block_doc():
    assert_rendered_doc_equal(
        "def f(x: int) -> int { return x }", "def f(x: int) -> int {\nreturn x\n}"
    )


def test_translate_while_stmt_to_typhon_style_block_doc():
    assert_rendered_doc_equal("while (ok) { work }", "while (ok) {\nwork\n}")


def test_translate_for_stmt_to_typhon_style_block_doc():
    assert_rendered_doc_equal(
        "for (let x in xs) { work }", "for (let x in xs) {\nwork\n}"
    )


def test_translate_with_stmt_to_typhon_style_block_doc():
    assert_rendered_doc_equal("with (resource) { use }", "with (resource) {\nuse\n}")


def test_translate_try_stmt_to_typhon_style_block_doc():
    assert_rendered_doc_equal(
        "try { work } except (Error as e) { recover } finally { cleanup }",
        "try {\nwork\n} except (Error as e) {\nrecover\n} finally {\ncleanup\n}",
    )


def test_translate_match_stmt_to_typhon_style_block_doc():
    assert_rendered_doc_equal(
        "match (x) { case (1) { a } case (_) { b } }",
        "match (x) {\ncase (1) {\na\n}\ncase (_) {\nb\n}\n}",
    )


def test_translate_match_stmt_with_class_pattern_doc():
    assert_rendered_doc_equal(
        "match (x) { case (Point(a, y=b)) { ok } }",
        "match (x) {\ncase (Point(a, y = b)) {\nok\n}\n}",
    )


def test_translate_match_stmt_with_attributes_pattern_doc():
    assert_rendered_doc_equal(
        "match (x) { case ({.a, .b = c}) { ok } }",
        "match (x) {\ncase ({.a, .b = c}) {\nok\n}\n}",
    )
