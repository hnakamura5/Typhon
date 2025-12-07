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
from ..Driver.debugging import debug_print, debug_verbose_print


@dataclass
class PlaceholderInfo:
    placeholder: ast.Name
    parent_stmt: ast.stmt
    bound_expr: ast.expr


class _Gather(TyphonASTVisitor):
    placeholders: list[PlaceholderInfo]

    def __init__(self, module: ast.Module):
        super().__init__(module)
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
            debug_print(
                f"Found placeholder: {node.id} bound_expr: {ast.dump(bound_expr)}"
            )
            self.placeholders.append(
                PlaceholderInfo(
                    placeholder=node, parent_stmt=parent_stmt, bound_expr=bound_expr
                )
            )
        return self.generic_visit(node)


class _Transform(TyphonASTTransformer):
    bound_exprs_to_placeholders: dict[ast.expr, list[PlaceholderInfo]]
    placeholder_to_args: dict[ast.Name, ast.arg]

    def __init__(
        self,
        module: ast.Module,
        bound_exprs_to_placeholders: dict[ast.expr, list[PlaceholderInfo]],
    ):
        super().__init__(module)
        self.bound_exprs_to_placeholders = bound_exprs_to_placeholders
        self.placeholder_to_args = {}

    def _placeholder_to_lambda(
        self, bound_expr: ast.expr, placeholders_inside: list[PlaceholderInfo]
    ) -> ast.Lambda:
        posonlyargs: list[ast.arg] = []
        for i, info in enumerate(placeholders_inside):
            arg = ast.arg(
                arg=self.new_arg_name(str(i)),
                **get_pos_attributes(info.placeholder),
            )
            posonlyargs.append(arg)
            self.placeholder_to_args[info.placeholder] = arg
            debug_print(
                f"Mapping placeholder {info.placeholder.id} to arg {arg.arg} in bound_expr {ast.dump(bound_expr)}"
            )
        lambda_expr = ast.Lambda(
            args=ast.arguments(
                posonlyargs=posonlyargs,
                args=[],
                vararg=None,
                kwonlyargs=[],
                kw_defaults=[],
                kwarg=None,
                defaults=[],
            ),
            body=bound_expr,
            **get_pos_attributes(bound_expr),
        )
        return lambda_expr

    def visit(self, node: ast.AST):
        # Transform the expression transformed into function.
        if isinstance(node, ast.expr):
            if node in self.bound_exprs_to_placeholders:
                debug_print(
                    f"Visiting parent statement with placeholders: {ast.dump(node)}"
                )
                lambda_expr = self._placeholder_to_lambda(
                    node,
                    self.bound_exprs_to_placeholders[node],
                )
                self.generic_visit(node)
                return lambda_expr
        return super().visit(node)

    def visit_Name(self, node: ast.Name):
        arg = self.placeholder_to_args.get(node, None)
        if arg:
            debug_verbose_print(f"Replacing placeholder {node.id} with arg {arg.arg}")
            return ast.Name(
                id=arg.arg,
                ctx=ast.Load(),
                **get_pos_attributes(node),
            )
        return self.generic_visit(node)


# Entry point for the transformation.
# Run after all process that expands expressions to function.
#   - function_literal_to_def
#   - comprehension_to_function
# Run after scope_check_rename. It marks the placeholder underscores.
# Pipe operator is already expanded to function call (currently in parser).
def placeholder_to_func(mod: ast.Module):
    gatherer = _Gather(mod)
    # First, gather all function literals with their parent statements.
    gatherer.run()
    # Do transform to the literals and the parent statements.
    bound_expr_to_placeholder_def: dict[ast.expr, list[PlaceholderInfo]] = {}
    for info in gatherer.placeholders:
        bound_expr_to_placeholder_def.setdefault(info.bound_expr, []).append(info)
    transformer = _Transform(mod, bound_expr_to_placeholder_def)
    transformer.run()
