from __future__ import annotations

from dataclasses import dataclass
import enum

# References: https://github.com/prettier/prettier/blob/main/commands.md


class LineMode(enum.Enum):
    # Typhon-specific: Prettier models line/softline/hardline/literalline as
    # separate constants. We unify them into one node + mode.
    SOFT = enum.auto()
    HARD = enum.auto()
    LITERAL = enum.auto()


@dataclass(frozen=True, slots=True)
class Nil:
    # Typhon-specific: explicit empty-doc sentinel.
    # Prettier uses empty string/empty arrays instead of a dedicated command.
    pass


@dataclass(frozen=True, slots=True)
class Text:
    # Typhon-specific: explicit text node.
    # Prettier directly uses plain strings for text segments.
    value: str


@dataclass(frozen=True, slots=True)
class Line:
    mode: LineMode


@dataclass(frozen=True, slots=True)
class Concat:
    # Typhon-specific: explicit concatenation node.
    # Prettier directly uses arrays of docs for concatenation.
    parts: list["Doc"]


@dataclass(frozen=True, slots=True)
class Group:
    content: "Doc"
    should_break: bool = False
    # Compatibility note: Prettier uses symbol; we use str for stable IDs.
    id: str | None = None
    # Compatibility note: mirrors Prettier's conditionalGroup alternatives.
    # When present, printer should try alternatives from least to most expanded.
    expanded_states: list["Doc"] | None = None


@dataclass(frozen=True, slots=True)
class Indent:
    content: "Doc"


@dataclass(frozen=True, slots=True)
class Align:
    content: "Doc"
    # Compatibility note: corresponds to Prettier's number | string width.
    n: int | str


@dataclass(frozen=True, slots=True)
class Fill:
    parts: list["Doc"]


@dataclass(frozen=True, slots=True)
class IfBreak:
    break_contents: "Doc | None" = None
    flat_contents: "Doc | None" = None
    # Compatibility note: Prettier uses symbol groupId; we use str.
    group_id: str | None = None


@dataclass(frozen=True, slots=True)
class LineSuffix:
    content: "Doc"


@dataclass(frozen=True, slots=True)
class LineSuffixBoundary:
    pass


@dataclass(frozen=True, slots=True)
class BreakParent:
    pass


@dataclass(frozen=True, slots=True)
class Trim:
    pass


@dataclass(frozen=True, slots=True)
class Cursor:
    pass


type Doc = (
    Nil
    | Text
    | Line
    | Concat
    | Group
    | Indent
    | Align
    | Fill
    | IfBreak
    | LineSuffix
    | LineSuffixBoundary
    | BreakParent
    | Trim
    | Cursor
)

# Typhon compatibility union:
# - Includes core Prettier commands.
# - Also includes structural wrappers (Nil/Text/Concat/Line+LineMode) that
#   normalize Prettier's primitive forms (empty/string/array).


NIL = Nil()
SOFTLINE = Line(LineMode.SOFT)
HARDLINE = Line(LineMode.HARD)
LITERALLINE = Line(LineMode.LITERAL)
LINE_SUFFIX_BOUNDARY = LineSuffixBoundary()
BREAK_PARENT = BreakParent()
TRIM = Trim()
CURSOR = Cursor()


def text(v: str) -> Doc:
    if v == "":
        return NIL
    return Text(v)


def space(n: int = 1) -> Doc:
    return text(" " * n)


def line() -> Doc:
    return SOFTLINE


def softline() -> Doc:
    return SOFTLINE


def hardline() -> Doc:
    return HARDLINE


def literalline() -> Doc:
    return LITERALLINE


def concat(parts: list[Doc]) -> Doc:
    flattened: list[Doc] = []
    for part in parts:
        if isinstance(part, Nil):
            continue
        if isinstance(part, Concat):
            flattened.extend(part.parts)
            continue
        flattened.append(part)

    if len(flattened) == 0:
        return NIL
    if len(flattened) == 1:
        return flattened[0]
    return Concat(flattened)


def group(
    content: Doc,
    should_break: bool = False,
    id: str | None = None,
    expanded_states: list[Doc] | None = None,
) -> Doc:
    return Group(
        content=content,
        should_break=should_break,
        id=id,
        expanded_states=expanded_states,
    )


def indent(content: Doc) -> Doc:
    return Indent(content)


def align(content: Doc, n: int | str) -> Doc:
    return Align(content=content, n=n)


def fill(parts: list[Doc]) -> Doc:
    return Fill(parts)


def if_break(
    break_contents: Doc | None = None,
    flat_contents: Doc | None = None,
    group_id: str | None = None,
) -> Doc:
    return IfBreak(
        break_contents=break_contents,
        flat_contents=flat_contents,
        group_id=group_id,
    )


def line_suffix(content: Doc) -> Doc:
    return LineSuffix(content)


def join(sep: Doc, parts: list[Doc]) -> Doc:
    if len(parts) == 0:
        return NIL

    joined: list[Doc] = [parts[0]]
    for part in parts[1:]:
        joined.append(sep)
        joined.append(part)
    return concat(joined)
