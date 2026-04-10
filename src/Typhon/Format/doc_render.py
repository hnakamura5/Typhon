from __future__ import annotations

import enum

from .doc_datatype import (
    Align,
    AlignToAnchor,
    Anchor,
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
)

DEFAULT_PRINT_WIDTH = 80
DEFAULT_INDENT_TEXT = "    "
DEFAULT_INDENT_WIDTH = len(DEFAULT_INDENT_TEXT)
DEFAULT_ALIGN_CHAR = " "
DEFAULT_NEWLINE = "\n"


class _RenderMode(enum.Enum):
    FLAT = enum.auto()
    BREAK = enum.auto()


type _Command = tuple[int, _RenderMode, Doc]


def _indent_width(indent_text: str) -> int:
    return len(indent_text)


def _align_width(n: int | str) -> int:
    if isinstance(n, int):
        return n
    return len(n)


def _line_indent(columns: int, *, align_char: str) -> str:
    if columns <= 0:
        return ""
    return align_char * columns


def _fits(
    *,
    width: int,
    current_column: int,
    commands: list[_Command],
    group_mode_by_id: dict[str, _RenderMode],
    indent_text: str,
) -> bool:
    remaining = width - current_column
    probe_column = current_column
    probe_stack = list(commands)
    probe_group_mode = dict(group_mode_by_id)
    probe_anchor_columns: dict[int, int] = {}

    while remaining >= 0 and len(probe_stack) > 0:
        indent, mode, doc = probe_stack.pop()

        if isinstance(doc, BreakParent):
            return False

        if isinstance(doc, Nil | Trim | Cursor):
            continue

        if isinstance(doc, Text):
            width_used = len(doc.value)
            remaining -= width_used
            probe_column += width_used
            continue

        if isinstance(doc, Concat):
            for part in reversed(doc.parts):
                probe_stack.append((indent, mode, part))
            continue

        if isinstance(doc, Indent):
            probe_stack.append((indent + _indent_width(indent_text), mode, doc.content))
            continue

        if isinstance(doc, Align):
            probe_stack.append((indent + _align_width(doc.n), mode, doc.content))
            continue

        if isinstance(doc, Anchor):
            probe_anchor_columns[id(doc)] = probe_column
            probe_stack.append((indent, mode, doc.content))
            continue

        if isinstance(doc, AlignToAnchor):
            anchor_column = (
                probe_anchor_columns.get(id(doc.anchor))
                if doc.anchor is not None
                else None
            )
            aligned_indent = (
                anchor_column + doc.offset if anchor_column is not None else indent
            )
            probe_stack.append((aligned_indent, mode, doc.content))
            continue

        if isinstance(doc, Group):
            group_mode = mode
            if doc.should_break:
                group_mode = _RenderMode.BREAK
            if doc.id is not None:
                probe_group_mode[doc.id] = group_mode
            content = doc.content
            if doc.expanded_states is not None and len(doc.expanded_states) > 0:
                content = doc.expanded_states[0]
            probe_stack.append((indent, group_mode, content))
            continue

        if isinstance(doc, IfBreak):
            target_mode = mode
            if doc.group_id is not None and doc.group_id in probe_group_mode:
                target_mode = probe_group_mode[doc.group_id]
            selected = (
                doc.break_contents
                if target_mode is _RenderMode.BREAK
                else doc.flat_contents
            )
            if selected is not None:
                probe_stack.append((indent, target_mode, selected))
            continue

        if isinstance(doc, LineSuffix):
            probe_stack.append((indent, mode, doc.content))
            continue

        if isinstance(doc, LineSuffixBoundary):
            return True

        if isinstance(doc, Fill):
            for part in reversed(doc.parts):
                probe_stack.append((indent, mode, part))
            continue

        if mode is _RenderMode.FLAT:
            if doc.mode is LineMode.LINE:
                remaining -= 1
                probe_column += 1
                continue
            if doc.mode is LineMode.SOFT:
                continue
            # hardline/literalline cannot stay in flat mode.
            return False
        return True

    return remaining >= 0


def _select_fill_layout(
    *,
    width: int,
    current_column: int,
    indent: int,
    parts: list[Doc],
    group_mode_by_id: dict[str, _RenderMode],
    indent_text: str,
) -> tuple[_Command, _Command, _Command | None]:
    content = parts[0]
    if len(parts) == 1:
        return (
            (indent, _RenderMode.BREAK, content),
            (indent, _RenderMode.BREAK, Nil()),
            None,
        )

    whitespace = parts[1]
    rest = parts[2:]

    content_flat = (indent, _RenderMode.FLAT, content)
    whitespace_flat = (indent, _RenderMode.FLAT, whitespace)
    whitespace_break = (indent, _RenderMode.BREAK, whitespace)

    if len(rest) > 0:
        next_content_flat: _Command = (indent, _RenderMode.FLAT, rest[0])
        if _fits(
            width=width,
            current_column=current_column,
            commands=[content_flat, whitespace_flat, next_content_flat],
            group_mode_by_id=group_mode_by_id,
            indent_text=indent_text,
        ):
            rest_doc = Fill(rest)
            return (
                content_flat,
                whitespace_flat,
                (indent, _RenderMode.BREAK, rest_doc),
            )

    if _fits(
        width=width,
        current_column=current_column,
        commands=[content_flat, whitespace_flat],
        group_mode_by_id=group_mode_by_id,
        indent_text=indent_text,
    ):
        rest_doc = Fill(rest) if len(rest) > 0 else None
        return (
            content_flat,
            whitespace_break,
            (indent, _RenderMode.BREAK, rest_doc) if rest_doc is not None else None,
        )

    rest_doc = Fill(rest) if len(rest) > 0 else None
    return (
        (indent, _RenderMode.BREAK, content),
        whitespace_break,
        (indent, _RenderMode.BREAK, rest_doc) if rest_doc is not None else None,
    )


def render_doc_to_string(
    doc: Doc,
    *,
    width: int = DEFAULT_PRINT_WIDTH,
    indent_text: str = DEFAULT_INDENT_TEXT,
    align_char: str = DEFAULT_ALIGN_CHAR,
    newline_text: str = DEFAULT_NEWLINE,
) -> str:
    lines: list[str] = [""]
    stack: list[_Command] = [(0, _RenderMode.BREAK, doc)]
    pending_line_suffixes: list[_Command] = []
    group_mode_by_id: dict[str, _RenderMode] = {}
    anchor_columns: dict[int, int] = {}

    def current_column() -> int:
        return len(lines[-1])

    def write_text(value: str) -> None:
        if value == "":
            return
        parts = value.split(newline_text)
        lines[-1] += parts[0]
        for part in parts[1:]:
            lines.append(part)

    def trim_line_end() -> None:
        lines[-1] = lines[-1].rstrip(" \t")

    def write_newline(indent: int, *, literal: bool) -> None:
        lines.append("" if literal else _line_indent(indent, align_char=align_char))

    while len(stack) > 0:
        indent, mode, current = stack.pop()

        if isinstance(current, Nil | BreakParent | Cursor):
            continue

        if isinstance(current, Text):
            write_text(current.value)
            continue

        if isinstance(current, Trim):
            trim_line_end()
            continue

        if isinstance(current, Concat):
            for part in reversed(current.parts):
                stack.append((indent, mode, part))
            continue

        if isinstance(current, Indent):
            stack.append((indent + _indent_width(indent_text), mode, current.content))
            continue

        if isinstance(current, Align):
            stack.append((indent + _align_width(current.n), mode, current.content))
            continue

        if isinstance(current, Anchor):
            anchor_columns[id(current)] = current_column()
            stack.append((indent, mode, current.content))
            continue

        if isinstance(current, AlignToAnchor):
            anchor_column = (
                anchor_columns.get(id(current.anchor))
                if current.anchor is not None
                else None
            )
            aligned_indent = (
                anchor_column + current.offset if anchor_column is not None else indent
            )
            stack.append((aligned_indent, mode, current.content))
            continue

        if isinstance(current, Group):
            selected_content: Doc = current.content
            selected_mode = mode
            if current.should_break:
                selected_mode = _RenderMode.BREAK
            elif mode is _RenderMode.FLAT:
                selected_mode = _RenderMode.FLAT
            elif (
                current.expanded_states is not None and len(current.expanded_states) > 0
            ):
                selected_mode = _RenderMode.BREAK
                for state in current.expanded_states:
                    if _fits(
                        width=width,
                        current_column=current_column(),
                        commands=[(indent, _RenderMode.FLAT, state)],
                        group_mode_by_id=group_mode_by_id,
                        indent_text=indent_text,
                    ):
                        selected_content = state
                        selected_mode = _RenderMode.FLAT
                        break
                if selected_mode is _RenderMode.BREAK:
                    selected_content = current.expanded_states[-1]
            else:
                if _fits(
                    width=width,
                    current_column=current_column(),
                    commands=[(indent, _RenderMode.FLAT, current.content)],
                    group_mode_by_id=group_mode_by_id,
                    indent_text=indent_text,
                ):
                    selected_mode = _RenderMode.FLAT
                else:
                    selected_mode = _RenderMode.BREAK

            if current.id is not None:
                group_mode_by_id[current.id] = selected_mode

            stack.append((indent, selected_mode, selected_content))
            continue

        if isinstance(current, IfBreak):
            target_mode = mode
            if current.group_id is not None and current.group_id in group_mode_by_id:
                target_mode = group_mode_by_id[current.group_id]

            selected = (
                current.break_contents
                if target_mode is _RenderMode.BREAK
                else current.flat_contents
            )
            if selected is not None:
                stack.append((indent, target_mode, selected))
            continue

        if isinstance(current, LineSuffix):
            pending_line_suffixes.append((indent, mode, current.content))
            continue

        if isinstance(current, LineSuffixBoundary):
            if len(pending_line_suffixes) > 0:
                boundary_suffixes: list[_Command] = pending_line_suffixes.copy()
                stack.append((indent, _RenderMode.BREAK, Line(LineMode.HARD)))
                for suffix_cmd in reversed(boundary_suffixes):
                    stack.append(suffix_cmd)
                pending_line_suffixes.clear()
            continue

        if isinstance(current, Fill):
            if len(current.parts) == 0:
                continue
            content_cmd, ws_cmd, rest_cmd = _select_fill_layout(
                width=width,
                current_column=current_column(),
                indent=indent,
                parts=current.parts,
                group_mode_by_id=group_mode_by_id,
                indent_text=indent_text,
            )
            if rest_cmd is not None:
                stack.append(rest_cmd)
            if not isinstance(ws_cmd[2], Nil):
                stack.append(ws_cmd)
            stack.append(content_cmd)
            continue

        if mode is _RenderMode.FLAT:
            if current.mode is LineMode.LINE:
                write_text(" ")
                continue
            if current.mode is LineMode.SOFT:
                continue

        if len(pending_line_suffixes) > 0:
            pending_suffixes: list[_Command] = pending_line_suffixes.copy()
            stack.append((indent, mode, current))
            for suffix_cmd in reversed(pending_suffixes):
                stack.append(suffix_cmd)
            pending_line_suffixes.clear()
            continue

        if current.mode is LineMode.LITERAL:
            write_newline(0, literal=True)
        else:
            write_newline(indent, literal=False)
        continue

    # Flush any remaining line suffixes at the end of the document
    if len(pending_line_suffixes) > 0:
        for suffix_cmd in reversed(pending_line_suffixes):
            stack.append(suffix_cmd)
        pending_line_suffixes.clear()
        while len(stack) > 0:
            s_indent, s_mode, s_current = stack.pop()
            if isinstance(s_current, Concat):
                for part in reversed(s_current.parts):
                    stack.append((s_indent, s_mode, part))
            elif isinstance(s_current, Text):
                write_text(s_current.value)
            elif isinstance(s_current, Nil):
                pass
            elif isinstance(s_current, Group):
                stack.append((s_indent, s_mode, s_current.content))

    return newline_text.join(lines)


__all__ = ["render_doc_to_string"]
