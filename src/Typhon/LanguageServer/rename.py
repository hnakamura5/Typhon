from typing import Callable, Mapping, Sequence
import copy

from lsprotocol import types

from ..SourceMap.ast_match_based_map import MatchBasedSourceMap
from ._utils.edit import DocumentEdits, TextEdits
from ._utils.mapping import (
    map_name_request_position_to_unparsed,
    map_translated_uri_and_name_range_to_original,
)
from ._utils.path import (
    canonicalize_uri,
)


type RenameResult = types.WorkspaceEdit | None


def map_rename_request_position(
    position: types.Position,
    source_map: MatchBasedSourceMap | None,
) -> types.Position | None:
    return map_name_request_position_to_unparsed(
        position,
        source_map,
        debug_prefix="Rename",
    )


def _map_text_edits(
    edit: TextEdits,
    mapped_range: types.Range,
) -> TextEdits:
    result = copy.deepcopy(edit)
    result.range = mapped_range
    return result


def _map_text_edit_range(
    translated_uri: str,
    source_range: types.Range,
    mapping: Callable[[str], MatchBasedSourceMap | None],
    translated_uri_to_original_uri: dict[str, str],
) -> tuple[str, types.Range] | None:
    return map_translated_uri_and_name_range_to_original(
        translated_uri,
        source_range,
        mapping,
        translated_uri_to_original_uri,
    )


def _map_changes(
    changes: Mapping[str, Sequence[types.TextEdit]] | None,
    mapping: Callable[[str], MatchBasedSourceMap | None],
    translated_uri_to_original_uri: dict[str, str],
) -> dict[str, list[types.TextEdit]] | None:
    if changes is None:
        return None
    # Original uri -> edits
    mapped_changes: dict[str, list[types.TextEdit]] = {}
    for translated_uri, edits in changes.items():
        mapped_edits: list[types.TextEdit] = []
        for edit in edits:
            mapped_result = _map_text_edit_range(
                translated_uri,
                edit.range,
                mapping,
                translated_uri_to_original_uri,
            )
            if mapped_result is None:
                continue
            _, mapped_range = mapped_result
            mapped_edits.append(
                types.TextEdit(range=mapped_range, new_text=edit.new_text)
            )
        if not mapped_edits:
            continue
        canonical_uri = canonicalize_uri(translated_uri)
        original_uri = translated_uri_to_original_uri.get(canonical_uri)
        if original_uri is None:
            continue
        mapped_changes[original_uri] = mapped_edits
    return mapped_changes if mapped_changes else None


def _map_text_document_edit(
    change: types.TextDocumentEdit,
    mapping: Callable[[str], MatchBasedSourceMap | None],
    translated_uri_to_original_uri: dict[str, str],
) -> types.TextDocumentEdit | None:
    translated_uri = change.text_document.uri
    original_uri = translated_uri_to_original_uri.get(canonicalize_uri(translated_uri))
    if original_uri is None:
        return None
    mapped_edits: list[TextEdits] = []
    for edit in change.edits:
        mapped_result = _map_text_edit_range(
            translated_uri,
            edit.range,
            mapping,
            translated_uri_to_original_uri,
        )
        if mapped_result is None:
            continue
        _, mapped_range = mapped_result
        mapped_edits.append(_map_text_edits(edit, mapped_range))
    if not mapped_edits:
        return None
    return types.TextDocumentEdit(
        text_document=types.OptionalVersionedTextDocumentIdentifier(
            uri=original_uri,
            version=change.text_document.version,
        ),
        edits=mapped_edits,
    )


def _map_document_change(
    change: DocumentEdits,
    mapping: Callable[[str], MatchBasedSourceMap | None],
    translated_uri_to_original_uri: dict[str, str],
) -> DocumentEdits | None:
    if isinstance(change, types.TextDocumentEdit):
        return _map_text_document_edit(
            change,
            mapping,
            translated_uri_to_original_uri,
        )
    if isinstance(change, types.CreateFile):
        return types.CreateFile(
            uri=translated_uri_to_original_uri.get(
                canonicalize_uri(change.uri),
                change.uri,
            ),
            options=change.options,
            annotation_id=change.annotation_id,
        )
    if isinstance(change, types.RenameFile):
        return types.RenameFile(
            old_uri=translated_uri_to_original_uri.get(
                canonicalize_uri(change.old_uri),
                change.old_uri,
            ),
            new_uri=translated_uri_to_original_uri.get(
                canonicalize_uri(change.new_uri),
                change.new_uri,
            ),
            options=change.options,
            annotation_id=change.annotation_id,
        )
    return types.DeleteFile(
        uri=translated_uri_to_original_uri.get(
            canonicalize_uri(change.uri),
            change.uri,
        ),
        options=change.options,
        annotation_id=change.annotation_id,
    )


def _map_document_changes(
    document_changes: Sequence[DocumentEdits] | None,
    mapping: Callable[[str], MatchBasedSourceMap | None],
    translated_uri_to_original_uri: dict[str, str],
) -> list[DocumentEdits] | None:
    if document_changes is None:
        return None
    mapped_changes: list[DocumentEdits] = []
    for change in document_changes:
        if mapped_change := _map_document_change(
            change,
            mapping,
            translated_uri_to_original_uri,
        ):
            mapped_changes.append(mapped_change)
    return mapped_changes if mapped_changes else None


def map_rename_result(
    rename_result: RenameResult,
    mapping: Callable[[str], MatchBasedSourceMap | None],
    translated_uri_to_original_uri: dict[str, str],
) -> RenameResult:
    if rename_result is None:
        return None

    mapped_changes = _map_changes(
        rename_result.changes,
        mapping,
        translated_uri_to_original_uri,
    )
    mapped_document_changes = _map_document_changes(
        rename_result.document_changes,
        mapping,
        translated_uri_to_original_uri,
    )
    if mapped_changes is None and mapped_document_changes is None:
        return None
    return types.WorkspaceEdit(
        changes=mapped_changes,
        document_changes=mapped_document_changes,
        change_annotations=rename_result.change_annotations,
    )
