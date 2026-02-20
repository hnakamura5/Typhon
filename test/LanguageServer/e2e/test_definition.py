import asyncio
from pathlib import Path
from collections.abc import Sequence

from lsprotocol import types
from pygls.lsp.client import LanguageClient

from Typhon.Driver.debugging import debug_verbose_print
from Typhon.LanguageServer.utils import canonicalize_uri, path_to_uri
from .utils import (
    ensure_exit,
    start_initialize_open_typhon_connection_client,
    wait_file_exists,
)


sample_workspace = Path(__file__).resolve().parent / "sample_workspace"
main_file = sample_workspace / "main.typh"
feature_file = sample_workspace / "pkg" / "nested" / "feature.typh"
math_file = sample_workspace / "pkg" / "math.typh"


def normalize_locations(
    result: types.Location
    | Sequence[types.Location]
    | Sequence[types.LocationLink]
    | None,
) -> list[types.Location]:
    if result is None:
        return []
    if isinstance(result, types.Location):
        return [result]

    locations: list[types.Location] = []
    for item in result:
        if isinstance(item, types.Location):
            locations.append(item)
        else:
            locations.append(
                types.Location(
                    uri=item.target_uri,
                    range=item.target_selection_range,
                )
            )
    return locations


async def request_definition(
    client: LanguageClient,
    uri: str,
    line: int,
    character: int,
) -> list[types.Location]:
    async with asyncio.timeout(10):
        result = await client.text_document_definition_async(
            types.DefinitionParams(
                text_document=types.TextDocumentIdentifier(uri=uri),
                position=types.Position(line=line, character=character),
            )
        )
    debug_verbose_print(f"Received definition result: {result}")
    return normalize_locations(result)


async def request_type_definition(
    client: LanguageClient,
    uri: str,
    line: int,
    character: int,
) -> list[types.Location]:
    async with asyncio.timeout(10):
        result = await client.text_document_type_definition_async(
            types.TypeDefinitionParams(
                text_document=types.TextDocumentIdentifier(uri=uri),
                position=types.Position(line=line, character=character),
            )
        )
    debug_verbose_print(f"Received type definition result: {result}")
    return normalize_locations(result)


def assert_has_location(
    locations: list[types.Location],
    expected_uri: str,
    expected_line: int,
    expected_start_character: int,
    expected_end_character: int,
) -> None:
    for location in locations:
        if (
            canonicalize_uri(location.uri) == expected_uri
            and location.range.start.line == expected_line
            and location.range.start.character == expected_start_character
            and location.range.end.character == expected_end_character
        ):
            return
    raise AssertionError(
        f"Expected definition location uri={expected_uri}, "
        f"line={expected_line}, start={expected_start_character}, "
        f"end={expected_end_character}, got={locations}"
    )


def test_definition_main_greet_to_feature_definition():
    async def run_test() -> None:
        client, _ = await start_initialize_open_typhon_connection_client(
            root_dir=sample_workspace,
            open_file=main_file,
        )
        # Wait until workspace preload.
        await wait_file_exists(feature_file)
        try:
            locations = await request_definition(
                client,
                path_to_uri(main_file),
                line=4,
                character=10,
            )
            assert len(locations) > 0
            assert_has_location(
                locations,
                expected_uri=path_to_uri(feature_file),
                expected_line=2,
                expected_start_character=4,
                expected_end_character=9,
            )
        finally:
            await ensure_exit(client)

    asyncio.run(run_test())


def test_definition_feature_add_to_math_definition():
    async def run_test() -> None:
        client, _ = await start_initialize_open_typhon_connection_client(
            root_dir=sample_workspace,
            open_file=feature_file,
        )
        # Wait until workspace preload.
        await wait_file_exists(math_file)
        try:
            locations = await request_definition(
                client,
                path_to_uri(feature_file),
                line=3,
                character=21,
            )
            assert len(locations) > 0
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


def test_type_definition_feature_greeter_usage_to_class_definition():
    async def run_test() -> None:
        client, _ = await start_initialize_open_typhon_connection_client(
            root_dir=sample_workspace,
            open_file=feature_file,
        )
        try:
            locations = await request_type_definition(
                client,
                path_to_uri(feature_file),
                line=16,
                character=11,
            )
            assert len(locations) > 0
            assert_has_location(
                locations,
                expected_uri=path_to_uri(feature_file),
                expected_line=8,
                expected_start_character=6,
                expected_end_character=13,
            )
        finally:
            await ensure_exit(client)

    asyncio.run(run_test())
