import ast
from ..Grammar.typhon_ast import (
    FunctionLiteral,
    get_function_literal_def,
    clear_function_literal_def,
    get_pos_attributes,
    is_placeholder,
)
from .visitor import TyphonASTVisitor, TyphonASTTransformer, flat_append
from dataclasses import dataclass


@dataclass
class PlaceholderInfo:
    placeholder: ast.Name
    parent_stmt: ast.stmt
    bound_expr: ast.expr


class _Gather(TyphonASTVisitor):
    placeholders: list[PlaceholderInfo]

    def __init__(self, module: ast.Module):
        super().__init__(module)
        self.func_literals = []
        self.placeholders = []

    def visit_Name(self, node: ast.Name):
        if is_placeholder(node):
            parent_stmt = self.parent_stmts[-1]
            bound_expr: ast.expr = node
            for parent_expr in reversed(self.parent_exprs):
                if bound_expr is not node:  # Placeholder alone is NOT the target.
                    if isinstance(parent_expr, (ast.Call)):
                        # Callee and arguments in function call are BOUNDARY.
                        break
                    # Pipe operator is BOUNDARY, but already expanded to function call.
                bound_expr = parent_expr
            if (bound_expr is node) or not parent_stmt:
                # TODO: better error message
                raise SyntaxError("Placeholder alone in statement is not allowed")
            print(f"Found placeholder: {node.id} bound_expr: {ast.dump(bound_expr)}")
            self.placeholders.append(
                PlaceholderInfo(
                    placeholder=node, parent_stmt=parent_stmt, bound_expr=bound_expr
                )
            )
        return self.generic_visit(node)


class _Transform(TyphonASTTransformer):
    parent_stmts_to_bound_expr_to_placeholders: dict[
        ast.stmt, dict[ast.expr, list[PlaceholderInfo]]
    ]
    bound_expr_to_function: dict[ast.expr, ast.FunctionDef]
    placeholder_to_args: dict[ast.Name, ast.arg]

    def __init__(
        self,
        module: ast.Module,
        parent_stmts_to_bound_expr_to_placeholders: dict[
            ast.stmt, dict[ast.expr, list[PlaceholderInfo]]
        ],
    ):
        super().__init__(module)
        self.parent_stmts_to_bound_expr_to_placeholders = (
            parent_stmts_to_bound_expr_to_placeholders
        )
        self.bound_expr_to_function = {}
        self.placeholder_to_args = {}

    def _placeholder_to_func_literal(
        self, bound_expr: ast.expr, placeholders_inside: list[PlaceholderInfo]
    ) -> ast.FunctionDef:
        posonlyargs = []
        for i, info in enumerate(placeholders_inside):
            arg = ast.arg(
                arg=self.new_arg_name(str(i)),
                **get_pos_attributes(info.placeholder),
            )
            posonlyargs.append(arg)
            self.placeholder_to_args[info.placeholder] = arg
            print(
                f"Mapping placeholder {info.placeholder.id} to arg {arg.arg} in bound_expr {ast.dump(bound_expr)}"
            )
        func_def = ast.FunctionDef(
            name=self.new_func_literal_name(),
            args=ast.arguments(
                posonlyargs=posonlyargs,
                args=[],
                vararg=None,
                kwonlyargs=[],
                kw_defaults=[],
                kwarg=None,
                defaults=[],
            ),
            body=[ast.Return(value=bound_expr, **get_pos_attributes(bound_expr))],
            decorator_list=[],
            returns=None,
            type_comment=None,
            **get_pos_attributes(bound_expr),
        )
        return func_def  # Return the constructed function definition

    def visit(self, node: ast.AST):
        print(f"placeholder_to_function _transform visit: {ast.dump(node)}")
        if isinstance(node, ast.stmt):
            # Expand the def of function literals before the parent statement.
            result: list[ast.AST] = []
            bound_expr_to_placeholders = (
                self.parent_stmts_to_bound_expr_to_placeholders.get(node, None)
            )
            if bound_expr_to_placeholders is not None:
                for bound_expr, placeholders in bound_expr_to_placeholders.items():
                    func_def = self._placeholder_to_func_literal(
                        bound_expr, placeholders
                    )
                    result.append(func_def)
                    self.bound_expr_to_function[bound_expr] = func_def
            node_result = super().visit(node)
            flat_append(result, node_result)
            return result
        # Transform the expression transformed into function.
        if isinstance(node, ast.expr):
            function_def_for_bound_expr = self.bound_expr_to_function.get(node, None)
            if function_def_for_bound_expr is not None:
                print(
                    f"Transforming expression: {ast.dump(node)} to function: {function_def_for_bound_expr.name}"
                )
                # This expression is transformed to function.
                # Replace only once for the original bound expression.
                # (Be attention not to replace again in transformed function.)
                self.bound_expr_to_function.pop(node)
                self.generic_visit(function_def_for_bound_expr)
                return ast.Name(
                    id=function_def_for_bound_expr.name,
                    ctx=ast.Load(),
                    **get_pos_attributes(node),
                )
            print(f"Visiting expr: {ast.dump(node)}")
        return super().visit(node)

    def visit_Name(self, node: ast.Name):
        print(f"visit_Name: {ast.dump(node)}")
        arg = self.placeholder_to_args.get(node, None)
        if arg:
            print(f"Replacing placeholder {node.id} with arg {arg.arg}")
            return ast.Name(
                id=arg.arg,
                ctx=ast.Load(),
                **get_pos_attributes(node),
            )
        return self.generic_visit(node)


# Entry point for the transformation.
# Run after function_literal_to_def.
# Run after scope_check_rename. It marks the placeholder underscores.
# Pipe operator is already expanded to function call (currently in parser).
def placeholder_to_func(mod: ast.Module):
    gatherer = _Gather(mod)
    # First, gather all function literals with their parent statements.
    gatherer.run()
    # Do transform to the literals and the parent statements.
    parent_stmts_to_bound_expr_to_placeholders: dict[
        ast.stmt, dict[ast.expr, list[PlaceholderInfo]]
    ] = {}
    for info in gatherer.placeholders:
        parent_stmts_to_bound_expr_to_placeholders.setdefault(
            info.parent_stmt, {}
        ).setdefault(info.bound_expr, []).append(info)

    transformer = _Transform(mod, parent_stmts_to_bound_expr_to_placeholders)
    transformer.run()
