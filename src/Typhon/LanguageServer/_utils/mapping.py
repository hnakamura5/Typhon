import ast
from typing import Callable

from lsprotocol import types

from ...Driver.debugging import debug_file_write_verbose
from ...SourceMap.ast_match_based_map import MatchBasedSourceMap
from ...SourceMap.datatype import Range, Pos
from .path import canonicalize_uri


def range_to_lsp_range(r: Range) -> types.Range:
    return types.Range(
        start=pos_to_lsp_position(r.start),
        end=pos_to_lsp_position(r.end),
    )


def lsp_range_to_range(r: types.Range) -> Range:
    return Range(
        start=lsp_position_to_pos(r.start),
        end=lsp_position_to_pos(r.end),
    )


def lsp_position_to_pos(position: types.Position) -> Pos:
    return Pos(line=position.line, column=position.character)


def pos_to_lsp_position(pos: Pos) -> types.Position:
    return types.Position(line=pos.line, character=pos.column)


def to_point_range(position: types.Position) -> Range:
    pos = lsp_position_to_pos(position)
    return Range(start=pos, end=pos)


def map_name_request_position_to_unparsed(
    position: types.Position,
    source_map: MatchBasedSourceMap | None,
    debug_prefix: str,
) -> types.Position | None:
    if source_map is None:
        return None
    mapped_name = source_map.origin_pos_to_unparsed_node(
        lsp_position_to_pos(position),
        ast.Name,
    )
    if not isinstance(mapped_name, ast.Name):
        debug_file_write_verbose(
            f"{debug_prefix} request position is not mapped as ast.Name: {position}"
        )
        return None
    mapped_range = Range.from_ast_node(mapped_name)
    if mapped_range is None:
        return None
    return pos_to_lsp_position(mapped_range.start)


def map_name_unparsed_range_to_original_range(
    original_uri: str,
    source_range: types.Range,
    mapping: Callable[[str], MatchBasedSourceMap | None],
) -> types.Range | None:
    result = None
    # When jumping (0, 0), possible to jump top of the file.
    # TODO: More precise way?
    if source_range.start.line == 0 and source_range.start.character == 0:
        result = source_range
    source_map = mapping(original_uri)
    if source_map is None:
        return result

    mapped_name = source_map.unparsed_pos_to_origin_node(
        lsp_position_to_pos(source_range.start),
        ast.Name,
    )
    if not isinstance(mapped_name, ast.Name):
        return result
    mapped_range = Range.from_ast_node(mapped_name)
    if mapped_range is None:
        return result

    # Sanity check: the mapped original name should map back to a translated name.
    mapped_position = pos_to_lsp_position(mapped_range.start)
    mapped_back = source_map.origin_pos_to_unparsed_node(
        lsp_position_to_pos(mapped_position),
        ast.Name,
    )
    if not isinstance(mapped_back, ast.Name):
        return result
    return range_to_lsp_range(mapped_range)


def map_translated_uri_and_name_range_to_original(
    translated_uri: str,
    source_range: types.Range,
    mapping: Callable[[str], MatchBasedSourceMap | None],
    translated_uri_to_original_uri: dict[str, str],
) -> tuple[str, types.Range] | None:
    original_uri = translated_uri_to_original_uri.get(canonicalize_uri(translated_uri))
    if original_uri is None:
        return None
    mapped_range = map_name_unparsed_range_to_original_range(
        original_uri,
        source_range,
        mapping,
    )
    if mapped_range is None:
        return None
    return original_uri, mapped_range
