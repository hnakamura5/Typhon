import ast
from ..Grammar.typhon_ast import (
    FunctionLiteral,
    get_function_literal_def,
    clear_function_literal_def,
    get_pos_attributes,
)
from .visitor import TyphonASTVisitor, TyphonASTTransformer, flat_append


def _is_ellipsis(node: ast.expr) -> bool:
    return isinstance(node, ast.Constant) and node.value is Ellipsis


class _Gather(TyphonASTVisitor):
    func_literals: list[tuple[FunctionLiteral, ast.stmt]]
    placeholder_func_literals: list[tuple[ast.Call, ast.stmt]]

    def __init__(self, module: ast.Module):
        super().__init__(module)
        self.func_literals = []
        self.placeholder_func_literals = []

    def visit_FunctionLiteral(self, node: FunctionLiteral):
        print(f"func_literal_to_def _Gather visit: {node} {node.__dict__}")
        self.func_literals.append((node, self.parent_stmts[-1]))
        return self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if sum(_is_ellipsis(arg) for arg in node.args) or any(
            _is_ellipsis(kw.value) for kw in node.keywords
        ):
            print(
                f"func_literal_to_def _Gather visit Call with ellipsis: {node} {node.__dict__}"
            )
            self.placeholder_func_literals.append((node, self.parent_stmts[-1]))
        return self.generic_visit(node)


class _Transform(TyphonASTTransformer):
    func_literals: dict[FunctionLiteral, ast.stmt]
    parent_stmts_for_literals: dict[ast.stmt, list[FunctionLiteral]]
    parent_stmts_for_placeholders: dict[ast.stmt, list[ast.Call]]
    placeholder_to_calls: dict[ast.Call, ast.FunctionDef]
    placeholder_calls: set[ast.Call]

    def __init__(
        self,
        module: ast.Module,
        func_literals: dict[FunctionLiteral, ast.stmt],
        parent_stmts_for_literals: dict[ast.stmt, list[FunctionLiteral]],
        parent_stmts_for_placeholders: dict[ast.stmt, list[ast.Call]],
        placeholder_calls: set[ast.Call],
    ):
        super().__init__(module)
        self.func_literals = func_literals
        self.parent_stmts_for_literals = parent_stmts_for_literals
        self.parent_stmts_for_placeholders = parent_stmts_for_placeholders
        self.placeholder_calls = placeholder_calls
        self.placeholder_to_calls = {}

    def _placeholder_to_func_literal(self, node: ast.Call) -> ast.FunctionDef:
        placed_args: list[ast.arg] = []
        for i in range(len(node.args)):
            arg = node.args[i]
            if _is_ellipsis(arg):
                arg_name = self.new_arg_name(str(i))
                node.args[i] = ast.Name(
                    id=arg_name, ctx=ast.Load(), **get_pos_attributes(arg)
                )
                placed_args.append(
                    ast.arg(
                        arg=arg_name,
                        annotation=None,
                        **get_pos_attributes(arg),
                    )
                )
        for i in range(len(node.keywords)):
            kw = node.keywords[i]
            if _is_ellipsis(kw.value):
                arg_name = self.new_arg_name(kw.arg or str(i))
                kw.value = ast.Name(
                    id=arg_name, ctx=ast.Load(), **get_pos_attributes(kw)
                )
                placed_args.append(
                    ast.arg(
                        arg=arg_name,
                        annotation=None,
                        **get_pos_attributes(node.keywords[i]),
                    )
                )
        func_def = ast.FunctionDef(
            name=self.new_func_literal_name(),
            args=ast.arguments(
                posonlyargs=[],
                args=placed_args,
                vararg=None,
                kwonlyargs=[],
                kw_defaults=[],
                kwarg=None,
                defaults=[],
            ),
            body=[ast.Return(value=node, **get_pos_attributes(node))],
            decorator_list=[],
            returns=None,
            type_comment=None,
            **get_pos_attributes(node),
        )
        return func_def  # Return the constructed function definition

    def visit(self, node: ast.AST):
        if not isinstance(node, ast.stmt):
            return super().visit(node)
        result: list[ast.AST] = []
        print(f"func_literal_to_def _Transform visit: {node} {node.__dict__}")
        # Expand the def of function literals before the parent statement.
        if node in self.parent_stmts_for_literals:
            for func_literal in self.parent_stmts_for_literals[node]:
                func_def = get_function_literal_def(func_literal)
                func_def.name = self.new_func_literal_name()
                func_literal.id = func_def.name
                flat_append(result, self.visit(func_def))
                clear_function_literal_def(func_literal)
        if node in self.parent_stmts_for_placeholders:
            for call in self.parent_stmts_for_placeholders[node]:
                func_def = self._placeholder_to_func_literal(call)
                self.placeholder_to_calls[call] = func_def
                result.append(func_def)
        node_result = super().visit(node)
        flat_append(result, node_result)
        return result

    def visit_Call(self, node: ast.Call):
        if node in self.placeholder_calls:
            func_def = self.placeholder_to_calls.get(node, None)
            assert func_def is not None, "Placeholder call must have a function def"
            return ast.Name(
                id=func_def.name, ctx=ast.Load(), **get_pos_attributes(node)
            )
        return self.generic_visit(node)


# Entry point for the transformation.
def func_literal_to_def(mod: ast.Module):
    gatherer = _Gather(mod)
    # First, gather all function literals with their parent statements.
    gatherer.run()
    # Do transform to the literals and the parent statements.
    func_literals = {}
    parent_stmts_for_literals = {}
    parent_stmts_for_placeholders = {}
    for func_literal, parent_stmt in gatherer.func_literals:
        func_literals[func_literal] = parent_stmt
        parent_stmts_for_literals.setdefault(parent_stmt, []).append(func_literal)
    placeholder_calls = set()
    for call, parent_stmt in gatherer.placeholder_func_literals:
        placeholder_calls.add(call)
        parent_stmts_for_placeholders.setdefault(parent_stmt, []).append(call)
    transformer = _Transform(
        mod,
        func_literals,
        parent_stmts_for_literals,
        parent_stmts_for_placeholders,
        placeholder_calls,
    )
    transformer.run()
