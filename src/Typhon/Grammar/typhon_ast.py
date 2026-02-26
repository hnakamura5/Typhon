# Ast Extensions for Typhon
from __future__ import annotations
import re
from typing import (
    Union,
    Unpack,
    TypedDict,
    Tuple,
    cast,
    TYPE_CHECKING,
    Optional,
    List,
    Any,
)
import ast
from dataclasses import dataclass
from copy import copy
from tokenize import TokenInfo
from ..Driver.debugging import debug_print, debug_verbose_print

if TYPE_CHECKING:
    from .parser_helper import Parser


# Same as ast module's position attributes
class PosAttributes(TypedDict):
    lineno: int
    col_offset: int
    end_lineno: int | None
    end_col_offset: int | None


def unpack_pos_default(pos: PosAttributes) -> Tuple[int, int, int, int]:
    return (
        pos["lineno"],
        pos["col_offset"],
        pos["end_lineno"] or pos["lineno"],
        pos["end_col_offset"] or pos["col_offset"] + 1,
    )


def unpack_pos_tuple(pos: PosAttributes) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    return (
        (pos["lineno"], pos["col_offset"]),
        (
            pos["end_lineno"] or pos["lineno"],
            pos["end_col_offset"] or pos["col_offset"] + 1,
        ),
    )


class PosRange(TypedDict):
    lineno: int
    col_offset: int
    end_lineno: int
    end_col_offset: int


def pos_attribute_to_range(pos: PosAttributes) -> PosRange:
    result: PosRange = {
        "lineno": pos["lineno"],
        "col_offset": pos["col_offset"],
        "end_lineno": pos["end_lineno"]
        if pos["end_lineno"] is not None
        else pos["lineno"],
        "end_col_offset": pos["end_col_offset"]
        if pos["end_col_offset"] is not None
        else pos["col_offset"],
    }

    return result


type PosNode = (
    ast.stmt
    | ast.expr
    | ast.alias
    | ast.arg
    | ast.type_param
    | ast.excepthandler
    | ast.pattern
    | ast.keyword
    | ast.match_case
)


def get_pos_attributes(node: PosNode | TokenInfo) -> PosAttributes:
    if isinstance(node, TokenInfo):
        return PosAttributes(
            lineno=node.start[0],
            col_offset=node.start[1],
            end_lineno=node.end[0],
            end_col_offset=node.end[1],
        )
    return PosAttributes(
        lineno=getattr(node, "lineno", 1),
        col_offset=getattr(node, "col_offset", 0),
        end_lineno=getattr(node, "end_lineno", None),
        end_col_offset=getattr(node, "end_col_offset", None),
    )


def get_pos_attributes_if_exists(node: ast.AST) -> PosAttributes | None:
    if hasattr(node, "lineno") and hasattr(node, "col_offset"):
        return PosAttributes(
            lineno=getattr(node, "lineno"),
            col_offset=getattr(node, "col_offset"),
            end_lineno=getattr(node, "end_lineno", None),
            end_col_offset=getattr(node, "end_col_offset", None),
        )
    return None


def get_empty_pos_attributes() -> PosAttributes:
    # Python ast position is 1-based for line, 0-based for column
    return PosAttributes(
        lineno=1,
        col_offset=0,
        end_lineno=1,
        end_col_offset=0,
    )


_ANONYMOUS_NAME = "_typh_anonymous"


def set_anonymous_name_id(node: ast.Name, id: int) -> ast.Name:
    setattr(node, _ANONYMOUS_NAME, id)
    return node


def get_anonymous_base_name() -> str:
    return _ANONYMOUS_NAME


def get_anonymous_name_id(node: ast.Name) -> int | None:
    return getattr(node, _ANONYMOUS_NAME, None)


def clear_anonymous_name(node: ast.Name) -> None:
    if hasattr(node, _ANONYMOUS_NAME):
        delattr(node, _ANONYMOUS_NAME)


def is_anonymous_name(node: ast.Name) -> bool:
    return hasattr(node, _ANONYMOUS_NAME)


def copy_anonymous_name(src: ast.Name, ctx: ast.expr_context) -> ast.Name:
    result = ast.Name(src.id, ctx, **get_pos_attributes(src))
    anon_id = get_anonymous_name_id(src)
    if anon_id is not None:
        set_anonymous_name_id(result, anon_id)
    return result


_TYPE_INVALID_NAME = "_typh_invalid_name"


def get_invalid_name() -> str:
    return _TYPE_INVALID_NAME


_TYPE_IGNORE_NODES = "_typh_type_ignore"


def get_type_ignore_tag(node: ast.AST) -> str | None:
    return getattr(node, _TYPE_IGNORE_NODES, None)


def get_type_ignore_comment(node: ast.AST) -> str | None:
    tag = get_type_ignore_tag(node)
    if tag is not None:
        return f"# type: ignore[{tag}]"
    return None


def set_type_ignore_node(node: ast.AST, tag: str) -> ast.AST:
    setattr(node, _TYPE_IGNORE_NODES, tag)
    return node


def is_type_ignore_node(node: ast.AST) -> bool:
    return hasattr(node, _TYPE_IGNORE_NODES)


def clear_type_ignore_node(node: ast.AST) -> None:
    if hasattr(node, _TYPE_IGNORE_NODES):
        delattr(node, _TYPE_IGNORE_NODES)


# The name is internal when it has no counterpart in input typhon source code.
_INTERNAL_NAME = "_typh_internal_name"


def is_internal_name(name: ast.Name) -> bool:
    return getattr(name, _INTERNAL_NAME, False)


def set_is_internal_name(name: ast.Name, is_internal: bool = True) -> ast.Name:
    setattr(name, _INTERNAL_NAME, is_internal)
    return name


def clear_internal_name(name: ast.Name) -> None:
    if hasattr(name, _INTERNAL_NAME):
        delattr(name, _INTERNAL_NAME)


# Normal assignments, let assignments for variable declarations,
# and constant assignments for constant definitions.
# They all are Assign/AnnAssign in Python, we distinguish them by
# additional attribute which the user can only access by API here.


# Note that inheriting from ast.Assign or ast.AnnAssign is not recommended
# because that breaks AST visitor (e.g.unparse method) that use type name
# directly to distinguish nodes.


def is_decl_stmt(node: ast.AST) -> bool:
    return isinstance(node, (ast.Assign, ast.AnnAssign))


DeclarableStmt = (
    ast.Assign
    | ast.AnnAssign
    | ast.withitem
    | ast.For
    | ast.AsyncFor
    | ast.comprehension
    | ast.pattern
)

_IS_VAR = "_typh_is_var"
_IS_LET = "_typh_is_let"
_TYPE_ANNOTATION = "_typh_annotation"
_IS_MULTI_DECL = "_typh_is_multi_decl"
_IS_TYPING_EXPRESSION = "_typh_is_typing_expression"


def is_var(node: DeclarableStmt) -> bool:
    return getattr(node, _IS_VAR, False)


def is_var_assign(node: ast.AST) -> bool:
    if not is_decl_stmt(node):
        return False
    return getattr(node, _IS_VAR, False)


def is_let(node: DeclarableStmt) -> bool:
    return getattr(node, _IS_LET, False)


def is_let_assign(node: ast.AST) -> bool:
    if not is_decl_stmt(node):
        return False
    return getattr(node, _IS_LET, False)


def is_decl_assign(node: ast.AST) -> bool:
    """Check if the node is a declaration assignment (let or var)."""
    return is_var_assign(node) or is_let_assign(node)


def set_is_var(node: DeclarableStmt):
    setattr(node, _IS_VAR, True)


def _set_is_let(node: DeclarableStmt):
    setattr(node, _IS_LET, True)


def _set_is_let_var(node: DeclarableStmt, decl_type: str):
    if decl_type == "var":
        set_is_var(node)
    elif decl_type == "let":
        _set_is_let(node)
    else:
        raise ValueError(f"Unknown declaration type: {decl_type}")


def copy_is_let_var[T: DeclarableStmt](src: DeclarableStmt, dest: T) -> T:
    if is_var(src):
        set_is_var(dest)
    if is_let(src):
        _set_is_let(dest)
    return dest


type PossibleAnnotatedNode = (
    ast.Name
    | ast.withitem
    | ast.For
    | ast.AsyncFor
    | ast.comprehension
    | ast.Starred
    | ast.pattern
    | ast.Tuple
    | ast.List
)


def set_type_annotation[T: PossibleAnnotatedNode](
    node: T, type_node: ast.expr | None
) -> T:
    debug_verbose_print(
        f"set_type_annotation: {ast.dump(node)} to {ast.dump(type_node) if type_node else 'None'}"
    )
    setattr(node, _TYPE_ANNOTATION, type_node)
    return node


def get_type_annotation(node: PossibleAnnotatedNode) -> ast.expr | None:
    return getattr(node, _TYPE_ANNOTATION, None)


def clear_type_annotation(node: ast.AST) -> None:
    if hasattr(node, _TYPE_ANNOTATION):
        delattr(node, _TYPE_ANNOTATION)


def set_is_multi_decl(node: ast.AST, is_multi: bool = True) -> ast.AST:
    setattr(node, _IS_MULTI_DECL, is_multi)
    return node


def is_multi_decl(node: ast.AST) -> bool:
    return getattr(node, _IS_MULTI_DECL, False)


def clear_is_multi_decl(node: ast.AST) -> None:
    if hasattr(node, _IS_MULTI_DECL):
        delattr(node, _IS_MULTI_DECL)


def set_is_typing_expression(node: ast.expr, is_typing: bool = True) -> ast.expr:
    result = copy(node)  # To avoid chached node is contaminated.
    setattr(result, _IS_TYPING_EXPRESSION, is_typing)
    debug_verbose_print(f"set_is_typing_expression: {ast.dump(result)}")
    return result


def is_typing_expression(node: ast.expr) -> bool:
    return getattr(node, _IS_TYPING_EXPRESSION, False)


def clear_is_typing_expression(node: ast.expr) -> None:
    if hasattr(node, _IS_TYPING_EXPRESSION):
        delattr(node, _IS_TYPING_EXPRESSION)


def assign_as_declaration(
    decl_type: str,
    assign: tuple[ast.expr, ast.expr | None, ast.expr | None],
    is_multi_target: bool,
    lineno: int,
    col_offset: int,
    end_lineno: int,
    end_col_offset: int,
) -> Union[ast.Assign, ast.AnnAssign]:
    [target, annotation, value] = assign

    if annotation is not None:
        result = ast.AnnAssign(
            target=cast(ast.Name, target),
            value=value,
            annotation=annotation,
            simple=1,
            lineno=lineno,
            col_offset=col_offset,
            end_lineno=end_lineno,
            end_col_offset=end_col_offset,
        )
    else:
        if value is None:
            # TODO: message
            raise SyntaxError("Declaration must have either annotation or value")
        result = ast.Assign(
            targets=[target],
            value=value,
            lineno=lineno,
            col_offset=col_offset,
            end_lineno=end_lineno,
            end_col_offset=end_col_offset,
        )
    _set_is_let_var(result, decl_type)
    if is_multi_target:
        set_is_multi_decl(result, True)
    return result


def get_target_of_declaration(assign: Union[ast.Assign, ast.AnnAssign]) -> ast.expr:
    if isinstance(assign, ast.Assign):
        return assign.targets[0]
    else:
        return assign.target


def _get_tuple_type_elements(type_node: ast.expr) -> list[ast.expr] | None:
    if isinstance(type_node, ast.Tuple):
        return type_node.elts
    elif (
        isinstance(type_node, ast.Subscript)
        and isinstance(type_node.value, ast.Name)
        and type_node.value.id == "tuple"
        and isinstance(type_node.slice, ast.Tuple)
    ):
        return type_node.slice.elts
    return None


def _get_list_type_elements(type_node: ast.expr) -> ast.expr | None:
    if isinstance(type_node, ast.List):
        return type_node.elts[0] if len(type_node.elts) == 1 else None
    elif isinstance(type_node, ast.Subscript):
        debug_verbose_print(
            f"_get_list_type_elements: {type_node} value: {type_node.value} id: {type_node.value.id if isinstance(type_node.value, ast.Name) else 'N/A'} slice: {type_node.slice}"
        )
        if (
            isinstance(type_node.value, ast.Name)
            and type_node.value.id == "list"
            and isinstance(type_node.slice, ast.Name)
        ):
            return type_node.slice
    return None


def _get_list_type(type_node: ast.expr, pos: PosAttributes) -> ast.expr:
    return ast.Subscript(
        value=ast.Name(id="list", **pos),
        slice=type_node,
        ctx=ast.Load(),
        **pos,
    )


def get_annotations_of_declaration_target(
    target: ast.expr,
    type_annotation: ast.expr | None,
) -> list[tuple[ast.Name, ast.expr | None]]:
    if isinstance(target, ast.Name):
        debug_verbose_print(
            f"get_annotations_of_declaration_target ast.Name: {target}, {type_annotation}"
        )
        return [(target, type_annotation)]
    elif isinstance(target, ast.Tuple):
        debug_verbose_print(
            f"get_annotations_of_declaration_target ast.Tuple: {target}, {type_annotation}"
        )
        type_elts = (
            _get_tuple_type_elements(type_annotation) if type_annotation else None
        )
        if type_elts is None or len(type_elts) != len(target.elts):
            type_elts = type_elts if type_elts is not None else []
            # return []
            type_elts = type_elts + [None] * (len(target.elts) - len(type_elts))
        names: list[tuple[ast.Name, ast.expr | None]] = []
        for elt, ty_elt in zip(target.elts, type_elts):
            if isinstance(elt, ast.Name):
                names.append((elt, ty_elt))
            else:
                names.extend(get_annotations_of_declaration_target(elt, ty_elt))
        return names
    elif isinstance(target, ast.List):
        debug_verbose_print(
            f"get_annotations_of_declaration_target ast.List: {target}, {type_annotation}"
        )
        type_elt = _get_list_type_elements(type_annotation) if type_annotation else None
        names: list[tuple[ast.Name, ast.expr | None]] = []
        for elt in target.elts:
            if isinstance(elt, ast.Name):
                names.append((elt, type_elt))
            else:
                names.extend(get_annotations_of_declaration_target(elt, type_elt))
        return names
    elif isinstance(target, ast.Starred):
        debug_verbose_print(
            f"get_annotations_of_declaration_target ast.Starred: {target}, {type_annotation}"
        )
        return get_annotations_of_declaration_target(
            target.value,
            _get_list_type(type_annotation, get_pos_attributes(target))
            if type_annotation
            else None,
        )
    else:
        # TODO: message
        raise SyntaxError("Invalid target syntax for declaration")


_INLINE_WITH = "_typh_inline_with"


def is_inline_with(node: Union[ast.With, ast.AsyncWith]) -> bool:
    return getattr(node, _INLINE_WITH, False)


def set_inline_with(
    node: Union[ast.With, ast.AsyncWith], is_inline: bool = True
) -> Union[ast.With, ast.AsyncWith]:
    setattr(node, _INLINE_WITH, is_inline)
    return node


def clear_inline_with(node: Union[ast.With, ast.AsyncWith]) -> None:
    if hasattr(node, _INLINE_WITH):
        delattr(node, _INLINE_WITH)


def make_with_stmt(
    is_async: bool,
    items: list[ast.withitem],
    body: list[ast.stmt],
    is_inline: bool,
    **kwargs: Unpack[PosAttributes],
) -> Union[ast.With, ast.AsyncWith]:
    result: Union[ast.With, ast.AsyncWith]
    if is_async:
        result = ast.AsyncWith(items=items, body=body, **kwargs)
    else:
        result = ast.With(items=items, body=body, **kwargs)
    if is_inline:
        set_inline_with(result, True)
    return result


def declaration_as_withitem(assign: Union[ast.Assign, ast.AnnAssign]) -> ast.withitem:
    if isinstance(assign, ast.Assign):
        # TODO when assignment target has several target?
        item = ast.withitem(context_expr=assign.value, optional_vars=assign.targets[0])
        copy_is_let_var(assign, item)
        return item
    else:
        if not assign.value:
            raise (SyntaxError)  # TODO: what message?
        item = ast.withitem(context_expr=assign.value, optional_vars=assign.target)
        set_type_annotation(item, assign.annotation)
        copy_is_let_var(assign, item)
        return item


def _make_with_let_pattern(
    parser: Parser,
    is_async: bool,
    decl_type: str,
    pattern_subjects: list[tuple[ast.pattern, ast.expr]],
    body: list[ast.stmt],
    **kwargs: Unpack[PosAttributes],
) -> tuple[ast.stmt, list[ast.withitem]]:
    items: list[ast.withitem] = []
    pattern_vars: list[tuple[ast.pattern, ast.expr]] = []
    for pattern, subject in pattern_subjects:
        var, var_id = parser.make_anonymous_name(
            ast.Store(), **get_pos_attributes(pattern)
        )
        item = ast.withitem(context_expr=subject, optional_vars=var)
        _set_is_let_var(item, decl_type)
        items.append(item)
        pattern_vars.append((pattern, copy_anonymous_name(var, ast.Load())))
    let_pattern_stmt = make_if_let(
        decl_type,
        pattern_subjects=pattern_vars,
        cond=None,
        body=body,
        orelse=None,
        is_let_else=True,
        **kwargs,
    )
    return let_pattern_stmt, items


def make_with_let_pattern(
    parser: Parser,
    is_async: bool,
    decl_type: str,
    pattern_subjects: list[tuple[ast.pattern, ast.expr]],
    body: list[ast.stmt],
    **kwargs: Unpack[PosAttributes],
) -> ast.With | ast.AsyncWith:
    let_pattern_stmt, items = _make_with_let_pattern(
        parser,
        is_async,
        decl_type,
        pattern_subjects,
        body,
        **kwargs,
    )
    return make_with_stmt(
        is_async=is_async,
        items=items,
        body=[let_pattern_stmt],
        is_inline=False,
        **kwargs,
    )


def make_inline_with_let_pattern(
    parser: Parser,
    is_async: bool,
    decl_type: str,
    pattern_subjects: list[tuple[ast.pattern, ast.expr]],
    **kwargs: Unpack[PosAttributes],
) -> list[ast.stmt]:
    """
    with <expr1> as <temp_name1>, ...: # inline with_let_pattern
    if True: # Sequentially expanded. Captured later.
        match <temp_name1>:
            case <pattern1>:
                match <temp_name2>:
                    case <pattern2>:
                        ...
                            match <temp_nameN>:
                                case <patternN> if <cond>:
                                    <body>
                                case _:
                                    pass
                        ...
                    case _:
                        pass
            case _:
                pass
    """
    let_pattern_stmt, items = _make_with_let_pattern(
        parser,
        is_async,
        decl_type,
        pattern_subjects,
        body=[],
        **kwargs,
    )
    inline_with = make_with_stmt(
        is_async=is_async,
        items=items,
        body=[],
        is_inline=True,
        **kwargs,
    )
    # inline_with will capture the let pattern stmt (and the following stmts) in its body later.
    return [inline_with, let_pattern_stmt]


# Use Name as a function literal. Replaced to name of FunctionDef.
type FunctionLiteral = ast.Name

_FUNC_DEF = "_typh_func_def"
_IS_FUNCTION_LITERAL = "_typh_is_function_literal"


def get_function_literal_def(name: FunctionLiteral) -> ast.FunctionDef:
    return getattr(name, _FUNC_DEF)


def is_function_literal(name: ast.Name) -> bool:
    return getattr(name, _FUNC_DEF, None) is not None


def set_function_literal_def(
    name: FunctionLiteral, func_def: ast.FunctionDef | ast.AsyncFunctionDef
):
    setattr(name, _FUNC_DEF, func_def)
    setattr(func_def, _IS_FUNCTION_LITERAL, True)
    set_is_internal_name(name)


def clear_function_literal_def(name: FunctionLiteral):
    if hasattr(name, _FUNC_DEF):
        delattr(name, _FUNC_DEF)


def is_function_literal_def(func_def: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return getattr(func_def, _IS_FUNCTION_LITERAL, False)


def is_arguments_inlineable(args: ast.arguments) -> bool:
    return all(arg.annotation is None for arg in args.args)


def make_function_literal(
    args: ast.arguments,
    returns: ast.expr,
    body: Union[list[ast.stmt], ast.expr],
    **kwargs: Unpack[PosAttributes],
) -> ast.Lambda | FunctionLiteral:
    func_id = "__function_literal"  # TODO: Get unique name?
    body_stmts: list[ast.stmt]
    if isinstance(body, list):
        body_stmts = body
    else:
        if is_inline_expr(body) and is_arguments_inlineable(args):
            # Make lambda expression if possible.
            return ast.Lambda(args=args, body=body, **kwargs)
        body_stmts = [
            ast.Return(
                body,
                lineno=body.lineno,
                col_offset=body.col_offset,
                end_lineno=body.end_lineno,
                end_col_offset=body.end_col_offset,
            )
        ]
    func_def = ast.FunctionDef(
        func_id, args, body_stmts, [], returns, type_comment=None, **kwargs
    )
    name = ast.Name(func_id, **kwargs)
    set_function_literal_def(name, func_def)
    return name


# Use Name as a function type. Replaced to name of Protocol.
type FunctionType = ast.Name

_ARG_TYPES = "_typh_arg_types"
_STAR_ARG = "_typh_star_arg"
_STAR_KWDS = "_typh_star_kwds"
_RETURNS = "_typh_returns"


def is_function_type(node: ast.Name) -> bool:
    return getattr(node, _ARG_TYPES, None) is not None


def get_args_of_function_type(node: FunctionType) -> list[ast.arg]:
    return getattr(node, _ARG_TYPES)


def set_args_of_function_type(node: FunctionType, args: list[ast.arg]):
    setattr(node, _ARG_TYPES, args)


def get_star_arg_of_function_type(node: FunctionType) -> ast.arg | None:
    return getattr(node, _STAR_ARG, None)


def set_star_arg_of_function_type(node: FunctionType, star_arg: ast.arg):
    setattr(node, _STAR_ARG, star_arg)


def get_star_kwds_of_function_type(node: FunctionType) -> ast.arg | None:
    return getattr(node, _STAR_KWDS, None)


def set_star_kwds_of_function_type(node: FunctionType, star_kwds: ast.arg):
    setattr(node, _STAR_KWDS, star_kwds)


def get_return_of_function_type(node: FunctionType) -> ast.expr | None:
    return getattr(node, _RETURNS, None)


def set_return_of_function_type(node: FunctionType, returns: ast.expr):
    setattr(node, _RETURNS, returns)


fieldsOfFunctionType = [_ARG_TYPES, _STAR_ARG, _STAR_KWDS, _RETURNS]


def clear_function_type(node: FunctionType):
    for field in fieldsOfFunctionType:
        if hasattr(node, field):
            delattr(node, field)


def _check_arrow_type_args(
    args: list[ast.arg],
    star_etc: Tuple[ast.arg, ast.arg] | None,
):
    # TODO* args check (args without name first, with name later, only one star arg, etc)
    kwarg_found = False
    for arg in args:
        if arg.arg.startswith("**"):
            # TODO: Source place
            raise SyntaxError("Only one keyword argument is allowed")
        elif arg.arg.startswith("*"):
            if kwarg_found:
                raise SyntaxError("Keyword argument must be last")
        if len(arg.arg) > 0:
            kwarg_found = True
        else:
            if kwarg_found:
                raise SyntaxError("Non-keyword argument must be first")


def make_arrow_type(
    args: list[ast.arg],
    star_etc: Tuple[ast.arg, ast.arg] | None,
    returns: ast.expr,
    **kwargs: Unpack[PosAttributes],
) -> FunctionType:
    # TODO: temporal name
    result = ast.Name("__arrow_type", **kwargs)
    set_args_of_function_type(result, args)
    set_return_of_function_type(result, returns)
    _check_arrow_type_args(args, star_etc)
    if star_etc:
        set_star_arg_of_function_type(result, star_etc[0])
        set_star_kwds_of_function_type(result, star_etc[1])
    return result


def make_arrow_type_single_chain(
    arg: ast.expr,
    star_etc: Tuple[ast.arg, ast.arg] | None,
    returns: list[ast.expr],
    **kwargs: Unpack[PosAttributes],
) -> FunctionType:
    # TODO: temporal name
    result = ast.Name("__arrow_type", **kwargs)
    if len(returns) == 1:
        args = [ast.arg(arg="", annotation=arg, **kwargs)]
        set_args_of_function_type(result, args)
        set_return_of_function_type(result, returns[0])
        _check_arrow_type_args(args, star_etc)
        if star_etc:
            set_star_arg_of_function_type(result, star_etc[0])
            set_star_kwds_of_function_type(result, star_etc[1])
    elif len(returns) == 0:
        raise SyntaxError("Arrow type must have one or more return types")
    else:
        return_type = make_arrow_type_single_chain(
            arg=returns[0],
            star_etc=None,
            returns=returns[1:],
            **kwargs,
        )
        args = [ast.arg(arg="", annotation=arg, **kwargs)]
        set_args_of_function_type(result, args)
        set_return_of_function_type(result, return_type)
        _check_arrow_type_args(args, star_etc)
        if star_etc:
            set_star_arg_of_function_type(result, star_etc[0])
            set_star_kwds_of_function_type(result, star_etc[1])
    return result


def make_for_stmt(
    decl_type: str,
    target: ast.expr,
    type_annotation: ast.expr | None,
    iter: ast.expr,
    body: list[ast.stmt],
    orelse: list[ast.stmt] | None,
    type_comment: str | None,
    is_async: bool,
    **kwargs: Unpack[PosAttributes],
) -> Union[ast.For, ast.AsyncFor]:
    if is_async:
        result = ast.AsyncFor(
            target=target,
            iter=iter,
            body=body,
            orelse=orelse or [],
            type_comment=type_comment,
            **kwargs,
        )
        _set_is_let_var(result, decl_type)
        set_type_annotation(result, type_annotation)
        return result
    else:
        result = ast.For(
            target=target,
            iter=iter,
            body=body,
            orelse=orelse or [],
            type_comment=type_comment,
            **kwargs,
        )
        _set_is_let_var(result, decl_type)
        set_type_annotation(result, type_annotation)
        return result


def make_for_let_pattern(
    parser: Parser,
    decl_type: str,
    pattern: ast.pattern,
    iter: ast.expr,
    body: list[ast.stmt],
    orelse: list[ast.stmt] | None,
    type_comment: str | None,
    is_async: bool,
    **kwargs: Unpack[PosAttributes],
):
    temp_name, anon_id = parser.make_anonymous_name(
        ast.Load(), **get_pos_attributes(pattern)
    )
    let_stmt = make_if_let(
        decl_type,
        pattern_subjects=[(pattern, temp_name)],
        cond=None,
        body=body,
        orelse=None,
        is_let_else=True,
        **kwargs,
    )
    temp_name_store = copy_anonymous_name(temp_name, ast.Store())
    return make_for_stmt(
        decl_type=decl_type,
        target=temp_name_store,
        type_annotation=None,
        iter=iter,
        body=[let_stmt],
        orelse=orelse,
        type_comment=type_comment,
        is_async=is_async,
        **kwargs,
    )


def _make_none_check(name: str, pos: PosAttributes) -> ast.Compare:
    return ast.Compare(
        left=ast.Name(id=name, ctx=ast.Load(), **pos),
        ops=[ast.IsNot()],
        comparators=[ast.Constant(value=None, **pos)],
        **pos,
    )


_LET_PATTERN_BODY = "_typh_multiple_let_pattern_body"
_IS_LET_ELSE = "_typh_is_let_else"


@dataclass
class LetPatternInfo:
    body: list[ast.stmt]
    is_all_pattern_irrefutable: bool


def get_let_pattern_body(node: ast.While | ast.If) -> LetPatternInfo | None:
    return getattr(node, _LET_PATTERN_BODY, None)


def set_let_pattern_body(
    node: ast.While | ast.If, body: LetPatternInfo
) -> ast.While | ast.If:
    setattr(node, _LET_PATTERN_BODY, body)
    return node


def clear_let_pattern_body(node: ast.While | ast.If) -> None:
    if hasattr(node, _LET_PATTERN_BODY):
        delattr(node, _LET_PATTERN_BODY)


type LetElseAnnotatedNode = ast.If | ast.Match | ast.match_case


def is_let_else(node: LetElseAnnotatedNode) -> bool:
    return getattr(node, _IS_LET_ELSE, False)


def set_is_let_else[T: LetElseAnnotatedNode](node: T, is_let_else: bool) -> T:
    setattr(node, _IS_LET_ELSE, is_let_else)
    return node


def clear_is_let_else(node: LetElseAnnotatedNode) -> None:
    if hasattr(node, _IS_LET_ELSE):
        delattr(node, _IS_LET_ELSE)


def _let_pattern_check(
    parser: Parser,
    decl_type_str: str,
    pattern_subjects: list[tuple[ast.pattern, ast.expr]],
    start_pos: tuple[int, int],
    end_pos: tuple[int, int],
) -> bool:
    if decl_type_str != "let":
        error = parser.build_syntax_error(
            "declaration pattern must be 'let' declaration", start_pos, end_pos
        )
    if len(pattern_subjects) == 0:
        parser.build_syntax_error(
            "declaration pattern must have at least one pattern", start_pos, end_pos
        )
    return True


def make_if_let(
    decl_type: TokenInfo | str,
    pattern_subjects: list[tuple[ast.pattern, ast.expr]],
    cond: ast.expr | None,
    body: list[ast.stmt],
    orelse: list[ast.stmt] | None,
    is_let_else: bool,
    **kwargs: Unpack[PosAttributes],
) -> ast.stmt:
    decl_type_str = decl_type.string if isinstance(decl_type, TokenInfo) else decl_type
    return set_is_let_else(
        _make_if_let_multiple(
            decl_type_str, pattern_subjects, cond, body, orelse, is_let_else, **kwargs
        ),
        is_let_else,
    )


def _make_if_let_single_case(
    decl_type: str,
    pattern: ast.pattern,
    cond: ast.expr | None,
    body: list[ast.stmt],
    make_none_check: bool,
    is_let_else: bool,
) -> ast.match_case:
    _set_is_let_var(pattern, decl_type)
    if (
        isinstance(pattern, ast.MatchAs)
        and pattern.pattern is None
        and pattern.name is not None
        and cond is None
        and make_none_check
    ):
        # Variable capture pattern, e.g. `let x = ...` without condition.
        # In this case, the condition is None check.
        return set_is_let_else(
            make_match_case(
                pattern=pattern,
                guard=_make_none_check(pattern.name, get_pos_attributes(pattern)),
                body=body,
                **get_pos_attributes(pattern),
            ),
            is_let_else,
        )
    else:
        return set_is_let_else(
            make_match_case(
                pattern=pattern, guard=cond, body=body, **get_pos_attributes(pattern)
            ),
            is_let_else,
        )


def _make_nested_match_for_multiple_let(
    decl_type: str,
    pattern_subjects: list[tuple[ast.pattern, ast.expr]],
    cond: ast.expr | None,
    body: list[ast.stmt],
    type_error_on_failure: bool,
    is_let_else: bool,
    else_pos: PosAttributes | None,
    **kwargs: Unpack[PosAttributes],
) -> list[ast.stmt]:
    # Build nested match statements from inside out.
    for pattern, subject in reversed(pattern_subjects):
        # Add a wildcard case to handle non-matching case to avoid linter error.
        default_case = ast.match_case(  # case _: pass
            pattern=ast.MatchAs(
                name=None, pattern=None, **pos_attribute_to_range(else_pos or kwargs)
            ),
            guard=None,
            body=[
                # raise TypeError in 'unreachable' case. 'cast' and so on can still cause failure even if the pattern is irrefutable after type check.
                ast.Raise(
                    ast.Name(
                        id="TypeError", ctx=ast.Load(), **get_empty_pos_attributes()
                    ),
                    None,
                    # **kwargs, # TODO: appropriate position?
                    **get_empty_pos_attributes(),
                )
                if type_error_on_failure
                else ast.Pass(**(else_pos or kwargs))
            ],
        )
        if type_error_on_failure:
            # Ignore unreachable clause error for this default case, because this is recovery for the
            # case type check can not detect a pattern mismatch (e.g. due to cast).
            set_type_ignore_node(default_case, "all")
        cases = [
            _make_if_let_single_case(
                decl_type,
                pattern,
                cond,
                body,
                make_none_check=cond is None,
                is_let_else=is_let_else,
            ),
            default_case,
        ]
        nested_match: ast.stmt = ast.Match(
            subject=subject,
            cases=cases,
            **kwargs,
        )
        body = [nested_match]
        cond = None  # Only the innermost match has the condition.
    return body


# Multiple patterns are combined into nested match statements.
def _make_if_let_multiple(
    decl_type: str,
    pattern_subjects: list[tuple[ast.pattern, ast.expr]],
    cond: ast.expr | None,
    body: list[ast.stmt],
    orelse: list[ast.stmt] | None,
    is_let_else: bool,
    **kwargs: Unpack[PosAttributes],
) -> ast.If:
    """
        if (let <pattern1> = <subject1>, <pattern2> = <subject2>, ...,
                <patternN> = <subjectN>[;<cond>]) {
            <body>
        } else {
            <orelse>
        }
    --> (temporary represented now)

        if True: # multiple_let_pattern_body set
            match <subject1>:
                case <pattern1>:
                    match <subject2>:
                        case <pattern2>:
                            ...
                                match <subjectN>:
                                    case <patternN> if <cond>:
                                        <body>
                                    case _:
                                        pass
                            ...
                        case _:
                            pass
                case _:
                    pass
        else:
            <orelse>
    """
    # Build nested match statements from inside out.
    is_all_pattern_irrefutable = all(
        is_pattern_irrefutable(pat) for pat, _ in pattern_subjects
    )
    is_all_pattern_truly_irrefutable = all(
        is_pattern_irrefutable(pat, assume_type_checked=False)
        for pat, _ in pattern_subjects
    )
    result = ast.If(
        test=ast.Constant(value=True, **kwargs),
        body=_make_nested_match_for_multiple_let(
            decl_type,
            pattern_subjects,
            cond,
            body,
            type_error_on_failure=(
                is_let_else
                and (orelse is None)
                and (not is_all_pattern_truly_irrefutable)
            ),
            is_let_else=is_let_else,
            else_pos=get_pos_attributes(orelse[0]) if orelse else None,
            **kwargs,
        ),
        orelse=orelse or [],
        **kwargs,
    )
    set_let_pattern_body(
        result,
        LetPatternInfo(
            body=body,
            is_all_pattern_irrefutable=is_all_pattern_irrefutable,
        ),
    )
    return result


def make_while_let(
    pattern_subjects: list[tuple[ast.pattern, ast.expr]],
    cond: ast.expr | None,
    body: list[ast.stmt],
    orelse: list[ast.stmt] | None,
    **kwargs: Unpack[PosAttributes],
) -> ast.While:
    return _make_while_let(pattern_subjects, cond, body, orelse, **kwargs)


def _make_while_let(
    pattern_subjects: list[tuple[ast.pattern, ast.expr]],
    cond: ast.expr | None,
    body: list[ast.stmt],
    orelse: list[ast.stmt] | None,
    **kwargs: Unpack[PosAttributes],
) -> ast.While:
    """
        while (let <pattern1> = <subject1>,
                   <pattern2> = <subject2>,
                   ...,
                   <patternN> = <subjectN>
                   [;<cond>]) {
            <body>
        } else {
            <orelse>
        }

    --> (temporary represented now)

        while True: # multiple_let_pattern_body set to <body>
            match <subject1>:
                case <pattern1>:
                    match <subject2>:
                        case <pattern2>:
                            ...
                                match <subjectN>:
                                    case <patternN> if <cond>:
                                        <body>
        else:
            <orelse>
    """

    result = ast.While(
        test=ast.Constant(value=True, **kwargs),
        body=_make_nested_match_for_multiple_let(
            "let",
            pattern_subjects,
            cond,
            body,
            False,
            False,
            else_pos=get_pos_attributes(orelse[0]) if orelse else None,
            **kwargs,
        ),
        orelse=orelse or [],
        **kwargs,
    )
    set_let_pattern_body(
        result,
        LetPatternInfo(
            body=body,
            is_all_pattern_irrefutable=all(
                is_pattern_irrefutable(pat) for pat, _ in pattern_subjects
            ),
        ),
    )
    return result


IS_STATIC = "_typh_is_static"


def set_is_static(node: ast.FunctionDef | ast.AsyncFunctionDef, is_static: bool = True):
    setattr(node, IS_STATIC, is_static)


def is_static(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return getattr(node, IS_STATIC, False)


_DEFINED_NAME = "_typh_defined_name"
DefinesName = (
    ast.FunctionDef
    | ast.AsyncFunctionDef
    | ast.ClassDef
    | ast.alias
    | ast.Attribute
    | ast.arg
)


def get_defined_name(node: DefinesName) -> ast.Name | None:
    return getattr(node, _DEFINED_NAME, None)


def set_defined_name(
    node: DefinesName,
    name: ast.Name,
):
    setattr(node, _DEFINED_NAME, name)


def maybe_copy_defined_name[T: ast.AST](
    from_node: T,
    to_node: T,
) -> T:
    if not isinstance(from_node, DefinesName) or not isinstance(to_node, DefinesName):
        return to_node
    name = get_defined_name(from_node)
    if name is not None:
        set_defined_name(to_node, name)
    return to_node


def set_defined_name_token(
    node: DefinesName, name: TokenInfo | ast.Name, ctx: ast.expr_context = ast.Store()
):
    if isinstance(name, TokenInfo):
        name = ast.Name(
            id=name.string,
            lineno=name.start[0],
            col_offset=name.start[1],
            end_lineno=name.end[0],
            end_col_offset=name.end[1],
            ctx=ctx,
        )
    setattr(node, _DEFINED_NAME, name)
    return node


def clear_defined_name(node: DefinesName):
    if hasattr(node, _DEFINED_NAME):
        delattr(node, _DEFINED_NAME)


_RETURN_TYPE_ANNOTATION_ANCHOR = "_typh_return_type_annotation_anchor"


def set_return_type_annotation_anchor(
    node: ast.FunctionDef | ast.AsyncFunctionDef, anchor: ast.Name | None
):
    setattr(node, _RETURN_TYPE_ANNOTATION_ANCHOR, anchor)


def get_return_type_annotation_anchor(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> ast.Name | None:
    return getattr(node, _RETURN_TYPE_ANNOTATION_ANCHOR, None)


def clear_return_type_annotation_anchor(node: ast.FunctionDef | ast.AsyncFunctionDef):
    if hasattr(node, _RETURN_TYPE_ANNOTATION_ANCHOR):
        delattr(node, _RETURN_TYPE_ANNOTATION_ANCHOR)


def make_function_def(
    is_async: bool,
    is_static: bool,
    name: TokenInfo | str,
    args: ast.arguments,
    returns: ast.expr | None,
    body: list[ast.stmt],
    type_comment: str | None,
    type_params: list[ast.type_param],
    close_paren_anchor: TokenInfo | None,
    **kwargs: Unpack[PosAttributes],
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    if is_async:
        result = ast.AsyncFunctionDef(
            name=name.string if isinstance(name, TokenInfo) else name,
            args=args,
            returns=returns,
            body=body,
            type_comment=type_comment,
            type_params=type_params,
            **kwargs,
        )
    else:
        result = ast.FunctionDef(
            name=name.string if isinstance(name, TokenInfo) else name,
            args=args,
            returns=returns,
            body=body,
            type_comment=type_comment,
            type_params=type_params,
            **kwargs,
        )
    set_is_static(result, is_static)
    if isinstance(name, TokenInfo):
        set_defined_name_token(result, name)
    if close_paren_anchor is not None:
        set_return_type_annotation_anchor(
            result,
            ast.Name(
                id=")",
                lineno=close_paren_anchor.start[0],
                col_offset=close_paren_anchor.start[1],
                end_lineno=close_paren_anchor.end[0],
                end_col_offset=close_paren_anchor.end[1],
                ctx=ast.Load(),
            ),
        )
    return result


def make_class_def(
    name: TokenInfo | str,
    bases: list[ast.expr],
    keywords: list[ast.keyword],
    body: list[ast.stmt],
    decorator_list: list[ast.expr],
    type_params: list[ast.type_param],
    **kwargs: Unpack[PosAttributes],
) -> ast.ClassDef:
    name_str = name.string if isinstance(name, TokenInfo) else name
    result = ast.ClassDef(
        name=name_str,
        bases=bases,
        keywords=keywords,
        body=body,
        decorator_list=decorator_list,
        type_params=type_params,
        **kwargs,
    )
    set_defined_name_token(
        result,
        name
        if isinstance(name, TokenInfo)
        else ast.Name(id=name, ctx=ast.Store(), **kwargs),
    )
    return result


def make_alias(
    name: list[TokenInfo],
    asname: TokenInfo | None,
    **kwargs: Unpack[PosAttributes],
) -> ast.alias:
    result = ast.alias(
        name=".".join(n.string for n in name),
        asname=asname.string if asname else None,
        **kwargs,
    )
    if asname is not None:
        set_defined_name_token(result, asname)
    else:
        set_defined_name_token(result, name[-1])
    return result


def make_attribute(
    value: ast.expr,
    attr: TokenInfo,
    ctx: ast.expr_context,
    **kwargs: Unpack[PosAttributes],
):
    return set_defined_name_token(
        ast.Attribute(
            value=value,
            attr=attr.string,
            ctx=ctx,
            **kwargs,
        ),
        attr,
        ctx,
    )


_IMPORT_FROM_NAMES = "_typh_import_from_names"


def get_import_from_names(node: ast.ImportFrom) -> list[ast.Name]:
    return getattr(node, _IMPORT_FROM_NAMES, [])


def set_import_from_names(
    node: ast.ImportFrom,
    names: list[ast.Name],
):
    setattr(node, _IMPORT_FROM_NAMES, names)


def clear_import_from_names(node: ast.ImportFrom):
    if hasattr(node, _IMPORT_FROM_NAMES):
        delattr(node, _IMPORT_FROM_NAMES)


# Used only the case module part exists.
def make_import_from(
    module: list[TokenInfo] | None,
    names: list[ast.alias],
    level: int,
    **kwargs: Unpack[PosAttributes],
) -> ast.ImportFrom:
    mod_name = ".".join(n.string for n in module) if module else None
    result = ast.ImportFrom(
        module=mod_name,
        names=names,
        level=level,
        **kwargs,
    )
    if module:
        import_names = [
            ast.Name(
                id=n.string,
                lineno=n.start[0],
                col_offset=n.start[1],
                end_lineno=n.end[0],
                end_col_offset=n.end[1],
                ctx=ast.Load(),
            )
            for n in module
        ]
        set_import_from_names(result, import_names)
    return result


_CONTROL_COMPREHENSION = "_typh_is_control_comprehension"
type ControlComprehension = ast.Name


def get_control_comprehension_def(
    node: ControlComprehension,
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    return getattr(node, _CONTROL_COMPREHENSION)


def is_control_comprehension(node: ControlComprehension) -> bool:
    return getattr(node, _CONTROL_COMPREHENSION, None) is not None


def set_control_comprehension_def(
    node: ControlComprehension, func_def: ast.FunctionDef | ast.AsyncFunctionDef
):
    setattr(node, _CONTROL_COMPREHENSION, func_def)
    set_is_internal_name(node)


def clear_is_control_comprehension(node: ControlComprehension) -> None:
    if hasattr(node, _CONTROL_COMPREHENSION):
        delattr(node, _CONTROL_COMPREHENSION)


# When for-if comprehensions has function literal or other control comprehension,
# it cannot be inline.
class _ExprInlineCheckVisitor(ast.NodeVisitor):
    is_inline: bool

    def __init__(self):
        self.is_inline = True

    def visit(self, node: ast.AST):
        if isinstance(node, ast.Name):
            if is_function_literal(node) or is_control_comprehension(node):
                self.is_inline = False
                return  # Stop visiting further.
        super().visit(node)


# Some expressions cannot be inline because they need control flow.
def is_inline_expr(node: ast.expr) -> bool:
    visitor = _ExprInlineCheckVisitor()
    visitor.visit(node)
    return visitor.is_inline


def _empty_args() -> ast.arguments:
    return ast.arguments(
        posonlyargs=[],
        args=[],
        kwonlyargs=[],
        kw_defaults=[],
        defaults=[],
        vararg=None,
        kwarg=None,
    )


def make_comprehension(
    decl_type: str,
    target: ast.expr,
    type_annotation: ast.expr | None,
    iter: ast.expr,
    ifs: list[ast.expr],
    is_async: int,
) -> ast.comprehension:
    clause = ast.comprehension(
        target=target,
        iter=iter,
        ifs=ifs,
        is_async=is_async,
    )
    _set_is_let_var(clause, decl_type)
    set_type_annotation(clause, type_annotation)
    return clause


def _comprehension_function(
    id: str,
    elt: ast.expr,
    generators: list[ast.comprehension],
    **kwargs: Unpack[PosAttributes],
) -> ast.FunctionDef:
    args = _empty_args()
    body_stmts: list[ast.stmt] = [
        ast.Expr(ast.Yield(value=elt, **get_pos_attributes(elt)))
    ]
    # Build nested for and if statements from inside out.
    for gen in reversed(generators):
        for if_clause in reversed(gen.ifs):
            body_stmts = [
                ast.If(
                    test=if_clause,
                    body=body_stmts,
                    orelse=[],
                    **get_pos_attributes(if_clause),
                )
            ]
        if gen.is_async:
            body_stmts = [
                copy_is_let_var(
                    gen,
                    ast.AsyncFor(
                        target=gen.target,
                        iter=gen.iter,
                        body=body_stmts,
                        orelse=[],
                        **kwargs,
                    ),
                )
            ]
        else:
            body_stmts = [
                copy_is_let_var(
                    gen,
                    ast.For(
                        target=gen.target,
                        iter=gen.iter,
                        body=body_stmts,
                        orelse=[],
                        **kwargs,
                    ),
                )
            ]
    func_def = ast.FunctionDef(
        name=id,
        args=args,
        body=body_stmts,
        decorator_list=[],
        returns=None,
        type_comment=None,
        **kwargs,
    )
    return func_def


def make_genexp(
    elt: ast.expr,
    generators: list[ast.comprehension],
    **kwargs: Unpack[PosAttributes],
) -> ast.expr:
    if is_inline_expr(elt):
        return ast.GeneratorExp(elt=elt, generators=generators, **kwargs)
    control_id = "__genexp_control"
    # Make a control comprehension to hold the generators.
    result = ast.Name(id=control_id, ctx=ast.Load(), **kwargs)
    func_def = _comprehension_function(control_id, elt, generators, **kwargs)
    set_control_comprehension_def(result, func_def)
    return result


def _ref_genexp(genexp: ast.expr, temp_name: str, is_async: int) -> ast.comprehension:
    return ast.comprehension(
        target=ast.Name(id=temp_name, ctx=ast.Store(), **get_pos_attributes(genexp)),
        iter=genexp,
        ifs=[],
        is_async=is_async,
    )


def make_listcomp(
    elt: ast.expr,
    generators: list[ast.comprehension],
    **kwargs: Unpack[PosAttributes],
) -> ast.ListComp:
    if is_inline_expr(elt):
        return ast.ListComp(elt=elt, generators=generators, **kwargs)
    comp_temp_name = "__listcomp_temp"
    return ast.ListComp(
        elt=ast.Name(id=comp_temp_name, ctx=ast.Load(), **kwargs),
        generators=[
            copy_is_let_var(
                generators[0],
                _ref_genexp(
                    make_genexp(elt, generators, **kwargs),
                    comp_temp_name,
                    generators[0].is_async,
                ),
            )
        ],
        **kwargs,
    )


def make_setcomp(
    elt: ast.expr,
    generators: list[ast.comprehension],
    **kwargs: Unpack[PosAttributes],
) -> ast.SetComp:
    if is_inline_expr(elt):
        return ast.SetComp(elt=elt, generators=generators, **kwargs)
    comp_temp_name = "__setcomp_temp"
    return ast.SetComp(
        elt=ast.Name(id=comp_temp_name, ctx=ast.Load(), **kwargs),
        generators=[
            copy_is_let_var(
                generators[0],
                _ref_genexp(
                    make_genexp(elt, generators, **kwargs),
                    comp_temp_name,
                    generators[0].is_async,
                ),
            )
        ],
        **kwargs,
    )


def make_dictcomp(
    key: ast.expr,
    value: ast.expr,
    generators: list[ast.comprehension],
    **kwargs: Unpack[PosAttributes],
) -> ast.DictComp:
    if is_inline_expr(key) and is_inline_expr(value):
        return ast.DictComp(key=key, value=value, generators=generators, **kwargs)
    comp_temp_name_key = "__dictcomp_temp_key"
    comp_temp_name_val = "__dictcomp_temp_val"
    return ast.DictComp(
        key=ast.Name(id=comp_temp_name_key, ctx=ast.Load(), **kwargs),
        value=ast.Name(id=comp_temp_name_val, ctx=ast.Load(), **kwargs),
        generators=[
            copy_is_let_var(
                generators[0],
                ast.comprehension(
                    target=ast.Tuple(
                        elts=[
                            ast.Name(id=comp_temp_name_key, ctx=ast.Store(), **kwargs),
                            ast.Name(id=comp_temp_name_val, ctx=ast.Store(), **kwargs),
                        ],
                        ctx=ast.Store(),
                        **get_pos_attributes(key),
                    ),
                    iter=make_genexp(
                        ast.Tuple(elts=[key, value], ctx=ast.Load(), **kwargs),
                        generators,
                        **kwargs,
                    ),
                    ifs=[],
                    is_async=generators[0].is_async,
                ),
            )
        ],
        **kwargs,
    )


def make_with_comp(
    is_async: bool,
    items: list[ast.withitem],
    body: ast.expr,
    **kwargs: Unpack[PosAttributes],
) -> ast.expr:
    control_id = "__with_control"
    func_def = make_function_def(
        is_async=is_async,
        is_static=False,
        name=control_id,
        args=_empty_args(),
        body=[
            ast.With(
                items=items,
                body=[ast.Return(value=body, **get_pos_attributes(body))],
                **kwargs,
            ),
        ],
        returns=None,
        type_comment=None,
        type_params=[],
        close_paren_anchor=None,
        **get_pos_attributes(body),
    )
    result = ast.Name(id=control_id, ctx=ast.Load(), **kwargs)
    set_control_comprehension_def(result, func_def)
    return result


def make_try_comp(
    body: ast.expr,
    handlers: list[ast.Name],
    **kwargs: Unpack[PosAttributes],
):
    control_id = "__try_comp"
    handler_blocks = (
        [
            ast.ExceptHandler(
                type=get_try_comp_except(handler)[0],
                name=handler.id if handler.id else None,
                body=[
                    ast.Return(
                        value=get_try_comp_except(handler)[1],
                        **get_pos_attributes(handler),
                    )
                ],
                **get_pos_attributes(handler),
            )
            for handler in handlers
        ]
        if handlers
        else [
            ast.ExceptHandler(
                type=None,
                name=None,
                body=[
                    ast.Return(
                        value=ast.Constant(value=None, **get_pos_attributes(body)),
                        **get_pos_attributes(body),
                    )
                ],
                **get_pos_attributes(body),
            )
        ]
    )
    func_def = make_function_def(
        is_async=False,
        is_static=False,
        name=control_id,
        args=_empty_args(),
        body=[
            ast.Try(
                body=[ast.Return(value=body, **get_pos_attributes(body))],
                handlers=handler_blocks,
                orelse=[],
                finalbody=[],
                **get_pos_attributes(body),
            )
        ],
        returns=None,
        type_comment=None,
        type_params=[],
        close_paren_anchor=None,
        **get_pos_attributes(body),
    )
    result = ast.Name(id=control_id, ctx=ast.Load(), **kwargs)
    set_control_comprehension_def(result, func_def)
    return result


_EXCEPT_COMP = "_typh_is_try_comp_except"


def set_try_comp_except(node: ast.Name, type_body: tuple[ast.expr | None, ast.expr]):
    setattr(node, _EXCEPT_COMP, type_body)


def get_try_comp_except(node: ast.Name) -> tuple[ast.expr | None, ast.expr]:
    return getattr(node, _EXCEPT_COMP)


def make_try_comp_except(
    name: str | None,
    ex_type: ast.expr | None,
    body: ast.expr,
    **kwargs: Unpack[PosAttributes],
) -> ast.Name:
    result = ast.Name(id=name or "", ctx=ast.Load(), **kwargs)
    set_try_comp_except(result, (ex_type, body))
    return result


_CASE_COMP = "_typh_is_case_comp_case"


def set_case_comp_case(
    node: ast.Name, pattern: ast.pattern, guard: ast.expr | None, body: ast.expr
):
    setattr(node, _CASE_COMP, (pattern, guard, body))


def get_case_comp_case(
    node: ast.Name,
) -> tuple[ast.pattern, ast.expr | None, ast.expr]:
    return getattr(node, _CASE_COMP)


def make_match_comp_case(
    pattern: ast.pattern,
    guard: ast.expr | None,
    body: ast.expr,
    **kwargs: Unpack[PosAttributes],
) -> ast.Name:
    result = ast.Name(id="", ctx=ast.Load(), **kwargs)
    set_case_comp_case(result, pattern, guard, body)
    return result


def make_match_comp(
    subject: ast.expr,
    cases: list[ast.Name],
    **kwargs: Unpack[PosAttributes],
) -> ast.expr:
    control_id = "__match_comp"
    func_def = make_function_def(
        is_async=False,
        is_static=False,
        name=control_id,
        args=_empty_args(),
        body=[
            ast.Match(
                subject=subject,
                cases=[
                    make_match_case(
                        pattern=get_case_comp_case(case)[0],
                        guard=get_case_comp_case(case)[1],
                        body=[
                            ast.Return(
                                value=get_case_comp_case(case)[2],
                                **get_pos_attributes(case),
                            )
                        ],
                        **get_pos_attributes(case),
                    )
                    for case in cases
                ],
                **kwargs,
            ),
            ast.Return(
                value=ast.Constant(value=None, **get_pos_attributes(subject)),
                **get_pos_attributes(subject),
            ),
        ],
        returns=None,
        type_comment=None,
        type_params=[],
        close_paren_anchor=None,
        **kwargs,
    )
    result = ast.Name(id=control_id, ctx=ast.Load(), **kwargs)
    set_control_comprehension_def(result, func_def)
    return result


def make_while_comp(
    test: ast.expr,
    body: ast.expr,
    **kwargs: Unpack[PosAttributes],
) -> ast.expr:
    control_id = "__while_comp"
    func_def = make_function_def(
        is_async=False,
        is_static=False,
        name=control_id,
        args=_empty_args(),
        body=[
            ast.While(
                test=test,
                body=[
                    ast.Expr(ast.Yield(body, **get_pos_attributes(body))),
                ],
                orelse=[],
                **kwargs,
            ),
        ],
        returns=None,
        type_comment=None,
        type_params=[],
        close_paren_anchor=None,
        **kwargs,
    )
    result = ast.Name(id=control_id, ctx=ast.Load(), **kwargs)
    set_control_comprehension_def(result, func_def)
    return result


def make_if_let_comp(
    pattern_subjects: list[tuple[ast.pattern, ast.expr]],
    cond: ast.expr | None,
    body: ast.expr,
    orelse: ast.expr | None,
    **kwargs: Unpack[PosAttributes],
) -> ast.expr:
    control_id = "__if_let_comp"
    func_def = make_function_def(
        is_async=False,
        is_static=False,
        name=control_id,
        args=_empty_args(),
        body=[
            make_if_let(
                "let",
                pattern_subjects,
                cond,
                [ast.Return(value=body, **get_pos_attributes(body))],
                [ast.Return(value=orelse, **get_pos_attributes(orelse))]
                if orelse
                else [],
                is_let_else=False,
                **kwargs,
            )
        ],
        returns=None,
        type_comment=None,
        type_params=[],
        close_paren_anchor=None,
        **kwargs,
    )
    result = ast.Name(id=control_id, ctx=ast.Load(), **kwargs)
    set_control_comprehension_def(result, func_def)
    return result


def make_while_let_comp(
    pattern_subjects: list[tuple[ast.pattern, ast.expr]],
    cond: ast.expr | None,
    body: ast.expr,
    **kwargs: Unpack[PosAttributes],
) -> ast.expr:
    control_id = "__while_let_comp"
    func_def = make_function_def(
        is_async=False,
        is_static=False,
        name=control_id,
        args=_empty_args(),
        body=[
            make_while_let(
                pattern_subjects,
                cond,
                [ast.Expr(ast.Yield(value=body, **get_pos_attributes(body)))],
                [],
                **kwargs,
            )
        ],
        returns=None,
        type_comment=None,
        type_params=[],
        close_paren_anchor=None,
        **kwargs,
    )
    result = ast.Name(id=control_id, ctx=ast.Load(), **kwargs)
    set_control_comprehension_def(result, func_def)
    return result


def make_let_comp(
    assignments: list[tuple[ast.expr, ast.expr | None, ast.expr | None]],
    body: ast.expr,
    **kwargs: Unpack[PosAttributes],
):
    control_id = "__let_comp"
    stmts: list[ast.stmt] = [
        cast(
            ast.stmt,
            assign_as_declaration(
                "let", a, len(assignments) > 0, **pos_attribute_to_range(kwargs)
            ),
        )
        for a in assignments
    ]
    stmts.append(
        ast.Return(
            value=body,
            **get_pos_attributes(body),
        )
    )
    func_def = make_function_def(
        is_async=False,
        is_static=False,
        name=control_id,
        args=_empty_args(),
        body=stmts,
        returns=None,
        type_comment=None,
        type_params=[],
        close_paren_anchor=None,
        **kwargs,
    )
    result = ast.Name(id=control_id, ctx=ast.Load(), **kwargs)
    set_control_comprehension_def(result, func_def)
    return result


IS_OPTIONAL = "_typh_is_optional"
IS_OPTIONAL_PIPE = "_typh_is_optional_pipe"


def maybe_optional(node: ast.expr, operator_string: str) -> ast.expr:
    if operator_string.startswith("?"):
        setattr(node, IS_OPTIONAL, True)
    return node


def set_is_optional(node: ast.expr, is_optional: bool = True) -> ast.expr:
    setattr(node, IS_OPTIONAL, is_optional)
    return node


def is_optional(node: ast.expr) -> bool:
    return getattr(node, IS_OPTIONAL, False)


def clear_is_optional(node: ast.expr) -> None:
    if hasattr(node, IS_OPTIONAL):
        delattr(node, IS_OPTIONAL)


def set_is_optional_pipe(node: ast.expr, is_optional: bool = True) -> ast.expr:
    setattr(node, IS_OPTIONAL_PIPE, is_optional)
    return node


def is_optional_pipe(node: ast.expr) -> bool:
    return getattr(node, IS_OPTIONAL_PIPE, False)


def clear_is_optional_pipe(node: ast.expr) -> None:
    if hasattr(node, IS_OPTIONAL_PIPE):
        delattr(node, IS_OPTIONAL_PIPE)


IS_COALESCING = "_typh_is_coalescing"


def set_is_coalescing(node: ast.Tuple, is_coalescing: bool = True) -> ast.expr:
    ast.Tuple()
    setattr(node, IS_COALESCING, is_coalescing)
    return node


def is_coalescing(node: ast.Tuple) -> bool:
    return getattr(node, IS_COALESCING, False)


UnaryPostfix = ast.Tuple  # Using Tuple node for postfix operators.
OPTIONAL_QUESTION = "_typh_op_optional_question"
FORCE_UNWRAP = "_typh_op_force_unwrap"


def get_optional_question_node(
    node: ast.expr,
    **kwargs: Unpack[PosAttributes],
) -> UnaryPostfix:
    result = ast.Tuple(elts=[node], ctx=ast.Load(), **kwargs)
    setattr(result, OPTIONAL_QUESTION, True)
    return result


def is_optional_question(node: ast.expr) -> bool:
    return getattr(node, OPTIONAL_QUESTION, False)


def get_force_unwrap_node(
    node: ast.expr,
    **kwargs: Unpack[PosAttributes],
) -> UnaryPostfix:
    result = ast.Tuple(elts=[node], ctx=ast.Load(), **kwargs)
    setattr(result, FORCE_UNWRAP, True)
    return result


def is_force_unwrap(node: ast.expr) -> bool:
    return getattr(node, FORCE_UNWRAP, False)


def make_pipe_call(
    left: ast.expr, rights: list[tuple[bool, ast.expr]], **kwargs: Unpack[PosAttributes]
) -> ast.expr:
    result: ast.expr = left
    for is_optional, right in rights:
        result = ast.Call(
            func=right,
            args=[result],
            keywords=[],
            **kwargs,
        )
        if is_optional:
            set_is_optional_pipe(result, True)
    return result


_IS_PLACEHOLDER = "_typh_is_placeholder"


def set_is_placeholder(node: ast.Name, is_placeholder: bool = True) -> ast.expr:
    setattr(node, _IS_PLACEHOLDER, is_placeholder)
    return node


def is_placeholder(node: ast.Name) -> bool:
    return getattr(node, _IS_PLACEHOLDER, False)


def clear_is_placeholder(node: ast.Name) -> None:
    if hasattr(node, _IS_PLACEHOLDER):
        delattr(node, _IS_PLACEHOLDER)


_RECORD_LITERAL_FIELDS = "_typh_is_record_literal_fields"
_RECORD_TYPE = "_typh_is_record_literal_type"
type RecordLiteral = ast.Name
type RecordType = ast.Name


def set_record_literal_fields(
    node: RecordLiteral, fields: list[tuple[ast.Name, ast.expr | None, ast.expr]]
) -> ast.expr:
    setattr(node, _RECORD_LITERAL_FIELDS, fields)
    return node


def get_record_literal_fields(
    node: RecordLiteral,
) -> list[tuple[ast.Name, ast.expr | None, ast.expr]] | None:
    return getattr(node, _RECORD_LITERAL_FIELDS, None)


def is_record_literal(node: RecordLiteral) -> bool:
    return getattr(node, _RECORD_LITERAL_FIELDS, None) is not None


def clear_record_literal_fields(node: RecordLiteral) -> None:
    if hasattr(node, _RECORD_LITERAL_FIELDS):
        delattr(node, _RECORD_LITERAL_FIELDS)


def make_record_literal(
    fields: list[tuple[ast.Name, ast.expr | None, ast.expr]],
    **kwargs: Unpack[PosAttributes],
) -> RecordLiteral:
    result = ast.Name(
        id="__record_literal",
        **kwargs,
    )
    set_record_literal_fields(result, fields)
    return result


def set_record_type_fields(
    node: RecordType, fields: list[tuple[ast.Name, ast.expr]]
) -> ast.expr:
    setattr(node, _RECORD_TYPE, fields)
    return node


def get_record_type_fields(
    node: RecordType,
) -> list[tuple[ast.Name, ast.expr]] | None:
    return getattr(node, _RECORD_TYPE, None)


def is_record_type(node: RecordType) -> bool:
    return getattr(node, _RECORD_TYPE, None) is not None


def clear_record_type(node: RecordType) -> None:
    if hasattr(node, _RECORD_TYPE):
        delattr(node, _RECORD_TYPE)


def make_record_type(
    fields: list[tuple[ast.Name, ast.expr]],
    **kwargs: Unpack[PosAttributes],
) -> RecordType:
    result = ast.Name(
        id="__record_type",
        **kwargs,
    )
    set_record_type_fields(result, fields)
    return result


_ATTRIBUTES_PATTERN = "_typh_is_attributes_pattern"
type AttributesPatternClass = ast.Name


def set_is_attributes_pattern(node: ast.Name, is_record_pattern: bool) -> ast.expr:
    setattr(node, _ATTRIBUTES_PATTERN, is_record_pattern)
    return node


def is_attributes_pattern(node: ast.Name) -> bool:
    return getattr(node, _ATTRIBUTES_PATTERN, None) is not None


def clear_is_attributes_pattern(node: ast.Name) -> None:
    if hasattr(node, _ATTRIBUTES_PATTERN):
        delattr(node, _ATTRIBUTES_PATTERN)


def make_attributes_pattern(
    keywords: list[tuple[ast.Name, ast.pattern | None]],
    **kwargs: Unpack[PosAttributes],
) -> ast.MatchClass:
    debug_verbose_print(f"Creating attributes pattern with keywords: {keywords}")
    kwd_attrs = [k.id for k, _ in keywords]
    kwd_patterns = [
        (
            p
            if p is not None
            # Only name is given, capture by member name.
            else ast.MatchAs(
                pattern=None, name=k.id, **pos_attribute_to_range(get_pos_attributes(k))
            )
        )
        for k, p in keywords
    ]
    cls_name = ast.Name(
        id="__attribute_pattern",
        **kwargs,
    )
    set_is_attributes_pattern(cls_name, True)
    result = ast.MatchClass(
        cls=cls_name,
        patterns=[],
        kwd_attrs=kwd_attrs,
        kwd_patterns=kwd_patterns,
        **pos_attribute_to_range(kwargs),
    )
    debug_verbose_print(f"Created attributes pattern: {ast.dump(result)}")
    return result


def if_comp_exp(
    test: ast.expr,
    body: ast.expr,
    orelse: ast.expr | None,
    **kwargs: Unpack[PosAttributes],
) -> ast.IfExp:
    if orelse is None:
        orelse = ast.Constant(value=None, **get_pos_attributes(test))
    return ast.IfExp(test=test, body=body, orelse=orelse, **kwargs)


def get_postfix_operator_temp_name(symbol: str) -> str:
    if symbol == "?":
        return OPTIONAL_QUESTION
    elif symbol == "!":
        return FORCE_UNWRAP
    else:
        raise ValueError(f"Unknown postfix operator symbol: {symbol}")


_GENERATED_NAME_ORIGINAL_MAP = "_typh_generated_name_original_map"


def get_generated_name_original_map(mod: ast.Module) -> dict[str, str]:
    mapping: dict[str, str] | None = getattr(mod, _GENERATED_NAME_ORIGINAL_MAP, None)
    if mapping is None:
        mapping = {}
        setattr(mod, _GENERATED_NAME_ORIGINAL_MAP, mapping)
    return mapping


def add_generated_name_original(
    mod: ast.Module,
    generated_name: str,
    original_name: str,
) -> None:
    get_generated_name_original_map(mod)[generated_name] = original_name


_IMPORTS = "_typh_imports"


def get_imports(mod: ast.Module) -> dict[tuple[str, str], ast.alias]:
    imports: dict[tuple[str, str], ast.alias] | None = getattr(mod, _IMPORTS, None)
    if imports is None:
        imports = {}
        setattr(mod, _IMPORTS, imports)
    return imports


def add_import_alias_top(mod: ast.Module, from_module: str, name: str, as_name: str):
    debug_verbose_print(f"Adding import: from {from_module} import {name} as {as_name}")
    # Check if already imported.
    imports = get_imports(mod)
    if (from_module, name) in imports and imports[
        (from_module, name)
    ].asname == as_name:
        return
    # Duplicate import is NOT a problem, but better to avoid it for speed.
    for stmt in mod.body:
        if isinstance(stmt, ast.ImportFrom):
            if stmt.module == from_module:
                for alias in stmt.names:
                    if alias.name == name and alias.asname == as_name:
                        return
        else:
            break  # Only check the top sequence of import statements.
    # Add import at the top.
    alias = ast.alias(name=name, asname=as_name, **get_empty_pos_attributes())
    imports[(from_module, name)] = alias
    import_stmt = ast.ImportFrom(
        module=from_module,
        names=[alias],
        level=0,
        **get_empty_pos_attributes(),
    )
    mod.body.insert(0, import_stmt)


_PATTERN_IS_TUPLE = "_typh_pattern_is_tuple"


def set_pattern_is_tuple(pattern: ast.pattern, is_tuple: bool = True) -> ast.pattern:
    setattr(pattern, _PATTERN_IS_TUPLE, is_tuple)
    return pattern


def is_pattern_tuple(pattern: ast.pattern) -> bool:
    return getattr(pattern, _PATTERN_IS_TUPLE, False)


def clear_pattern_is_tuple(pattern: ast.pattern) -> None:
    if hasattr(pattern, _PATTERN_IS_TUPLE):
        delattr(pattern, _PATTERN_IS_TUPLE)


def make_tuple_pattern(
    patterns: list[ast.pattern],
    **kwargs: Unpack[PosAttributes],
) -> ast.MatchSequence:
    result = ast.MatchSequence(
        patterns=patterns,
        **pos_attribute_to_range(kwargs),
    )
    set_pattern_is_tuple(result, True)
    return result


def is_pattern_irrefutable(
    pattern: ast.pattern, assume_type_checked: bool = True
) -> bool:
    if isinstance(pattern, ast.MatchAs):
        if pattern.pattern is None:  # Wildcard pattern or variable capture.
            return True
        return is_pattern_irrefutable(pattern.pattern)
    if isinstance(pattern, ast.MatchOr):
        return any(is_pattern_irrefutable(p) for p in pattern.patterns)
    if assume_type_checked:  # Irrefutable if type is correct.
        if isinstance(pattern, ast.MatchClass):
            for p in pattern.patterns:
                if not is_pattern_irrefutable(p, assume_type_checked):
                    return False
            for p in pattern.kwd_patterns:
                if not is_pattern_irrefutable(p, assume_type_checked):
                    return False
            return True
        if isinstance(pattern, ast.MatchSequence):
            # Sequence is in general refutable due to length mismatch,
            # but if we assume tuple is type-checked, we can consider it irrefutable.
            if is_pattern_tuple(pattern):
                for p in pattern.patterns:
                    if not is_pattern_irrefutable(p, assume_type_checked):
                        return False
                return True
    # Other patterns are considered refutable.
    return False


def is_case_irrefutable(case: ast.match_case) -> bool:
    if case.guard:
        return False
    return is_pattern_irrefutable(case.pattern)


def make_match_case(
    pattern: ast.pattern,
    guard: ast.expr | None,
    body: list[ast.stmt],
    **kwargs: Unpack[PosAttributes],
) -> ast.match_case:
    node = ast.match_case(pattern=pattern, guard=guard, body=body)
    # Append position attributes
    for key, value in kwargs.items():
        setattr(node, key, value)
    return node


def make_arg(
    arg: TokenInfo | None,
    annotation: ast.expr | None,
    **kwargs: Unpack[PosAttributes],
):
    """Build a function definition argument."""
    node = ast.arg(
        arg=arg.string if arg else "",
        annotation=annotation,
        **kwargs,
    )
    if arg:
        set_defined_name_token(node, arg)
    return node


def make_arguments(
    pos_only: Optional[List[Tuple[ast.arg, None]]],
    pos_only_with_default: List[Tuple[ast.arg, Any]],
    param_no_default: Optional[List[ast.arg]],
    param_default: Optional[List[Tuple[ast.arg, Any]]],
    after_star: Optional[
        Tuple[Optional[ast.arg], List[Tuple[ast.arg, Any]], Optional[ast.arg]]
    ],
    **kwargs: Unpack[PosAttributes],
) -> ast.arguments:
    """Build a function definition arguments."""
    defaults = (
        [d for _, d in pos_only_with_default if d is not None]
        if pos_only_with_default
        else []
    )
    defaults += [d for _, d in param_default if d is not None] if param_default else []

    pos_only = pos_only or pos_only_with_default

    # Because we need to combine pos only with and without default even
    # the version with no default is a tuple
    pos_only_args = [p for p, _ in pos_only]
    params = (param_no_default or []) + (
        [p for p, _ in param_default] if param_default else []
    )

    # If after_star is None, make a default tuple
    after_star = after_star or (None, [], None)

    node = ast.arguments(
        posonlyargs=pos_only_args,
        args=params,
        defaults=defaults,
        vararg=after_star[0],
        kwonlyargs=[p for p, _ in after_star[1]],
        kw_defaults=[d for _, d in after_star[1]],
        kwarg=after_star[2],
    )
    # Append position attributes
    for key, value in kwargs.items():
        setattr(node, key, value)
    return node
