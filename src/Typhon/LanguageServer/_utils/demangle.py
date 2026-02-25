import ast
import re

from Typhon.Driver.debugging import debug_verbose_print

from ...Grammar.parser import parse_type
from ...Grammar.pretty_printer import (
    has_pretty_print_type_arg_placeholders,
    apply_pretty_print_arg_placeholders,
    pretty_print_expr,
)
from ...Grammar.typhon_ast import (
    get_generated_name_original_map,
)


_MANGLED_NAME_PATTERN = re.compile(r"\b(?P<name>_typh_[A-Za-z0-9_]+)\b")

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
        return "<anonymous>"  # TODO: Temporal
    return None


def _get_demangle_mapping(module: ast.Module | None) -> dict[str, str]:
    if module is None:
        return {}
    mapping = get_generated_name_original_map(module)
    if not mapping:
        return {}
    return mapping


def _extract_type_param_suffix(text: str, index: int) -> tuple[str | None, int]:
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
) -> list[ast.expr] | None:
    try:
        # Still is python syntax.
        parsed = ast.parse(suffix, mode="eval").body
    except Exception:
        return None

    if isinstance(parsed, ast.List):
        return parsed.elts
    return None


def _pretty_print_and_demangle_type_args_suffix(
    suffix: str,
    mapping: dict[str, str],
) -> list[str]:
    inner = suffix[1:-1].strip()
    if not inner:  # Fast path for empty type args.
        return []
    if parsed_args := _parse_type_args_suffix(suffix):
        return [
            replace_mangled_names(pretty_print_expr(arg), mapping)
            for arg in parsed_args
        ]
    return [replace_mangled_names(inner, mapping)]


def pretty_print_and_demangle_type_args_suffix(
    maybe_suffix: str | None,
    module: ast.Module | None,
) -> list[str] | None:
    if maybe_suffix is None:
        return None
    mapping = _get_demangle_mapping(module)
    pretty_args = _pretty_print_and_demangle_type_args_suffix(maybe_suffix, mapping)
    return pretty_args


def replace_mangled_names(text: str, mapping: dict[str, str]) -> str:
    result: list[str] = []
    last_index = 0
    debug_verbose_print(
        f"Replacing mangled names in text: '{text}' with mapping: {mapping}"
    )
    for match in _MANGLED_NAME_PATTERN.finditer(text):
        start, end = match.span("name")
        if start < last_index:
            continue
        result.append(text[last_index:start])
        last_index = end
        name = match.group("name")
        original_name = mapping.get(name, "")
        if not original_name:
            fallback = _fallback_demangle_generated_name(name)
            original_name = fallback if fallback else name
        # Check for type params like "[int, str]" after the mangled name.
        suffix_type_param, suffix_end = _extract_type_param_suffix(text, end)
        replacement: str = original_name
        debug_verbose_print(
            f"Demangling name '{name}' with original name '{original_name}' and type args suffix '{suffix_type_param}', has placeholders: {has_pretty_print_type_arg_placeholders(original_name)}"
        )
        if suffix_type_param is not None:
            last_index = suffix_end
            pretty_args = _pretty_print_and_demangle_type_args_suffix(
                suffix_type_param, mapping
            )
            # If the original contains placeholders, replace them with the pretty-printed args.

            if has_pretty_print_type_arg_placeholders(original_name):
                replacement = apply_pretty_print_arg_placeholders(
                    original_name, pretty_args
                )
            else:
                replacement = original_name + "[" + ", ".join(pretty_args) + "]"
        result.append(replacement)
    result.append(text[last_index:])  # Save the remaining text after the last match.
    return "".join(result)


def demangle_text(text: str, module: ast.Module | None) -> str:
    return replace_mangled_names(text, _get_demangle_mapping(module))
