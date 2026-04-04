from __future__ import annotations

import ast
from typing import cast

from Typhon.Grammar.pretty_printer import pretty_print_expr
from Typhon.Grammar.typhon_ast import (
    ControlComprehension,
    FunctionLiteral,
    FunctionType,
    get_constant_raw_tokens,
    get_control_comprehension_def,
    get_function_literal_def,
    get_let_pattern_body,
    get_match_class_keyword_names,
    get_type_annotation,
    get_wrapper_paren_tokens,
    is_attributes_pattern,
    is_coalescing,
    is_force_unwrap,
    is_function_type,
    is_let,
    is_let_assign,
    is_let_else,
    is_multi_decl,
    is_optional,
    is_optional_pipe,
    is_optional_question,
    is_pattern_tuple,
    is_record_literal,
    is_record_type,
    is_static,
    is_var,
    is_var_assign,
)
from Typhon.Transform.visitor import TyphonASTVisitor


_INDENT = "    "


def _indent_text(text: str, level: int = 1) -> str:
    prefix = _INDENT * level
    return "\n".join(prefix + line if line else line for line in text.splitlines())


def _strip_outer_parens(text: str) -> str:
    if len(text) >= 2 and text[0] == "(" and text[-1] == ")":
        return text[1:-1]
    return text


class _TyphonUnparseVisitor(TyphonASTVisitor):
    def __init__(self, module: ast.Module):
        super().__init__(module)

    def _v(self, node: ast.AST) -> str:
        return cast(str, self.visit(node))

    def _apply_wrapper_parens(self, node: ast.expr, rendered: str) -> str:
        tokens = get_wrapper_paren_tokens(node)
        if not tokens or len(tokens) < 2:
            return rendered
        return f"{tokens[0].string}{rendered}{tokens[-1].string}"

    def _render_block(self, body: list[ast.stmt]) -> str:
        if len(body) == 0:
            return "{\n}"  # defensive fallback
        rendered = self._render_stmt_list(body)
        return "{\n" + _indent_text(rendered) + "\n}"

    def _decl_keyword(
        self,
        node: ast.Assign
        | ast.AnnAssign
        | ast.For
        | ast.AsyncFor
        | ast.withitem
        | ast.comprehension,
    ) -> str:
        if is_var(node):
            return "var"
        if is_let(node):
            return "let"
        return "let"

    def _render_decl_fragment(self, node: ast.Assign | ast.AnnAssign) -> str:
        if isinstance(node, ast.Assign):
            target = self._v(node.targets[0])
            return f"{target} = {self._v(node.value)}"

        target = self._v(node.target)
        annotation = self._v(node.annotation)
        if node.value is None:
            return f"{target}: {annotation}"
        return f"{target}: {annotation} = {self._v(node.value)}"

    def _render_decl_stmt(self, node: ast.Assign | ast.AnnAssign) -> str:
        return f"{self._decl_keyword(node)} {self._render_decl_fragment(node)}"

    def _render_stmt_list(self, body: list[ast.stmt]) -> str:
        lines: list[str] = []
        i = 0
        while i < len(body):
            stmt = body[i]
            if (
                isinstance(stmt, (ast.Assign, ast.AnnAssign))
                and (is_var_assign(stmt) or is_let_assign(stmt))
                and is_multi_decl(stmt)
            ):
                head_kw = self._decl_keyword(stmt)
                parts: list[str] = [self._render_decl_fragment(stmt)]
                j = i + 1
                while j < len(body):
                    nxt = body[j]
                    if not isinstance(nxt, (ast.Assign, ast.AnnAssign)):
                        break
                    if not is_multi_decl(nxt):
                        break
                    if self._decl_keyword(nxt) != head_kw:
                        break
                    parts.append(self._render_decl_fragment(nxt))
                    j += 1
                lines.append(f"{head_kw} " + ", ".join(parts))
                i = j
                continue

            lines.append(cast(str, self.visit(stmt)))
            i += 1
        return "\n".join(lines)

    def _render_name_or_expr(self, node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return node.id
        return self._v(node)

    def _render_pattern(self, pattern: ast.pattern) -> str:
        if isinstance(pattern, ast.MatchValue):
            return self._v(pattern.value)
        if isinstance(pattern, ast.MatchSingleton):
            if pattern.value is None:
                return "None"
            return "True" if pattern.value else "False"
        if isinstance(pattern, ast.MatchAs):
            if pattern.pattern is None and pattern.name is None:
                return "_"
            if pattern.pattern is None and pattern.name is not None:
                return pattern.name
            left = self._render_pattern(cast(ast.pattern, pattern.pattern))
            if pattern.name is None:
                return left
            return f"{left} as {pattern.name}"
        if isinstance(pattern, ast.MatchOr):
            return " | ".join(self._render_pattern(p) for p in pattern.patterns)
        if isinstance(pattern, ast.MatchSequence):
            content = ", ".join(self._render_pattern(p) for p in pattern.patterns)
            if is_pattern_tuple(pattern):
                return f"({content})"
            return f"[{content}]"
        if isinstance(pattern, ast.MatchStar):
            if pattern.name is None:
                return "*_"
            return f"*{pattern.name}"
        if isinstance(pattern, ast.MatchMapping):
            items = [
                f"{self._v(k)}: {self._render_pattern(v)}"
                for k, v in zip(pattern.keys, pattern.patterns)
            ]
            if pattern.rest:
                items.append(f"**{pattern.rest}")
            return "{" + ", ".join(items) + "}"
        if isinstance(pattern, ast.MatchClass):
            if isinstance(pattern.cls, ast.Name) and is_attributes_pattern(pattern.cls):
                attrs: list[str] = []
                for name, pat in zip(pattern.kwd_attrs, pattern.kwd_patterns):
                    rendered = self._render_pattern(pat)
                    if rendered == name:
                        attrs.append(f".{name}")
                    else:
                        attrs.append(f".{name} = {rendered}")
                return "{" + ", ".join(attrs) + "}"

            pos = [self._render_pattern(p) for p in pattern.patterns]
            kw_names = get_match_class_keyword_names(pattern)
            if kw_names is not None and len(kw_names) == len(pattern.kwd_patterns):
                kws = [
                    f"{kw.id} = {self._render_pattern(p)}"
                    for kw, p in zip(kw_names, pattern.kwd_patterns)
                ]
            else:
                kws = [
                    f"{kw} = {self._render_pattern(p)}"
                    for kw, p in zip(pattern.kwd_attrs, pattern.kwd_patterns)
                ]
            inside = ", ".join(pos + kws)
            return f"{self._v(pattern.cls)}({inside})"

        return ast.unparse(pattern)

    def _is_auto_none_check(self, guard: ast.expr, pattern: ast.pattern) -> bool:
        if not isinstance(pattern, ast.MatchAs):
            return False
        if pattern.pattern is not None or pattern.name is None:
            return False
        if not isinstance(guard, ast.Compare):
            return False
        if len(guard.ops) != 1 or len(guard.comparators) != 1:
            return False
        if not isinstance(guard.ops[0], ast.IsNot):
            return False
        if not (
            isinstance(guard.left, ast.Name)
            and guard.left.id == pattern.name
            and isinstance(guard.comparators[0], ast.Constant)
            and guard.comparators[0].value is None
        ):
            return False
        return True

    def _extract_let_chain(
        self, body: list[ast.stmt]
    ) -> tuple[list[tuple[ast.pattern, ast.expr]], ast.expr | None]:
        pairs: list[tuple[ast.pattern, ast.expr]] = []
        cond: ast.expr | None = None
        current = body
        while len(current) == 1 and isinstance(current[0], ast.Match):
            match_stmt = current[0]
            if len(match_stmt.cases) == 0:
                break
            first = match_stmt.cases[0]
            pairs.append((first.pattern, match_stmt.subject))
            if first.guard is not None:
                cond = first.guard
            current = first.body

        if (
            cond is not None
            and len(pairs) == 1
            and self._is_auto_none_check(cond, pairs[0][0])
        ):
            cond = None
        return pairs, cond

    def _render_let_bindings(self, pairs: list[tuple[ast.pattern, ast.expr]]) -> str:
        return ", ".join(
            f"{self._render_pattern(pat)} = {self._v(subject)}"
            for pat, subject in pairs
        )

    def _render_type_params(self, params: list[ast.type_param]) -> str:
        if len(params) == 0:
            return ""

        def _one(p: ast.type_param) -> str:
            if isinstance(p, ast.TypeVar):
                out = p.name
                bound = getattr(p, "bound", None)
                if bound is not None:
                    out += f": {self._v(bound)}"
                return out
            if isinstance(p, ast.TypeVarTuple):
                out = f"*{p.name}"
                bound = getattr(p, "bound", None)
                if bound is not None:
                    out += f": {self._v(bound)}"
                return out
            if isinstance(p, ast.ParamSpec):
                out = f"**{p.name}"
                bound = getattr(p, "bound", None)
                if bound is not None:
                    out += f": {self._v(bound)}"
                return out
            return ast.unparse(p)

        return "[" + ", ".join(_one(p) for p in params) + "]"

    def _render_arg(self, arg: ast.arg) -> str:
        if arg.arg == "":
            if arg.annotation is None:
                return ""
            return self._v(arg.annotation)
        if arg.annotation is None:
            return arg.arg
        return f"{arg.arg}: {self._v(arg.annotation)}"

    def _render_arguments(self, args: ast.arguments) -> str:
        items: list[str] = []

        positional = args.posonlyargs + args.args
        defaults = args.defaults
        default_start = len(positional) - len(defaults)

        for idx, arg in enumerate(positional):
            rendered = self._render_arg(arg)
            if idx >= default_start:
                rendered += f" = {self._v(defaults[idx - default_start])}"
            items.append(rendered)

        if len(args.posonlyargs) > 0:
            insert_at = len(args.posonlyargs)
            items.insert(insert_at, "/")

        if args.vararg is not None:
            items.append(f"*{self._render_arg(args.vararg)}")
        elif len(args.kwonlyargs) > 0:
            items.append("*")

        for kwarg, default in zip(args.kwonlyargs, args.kw_defaults):
            rendered = self._render_arg(kwarg)
            if default is not None:
                rendered += f" = {self._v(default)}"
            items.append(rendered)

        if args.kwarg is not None:
            items.append(f"**{self._render_arg(args.kwarg)}")

        return ", ".join(items)

    def visit_Module(self, node: ast.Module) -> str:
        return self._render_stmt_list(node.body)

    def visit_Expr(self, node: ast.Expr) -> str:
        return self._v(node.value)

    def visit_Name(self, node: ast.Name) -> str:
        if is_function_type(node) or is_record_literal(node) or is_record_type(node):
            return pretty_print_expr(node)
        return self._apply_wrapper_parens(node, node.id)

    def visit_Constant(self, node: ast.Constant) -> str:
        raw = get_constant_raw_tokens(node)
        if raw:
            return self._apply_wrapper_parens(node, "".join(tok.string for tok in raw))
        if node.value is None:
            return "None"
        if node.value is True:
            return "True"
        if node.value is False:
            return "False"
        return self._apply_wrapper_parens(node, repr(node.value))

    def visit_Attribute(self, node: ast.Attribute) -> str:
        op = "?." if is_optional(node) else "."
        return self._apply_wrapper_parens(node, f"{self._v(node.value)}{op}{node.attr}")

    def visit_Subscript(self, node: ast.Subscript) -> str:
        op = "?[" if is_optional(node) else "["
        return self._apply_wrapper_parens(
            node,
            f"{self._v(node.value)}{op}{self._v(node.slice)}]",
        )

    def visit_Call(self, node: ast.Call) -> str:
        if is_optional_pipe(node) and len(node.args) == 1 and len(node.keywords) == 0:
            return f"{self._v(node.args[0])} ?|> {self._v(node.func)}"

        args = [self._v(arg) for arg in node.args]
        args.extend(
            (
                f"{kw.arg}={self._v(kw.value)}"
                if kw.arg is not None
                else f"**{self._v(kw.value)}"
            )
            for kw in node.keywords
        )
        open_paren = "?(" if is_optional(node) else "("
        return self._apply_wrapper_parens(
            node,
            f"{self._v(node.func)}{open_paren}{', '.join(args)})",
        )

    def visit_Tuple(self, node: ast.Tuple) -> str:
        if is_coalescing(node):
            return self._apply_wrapper_parens(
                node, " ?? ".join(self._v(e) for e in node.elts)
            )
        if is_optional_question(node) and len(node.elts) == 1:
            return self._apply_wrapper_parens(node, f"{self._v(node.elts[0])}?")
        if is_force_unwrap(node) and len(node.elts) == 1:
            return self._apply_wrapper_parens(node, f"{self._v(node.elts[0])}!")

        if len(node.elts) == 1:
            rendered = f"({self._v(node.elts[0])},)"
        else:
            rendered = "(" + ", ".join(self._v(e) for e in node.elts) + ")"
        return self._apply_wrapper_parens(node, rendered)

    def visit_List(self, node: ast.List) -> str:
        return self._apply_wrapper_parens(
            node, "[" + ", ".join(self._v(e) for e in node.elts) + "]"
        )

    def visit_Set(self, node: ast.Set) -> str:
        return "{" + ", ".join(self._v(e) for e in node.elts) + "}"

    def visit_Dict(self, node: ast.Dict) -> str:
        items: list[str] = []
        for k, v in zip(node.keys, node.values):
            if k is None:
                items.append(f"**{self._v(v)}")
            else:
                items.append(f"{self._v(k)}: {self._v(v)}")
        return "{" + ", ".join(items) + "}"

    def visit_BoolOp(self, node: ast.BoolOp) -> str:
        op = " && " if isinstance(node.op, ast.And) else " || "
        return "(" + op.join(self._v(v) for v in node.values) + ")"

    def visit_UnaryOp(self, node: ast.UnaryOp) -> str:
        if isinstance(node.op, ast.Not):
            return f"(!{self._v(node.operand)})"
        if isinstance(node.op, ast.UAdd):
            return f"(+{self._v(node.operand)})"
        if isinstance(node.op, ast.USub):
            return f"(-{self._v(node.operand)})"
        if isinstance(node.op, ast.Invert):
            return f"(~{self._v(node.operand)})"
        return ast.unparse(node)

    def visit_BinOp(self, node: ast.BinOp) -> str:
        symbol: str | None = None
        if isinstance(node.op, ast.Add):
            symbol = "+"
        elif isinstance(node.op, ast.Sub):
            symbol = "-"
        elif isinstance(node.op, ast.Mult):
            symbol = "*"
        elif isinstance(node.op, ast.MatMult):
            symbol = "@"
        elif isinstance(node.op, ast.Div):
            symbol = "/"
        elif isinstance(node.op, ast.FloorDiv):
            symbol = "//"
        elif isinstance(node.op, ast.Mod):
            symbol = "%"
        elif isinstance(node.op, ast.Pow):
            symbol = "**"
        elif isinstance(node.op, ast.LShift):
            symbol = "<<"
        elif isinstance(node.op, ast.RShift):
            symbol = ">>"
        elif isinstance(node.op, ast.BitAnd):
            symbol = "&"
        elif isinstance(node.op, ast.BitOr):
            symbol = "|"
        elif isinstance(node.op, ast.BitXor):
            symbol = "^"
        if symbol is None:
            return ast.unparse(node)
        return f"({self._v(node.left)} {symbol} {self._v(node.right)})"

    def visit_Compare(self, node: ast.Compare) -> str:
        op_map: dict[type[ast.cmpop], str] = {
            ast.Eq: "==",
            ast.NotEq: "!=",
            ast.Lt: "<",
            ast.LtE: "<=",
            ast.Gt: ">",
            ast.GtE: ">=",
            ast.Is: "is",
            ast.IsNot: "is not",
            ast.In: "in",
            ast.NotIn: "not in",
        }
        parts: list[str] = [self._v(node.left)]
        for op, comp in zip(node.ops, node.comparators):
            token = op_map.get(type(op), ast.unparse(op))
            parts.append(f"{token} {self._v(comp)}")
        return "(" + " ".join(parts) + ")"

    def visit_IfExp(self, node: ast.IfExp) -> str:
        return f"({self._v(node.body)} if ({self._v(node.test)}) else {self._v(node.orelse)})"

    def visit_NamedExpr(self, node: ast.NamedExpr) -> str:
        return f"{self._v(node.target)} := {self._v(node.value)}"

    def visit_Starred(self, node: ast.Starred) -> str:
        return f"*{self._v(node.value)}"

    def visit_Await(self, node: ast.Await) -> str:
        return f"await {self._v(node.value)}"

    def visit_Yield(self, node: ast.Yield) -> str:
        if node.value is None:
            return "yield"
        return f"yield {self._v(node.value)}"

    def visit_YieldFrom(self, node: ast.YieldFrom) -> str:
        return f"yield from {self._v(node.value)}"

    def visit_Lambda(self, node: ast.Lambda) -> str:
        args = self._render_arguments(node.args)
        return f"({args}) => {self._v(node.body)}"

    def visit_Slice(self, node: ast.Slice) -> str:
        lower = "" if node.lower is None else self._v(node.lower)
        upper = "" if node.upper is None else self._v(node.upper)
        if node.step is None:
            return f"{lower}:{upper}"
        return f"{lower}:{upper}:{self._v(node.step)}"

    def visit_JoinedStr(self, node: ast.JoinedStr) -> str:
        return ast.unparse(node)

    def visit_FormattedValue(self, node: ast.FormattedValue) -> str:
        return ast.unparse(node)

    def visit_ListComp(self, node: ast.ListComp) -> str:
        return f"[{self._v(node.elt)} {self._render_comp_generators(node.generators)}]"

    def visit_SetComp(self, node: ast.SetComp) -> str:
        return (
            f"{{{self._v(node.elt)} {self._render_comp_generators(node.generators)}}}"
        )

    def visit_DictComp(self, node: ast.DictComp) -> str:
        return (
            "{"
            + f"{self._v(node.key)}: {self._v(node.value)} {self._render_comp_generators(node.generators)}"
            + "}"
        )

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> str:
        return f"({self._v(node.elt)} {self._render_comp_generators(node.generators)})"

    def _render_comp_generators(self, generators: list[ast.comprehension]) -> str:
        rendered: list[str] = []
        for gen in generators:
            async_prefix = "async " if gen.is_async else ""
            decl = self._decl_keyword(gen)
            target = self._v(gen.target)
            type_ann = get_type_annotation(gen)
            type_text = f": {self._v(type_ann)}" if type_ann is not None else ""
            rendered.append(
                f"{async_prefix}for ({decl} {target}{type_text} in {self._v(gen.iter)})"
            )
            for cond in gen.ifs:
                rendered.append(f"if ({self._v(cond)})")
        return " ".join(rendered)

    def _extract_control_genexp(
        self,
        stmt: ast.stmt,
    ) -> tuple[list[ast.comprehension], ast.expr] | None:
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Yield):
            if stmt.value.value is None:
                return None
            return [], stmt.value.value

        if not isinstance(stmt, (ast.For, ast.AsyncFor)):
            return None

        cursor = stmt.body
        ifs: list[ast.expr] = []
        while (
            len(cursor) == 1
            and isinstance(cursor[0], ast.If)
            and len(cursor[0].orelse) == 0
        ):
            ifs.append(cursor[0].test)
            cursor = cursor[0].body

        if len(cursor) != 1:
            return None
        inner = self._extract_control_genexp(cursor[0])
        if inner is None:
            return None
        inner_gens, elt = inner

        gen = ast.comprehension(
            target=stmt.target,
            iter=stmt.iter,
            ifs=ifs,
            is_async=1 if isinstance(stmt, ast.AsyncFor) else 0,
        )

        return [gen, *inner_gens], elt

    def _extract_let_chain_return_expr(self, body: list[ast.stmt]) -> ast.expr | None:
        current = body
        while len(current) == 1 and isinstance(current[0], ast.Match):
            match_stmt = current[0]
            if len(match_stmt.cases) == 0:
                return None
            current = match_stmt.cases[0].body
        if len(current) != 1 or not isinstance(current[0], ast.Return):
            return None
        return current[0].value

    def _render_control_comprehension(
        self, func_def: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> str | None:
        body = func_def.body

        # (for (...) ... yield ...), (while (...) yield ...)
        if len(body) == 1:
            # Generator-like control comprehension
            extracted = self._extract_control_genexp(body[0])
            if extracted is not None:
                generators, elt = extracted
                return (
                    "(for "
                    + self._render_comp_generators(generators)
                    + f" yield {self._v(elt)})"
                )

            # while comprehension
            if isinstance(body[0], ast.While):
                while_stmt = body[0]
                if len(while_stmt.body) == 1 and isinstance(
                    while_stmt.body[0], ast.Expr
                ):
                    expr = while_stmt.body[0]
                    if (
                        isinstance(expr.value, ast.Yield)
                        and expr.value.value is not None
                    ):
                        return f"(while ({self._v(while_stmt.test)}) yield {self._v(expr.value.value)})"
                raise ValueError(
                    "Unsupported control comprehension: invalid while-comp shape"
                )

            # with comprehension
            if isinstance(body[0], (ast.With, ast.AsyncWith)):
                with_stmt = body[0]
                if len(with_stmt.body) != 1 or not isinstance(
                    with_stmt.body[0], ast.Return
                ):
                    raise ValueError(
                        "Unsupported control comprehension: invalid with-comp body"
                    )
                ret = with_stmt.body[0]
                if ret.value is None:
                    raise ValueError(
                        "Unsupported control comprehension: with-comp missing return value"
                    )
                head = "async with" if isinstance(with_stmt, ast.AsyncWith) else "with"
                items = ", ".join(self._render_with_item(it) for it in with_stmt.items)
                return f"({head} ({items}) {self._v(ret.value)})"

            # try comprehension
            if isinstance(body[0], ast.Try):
                try_stmt = body[0]
                if len(try_stmt.body) != 1 or not isinstance(
                    try_stmt.body[0], ast.Return
                ):
                    raise ValueError(
                        "Unsupported control comprehension: invalid try-comp body"
                    )
                try_ret = try_stmt.body[0].value
                if try_ret is None:
                    raise ValueError(
                        "Unsupported control comprehension: try-comp missing try expression"
                    )
                try_parts: list[str] = [f"(try {self._v(try_ret)}"]
                for handler in try_stmt.handlers:
                    if len(handler.body) != 1 or not isinstance(
                        handler.body[0], ast.Return
                    ):
                        raise ValueError(
                            "Unsupported control comprehension: invalid try-comp except body"
                        )
                    ex_ret = handler.body[0].value
                    if ex_ret is None:
                        raise ValueError(
                            "Unsupported control comprehension: except-comp missing expression"
                        )
                    if handler.type is None:
                        try_parts.append(f"except {self._v(ex_ret)}")
                    else:
                        if handler.name is None:
                            try_parts.append(
                                f"except ({self._v(handler.type)}) {self._v(ex_ret)}"
                            )
                        else:
                            try_parts.append(
                                f"except ({self._v(handler.type)} as {handler.name}) {self._v(ex_ret)}"
                            )
                try_parts.append(")")
                return " ".join(try_parts)

            # if/if-let comprehension (function with single if)
            if isinstance(body[0], ast.If):
                if_stmt = body[0]
                if (
                    get_let_pattern_body(if_stmt) is not None
                    and is_let_else(if_stmt)
                    and not if_stmt.orelse
                ):
                    pairs, cond = self._extract_let_chain(if_stmt.body)
                    return_expr = self._extract_let_chain_return_expr(if_stmt.body)
                    if len(pairs) > 0 and return_expr is not None:
                        binds = self._render_let_bindings(pairs)
                        cond_text = "" if cond is None else f"; {self._v(cond)}"
                        return f"(let {binds}{cond_text}; {self._v(return_expr)})"
                # Reuse statement unparser and convert block form to expression tail.
                rendered_stmt = self.visit_If(if_stmt)
                # expected: if (...) { <expr-stmt> } [elif ...] [else { <expr-stmt> }]
                # Convert conservative pattern by replacing first statement braces.
                return f"({rendered_stmt})"

        # let comprehension: decls + return
        if (
            len(body) >= 1
            and isinstance(body[-1], ast.Return)
            and body[-1].value is not None
        ):
            decls = body[:-1]
            if all(
                isinstance(s, (ast.Assign, ast.AnnAssign)) and is_let_assign(s)
                for s in decls
            ):
                decl_text = ", ".join(
                    self._render_decl_fragment(cast(ast.Assign | ast.AnnAssign, s))
                    for s in decls
                )
                return f"(let {decl_text}; {self._v(body[-1].value)})"

        # match comprehension
        if len(body) >= 1 and isinstance(body[0], ast.Match):
            match_stmt = body[0]
            match_parts: list[str] = [f"(match ({self._v(match_stmt.subject)})"]
            for case in match_stmt.cases:
                if len(case.body) != 1 or not isinstance(case.body[0], ast.Return):
                    raise ValueError(
                        "Unsupported control comprehension: invalid match-comp case body"
                    )
                case_ret = case.body[0].value
                if case_ret is None:
                    raise ValueError(
                        "Unsupported control comprehension: match-comp case missing expression"
                    )
                head = f"case ({self._render_pattern(case.pattern)})"
                if case.guard is not None:
                    head += f" if ({self._v(case.guard)})"
                match_parts.append(f"{head} {self._v(case_ret)}")
            match_parts.append(")")
            return " ".join(match_parts)

        return None

    def visit_Assign(self, node: ast.Assign) -> str:
        if is_var_assign(node) or is_let_assign(node):
            return self._render_decl_stmt(node)
        return " = ".join([*(self._v(t) for t in node.targets), self._v(node.value)])

    def visit_AnnAssign(self, node: ast.AnnAssign) -> str:
        if is_var_assign(node) or is_let_assign(node):
            return self._render_decl_stmt(node)

        rendered = f"{self._v(node.target)}: {self._v(node.annotation)}"
        if node.value is not None:
            rendered += f" = {self._v(node.value)}"
        return rendered

    def visit_AugAssign(self, node: ast.AugAssign) -> str:
        symbol: str | None = None
        if isinstance(node.op, ast.Add):
            symbol = "+="
        elif isinstance(node.op, ast.Sub):
            symbol = "-="
        elif isinstance(node.op, ast.Mult):
            symbol = "*="
        elif isinstance(node.op, ast.MatMult):
            symbol = "@="
        elif isinstance(node.op, ast.Div):
            symbol = "/="
        elif isinstance(node.op, ast.FloorDiv):
            symbol = "//="
        elif isinstance(node.op, ast.Mod):
            symbol = "%="
        elif isinstance(node.op, ast.Pow):
            symbol = "**="
        elif isinstance(node.op, ast.LShift):
            symbol = "<<="
        elif isinstance(node.op, ast.RShift):
            symbol = ">>="
        elif isinstance(node.op, ast.BitAnd):
            symbol = "&="
        elif isinstance(node.op, ast.BitOr):
            symbol = "|="
        elif isinstance(node.op, ast.BitXor):
            symbol = "^="
        if symbol is None:
            return ast.unparse(node)
        return f"{self._v(node.target)} {symbol} {self._v(node.value)}"

    def visit_Return(self, node: ast.Return) -> str:
        if node.value is None:
            return "return"
        return f"return {self._v(node.value)}"

    def visit_Raise(self, node: ast.Raise) -> str:
        if node.exc is None:
            return "raise"
        if node.cause is None:
            return f"raise {self._v(node.exc)}"
        return f"raise {self._v(node.exc)} from {self._v(node.cause)}"

    def visit_Assert(self, node: ast.Assert) -> str:
        if node.msg is None:
            return f"assert {self._v(node.test)}"
        return f"assert {self._v(node.test)}, {self._v(node.msg)}"

    def visit_Pass(self, node: ast.Pass) -> str:
        return "pass"

    def visit_Break(self, node: ast.Break) -> str:
        return "break"

    def visit_Continue(self, node: ast.Continue) -> str:
        return "continue"

    def visit_Delete(self, node: ast.Delete) -> str:
        assert False
        return "del " + ", ".join(self._v(t) for t in node.targets)

    def visit_Global(self, node: ast.Global) -> str:
        assert False
        return "global " + ", ".join(node.names)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> str:
        assert False
        return "nonlocal " + ", ".join(node.names)

    def visit_Import(self, node: ast.Import) -> str:
        names = [
            alias.name if alias.asname is None else f"{alias.name} as {alias.asname}"
            for alias in node.names
        ]
        return "import " + ", ".join(names)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> str:
        dots = "." * node.level
        mod = "" if node.module is None else node.module
        names = [
            alias.name if alias.asname is None else f"{alias.name} as {alias.asname}"
            for alias in node.names
        ]
        return f"from {dots}{mod} import " + ", ".join(names)

    def visit_If(self, node: ast.If) -> str:
        let_info = get_let_pattern_body(node)
        if let_info is not None:
            pairs, cond = self._extract_let_chain(node.body)
            binds = self._render_let_bindings(pairs)
            if is_let_else(node):
                result = f"let {binds}"
                if node.orelse:
                    result += " else " + self._render_block(node.orelse)
                return result

            cond_text = "" if cond is None else f"; {self.visit(cond)}"
            result = f"if (let {binds}{cond_text}) " + self._render_block(let_info.body)
            if node.orelse:
                if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                    elif_part = self._v(node.orelse[0])
                    if elif_part.startswith("if "):
                        elif_part = "elif " + elif_part[3:]
                    result += " " + elif_part
                else:
                    result += " else " + self._render_block(node.orelse)
            return result

        result = f"if ({self._v(node.test)}) " + self._render_block(node.body)
        if node.orelse:
            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                elif_part = self._v(node.orelse[0])
                if elif_part.startswith("if "):
                    elif_part = "elif " + elif_part[3:]
                result += " " + elif_part
            else:
                result += " else " + self._render_block(node.orelse)
        return result

    def visit_While(self, node: ast.While) -> str:
        let_info = get_let_pattern_body(node)
        if let_info is not None:
            pairs, cond = self._extract_let_chain(node.body)
            binds = self._render_let_bindings(pairs)
            cond_text = "" if cond is None else f"; {self._v(cond)}"
            result = f"while (let {binds}{cond_text}) " + self._render_block(
                let_info.body
            )
            if node.orelse:
                result += " else " + self._render_block(node.orelse)
            return result

        result = f"while ({self._v(node.test)}) " + self._render_block(node.body)
        if node.orelse:
            result += " else " + self._render_block(node.orelse)
        return result

    def visit_For(self, node: ast.For) -> str:
        decl = self._decl_keyword(node)
        target = self._v(node.target)
        type_ann = get_type_annotation(node)
        type_text = f": {self._v(type_ann)}" if type_ann is not None else ""
        result = (
            f"for ({decl} {target}{type_text} in {self._v(node.iter)}) "
            + self._render_block(node.body)
        )
        if node.orelse:
            result += " else " + self._render_block(node.orelse)
        return result

    def visit_AsyncFor(self, node: ast.AsyncFor) -> str:
        decl = self._decl_keyword(node)
        target = self._v(node.target)
        type_ann = get_type_annotation(node)
        type_text = f": {self._v(type_ann)}" if type_ann is not None else ""
        result = (
            f"async for ({decl} {target}{type_text} in {self._v(node.iter)}) "
            + self._render_block(node.body)
        )
        if node.orelse:
            result += " else " + self._render_block(node.orelse)
        return result

    def _render_with_item(self, item: ast.withitem) -> str:
        if item.optional_vars is not None and (is_let(item) or is_var(item)):
            decl = self._decl_keyword(item)
            name = self._v(item.optional_vars)
            type_ann = get_type_annotation(item)
            type_text = f": {self._v(type_ann)}" if type_ann is not None else ""
            return f"{decl} {name}{type_text} = {self._v(item.context_expr)}"
        if item.optional_vars is None:
            return self._v(item.context_expr)
        return f"{self._v(item.context_expr)} as {self._v(item.optional_vars)}"

    def visit_With(self, node: ast.With) -> str:
        items = ", ".join(self._render_with_item(it) for it in node.items)
        return f"with ({items}) " + self._render_block(node.body)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> str:
        items = ", ".join(self._render_with_item(it) for it in node.items)
        return f"async with ({items}) " + self._render_block(node.body)

    def visit_Try(self, node: ast.Try) -> str:
        result = "try " + self._render_block(node.body)
        for handler in node.handlers:
            result += " " + self._v(handler)
        if node.orelse:
            result += " else " + self._render_block(node.orelse)
        if node.finalbody:
            result += " finally " + self._render_block(node.finalbody)
        return result

    def visit_TryStar(self, node: ast.TryStar) -> str:
        result = "try " + self._render_block(node.body)
        for handler in node.handlers:
            result += " " + self._v(handler)
        if node.orelse:
            result += " else " + self._render_block(node.orelse)
        if node.finalbody:
            result += " finally " + self._render_block(node.finalbody)
        return result

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> str:
        if node.type is None:
            return "except " + self._render_block(node.body)
        type_text = self._v(node.type)
        head = f"except ({type_text})"
        if node.name is not None:
            head += f" as {node.name}"
        return head + " " + self._render_block(node.body)

    def visit_Match(self, node: ast.Match) -> str:
        cases = "\n".join(_indent_text(self._v(case)) for case in node.cases)
        return f"match ({self._v(node.subject)}) {{\n{cases}\n}}"

    def visit_match_case(self, node: ast.match_case) -> str:
        head = f"case ({self._render_pattern(node.pattern)})"
        if node.guard is not None:
            head += f" if ({self._v(node.guard)})"
        return head + " " + self._render_block(node.body)

    def visit_TypeAlias(self, node: ast.TypeAlias) -> str:
        name = self._render_name_or_expr(cast(ast.expr, node.name))
        type_params = self._render_type_params(node.type_params)
        return f"type {name}{type_params} = {self._v(node.value)}"

    def visit_FunctionType(self, node: FunctionType) -> str:
        return pretty_print_expr(node)

    def visit_ControlComprehension(self, node: ControlComprehension) -> str:
        func_def = get_control_comprehension_def(node)
        if func_def is None:
            raise ValueError("Control comprehension node has no function definition")
        rendered = self._render_control_comprehension(func_def)
        if rendered is None:
            raise ValueError(
                f"Unsupported control comprehension shape in '{func_def.name}'"
            )
        return rendered

    def visit_FunctionLiteral(self, node: FunctionLiteral) -> str:
        func_def = get_function_literal_def(node)
        args = self._render_arguments(func_def.args)
        ret = ""
        if func_def.returns is not None:
            ret = f" -> {self._v(func_def.returns)}"

        if (
            len(func_def.body) == 1
            and isinstance(func_def.body[0], ast.Return)
            and func_def.body[0].value is not None
        ):
            return f"({args}){ret} => {self._v(func_def.body[0].value)}"

        return f"({args}){ret} => " + self._render_block(func_def.body)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> str:
        decorators = [f"@{self._v(d)}" for d in node.decorator_list]
        static_prefix = "static " if is_static(node) else ""
        params = self._render_arguments(node.args)
        type_params = self._render_type_params(node.type_params)
        returns = "" if node.returns is None else f" -> {self._v(node.returns)}"
        head = f"{static_prefix}def {node.name}{type_params}({params}){returns}"
        rendered = head + " " + self._render_block(node.body)
        if decorators:
            return "\n".join([*decorators, rendered])
        return rendered

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> str:
        decorators = [f"@{self._v(d)}" for d in node.decorator_list]
        static_prefix = "static " if is_static(node) else ""
        params = self._render_arguments(node.args)
        type_params = self._render_type_params(node.type_params)
        returns = "" if node.returns is None else f" -> {self._v(node.returns)}"
        head = f"{static_prefix}async def {node.name}{type_params}({params}){returns}"
        rendered = head + " " + self._render_block(node.body)
        if decorators:
            return "\n".join([*decorators, rendered])
        return rendered

    def visit_ClassDef(self, node: ast.ClassDef) -> str:
        decorators = [f"@{self._v(d)}" for d in node.decorator_list]
        type_params = self._render_type_params(node.type_params)
        base_items = [self._v(b) for b in node.bases]
        base_items.extend(
            (
                f"{kw.arg}={self._v(kw.value)}"
                if kw.arg is not None
                else f"**{self._v(kw.value)}"
            )
            for kw in node.keywords
        )
        if base_items:
            head = f"class {node.name}{type_params}(" + ", ".join(base_items) + ")"
        else:
            head = f"class {node.name}{type_params}"
        rendered = head + " " + self._render_block(node.body)
        if decorators:
            return "\n".join([*decorators, rendered])
        return rendered


def typhon_unparse(node: ast.AST) -> str:
    if isinstance(node, ast.Module):
        module = node
    elif isinstance(node, ast.stmt):
        module = ast.Module(body=[node], type_ignores=[])
    elif isinstance(node, ast.expr):
        module = ast.Module(body=[ast.Expr(value=node)], type_ignores=[])
    else:
        raise TypeError(
            f"Unsupported node type for typhon_unparse: {type(node).__name__}"
        )

    visitor = _TyphonUnparseVisitor(module)
    rendered = cast(str, visitor.visit(node))
    return _strip_outer_parens(rendered) if isinstance(node, ast.expr) else rendered


__all__ = ["typhon_unparse"]
