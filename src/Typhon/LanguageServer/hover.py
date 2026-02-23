import copy
import ast
from collections.abc import Sequence

from lsprotocol import types

from ..Driver.debugging import debug_file_write_verbose
from ..SourceMap.ast_match_based_map import MatchBasedSourceMap
from ._utils.demangle import get_demangle_mapping, replace_mangled_names
from ._utils.mapping import (
    lsp_range_to_range,
    range_to_lsp_range,
    pos_to_lsp_position,
    lsp_position_to_pos,
)


type HoverContents = (
    types.MarkedString | types.MarkupContent | Sequence[types.MarkedString]
)


def _demangle_marked_string(
    marked: types.MarkedString,
    mapping: dict[str, str],
) -> types.MarkedString:
    if isinstance(marked, str):
        return replace_mangled_names(marked, mapping)
    return types.MarkedStringWithLanguage(
        language=marked.language,
        value=replace_mangled_names(marked.value, mapping),
    )


def _demangle_hover_contents(
    contents: HoverContents,
    mapping: dict[str, str],
) -> HoverContents:
    if isinstance(contents, str):
        return replace_mangled_names(contents, mapping)
    if isinstance(contents, types.MarkedStringWithLanguage):
        return _demangle_marked_string(contents, mapping)
    if isinstance(contents, types.MarkupContent):
        return types.MarkupContent(
            kind=contents.kind,
            value=replace_mangled_names(contents.value, mapping),
        )
    return [_demangle_marked_string(item, mapping) for item in contents]


def demangle_hover_names(hover: types.Hover, module: ast.Module | None) -> types.Hover:
    if module is None:
        return hover
    mapping = dict(get_demangle_mapping(module))
    demangled = copy.copy(hover)
    demangled.contents = _demangle_hover_contents(hover.contents, mapping)
    return demangled


def map_hover_position(
    position: types.Position,
    source_map: MatchBasedSourceMap | None,
) -> types.Position | None:
    if source_map is None:
        return None

    mapped_pos = source_map.origin_pos_to_unparsed_pos(
        lsp_position_to_pos(position),
        prefer_right=True,
    )
    if mapped_pos is None:
        debug_file_write_verbose(
            f"Could not map hover position {position} to translated source."
        )
        return None
    mapped_position = pos_to_lsp_position(mapped_pos)
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

    mapped_range = source_map.unparsed_range_to_origin_range(
        lsp_range_to_range(hover.range)
    )
    if mapped_range is None:
        debug_file_write_verbose(f"Could not map hover range: {hover.range}")
        return None

    mapped_hover = copy.copy(hover)
    mapped_hover.range = range_to_lsp_range(mapped_range)
    return mapped_hover
