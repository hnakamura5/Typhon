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
