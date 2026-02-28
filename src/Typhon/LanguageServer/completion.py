from typing import Callable, Sequence

from lsprotocol import types

from ..Driver.debugging import debug_file_write
from ..SourceMap.ast_match_based_map import MatchBasedSourceMap


type CompletionResult = types.CompletionList | Sequence[types.CompletionItem] | None


def map_completion_request_params(
    params: types.CompletionParams,
    source_map: MatchBasedSourceMap | None,
) -> types.CompletionParams | None:
    debug_file_write(
        "Completion request mapper (dummy): "
        f"uri={params.text_document.uri}, "
        f"position={params.position}, "
        f"context={params.context}, "
        f"has_source_map={source_map is not None}"
    )
    return None


def map_completion_result(
    completion_result: CompletionResult,
    mapping: Callable[[str], MatchBasedSourceMap | None],
    translated_uri_to_original_uri: dict[str, str],
) -> types.CompletionList:
    debug_file_write(
        "Completion result mapper (dummy): "
        f"result={completion_result}, "
        f"known_mappings={len(translated_uri_to_original_uri)}"
    )
    return types.CompletionList(is_incomplete=False, items=[])
