from __future__ import annotations

import ast
from contextlib import contextmanager
from typing import Literal, cast, override

from Typhon.Format.doc_render import DEFAULT_INDENT_WIDTH
from Typhon.Grammar.typhon_ast import (
    FunctionLiteral,
    FunctionType,
    RecordLiteral,
    get_args_of_function_type,
    get_constant_raw_tokens,
    get_control_comprehension_def,
    get_dangling_comments,
    get_function_literal_def,
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
    get_call_argument_comma_anchors,
    get_trailing_comma_anchor,
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


def comma() -> Doc:
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

    def _comma_combined_doc(
        self,
        elts: list[Doc],
        comma_anchors: list[ast.Name] | None,
        trailing_comma: ast.Name | None,
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
                else:
                    # Append trailling comma if call is multi-line.
                    parts.append(if_break(text(","), text("")))
            else:
                parts.append(
                    self._visit_anchor_or(
                        comma_anchors[i] if comma_anchors else None, comma()
                    )
                )
                parts.append(line_or_space())
        return concat(parts)

    def _visit_doc(self, node: ast.AST) -> Doc:
        doc = cast(Doc, self.visit(node))
        if isinstance(node, ast.expr):
            if leading := self._leading_comments_doc(node):
                doc = concat([leading, doc])
            if trailing := self._trailing_comment_doc(node):
                doc = concat([doc, trailing])
        return doc

    def _block_doc(self, body: list[ast.stmt], container: ast.AST | None = None) -> Doc:
        if len(body) == 0:
            # Empty block: check for dangling comments from the container
            if container is not None:
                if dangling := self._dangling_comments_doc(container):
                    return group(
                        [
                            space(),
                            text("{"),
                            indent([hardline(), dangling]),
                            hardline(),
                            text("}"),
                        ]
                    )
            return concat([space(), text("{"), text("}")])
        if len(body) == 1:
            # Special inlining case for single pass and ...
            stmt = body[0]
            if has_comments(stmt):
                # Placeholder pass for empty block
                if isinstance(stmt, ast.Pass) and is_empty_pass(stmt):
                    # This block must only contains the comment
                    result = concat(
                        [
                            space(),
                            text("{"),
                            indent([hardline(), self._stmt_doc_with_comments(stmt)]),
                            hardline(),
                            text("}"),
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
                        return concat([space(), text("{"), text("}")])
                    # prefer flat form { pass }
                    return concat(
                        [space(), text("{"), space(), text("pass"), space(), text("}")]
                    )
                if (
                    isinstance(stmt, ast.Expr)
                    and isinstance(stmt.value, ast.Constant)
                    and stmt.value.value == Ellipsis
                ):
                    # prefer flat form { ... }
                    return concat(
                        [space(), text("{"), space(), text("..."), space(), text("}")]
                    )
        return group(
            [
                space(),
                text("{"),
                indent(
                    [
                        hardline(),
                        join(
                            hardline(),
                            [self._stmt_doc_with_comments(stmt) for stmt in body],
                        ),
                    ]
                ),
                hardline(),
                text("}"),
            ]
        )

    def _typed_name_doc(self, arg: ast.arg) -> Doc:
        base = text(arg.arg)
        if arg.annotation is None:
            return base
        return concat([base, text(":"), space(), self._visit_doc(arg.annotation)])

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
            if is_block_comment(c):
                parts.extend([line_or_space(), self._comment_text_doc(c.string)])
            else:
                # Line comment
                parts.append(
                    line_suffix(concat([text("  "), self._comment_text_doc(c.string)]))
                )
                # parts.extend([text("  "), self._comment_text_doc(c.string)])
                # if not isinstance(node, ast.stmt):
                #     # Force line break even node is not statement.
                #     # statement has already breakafter it.
                #     parts.append(hardline())
                parts.append(BreakParent())

                # parts.append(
                #     line_suffix(concat([text("  "), self._comment_text_doc(c.string)]))
                # )
                # Line comments (# ...) extend to end of line;
                # force enclosing group to break so a newline follows.
                # TODO: If this is expression (so in group) this makes assignment broken.
                # if not is_block_comment(c):
                # parts.append(hardline())
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
        debug_verbose_print(
            lambda: (
                f"Generating doc for stmt: {ast.dump(node, include_attributes=True)}\n"
                f"    Leading comments doc: {leading}, parts: {parts}\n"
            )
        )
        body = self._visit_doc(node)
        parts.append(body)
        if trailing := self._trailing_comment_doc(node):
            parts.append(trailing)
        if dangling := self._dangling_comments_doc(node):
            parts.append(dangling)  # TODO: Is this OK?
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
        if raw_tokens:
            return self._maybe_wrap_group_paren(
                node,
                text("".join(tok.string for tok in raw_tokens)),
            )
        if node.value is None:
            return text("None")
        raise ValueError(f"Unsupported constant without raw tokens: {node.value!r}")

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
        parts: list[Doc] = [text("{"), self._visit_doc(node.value)]
        if node.conversion != -1:
            parts.extend([text("!"), text(chr(node.conversion))])
        if node.format_spec is not None:
            parts.extend([text(":"), self._visit_doc(node.format_spec)])
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
        kw_docs = [
            concat([text(kw.arg), text("="), self._visit_doc(kw.value)])
            if kw.arg is not None
            else concat([text("**"), self._visit_doc(kw.value)])
            for kw in node.keywords
        ]
        comma_anchors = get_call_argument_comma_anchors(node)
        trailing_comma = get_trailing_comma_anchor(node)
        args_doc = self._comma_combined_doc(
            args_docs + kw_docs, comma_anchors, trailing_comma
        )
        doc = group(
            [
                self._visit_doc(node.func),
                paren(args_doc, is_optional(node)),
            ],
        )
        return self._maybe_wrap_group_paren(node, doc)

    def visit_Attribute(self, node: ast.Attribute) -> Doc:
        doc = group(
            [
                self._visit_doc(node.value),
                softline(),
                text("?." if is_optional(node) else "."),
                text(node.attr),
            ]
        )
        return self._maybe_wrap_group_paren(node, doc)

    def visit_Subscript(self, node: ast.Subscript) -> Doc:
        doc = group(
            [
                self._visit_doc(node.value),
                bracket(
                    self._visit_doc(node.slice), optional_bracket=is_optional(node)
                ),
            ]
        )
        return self._maybe_wrap_group_paren(node, doc)

    def visit_Slice(self, node: ast.Slice) -> Doc:
        lower = self._visit_doc(node.lower) if node.lower is not None else NIL
        upper = self._visit_doc(node.upper) if node.upper is not None else NIL
        if node.step is None:
            return concat([lower, text(":"), upper])
        step = self._visit_doc(node.step)
        return concat([lower, text(":"), upper, text(":"), step])

    def visit_Starred(self, node: ast.Starred) -> Doc:
        return concat([text("*"), self._visit_doc(node.value)])

    def visit_List(self, node: ast.List) -> Doc:
        has_trailing_comma = get_trailing_comma_anchor(node) is not None
        items = [self._visit_doc(e) for e in node.elts]
        if has_trailing_comma and len(items) > 0:
            inner = concat([join(concat([text(","), hardline()]), items), text(",")])
        else:
            inner = join(comma(), items)
        doc = bracket(
            [
                inner,
            ]
        )
        return self._maybe_wrap_group_paren(node, doc)

    def visit_Dict(self, node: ast.Dict) -> Doc:
        has_trailing_comma = get_trailing_comma_anchor(node) is not None
        entries: list[Doc] = []
        for key, value in zip(node.keys, node.values):
            if key is None:
                entries.append(concat([text("**"), self._visit_doc(value)]))
            else:
                entries.append(
                    concat(
                        [
                            self._visit_doc(key),
                            text(":"),
                            space(),
                            self._visit_doc(value),
                        ]
                    )
                )
        if has_trailing_comma and len(entries) > 0:
            entries_doc = concat(
                [
                    join(concat([text(","), hardline()]), entries),
                    text(","),
                ]
            )
        else:
            entries_doc = join(comma(), entries)
        return brace(entries_doc)

    def visit_Set(self, node: ast.Set) -> Doc:
        has_trailing_comma = get_trailing_comma_anchor(node) is not None
        items = [self._visit_doc(e) for e in node.elts]
        if has_trailing_comma and len(items) > 0:
            items_doc = concat(
                [
                    join(concat([text(","), hardline()]), items),
                    text(","),
                ]
            )
        else:
            items_doc = join(comma(), items)
        return brace(items_doc)

    def visit_Tuple(self, node: ast.Tuple) -> Doc:
        has_trailing_comma = get_trailing_comma_anchor(node) is not None
        if has_trailing_comma and len(node.elts) > 0:
            inner = concat(
                [
                    join(
                        concat([text(","), hardline()]),
                        [self._visit_doc(e) for e in node.elts],
                    ),
                    text(","),
                ]
            )
        elif len(node.elts) == 1:
            inner = concat([self._visit_doc(node.elts[0]), comma()])
        else:
            inner = join(comma(), [self._visit_doc(e) for e in node.elts])
        return paren(inner)

    def visit_comprehension(self, node: ast.comprehension) -> Doc:
        decl = text("let") if is_let(node) else text("var")
        target = concat([decl, space(), self._visit_doc(node.target)])
        if type_ann := get_type_annotation(node):
            target = concat([target, text(":"), space(), self._visit_doc(type_ann)])

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
                            text(":"),
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

        targets_doc = join(comma(), [self._visit_doc(t) for t in node.targets])
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
                text(":"),
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
            [text("yield"), space(), text("from"), space(), self._visit_doc(node.value)]
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
            result = concat([result, comma(), self._visit_doc(node.msg)])
        return result

    def _alias_doc(self, node: ast.alias) -> Doc:
        result: Doc = text(node.name)
        if node.asname is not None:
            result = concat([result, space(), text("as"), space(), text(node.asname)])
        return result

    def _alias_list_doc(self, aliases: list[ast.alias]) -> Doc:
        if len(aliases) == 0:
            return NIL
        first_alias_anchor = anchor()
        docs = [self._alias_doc(a) for a in aliases]
        parts: list[Doc] = [first_alias_anchor, docs[0]]
        for a in docs[1:]:
            parts.extend(
                [
                    text(","),
                    align_to_anchor([line_or_space(), a], first_alias_anchor),
                ]
            )
        return group(parts)

    def visit_Import(self, node: ast.Import) -> Doc:
        return group(
            [
                text("import"),
                space(),
                self._alias_list_doc(node.names),
            ]
        )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Doc:
        module = concat([text("." * node.level), text(node.module or "")])
        return group(
            [
                text("from"),
                space(),
                module,
                space(),
                text("import"),
                space(),
                self._alias_list_doc(node.names),
            ]
        )

    def _type_param_doc(self, node: ast.type_param) -> Doc:
        if isinstance(node, ast.TypeVar):
            parts: list[Doc] = [text(node.name)]
            if node.bound is not None:
                parts.extend([text(":"), space(), self._visit_doc(node.bound)])
            return concat(parts)
        elif isinstance(node, ast.TypeVarTuple):
            return concat([text("*"), text(node.name)])
        elif isinstance(node, ast.ParamSpec):
            return concat([text("**"), text(node.name)])
        return self._unsupported_syntax_doc(node)

    def _type_params_doc(self, type_params: list[ast.type_param]) -> Doc:
        return bracket(
            join(comma(), [self._type_param_doc(p) for p in type_params]),
        )

    def visit_TypeAlias(self, node: ast.TypeAlias) -> Doc:
        parts: list[Doc] = [
            text("type"),
            space(),
            self._visit_doc(node.name),
        ]
        if len(node.type_params) > 0:
            parts.append(self._type_params_doc(node.type_params))
        parts.extend([space(), text("="), space(), self._visit_doc(node.value)])
        return concat(parts)

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
            text("="),
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
                parts.extend([text(";"), line_or_space(), self._visit_doc(cond)])
            return parts
        else:
            assert cond is None, "Only innermost pattern can have condition"
            parts.append(comma())
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
            parts = [text("let" if let_pattern.is_let else "var"), space()]
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
                text(keyword),
                self._space_between_statement_keywords_and_paren,
                paren(cond_doc),
                self._block_doc(body),
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
        return group([body_doc, space(), text("else"), self._block_doc(node.orelse)])

    def visit_If(self, node: ast.If) -> Doc:
        return self._if_chain_doc(node, "if")

    def visit_While(self, node: ast.While) -> Doc:
        doc = self._if_while_body("while", node)
        if len(node.orelse) > 0:
            doc = concat([doc, space(), text("else"), self._block_doc(node.orelse)])
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
            target = concat([target, text(":"), space(), self._visit_doc(type_ann)])
        doc = concat(
            [
                text("for"),
                self._space_between_statement_keywords_and_paren,
                paren(
                    [
                        target,
                        space(),
                        text("in"),
                        space(),
                        self._visit_doc(node.iter),
                    ]
                ),
                self._block_doc(node.body),
            ]
        )
        if len(node.orelse) > 0:
            doc = concat([doc, space(), text("else"), self._block_doc(node.orelse)])
        return doc

    def visit_AsyncFor(self, node: ast.AsyncFor) -> Doc:
        for_doc = self.visit_For(cast(ast.For, node))
        return concat([text("async"), space(), for_doc])

    def _withitem_doc(self, node: ast.withitem) -> Doc:
        context_expr_doc = self._visit_doc(node.context_expr)
        if node.optional_vars:
            decl = text("let") if is_let(node) else text("var")
            target = self._visit_doc(node.optional_vars)
            if type_ann := get_type_annotation(node):
                target = concat([target, text(":"), space(), self._visit_doc(type_ann)])
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
            text("with"),
            self._space_between_statement_keywords_and_paren,
        ]
        items = join(
            comma(),
            [self._withitem_doc(i) for i in node.items],
        )
        if is_inline_with(node):
            parts.append(items)
            parts.append(hardline())
        else:
            parts.append(paren(items))
            parts.extend([self._block_doc(node.body)])
        doc = concat(parts)
        return doc

    def visit_AsyncWith(self, node: ast.AsyncWith) -> Doc:
        with_doc = self.visit_With(cast(ast.With, node))
        return concat([text("async"), space(), with_doc])

    def _except_handler_doc(
        self, node: ast.ExceptHandler, *, is_star: bool = False
    ) -> Doc:
        keyword = "except*" if is_star else "except"
        if node.type is None:
            head = text(keyword)
        else:
            head_parts: list[Doc] = [
                text(keyword),
                self._space_between_statement_keywords_and_paren,
            ]
            if node.name is not None:
                as_parts = [
                    self._visit_doc(node.type),
                    space(),
                    text("as"),
                    space(),
                    text(node.name),
                ]
                head_parts.append(paren(as_parts))
            else:
                head_parts.append(paren(self._visit_doc(node.type)))
            head = concat(head_parts)
        return concat([head, self._block_doc(node.body)])

    def _try_body_doc(
        self,
        node: ast.Try | ast.TryStar,
        *,
        is_star: bool = False,
    ) -> Doc:
        parts: list[Doc] = [text("try"), self._block_doc(node.body)]
        for handler in node.handlers:
            parts.extend([space(), self._except_handler_doc(handler, is_star=is_star)])
        if len(node.orelse) > 0:
            parts.extend([space(), text("else"), self._block_doc(node.orelse)])
        if len(node.finalbody) > 0:
            parts.extend([space(), text("finally"), self._block_doc(node.finalbody)])
        return concat(parts)

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
        items = join(comma(), [self._visit_doc(p) for p in node.patterns])
        if is_pattern_tuple(node):
            if len(node.patterns) == 1:
                items = concat([items, comma()])
            return paren(items)
        return bracket(items)

    def visit_MatchMapping(self, node: ast.MatchMapping) -> Doc:
        entries: list[Doc] = [
            concat([self._visit_doc(key), text(":"), space(), self._visit_doc(pattern)])
            for key, pattern in zip(node.keys, node.patterns)
        ]
        if node.rest is not None:
            entries.append(concat([text("**"), text(node.rest)]))
        return brace(join(comma(), entries))

    def visit_MatchStar(self, node: ast.MatchStar) -> Doc:
        if node.name is None:
            return text("*_")
        star_target: Doc = text(node.name)
        if type_ann := get_type_annotation(node):
            star_target = concat(
                [star_target, text(":"), space(), self._visit_doc(type_ann)]
            )
        return concat([text("*"), star_target])

    def visit_MatchAs(self, node: ast.MatchAs) -> Doc:
        if node.pattern is None and node.name is None:
            return text("_")
        if node.pattern is None:
            assert node.name is not None
            capture: Doc = text(node.name)
            if type_ann := get_type_annotation(node):
                capture = concat(
                    [capture, text(":"), space(), self._visit_doc(type_ann)]
                )
            return capture
        if node.name is None:
            return self._visit_doc(node.pattern)
        capture = text(node.name)
        if type_ann := get_type_annotation(node):
            capture = concat([capture, text(":"), space(), self._visit_doc(type_ann)])
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
                join(comma(), entries),
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
                paren(join(comma(), args)),
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
        return concat(
            [
                text("match"),
                self._space_between_statement_keywords_and_paren,
                paren(self._visit_doc(node.subject)),
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
        return [concat([text("@"), self._visit_doc(d), hardline()]) for d in decos]

    def visit_ClassDef(self, node: ast.ClassDef) -> Doc:
        deco_docs = self._visit_Decorators(node.decorator_list)
        args: list[Doc] = [self._visit_doc(base) for base in node.bases]
        args.extend(
            [
                concat([text(k.arg), text("="), self._visit_doc(k.value)])
                if k.arg is not None
                else concat([text("**"), self._visit_doc(k.value)])
                for k in node.keywords
            ]
        )
        class_head = [text("class"), space(), text(node.name)]
        if len(node.type_params) > 0:
            class_head.append(self._type_params_doc(node.type_params))
        if len(args) > 0:
            class_head.extend(
                [
                    paren(join(comma(), args)),
                ]
            )
        class_head.extend([self._block_doc(node.body, container=node)])
        return concat(deco_docs + [concat(class_head)])

    def _arguments_doc(self, args: ast.arguments) -> Doc:
        params: list[Doc] = []
        for arg in args.posonlyargs:
            params.append(self._typed_name_doc(arg))
        if len(args.posonlyargs) > 0:
            params.append(text("/"))
        for index, arg in enumerate(args.args):
            default_index = index - (len(args.args) - len(args.defaults))
            if default_index >= 0:
                params.append(
                    concat(
                        [
                            self._typed_name_doc(arg),
                            space(),
                            text("="),
                            space(),
                            self._visit_doc(args.defaults[default_index]),
                        ]
                    )
                )
            else:
                params.append(self._typed_name_doc(arg))

        if args.vararg is not None:
            params.append(concat([text("*"), self._typed_name_doc(args.vararg)]))
        elif len(args.kwonlyargs) > 0:
            params.append(text("*"))

        for kw_arg, kw_default in zip(args.kwonlyargs, args.kw_defaults):
            if kw_default is None:
                params.append(self._typed_name_doc(kw_arg))
            else:
                params.append(
                    concat(
                        [
                            self._typed_name_doc(kw_arg),
                            space(),
                            text("="),
                            space(),
                            self._visit_doc(kw_default),
                        ]
                    )
                )

        if args.kwarg is not None:
            params.append(concat([text("**"), self._typed_name_doc(args.kwarg)]))

        return group(join(comma(), params))

    def _visit_FcuntionDef_AsyncFunctionDef(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> Doc:
        deco_docs = self._visit_Decorators(node.decorator_list)
        head_parts: list[Doc] = []
        if is_static(node):
            head_parts.extend([text("static"), space()])
        if isinstance(node, ast.AsyncFunctionDef):
            head_parts.extend([text("async"), space()])
        head_parts.extend(
            [
                text("def"),
                space(),
                text(node.name),
            ]
        )
        if len(node.type_params) > 0:
            head_parts.append(self._type_params_doc(node.type_params))
        head_parts.append(paren(self._arguments_doc(node.args)))
        if node.returns is not None:
            head_parts.extend(
                [space(), text("->"), space(), self._visit_doc(node.returns)]
            )
        head_parts.extend([self._block_doc(node.body, container=node)])
        return concat(deco_docs + [concat(head_parts)])

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Doc:
        return self._visit_FcuntionDef_AsyncFunctionDef(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Doc:
        return self._visit_FcuntionDef_AsyncFunctionDef(node)

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
            parts: list[Doc] = [text(name.id)]
            if annotation is not None:
                parts.extend([text(":"), space(), self._visit_doc(annotation)])
            parts.extend([space(), text("="), space(), self._visit_doc(value)])
            field_docs.append(concat(parts))

        has_trailing_comma = get_trailing_comma_anchor(node) is not None
        if has_trailing_comma and len(field_docs) > 0:
            fields_doc = concat(
                [
                    join(concat([text(","), hardline()]), field_docs),
                    text(","),
                ]
            )
        else:
            fields_doc = join(comma(), field_docs)
        return group(
            [
                text("{|"),
                indent([softline(), fields_doc]),
                softline(),
                text("|}"),
            ]
        )

    def visit_RecordType(self, node: ast.Name) -> Doc:
        fields = get_record_type_fields(node)
        if fields is None:
            raise ValueError("RecordType node has no field metadata")
        if len(fields) == 0:
            return group([text("{|"), space(), text("|}")])
        field_docs = [
            concat([text(name.id), text(":"), space(), self._visit_doc(annotation)])
            for name, annotation in fields
        ]
        has_trailing_comma = get_trailing_comma_anchor(node) is not None
        if has_trailing_comma:
            fields_doc = concat(
                [
                    join(concat([text(","), hardline()]), field_docs),
                    text(","),
                ]
            )
        else:
            fields_doc = join(comma(), field_docs)
        return group(
            [
                text("{|"),
                indent([softline(), fields_doc]),
                softline(),
                text("|}"),
            ]
        )

    def _arg_doc(self, arg: ast.arg) -> Doc:
        parts: list[Doc] = [text(arg.arg)]
        if arg.annotation is not None:
            parts.extend([text(":"), space(), self._visit_doc(arg.annotation)])
        return concat(parts)

    def visit_FunctionType(self, node: FunctionType) -> Doc:
        arguments_doc: list[Doc] = []
        for arg in get_args_of_function_type(node):
            arguments_doc.append(self._arg_doc(arg))
        if star_arg := get_star_arg_of_function_type(node):
            arguments_doc.append(concat([text("*"), self._arg_doc(star_arg)]))
        if star_kwds := get_star_kwds_of_function_type(node):
            arguments_doc.append(concat([text("**"), self._arg_doc(star_kwds)]))
        return_type = get_return_of_function_type(node)
        return self._maybe_wrap_group_paren(
            node,
            group(
                [
                    paren(join(comma(), arguments_doc)),
                    space(),
                    text("->"),
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
        head_parts: list[Doc] = []
        head_parts.extend(
            [
                paren(self._arguments_doc(func_def.args)),
                space(),
            ]
        )
        if func_def.returns is not None:
            head_parts.extend(
                [
                    text("->"),
                    space(),
                    self._visit_doc(func_def.returns),
                    space(),
                ]
            )
        head_parts.extend(
            [
                text("=>"),
            ]
        )
        if is_function_literal_inline_return(node):
            assert len(func_def.body) == 1, (
                "Inline return function literal must have single statement body"
            )
            if stmt := func_def.body[0]:
                if isinstance(stmt, ast.Return) and stmt.value is not None:
                    # Special case for single return value.
                    return concat(head_parts + [space(), self._visit_doc(stmt.value)])
        return self._maybe_wrap_group_paren(
            node, group(head_parts + [self._block_doc(func_def.body)])
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
    def _block_doc(self, body: list[ast.stmt]) -> Doc:
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
