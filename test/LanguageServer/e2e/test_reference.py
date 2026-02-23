import asyncio
from pathlib import Path

from lsprotocol import types
from pygls.lsp.client import LanguageClient

from Typhon.Driver.debugging import debug_verbose_print
from Typhon.LanguageServer._utils.path import canonicalize_uri, path_to_uri
from .utils import (
    ensure_exit,
    open_file_in_client,
    start_initialize_open_typhon_connection_client,
    wait_file_exists,
    sample_workspace,
    main_file,
    feature_file,
    math_file,
    assert_has_location,
)


async def request_references(
    client: LanguageClient,
    uri: str,
    line: int,
    character: int,
    include_declaration: bool = True,
) -> list[types.Location]:
    async with asyncio.timeout(10):
        result = await client.text_document_references_async(
            types.ReferenceParams(
                text_document=types.TextDocumentIdentifier(uri=uri),
                position=types.Position(line=line, character=character),
                context=types.ReferenceContext(
                    include_declaration=include_declaration,
                ),
            )
        )
    debug_verbose_print(f"Received references result: {result}")
    return list(result) if result else []


def test_references_main_greet_definitiont_to_usage():
    async def run_test() -> None:
        client, _ = await start_initialize_open_typhon_connection_client(
            root_dir=sample_workspace,
            open_file=main_file,
        )
        # Wait until workspace preload.
        open_file_in_client(client, feature_file)
        await wait_file_exists(feature_file)
        try:
            # 'greet' definition in feature.typh
            locations = await request_references(
                client,
                path_to_uri(feature_file),
                line=2,
                character=4,
            )
            assert len(locations) >= 2
            assert_has_location(
                locations,
                expected_uri=path_to_uri(feature_file),
                expected_line=2,
                expected_start_character=4,
                expected_end_character=9,
            )
            # Import usage in main.typh
            assert_has_location(
                locations,
                expected_uri=path_to_uri(main_file),
                expected_line=1,
                expected_start_character=31,
                expected_end_character=36,
            )
            # Usage in main.typh
            assert_has_location(
                locations,
                expected_uri=path_to_uri(main_file),
                expected_line=4,
                expected_start_character=10,
                expected_end_character=15,
            )
        finally:
            await ensure_exit(client)

    asyncio.run(run_test())


def test_references_feature_add_usage_to_definition_and_usage():
    async def run_test() -> None:
        client, _ = await start_initialize_open_typhon_connection_client(
            root_dir=sample_workspace,
            open_file=feature_file,
        )
        # Wait until workspace preload.
        await wait_file_exists(math_file)
        try:
            # 'add' usage in feature.typh
            locations = await request_references(
                client,
                path_to_uri(feature_file),
                line=3,
                character=21,
            )
            assert len(locations) >= 2
            # itself
            assert_has_location(
                locations,
                expected_uri=path_to_uri(feature_file),
                expected_line=3,
                expected_start_character=21,
                expected_end_character=24,
            )
            # Definition pkg/math.typh
            assert_has_location(
                locations,
                expected_uri=path_to_uri(math_file),
                expected_line=0,
                expected_start_character=4,
                expected_end_character=7,
            )
        finally:
            await ensure_exit(client)

    asyncio.run(run_test())
