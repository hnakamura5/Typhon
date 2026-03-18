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
from .test_completion import request_completion, assert_candidate_in_completion_result


normal_completion_file = sample_workspace / "normal_completion.typh"
trigger_completion_dot_file = sample_workspace / "trigger_completion_dot.typh"
trigger_completion_dot_optional_file = (
    sample_workspace / "trigger_completion_optional.typh"
)
trigger_completion_subscr_file = sample_workspace / "trigger_completion_subscr.typh"
trigger_completion_subscr_optional_file = (
    sample_workspace / "trigger_completion_subscr_optional.typh"
)

type CompletionResult = types.CompletionList | Sequence[types.CompletionItem] | None


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


async def request_trigger_completion(
    client: LanguageClient,
    trigger_uri: str,
    trigger_char: str,
    line: int,
    character: int,
    trigger_change: str | None = None,
) -> CompletionResult:
    trigger_change = trigger_change if trigger_change is not None else trigger_char
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
                    text=trigger_char,
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
            trigger_character=trigger_char,
        ),
    )
    return result


def test_completion_trigger_character_dot_typed_e2e():
    async def run_test() -> None:
        client, _ = await start_initialize_open_typhon_connection_client(
            root_dir=sample_workspace,
            open_file=trigger_completion_dot_file,
            testing_reparser=True,
        )
        try:
            trigger_uri = path_to_uri(trigger_completion_dot_file)
            result = await request_trigger_completion(
                client,
                trigger_uri,
                trigger_char=".",
                line=3,
                character=18,
            )
            assert result is None or isinstance(result, (types.CompletionList, list))
            assert_candidate_in_completion_result(
                result,
                expected_label="add",
                expected_kind=types.CompletionItemKind.Function,
            )
            result = await request_trigger_completion(
                client,
                trigger_uri,
                trigger_char=".",
                line=3,
                character=18,
            )
        finally:
            await ensure_exit(client)

    asyncio.run(run_test())


def test_completion_trigger_character_optional_dot_typed_e2e():
    async def run_test() -> None:
        client, _ = await start_initialize_open_typhon_connection_client(
            root_dir=sample_workspace,
            open_file=trigger_completion_dot_file,
            testing_reparser=True,
        )
        try:
            trigger_uri = path_to_uri(trigger_completion_dot_file)
            result = await request_trigger_completion(
                client,
                trigger_uri,
                trigger_char=".",
                line=4,
                character=19,
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
