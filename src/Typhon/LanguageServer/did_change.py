from collections.abc import Sequence
import bisect
import difflib

from lsprotocol import types

from ..LanguageServer.parsed_buffer import LanguageServerParsedBuffer
from ..LanguageServer.partial_reparse import try_reparse_range
from ..Driver.debugging import (
    debug_file_write,
    debug_file_write_verbose,
    is_testing_reparser,
)
from ..SourceMap.ast_match_based_map import MatchBasedSourceMap
from ._utils.mapping import (
    lsp_range_to_range,
    range_to_lsp_range,
    lsp_position_to_pos,
    pos_to_lsp_position,
)


def _to_line_starts(text: str) -> list[int]:
    line_starts = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            line_starts.append(i + 1)
    return line_starts


def _offset_to_lsp_position(offset: int, line_starts: list[int]) -> types.Position:
    line = bisect.bisect_right(line_starts, offset) - 1
    return types.Position(line=line, character=offset - line_starts[line])


def text_diff_to_partial_changes(
    unparsed_before_change: str,
    unparsed_after_change: str,
) -> list[types.TextDocumentContentChangePartial]:
    if unparsed_before_change == unparsed_after_change:
        return []
    before_line_starts = _to_line_starts(unparsed_before_change)
    matcher = difflib.SequenceMatcher(
        a=unparsed_before_change,
        b=unparsed_after_change,
        autojunk=False,
    )
    changes: list[types.TextDocumentContentChangePartial] = []
    for tag, before_start, before_end, after_start, after_end in reversed(
        matcher.get_opcodes()
    ):
        if tag == "equal":
            continue
        changes.append(
            types.TextDocumentContentChangePartial(
                range=types.Range(
                    start=_offset_to_lsp_position(before_start, before_line_starts),
                    end=_offset_to_lsp_position(before_end, before_line_starts),
                ),
                text=unparsed_after_change[after_start:after_end],
            )
        )
    return changes


def map_content_change(
    change: types.TextDocumentContentChangeEvent,
    source_map: MatchBasedSourceMap,
) -> types.TextDocumentContentChangeEvent | None:
    if isinstance(change, types.TextDocumentContentChangeWholeDocument):
        return change
    if change.range.start == change.range.end:
        # One position change.
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
        mapped_range = source_map.origin_range_to_unparsed_range(
            lsp_range_to_range(change.range)
        )
    if mapped_range is None:
        debug_file_write(
            lambda: (
                f"Did change range mapping failed for {change.range}, skipping this change."
            )
        )
        return None
    return types.TextDocumentContentChangePartial(
        range=(
            mapped_range
            if isinstance(mapped_range, types.Range)
            else range_to_lsp_range(mapped_range)
        ),
        text=change.text,
        range_length=change.range_length,
    )


def map_did_change_content_changes(
    content_changes: Sequence[types.TextDocumentContentChangeEvent],
    source_map: MatchBasedSourceMap,
) -> list[types.TextDocumentContentChangeEvent]:
    return [
        mapped_change
        for change in content_changes
        if (mapped_change := map_content_change(change, source_map)) is not None
    ]


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


def map_did_change_params_with_reparse(
    parsed_buffer: LanguageServerParsedBuffer,
    translated_uri: str,
    params: types.DidChangeTextDocumentParams,
) -> types.DidChangeTextDocumentParams | None:
    original_uri = params.text_document.uri
    content_changes = params.content_changes
    source_map = parsed_buffer.get_mapping(original_uri)
    result: list[types.TextDocumentContentChangeEvent] = []
    if not source_map:
        debug_file_write(
            lambda: (
                f"No source map for {original_uri}, cannot map did change content changes, skipping mapping and trying partial reparse."
            )
        )
        return None
    for change in content_changes:
        debug_file_write_verbose(lambda: f"Processing change: {change}")
        if isinstance(change, types.TextDocumentContentChangePartial):
            unparsed_before_change = parsed_buffer.get_translated_source(original_uri)
            if try_reparse_range(
                parsed_buffer,
                original_uri,
                source_map.source_code,
                change.range,
            ):
                debug_file_write(
                    lambda: (
                        f"Successfully reparsed changed range {change.range} in {original_uri}, skipping mapping and using reparse result."
                    )
                )
                unparsed_after_reparse = parsed_buffer.get_translated_source(
                    original_uri
                )
                if not unparsed_before_change or not unparsed_after_reparse:
                    return None
                content_changes_after_reparse = text_diff_to_partial_changes(
                    unparsed_before_change,
                    unparsed_after_reparse,
                )
                if not content_changes_after_reparse:
                    return None  # TODO: This casee is full change. Maybe not None.
                return types.DidChangeTextDocumentParams(
                    text_document=types.VersionedTextDocumentIdentifier(
                        uri=translated_uri,
                        version=params.text_document.version,
                    ),
                    content_changes=content_changes_after_reparse,
                )
        # if mapped_change := map_content_change(change, source_map):
        #     result.append(mapped_change)
    debug_file_write_verbose(lambda: f"Mapped did change content changes: {result}")
    if not result:
        if is_testing_reparser():
            debug_file_write(
                lambda: (
                    f"No mapped content changes for {params.content_changes} in {original_uri}, but we're in testing reparser mode, so we will return None to trigger full reparse."
                )
            )
            assert False
        return None
    return (
        types.DidChangeTextDocumentParams(
            text_document=types.VersionedTextDocumentIdentifier(
                uri=translated_uri,
                version=params.text_document.version,
            ),
            content_changes=result,
        )
        if result
        else None
    )
