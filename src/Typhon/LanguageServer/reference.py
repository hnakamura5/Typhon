from typing import Callable, Sequence

from lsprotocol import types

from ..SourceMap.ast_match_based_map import MatchBasedSourceMap
from .utils import (
    map_name_request_position_to_unparsed,
    map_translated_uri_and_name_range_to_original,
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
    mapping: Callable[[str], MatchBasedSourceMap | None],
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


def map_reference_result(
    reference_result: ReferenceResult,
    mapping: Callable[[str], MatchBasedSourceMap | None],
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
