from dataclasses import dataclass
from ..Grammar.typhon_ast import PosAttributes, PosRange, get_pos_attributes_if_exists
from ..Driver.debugging import debug_verbose_print
from intervaltree import IntervalTree, Interval  # type: ignore[import]
from typing import Iterable
import ast


@dataclass(frozen=True, unsafe_hash=True, order=True)
class Pos:
    line: int
    column: int

    @staticmethod
    def from_start_pos_attributes(attr: PosAttributes) -> "Pos":
        return Pos(line=attr["lineno"], column=attr["col_offset"])

    @staticmethod
    def from_end_pos_attributes(attr: PosAttributes) -> "Pos | None":
        if attr["end_lineno"] is None or attr["end_col_offset"] is None:
            return None
        return Pos(line=attr["end_lineno"], column=attr["end_col_offset"])

    @staticmethod
    def from_node_start(node: ast.AST) -> "Pos | None":
        mapped_range = Range.from_ast_node(node)
        if mapped_range is None:
            return None
        return mapped_range.start

    @staticmethod
    def from_node_end(node: ast.AST) -> "Pos | None":
        mapped_range = Range.from_ast_node(node)
        if mapped_range is None:
            return None
        return mapped_range.end

    def col_back(self) -> "Pos":
        if self.column == 0:
            return self
        else:
            return Pos(line=self.line, column=self.column - 1)

    def col_forward(self) -> "Pos":
        return Pos(line=self.line, column=self.column + 1)

    def calc_offset(self, other: "Pos") -> "Pos":
        line_offset = other.line - self.line
        if line_offset == 0:
            column_offset = other.column - self.column
        else:
            column_offset = other.column
        return Pos(line=line_offset, column=column_offset)

    def apply_offset(self, offset: "Range") -> "Range":
        # offset is (start_offset, offset_from_start_to_end)
        start_column_offset = 0
        if offset.start.line == 0:
            start_column_offset = self.column + offset.start.column
        new_start_column = start_column_offset
        end_column_start = 0
        if offset.end.line == 0:
            end_column_start = new_start_column
        debug_verbose_print(
            f"Applying offset: pos={self}, offset={offset} -> new_start_column={
                new_start_column
            }, end_column_start={end_column_start} = {
                Range(
                    Pos(self.line + offset.start.line, new_start_column),
                    Pos(
                        self.line + offset.start.line + offset.end.line,
                        end_column_start + offset.end.column,
                    ),
                )
            }"
        )
        return Range(
            Pos(self.line + offset.start.line, new_start_column),
            Pos(
                self.line + offset.start.line + offset.end.line,
                end_column_start + offset.end.column,
            ),
        )


# Common central datatype for source range. All are 0 based.
@dataclass(frozen=True, unsafe_hash=True, order=True)
class Range:
    start: Pos
    end: Pos

    def is_empty(self) -> bool:
        return (self.start == self.end) and (self.start == Pos(0, 0))

    def contains(self, pos: Pos) -> bool:
        return self.start <= pos < self.end

    def includes(self, other: "Range") -> bool:
        return self.start <= other.start and other.end <= self.end

    def calc_offset(self, other: "Range") -> "Range":
        offset = self.start.calc_offset(other.start)
        end_offset = other.start.calc_offset(other.end)
        return Range(offset, end_offset)

    def col_back(self) -> "Range":
        return Range(start=self.start.col_back(), end=self.end.col_back())

    def col_forward(self) -> "Range":
        return Range(start=self.start.col_forward(), end=self.end.col_forward())

    @staticmethod
    def from_positions(
        start_line: int, start_column: int, end_line: int, end_column: int
    ) -> "Range":
        return Range(
            start=Pos(line=start_line, column=start_column),
            end=Pos(line=end_line, column=end_column),
        )

    @staticmethod
    def from_pos_range(pos_range: PosRange) -> "Range":
        return Range(
            start=Pos(line=pos_range["lineno"] - 1, column=pos_range["col_offset"]),
            end=Pos(
                line=pos_range["end_lineno"] - 1, column=pos_range["end_col_offset"]
            ),
        )

    @staticmethod
    def from_pos_attr(attr: PosAttributes) -> "Range | None":
        # Python ast position is 1-based for line, 0-based for column
        if attr["end_lineno"] is None or attr["end_col_offset"] is None:
            return None
        return Range(
            start=Pos(line=attr["lineno"] - 1, column=attr["col_offset"]),
            end=Pos(line=attr["end_lineno"] - 1, column=attr["end_col_offset"]),
        )

    @staticmethod
    def from_pos_attr_may_not_end(attr: PosAttributes) -> "Range":
        start_line = attr["lineno"]
        start_column = attr["col_offset"]
        end_line = (
            attr["end_lineno"] if attr["end_lineno"] is not None else attr["lineno"]
        )
        end_column = (
            attr["end_col_offset"]
            if attr["end_col_offset"] is not None
            else attr["col_offset"] + 1
        )
        if end_line == start_line and start_column == end_column:
            end_column += 1  # Ensure non-zero length
        return Range(
            start=Pos(line=start_line - 1, column=start_column),
            end=Pos(line=end_line - 1, column=end_column),
        )

    @staticmethod
    def from_interval(interval: Interval) -> "Range":
        return Range(start=interval.begin, end=interval.end)  # type: ignore[misc]

    @staticmethod
    def from_ast_node(node: ast.AST) -> "Range | None":
        attr = get_pos_attributes_if_exists(node)
        if attr is None:
            return None
        return Range.from_pos_attr(attr)

    @staticmethod
    def from_syntax_error(e: SyntaxError) -> "Range":
        start_line = e.lineno or 1
        start_column = e.offset or 0
        end_line = e.end_lineno or start_line
        end_column = e.end_offset or (start_column + 1)
        return Range(
            start=Pos(line=start_line - 1, column=start_column),
            end=Pos(line=end_line - 1, column=end_column),
        )

    @staticmethod
    def merge_ranges(ranges: Iterable["Range"]) -> "Range | None":
        if not ranges:
            return None
        debug_verbose_print("Merging ranges: ", ranges)
        ranges = list(ranges)
        start = min(r.start for r in ranges)
        end = max([r.end for r in ranges] + [start])
        debug_verbose_print(f"Merged range: start={start}, end={end}")
        return Range(start=start, end=end)

    def of_string(self, source: str) -> str:
        lines = source.splitlines()
        return self.of_lines(lines)

    def of_lines(self, lines: list[str]) -> str:
        start_line = self.start.line
        end_line = self.end.line
        start_column = self.start.column
        end_column = self.end.column

        def get_in_line(line: str, start_col: int, end_col: int) -> str:
            return line[start_col : min(end_col, len(line))]

        if start_line >= len(lines) or end_line >= len(lines):
            return ""
        if start_line == end_line:
            the_line = lines[start_line]
            return get_in_line(the_line, start_column, end_column)
        else:
            result_lines: list[str] = []
            result_lines.append(lines[start_line][start_column:])
            for line_num in range(start_line, end_line):
                result_lines.append(lines[line_num])
            result_lines.append(get_in_line(lines[end_line], 0, end_column))
            return "\n".join(result_lines)

    def deconstruct_str(self):
        return f"Range(Pos({self.start.line}, {self.start.column}), Pos({self.end.line}, {self.end.column}))"


type RangeInterval[T] = tuple[Range, T]


# Wrapper around IntervalTree for Range keys
class RangeIntervalTree[T]:
    def __init__(self):
        self.interval_tree = IntervalTree()

    def add(self, range: Range, data: T):
        self.interval_tree.addi(  # type: ignore[misc]
            range.start,
            range.end,
            data,
        )

    def at(self, pos: Pos) -> list[RangeInterval[T]]:
        intervals = self.interval_tree.at(pos)  # type: ignore[misc]
        return [
            (Range.from_interval(interval), interval.data)  # type: ignore[misc]
            for interval in intervals  # type: ignore[misc]
        ]

    def overlap(self, range: Range) -> list[RangeInterval[T]]:
        intervals = self.interval_tree.overlap(range.start, range.end)  # type: ignore[misc]
        return [
            (Range.from_interval(interval), interval.data)  # type: ignore[misc]
            for interval in intervals  # type: ignore[misc]
        ]

    def envelop(self, range: Range) -> list[RangeInterval[T]]:
        intervals = self.interval_tree.envelop(range.start, range.end)  # type: ignore[misc]
        return [
            (Range.from_interval(interval), interval.data)  # type: ignore[misc]
            for interval in intervals  # type: ignore[misc]
        ]

    def _container_intervals(self, range: Range) -> list[Interval]:
        # TODO: How to write this even IntervalTree doesn't have containers method?
        start_intervals = self.interval_tree.at(range.start)  # type: ignore[misc]
        if not start_intervals:
            return []
        return [
            interval  # type: ignore[misc]
            for interval in start_intervals  # type: ignore[misc]
            if (interval.contains_point(range.end) or interval.end == range.end)  # type: ignore[misc]
        ]

    def containers(self, range: Range) -> list[RangeInterval[T]]:
        containers = self._container_intervals(range)
        result: list[RangeInterval[T]] = []
        for interval in containers:
            result.append((Range.from_interval(interval), interval.data))  # type: ignore[misc]
        return result

    def minimal_containers(self, range: Range) -> list[RangeInterval[T]]:
        containers = self._container_intervals(range)
        debug_verbose_print(f"Minimal containers for range {range}: {containers}")
        if not containers:
            return []
        result: list[RangeInterval[T]] = []
        interval: Interval
        for i, interval in enumerate(containers):
            is_minimal = True
            for j, other_interval in enumerate(containers):
                if (
                    i != j
                    and interval.contains_interval(other_interval)  # type: ignore[misc]
                    and not interval.range_matches(other_interval)  # type: ignore[misc]
                ):
                    is_minimal = False
                    break
            if is_minimal:
                debug_verbose_print(f"  Minimal container: {interval}")
                result.append((Range.from_interval(interval), interval.data))  # type: ignore[misc]
        return result
