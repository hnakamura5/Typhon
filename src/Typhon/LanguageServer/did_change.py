from collections.abc import Sequence

from lsprotocol import types

from ..Driver.debugging import debug_file_write
from ..SourceMap.ast_match_based_map import MatchBasedSourceMap
from ._utils.mapping import (
    lsp_range_to_range,
    range_to_lsp_range,
    lsp_position_to_pos,
    pos_to_lsp_position,
)


type DidChangeContentChange = (
    types.TextDocumentContentChangePartial
    | types.TextDocumentContentChangeWholeDocument
)


def map_did_change_content_changes(
    content_changes: Sequence[DidChangeContentChange],
    source_map: MatchBasedSourceMap,
) -> list[DidChangeContentChange]:
    mapped_content_changes: list[DidChangeContentChange] = []
    for change in content_changes:
        if isinstance(change, types.TextDocumentContentChangeWholeDocument):
            mapped_content_changes.append(change)
            continue
        if change.range.start == change.range.end:
            mapped_pos = source_map.origin_pos_to_unparsed_pos(
                lsp_position_to_pos(change.range.start).col_back(),
                prefer_right=True,
            )
            mapped_range = (
                types.Range(
                    start=pos_to_lsp_position(mapped_pos.col_forward()),
                    end=pos_to_lsp_position(mapped_pos.col_forward()),
                )
                if mapped_pos is not None
                else None
            )
        else:
            mapped_pos = None
            mapped_range = source_map.origin_range_to_unparsed_range(
                lsp_range_to_range(change.range)
            )
        if mapped_range is None:
            debug_file_write(
                lambda: (
                    f"Did change range mapping failed for {change.range}, skipping this change."
                )
            )
            continue
        mapped_content_changes.append(
            types.TextDocumentContentChangePartial(
                range=(
                    mapped_range
                    if isinstance(mapped_range, types.Range)
                    else range_to_lsp_range(mapped_range)
                ),
                text=change.text,
                range_length=change.range_length,
            )
        )
    return mapped_content_changes


def map_did_change_params(
    params: types.DidChangeTextDocumentParams,
    translated_uri: str,
    source_map: MatchBasedSourceMap,
) -> types.DidChangeTextDocumentParams | None:
    mapped_content_changes = map_did_change_content_changes(
        params.content_changes,
        source_map,
    )
    if not mapped_content_changes:
        return None
    return types.DidChangeTextDocumentParams(
        text_document=types.VersionedTextDocumentIdentifier(
            uri=translated_uri,
            version=params.text_document.version,
        ),
        content_changes=mapped_content_changes,
    )
