import copy

from lsprotocol import types

from ..Driver.debugging import debug_file_write_verbose
from ..SourceMap.ast_match_based_map import MatchBasedSourceMap
from ..SourceMap.datatype import Pos, Range
from .utils import (
    lsp_range_to_range,
    point_range_from_lsp_position,
    range_to_lsp_range,
)


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
