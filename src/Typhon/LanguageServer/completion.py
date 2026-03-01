import copy
from typing import Callable, Sequence

from lsprotocol import types

from ..Driver.debugging import debug_file_write
from ..SourceMap.ast_match_based_map import MatchBasedSourceMap
from ..SourceMap.datatype import Pos
from ._utils.mapping import (
    lsp_position_to_pos,
    lsp_range_to_range,
    pos_to_lsp_position,
    range_to_lsp_range,
)


type CompletionResult = types.CompletionList | Sequence[types.CompletionItem] | None


def map_completion_request_params(
    params: types.CompletionParams,
    source_map: MatchBasedSourceMap | None,
) -> types.CompletionParams | None:
    if source_map is None:
        debug_file_write("Completion request mapper: source map is not available.")
        return None

    trigger_character = params.context.trigger_character if params.context else None
    trigger_len = len(trigger_character) if trigger_character else 0
    original_pos = lsp_position_to_pos(params.position)
    probe_col = max(0, original_pos.column - trigger_len)
    mapped_probe = source_map.origin_pos_to_unparsed_pos(
        Pos(line=original_pos.line, column=probe_col).col_back(),
        prefer_right=True,
    )
    if mapped_probe is None:
        debug_file_write(
            "Completion request mapper: failed to map origin position "
            f"{params.position} probe_col={probe_col} (trigger={trigger_character})."
        )
        return None
    mapped_column = mapped_probe.column + trigger_len
    mapped_position = pos_to_lsp_position(
        Pos(line=mapped_probe.line, column=mapped_column)
    )
    mapped_params = copy.deepcopy(params)
    mapped_params.position = mapped_position
    debug_file_write(
        "Completion request mapper: "
        f"uri={params.text_document.uri}, "
        f"position={params.position} -> {mapped_position}, "
        f"context={params.context}, "
        f"trigger_len={trigger_len}"
    )
    return mapped_params


def map_completion_result(
    completion_result: CompletionResult,
    original_uri: str,
    mapping: Callable[[str], MatchBasedSourceMap | None],
) -> CompletionResult:
    if completion_result is None:
        return None

    def _map_text_edit(
        edit: types.TextEdit | types.InsertReplaceEdit,
        source_map: MatchBasedSourceMap,
    ) -> types.TextEdit | types.InsertReplaceEdit | None:
        if isinstance(edit, types.TextEdit):
            mapped_range = source_map.unparsed_range_to_origin_range(
                lsp_range_to_range(edit.range)
            )
            if mapped_range is None:
                return None
            return types.TextEdit(
                range=range_to_lsp_range(mapped_range),
                new_text=edit.new_text,
            )
        mapped_insert = source_map.unparsed_range_to_origin_range(
            lsp_range_to_range(edit.insert)
        )
        mapped_replace = source_map.unparsed_range_to_origin_range(
            lsp_range_to_range(edit.replace)
        )
        if mapped_insert is None or mapped_replace is None:
            return None
        return types.InsertReplaceEdit(
            new_text=edit.new_text,
            insert=range_to_lsp_range(mapped_insert),
            replace=range_to_lsp_range(mapped_replace),
        )

    def _map_item(
        item: types.CompletionItem,
        source_map: MatchBasedSourceMap,
    ) -> types.CompletionItem:
        mapped_item = copy.deepcopy(item)
        if mapped_item.text_edit is not None:
            mapped_edit = _map_text_edit(mapped_item.text_edit, source_map)
            mapped_item.text_edit = mapped_edit
        if mapped_item.additional_text_edits is not None:
            mapped_additional: list[types.TextEdit] = []
            for edit in mapped_item.additional_text_edits:
                mapped_edit = _map_text_edit(edit, source_map)
                if isinstance(mapped_edit, types.TextEdit):
                    mapped_additional.append(mapped_edit)
            mapped_item.additional_text_edits = mapped_additional
        return mapped_item

    source_map = mapping(original_uri)

    if source_map is None:
        debug_file_write(
            "Completion result mapper: source map unavailable. Returning backend result as-is."
        )
        return completion_result

    if isinstance(completion_result, types.CompletionList):
        mapped_items = [_map_item(item, source_map) for item in completion_result.items]
        return types.CompletionList(
            is_incomplete=completion_result.is_incomplete,
            item_defaults=completion_result.item_defaults,
            items=mapped_items,
        )

    mapped_sequence = [_map_item(item, source_map) for item in completion_result]
    debug_file_write(
        "Completion result mapper: "
        f"result={completion_result}, "
        f"original_uri={original_uri}"
    )
    return mapped_sequence
