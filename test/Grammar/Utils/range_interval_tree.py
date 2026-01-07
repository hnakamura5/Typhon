from src.Typhon.SourceMap.datatype import (
    Range,
    Pos,
    RangeIntervalTree,
    RangeInterval,
)
import ast


def assert_range_list(
    result: list[RangeInterval[str]],
    expected: set[str],
):
    assert len(expected) == len(result)
    res_set = {res[1] for res in result}
    assert res_set == expected


tree = RangeIntervalTree[str]()
tree.add(Range(Pos(1, 0), Pos(3, 0)), "A")
tree.add(Range(Pos(2, 5), Pos(4, 0)), "B")
tree.add(Range(Pos(5, 5), Pos(6, 5)), "C")
tree.add(Range(Pos(0, 0), Pos(7, 0)), "D")


def test_range_interval_tree_at():
    assert_range_list(tree.at(Pos(0, 5)), {"D"})
    assert_range_list(tree.at(Pos(2, 10)), {"A", "B", "D"})
    assert_range_list(tree.at(Pos(9, 0)), set())


def test_range_interval_tree_overlap():
    assert_range_list(tree.overlap(Range(Pos(1, 0), Pos(2, 0))), {"A", "D"})
    # Range is open at the end, so  A, C is not included
    assert_range_list(tree.overlap(Range(Pos(3, 0), Pos(5, 5))), {"B", "D"})


def test_range_interval_tree_envelop():
    assert_range_list(tree.envelop(Range(Pos(2, 0), Pos(6, 5))), {"B", "C"})
    assert_range_list(tree.envelop(Range(Pos(0, 0), Pos(7, 0))), {"A", "B", "C", "D"})


def test_range_interval_tree_container():
    assert_range_list(tree.containers(Range(Pos(1, 0), Pos(3, 0))), {"A", "D"})
    assert_range_list(tree.containers(Range(Pos(2, 10), Pos(3, 0))), {"A", "B", "D"})


def test_range_interval_tree_minimal_container():
    assert_range_list(tree.minimal_containers(Range(Pos(1, 0), Pos(3, 0))), {"A"})
    assert_range_list(tree.minimal_containers(Range(Pos(2, 10), Pos(3, 0))), {"A", "B"})
