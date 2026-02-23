# type: ignore[all]
import ast
import re

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


_RECORD_TYPE_DEMANGLE_PLACEHOLDER_PREFIX = "_typh_record_type_arg_"
RECORD_TYPE_DEMANGLE_PLACEHOLDER_PATTERN = re.compile(
    rf"{_RECORD_TYPE_DEMANGLE_PLACEHOLDER_PREFIX}(\d+)_"
)


def record_type_demangle_placeholder(index: int) -> str:
    return f"{_RECORD_TYPE_DEMANGLE_PLACEHOLDER_PREFIX}{index}_"


def make_record_type_demangle_template(field_names: list[str]) -> str:
    field_parts = [
        f"{field_name}: {record_type_demangle_placeholder(i)}"
        for i, field_name in enumerate(field_names)
    ]
    return "{| " + ", ".join(field_parts) + " |}"


def make_record_literal_demangle_template(
    fields: list[tuple[str, str | None, str | None]],
    *,
    include_values: bool = False,
) -> str:
    """
    Build demangle template for record literals.

    If a field type is unknown, the type slot is represented by a placeholder
    so callers can inject inferred type arguments later.

    By default this returns a type-only shape (no `= value`) for type-hint use.
    Set `include_values=True` when value text should be retained for future
    literal-inline hint rendering.
    """
    parts: list[str] = []
    placeholder_index = 0
    for name, annotation_text, value_text in fields:
        if annotation_text is None:
            annotation_text = record_type_demangle_placeholder(placeholder_index)
            placeholder_index += 1
        if include_values and value_text is not None:
            parts.append(f"{name}: {annotation_text} = {value_text}")
        else:
            parts.append(f"{name}: {annotation_text}")
    return "{| " + ", ".join(parts) + " |}"


def apply_record_type_arg_placeholders(template: str, args: list[str]) -> str:
    def _replace_placeholder(match: re.Match[str]) -> str:
        index = int(match.group(1))
        if 0 <= index < len(args):
            return args[index]
        return match.group(0)

    return RECORD_TYPE_DEMANGLE_PLACEHOLDER_PATTERN.sub(_replace_placeholder, template)


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
