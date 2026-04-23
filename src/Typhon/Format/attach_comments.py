# Attach comment tokens from lossless token info to AST nodes.
import ast
from dataclasses import dataclass
from tokenize import TokenInfo, COMMENT, ENDMARKER
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


def attach_comments(module: ast.Module, ast_cache: SourceAstCache) -> None:
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
