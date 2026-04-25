# type: ignore[all]
# TODO: Never forget implementation here is temporal hack.
import ast

from .position import get_expr_format_anchors
from .typhon_ast import get_type_ignore_comment


# Hack the ast._Unparser to create our CustomUnparser.
# DO make new class from scratch when we need to change more things.
class CustomUnparser(ast._Unparser):
    def __init__(self):
        super().__init__()

    def visit_match_case(self, node):
        self.fill("case ")
        self.traverse(node.pattern)
        if node.guard:
            self.write(" if ")
            self.traverse(node.guard)
        with self.block(extra=get_type_ignore_comment(node)):
            self.traverse(node.body)

    def visit_Call(
        self,
        node: ast.Call,
    ):
        super().visit_Call(node)
        # Ad-hoc insertion of trailing comma. Mainly for signature help.
        comma_anchors = get_expr_format_anchors(node)
        if comma_anchors is not None and comma_anchors.trailing_comma is not None:
            self._source[-1] = ","
            self._source.extend(")")


# Utility for formatter and pretty printing.
class CustomUnparseHelper(ast._Unparser):
    def __init__(self):
        super().__init__()

    def get_binop_operator(self, op: ast.operator) -> str:
        return self.binop[op.__class__.__name__]

    def get_unaryop_operator(self, op: ast.unaryop) -> str:
        return self.unop[op.__class__.__name__]

    def get_cmpop_operator(self, op: ast.cmpop) -> str:
        return self.cmpops[op.__class__.__name__]


def unparse_custom(node: ast.AST) -> str:
    unparser = CustomUnparser()
    return unparser.visit(node)
