import ast
import re
from collections.abc import Mapping

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


def replace_mangled_names(text: str, mapping: Mapping[str, str]) -> str:
    def _replace(match: re.Match[str]) -> str:
        name = match.group(1)
        original = mapping.get(name, "")
        if original:
            return original
        fallback = _fallback_demangle_generated_name(name)
        return fallback if fallback else name

    return _MANGLED_NAME_PATTERN.sub(_replace, text)


def demangle_text(text: str, module: ast.Module | None) -> str:
    return replace_mangled_names(text, get_demangle_mapping(module))
