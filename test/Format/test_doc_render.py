from Typhon.Format.doc_datatype import (
    BreakParent,
    Concat,
    Cursor,
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
    concat,
    group,
    indent,
    line,
    text,
)
from Typhon.Format.doc_render import render_doc_to_string


def test_render_nil():
    assert render_doc_to_string(Nil()) == ""


def test_render_text():
    assert render_doc_to_string(Text("hello")) == "hello"


def test_render_hardline():
    doc = Concat([Text("a"), Line(LineMode.HARD), Text("b")])
    assert render_doc_to_string(doc) == "a\nb"


def test_render_line_is_space_in_flat_mode():
    doc = Group(Concat([Text("a"), Line(LineMode.LINE), Text("b")]))
    assert render_doc_to_string(doc) == "a b"


def test_render_line_breaks_in_break_mode():
    doc = Group(
        Concat([Text("a"), Line(LineMode.LINE), Text("b")]),
        should_break=True,
    )
    assert render_doc_to_string(doc) == "a\nb"


def test_group_fits_flat():
    doc = Group(Concat([Text("a"), Line(LineMode.SOFT), Text("b")]))
    assert render_doc_to_string(doc) == "ab"


def test_group_breaks_when_too_long():
    long_text = "x" * 81
    doc = Group(Concat([Text(long_text), Line(LineMode.SOFT), Text("y")]))
    assert render_doc_to_string(doc) == long_text + "\ny"


def test_group_should_break_forces_break():
    doc = Group(
        Concat([Text("a"), Line(LineMode.SOFT), Text("b")]),
        should_break=True,
    )
    assert render_doc_to_string(doc) == "a\nb"


def test_indent_applies_after_break():
    inner = Concat([Text("a"), Line(LineMode.SOFT), Text("b")])
    doc = Group(Indent(inner), should_break=True)
    assert render_doc_to_string(doc) == "a\n    b"


def test_if_break_uses_group_id_mode():
    doc = Concat(
        [
            Group(
                Concat([Text("a"), Line(LineMode.SOFT), Text("b")]),
                should_break=True,
                id="g1",
            ),
            IfBreak(
                break_contents=Text(" BROKEN"),
                flat_contents=Text(" FLAT"),
                group_id="g1",
            ),
        ]
    )
    assert render_doc_to_string(doc) == "a\nb BROKEN"


def test_fill_wraps_when_needed():
    word = "x" * 30
    parts: list[Doc] = [
        Text(word),
        Line(LineMode.LINE),
        Text(word),
        Line(LineMode.LINE),
        Text(word),
    ]
    assert render_doc_to_string(Fill(parts)) == f"{word} {word}\n{word}"


def test_line_suffix_appended_before_newline():
    doc = Concat(
        [
            Text("code"),
            LineSuffix(Text(" // comment")),
            Line(LineMode.HARD),
            Text("next"),
        ]
    )
    assert render_doc_to_string(doc) == "code // comment\nnext"


def test_line_suffix_boundary_forces_suffix_flush():
    doc = Concat(
        [
            Text("a"),
            LineSuffix(Text(" // c")),
            LineSuffixBoundary(),
            Text("b"),
        ]
    )
    assert render_doc_to_string(doc) == "a // c\nb"


def test_trim_removes_trailing_whitespace():
    doc = Concat([Text("hello   \t"), Trim(), Text("!")])
    assert render_doc_to_string(doc) == "hello!"


def test_break_parent_and_cursor_are_noop():
    doc = Concat([Text("a"), BreakParent(), Cursor(), Text("b")])
    assert render_doc_to_string(doc) == "ab"


def test_builder_helpers():
    doc = group(
        concat(
            [
                text("fn("),
                indent(concat([line(), text("a,"), line(), text("b")])),
                line(),
                text(")"),
            ]
        )
    )
    assert render_doc_to_string(doc) == "fn( a, b )"
