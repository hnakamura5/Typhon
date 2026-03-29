import ast

from Typhon.Format.doc_datatype import (
    Align,
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


def _render_doc(doc: Doc) -> str:
    if isinstance(doc, Nil):
        return ""
    if isinstance(doc, Text):
        return doc.value
    if isinstance(doc, Line):
        if doc.mode == LineMode.SOFT:
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


def test_translate_constant_preserves_raw_tokens():
    module = _parse_module("1_000")

    doc = print_to_doc(module)

    assert _render_doc(doc) == "1_000"


def test_translate_group_expr_preserves_wrapper_paren_tokens():
    module = _parse_module("(1 + 2)")

    doc = print_to_doc(module)

    assert _render_doc(doc) == "(1 + 2)"


def test_translate_module_statements_with_newline_separator():
    module = _parse_module("a\nb")

    doc = print_to_doc(module)

    assert _render_doc(doc) == "a\nb"


def test_translate_call_with_keyword_argument():
    module = _parse_module("f(1, x=2)")

    doc = print_to_doc(module)

    assert _render_doc(doc) == "f(1, x=2)"


def test_translate_if_stmt_to_typhon_style_block_doc():
    module = _parse_module("if (a) { b } else { c }")

    doc = print_to_doc(module)

    assert _render_doc(doc) == "if (a) {\nb\n} else {\nc\n}"


def test_translate_class_stmt_to_typhon_style_block_doc():
    module = _parse_module("class C { pass }")

    doc = print_to_doc(module)

    assert _render_doc(doc) == "class C { pass }"


def test_translate_function_stmt_to_typhon_style_block_doc():
    module = _parse_module("def f(x: int) -> int { return x }")

    doc = print_to_doc(module)

    assert _render_doc(doc) == "def f(x: int) -> int {\nreturn x\n}"


def test_translate_while_stmt_to_typhon_style_block_doc():
    module = _parse_module("while (ok) { work }")

    doc = print_to_doc(module)

    assert _render_doc(doc) == "while (ok) {\nwork\n}"


def test_translate_for_stmt_to_typhon_style_block_doc():
    module = _parse_module("for (let x in xs) { work }")

    doc = print_to_doc(module)

    assert _render_doc(doc) == "for (let x in xs) {\nwork\n}"


def test_translate_with_stmt_to_typhon_style_block_doc():
    module = _parse_module("with (resource) { use }")

    doc = print_to_doc(module)

    assert _render_doc(doc) == "with ((resource)) {\nuse\n}"


def test_translate_try_stmt_to_typhon_style_block_doc():
    module = _parse_module(
        "try { work } except (Error as e) { recover } finally { cleanup }"
    )

    doc = print_to_doc(module)

    assert (
        _render_doc(doc)
        == "try {\nwork\n} except (Error as e) {\nrecover\n} finally {\ncleanup\n}"
    )


def test_translate_match_stmt_to_typhon_style_block_doc():
    module = _parse_module("match (x) { case (1) { a } case (_) { b } }")

    doc = print_to_doc(module)

    assert _render_doc(doc) == "match (x) {\ncase (1) {\na\n}\ncase (_) {\nb\n}\n}"


def test_translate_match_stmt_with_class_pattern_doc():
    module = _parse_module("match (x) { case (Point(a, y=b)) { ok } }")

    doc = print_to_doc(module)

    assert _render_doc(doc) == "match (x) {\ncase (Point(a, y = b)) {\nok\n}\n}"


def test_translate_match_stmt_with_attributes_pattern_doc():
    module = _parse_module("match (x) { case ({.a, .b = c}) { ok } }")

    doc = print_to_doc(module)

    assert _render_doc(doc) == "match (x) {\ncase ({.a, .b = c}) {\nok\n}\n}"
