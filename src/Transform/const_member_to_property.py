import ast
from ..Grammar.typhon_ast import is_decl_assign, get_pos_attributes, is_let_assign
from .visitor import TyphonASTTransformer, flat_append


class ConstMemberToProperty(TyphonASTTransformer):
    def __init__(self, module: ast.Module):
        super().__init__(module)
        self.func_literals = []

    def is_in_class_def(self):
        return isinstance(self.get_parent_python_scope(), ast.ClassDef)

    def _visit_Decl(self, node: ast.Assign | ast.AnnAssign, target: ast.Name):
        assert is_decl_assign(node), "Unexpected non-decl assign in class def"
        if not is_let_assign(node):
            return self.generic_visit(node)
        result: list[ast.AST] = []
        pos = get_pos_attributes(node)
        target_name = target.id
        new_hiding_name = self.new_const_rename_name(target_name)
        target.id = new_hiding_name
        result.append(
            # def <target_name>(self): return self.<hiding_name>
            ast.FunctionDef(
                decorator_list=[ast.Name(id="property", ctx=ast.Load(), **pos)],
                name=target_name,
                args=ast.arguments(
                    posonlyargs=[],
                    args=[ast.arg(arg="self", annotation=None, **pos)],
                    kwonlyargs=[],
                    kw_defaults=[],
                    defaults=[],
                ),
                # return self.<hiding_name>
                body=[
                    ast.Return(
                        value=ast.Attribute(
                            value=ast.Name(id="self", ctx=ast.Load()),
                            attr=new_hiding_name,
                            ctx=ast.Load(),
                            **pos,
                        ),
                        **pos,
                    )
                ],
                returns=None,
                type_comment=None,
                **pos,
            )
        )
        flat_append(result, self.generic_visit(node))
        return result

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
        return self._visit_Decl(node, target)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if not self.is_in_class_def():
            return self.generic_visit(node)
        target = node.target
        assert isinstance(target, ast.Name), (
            "Only simple name target assign is supported. And it should be checked."
        )
        return self._visit_Decl(node, target)


def const_member_to_property(module: ast.Module):
    ConstMemberToProperty(module).run()
