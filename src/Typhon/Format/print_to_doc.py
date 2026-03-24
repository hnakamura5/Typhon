from __future__ import annotations

import ast
from typing import cast

from Typhon.Grammar.pretty_printer import pretty_print_expr
from Typhon.Grammar.typhon_ast import (
    FunctionLiteral,
    FunctionType,
    get_constant_raw_tokens,
    get_control_comprehension_def,
    get_function_literal_def,
    get_wrapper_paren_tokens,
)
from Typhon.Transform.visitor import TyphonASTRawVisitor

from .doc_datatype import Doc, NIL, concat, group, hardline, join, text


_BINOP_SYMBOLS: dict[type[ast.operator], str] = {
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "*",
    ast.MatMult: "@",
    ast.Div: "/",
    ast.FloorDiv: "//",
    ast.Mod: "%",
    ast.Pow: "**",
    ast.LShift: "<<",
    ast.RShift: ">>",
    ast.BitAnd: "&",
    ast.BitOr: "|",
    ast.BitXor: "^",
}

_UNARY_SYMBOLS: dict[type[ast.unaryop], str] = {
    ast.Invert: "~",
    ast.Not: "not ",
    ast.UAdd: "+",
    ast.USub: "-",
}


class _PrintToDocVisitor(TyphonASTRawVisitor):
    """Translate Typhon AST nodes to Doc intermediate representation.

    This visitor intentionally supports a small, composable core and falls back to
    textual rendering for unsupported nodes.
    """

    def __init__(self, module: ast.Module):
        super().__init__()
        self.module = module

    def _maybe_wrap_group_paren(self, node: ast.expr, doc: Doc) -> Doc:
        wrappers = get_wrapper_paren_tokens(node)
        if not wrappers:
            return doc
        if len(wrappers) < 2:
            return doc
        return concat([text(wrappers[0].string), doc, text(wrappers[-1].string)])

    def _visit_doc(self, node: ast.AST) -> Doc:
        return cast(Doc, self.visit(node))

    def _fallback_expr_doc(self, node: ast.expr) -> Doc:
        try:
            rendered = pretty_print_expr(node)
        except Exception:
            rendered = ast.unparse(node)
        return self._maybe_wrap_group_paren(node, text(rendered))

    def _fallback_stmt_doc(self, node: ast.stmt) -> Doc:
        return text(ast.unparse(node).strip())

    def visit_Module(self, node: ast.Module) -> Doc:
        if len(node.body) == 0:
            return NIL
        return join(hardline(), [self._visit_doc(stmt) for stmt in node.body])

    def visit_Expr(self, node: ast.Expr) -> Doc:
        return self._visit_doc(node.value)

    def visit_Name(self, node: ast.Name) -> Doc:
        return self._maybe_wrap_group_paren(node, text(node.id))

    def visit_Constant(self, node: ast.Constant) -> Doc:
        raw_tokens = get_constant_raw_tokens(node)
        if raw_tokens:
            return self._maybe_wrap_group_paren(
                node,
                text("".join(tok.string for tok in raw_tokens)),
            )
        return self._fallback_expr_doc(node)

    def visit_BinOp(self, node: ast.BinOp) -> Doc:
        op = _BINOP_SYMBOLS.get(type(node.op))
        if op is None:
            return self._fallback_expr_doc(node)
        doc = group(
            concat(
                [
                    self._visit_doc(node.left),
                    text(" "),
                    text(op),
                    text(" "),
                    self._visit_doc(node.right),
                ]
            )
        )
        return self._maybe_wrap_group_paren(node, doc)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Doc:
        op = _UNARY_SYMBOLS.get(type(node.op))
        if op is None:
            return self._fallback_expr_doc(node)
        doc = concat([text(op), self._visit_doc(node.operand)])
        return self._maybe_wrap_group_paren(node, doc)

    def visit_Call(self, node: ast.Call) -> Doc:
        args_docs = [self._visit_doc(arg) for arg in node.args]
        kw_docs = [
            concat([text(kw.arg), text("="), self._visit_doc(kw.value)])
            if kw.arg is not None
            else concat([text("**"), self._visit_doc(kw.value)])
            for kw in node.keywords
        ]
        all_args = args_docs + kw_docs
        doc = concat(
            [
                self._visit_doc(node.func),
                text("("),
                join(concat([text(","), text(" ")]), all_args),
                text(")"),
            ]
        )
        return self._maybe_wrap_group_paren(node, doc)

    def visit_Attribute(self, node: ast.Attribute) -> Doc:
        doc = concat([self._visit_doc(node.value), text("."), text(node.attr)])
        return self._maybe_wrap_group_paren(node, doc)

    def visit_Subscript(self, node: ast.Subscript) -> Doc:
        doc = concat(
            [
                self._visit_doc(node.value),
                text("["),
                self._visit_doc(node.slice),
                text("]"),
            ]
        )
        return self._maybe_wrap_group_paren(node, doc)

    def visit_List(self, node: ast.List) -> Doc:
        doc = concat(
            [
                text("["),
                join(
                    concat([text(","), text(" ")]),
                    [self._visit_doc(e) for e in node.elts],
                ),
                text("]"),
            ]
        )
        return self._maybe_wrap_group_paren(node, doc)

    def visit_Tuple(self, node: ast.Tuple) -> Doc:
        if len(node.elts) == 1:
            inner = concat([self._visit_doc(node.elts[0]), text(",")])
        else:
            inner = join(
                concat([text(","), text(" ")]), [self._visit_doc(e) for e in node.elts]
            )
        doc = concat([text("("), inner, text(")")])
        return self._maybe_wrap_group_paren(node, doc)

    def visit_FunctionLiteral(self, node: FunctionLiteral) -> Doc:
        func_def = get_function_literal_def(node)
        return text(func_def.name)

    def visit_FunctionType(self, node: FunctionType) -> Doc:
        return text(pretty_print_expr(node))

    def visit_ControlComprehension(self, node: ast.Name) -> Doc:
        func_def = get_control_comprehension_def(node)
        if func_def is None:
            return text(node.id)
        return text(func_def.name)

    def visit_Assign(self, node: ast.Assign) -> Doc:
        return self._fallback_stmt_doc(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> Doc:
        return self._fallback_stmt_doc(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> Doc:
        return self._fallback_stmt_doc(node)

    def visit_Return(self, node: ast.Return) -> Doc:
        return self._fallback_stmt_doc(node)

    def visit_Pass(self, node: ast.Pass) -> Doc:
        return self._fallback_stmt_doc(node)

    def visit_If(self, node: ast.If) -> Doc:
        return self._fallback_stmt_doc(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Doc:
        return self._fallback_stmt_doc(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Doc:
        return self._fallback_stmt_doc(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> Doc:
        return self._fallback_stmt_doc(node)


def print_to_doc(node: ast.AST) -> Doc:
    if isinstance(node, ast.Module):
        module = node
    else:
        module = ast.Module(
            body=[ast.Expr(value=cast(ast.expr, node))], type_ignores=[]
        )
    visitor = _PrintToDocVisitor(module)
    return cast(Doc, visitor.visit(node))
