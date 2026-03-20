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
    assert_candidate_in_completion_result,
    request_trigger_completion,
    CompletionResult,
    trigger_completion_subscr_file,
)


def assert_pos_attributes_in_completion_result(
    result: CompletionResult,
) -> None:
    assert result is not None, "Completion result is None"
    assert_candidate_in_completion_result(
        result,
        expected_label="'lineno'",
        expected_kind=types.CompletionItemKind.Constant,
    )
    assert_candidate_in_completion_result(
        result,
        expected_label="'col_offset'",
        expected_kind=types.CompletionItemKind.Constant,
    )
    assert_candidate_in_completion_result(
        result,
        expected_label="'end_lineno'",
        expected_kind=types.CompletionItemKind.Constant,
    )
    assert_candidate_in_completion_result(
        result,
        expected_label="'end_col_offset'",
        expected_kind=types.CompletionItemKind.Constant,
    )


def test_completion_trigger_character_subscr_typed_e2e():
    async def run_test() -> None:
        client, _ = await start_initialize_open_typhon_connection_client(
            root_dir=sample_workspace,
            open_file=trigger_completion_subscr_file,
            testing_reparser=True,
        )
        try:
            trigger_uri = path_to_uri(trigger_completion_subscr_file)
            result = await request_trigger_completion(
                client,
                trigger_uri,
                trigger_char="[",
                line=16,
                character=17,
                trigger_change="[]",
            )
            assert result is None or isinstance(result, (types.CompletionList, list))
            assert_pos_attributes_in_completion_result(result)
        finally:
            await ensure_exit(client)

    asyncio.run(run_test())


def test_completion_trigger_character_optional_subscr_typed_e2e():
    async def run_test() -> None:
        client, _ = await start_initialize_open_typhon_connection_client(
            root_dir=sample_workspace,
            open_file=trigger_completion_subscr_file,
            testing_reparser=True,
        )
        try:
            trigger_uri = path_to_uri(trigger_completion_subscr_file)
            result = await request_trigger_completion(
                client,
                trigger_uri,
                trigger_char="[",
                line=17,
                character=18,
                trigger_change="[]",
            )
            assert result is None or isinstance(result, (types.CompletionList, list))
            assert_pos_attributes_in_completion_result(result)
        finally:
            await ensure_exit(client)

    asyncio.run(run_test())
