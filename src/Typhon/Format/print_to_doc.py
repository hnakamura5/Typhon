from __future__ import annotations

import ast
from contextlib import contextmanager
from typing import Literal, cast, override

from Typhon.Format.doc_render import DEFAULT_INDENT_WIDTH
from Typhon.Grammar.typhon_ast import (
    FunctionLiteral,
    FunctionType,
    RecordLiteral,
    get_completion_trigger_anchor,
    get_prefix_format_anchor,
    get_args_of_function_type,
    get_constant_raw_tokens,
    get_control_comprehension_def,
    get_defined_name,
    get_dangling_comments,
    get_function_literal_def,
    get_import_from_names,
    get_leading_comments,
    get_let_pattern_body,
    get_record_literal_fields,
    get_record_type_fields,
    get_return_of_function_type,
    get_star_arg_of_function_type,
    get_star_kwds_of_function_type,
    get_trailing_comments,
    get_type_annotation,
    get_wrapper_paren_tokens,
    has_comments,
    is_attributes_pattern,
    is_block_comment,
    is_control_comprehension,
    is_elseless_if_exp,
    is_empty_pass,
    is_function_literal,
    is_function_literal_def,
    is_function_literal_inline_return,
    is_if_let_implicit_none_check,
    is_inline_with,
    is_let,
    is_let_assign,
    is_let_else,
    is_optional,
    is_optional_pipe,
    is_pattern_tuple,
    is_pipe,
    is_record_literal,
    is_record_type,
    is_static,
    is_var_assign,
)
from ..Grammar.position import (
    PosNode,
    ExprFormatAnchors,
    get_block_stmt_anchors,
    get_expr_format_anchors,
)
from Typhon.Grammar.unparse_custom import CustomUnparseHelper
from Typhon.Transform.visitor import TyphonASTRawVisitor
from ..Driver.debugging import debug_verbose_print

from .doc_datatype import (
    Anchor,
    BREAK_PARENT,
    BreakParent,
    Doc,
    NIL,
    align,
    align_to_anchor,
    anchor,
    concat,
    group,
    if_break,
    line_or_space,
    line_suffix,
    softline,
    hardline,
    indent,
    join,
    space,
    text,
)

_INSERT_SPACE_AFTER_COMPREHENSION_KEYWORDS = False


def comma_space() -> Doc:
    return concat([text(","), line_or_space()])


def paren(content: Doc | list[Doc], optional_paren: bool = False) -> Doc:
    if isinstance(content, list):
        content = concat(content)
    return group(
        concat(
            [
                text("?(") if optional_paren else text("("),
                indent([softline(), content]),
                softline(),
                text(")"),
            ]
        )
    )


def bracket(content: Doc | list[Doc], optional_bracket: bool = False) -> Doc:
    if isinstance(content, list):
        content = concat(content)
    return group(
        concat(
            [
                text("?[") if optional_bracket else text("["),
                indent([softline(), content]),
                softline(),
                text("]"),
            ]
        )
    )


def brace(content: Doc | list[Doc]) -> Doc:
    if isinstance(content, list):
        content = concat(content)
    return group(
        concat(
            [
                text("{"),
                indent([softline(), content]),
                softline(),
                text("}"),
            ]
        ),
    )


class _PrintToDocVisitor(TyphonASTRawVisitor):
    """Translate Typhon AST nodes to Doc intermediate representation.

    This visitor intentionally supports a small, composable core and falls back to
    textual rendering for unsupported nodes.
    """

    def __init__(
        self,
        module: ast.Module,
        *,
        comprehension_printer: _PrintComprehensionToDocVisitor | None = None,
        insert_space_statement_between_statement_keywords_and_paren: bool = True,
    ):
        super().__init__()
        self.module = module
        # Only the helper. Not used for actual unparsing.
        self._helper = CustomUnparseHelper()
        self._comprehension_printer: _PrintComprehensionToDocVisitor = (
            comprehension_printer or _PrintComprehensionToDocVisitor(module, self)
        )
        self._is_comprehension_printer = (
            insert_space_statement_between_statement_keywords_and_paren
        )
        self._space_between_statement_keywords_and_paren = (
            text(" ")
            if insert_space_statement_between_statement_keywords_and_paren
            else NIL
        )
        self._space_between_comprehension_keywords_and_paren = (
            text(" ") if _INSERT_SPACE_AFTER_COMPREHENSION_KEYWORDS else NIL
        )
        self.comprehension_open_anchor: list[Anchor] = []

    def _get_current_comprehension_open_anchor(self) -> Anchor | None:
        if len(self.comprehension_open_anchor) == 0:
            return None
        return self.comprehension_open_anchor[-1]

    @contextmanager
    def _comprehension_open_anchor_ctx(self):
        open_anchor = anchor()
        self.comprehension_open_anchor.append(open_anchor)
        self._comprehension_printer.comprehension_open_anchor.append(open_anchor)
        yield open_anchor
        self._comprehension_printer.comprehension_open_anchor.pop()
        self.comprehension_open_anchor.pop()

    def _anchor_to_current(self, content: Doc | list[Doc], offset: int = 0):
        return align_to_anchor(
            content, self._get_current_comprehension_open_anchor(), offset
        )

    def _get_binop_symbol(self, op: ast.operator) -> str:
        return self._helper.get_binop_operator(op)

    def _get_unaryop_symbol(self, op: ast.unaryop) -> str:
        result = self._helper.get_unaryop_operator(op)
        if result == "not":
            return "!"
        return result

    def _get_boolop_symbol(self, op: ast.boolop) -> str:
        if isinstance(op, ast.And):
            return "&&"
        elif isinstance(op, ast.Or):
            return "||"
        else:
            raise ValueError(f"Unsupported boolean operator: {type(op)}")

    def _get_cmpop_symbol(self, op: ast.cmpop) -> str:
        return self._helper.get_cmpop_operator(op)

    def _maybe_wrap_group_paren(self, node: ast.expr, doc: Doc) -> Doc:
        wrappers = get_wrapper_paren_tokens(node)
        if not wrappers:
            return doc
        if len(wrappers) < 2:
            return doc
        return concat([text(wrappers[0].string), doc, text(wrappers[-1].string)])

    def _defined_name_doc(self, node: ast.AST, default: Doc) -> Doc:
        if defined_name := get_defined_name(node):
            return self._visit_doc(defined_name)
        return default

    def _completion_trigger_doc(
        self,
        node: ast.AST,
        default: Doc,
        *,
        optional_prefix: str | None = None,
    ) -> Doc:
        if anchor := get_completion_trigger_anchor(node):
            anchor_doc = self._visit_doc(anchor)
            if optional_prefix and isinstance(node, ast.expr) and is_optional(node):
                return concat([text(optional_prefix), anchor_doc])
            return anchor_doc
        return default

    def _prefixed_completion_trigger_doc(self, node: ast.AST, default: Doc) -> Doc:
        if get_completion_trigger_anchor(node) is None:
            return default
        return concat([self._completion_trigger_doc(node, text("")), default])

    def _wrapped_with_expr_anchor(
        self,
        node: ast.AST,
        content: Doc,
    ) -> Doc:
        expr_anchors = (
            get_expr_format_anchors(node) if isinstance(node, ast.expr) else None
        )
        debug_verbose_print(
            lambda: (
                f"Visiting node with expr anchors: {ast.dump(node, include_attributes=True)}\n"
                f"    Anchors: {expr_anchors}, Content: {content}\n"
            )
        )
        if not expr_anchors:
            return content
        if expr_anchors.surround_open is not None:
            assert expr_anchors.surround_close is not None, (
                f"Expected surround close anchor for node type {type(node).__name__} when surround open anchor is present"
            )
            open_doc = self._visit_doc(expr_anchors.surround_open)
            close_doc = self._visit_doc(expr_anchors.surround_close)
            if content is NIL:
                return concat([open_doc, close_doc])
            return group(
                [
                    open_doc,
                    indent([softline(), content]),
                    softline(),
                    close_doc,
                ]
            )
        else:
            return content

    # Ad-hoc preference to represent complex expression (with brace) should
    # be broken in the right-hand-side of assignment.
    def _prefer_break_complex_expr_in_assign(self, value: ast.expr) -> bool:
        if isinstance(
            value,
            (
                ast.Tuple,
                ast.List,
                ast.Set,
            ),
        ):
            return len(value.elts) > 0
        if isinstance(value, ast.Dict):
            return len(value.keys) > 0
        if isinstance(value, ast.Name) and is_record_literal(value):
            return len(get_record_literal_fields(value) or []) > 0
        if isinstance(value, ast.Name) and is_record_type(value):
            return len(get_record_type_fields(value) or []) > 0
        if isinstance(value, ast.Call):
            return len(value.args) + len(value.keywords) > 0
        if isinstance(
            value,
            (
                ast.IfExp,
                ast.ListComp,
                ast.SetComp,
                ast.GeneratorExp,
                ast.DictComp,
                ast.JoinedStr,
            ),
        ):
            return True
        if isinstance(value, ast.Name) and (
            is_function_literal(value) or is_control_comprehension(value)
        ):
            return True
        if get_wrapper_paren_tokens(value):
            return True
        return False

    def _visit_anchor_or(self, anchor: ast.Name | None, default: Doc):
        if anchor is not None:
            return self._visit_doc(anchor)
        return default

    def _prefix_anchor_doc(self, node: ast.AST | None, default_doc: Doc) -> Doc:
        if not node:
            return default_doc
        return self._visit_anchor_or(get_prefix_format_anchor(node), default_doc)

    def _stmt_separator_doc(self, prev_node: ast.stmt, node: ast.stmt) -> Doc:
        anchor = get_prefix_format_anchor(node)
        if anchor is None:
            return NIL
        if not (
            has_comments(anchor)
            or get_trailing_comments(prev_node)
            or get_leading_comments(node)
        ):
            return NIL
        return self._visit_doc(anchor)

    def _comma_combined_doc(
        self,
        elts: list[Doc],
        comma_anchors: list[ast.Name] | None,
        trailing_comma: ast.Name | None,
        add_if_break_last_comma: bool = False,
    ) -> Doc:
        parts: list[Doc] = []
        if trailing_comma:
            parts.append(BreakParent())
        for i, elt in enumerate(elts):
            parts.append(elt)
            is_last = i == len(elts) - 1
            if is_last:
                if trailing_comma:
                    parts.append(self._visit_doc(trailing_comma))
                elif add_if_break_last_comma:
                    # Append trailing comma when this group breaks.
                    parts.append(if_break(text(","), text("")))
            else:
                parts.append(
                    self._visit_anchor_or(
                        comma_anchors[i]
                        if comma_anchors and i < len(comma_anchors)
                        else None,
                        text(","),
                    )
                )
                parts.append(line_or_space())
        debug_verbose_print(lambda: f"Comma combined doc for element: parts={parts}\n")
        return concat(parts)

    def _visit_doc(self, node: ast.AST) -> Doc:
        doc = cast(Doc, self.visit(node))
        if isinstance(node, ast.expr):
            if leading := self._leading_comments_doc(node):
                doc = concat([leading, doc])
            if trailing := self._trailing_comment_doc(node):
                doc = concat([doc, trailing])
            if dangling := self._dangling_comments_doc(node):
                doc = concat([doc, hardline(), dangling])
            debug_verbose_print(
                lambda: (
                    f"Generating doc with comments for expr: {ast.dump(node, include_attributes=True)}\n"
                    f"    Leading: {leading}, Trailing: {trailing}, Dangling: {dangling}, Doc: {doc}\n"
                )
            )
        return doc

    def _stmt_paren(self, node: ast.AST, content: Doc | list[Doc]) -> Doc:
        if isinstance(content, list):
            content = concat(content)
        if isinstance(node, PosNode):
            if anchors := get_block_stmt_anchors(node):
                if (
                    anchors.open_paren_anchor is not None
                    and anchors.close_paren_anchor is not None
                ):
                    return group(
                        concat(
                            [
                                self._visit_doc(anchors.open_paren_anchor),
                                indent([softline(), content]),
                                softline(),
                                self._visit_doc(anchors.close_paren_anchor),
                            ]
                        )
                    )
        return paren(content)

    def _stmt_type_param_bracket(self, node: ast.AST, content: Doc | list[Doc]) -> Doc:
        if isinstance(content, list):
            content = concat(content)
        if isinstance(node, PosNode):
            if anchors := get_block_stmt_anchors(node):
                if (
                    anchors.open_type_param_bracket_anchor is not None
                    and anchors.close_type_param_bracket_anchor is not None
                ):
                    return group(
                        concat(
                            [
                                self._visit_doc(anchors.open_type_param_bracket_anchor),
                                indent([softline(), content]),
                                softline(),
                                self._visit_doc(
                                    anchors.close_type_param_bracket_anchor
                                ),
                            ]
                        )
                    )
        return bracket(content)

    def _stmt_begin_keyword_doc(self, node: ast.AST, keyword: str) -> Doc:
        if isinstance(node, PosNode):
            if anchors := get_block_stmt_anchors(node):
                for token_anchor in anchors.keywords:
                    if token_anchor.id == keyword:
                        return self._visit_doc(token_anchor)
        return text(keyword)

    def _stmt_inner_separator_doc(self, node: ast.AST, keyword: str) -> Doc:
        if isinstance(node, PosNode):
            if anchors := get_block_stmt_anchors(node):
                for token_anchor in anchors.inner_separator_anchors:
                    if token_anchor.id == keyword:
                        return self._visit_doc(token_anchor)
        return text(keyword)

    def _expr_keyword_doc(self, node: ast.AST, keyword: str) -> Doc:
        if isinstance(node, ast.expr):
            if anchors := get_expr_format_anchors(node):
                for token_anchor in anchors.keywords or []:
                    if token_anchor.id == keyword:
                        return self._visit_doc(token_anchor)
        return text(keyword)

    def _block_doc(
        self,
        body: list[ast.stmt],
        container: ast.AST | None = None,
        block_kind: Literal["body", "else", "finally"] = "body",
    ) -> Doc:
        open_brace_doc: Doc = text("{")
        close_brace_doc: Doc = text("}")
        close_anchor_node: ast.Name | None = None
        if container is not None and isinstance(container, PosNode):
            if anchors := get_block_stmt_anchors(container):
                if block_kind == "body":
                    open_anchor = anchors.open_brace_anchor
                    close_anchor = anchors.close_brace_anchor
                elif block_kind == "else":
                    open_anchor = anchors.else_brace_open_anchor
                    close_anchor = anchors.else_brace_close_anchor
                else:
                    open_anchor = anchors.finally_open_anchor
                    close_anchor = anchors.finally_close_anchor
                if open_anchor is not None:
                    open_brace_doc = self._visit_doc(open_anchor)
                if close_anchor is not None:
                    close_anchor_node = close_anchor
                    close_brace_doc = self._visit_doc(close_anchor)

        if len(body) == 0:
            return concat([space(), open_brace_doc, close_brace_doc])
        if len(body) == 1:
            # Special inlining case for single pass and ...
            stmt = body[0]
            if has_comments(stmt):
                # Placeholder pass for empty block
                if isinstance(stmt, ast.Pass) and is_empty_pass(stmt):
                    # This block must only contains the comment
                    inside_comments_doc, after_close_comments_doc = (
                        self._empty_pass_comment_docs(stmt, close_anchor_node)
                    )
                    result = concat(
                        [
                            space(),
                            open_brace_doc,
                            indent([hardline(), inside_comments_doc]),
                            hardline(),
                            close_brace_doc,
                            after_close_comments_doc,
                        ]
                    )
                    debug_verbose_print(
                        lambda: (
                            f"Empty block with pass statement: {ast.dump(stmt, include_attributes=True)} doc: {result}"
                        )
                    )
                    return result
            else:
                if isinstance(stmt, ast.Pass):
                    if is_empty_pass(stmt):  # empty block
                        return concat([space(), open_brace_doc, close_brace_doc])
                    # prefer flat form { pass }
                    return concat(
                        [
                            space(),
                            open_brace_doc,
                            space(),
                            text("pass"),
                            space(),
                            close_brace_doc,
                        ]
                    )
                if (
                    isinstance(stmt, ast.Expr)
                    and isinstance(stmt.value, ast.Constant)
                    and stmt.value.value == Ellipsis
                ):
                    # prefer flat form { ... }
                    return concat(
                        [
                            space(),
                            open_brace_doc,
                            space(),
                            text("..."),
                            space(),
                            close_brace_doc,
                        ]
                    )
        body_docs: list[Doc] = [self._stmt_doc_with_comments(body[0])]
        prev_stmt = body[0]
        for stmt in body[1:]:
            separator_doc = self._stmt_separator_doc(prev_stmt, stmt)
            body_docs.append(hardline())
            if separator_doc is not NIL:
                body_docs.extend([separator_doc, hardline()])
            body_docs.append(self._stmt_doc_with_comments(stmt))
            prev_stmt = stmt
        return group(
            [
                space(),
                open_brace_doc,
                indent([hardline(), concat(body_docs)]),
                hardline(),
                close_brace_doc,
            ]
        )

    def _empty_pass_comment_docs(
        self,
        node: ast.Pass,
        close_anchor: ast.Name | None,
    ) -> tuple[Doc, Doc]:
        comments = [
            *get_leading_comments(node),
            *get_trailing_comments(node),
            *get_dangling_comments(node),
        ]
        comments.sort(key=lambda comment: (comment.start[0], comment.start[1]))
        if close_anchor is None:
            inside_comments = comments
            after_close_comments: list = []
        else:
            close_pos = (close_anchor.lineno, close_anchor.col_offset)
            inside_comments = [
                comment
                for comment in comments
                if (comment.start[0], comment.start[1]) < close_pos
            ]
            after_close_comments = [
                comment
                for comment in comments
                if (comment.start[0], comment.start[1]) >= close_pos
            ]

        inside_doc = join(
            hardline(),
            [self._comment_text_doc(comment.string) for comment in inside_comments],
        )
        after_doc_parts: list[Doc] = []
        if close_anchor is not None:
            for comment in after_close_comments:
                is_comment_same_line = close_anchor.end_lineno == comment.start[0]
                if is_block_comment(comment):
                    after_doc_parts.append(
                        space() if is_comment_same_line else hardline()
                    )
                    after_doc_parts.append(self._comment_text_doc(comment.string))
                else:
                    if not is_comment_same_line:
                        after_doc_parts.append(hardline())
                    after_doc_parts.append(
                        line_suffix(
                            concat([text("  "), self._comment_text_doc(comment.string)])
                        )
                    )
                    after_doc_parts.append(BreakParent())
        return inside_doc, concat(after_doc_parts)

    def _unsupported_syntax_doc(self, node: ast.AST) -> Doc:
        debug_verbose_print(
            lambda: (
                f"Unsupported syntax in print_to_doc: {ast.dump(node, include_attributes=True)}"
            )
        )
        return text(f"<Unsupported syntax: {type(node).__name__}>")

    # Convert a comment token string to Doc, handling multi-line block comments.
    def _comment_text_doc(self, comment_string: str) -> Doc:
        lines = comment_string.split("\n")
        if len(lines) == 1:
            return text(comment_string)
        return join(hardline(), [text(line) for line in lines])

    def _leading_comments_doc(self, node: ast.AST) -> Doc | None:
        comments = get_leading_comments(node)
        if not comments:
            return None
        node_line = getattr(node, "lineno", None)
        parts: list[Doc] = []
        for i, c in enumerate(comments):
            is_last = i == len(comments) - 1
            next_c = comments[i + 1] if not is_last else None
            next_line = next_c.start[0] if next_c else (node_line or None)
            parts.append(self._comment_text_doc(c.string))
            break_here = False
            # Line comment
            break_here |= not is_block_comment(c)
            # Next token is on different line
            break_here |= next_line is not None and c.end[0] != next_line
            # Statement to be start in new line
            break_here |= isinstance(node, ast.stmt) and is_last
            debug_verbose_print(
                lambda: (
                    f"Leading comment: {c.string!r}, break_here: {break_here}, "
                    f"comment end line: {c.end[0]}, next token line: {next_line}, "
                    f"node line: {node_line}, is_block_comment: {is_block_comment(c)}"
                )
            )
            if isinstance(node, ast.Pass) and is_empty_pass(node):
                pass  # TODO: too ad-hoc?
            elif break_here:
                parts.append(hardline())
            else:
                parts.append(space())
        return concat(parts)

    def _trailing_comment_doc(self, node: ast.AST) -> Doc | None:
        comments = get_trailing_comments(node)
        if not comments:
            return None
        parts: list[Doc] = []
        for c in comments:
            is_comment_same_line = getattr(node, "end_lineno", None) == c.start[0]
            if is_block_comment(c):
                if is_comment_same_line:
                    parts.append(line_or_space())
                else:
                    parts.append(hardline())
                parts.append(self._comment_text_doc(c.string))
            else:
                # Line comment
                if not is_comment_same_line:
                    parts.append(hardline())
                parts.append(
                    line_suffix(concat([text("  "), self._comment_text_doc(c.string)]))
                )
                parts.append(BreakParent())
            debug_verbose_print(
                lambda: (
                    f"Trailing comment: {c.string!r} for node {ast.dump(node, include_attributes=True)}, parts: {parts} is_block_comment: {is_block_comment(c)}"
                )
            )
        return concat(parts)

    def _dangling_comments_doc(self, node: ast.AST) -> Doc | None:
        comments = get_dangling_comments(node)
        debug_verbose_print(
            lambda: (
                f"Dangling comments for node {ast.dump(node, include_attributes=True)}: {[c.string for c in comments]}"
            )
        )
        if not comments:
            return None
        parts: list[Doc] = []
        for c in comments:
            parts.append(self._comment_text_doc(c.string))
        return join(hardline(), parts)

    def _stmt_doc_with_comments(self, node: ast.stmt) -> Doc:
        """Wrap a statement's Doc with its leading, trailing, and dangling comments."""
        parts: list[Doc] = []
        if leading := self._leading_comments_doc(node):
            parts.append(leading)
        body = self._visit_doc(node)
        parts.append(body)
        if trailing := self._trailing_comment_doc(node):
            parts.append(trailing)
        if dangling := self._dangling_comments_doc(node):
            parts.append(dangling)  # TODO: Is this OK?
        if leading or trailing or dangling:
            debug_verbose_print(
                lambda: (
                    f"Generating doc with comments for stmt: {ast.dump(node, include_attributes=True)}\n"
                    f"    Leading: {leading}, Trailing: {trailing}, Dangling: {dangling}, Parts: {parts}\n"
                )
            )
        if not parts:
            return NIL
        if len(parts) == 1:
            return parts[0]
        debug_verbose_print(
            lambda: (
                f"Stmt with comments: {ast.dump(node, include_attributes=True)}, parts: {parts}, concatenated: {concat(parts)}"
            )
        )
        return concat(parts)

    def _doc_with_comments(self, node: ast.AST, body: Doc) -> Doc:
        """Wrap a node Doc with its leading, trailing, and dangling comments."""
        parts: list[Doc] = []
        if leading := self._leading_comments_doc(node):
            parts.append(leading)
        parts.append(body)
        if trailing := self._trailing_comment_doc(node):
            parts.append(trailing)
        if dangling := self._dangling_comments_doc(node):
            parts.extend([hardline(), dangling])
        if leading or trailing or dangling:
            debug_verbose_print(
                lambda: (
                    f"Generating doc with comments: {ast.dump(node, include_attributes=True)}\n"
                    f"    Leading: {leading}, Trailing: {trailing}, Dangling: {dangling}, Parts: {parts}\n"
                )
            )
        if len(parts) == 1:
            return parts[0]
        return concat(parts)

    def visit_Module(self, node: ast.Module) -> Doc:
        if len(node.body) == 0:
            if dangling := self._dangling_comments_doc(node):
                return dangling
            return NIL
        stmt_docs = [self._stmt_doc_with_comments(stmt) for stmt in node.body]
        result = join(hardline(), stmt_docs)
        if dangling := self._dangling_comments_doc(node):
            result = concat([result, hardline(), dangling])
        return result

    def visit_Delete(self, node: ast.Delete) -> Doc:
        return self._unsupported_syntax_doc(node)

    def visit_Global(self, node: ast.Global) -> Doc:
        return self._unsupported_syntax_doc(node)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> Doc:
        return self._unsupported_syntax_doc(node)

    def visit_Name(self, node: ast.Name) -> Doc:
        return text(node.id)

    def visit_NamedExpr(self, node: ast.NamedExpr) -> Doc:
        return self._unsupported_syntax_doc(node)

    def visit_Expr(self, node: ast.Expr) -> Doc:
        return self._visit_doc(node.value)

    def visit_Compare(self, node: ast.Compare) -> Doc:
        comps: list[Doc] = [self._visit_doc(node.left)]
        for op, right in zip(node.ops, node.comparators):
            op_symbol = self._get_cmpop_symbol(op)
            comps.append(space())
            comps.append(text(op_symbol))
            comps.append(space())
            comps.append(self._visit_doc(right))
        return self._maybe_wrap_group_paren(node, concat(comps))

    def visit_Constant(self, node: ast.Constant) -> Doc:
        raw_tokens = get_constant_raw_tokens(node)
        if raw_tokens is not None:
            return self._maybe_wrap_group_paren(
                node,
                text("".join(tok.string for tok in raw_tokens)),
            )
        if node.value is None:
            return text("None")
        raise ValueError(
            f"Unsupported constant without raw tokens: {ast.dump(node, include_attributes=True)}"
        )

    def visit_JoinedStr(self, node: ast.JoinedStr) -> Doc:
        parts: list[Doc] = [text('f"')]
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(text(value.value))
            else:
                parts.append(self._visit_doc(value))
        parts.append(text('"'))
        return concat(parts)

    def visit_FormattedValue(self, node: ast.FormattedValue) -> Doc:
        parts: list[Doc] = [
            self._completion_trigger_doc(node, text("{")),
            self._visit_doc(node.value),
        ]
        if node.conversion != -1:
            parts.extend(
                [
                    text("!"),
                    self._defined_name_doc(node, text(chr(node.conversion))),
                ]
            )
        if node.format_spec is not None:
            parts.extend(
                [
                    self._prefix_anchor_doc(node.format_spec, text(":")),
                    self._visit_doc(node.format_spec),
                ]
            )
        parts.append(text("}"))
        return concat(parts)

    def visit_BinOp(self, node: ast.BinOp) -> Doc:
        op = self._get_binop_symbol(node.op)
        binop_open_anchor = anchor()
        doc = group(
            [
                binop_open_anchor,
                self._visit_doc(node.left),
                align_to_anchor(
                    [
                        line_or_space(),
                        text(op),
                        space(),
                        self._visit_doc(node.right),
                    ],
                    binop_open_anchor,
                    0,
                ),
            ]
        )
        return self._maybe_wrap_group_paren(node, doc)

    def visit_BoolOp(self, node: ast.BoolOp) -> Doc:
        op = self._get_boolop_symbol(node.op)
        doc = group(
            join(
                concat([space(), text(op), space()]),
                [self._visit_doc(v) for v in node.values],
            )
        )
        return self._maybe_wrap_group_paren(node, doc)

    def _if_exp_chain_doc(
        self, node: ast.IfExp, keyword: Literal["if", "elif"] = "if"
    ) -> Doc:
        # Keep this segment ungrouped so outer else/elif breaks also force
        # the body after if/elif to break consistently.
        doc = concat(
            [
                text(keyword),
                self._space_between_comprehension_keywords_and_paren,
                paren(self._visit_doc(node.test)),
                self._anchor_to_current(
                    [
                        line_or_space(),
                        self._visit_doc(node.body),
                    ],
                    DEFAULT_INDENT_WIDTH + 1,
                ),
            ]
        )
        if not is_elseless_if_exp(node):
            if isinstance(node.orelse, ast.IfExp):
                return concat(  # chain the child IfExp
                    [
                        doc,
                        self._anchor_to_current(
                            [
                                line_or_space(),
                                self._if_exp_chain_doc(node.orelse, "elif"),
                            ],
                            1,
                        ),
                    ]
                )
            else:
                doc = concat(  # else
                    [
                        doc,
                        self._anchor_to_current(
                            [
                                line_or_space(),
                                text("else"),
                                self._anchor_to_current(
                                    [
                                        line_or_space(),
                                        self._visit_doc(node.orelse),
                                    ],
                                    DEFAULT_INDENT_WIDTH + 1,
                                ),
                            ],
                            1,
                        ),
                    ]
                )
        return doc

    def visit_IfExp(self, node: ast.IfExp) -> Doc:
        with self._comprehension_open_anchor_ctx() as open_anchor:
            parts: list[Doc] = [
                open_anchor,
                text("("),  # No space here
                self._if_exp_chain_doc(node, "if"),
                text(")"),
            ]
        return group(parts)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Doc:
        op = self._get_unaryop_symbol(node.op)
        doc = concat([text(op), self._visit_doc(node.operand)])
        return self._maybe_wrap_group_paren(node, doc)

    def visit_Await(self, node: ast.Await) -> Doc:
        return concat([text("await"), space(), self._visit_doc(node.value)])

    def _pipe_operator_doc(self, node: ast.Call, is_optional: bool) -> Doc:
        pipe_open_anchor = anchor()
        doc = group(
            [
                pipe_open_anchor,
                self._visit_doc(node.args[0]),
                align_to_anchor(
                    [
                        line_or_space(),
                        text("?|>" if is_optional else "|>"),
                        space(),
                        self._visit_doc(node.func),
                    ],
                    pipe_open_anchor,
                    0,
                ),
            ]
        )
        return self._maybe_wrap_group_paren(node, doc)

    def visit_Call(self, node: ast.Call) -> Doc:
        if is_pipe(node):
            return self._pipe_operator_doc(node, is_optional=False)
        if is_optional_pipe(node):
            return self._pipe_operator_doc(node, is_optional=True)
        args_docs = [self._visit_doc(arg) for arg in node.args]
        kw_docs = [self._keyword_doc(kw) for kw in node.keywords]
        comma_anchor_info = get_expr_format_anchors(node)
        comma_anchors = comma_anchor_info.commas if comma_anchor_info else None
        trailing_comma = comma_anchor_info.trailing_comma if comma_anchor_info else None
        args_doc = self._comma_combined_doc(
            args_docs + kw_docs,
            comma_anchors,
            trailing_comma,
            add_if_break_last_comma=True,
        )
        doc = group(
            [
                self._visit_doc(node.func),
                self._wrapped_with_expr_anchor(node, args_doc),
            ],
        )
        return self._maybe_wrap_group_paren(node, doc)

    def visit_Attribute(self, node: ast.Attribute) -> Doc:
        doc = group(
            [
                self._visit_doc(node.value),
                softline(),
                self._completion_trigger_doc(
                    node,
                    text("?." if is_optional(node) else "."),
                    optional_prefix="?",
                ),
                self._defined_name_doc(node, text(node.attr)),
            ]
        )
        return self._maybe_wrap_group_paren(node, doc)

    def visit_Subscript(self, node: ast.Subscript) -> Doc:
        # Special ad-hoc case where slice is tuple.
        # x[a, b] is x[(a, b)] in AST.
        # Problematic case is x[(a, b)], that is x[((a, b))] in AST, which is different semantics than the original code.
        if isinstance(node.slice, ast.Tuple):
            slice_doc = self._tuple_inner_doc(node.slice)
        else:
            slice_doc = self._visit_doc(node.slice)
        doc = group(
            [
                self._visit_doc(node.value),
                self._wrapped_with_expr_anchor(node, slice_doc),
            ]
        )
        return self._maybe_wrap_group_paren(node, doc)

    def visit_Slice(self, node: ast.Slice) -> Doc:
        lower = self._visit_doc(node.lower) if node.lower is not None else NIL
        upper = self._visit_doc(node.upper) if node.upper is not None else NIL
        if node.step is None:
            return concat(
                [lower, self._prefix_anchor_doc(node.upper, text(":")), upper]
            )
        step = self._visit_doc(node.step)
        return concat(
            [
                lower,
                self._prefix_anchor_doc(node.upper, text(":")),
                upper,
                self._prefix_anchor_doc(node.step, text(":")),
                step,
            ]
        )

    def visit_Starred(self, node: ast.Starred) -> Doc:
        return concat(
            [
                self._prefix_anchor_doc(node, text("*")),
                self._visit_doc(node.value),
            ]
        )

    def visit_List(self, node: ast.List) -> Doc:
        comma_anchor_info = get_expr_format_anchors(node)
        inner = self._comma_combined_doc(
            [self._visit_doc(e) for e in node.elts],
            comma_anchor_info.commas if comma_anchor_info else None,
            comma_anchor_info.trailing_comma if comma_anchor_info else None,
        )
        doc = self._wrapped_with_expr_anchor(node, inner)
        return self._maybe_wrap_group_paren(node, doc)

    def visit_Dict(self, node: ast.Dict) -> Doc:
        entries: list[Doc] = []
        for key, value in zip(node.keys, node.values):
            if key is None:
                entries.append(
                    concat(
                        [
                            self._prefix_anchor_doc(value, text("**")),
                            self._visit_doc(value),
                        ]
                    )
                )
            else:
                entries.append(
                    concat(
                        [
                            self._visit_doc(key),
                            self._prefix_anchor_doc(value, text(":")),
                            space(),
                            self._visit_doc(value),
                        ]
                    )
                )
        comma_anchor_info = get_expr_format_anchors(node)
        entries_doc = self._comma_combined_doc(
            entries,
            comma_anchor_info.commas if comma_anchor_info else None,
            comma_anchor_info.trailing_comma if comma_anchor_info else None,
        )
        return self._wrapped_with_expr_anchor(node, entries_doc)

    def visit_Set(self, node: ast.Set) -> Doc:
        comma_anchor_info = get_expr_format_anchors(node)
        items_doc = self._comma_combined_doc(
            [self._visit_doc(e) for e in node.elts],
            comma_anchor_info.commas if comma_anchor_info else None,
            comma_anchor_info.trailing_comma if comma_anchor_info else None,
        )
        return self._wrapped_with_expr_anchor(node, items_doc)

    def _tuple_inner_doc(self, node: ast.Tuple) -> Doc:
        comma_anchor_info = get_expr_format_anchors(node)
        if len(node.elts) == 1 and (
            comma_anchor_info is None or comma_anchor_info.trailing_comma is None
        ):
            inner = concat([self._visit_doc(node.elts[0]), comma_space()])
        else:
            inner = self._comma_combined_doc(
                [self._visit_doc(e) for e in node.elts],
                comma_anchor_info.commas if comma_anchor_info else None,
                comma_anchor_info.trailing_comma if comma_anchor_info else None,
            )
        return inner

    def visit_Tuple(self, node: ast.Tuple) -> Doc:
        inner = self._tuple_inner_doc(node)
        return self._wrapped_with_expr_anchor(node, inner)

    def _keyword_doc(self, kw: ast.keyword) -> Doc:
        if kw.arg is None:
            return self._doc_with_comments(
                kw,
                concat(
                    [
                        self._prefix_anchor_doc(kw, text("**")),
                        self._visit_doc(kw.value),
                    ]
                ),
            )
        return self._doc_with_comments(
            kw,
            concat(
                [
                    self._defined_name_doc(kw, text(kw.arg)),
                    text("="),
                    self._visit_doc(kw.value),
                ]
            ),
        )

    def visit_comprehension(self, node: ast.comprehension) -> Doc:
        decl = text("let") if is_let(node) else text("var")
        target = concat([decl, space(), self._visit_doc(node.target)])
        if type_ann := get_type_annotation(node):
            target = concat(
                [
                    target,
                    self._prefix_anchor_doc(type_ann, text(":")),
                    space(),
                    self._visit_doc(type_ann),
                ]
            )

        head = (
            [
                text("async"),
                space(),
            ]
            if node.is_async
            else []
        )
        head.extend(
            [
                text("for"),
                self._space_between_comprehension_keywords_and_paren,
                paren(
                    [
                        target,
                        space(),
                        text("in"),
                        space(),
                        self._visit_doc(node.iter),
                    ]
                ),
            ]
        )
        parts: list[Doc] = [concat(head)]
        for cond in node.ifs:
            parts.extend(
                [
                    space(),
                    text("if"),
                    self._space_between_comprehension_keywords_and_paren,
                    paren(self._visit_doc(cond)),
                ]
            )
        return group(parts)

    def _comprehension_list_doc(self, generators: list[ast.comprehension]) -> Doc:
        return join(space(), [self._visit_doc(gen) for gen in generators])

    def _comp_doc(
        self, node: ast.ListComp | ast.SetComp | ast.GeneratorExp, open: str, close: str
    ) -> Doc:
        with self._comprehension_open_anchor_ctx() as open_anchor:
            return group(
                [
                    open_anchor,
                    text(open),
                    self._comprehension_list_doc(node.generators),
                    align_to_anchor(
                        [
                            line_or_space(),
                            group(
                                [
                                    text("yield"),
                                    space(),
                                    self._visit_doc(node.elt),
                                ]
                            ),
                        ],
                        open_anchor,
                        DEFAULT_INDENT_WIDTH + len(open),
                    ),
                    text(close),
                ]
            )

    def visit_ListComp(self, node: ast.ListComp) -> Doc:
        return self._comp_doc(node, "[", "]")

    def visit_SetComp(self, node: ast.SetComp) -> Doc:
        return self._comp_doc(node, "{", "}")

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> Doc:
        return self._comp_doc(node, "(", ")")

    def visit_DictComp(self, node: ast.DictComp) -> Doc:
        with self._comprehension_open_anchor_ctx() as open_anchor:
            return group(
                [
                    open_anchor,
                    text("{"),  # No space here
                    self._comprehension_list_doc(node.generators),
                    self._anchor_to_current(
                        [
                            line_or_space(),
                            text("yield"),
                            space(),
                            self._visit_doc(node.key),
                            self._prefix_anchor_doc(node.value, text(":")),
                            space(),
                            self._visit_doc(node.value),
                        ],
                        DEFAULT_INDENT_WIDTH + 1,
                    ),
                    text("}"),
                ]
            )

    def visit_Assign(self, node: ast.Assign) -> Doc:
        decl_prefix = ""
        if is_var_assign(node):
            decl_prefix = "var"
        elif is_let_assign(node):
            decl_prefix = "let"

        targets_doc = join(comma_space(), [self._visit_doc(t) for t in node.targets])
        value_doc = self._visit_doc(node.value)
        if self._prefer_break_complex_expr_in_assign(node.value):
            value_doc = concat([space(), value_doc])
        else:
            value_doc = indent([line_or_space(), value_doc])
        return group(
            [
                text(decl_prefix),
                space(),
                targets_doc,
                space(),
                text("="),
                value_doc,
            ]
        )

    def visit_AnnAssign(self, node: ast.AnnAssign) -> Doc:
        decl_prefix = ""
        if is_var_assign(node):
            decl_prefix = "var"
        elif is_let_assign(node):
            decl_prefix = "let"
        base = concat(
            [
                text(decl_prefix),
                space(),
                self._visit_doc(node.target),
                self._prefix_anchor_doc(node.annotation, text(":")),
                space(),
                self._visit_doc(node.annotation),
            ]
        )
        if node.value is None:
            return base
        value_doc = self._visit_doc(node.value)
        if self._prefer_break_complex_expr_in_assign(
            node.value
        ) or self._prefer_break_complex_expr_in_assign(node.annotation):
            # Prefer to break in expressions rather than next of equal.
            value_doc = concat([space(), value_doc])
        else:
            value_doc = indent([line_or_space(), value_doc])
        return group(
            [
                base,
                space(),
                text("="),
                value_doc,
            ]
        )

    def visit_AugAssign(self, node: ast.AugAssign) -> Doc:
        op = self._get_binop_symbol(node.op)
        value_doc = self._visit_doc(node.value)
        if self._prefer_break_complex_expr_in_assign(node.value):
            value_doc = concat([space(), value_doc])
        else:
            value_doc = indent([line_or_space(), value_doc])
        return group(
            [
                self._visit_doc(node.target),
                space(),
                text(op),
                text("="),
                value_doc,
            ]
        )

    def visit_Return(self, node: ast.Return) -> Doc:
        if node.value is None:
            return text("return")
        return concat([text("return"), space(), self._visit_doc(node.value)])

    def visit_Yield(self, node: ast.Yield) -> Doc:
        if node.value is None:
            return text("yield")
        return concat([text("yield"), space(), self._visit_doc(node.value)])

    def visit_YieldFrom(self, node: ast.YieldFrom) -> Doc:
        return concat(
            [
                text("yield"),
                space(),
                self._prefix_anchor_doc(node.value, text("from")),
                space(),
                self._visit_doc(node.value),
            ]
        )

    def visit_Raise(self, node: ast.Raise) -> Doc:
        if node.exc is None:
            return text("raise")
        result = concat([text("raise"), space(), self._visit_doc(node.exc)])
        if node.cause is not None:
            result = concat(
                [result, space(), text("from"), space(), self._visit_doc(node.cause)]
            )
        return result

    def visit_Break(self, node: ast.Break) -> Doc:
        return text("break")

    def visit_Continue(self, node: ast.Continue) -> Doc:
        return text("continue")

    def visit_Pass(self, node: ast.Pass) -> Doc:
        if is_empty_pass(node):
            return NIL
        return text("pass")

    def visit_Assert(self, node: ast.Assert) -> Doc:
        result = concat([text("assert"), space(), self._visit_doc(node.test)])
        if node.msg is not None:
            result = concat([result, comma_space(), self._visit_doc(node.msg)])
        return result

    def _alias_doc(self, node: ast.alias) -> Doc:
        result: Doc = self._defined_name_doc(node, text(node.name))
        if node.asname is not None:
            defined_name = get_defined_name(node)
            as_doc: Doc = text("as")
            target_doc: Doc = text(node.asname)
            if defined_name is not None:
                as_doc = self._completion_trigger_doc(defined_name, as_doc)
                target_doc = self._visit_doc(defined_name)
            result = concat(
                [
                    text(node.name),
                    space(),
                    as_doc,
                    space(),
                    target_doc,
                ]
            )
        return self._doc_with_comments(node, result)

    def _alias_list_doc(self, aliases: list[ast.alias]) -> Doc:
        if len(aliases) == 0:
            return NIL
        first_alias_anchor = anchor()
        docs = [self._alias_doc(a) for a in aliases]
        parts: list[Doc] = [first_alias_anchor, docs[0]]
        for alias, a in zip(aliases[1:], docs[1:], strict=False):
            parts.extend(
                [
                    self._completion_trigger_doc(alias, text(",")),
                    align_to_anchor([line_or_space(), a], first_alias_anchor),
                ]
            )
        return group(parts)

    def visit_Import(self, node: ast.Import) -> Doc:
        return group(
            [
                self._stmt_begin_keyword_doc(node, "import"),
                space(),
                self._alias_list_doc(node.names),
            ]
        )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Doc:
        module_names = get_import_from_names(node)
        if module_names:
            module = concat(
                [
                    self._completion_trigger_doc(node, text("." * node.level)),
                    *[
                        self._prefixed_completion_trigger_doc(
                            module_name, text(module_name.id)
                        )
                        for module_name in module_names
                    ],
                ]
            )
        else:
            module = concat(
                [
                    self._completion_trigger_doc(node, text("." * node.level)),
                    text(node.module or ""),
                ]
            )
        return group(
            [
                self._stmt_begin_keyword_doc(node, "from"),
                space(),
                module,
                space(),
                self._stmt_begin_keyword_doc(node, "import"),
                space(),
                self._alias_list_doc(node.names),
            ]
        )

    def _type_param_doc(self, node: ast.type_param) -> Doc:
        if isinstance(node, ast.TypeVar):
            parts: list[Doc] = [self._defined_name_doc(node, text(node.name))]
            if node.bound is not None:
                parts.extend(
                    [
                        self._prefix_anchor_doc(node.bound, text(":")),
                        space(),
                        self._visit_doc(node.bound),
                    ]
                )
            return self._doc_with_comments(node, concat(parts))
        elif isinstance(node, ast.TypeVarTuple):
            return self._doc_with_comments(
                node,
                concat(
                    [
                        self._prefix_anchor_doc(node, text("*")),
                        self._defined_name_doc(node, text(node.name)),
                    ]
                ),
            )
        elif isinstance(node, ast.ParamSpec):
            return self._doc_with_comments(
                node,
                concat(
                    [
                        self._prefix_anchor_doc(node, text("**")),
                        self._defined_name_doc(node, text(node.name)),
                    ]
                ),
            )
        return self._doc_with_comments(node, self._unsupported_syntax_doc(node))

    def _type_params_doc(
        self,
        node: ast.AST,
        type_params: list[ast.type_param],
        commas: list[ast.Name] | None = None,
        trailing_comma: ast.Name | None = None,
    ) -> Doc:
        return self._stmt_type_param_bracket(
            node,
            self._comma_combined_doc(
                [self._type_param_doc(p) for p in type_params], commas, trailing_comma
            ),
        )

    def visit_TypeAlias(self, node: ast.TypeAlias) -> Doc:
        parts: list[Doc] = [
            self._stmt_begin_keyword_doc(node, "type"),
            space(),
            self._visit_doc(node.name),
        ]
        if len(node.type_params) > 0:
            parts.append(self._type_params_doc(node, node.type_params))
        parts.extend([space(), text("="), space(), self._visit_doc(node.value)])
        return group(parts)

    def _let_patterns_match_doc(
        self, body: list[ast.stmt], innermost_body: list[ast.stmt]
    ) -> list[Doc]:
        """
        match <subject1>:
            case <pattern1>:
                match <subject2>:
                    case <pattern2>:
                        ...
                            match <subjectN>:
                                case <patternN> if <cond>:
                                    <body>
            case _:
                pass # Default case possibly exists

        -->

        let <pattern1> = <subject1>,
                   <pattern2> = <subject2>,
                   ...,
                   <patternN> = <subjectN>
                   [;<cond>]
        """
        # TODO: Implement while-let pattern
        # body must be nested match with single pattern case. cond is only attached to the innermost pattern.
        assert body is not innermost_body
        assert len(body) == 1
        match_stmt = body[0]
        assert isinstance(match_stmt, ast.Match)
        debug_verbose_print(
            lambda: (
                f"_let_patterns_match_doc: match_stmt={ast.dump(match_stmt, include_attributes=True)}"
            )
        )
        assert len(match_stmt.cases) > 0
        # First case is the case
        case = match_stmt.cases[0]
        pattern = case.pattern
        parts: list[Doc] = [
            self._visit_doc(pattern),
            space(),
            self._prefix_anchor_doc(match_stmt.subject, text("=")),
            line_or_space(),
            indent(
                self._visit_doc(match_stmt.subject),
            ),
        ]
        cond = case.guard
        if cond and is_if_let_implicit_none_check(cond):
            cond = None
        case_body = case.body
        if case_body is innermost_body:
            # Base case: pattern matches directly to the body.
            if cond is not None:
                parts.extend(
                    [
                        self._prefix_anchor_doc(cond, text(";")),
                        line_or_space(),
                        self._visit_doc(cond),
                    ]
                )
            return parts
        else:
            assert cond is None, "Only innermost pattern can have condition"
            parts.append(comma_space())
            parts.extend(self._let_patterns_match_doc(case_body, innermost_body))
            return parts

    def _let_else_doc(self, node: ast.If, cond_doc: Doc, body: list[ast.stmt]) -> Doc:
        # body is empty for statement case.
        assert len(body) == 0
        return cond_doc

    def _if_while_body(self, keyword: str, node: ast.If | ast.While) -> Doc:
        if let_pattern := get_let_pattern_body(node):
            # if-let or while-let pattern
            body = let_pattern.body
            pattens = self._let_patterns_match_doc(node.body, body)
            parts = [
                self._stmt_begin_keyword_doc(
                    node, "let" if let_pattern.is_let else "var"
                ),
                space(),
            ]
            parts.extend(pattens)
            cond_doc = group(parts)
            if isinstance(node, ast.If) and is_let_else(node):
                # let-else pattern.
                return self._let_else_doc(node, cond_doc, body)
        else:
            body = node.body
            cond_doc = self._visit_doc(node.test)
        body_doc = group(
            [
                (
                    text("elif")
                    if keyword == "elif"
                    else self._stmt_begin_keyword_doc(node, keyword)
                ),
                self._space_between_statement_keywords_and_paren,
                self._stmt_paren(node, cond_doc),
                self._block_doc(body, container=node),
            ]
        )
        return body_doc

    def _if_chain_doc(self, node: ast.If, keyword: Literal["if", "elif"] = "if") -> Doc:
        body_doc = self._if_while_body(keyword, node)
        if len(node.orelse) == 0:
            return body_doc
        if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
            # Note in if-elif chain orelse is single statement
            return group(
                [body_doc, space(), self._if_chain_doc(node.orelse[0], "elif")]
            )
        return group(
            [
                body_doc,
                space(),
                self._stmt_inner_separator_doc(node, "else"),
                self._block_doc(node.orelse, container=node, block_kind="else"),
            ]
        )

    def visit_If(self, node: ast.If) -> Doc:
        return self._if_chain_doc(node, "if")

    def visit_While(self, node: ast.While) -> Doc:
        doc = self._if_while_body("while", node)
        if len(node.orelse) > 0:
            doc = concat(
                [
                    doc,
                    space(),
                    self._stmt_inner_separator_doc(node, "else"),
                    self._block_doc(node.orelse, container=node, block_kind="else"),
                ]
            )
        return doc

    def visit_For(self, node: ast.For) -> Doc:
        target = concat(
            [
                text("let" if is_let(node) else "var"),
                space(),
                self._visit_doc(node.target),
            ]
        )
        if type_ann := get_type_annotation(node):
            target = concat(
                [
                    target,
                    self._prefix_anchor_doc(type_ann, text(":")),
                    space(),
                    self._visit_doc(type_ann),
                ]
            )
        keyword = self._stmt_begin_keyword_doc(node, "for")
        doc = group(
            [
                keyword,
                self._space_between_statement_keywords_and_paren,
                self._stmt_paren(
                    node,
                    [
                        target,
                        space(),
                        text("in"),
                        space(),
                        self._visit_doc(node.iter),
                    ],
                ),
                self._block_doc(node.body, container=node),
            ]
        )
        if len(node.orelse) > 0:
            doc = concat(
                [
                    doc,
                    space(),
                    self._stmt_inner_separator_doc(node, "else"),
                    self._block_doc(node.orelse, container=node, block_kind="else"),
                ]
            )
        return doc

    def visit_AsyncFor(self, node: ast.AsyncFor) -> Doc:
        for_doc = self.visit_For(cast(ast.For, node))
        return group([self._stmt_begin_keyword_doc(node, "async"), space(), for_doc])

    def _withitem_doc(self, node: ast.withitem) -> Doc:
        context_expr_doc = self._visit_doc(node.context_expr)
        if node.optional_vars:
            decl = text("let") if is_let(node) else text("var")
            target = self._visit_doc(node.optional_vars)
            if type_ann := get_type_annotation(node):
                target = concat(
                    [
                        target,
                        self._prefix_anchor_doc(type_ann, text(":")),
                        space(),
                        self._visit_doc(type_ann),
                    ]
                )
            return concat(
                [
                    decl,
                    space(),
                    target,
                    space(),
                    text("="),
                    line_or_space(),
                    indent(context_expr_doc),
                ]
            )
        else:
            return context_expr_doc

    def visit_With(self, node: ast.With) -> Doc:
        parts = [
            self._stmt_begin_keyword_doc(node, "with"),
            self._space_between_statement_keywords_and_paren,
        ]
        items = join(
            comma_space(),
            [self._withitem_doc(i) for i in node.items],
        )
        if is_inline_with(node):
            parts.append(items)
            parts.append(hardline())
        else:
            parts.append(self._stmt_paren(node, items))
            parts.extend([self._block_doc(node.body, container=node)])
        doc = group(parts)
        return doc

    def visit_AsyncWith(self, node: ast.AsyncWith) -> Doc:
        with_doc = self.visit_With(cast(ast.With, node))
        return group([self._stmt_begin_keyword_doc(node, "async"), space(), with_doc])

    def _except_handler_doc(
        self, node: ast.ExceptHandler, *, is_star: bool = False
    ) -> Doc:
        keyword_doc: Doc
        if is_star:
            keyword_doc = concat(
                [
                    self._stmt_begin_keyword_doc(node, "except"),
                    self._stmt_begin_keyword_doc(node, "*"),
                ]
            )
        else:
            keyword_doc = self._stmt_begin_keyword_doc(node, "except")
        if node.type is None:
            head = keyword_doc
        else:
            head_parts: list[Doc] = [
                keyword_doc,
                self._space_between_statement_keywords_and_paren,
            ]
            if node.name is not None:
                as_parts = [
                    self._visit_doc(node.type),
                    space(),
                    text("as"),
                    space(),
                    self._defined_name_doc(node, text(node.name)),
                ]
                head_parts.append(self._stmt_paren(node, as_parts))
            else:
                head_parts.append(self._stmt_paren(node, self._visit_doc(node.type)))
            head = concat(head_parts)
        return concat([head, self._block_doc(node.body, container=node)])

    def _try_body_doc(
        self,
        node: ast.Try | ast.TryStar,
        *,
        is_star: bool = False,
    ) -> Doc:
        parts: list[Doc] = [
            self._stmt_begin_keyword_doc(node, "try"),
            self._block_doc(node.body, container=node),
        ]
        for handler in node.handlers:
            parts.extend([space(), self._except_handler_doc(handler, is_star=is_star)])
        if len(node.orelse) > 0:
            parts.extend(
                [
                    space(),
                    self._stmt_inner_separator_doc(node, "else"),
                    self._block_doc(node.orelse, container=node, block_kind="else"),
                ]
            )
        if len(node.finalbody) > 0:
            parts.extend(
                [
                    space(),
                    self._stmt_inner_separator_doc(node, "finally"),
                    self._block_doc(
                        node.finalbody,
                        container=node,
                        block_kind="finally",
                    ),
                ]
            )
        return group(parts)

    def visit_Try(self, node: ast.Try) -> Doc:
        return self._try_body_doc(node, is_star=False)

    def visit_TryStar(self, node: ast.TryStar) -> Doc:
        return self._try_body_doc(node, is_star=True)

    def visit_MatchValue(self, node: ast.MatchValue) -> Doc:
        return self._visit_doc(node.value)

    def visit_MatchSingleton(self, node: ast.MatchSingleton) -> Doc:
        if node.value is None:
            return text("None")
        if node.value is True:
            return text("True")
        if node.value is False:
            return text("False")
        raise ValueError(f"Unsupported singleton in match pattern: {node.value!r}")

    def visit_MatchSequence(self, node: ast.MatchSequence) -> Doc:
        items = join(comma_space(), [self._visit_doc(p) for p in node.patterns])
        if is_pattern_tuple(node):
            if len(node.patterns) == 1:
                items = concat([items, comma_space()])
            return paren(items)
        return bracket(items)

    def visit_MatchMapping(self, node: ast.MatchMapping) -> Doc:
        entries: list[Doc] = [
            concat(
                [
                    self._visit_doc(key),
                    self._prefix_anchor_doc(pattern, text(":")),
                    space(),
                    self._visit_doc(pattern),
                ]
            )
            for key, pattern in zip(node.keys, node.patterns)
        ]
        if node.rest is not None:
            entries.append(
                concat([self._prefix_anchor_doc(node, text("**")), text(node.rest)])
            )
        return brace(join(comma_space(), entries))

    def visit_MatchStar(self, node: ast.MatchStar) -> Doc:
        if node.name is None:
            return text("*_")
        star_target: Doc = text(node.name)
        if type_ann := get_type_annotation(node):
            star_target = concat(
                [
                    star_target,
                    self._prefix_anchor_doc(type_ann, text(":")),
                    space(),
                    self._visit_doc(type_ann),
                ]
            )
        return concat([self._prefix_anchor_doc(node, text("*")), star_target])

    def visit_MatchAs(self, node: ast.MatchAs) -> Doc:
        if node.pattern is None and node.name is None:
            return text("_")
        if node.pattern is None:
            assert node.name is not None
            capture: Doc = self._defined_name_doc(node, text(node.name))
            if type_ann := get_type_annotation(node):
                capture = concat(
                    [
                        capture,
                        self._prefix_anchor_doc(type_ann, text(":")),
                        space(),
                        self._visit_doc(type_ann),
                    ]
                )
            return capture
        if node.name is None:
            return self._visit_doc(node.pattern)
        capture = self._defined_name_doc(node, text(node.name))
        if type_ann := get_type_annotation(node):
            capture = concat(
                [
                    capture,
                    self._prefix_anchor_doc(type_ann, text(":")),
                    space(),
                    self._visit_doc(type_ann),
                ]
            )
        return concat(
            [self._visit_doc(node.pattern), space(), text("as"), space(), capture]
        )

    def visit_MatchOr(self, node: ast.MatchOr) -> Doc:
        return join(
            concat([space(), text("|"), space()]),
            [self._visit_doc(p) for p in node.patterns],
        )

    def _attribute_pattern_doc(self, node: ast.MatchClass) -> Doc:
        # { .attr1, .attr2=pattern, ... }
        entries: list[Doc] = []
        for attr, pattern in zip(node.kwd_attrs, node.kwd_patterns):
            default_name_capture = (
                isinstance(pattern, ast.MatchAs)
                and pattern.pattern is None
                and pattern.name == attr
                and get_type_annotation(pattern) is None
            )
            if default_name_capture:
                # The case { .attr }.
                entries.append(concat([text("."), text(attr)]))
            else:
                # The case { .attr = pattern }.
                entries.append(
                    concat(
                        [
                            text("."),
                            text(attr),
                            space(),
                            text("="),
                            space(),
                            self._visit_doc(pattern),
                        ]
                    )
                )
        return concat(
            [
                text("{"),
                join(comma_space(), entries),
                text("}"),
            ]
        )

    def visit_MatchClass(self, node: ast.MatchClass) -> Doc:
        if isinstance(node.cls, ast.Name) and is_attributes_pattern(node.cls):
            return self._attribute_pattern_doc(node)
        args: list[Doc] = [self._visit_doc(pattern) for pattern in node.patterns]
        args.extend(
            [
                concat(
                    [text(attr), space(), text("="), space(), self._visit_doc(pattern)]
                )
                for attr, pattern in zip(node.kwd_attrs, node.kwd_patterns)
            ]
        )
        return concat(
            [
                self._visit_doc(node.cls),
                paren(join(comma_space(), args)),
            ]
        )

    def _match_case_doc(self, node: ast.match_case) -> Doc:
        head: list[Doc] = [
            text("case"),
            self._space_between_statement_keywords_and_paren,
            paren(self._visit_doc(node.pattern)),
        ]
        if node.guard is not None:
            head.extend(
                [
                    space(),
                    text("if"),
                    self._space_between_statement_keywords_and_paren,
                    paren(self._visit_doc(node.guard)),
                ]
            )
        return concat([concat(head), self._block_doc(node.body)])

    def visit_Match(self, node: ast.Match) -> Doc:
        return group(
            [
                text("match"),
                self._space_between_statement_keywords_and_paren,
                self._stmt_paren(node, self._visit_doc(node.subject)),
                space(),
                text("{"),
                indent(
                    concat(
                        [
                            hardline(),
                            join(
                                hardline(),
                                [self._match_case_doc(c) for c in node.cases],
                            ),
                        ]
                    )
                ),
                hardline(),
                text("}"),
            ]
        )

    def _visit_Decorators(self, decos: list[ast.expr]) -> list[Doc]:
        return [group([text("@"), self._visit_doc(d), hardline()]) for d in decos]

    def visit_ClassDef(self, node: ast.ClassDef) -> Doc:
        deco_docs = self._visit_Decorators(node.decorator_list)
        args: list[Doc] = [self._visit_doc(base) for base in node.bases]
        args.extend(
            [
                concat([text(k.arg), text("="), self._visit_doc(k.value)])
                if k.arg is not None
                else concat(
                    [
                        self._prefix_anchor_doc(k.value, text("**")),
                        self._visit_doc(k.value),
                    ]
                )
                for k in node.keywords
            ]
        )
        stmt_anchor = get_block_stmt_anchors(node)
        class_head = [
            self._stmt_begin_keyword_doc(node, "class"),
            space(),
            self._defined_name_doc(node, text(node.name)),
        ]
        if len(node.type_params) > 0:
            class_head.append(
                self._type_params_doc(
                    node,
                    node.type_params,
                    stmt_anchor.type_param_comma_anchors if stmt_anchor else None,
                    stmt_anchor.type_param_trailing_comma_anchor
                    if stmt_anchor
                    else None,
                )
            )
        if len(args) > 0:
            class_head.extend(
                [
                    self._stmt_paren(
                        node,
                        self._comma_combined_doc(
                            args,
                            stmt_anchor.param_comma_anchors if stmt_anchor else [],
                            stmt_anchor.param_trailing_comma_anchor
                            if stmt_anchor
                            else None,
                        ),
                    ),
                ]
            )
        class_head.extend([self._block_doc(node.body, container=node)])
        return group(deco_docs + [group(class_head)])

    def _typed_arg_doc(
        self,
        arg: ast.arg,
        *,
        prefix: str = "",
        default: ast.expr | None = None,
    ) -> Doc:
        parts: list[Doc] = []
        if prefix:
            parts.append(text(prefix))
        parts.append(self._defined_name_doc(arg, text(arg.arg)))
        if arg.annotation is not None:
            parts.extend(
                [
                    self._prefix_anchor_doc(arg.annotation, text(":")),
                    space(),
                    self._visit_doc(arg.annotation),
                ]
            )
        if default is not None:
            parts.extend([space(), text("="), space(), self._visit_doc(default)])
        return self._doc_with_comments(arg, concat(parts))

    def _arguments_doc(
        self,
        args: ast.arguments,
        commas: list[ast.Name] | None = None,
        trailing_comma: ast.Name | None = None,
    ) -> Doc:
        params: list[Doc] = []
        for arg in args.posonlyargs:
            params.append(self._typed_arg_doc(arg))
        if len(args.posonlyargs) > 0:
            params.append(text("/"))
        for index, arg in enumerate(args.args):
            default_index = index - (len(args.args) - len(args.defaults))
            if default_index >= 0:
                params.append(
                    self._typed_arg_doc(arg, default=args.defaults[default_index])
                )
            else:
                params.append(self._typed_arg_doc(arg))

        if args.vararg is not None:
            params.append(self._typed_arg_doc(args.vararg, prefix="*"))
        elif len(args.kwonlyargs) > 0:
            params.append(text("*"))

        for kw_arg, kw_default in zip(args.kwonlyargs, args.kw_defaults):
            if kw_default is None:
                params.append(self._typed_arg_doc(kw_arg))
            else:
                params.append(self._typed_arg_doc(kw_arg, default=kw_default))

        if args.kwarg is not None:
            params.append(self._typed_arg_doc(args.kwarg, prefix="**"))

        return group(
            self._comma_combined_doc(
                params, commas if commas is not None else [], trailing_comma
            )
        )

    def _visit_FunctionDef_AsyncFunctionDef(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> Doc:
        deco_docs = self._visit_Decorators(node.decorator_list)
        stmt_anchor = get_block_stmt_anchors(node)
        head_parts: list[Doc] = []
        if is_static(node):
            head_parts.extend([self._stmt_begin_keyword_doc(node, "static"), space()])
        if isinstance(node, ast.AsyncFunctionDef):
            head_parts.extend([self._stmt_begin_keyword_doc(node, "async"), space()])
        head_parts.extend(
            [
                self._stmt_begin_keyword_doc(node, "def"),
                space(),
                self._defined_name_doc(node, text(node.name)),
            ]
        )
        if len(node.type_params) > 0:
            head_parts.append(
                self._type_params_doc(
                    node,
                    node.type_params,
                    stmt_anchor.type_param_comma_anchors if stmt_anchor else None,
                    stmt_anchor.type_param_trailing_comma_anchor
                    if stmt_anchor
                    else None,
                )
            )
        head_parts.append(
            self._stmt_paren(
                node,
                self._arguments_doc(
                    node.args,
                    stmt_anchor.param_comma_anchors if stmt_anchor else None,
                    stmt_anchor.param_trailing_comma_anchor if stmt_anchor else None,
                ),
            )
        )
        if node.returns is not None:
            head_parts.extend(
                [
                    space(),
                    self._prefix_anchor_doc(node.returns, text("->")),
                    space(),
                    self._visit_doc(node.returns),
                ]
            )
        head_parts.extend([self._block_doc(node.body, container=node)])
        return group(deco_docs + [group(head_parts)])

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Doc:
        return self._visit_FunctionDef_AsyncFunctionDef(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Doc:
        return self._visit_FunctionDef_AsyncFunctionDef(node)

    def visit_Lambda(self, node: ast.Lambda) -> Doc:
        return self._maybe_wrap_group_paren(
            node,
            group(
                [
                    paren(self._arguments_doc(node.args)),
                    space(),
                    text("=>"),
                    space(),
                    self._visit_doc(node.body),
                ]
            ),
        )

    def visit_RecordLiteral(self, node: ast.Name) -> Doc:
        fields = get_record_literal_fields(node)
        if fields is None:
            raise ValueError("RecordLiteral node has no field metadata")
        if len(fields) == 0:
            return group([text("{|"), space(), text("|}")])
        field_docs: list[Doc] = []
        for name, annotation, value in fields:
            parts: list[Doc] = [self._visit_doc(name)]
            if annotation is not None:
                parts.extend(
                    [
                        self._prefix_anchor_doc(annotation, text(":")),
                        space(),
                        self._visit_doc(annotation),
                    ]
                )
            parts.extend(
                [
                    space(),
                    self._prefix_anchor_doc(value, text("=")),
                    space(),
                    self._visit_doc(value),
                ]
            )
            field_docs.append(concat(parts))

        comma_anchor_info = get_expr_format_anchors(node)
        fields_doc = self._comma_combined_doc(
            field_docs,
            comma_anchor_info.commas if comma_anchor_info else None,
            comma_anchor_info.trailing_comma if comma_anchor_info else None,
        )
        return self._wrapped_with_expr_anchor(node, fields_doc)

    def visit_RecordType(self, node: ast.Name) -> Doc:
        fields = get_record_type_fields(node)
        if fields is None:
            raise ValueError("RecordType node has no field metadata")
        if len(fields) == 0:
            return group([text("{|"), space(), text("|}")])
        field_docs = [
            concat(
                [
                    self._visit_doc(name),
                    self._prefix_anchor_doc(annotation, text(":")),
                    space(),
                    self._visit_doc(annotation),
                ]
            )
            for name, annotation in fields
        ]
        comma_anchor_info = get_expr_format_anchors(node)
        fields_doc = self._comma_combined_doc(
            field_docs,
            comma_anchor_info.commas if comma_anchor_info else None,
            comma_anchor_info.trailing_comma if comma_anchor_info else None,
        )
        return self._wrapped_with_expr_anchor(node, fields_doc)

    def _arg_doc(self, arg: ast.arg) -> Doc:
        parts: list[Doc] = [self._defined_name_doc(arg, text(arg.arg))]
        if arg.annotation is not None:
            parts.extend(
                [
                    self._prefix_anchor_doc(arg.annotation, text(":")),
                    space(),
                    self._visit_doc(arg.annotation),
                ]
            )
        return self._doc_with_comments(arg, concat(parts))

    def visit_FunctionType(self, node: FunctionType) -> Doc:
        arguments_doc: list[Doc] = []
        for arg in get_args_of_function_type(node):
            arguments_doc.append(self._arg_doc(arg))
        if star_arg := get_star_arg_of_function_type(node):
            arguments_doc.append(
                concat(
                    [
                        self._prefix_anchor_doc(star_arg, text("*")),
                        self._arg_doc(star_arg),
                    ]
                )
            )
        if star_kwds := get_star_kwds_of_function_type(node):
            arguments_doc.append(
                concat(
                    [
                        self._prefix_anchor_doc(star_kwds, text("**")),
                        self._arg_doc(star_kwds),
                    ]
                )
            )
        comma_anchor_info = get_expr_format_anchors(node)
        debug_verbose_print(
            lambda: (
                f"FunctionType arguments doc for {ast.dump(node)}: {arguments_doc}, comma_anchor_info={comma_anchor_info}"
            )
        )
        return_type = get_return_of_function_type(node)
        return self._maybe_wrap_group_paren(
            node,
            group(
                [
                    self._wrapped_with_expr_anchor(
                        node,
                        self._comma_combined_doc(
                            arguments_doc,
                            comma_anchor_info.commas if comma_anchor_info else None,
                            comma_anchor_info.trailing_comma
                            if comma_anchor_info
                            else None,
                        ),
                    ),
                    space(),
                    self._prefix_anchor_doc(return_type, text("->")),
                    space(),
                    self._visit_doc(return_type)
                    if return_type is not None
                    else text("None"),
                ]
            ),
        )

    def visit_FunctionLiteral(self, node: FunctionLiteral) -> Doc:
        func_def = get_function_literal_def(node)
        assert func_def is not None, (
            "FunctionLiteral must have a corresponding FunctionDef"
        )
        arg_comma_anchor_info = get_expr_format_anchors(node)
        head_parts: list[Doc] = []
        head_parts.extend(
            [
                self._wrapped_with_expr_anchor(
                    node,
                    self._arguments_doc(
                        func_def.args,
                        arg_comma_anchor_info.commas if arg_comma_anchor_info else None,
                        arg_comma_anchor_info.trailing_comma
                        if arg_comma_anchor_info
                        else None,
                    ),
                ),
                space(),
            ]
        )
        if func_def.returns is not None:
            head_parts.extend(
                [
                    self._prefix_anchor_doc(func_def.returns, text("->")),
                    space(),
                    self._visit_doc(func_def.returns),
                    space(),
                ]
            )
        head_parts.append(self._expr_keyword_doc(node, "=>"))
        if is_function_literal_inline_return(node):
            assert len(func_def.body) == 1, (
                "Inline return function literal must have single statement body"
            )
            if stmt := func_def.body[0]:
                if isinstance(stmt, ast.Return) and stmt.value is not None:
                    # Special case for single return value.
                    return group(head_parts + [space(), self._visit_doc(stmt.value)])
        return self._maybe_wrap_group_paren(
            node,
            group(head_parts + [self._block_doc(func_def.body, container=func_def)]),
        )

    def visit_ControlComprehension(self, node: ast.Name) -> Doc:
        if func_def := get_control_comprehension_def(node):
            with self._comprehension_open_anchor_ctx() as open_anchor:
                result = concat(
                    [
                        open_anchor,
                        text("("),  # No space here
                        self._comprehension_printer._visit_doc(func_def),
                        text(")"),
                    ]
                )
                debug_verbose_print(
                    lambda: f"Control comprehension doc for {node.id}: {result}"
                )
                return result
        raise ValueError(f"Unsupported control comprehension: {node.id}")


class _PrintComprehensionToDocVisitor(_PrintToDocVisitor):
    def __init__(self, module: ast.Module, parent: _PrintToDocVisitor):
        super().__init__(
            module,
            comprehension_printer=self,
            insert_space_statement_between_statement_keywords_and_paren=_INSERT_SPACE_AFTER_COMPREHENSION_KEYWORDS,
        )
        self._parent = parent

    @override
    def _let_else_doc(self, node: ast.If, cond_doc: Doc, body: list[ast.stmt]) -> Doc:
        # let comprehension has return as body.
        assert (
            len(body) == 1
            and isinstance(body[0], ast.Return)
            and body[0].value is not None
        )
        return group(
            [
                cond_doc,
                text(";"),
                line_or_space(),
                self._visit_doc(body[0].value),
            ]
        )

    # Entry point for comprehension body
    @override
    def visit_FunctionDef(self, node: ast.FunctionDef) -> Doc:
        assert len(node.body) < 3, "Comprehension body must have at most 2 statements"
        debug_verbose_print(
            lambda: f"Visiting function def in comprehension body: {ast.dump(node)}"
        )
        return join(
            concat([text(";"), line_or_space()]),
            [self._visit_doc(stmt) for stmt in node.body],
        )

    @override
    def visit_Return(self, node: ast.Return) -> Doc:
        debug_verbose_print(
            lambda: f"Visiting return in comprehension body: {ast.dump(node)}"
        )
        if node.value is None:
            return NIL
        return self._visit_doc(node.value)

    @override
    def _block_doc(
        self,
        body: list[ast.stmt],
        container: ast.AST | None = None,
        block_kind: Literal["body", "else", "finally"] = "body",
    ) -> Doc:
        # 'Block' must be single expression or yield.
        assert len(body) == 1
        stmt = body[0]
        assert self._get_current_comprehension_open_anchor(), (
            "Comprehension block must be within a comprehension"
        )
        # Falling back to parent for contents of the block.
        if isinstance(stmt, ast.Expr):
            content = self._visit_doc(stmt.value)
        elif isinstance(stmt, ast.Yield) and stmt.value is not None:
            content = self._visit_doc(stmt.value)
        else:  # TODO: Only return?
            content = self._visit_doc(stmt)
        debug_verbose_print(
            lambda: f"Comprehension block content: {ast.dump(stmt)} -> {content}"
        )
        return self._anchor_to_current(
            [line_or_space(), content], DEFAULT_INDENT_WIDTH + 1
        )

    # Override for let comprehension
    @override
    def visit_Assign(self, node: ast.Assign) -> Doc:
        return super().visit_Assign(node)


def print_to_doc(node: ast.AST) -> Doc:
    if isinstance(node, ast.Module):
        module = node
    else:
        module = ast.Module(
            body=[ast.Expr(value=cast(ast.expr, node))], type_ignores=[]
        )
    visitor = _PrintToDocVisitor(module)
    return cast(Doc, visitor.visit(node))
