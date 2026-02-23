# type: ignore[all]
import ast

from .typhon_ast import (
    FunctionType,
    RecordLiteral,
    RecordType,
    get_args_of_function_type,
    get_record_literal_fields,
    get_record_type_fields,
    get_return_of_function_type,
    get_star_arg_of_function_type,
    get_star_kwds_of_function_type,
    is_function_type,
    is_record_literal,
    is_record_type,
)


def _print_arg(arg: ast.arg) -> str:
    annotation = arg.annotation
    if annotation is None:
        return arg.arg
    if arg.arg:
        return f"{arg.arg}: {pretty_print_expr(annotation)}"
    return pretty_print_expr(annotation)


def _print_function_type(node: FunctionType) -> str:
    args = [_print_arg(arg) for arg in get_args_of_function_type(node)]
    star_arg = get_star_arg_of_function_type(node)
    if star_arg is not None:
        args.append(f"*{_print_arg(star_arg)}")
    star_kwds = get_star_kwds_of_function_type(node)
    if star_kwds is not None:
        args.append(f"**{_print_arg(star_kwds)}")

    returns = get_return_of_function_type(node)
    returns_str = "None" if returns is None else pretty_print_expr(returns)
    return f"({', '.join(args)}) -> {returns_str}"


def _print_record_literal(node: RecordLiteral) -> str:
    fields = get_record_literal_fields(node)
    if not fields:
        return "{| |}"

    field_texts: list[str] = []
    for name, annotation, value in fields:
        annotation_text = (
            f": {pretty_print_expr(annotation)}" if annotation is not None else ""
        )
        field_texts.append(f"{name.id}{annotation_text} = {pretty_print_expr(value)}")

    return "{| " + ", ".join(field_texts) + " |}"


def _print_record_type(node: RecordType) -> str:
    fields = get_record_type_fields(node)
    if not fields:
        return "{| |}"
    field_texts = [f"{name.id}: {pretty_print_expr(typ)}" for name, typ in fields]
    return "{| " + ", ".join(field_texts) + " |}"


def _is_name_with_id(node: ast.AST, id: str) -> bool:
    return isinstance(node, ast.Name) and node.id == id


def _is_none_node(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Constant)
        and node.value is None
        or _is_name_with_id(node, "None")
    )


def _print_subscript_abbrev(node: ast.Subscript) -> str | None:
    if not (
        _is_name_with_id(node.value, "list") or _is_name_with_id(node.value, "tuple")
    ):
        return None

    if isinstance(node.slice, ast.Tuple):
        slice_text = ", ".join(pretty_print_expr(elt) for elt in node.slice.elts)
    else:
        slice_text = pretty_print_expr(node.slice)
    if _is_name_with_id(node.value, "tuple"):
        return f"({slice_text})"
    return f"[{slice_text}]"


def _print_optional_abbrev(node: ast.BinOp) -> str | None:
    if not isinstance(node.op, ast.BitOr):
        return None
    if _is_none_node(node.left):
        return f"{pretty_print_expr(node.right)}?"
    if _is_none_node(node.right):
        return f"{pretty_print_expr(node.left)}?"
    return None


class _ExprPrettyPrinter(ast._Unparser):
    def visit_Subscript(self, node: ast.Subscript) -> None:
        if abbreviated := _print_subscript_abbrev(node):
            self.write(abbreviated)
            return
        super().visit_Subscript(node)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        if abbreviated := _print_optional_abbrev(node):
            self.write(abbreviated)
            return
        super().visit_BinOp(node)

    def visit_Name(self, node: ast.Name) -> None:
        if is_function_type(node):
            self.write(_print_function_type(node))
            return
        if is_record_literal(node):
            self.write(_print_record_literal(node))
            return
        if is_record_type(node):
            self.write(_print_record_type(node))
            return
        super().visit_Name(node)


def pretty_print_expr(node: ast.expr) -> str:
    unparser = _ExprPrettyPrinter()
    return unparser.visit(node)
