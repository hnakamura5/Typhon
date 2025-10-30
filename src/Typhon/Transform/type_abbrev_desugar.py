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
    is_optional_question,
)
from ..Grammar.syntax_errors import raise_type_annotation_error
from .visitor import TyphonASTVisitor, TyphonASTTransformer
from .utils import add_import_for_protocol, get_insert_point_for_class
from ..Driver.debugging import debug_print, debug_verbose_print


class _GatherArrowType(TyphonASTVisitor):
    func_types: list[tuple[FunctionType, str]]

    def __init__(self, module: ast.Module):
        super().__init__(module)
        self.func_types = []

    def visit_FunctionType(self, node: FunctionType):
        self.func_types.append((node, self.new_arrow_type_name()))
        return self.generic_visit(node)


def _protocol_for_function_type(
    func_type: FunctionType, arrow_type_name: str, protocol_name: str
) -> ast.ClassDef:
    func_type.id = arrow_type_name
    args = get_args_of_function_type(func_type)
    posonlyargs: list[ast.arg] = []
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
            ast.Name(id=protocol_name, ctx=ast.Load()),
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
    mod: ast.Module, func_types: list[tuple[FunctionType, str]], protocol_name: str
) -> dict[FunctionType, ast.ClassDef]:
    result: dict[FunctionType, ast.ClassDef] = {}
    # Insert after imports.
    insert_point = get_insert_point_for_class(mod)
    for func_type, arrow_type_name in func_types:
        debug_print(
            f"Adding protocol for function type: {func_type.__dict__} as {arrow_type_name}"
        )
        protocol_def = _protocol_for_function_type(
            func_type, arrow_type_name, protocol_name
        )
        result[func_type] = protocol_def
        mod.body.insert(insert_point, protocol_def)
        insert_point += 1
    return result


class _OptionalQuestionTransformer(TyphonASTTransformer):
    def visit_Tuple(self, node: ast.Tuple):
        debug_verbose_print(
            f"Visiting Tuple: {ast.dump(node)} is_optional_question={is_optional_question(node)}"
        )
        if not is_optional_question(node):
            return self.generic_visit(node)
        pos = get_pos_attributes(node)
        if len(node.elts) != 1:
            raise_type_annotation_error(
                "Postfix `?` type annotation must have exactly one element type.", **pos
            )
        elt = node.elts[0]
        assert isinstance(elt, ast.expr), (
            f"Unexpected element in OptionalQuestion: {ast.dump(elt)}"
        )
        result = ast.BinOp(
            left=elt, op=ast.BitOr(), right=ast.Name(id="None", ctx=ast.Load()), **pos
        )
        return self.generic_visit(result)


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
        debug_verbose_print(f"Desugaring Tuple to tuple[]: {ast.dump(node)}")
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
        debug_verbose_print(f"Desugaring List to list[]: {ast.dump(node)}")
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
        protocol_name = add_import_for_protocol(mod)
        _add_protocols(mod, gatherer.func_types, protocol_name)
    # Run optional question first, as it is represented as Tuple nodes.
    _OptionalQuestionTransformer(mod).run()
    _TupleListTransformer(mod).run()
