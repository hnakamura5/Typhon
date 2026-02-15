import asyncio
from lsprotocol import types
from pygls.lsp.client import LanguageClient

from src.Typhon.LanguageServer.utils import path_to_uri
from .utils import (
    run_file_dir,
    semtok_file,
    start_initialize_open_typhon_connection_client,
)


async def request_hover(
    client: LanguageClient,
    uri: str,
    line: int,
    character: int,
) -> types.Hover | None:
    async with asyncio.timeout(10):
        return await client.text_document_hover_async(
            types.HoverParams(
                text_document=types.TextDocumentIdentifier(uri=uri),
                position=types.Position(line=line, character=character),
            )
        )


async def assert_hover(
    client: LanguageClient,
    uri: str,
    line: int,
    character: int,
    expected_start_character: int,
    expected_end_character: int,
) -> None:
    hover = await request_hover(client, uri, line=line, character=character)
    assert hover is not None
    assert hover.contents is not None
    assert hover.range is not None
    assert hover.range.start.line == line
    assert hover.range.end.line == line
    assert hover.range.start.character == expected_start_character
    assert hover.range.end.character == expected_end_character


def test_hover_mapped_range():
    async def run_test():
        target_file_uri = path_to_uri(semtok_file)
        client, _ = await start_initialize_open_typhon_connection_client(
            root_dir=run_file_dir,
            open_file=semtok_file,
        )

        # file parameter declaration: def fun(file: Path)
        await assert_hover(
            client,
            target_file_uri,
            line=10,
            character=9,
            expected_start_character=8,
            expected_end_character=12,
        )

        # file parameter usage: str(file)
        await assert_hover(
            client,
            target_file_uri,
            line=12,
            character=29,
            expected_start_character=27,
            expected_end_character=31,
        )

        # variable usage: my_dir.exists()
        await assert_hover(
            client,
            target_file_uri,
            line=19,
            character=6,
            expected_start_character=4,
            expected_end_character=10,
        )

        await client.shutdown_async(None)

    asyncio.run(run_test())
