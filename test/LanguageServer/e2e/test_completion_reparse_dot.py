import asyncio
from collections.abc import Sequence

from lsprotocol import types

from Typhon.LanguageServer._utils.path import path_to_uri
from .utils import (
    start_initialize_open_typhon_connection_client,
    ensure_exit,
    sample_workspace,
)
from .test_completion import (
    request_completion,
    assert_candidate_in_completion_result,
    request_trigger_completion,
    normal_completion_file,
    trigger_completion_dot_file,
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
