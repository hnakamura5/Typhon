import copy
import re
import ast
from collections.abc import Sequence

from lsprotocol import types

from ..Driver.debugging import debug_file_write_verbose
from ..Grammar.typhon_ast import (
    get_generated_name_original_map,
    get_mangled_name_pattern,
)
from ..SourceMap.ast_match_based_map import MatchBasedSourceMap
from ..SourceMap.datatype import Pos, Range
from .utils import (
    lsp_range_to_range,
    point_range_from_lsp_position,
    range_to_lsp_range,
)


_MANGLED_NAME_PATTERN = get_mangled_name_pattern()
type HoverContents = (
    types.MarkedString | types.MarkupContent | Sequence[types.MarkedString]
)


def _replace_mangled_names(text: str, mapping: dict[str, str]) -> str:
    def _replace(match: re.Match[str]) -> str:
        name = match.group(1)
        original = mapping.get(name, "")
        return original if original else name

    return _MANGLED_NAME_PATTERN.sub(_replace, text)


def _demangle_marked_string(
    marked: types.MarkedString,
    mapping: dict[str, str],
) -> types.MarkedString:
    if isinstance(marked, str):
        return _replace_mangled_names(marked, mapping)
    return types.MarkedStringWithLanguage(
        language=marked.language,
        value=_replace_mangled_names(marked.value, mapping),
    )


def _demangle_hover_contents(
    contents: HoverContents,
    mapping: dict[str, str],
) -> HoverContents:
    if isinstance(contents, str):
        return _replace_mangled_names(contents, mapping)
    if isinstance(contents, types.MarkedStringWithLanguage):
        return _demangle_marked_string(contents, mapping)
    if isinstance(contents, types.MarkupContent):
        return types.MarkupContent(
            kind=contents.kind,
            value=_replace_mangled_names(contents.value, mapping),
        )
    return [_demangle_marked_string(item, mapping) for item in contents]


def demangle_hover_names(hover: types.Hover, module: ast.Module | None) -> types.Hover:
    if module is None:
        return hover
    mapping = get_generated_name_original_map(module)
    if not mapping:
        return hover
    demangled = copy.copy(hover)
    demangled.contents = _demangle_hover_contents(hover.contents, mapping)
    return demangled


def map_hover_position(
    position: types.Position,
    source_map: MatchBasedSourceMap | None,
) -> types.Position | None:
    if source_map is None:
        return None

    point = point_range_from_lsp_position(position)
    mapped = source_map.origin_range_to_unparsed(point)

    # Fallback for cursor-at-token-end cases.
    if mapped is None and position.character > 0:
        mapped = source_map.origin_range_to_unparsed(
            Range(
                start=Pos(line=position.line, column=position.character - 1),
                end=Pos(line=position.line, column=position.character),
            )
        )
    if mapped is None:
        debug_file_write_verbose(
            f"Could not map hover position {position} to translated source."
        )
        return None
    mapped_position = types.Position(
        line=mapped.start.line,
        character=mapped.start.column,
    )
    debug_file_write_verbose(
        f"Mapped hover position from {position} to {mapped_position}"
    )
    return mapped_position


def map_hover(
    hover: types.Hover,
    source_map: MatchBasedSourceMap | None,
) -> types.Hover | None:
    if source_map is None or hover.range is None:
        return None

    mapped_range = source_map.unparsed_range_to_origin(lsp_range_to_range(hover.range))
    if mapped_range is None:
        debug_file_write_verbose(f"Could not map hover range: {hover.range}")
        return None

    mapped_hover = copy.copy(hover)
    mapped_hover.range = range_to_lsp_range(mapped_range)
    return mapped_hover
