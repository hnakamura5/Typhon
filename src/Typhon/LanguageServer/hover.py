import copy
import ast
from collections.abc import Sequence

from lsprotocol import types

from ..Driver.debugging import debug_file_write_verbose
from ..SourceMap.ast_match_based_map import MatchBasedSourceMap
from ._utils.demangle import demangle_text
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
    module: ast.Module | None,
) -> types.MarkedString:
    if isinstance(marked, str):
        return demangle_text(marked, module)
    return types.MarkedStringWithLanguage(
        language=marked.language,
        value=demangle_text(marked.value, module),
    )


def _demangle_hover_contents(
    contents: HoverContents, module: ast.Module | None
) -> HoverContents:
    if isinstance(contents, str):
        return demangle_text(contents, module)
    if isinstance(contents, types.MarkedStringWithLanguage):
        return _demangle_marked_string(contents, module)
    if isinstance(contents, types.MarkupContent):
        return types.MarkupContent(
            kind=contents.kind,
            value=demangle_text(contents.value, module),
        )
    return [_demangle_marked_string(item, module) for item in contents]


def demangle_hover_names(hover: types.Hover, module: ast.Module | None) -> types.Hover:
    demangled = copy.copy(hover)
    demangled.contents = _demangle_hover_contents(hover.contents, module)
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
