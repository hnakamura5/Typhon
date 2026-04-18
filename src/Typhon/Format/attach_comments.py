"""Attach comment tokens from lossless token info to AST nodes.

This module classifies each comment as leading, trailing, or dangling
relative to the nearest AST node and stores them on the node via the
attribute APIs in ``typhon_ast``.

The attachment runs *before* ``print_to_doc`` so that the Doc printer
can emit comments in their correct positions.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from tokenize import TokenInfo, COMMENT, ENDMARKER
from bisect import bisect_left, bisect_right
from typing import Sequence, Literal

from Typhon.Grammar.position import PosNode, get_pos_attributes
from Typhon.SourceMap.datatype import Pos, Range
from Typhon.SourceMap.source_ast_cache import SourceAstCache

from ..Driver.debugging import debug_verbose_print
from ..Grammar.typhon_ast import (
    add_dangling_comments,
    add_leading_comments,
    add_trailling_comments,
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


def _collect_expr_nodes(module: ast.Module) -> list[ast.expr]:
    """Return all expression nodes sorted by start position."""
    exprs: list[ast.expr] = []
    for node in ast.walk(module):
        if isinstance(node, ast.expr) and _has_pos(node):
            exprs.append(node)
    exprs.sort(key=_node_start)
    return exprs


def _collect_stmt_nodes(module: ast.Module) -> list[ast.stmt]:
    """Return all statement nodes sorted by start position."""
    stmts: list[ast.stmt] = []
    for node in ast.walk(module):
        debug_verbose_print(
            lambda: f"Visiting node: {ast.dump(node)} (type {type(node).__name__})"
        )
        if isinstance(node, ast.stmt):
            stmts.append(node)
    stmts.sort(key=_node_start)
    return stmts


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
    tokens: Sequence[TokenInfo],
) -> list[TokenInfo]:
    """Filter comment tokens from the full token list."""
    return [t for t in tokens if t.type == COMMENT]


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
    exprs = _collect_expr_nodes(module)
    if not stmts:
        # Only comments, no statements — attach all as dangling on module
        set_dangling_comments(module, comments)
        return

    debug_verbose_print(
        lambda: (
            f"Collected statements {stmts} and expressions {exprs} for comment attachment"
        )
    )

    # Build start-line index for fast lookup
    stmt_start_lines = [s.lineno for s in stmts]
    parent_map = _build_parent_map(module)

    for comment in comments:
        comment_line = comment.start[0]
        comment_start: _Pos = comment.start
        comment_end: _Pos = comment.end

        debug_verbose_print(
            lambda: (
                f"Processing comment: {comment.string} at {comment_start}-{comment_end}"
            )
        )
        attached = False

        # --- 1. Trailing: comment on the same line as a node's end ---
        # Pick the innermost (latest-ending) statement whose end is on the
        # comment line and whose end column is before the comment.
        best_trailing: ast.stmt | None = None
        for stmt in stmts:
            stmt_end_line = stmt.end_lineno
            if stmt_end_line is None:
                continue
            debug_verbose_print(
                lambda: (
                    f"Checking stmt {ast.dump(stmt)} ending at line {stmt_end_line} for trailing comment @ {get_pos_attributes(stmt)}"
                )
            )
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
            debug_verbose_print(
                lambda: (
                    f"Attached as trailing comment to stmt ending at {ast.dump(best_trailing) if best_trailing else None}"
                )
            )
            attached = True
            continue

        # --- 1b. Trailing on expression: same line, after an expression node ---
        best_trailing_expr: ast.expr | None = None
        for expr in exprs:
            expr_end_line = expr.end_lineno
            if expr_end_line is None:
                continue
            debug_verbose_print(
                lambda: (
                    f"Checking expr {ast.dump(expr)} ending at line {expr_end_line} for trailing comment"
                )
            )
            if comment_line == expr_end_line and comment.start[1] > (
                expr.end_col_offset or 0
            ):
                if best_trailing_expr is None:
                    best_trailing_expr = expr
                else:
                    bt_start = _node_start(best_trailing_expr)
                    e_start = _node_start(expr)
                    bt_end = _node_end(best_trailing_expr)
                    e_end = _node_end(expr)
                    if e_start >= bt_start and e_end <= bt_end:
                        best_trailing_expr = expr
        if best_trailing_expr is not None:
            trailing = get_trailing_comments(best_trailing_expr)
            set_trailing_comments(best_trailing_expr, trailing + [comment])
            debug_verbose_print(
                lambda: (
                    f"Attached as trailing comment to expr ending at {ast.dump(best_trailing_expr) if best_trailing_expr else None}"
                )
            )
            attached = True
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
                    if (
                        s.lineno <= comment_line <= s_end
                        and comment_line < next_stmt.lineno
                    ):
                        next_end = next_stmt.end_lineno or next_stmt.lineno
                        if not (s.lineno <= next_stmt.lineno and next_end <= s_end):
                            is_leading = False
                            break
                if is_leading:
                    leading = get_leading_comments(next_stmt)
                    set_leading_comments(next_stmt, leading + [comment])
                    debug_verbose_print(
                        lambda: (
                            f"Attached as leading comment to stmt starting at {ast.dump(next_stmt) if next_stmt else None}"
                        )
                    )
                    attached = True
                    continue

        # --- 2b. Leading on expression: comment just before an expression ---
        # Covers inline block comments (e.g. ``#(x)# expr``) and line comments
        # on a preceding line inside expression-level constructs (calls, lists, etc.).
        expr_starts = [_node_start(e) for e in exprs]
        eidx = bisect_left(expr_starts, comment_end)
        # Skip expressions that start strictly before the comment ends
        while eidx < len(exprs) and _node_start(exprs[eidx]) < comment_end:
            eidx += 1
        if eidx < len(exprs):
            next_expr = exprs[eidx]
            leading = get_leading_comments(next_expr)
            set_leading_comments(next_expr, leading + [comment])
            debug_verbose_print(
                lambda: (
                    f"Attached as leading comment to expr starting at {ast.dump(next_expr) if next_expr else None}"
                )
            )
            attached = True
            continue

        # --- 3. Dangling: inside a container but not adjacent to any child stmt ---
        container = _find_enclosing_container(
            comment_start, comment_end, module, parent_map
        )
        add_dangling_comments(container, [comment])
        debug_verbose_print(
            lambda: (
                f"Attached as dangling comment to container starting at {ast.dump(container) if container else None}"
            )
        )


@dataclass
class CommentInfo:
    comment: TokenInfo
    index: int
    before_non_comment_tok: TokenInfo | None
    after_non_comment_tok: TokenInfo | None


# Grouping rules:
# - Consecutive comment tokens in the same line are grouped together.
def _gather_comments(tokens: Sequence[TokenInfo]) -> list[CommentInfo]:
    """Group consecutive comment tokens and identify adjacent nodes."""
    result: list[CommentInfo] = []
    before_non_comment_tok: TokenInfo | None = None
    for i, tok in enumerate(tokens):
        if tok.type == COMMENT:
            result.append(
                CommentInfo(
                    comment=tok,
                    index=i,
                    before_non_comment_tok=before_non_comment_tok,
                    after_non_comment_tok=None,  # to be filled in next iteration
                )
            )
        else:
            before_non_comment_tok = tok
            # Fill in after_non_comment_tok for the comments if not already set
            for i in range(len(result) - 1, -1, -1):
                if result[i].after_non_comment_tok is None:
                    result[i].after_non_comment_tok = tok
                else:
                    break
    return result


def _node_attachable_comment_to(
    ast_cache: SourceAstCache,
    anchor_tok: TokenInfo,
    filter_node_type: type[ast.AST] | None = None,
    *,
    before: bool,
) -> ast.AST | None:
    tok_range = Range.from_pos_attr(get_pos_attributes(anchor_tok))
    if not tok_range:
        return None
    tok_node = ast_cache.source_range_to_node(tok_range, filter_node_type)
    if not tok_node:
        return None
    if not isinstance(tok_node, PosNode):
        return None
    tok_node_range = Range.from_pos_attr(get_pos_attributes(tok_node))
    if not tok_node_range:
        return None
    if before:
        # For before attachment, the token must be the last token of the node.
        if tok_range.end == tok_node_range.end:
            return tok_node
    else:
        # For after attachment, the token must be the first token of the node.
        if tok_range.start == tok_node_range.start:
            return tok_node
    return None


def _select_before_or_after(
    comment: CommentInfo,
    before_node: ast.AST | None,
    after_node: ast.AST | None,
) -> tuple[Literal["before"] | Literal["after"], ast.AST]:
    if before_node and not after_node:
        return "before", before_node
    elif after_node and not before_node:
        return "after", after_node
    assert before_node and after_node, "At least one node must be present"
    assert isinstance(before_node, PosNode) and isinstance(after_node, PosNode)
    # If both nodes are present, select the one based on line similarity.
    before_line = get_pos_attributes(before_node)["end_lineno"]
    after_line = get_pos_attributes(after_node)["lineno"]
    comment_line = comment.comment.start[0]
    if before_line == comment_line:
        return "before", before_node
    else:
        return "after", after_node


def _try_attach_to_ast_node(
    ast_cache: SourceAstCache,
    comment: CommentInfo,
    filter_node_type: type[ast.AST] | None = None,
) -> bool:
    # Try attaching to the minimal node before/after the comment group.
    after_node: ast.AST | None = None
    if after_tok := comment.after_non_comment_tok:
        after_node = _node_attachable_comment_to(
            ast_cache, after_tok, filter_node_type, before=False
        )
        if after_node:
            debug_verbose_print(
                lambda: (
                    f"  Attachable as leading comment group {comment.comment} to node {filter_node_type} type {ast.dump(after_node)} at {get_pos_attributes(after_node)}"
                )
            )
    before_node: ast.AST | None = None
    if before_tok := comment.before_non_comment_tok:
        before_node = _node_attachable_comment_to(
            ast_cache, before_tok, filter_node_type, before=True
        )
        if before_node:
            debug_verbose_print(
                lambda: (
                    f"  Attachable as trailing comment group {comment.comment} to node {filter_node_type} type {ast.dump(before_node)} at {get_pos_attributes(before_node)}"
                )
            )
    if not before_node and not after_node:
        return False
    # Select the best attachment point based on proximity and node type.
    selected, selected_node = _select_before_or_after(comment, before_node, after_node)
    debug_verbose_print(
        lambda: (
            f"  Selected {selected} node {ast.dump(selected_node)} for comment group {comment.comment}"
        )
    )
    if selected == "after":
        add_leading_comments(selected_node, [comment.comment])
    else:
        add_trailling_comments(selected_node, [comment.comment])
    return True


def attach_comments_v2(module: ast.Module, ast_cache: SourceAstCache) -> None:
    """Alternative comment attachment using sequential grouping."""
    tokens = get_lossless_token_info(module)
    if tokens is None:
        return
    comments = _gather_comments(tokens)
    for comment in comments:
        debug_verbose_print(
            lambda: (
                f"Processing comment group {comment.comment} from index {comment.index}, before_tok={comment.before_non_comment_tok}, after_tok={comment.after_non_comment_tok}"
            )
        )
        if _try_attach_to_ast_node(ast_cache, comment, ast.stmt):
            # First try attaching to statements, which are more likely to be the intended targets for comments.
            continue
        if _try_attach_to_ast_node(ast_cache, comment):
            # Next try other nodes, which can capture inline comments.
            continue
        if (
            comment.after_non_comment_tok
            and comment.after_non_comment_tok.type == ENDMARKER
        ):
            # Comments are the last tokens in the module
            debug_verbose_print(lambda: "  Appended to module.")
            add_dangling_comments(ast_cache.module, [comment.comment])
            continue
        # Fallback: attach as dangling.
        debug_verbose_print(
            lambda: (
                "Could not attach comment group to adjacent nodes, attaching as dangling to module"
            )
        )
        add_dangling_comments(ast_cache.module, [comment.comment])
