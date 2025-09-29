import ast
from ..Grammar.typhon_ast import (
    is_decl_assign,
    get_pos_attributes,
    is_let_assign,
    add_import_alias_top,
)
from .visitor import TyphonASTTransformer, flat_append
from .name_generator import get_final_name


class ConstMemberToFinal(TyphonASTTransformer):
    def __init__(self, module: ast.Module):
        super().__init__(module)
        self.func_literals = []
        self.changed = False

    def is_in_class_def(self):
        return isinstance(self.get_parent_python_scope(), ast.ClassDef)

    def _visit_Decl(
        self,
        node: ast.Assign | ast.AnnAssign,
        target: ast.Name,
        annotation: ast.expr | None,
    ):
        assert is_decl_assign(node), "Unexpected non-decl assign in class def"
        if not is_let_assign(node):
            return self.generic_visit(node)
        self.changed = True
        pos = get_pos_attributes(node)
        self.generic_visit(node)
        if annotation is not None:
            new_annotation = ast.Subscript(
                value=ast.Name(id=get_final_name(), ctx=ast.Load(), **pos),
                slice=annotation,
                ctx=ast.Load(),
                **pos,
            )
        else:
            new_annotation = ast.Name(id=get_final_name(), ctx=ast.Load(), **pos)
        return ast.AnnAssign(
            target=ast.Name(id=target.id, ctx=ast.Store(), **pos),
            annotation=new_annotation,
            value=node.value,
            simple=1,
            **pos,
        )

    def visit_Assign(self, node: ast.Assign):
        if not self.is_in_class_def():
            return self.generic_visit(node)
        assert len(node.targets) == 1, (
            "Only single target assign is supported. And it should be checked."
        )
        target = node.targets[0]
        assert isinstance(target, ast.Name), (
            "Only simple name target assign is supported. And it should be checked."
        )
        return self._visit_Decl(node, target, None)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if not self.is_in_class_def():
            return self.generic_visit(node)
        target = node.target
        assert isinstance(target, ast.Name), (
            "Only simple name target assign is supported. And it should be checked."
        )
        return self._visit_Decl(node, target, node.annotation)


def _add_import_for_final(mod: ast.Module):
    add_import_alias_top(mod, "typing", "Final", get_final_name())


def const_member_to_final(module: ast.Module):
    transformer = ConstMemberToFinal(module)
    transformer.run()
    if transformer.changed:
        _add_import_for_final(module)
