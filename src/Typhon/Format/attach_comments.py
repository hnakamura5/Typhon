"""Attach comment tokens from lossless token info to AST nodes.

This module classifies each comment as leading, trailing, or dangling
relative to the nearest AST node and stores them on the node via the
attribute APIs in ``typhon_ast``.

The attachment runs *before* ``print_to_doc`` so that the Doc printer
can emit comments in their correct positions.
"""

from __future__ import annotations

import ast
import tokenize
from bisect import bisect_left, bisect_right
from typing import Sequence

from ..Grammar.typhon_ast import (
    get_lossless_token_info,
    get_leading_comments,
    get_trailing_comments,
    get_dangling_comments,
    set_leading_comments,
    set_trailing_comments,
    set_dangling_comments,
)


type _Pos = tuple[int, int]  # (line, col)


def _node_start(node: ast.AST) -> _Pos:
    return (node.lineno, node.col_offset)  # type: ignore[attr-defined]


def _node_end(node: ast.AST) -> _Pos:
    return (node.end_lineno, node.end_col_offset)  # type: ignore[attr-defined]


def _has_pos(node: ast.AST) -> bool:
    return hasattr(node, "lineno") and hasattr(node, "end_lineno")


# ---------------------------------------------------------------------------
# Collect positioned nodes
# ---------------------------------------------------------------------------


def _collect_positioned_nodes(module: ast.Module) -> list[ast.AST]:
    """Return all AST nodes that carry position info, sorted by start position."""
    nodes: list[ast.AST] = []
    for node in ast.walk(module):
        if _has_pos(node) and node is not module:
            nodes.append(node)
    nodes.sort(key=_node_start)
    return nodes


def _collect_stmt_nodes(module: ast.Module) -> list[ast.stmt]:
    """Return all statement nodes sorted by start position."""
    stmts: list[ast.stmt] = []
    for node in ast.walk(module):
        if isinstance(node, ast.stmt) and node is not module:
            stmts.append(node)
    stmts.sort(key=_node_start)
    return stmts


def _get_children_stmts(node: ast.AST) -> list[ast.stmt]:
    """Return direct child statements of a node (body, orelse, handlers, finalbody, etc.)."""
    children: list[ast.stmt] = []
    for field_name in ("body", "orelse", "handlers", "finalbody"):
        field = getattr(node, field_name, None)
        if isinstance(field, list):
            for child in field:
                if isinstance(child, ast.stmt):
                    children.append(child)
    # match_case bodies
    if isinstance(node, ast.match_case) and isinstance(node.body, list):
        children.extend(s for s in node.body if isinstance(s, ast.stmt))
    return children


# ---------------------------------------------------------------------------
# Container hierarchy
# ---------------------------------------------------------------------------


def _build_parent_map(module: ast.Module) -> dict[int, ast.AST]:
    """Map id(child) -> parent for container lookup."""
    parents: dict[int, ast.AST] = {}
    for node in ast.walk(module):
        for child in ast.iter_child_nodes(node):
            parents[id(child)] = node
    return parents


# ---------------------------------------------------------------------------
# Core attachment logic
# ---------------------------------------------------------------------------


def _extract_comments(
    tokens: Sequence[tokenize.TokenInfo],
) -> list[tokenize.TokenInfo]:
    """Filter comment tokens from the full token list."""
    return [t for t in tokens if t.type == tokenize.COMMENT]


def _find_enclosing_container(
    comment_start: _Pos,
    comment_end: _Pos,
    module: ast.Module,
    parent_map: dict[int, ast.AST],
) -> ast.AST:
    """Find the innermost container node that fully encloses the comment."""
    best: ast.AST = module
    for node in ast.walk(module):
        if node is module:
            continue
        if not _has_pos(node):
            continue
        ns = _node_start(node)
        ne = _node_end(node)
        if ns <= comment_start and comment_end <= ne:
            # Prefer deeper (more specific) containers
            bs = _node_start(best) if best is not module else (0, 0)
            be = _node_end(best) if best is not module else (999999, 999999)
            if ns >= bs and ne <= be:
                best = node
    return best


def attach_comments(module: ast.Module) -> None:
    """Attach comments from lossless token info to AST nodes.

    After this function, each relevant AST node may have:
    - leading comments: comments on lines immediately before the node
    - trailing comments: comments on the same line after the node
    - dangling comments: comments inside a container with no child at that position
    """
    tokens = get_lossless_token_info(module)
    if tokens is None:
        return

    comments = _extract_comments(tokens)
    if not comments:
        return

    stmts = _collect_stmt_nodes(module)
    if not stmts:
        # Only comments, no statements — attach all as dangling on module
        set_dangling_comments(module, comments)
        return

    # Build start-line index for fast lookup
    stmt_start_lines = [s.lineno for s in stmts]

    parent_map = _build_parent_map(module)

    for comment in comments:
        comment_line = comment.start[0]
        comment_start: _Pos = comment.start
        comment_end: _Pos = comment.end

        attached = False

        # --- 1. Trailing: comment on the same line as a node's end ---
        # Pick the innermost (latest-ending) statement whose end is on the
        # comment line and whose end column is before the comment.
        best_trailing: ast.stmt | None = None
        for stmt in stmts:
            stmt_end_line = stmt.end_lineno
            if stmt_end_line is None:
                continue
            if comment_line == stmt_end_line and comment.start[1] > (
                stmt.end_col_offset or 0
            ):
                if best_trailing is None:
                    best_trailing = stmt
                else:
                    # Prefer the innermost (most specific) node
                    bt_start = _node_start(best_trailing)
                    s_start = _node_start(stmt)
                    bt_end = _node_end(best_trailing)
                    s_end = _node_end(stmt)
                    if s_start >= bt_start and s_end <= bt_end:
                        best_trailing = stmt
        if best_trailing is not None:
            trailing = get_trailing_comments(best_trailing)
            set_trailing_comments(best_trailing, trailing + [comment])
            attached = True

        if attached:
            continue

        # --- 2. Leading: comment on a line just before a statement ---
        # Find the first statement that starts after the comment line
        idx = bisect_right(stmt_start_lines, comment_line)
        if idx < len(stmts):
            next_stmt = stmts[idx]
            # Check if there are no other statements between comment and next_stmt
            # and the comment is before the next statement's start
            if comment_line < next_stmt.lineno:
                # Verify no statement ends on or after comment_line before next_stmt
                is_leading = True
                for s in stmts:
                    if s is next_stmt:
                        continue
                    s_end = s.end_lineno or s.lineno
                    # If another statement's range covers the comment line,
                    # the comment belongs inside that statement, not as leading
                    # — unless that statement also contains next_stmt (parent-child).
                    if s.lineno <= comment_line <= s_end and comment_line < next_stmt.lineno:
                        next_end = next_stmt.end_lineno or next_stmt.lineno
                        if not (s.lineno <= next_stmt.lineno and next_end <= s_end):
                            is_leading = False
                            break
                if is_leading:
                    leading = get_leading_comments(next_stmt)
                    set_leading_comments(next_stmt, leading + [comment])
                    attached = True

        if attached:
            continue

        # --- 3. Dangling: inside a container but not adjacent to any child stmt ---
        container = _find_enclosing_container(
            comment_start, comment_end, module, parent_map
        )
        dangling = get_dangling_comments(container)
        set_dangling_comments(container, dangling + [comment])
