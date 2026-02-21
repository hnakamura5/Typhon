from collections.abc import Sequence

from lsprotocol import types

from ..SourceMap.ast_match_based_map import MatchBasedSourceMap
from .utils import (
    map_name_request_position_to_unparsed,
    map_translated_uri_and_name_range_to_original,
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
    mapped_result = map_translated_uri_and_name_range_to_original(
        location.uri,
        location.range,
        mapping,
        translated_uri_to_original_uri,
    )
    if mapped_result is None:
        return None
    original_uri, mapped_range = mapped_result
    return types.Location(uri=original_uri, range=mapped_range)


def _map_location_link(
    location_link: types.LocationLink,
    mapping: dict[str, MatchBasedSourceMap],
    translated_uri_to_original_uri: dict[str, str],
) -> types.LocationLink | None:
    mapped_target_selection_range_result = (
        map_translated_uri_and_name_range_to_original(
            location_link.target_uri,
            location_link.target_selection_range,
            mapping,
            translated_uri_to_original_uri,
        )
    )
    mapped_target_range_result = map_translated_uri_and_name_range_to_original(
        location_link.target_uri,
        location_link.target_range,
        mapping,
        translated_uri_to_original_uri,
    )
    if (
        mapped_target_selection_range_result is None
        or mapped_target_range_result is None
    ):
        return None
    target_selection_uri, mapped_target_selection_range = (
        mapped_target_selection_range_result
    )
    target_uri, mapped_target_range = mapped_target_range_result
    if target_selection_uri != target_uri:
        return None
    return types.LocationLink(
        target_uri=target_uri,
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
