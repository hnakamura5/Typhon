from __future__ import annotations

import ast
from typing import Literal, cast, override

from Typhon.Grammar.typhon_ast import (
    FunctionLiteral,
    FunctionType,
    get_args_of_function_type,
    get_constant_raw_tokens,
    get_control_comprehension_def,
    get_function_literal_def,
    get_let_pattern_body,
    get_record_literal_fields,
    get_record_type_fields,
    get_return_of_function_type,
    get_star_arg_of_function_type,
    get_star_kwds_of_function_type,
    get_type_annotation,
    get_wrapper_paren_tokens,
    is_attributes_pattern,
    is_elseless_if_exp,
    is_inline_with,
    is_let,
    is_let_assign,
    is_optional,
    is_optional_pipe,
    is_pattern_tuple,
    is_pipe,
    is_static,
    is_var_assign,
)
from Typhon.Grammar.unparse_custom import CustomUnparseHelper
from Typhon.Transform.visitor import TyphonASTRawVisitor
from ..Driver.debugging import debug_verbose_print

from .doc_datatype import (
    Doc,
    NIL,
    concat,
    group,
    line,
    softline,
    hardline,
    indent,
    join,
    space,
    text,
)


def comma() -> Doc:
    return concat([text(","), line()])


def paren(content: Doc | list[Doc]) -> Doc:
    if isinstance(content, list):
        content = concat(content)
    return group(
        concat([text("("), softline(), indent(content), softline(), text(")")])
    )


def bracket(content: Doc | list[Doc]) -> Doc:
    if isinstance(content, list):
        content = concat(content)
    return group(
        concat([text("["), softline(), indent(content), softline(), text("]")])
    )


def brace(content: Doc | list[Doc]) -> Doc:
    if isinstance(content, list):
        content = concat(content)
    return group(
        concat([text("{"), softline(), indent(content), softline(), text("}")])
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
    ):
        super().__init__()
        self.module = module
        # Only the helper. Not used for actual unparsing.
        self._helper = CustomUnparseHelper()
        self._comprehension_printer: _PrintComprehensionToDocVisitor = (
            comprehension_printer or _PrintComprehensionToDocVisitor(module, self)
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

    def _visit_doc(self, node: ast.AST) -> Doc:
        return cast(Doc, self.visit(node))

    def _block_doc(self, body: list[ast.stmt]) -> Doc:
        if len(body) == 0:
            return concat([text("{"), space(), text("}")])
        if len(body) == 1 and isinstance(body[0], ast.Pass):
            return concat([text("{"), space(), text("pass"), space(), text("}")])
        return group(
            [
                text("{"),
                indent(
                    concat(
                        [
                            hardline(),
                            join(hardline(), [self._visit_doc(stmt) for stmt in body]),
                        ]
                    )
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

    def visit_Module(self, node: ast.Module) -> Doc:
        if len(node.body) == 0:
            return NIL
        return join(hardline(), [self._visit_doc(stmt) for stmt in node.body])

    def visit_Expr(self, node: ast.Expr) -> Doc:
        return self._visit_doc(node.value)

    def visit_Name(self, node: ast.Name) -> Doc:
        return self._maybe_wrap_group_paren(node, text(node.id))

    def visit_Compare(self, node: ast.Compare) -> Doc:
        comps: list[Doc] = [self._visit_doc(node.left)]
        debug_verbose_print(
            lambda: f"Translating Compare node: {ast.dump(node, indent=4)}"
        )
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
        raise ValueError(f"Unsupported constant without raw tokens: {node.value!r}")

    def visit_BinOp(self, node: ast.BinOp) -> Doc:
        op = self._get_binop_symbol(node.op)
        doc = group(
            concat(
                [
                    self._visit_doc(node.left),
                    space(),
                    text(op),
                    space(),
                    self._visit_doc(node.right),
                ]
            )
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

    def visit_IfExp(self, node: ast.IfExp) -> Doc:
        parts: list[Doc] = [
            text("("),  # No space here
            text("if"),
            space(),
            paren(self._visit_doc(node.test)),
            space(),
            self._visit_doc(node.body),
        ]
        if not is_elseless_if_exp(node):
            parts.extend(
                [
                    space(),
                    text("else"),
                    space(),
                    self._visit_doc(node.orelse),
                ]
            )
        parts.append(text(")"))
        doc = group(concat(parts))
        return self._maybe_wrap_group_paren(node, doc)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Doc:
        op = self._get_unaryop_symbol(node.op)
        doc = concat([text(op), self._visit_doc(node.operand)])
        return self._maybe_wrap_group_paren(node, doc)

    def _pipe_operator_doc(self, node: ast.Call, is_optional: bool) -> Doc:
        doc = group(
            concat(
                [
                    self._visit_doc(node.args[0]),
                    space(),
                    text("?|>" if is_optional else "|>"),
                    space(),
                    self._visit_doc(node.func),
                ]
            )
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
        all_args = args_docs + kw_docs
        doc = group(
            [
                self._visit_doc(node.func),
                text("?(" if is_optional(node) else "("),
                join(comma(), all_args),
                text(")"),
            ]
        )
        return self._maybe_wrap_group_paren(node, doc)

    def visit_Attribute(self, node: ast.Attribute) -> Doc:
        doc = concat(
            [
                self._visit_doc(node.value),
                text("?." if is_optional(node) else "."),
                text(node.attr),
            ]
        )
        return self._maybe_wrap_group_paren(node, doc)

    def visit_Subscript(self, node: ast.Subscript) -> Doc:
        doc = group(
            [
                self._visit_doc(node.value),
                text("?[" if is_optional(node) else "["),
                self._visit_doc(node.slice),
                text("]"),
            ]
        )
        return self._maybe_wrap_group_paren(node, doc)

    def visit_List(self, node: ast.List) -> Doc:
        doc = bracket(
            [
                join(
                    comma(),
                    [self._visit_doc(e) for e in node.elts],
                ),
            ]
        )
        return self._maybe_wrap_group_paren(node, doc)

    def visit_Tuple(self, node: ast.Tuple) -> Doc:
        if len(node.elts) == 1:
            inner = concat([self._visit_doc(node.elts[0]), comma()])
        else:
            inner = join(comma(), [self._visit_doc(e) for e in node.elts])
        return self._maybe_wrap_group_paren(node, paren(inner))

    def _comprehension_list_doc(self, generators: list[ast.comprehension]) -> Doc:
        return join(space(), [self._visit_doc(gen) for gen in generators])

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
                space(),
                paren(target),
                space(),
                text("in"),
                space(),
                self._visit_doc(node.iter),
                text(")"),
            ]
        )
        parts: list[Doc] = [concat(head)]
        for cond in node.ifs:
            parts.extend(
                [
                    space(),
                    text("if"),
                    space(),
                    paren(self._visit_doc(cond)),
                ]
            )
        return concat(parts)

    def _comp_doc(
        self, node: ast.ListComp | ast.SetComp | ast.GeneratorExp, open: str, close: str
    ) -> Doc:
        return group(
            [
                text(open),
                self._comprehension_list_doc(node.generators),
                space(),
                text("yield"),
                space(),
                self._visit_doc(node.elt),
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
        return group(
            [
                text("{"),  # No space here
                self._comprehension_list_doc(node.generators),
                space(),
                text("yield"),
                space(),
                self._visit_doc(node.key),
                text(":"),
                self._visit_doc(node.value),
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
        return concat(
            [
                text(decl_prefix),
                space(),
                targets_doc,
                space(),
                text("="),
                group(
                    [
                        line(),
                        indent(
                            self._visit_doc(node.value),
                        ),
                    ]
                ),
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
        return concat(
            [
                base,
                space(),
                text("="),
                indent(group([line(), self._visit_doc(node.value)])),
            ]
        )

    def visit_AugAssign(self, node: ast.AugAssign) -> Doc:
        op = self._get_binop_symbol(node.op)
        return concat(
            [
                self._visit_doc(node.target),
                space(),
                text(op),
                text("="),
                indent(
                    group(
                        [
                            line(),
                            self._visit_doc(node.value),
                        ]
                    )
                ),
            ]
        )

    def visit_Return(self, node: ast.Return) -> Doc:
        if node.value is None:
            return text("return")
        return concat([text("return"), space(), self._visit_doc(node.value)])

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
        return text("pass")

    def visit_Assert(self, node: ast.Assert) -> Doc:
        result = concat([text("assert"), space(), self._visit_doc(node.test)])
        if node.msg is not None:
            result = concat([result, comma(), self._visit_doc(node.msg)])
        return result

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
        assert len(match_stmt.cases) == 1
        case = match_stmt.cases[0]
        pattern = case.pattern
        parts: list[Doc] = [
            self._visit_doc(pattern),
            space(),
            text("="),
            line(),
            indent(
                self._visit_doc(match_stmt.subject),
            ),
        ]
        cond = case.guard
        case_body = case.body
        if case_body is innermost_body:
            # Base case: pattern matches directly to the body.
            if cond is not None:
                parts.extend([text(";"), line(), self._visit_doc(cond)])
            return parts
        else:
            assert cond is None, "Only innermost pattern can have condition"
            parts.append(comma())
            parts.extend(self._let_patterns_match_doc(case_body, innermost_body))
            return parts

    def _if_while_body(self, keyword: str, node: ast.If | ast.While) -> Doc:
        if let_pattern := get_let_pattern_body(node):
            body = let_pattern.body
            pattens = self._let_patterns_match_doc(node.body, body)
            parts = [text("let" if let_pattern.is_let else "var"), space()]
            parts.extend(pattens)
            cond_doc = concat(parts)
        else:
            body = node.body
            cond_doc = self._visit_doc(node.test)
        body_doc = concat(
            [
                text(keyword),
                space(),
                paren(cond_doc),
                space(),
                self._block_doc(body),
            ]
        )
        return body_doc

    def _if_chain_doc(self, node: ast.If, keyword: Literal["if", "elif"] = "if") -> Doc:
        doc = self._if_while_body(keyword, node)
        if len(node.orelse) == 0:
            return doc
        if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
            # Note in if-elif chain orelse is single statement
            return concat([doc, space(), self._if_chain_doc(node.orelse[0], "elif")])
        return concat(
            [doc, space(), text("else"), space(), self._block_doc(node.orelse)]
        )

    def visit_If(self, node: ast.If) -> Doc:
        return self._if_chain_doc(node, "if")

    def visit_While(self, node: ast.While) -> Doc:
        doc = self._if_while_body("while", node)
        if len(node.orelse) > 0:
            doc = concat(
                [doc, space(), text("else"), space(), self._block_doc(node.orelse)]
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
            target = concat([target, text(":"), space(), self._visit_doc(type_ann)])
        doc = concat(
            [
                text("for"),
                space(),
                paren(
                    [
                        target,
                        space(),
                        text("in"),
                        space(),
                        self._visit_doc(node.iter),
                    ]
                ),
                space(),
                self._block_doc(node.body),
            ]
        )
        if len(node.orelse) > 0:
            doc = concat(
                [doc, space(), text("else"), space(), self._block_doc(node.orelse)]
            )
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
                    line(),
                    indent(context_expr_doc),
                ]
            )
        else:
            return context_expr_doc

    def visit_With(self, node: ast.With) -> Doc:
        parts = [
            text("with"),
            space(),
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
            parts.extend([space(), self._block_doc(node.body)])
        doc = concat(parts)
        return doc

    def visit_AsyncWith(self, node: ast.AsyncWith) -> Doc:
        with_doc = self.visit_With(cast(ast.With, node))
        return concat([text("async"), space(), with_doc])

    def _except_handler_doc(self, node: ast.ExceptHandler) -> Doc:
        if node.type is None:
            head = text("except")
        else:
            head_parts: list[Doc] = [
                text("except"),
                space(),
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
        return concat([head, space(), self._block_doc(node.body)])

    def visit_Try(self, node: ast.Try) -> Doc:
        parts: list[Doc] = [text("try"), space(), self._block_doc(node.body)]
        for handler in node.handlers:
            parts.extend([space(), self._except_handler_doc(handler)])
        if len(node.orelse) > 0:
            parts.extend([space(), text("else"), space(), self._block_doc(node.orelse)])
        if len(node.finalbody) > 0:
            parts.extend(
                [space(), text("finally"), space(), self._block_doc(node.finalbody)]
            )
        return concat(parts)

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
            space(),
            paren(self._visit_doc(node.pattern)),
        ]
        if node.guard is not None:
            head.extend(
                [
                    space(),
                    text("if"),
                    space(),
                    paren(self._visit_doc(node.guard)),
                ]
            )
        return concat([concat(head), space(), self._block_doc(node.body)])

    def visit_Match(self, node: ast.Match) -> Doc:
        return concat(
            [
                text("match"),
                space(),
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
        if len(args) > 0:
            class_head.extend(
                [
                    paren(join(comma(), args)),
                ]
            )
        class_head.extend([space(), self._block_doc(node.body)])
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
                paren(self._arguments_doc(node.args)),
            ]
        )
        if node.returns is not None:
            head_parts.extend(
                [space(), text("->"), space(), self._visit_doc(node.returns)]
            )
        head_parts.extend([space(), self._block_doc(node.body)])
        return concat(deco_docs + [concat(head_parts)])

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Doc:
        return self._visit_FcuntionDef_AsyncFunctionDef(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Doc:
        return self._visit_FcuntionDef_AsyncFunctionDef(node)

    def visit_RecordLiteral(self, node: ast.Name) -> Doc:
        fields = get_record_literal_fields(node)
        if fields is None:
            raise ValueError("RecordLiteral node has no field metadata")
        if len(fields) == 0:
            return self._maybe_wrap_group_paren(
                node, group([text("{|"), space(), text("|}")])
            )
        field_docs: list[Doc] = []
        for name, annotation, value in fields:
            parts: list[Doc] = [text(name.id)]
            if annotation is not None:
                parts.extend([text(":"), space(), self._visit_doc(annotation)])
            parts.extend([space(), text("="), space(), self._visit_doc(value)])
            field_docs.append(concat(parts))

        return self._maybe_wrap_group_paren(
            node,
            group(
                [
                    text("{|"),
                    softline(),
                    join(comma(), field_docs),
                    softline(),
                    text("|}"),
                ]
            ),
        )

    def visit_RecordType(self, node: ast.Name) -> Doc:
        fields = get_record_type_fields(node)
        if fields is None:
            raise ValueError("RecordType node has no field metadata")
        if len(fields) == 0:
            return self._maybe_wrap_group_paren(
                node, concat([text("{|"), space(), text("|}")])
            )
        field_docs = [
            concat([text(name.id), text(":"), space(), self._visit_doc(annotation)])
            for name, annotation in fields
        ]
        return self._maybe_wrap_group_paren(
            node,
            concat(
                [
                    text("{|"),
                    join(comma(), field_docs),
                    text("|}"),
                ]
            ),
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
        return concat(
            [
                paren(join(comma(), arguments_doc)),
                space(),
                text("->"),
                space(),
                self._visit_doc(return_type)
                if return_type is not None
                else text("None"),
            ]
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
                space(),
            ]
        )
        if len(func_def.body) == 1:
            if stmt := func_def.body[0]:
                if isinstance(stmt, ast.Return) and stmt.value is not None:
                    # Special case for single return value.
                    return concat(head_parts + [self._visit_doc(stmt.value)])
        return concat(head_parts + [self._block_doc(func_def.body)])

    def visit_ControlComprehension(self, node: ast.Name) -> Doc:
        if func_def := get_control_comprehension_def(node):
            return concat(
                [
                    text("("),  # No space here
                    self._comprehension_printer._visit_doc(func_def.body[0]),
                    text(")"),
                ]
            )
        raise ValueError(f"Unsupported control comprehension: {node.id}")


class _PrintComprehensionToDocVisitor(_PrintToDocVisitor):
    def __init__(self, module: ast.Module, parent: _PrintToDocVisitor):
        super().__init__(module, comprehension_printer=self)
        self._parent = parent

    @override
    def _block_doc(self, body: list[ast.stmt]) -> Doc:
        # 'Block' must be single expression or yield.
        assert len(body) == 1
        stmt = body[0]
        # Falling back to parent for contents of the block.
        if isinstance(stmt, ast.Expr):
            return self._parent._visit_doc(stmt.value)
        elif isinstance(stmt, ast.Yield) and stmt.value is not None:
            return self._parent._visit_doc(stmt.value)
        return self._parent._visit_doc(stmt)


def print_to_doc(node: ast.AST) -> Doc:
    if isinstance(node, ast.Module):
        module = node
    else:
        module = ast.Module(
            body=[ast.Expr(value=cast(ast.expr, node))], type_ignores=[]
        )
    visitor = _PrintToDocVisitor(module)
    return cast(Doc, visitor.visit(node))
