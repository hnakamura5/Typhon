from lsprotocol import types

from Typhon.LanguageServer.did_change import text_diff_to_partial_changes


def assert_partial_change(
    actual_change: types.TextDocumentContentChangePartial,
    start_line: int,
    start_character: int,
    end_line: int,
    end_character: int,
    change_text: str,
) -> None:
    assert actual_change.range.start.line == start_line
    assert actual_change.range.start.character == start_character
    assert actual_change.range.end.line == end_line
    assert actual_change.range.end.character == end_character
    assert actual_change.text == change_text


def test_text_diff_to_partial_changes_no_change() -> None:
    changes = text_diff_to_partial_changes("hello", "hello")
    assert len(changes) == 0


def test_text_diff_to_partial_changes_single_insertion() -> None:
    changes = text_diff_to_partial_changes("abc", "abXc")
    assert len(changes) == 1
    assert_partial_change(
        actual_change=changes[0],
        start_line=0,
        start_character=2,
        end_line=0,
        end_character=2,
        change_text="X",
    )


def test_text_diff_to_partial_changes_multiline_edit() -> None:
    before = "a\nbc\n"
    after = "a\nbXc\n"
    changes = text_diff_to_partial_changes(before, after)
    assert len(changes) == 1
    assert_partial_change(
        actual_change=changes[0],
        start_line=1,
        start_character=1,
        end_line=1,
        end_character=1,
        change_text="X",
    )


def test_text_diff_to_partial_changes_multiple_changes_desc_order() -> None:
    before = "0123456789"
    after = "01A34567B9"
    changes = text_diff_to_partial_changes(before, after)
    assert len(changes) == 2
    assert_partial_change(
        actual_change=changes[0],
        start_line=0,
        start_character=8,
        end_line=0,
        end_character=9,
        change_text="B",
    )
    assert_partial_change(
        actual_change=changes[1],
        start_line=0,
        start_character=2,
        end_line=0,
        end_character=3,
        change_text="A",
    )
