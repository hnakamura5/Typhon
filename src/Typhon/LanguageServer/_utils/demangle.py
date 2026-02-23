import ast
import re
from collections.abc import Mapping

from ...Grammar.parser import parse_type
from ...Grammar.pretty_printer import (
    RECORD_TYPE_DEMANGLE_PLACEHOLDER_PATTERN,
    apply_record_type_arg_placeholders,
    pretty_print_expr,
)
from ...Grammar.typhon_ast import (
    get_generated_name_original_map,
    get_mangled_name_pattern,
)


_MANGLED_NAME_PATTERN = get_mangled_name_pattern()
_GENERATED_NAME_ORIGINAL_SUFFIX_PATTERN = re.compile(
    r"^_typh_[a-z]{2}_[mcf]\d+_\d+_(?P<name>[A-Za-z_][A-Za-z0-9_]*)$"
)
_BUILTIN_MANGLED_NAME_PATTERN = re.compile(
    r"^_typh_bi_(?P<name>[A-Za-z_][A-Za-z0-9_]*)$"
)


def _fallback_demangle_generated_name(name: str) -> str | None:
    if match := _BUILTIN_MANGLED_NAME_PATTERN.match(name):
        return match.group("name")
    if match := _GENERATED_NAME_ORIGINAL_SUFFIX_PATTERN.match(name):
        return match.group("name")
    if name.startswith("_typh_"):
        return "anonymous"  # TODO: Temporal
    return None


def get_demangle_mapping(module: ast.Module | None) -> Mapping[str, str]:
    if module is None:
        return {}
    mapping = get_generated_name_original_map(module)
    if not mapping:
        return {}
    return mapping


def _extract_bracket_suffix(text: str, index: int) -> tuple[str | None, int]:
    if index >= len(text) or text[index] != "[":
        return None, index
    depth = 0
    for i in range(index, len(text)):
        char = text[i]
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return text[index : i + 1], i + 1
    return None, index


def _parse_type_args_suffix(
    suffix: str,
    mapping: Mapping[str, str],
) -> list[ast.expr] | None:
    inner = suffix[1:-1].strip()
    if not inner:
        return []
    demangled_inner = replace_mangled_names(inner, mapping)
    try:
        parsed = parse_type(f"tuple[{demangled_inner}]")
    except (SyntaxError, AssertionError):
        return None

    if not isinstance(parsed, ast.Subscript):
        return None
    if isinstance(parsed.slice, ast.Tuple):
        return [*parsed.slice.elts]
    return [parsed.slice]


def _pretty_print_type_arg(text: str, mapping: Mapping[str, str]) -> str:
    demangled = replace_mangled_names(text.strip(), mapping)
    try:
        parsed = ast.parse(demangled, mode="eval")
    except (SyntaxError, AssertionError):
        return demangled
    return pretty_print_expr(parsed.body)


def _pretty_print_type_args_suffix(
    suffix: str,
    mapping: Mapping[str, str],
) -> list[str]:
    inner = suffix[1:-1].strip()
    if not inner:
        return []
    parsed_args = _parse_type_args_suffix(suffix, mapping)
    if parsed_args is not None:
        return [pretty_print_expr(arg) for arg in parsed_args]
    return [_pretty_print_type_arg(inner, mapping)]


def replace_mangled_names(text: str, mapping: Mapping[str, str]) -> str:
    result: list[str] = []
    last_index = 0

    for match in _MANGLED_NAME_PATTERN.finditer(text):
        start, end = match.span(1)
        if start < last_index:
            continue

        result.append(text[last_index:start])
        name = match.group(1)

        original = mapping.get(name, "")
        base = original
        if not base:
            fallback = _fallback_demangle_generated_name(name)
            base = fallback if fallback else name

        suffix, suffix_end = _extract_bracket_suffix(text, end)
        consumed_until = end
        replacement = base

        if suffix is not None:
            consumed_until = suffix_end
            pretty_args = _pretty_print_type_args_suffix(suffix, mapping)
            if RECORD_TYPE_DEMANGLE_PLACEHOLDER_PATTERN.search(base):
                replacement = apply_record_type_arg_placeholders(base, pretty_args)
            elif base == name:
                replacement = base + "[" + ", ".join(pretty_args) + "]"

        result.append(replacement)
        last_index = consumed_until

    result.append(text[last_index:])
    return "".join(result)


def demangle_text(text: str, module: ast.Module | None) -> str:
    return replace_mangled_names(text, get_demangle_mapping(module))
