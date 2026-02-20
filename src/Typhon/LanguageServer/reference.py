from collections.abc import Sequence

from lsprotocol import types

from ..SourceMap.ast_match_based_map import MatchBasedSourceMap
from .utils import (
    canonicalize_uri,
    map_name_unparsed_range_to_original_range,
    map_name_request_position_to_unparsed,
)


type ReferenceResult = Sequence[types.Location] | None


def map_reference_request_position(
    position: types.Position,
    source_map: MatchBasedSourceMap | None,
) -> types.Position | None:
    return map_name_request_position_to_unparsed(
        position,
        source_map,
        debug_prefix="Reference",
    )


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


def map_reference_result(
    reference_result: ReferenceResult,
    mapping: dict[str, MatchBasedSourceMap],
    translated_uri_to_original_uri: dict[str, str],
) -> ReferenceResult:
    if reference_result is None:
        return None
    if len(reference_result) == 0:
        return []

    mapped_locations: list[types.Location] = []
    for location in reference_result:
        if mapped := _map_location(
            location,
            mapping,
            translated_uri_to_original_uri,
        ):
            mapped_locations.append(mapped)
    return mapped_locations
