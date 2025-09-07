import ast
from typing import cast
from contextlib import contextmanager
from ..Grammar.typhon_ast import (
    FunctionType,
    get_args_of_function_type,
    get_star_arg_of_function_type,
    get_star_kwds_of_function_type,
    get_return_of_function_type,
    get_empty_pos_attributes,
    get_pos_attributes,
    is_typing_expression,
)
from ..Grammar.syntax_errors import raise_type_annotation_error
from .visitor import TyphonASTVisitor, TyphonASTTransformer
from .name_generator import get_protocol_name


class _GatherArrowType(TyphonASTVisitor):
    func_types: list[tuple[FunctionType, str]]

    def __init__(self, module: ast.Module):
        super().__init__(module)
        self.func_types = []

    def visit_FunctionType(self, node: FunctionType):
        self.func_types.append((node, self.new_arrow_type_name()))
        return self.generic_visit(node)


def _add_import_for_protocol(mod: ast.Module):
    # Duplicate import is NOT a problem, but better to avoid it for speed.
    import_stmt = ast.ImportFrom(
        module="typing",
        names=[
            ast.alias(
                name="Protocol",
                asname=get_protocol_name(),
                **get_empty_pos_attributes(),
            )
        ],
        level=0,
        **get_empty_pos_attributes(),
    )
    mod.body.insert(0, import_stmt)


def _protocol_for_function_type(
    func_type: FunctionType, arrow_type_name: str
) -> ast.ClassDef:
    func_type.id = arrow_type_name
    args = get_args_of_function_type(func_type)
    posonlyargs = []
    for arg in args:
        if len(arg.arg) == 0:
            arg.arg = f"{arrow_type_name}_a{len(posonlyargs)}"
            posonlyargs.append(arg)
        else:
            break
    named_args = args[len(posonlyargs) :]
    if not posonlyargs:
        named_args.insert(
            0, ast.arg(arg="self", annotation=None, **get_pos_attributes(func_type))
        )
    else:
        posonlyargs.insert(
            0, ast.arg(arg="self", annotation=None, **get_pos_attributes(func_type))
        )

    func_def = ast.FunctionDef(
        name="__call__",
        args=ast.arguments(
            posonlyargs=posonlyargs,
            args=named_args,
            vararg=get_star_arg_of_function_type(func_type),
            kwonlyargs=[],
            kw_defaults=[],
            kwarg=get_star_kwds_of_function_type(func_type),
            defaults=[],
        ),
        body=[ast.Expr(ast.Constant(value=Ellipsis))],
        decorator_list=[],
        returns=get_return_of_function_type(func_type),
        type_comment=None,
        lineno=func_type.lineno,
        col_offset=func_type.col_offset,
        end_lineno=func_type.end_lineno,
        end_col_offset=func_type.end_col_offset,
    )
    protocol_def = ast.ClassDef(
        name=arrow_type_name,
        bases=[
            ast.Name(id=get_protocol_name(), ctx=ast.Load()),
        ],
        keywords=[],
        body=[func_def],
        decorator_list=[],
        end_lineno=func_type.end_lineno,
        end_col_offset=func_type.end_col_offset,
        lineno=func_type.lineno,
        col_offset=func_type.col_offset,
    )
    return protocol_def


def _add_protocols(
    mod: ast.Module, func_types: list[tuple[FunctionType, str]]
) -> dict[FunctionType, ast.ClassDef]:
    result: dict[FunctionType, ast.ClassDef] = {}
    insert_point = 0
    # Insert after imports.
    for i, stmt in enumerate(mod.body):
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            insert_point = i + 1
        else:
            break
    for func_type, arrow_type_name in func_types:
        print(
            f"Adding protocol for function type: {func_type.__dict__} as {arrow_type_name}"
        )
        protocol_def = _protocol_for_function_type(func_type, arrow_type_name)
        result[func_type] = protocol_def
        mod.body.insert(insert_point, protocol_def)
        insert_point += 1
    return result


class _TupleListTransformer(TyphonASTTransformer):
    is_inside_typing_expr: bool

    def __init__(self, module: ast.Module):
        super().__init__(module)
        self.is_inside_typing_expr = False

    @contextmanager
    def _typing_expr(self, node: ast.AST):
        current = self.is_inside_typing_expr
        if isinstance(node, ast.expr) and is_typing_expression(node):
            self.is_inside_typing_expr = True
            yield
            self.is_inside_typing_expr = current
        else:
            yield

    def visit(self, node: ast.AST):
        with self._typing_expr(node):
            return super().visit(node)

    def visit_Tuple(self, node: ast.Tuple):
        if not self.is_inside_typing_expr:
            return self.generic_visit(node)
        pos = get_pos_attributes(node)
        print(f"Desugaring Tuple to tuple[]: {ast.dump(node)}")
        return ast.Subscript(
            value=ast.Name(id="tuple", **pos),
            slice=cast(ast.Tuple, self.generic_visit(node)),
            ctx=ast.Load(),
            **pos,
        )

    def visit_List(self, node: ast.List):
        if not self.is_inside_typing_expr:
            return self.generic_visit(node)
        pos = get_pos_attributes(node)
        print(f"Desugaring List to list[]: {ast.dump(node)}")
        if len(node.elts) != 1:
            raise_type_annotation_error(
                "List type annotation must have exactly one element type.", **pos
            )
        return ast.Subscript(
            value=ast.Name(id="list", **pos),
            slice=cast(ast.expr, self.visit(node.elts[0])),
            ctx=ast.Load(),
            **pos,
        )


def type_abbrev_desugar(mod: ast.Module):
    gatherer = _GatherArrowType(mod)
    gatherer.run()
    if gatherer.func_types:
        _add_import_for_protocol(mod)
        _add_protocols(mod, gatherer.func_types)
    _TupleListTransformer(mod).run()
