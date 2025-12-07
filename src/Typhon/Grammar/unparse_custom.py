# type: ignore[all]
# TODO: Never forget implementation here is temporal hack.
import ast
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


def unparse_custom(node: ast.AST) -> str:
    unparser = CustomUnparser()
    return unparser.visit(node)
