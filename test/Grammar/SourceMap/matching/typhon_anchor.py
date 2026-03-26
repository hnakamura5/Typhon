from ...assertion_utils import (
    assert_typh_code_match_unparse,
    assert_transform,
    SourceMapAsserter,
)
from Typhon.SourceMap.datatype import Range, Pos


code_completion_trigger_anchor = """
"Hello"[1].find("e", 0, 5)
"""
transformed_code_completion_trigger_anchor = """
'Hello'[1].find('e', 0, 5)
"""


def test_match_typhon_stmt_completion_trigger_anchor():
    assert_transform(
        code_completion_trigger_anchor, transformed_code_completion_trigger_anchor
    )
    assert_typh_code_match_unparse(code_completion_trigger_anchor)
    sa = SourceMapAsserter(code_completion_trigger_anchor)
    sa.assert_range_text(  # '[' of "Hello"[1]
        Range(start=Pos(1, 7), end=Pos(1, 8)),
        "[",
        Range(start=Pos(0, 7), end=Pos(0, 8)),
        "[",
    )
    sa.assert_range_text(  # '.' before "find"
        Range(start=Pos(1, 10), end=Pos(1, 11)),
        ".",
        Range(start=Pos(0, 10), end=Pos(0, 11)),
        ".",
    )
    sa.assert_range_text(  # '(' after "find"
        Range(start=Pos(1, 15), end=Pos(1, 16)),
        "(",
        Range(start=Pos(0, 15), end=Pos(0, 16)),
        "(",
    )


code_completion_trigger_anchor_optional = """
"Hello"?[1]?.find?("e", 0, 5)
"""
transformed_code_completion_trigger_anchor_optional = """
_typh_v_fimh5dnn('e', 0, 5) if (_typh_v_fimh5dnn := (_typh_v_ij7ybbsf.find if (_typh_v_ij7ybbsf := (_typh_v_3r6vosme[1] if (_typh_v_3r6vosme := 'Hello') is not None else None)) is not None else None)) is not None else None
"""


def test_match_typhon_stmt_completion_trigger_anchor_optional():
    assert_transform(
        code_completion_trigger_anchor_optional,
        transformed_code_completion_trigger_anchor_optional,
    )
    assert_typh_code_match_unparse(code_completion_trigger_anchor_optional)
    sa = SourceMapAsserter(code_completion_trigger_anchor_optional)
    sa.assert_range_text(  # '[' of "Hello"?[1]
        Range(start=Pos(1, 8), end=Pos(1, 9)),
        "[",
        Range(start=Pos(0, 116), end=Pos(0, 117)),
        "[",
    )
    sa.assert_range_text(  # '.' before "find"
        Range(start=Pos(1, 12), end=Pos(1, 13)),
        ".",
        Range(start=Pos(0, 69), end=Pos(0, 70)),
        ".",
    )
    sa.assert_range_text(  # '(' after "find?"
        Range(start=Pos(1, 18), end=Pos(1, 19)),
        "(",
        Range(start=Pos(0, 16), end=Pos(0, 17)),
        "(",
    )
