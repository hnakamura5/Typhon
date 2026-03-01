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


def test_completion_trigger_character_dot_typed_e2e():
    async def run_test() -> None:
        client, _ = await start_initialize_open_typhon_connection_client(
            root_dir=sample_workspace,
            open_file=trigger_completion_file,
        )
        try:
            trigger_uri = path_to_uri(trigger_completion_file)
            client.text_document_did_change(
                types.DidChangeTextDocumentParams(
                    text_document=types.VersionedTextDocumentIdentifier(
                        version=2,
                        uri=trigger_uri,
                    ),
                    content_changes=[
                        types.TextDocumentContentChangePartial(
                            range=types.Range(
                                start=types.Position(line=3, character=17),
                                end=types.Position(line=3, character=17),
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
                line=3,
                character=18,
                context=types.CompletionContext(
                    trigger_kind=types.CompletionTriggerKind.TriggerCharacter,
                    trigger_character=".",
                ),
            )
            assert result is None or isinstance(result, (types.CompletionList, list))
        finally:
            await ensure_exit(client)

    asyncio.run(run_test())
