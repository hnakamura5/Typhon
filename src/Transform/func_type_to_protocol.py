import ast
from ..Grammar.typhon_ast import (
    FunctionType,
    get_args_of_function_type,
    get_star_arg_of_function_type,
    get_star_kwds_of_function_type,
    get_return_of_function_type,
    get_empty_pos_attributes,
    get_pos_attributes,
)
from .visitor import TyphonASTVisitor
from .name_generator import get_protocol_name


class _Gather(TyphonASTVisitor):
    func_types: list[tuple[FunctionType, str]]

    def __init__(self):
        super().__init__()
        self.func_types = []

    def visit_FunctionType(self, node: FunctionType):
        self.func_types.append((node, self.new_arrow_type_name()))
        return self.generic_visit(node)


def add_import_for_protocol(mod: ast.Module):
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


def protocol_for_function_type(
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


def add_protocols(
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
        protocol_def = protocol_for_function_type(func_type, arrow_type_name)
        result[func_type] = protocol_def
        mod.body.insert(insert_point, protocol_def)
        insert_point += 1
    return result


def func_type_to_protocol(mod: ast.Module):
    gatherer = _Gather()
    gatherer.visit(mod)
    if not gatherer.func_types:
        return
    add_import_for_protocol(mod)
    add_protocols(mod, gatherer.func_types)
