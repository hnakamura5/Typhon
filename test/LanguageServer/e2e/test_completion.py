import asyncio
from collections.abc import Sequence

from lsprotocol import types
from pygls.lsp.client import LanguageClient

from Typhon.LanguageServer._utils.path import path_to_uri
from .utils import (
    start_initialize_open_typhon_connection_client,
    ensure_exit,
    sample_workspace,
)


normal_completion_file = sample_workspace / "normal_completion.typh"
trigger_completion_file = sample_workspace / "trigger_completion.typh"
trigger_completion_optional_file = sample_workspace / "trigger_completion_optional.typh"

type CompletionResult = types.CompletionList | Sequence[types.CompletionItem] | None


async def request_completion(
    client: LanguageClient,
    uri: str,
    line: int,
    character: int,
    context: types.CompletionContext | None = None,
) -> CompletionResult:
    async with asyncio.timeout(10):
        return await client.text_document_completion_async(
            types.CompletionParams(
                text_document=types.TextDocumentIdentifier(uri=uri),
                position=types.Position(line=line, character=character),
                context=context,
            )
        )


def assert_candidate_in_completion_result(
    result: CompletionResult,
    expected_label: str,
    expected_kind: types.CompletionItemKind | None = None,
) -> None:
    assert result is not None, "Completion result is None"
    items = result.items if isinstance(result, types.CompletionList) else result
    for item in items:
        if item.label == expected_label:
            if expected_kind is not None:
                assert item.kind == expected_kind, (
                    f"Expected kind {expected_kind} but got {item.kind}"
                )
            return
    assert False, (
        f"Expected completion item with label '{expected_label}' of kind '{expected_kind}' not found in completion results."
    )


def test_completion_normal_invoked_e2e():
    async def run_test() -> None:
        client, _ = await start_initialize_open_typhon_connection_client(
            root_dir=sample_workspace,
            open_file=normal_completion_file,
        )
        try:
            result = await request_completion(
                client,
                path_to_uri(normal_completion_file),
                line=3,
                character=13,
            )
            assert result is None or isinstance(result, (types.CompletionList, list))
        finally:
            await ensure_exit(client)

    asyncio.run(run_test())


async def request_dot_trigger_completion(
    client: LanguageClient,
    trigger_uri: str,
    line: int,
    character: int,
) -> CompletionResult:
    client.text_document_did_change(
        types.DidChangeTextDocumentParams(
            text_document=types.VersionedTextDocumentIdentifier(
                version=2,
                uri=trigger_uri,
            ),
            content_changes=[
                types.TextDocumentContentChangePartial(
                    range=types.Range(
                        start=types.Position(line=line, character=character),
                        end=types.Position(line=line, character=character),
                    ),
                    text=".",
                    range_length=0,
                )
            ],
        )
    )
    result = await request_completion(
        client,
        trigger_uri,
        line=line,
        character=character + 1,
        context=types.CompletionContext(
            trigger_kind=types.CompletionTriggerKind.TriggerCharacter,
            trigger_character=".",
        ),
    )
    return result


def test_completion_trigger_character_dot_typed_e2e():
    async def run_test() -> None:
        client, _ = await start_initialize_open_typhon_connection_client(
            root_dir=sample_workspace,
            open_file=trigger_completion_file,
        )
        try:
            trigger_uri = path_to_uri(trigger_completion_file)
            result = await request_dot_trigger_completion(
                client,
                trigger_uri,
                line=3,
                character=17,
            )
            assert result is None or isinstance(result, (types.CompletionList, list))
            assert_candidate_in_completion_result(
                result,
                expected_label="add",
                expected_kind=types.CompletionItemKind.Function,
            )
        finally:
            await ensure_exit(client)

    asyncio.run(run_test())


def test_completion_trigger_character_optional_dot_typed_e2e():
    async def run_test() -> None:
        client, _ = await start_initialize_open_typhon_connection_client(
            root_dir=sample_workspace,
            open_file=trigger_completion_optional_file,
        )
        try:
            trigger_uri = path_to_uri(trigger_completion_optional_file)
            result = await request_dot_trigger_completion(
                client,
                trigger_uri,
                line=3,
                character=18,
            )
            assert result is None or isinstance(result, (types.CompletionList, list))
            assert_candidate_in_completion_result(
                result,
                expected_label="add",
                expected_kind=types.CompletionItemKind.Function,
            )
        finally:
            await ensure_exit(client)

    asyncio.run(run_test())
