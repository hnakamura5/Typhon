import asyncio
from pathlib import Path
from collections.abc import Sequence

from lsprotocol import types
from pygls.lsp.client import LanguageClient

from Typhon.LanguageServer._utils.path import path_to_uri
from .utils import start_initialize_open_typhon_connection_client, ensure_exit


completion_input_dir = Path(__file__).resolve().parent / "completion_inputs"
normal_completion_file = completion_input_dir / "normal_completion.typh"
trigger_completion_broken_file = completion_input_dir / "trigger_completion_broken.typh"


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
            root_dir=completion_input_dir,
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


def test_completion_trigger_character_broken_source_e2e():
    async def run_test() -> None:
        client, _ = await start_initialize_open_typhon_connection_client(
            root_dir=completion_input_dir,
            open_file=trigger_completion_broken_file,
        )
        try:
            result = await request_completion(
                client,
                path_to_uri(trigger_completion_broken_file),
                line=3,
                character=22,
                context=types.CompletionContext(
                    trigger_kind=types.CompletionTriggerKind.TriggerCharacter,
                    trigger_character=".",
                ),
            )
            assert result is None or isinstance(result, (types.CompletionList, list))
        finally:
            await ensure_exit(client)

    asyncio.run(run_test())
