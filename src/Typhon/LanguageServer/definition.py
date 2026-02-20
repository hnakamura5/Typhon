from collections.abc import Sequence

from lsprotocol import types

from ..SourceMap.ast_match_based_map import MatchBasedSourceMap
from .utils import (
    canonicalize_uri,
    map_name_unparsed_range_to_original_range,
    map_name_request_position_to_unparsed,
)


type DefinitionItem = types.Location | types.LocationLink
type DefinitionResult = (
    types.Location | Sequence[types.Location] | Sequence[types.LocationLink] | None
)
type TypeDefinitionResult = DefinitionResult


def map_definition_request_position(
    position: types.Position,
    source_map: MatchBasedSourceMap | None,
) -> types.Position | None:
    return map_name_request_position_to_unparsed(
        position,
        source_map,
        debug_prefix="Definition",
    )


def map_type_definition_request_position(
    position: types.Position,
    source_map: MatchBasedSourceMap | None,
) -> types.Position | None:
    return map_definition_request_position(position, source_map)


def _map_location(
    location: types.Location,
    mapping: dict[str, MatchBasedSourceMap],
    translated_uri_to_original_uri: dict[str, str],
) -> types.Location | None:
    original_uri = translated_uri_to_original_uri.get(canonicalize_uri(location.uri))
    if original_uri is None:
        return None
    mapped_range = map_name_unparsed_range_to_original_range(
        original_uri,
        location.range,
        mapping,
    )
    if mapped_range is None:
        return None
    return types.Location(uri=original_uri, range=mapped_range)


def _map_location_link(
    location_link: types.LocationLink,
    mapping: dict[str, MatchBasedSourceMap],
    translated_uri_to_original_uri: dict[str, str],
) -> types.LocationLink | None:
    original_uri = translated_uri_to_original_uri.get(
        canonicalize_uri(location_link.target_uri)
    )
    if original_uri is None:
        return None

    mapped_target_selection_range = map_name_unparsed_range_to_original_range(
        original_uri,
        location_link.target_selection_range,
        mapping,
    )
    mapped_target_range = map_name_unparsed_range_to_original_range(
        original_uri,
        location_link.target_range,
        mapping,
    )
    if mapped_target_selection_range is None or mapped_target_range is None:
        return None
    return types.LocationLink(
        target_uri=original_uri,
        target_range=mapped_target_range,
        target_selection_range=mapped_target_selection_range,
        origin_selection_range=None,
    )


def map_definition_result(
    definition_result: DefinitionResult,
    mapping: dict[str, MatchBasedSourceMap],
    translated_uri_to_original_uri: dict[str, str],
) -> DefinitionResult:
    if definition_result is None:
        return None
    if isinstance(definition_result, types.Location):
        return _map_location(
            definition_result,
            mapping,
            translated_uri_to_original_uri,
        )
    if len(definition_result) == 0:
        return []
    if isinstance(definition_result[0], types.Location):
        mapped_locations: list[types.Location] = []
        for location in definition_result:
            if isinstance(location, types.Location):
                if mapped := _map_location(
                    location,
                    mapping,
                    translated_uri_to_original_uri,
                ):
                    mapped_locations.append(mapped)
        return mapped_locations
    else:
        mapped_location_links: list[types.LocationLink] = []
        for item in definition_result:
            if isinstance(item, types.LocationLink):
                if mapped := _map_location_link(
                    item,
                    mapping,
                    translated_uri_to_original_uri,
                ):
                    mapped_location_links.append(mapped)
        return mapped_location_links


def map_type_definition_result(
    type_definition_result: TypeDefinitionResult,
    mapping: dict[str, MatchBasedSourceMap],
    translated_uri_to_original_uri: dict[str, str],
) -> TypeDefinitionResult:
    return map_definition_result(
        type_definition_result,
        mapping,
        translated_uri_to_original_uri,
    )
