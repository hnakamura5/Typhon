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


class _ExprPrettyPrinter(ast._Unparser):
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
