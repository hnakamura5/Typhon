import asyncio

from lsprotocol import types
from pygls.lsp.client import LanguageClient

from Typhon.Driver.debugging import debug_verbose_print
from Typhon.LanguageServer.utils import canonicalize_uri, path_to_uri
from .utils import (
    SampleWorkspaceFiles,
    copy_sample_workspace_to_temp,
    ensure_exit,
    open_file_in_client,
    start_initialize_open_typhon_connection_client,
    wait_file_exists,
)


def collect_text_edits(
    workspace_edit: types.WorkspaceEdit,
) -> list[tuple[str, types.Range, str]]:
    edits: list[tuple[str, types.Range, str]] = []
    if workspace_edit.changes:
        for uri, text_edits in workspace_edit.changes.items():
            for edit in text_edits:
                edits.append((uri, edit.range, edit.new_text))

    if workspace_edit.document_changes:
        for change in workspace_edit.document_changes:
            if isinstance(change, types.TextDocumentEdit):
                for edit in change.edits:
                    if isinstance(edit, types.SnippetTextEdit):
                        edits.append(
                            (change.text_document.uri, edit.range, str(edit.snippet))
                        )
                    else:
                        edits.append(
                            (change.text_document.uri, edit.range, edit.new_text)
                        )
    return edits


def assert_has_text_edit(
    edits: list[tuple[str, types.Range, str]],
    expected_uri: str,
    expected_line: int,
    expected_start_character: int,
    expected_end_character: int,
    expected_new_text: str,
) -> None:
    canonical_expected_uri = canonicalize_uri(expected_uri)
    for uri, r, new_text in edits:
        if (
            canonicalize_uri(uri) == canonical_expected_uri
            and r.start.line == expected_line
            and r.start.character == expected_start_character
            and r.end.character == expected_end_character
            and new_text == expected_new_text
        ):
            return
    raise AssertionError(
        f"Expected edit uri={expected_uri}, line={expected_line}, "
        f"start={expected_start_character}, end={expected_end_character}, "
        f"new_text={expected_new_text}, got={edits}"
    )


async def request_rename(
    client: LanguageClient,
    uri: str,
    line: int,
    character: int,
    new_name: str,
) -> types.WorkspaceEdit | None:
    async with asyncio.timeout(10):
        result = await client.text_document_rename_async(
            types.RenameParams(
                text_document=types.TextDocumentIdentifier(uri=uri),
                position=types.Position(line=line, character=character),
                new_name=new_name,
            )
        )
    debug_verbose_print(f"Received rename result: {result}")
    return result


def test_rename_feature_greet_definition_to_main_usage():
    async def run_test() -> None:
        temp_workspace: SampleWorkspaceFiles = copy_sample_workspace_to_temp()
        client, _ = await start_initialize_open_typhon_connection_client(
            root_dir=temp_workspace.root,
            open_file=temp_workspace.main_file,
        )
        # Wait until workspace preload.
        open_file_in_client(client, temp_workspace.feature_file)
        await wait_file_exists(temp_workspace.feature_file)
        try:
            # 'greet' in feature.typh is renamed to 'salute'.
            workspace_edit = await request_rename(
                client,
                path_to_uri(temp_workspace.feature_file),
                line=2,
                character=4,
                new_name="salute",
            )
            assert workspace_edit is not None
            edits = collect_text_edits(workspace_edit)
            assert len(edits) >= 2
            # The definition in feature.typh is renamed.
            assert_has_text_edit(
                edits,
                expected_uri=path_to_uri(temp_workspace.feature_file),
                expected_line=2,
                expected_start_character=4,
                expected_end_character=9,
                expected_new_text="salute",
            )
            # The usage in main.typh is renamed.
            assert_has_text_edit(
                edits,
                expected_uri=path_to_uri(temp_workspace.main_file),
                expected_line=4,
                expected_start_character=10,
                expected_end_character=15,
                expected_new_text="salute",
            )
        finally:
            await ensure_exit(client)

    asyncio.run(run_test())


def test_rename_feature_parameter_name_definition_and_usage():
    async def run_test() -> None:
        temp_workspace: SampleWorkspaceFiles = copy_sample_workspace_to_temp()
        client, _ = await start_initialize_open_typhon_connection_client(
            root_dir=temp_workspace.root,
            open_file=temp_workspace.feature_file,
        )
        try:
            # 'name' parameter in feature.typh is renamed to 'person'.
            workspace_edit = await request_rename(
                client,
                path_to_uri(temp_workspace.feature_file),
                line=2,
                character=10,
                new_name="person",
            )
            assert workspace_edit is not None
            edits = collect_text_edits(workspace_edit)
            assert (
                len(edits) == 2
            )  # Only including the parameter definition and usage, not 'name' in other contexts.
            # The parameter definition in feature.typh is renamed.
            assert_has_text_edit(
                edits,
                expected_uri=path_to_uri(temp_workspace.feature_file),
                expected_line=2,
                expected_start_character=10,
                expected_end_character=14,
                expected_new_text="person",
            )
            # The parameter usage in feature.typh is renamed.
            assert_has_text_edit(
                edits,
                expected_uri=path_to_uri(temp_workspace.feature_file),
                expected_line=4,
                expected_start_character=20,
                expected_end_character=24,
                expected_new_text="person",
            )
        finally:
            await ensure_exit(client)

    asyncio.run(run_test())
