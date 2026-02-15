from Typhon.SourceMap.datatype import Range, Pos
import ast


def test_range_contains():
    assert Range(Pos(1, 0), Pos(3, 5)).contains(Pos(1, 0))
    assert Range(Pos(1, 0), Pos(3, 5)).contains(Pos(2, 10))
    assert Range(Pos(1, 0), Pos(3, 5)).contains(Pos(3, 4))
    assert not Range(Pos(1, 0), Pos(3, 5)).contains(Pos(0, 10))
    assert not Range(Pos(1, 0), Pos(3, 5)).contains(Pos(3, 5))


def test_range_includes():
    assert Range(Pos(1, 0), Pos(5, 0)).includes(Range(Pos(1, 0), Pos(5, 0)))
    assert Range(Pos(1, 0), Pos(5, 0)).includes(Range(Pos(2, 0), Pos(4, 10)))
    assert not Range(Pos(1, 0), Pos(5, 0)).includes(Range(Pos(0, 10), Pos(4, 10)))


def test_range_offset():
    base_range = Range(Pos(2, 5), Pos(4, 10))
    included_range_in_line = Range(Pos(2, 6), Pos(2, 9))
    included_range_same_line = Range(Pos(3, 0), Pos(3, 5))
    included_range_diff_line = Range(Pos(2, 10), Pos(3, 5))
    assert base_range.calc_offset(included_range_in_line) == Range(Pos(0, 1), Pos(0, 3))
    assert base_range.calc_offset(included_range_same_line) == Range(
        Pos(1, 0), Pos(0, 5)
    )
    assert base_range.calc_offset(included_range_diff_line) == Range(
        Pos(0, 5), Pos(1, 5)
    )


def test_range_apply_offset():
    base_pos = Pos(3, 10)
    offset_in_line = Range(Pos(0, 2), Pos(0, 5))
    offset_same_line = Range(Pos(1, 0), Pos(0, 5))
    offset_diff_line = Range(Pos(0, 5), Pos(1, 5))
    assert base_pos.apply_offset(offset_in_line) == Range(Pos(3, 12), Pos(3, 17))
    assert base_pos.apply_offset(offset_same_line) == Range(Pos(4, 0), Pos(4, 5))
    assert base_pos.apply_offset(offset_diff_line) == Range(Pos(3, 15), Pos(4, 5))


def test_range_from_ast_node():
    node = ast.parse("x = 10\ny = 20")
    assign_node = node.body[0]  # ast.Assign
    range = Range.from_ast_node(assign_node)
    assert range
    assert range.start == Pos(0, 0)
    assert range.end == Pos(0, 6)  # "x = 10" ends at column 6


def test_merge_ranges():
    range1 = Range(Pos(1, 0), Pos(2, 5))
    range2 = Range(Pos(2, 0), Pos(3, 10))
    merged_range = Range.merge_ranges([range1, range2])
    assert merged_range
    assert merged_range.start == Pos(1, 0)
    assert merged_range.end == Pos(3, 10)
