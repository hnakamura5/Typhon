import asyncio
from lsprotocol import types
from pygls.lsp.client import LanguageClient

from Typhon.Driver.debugging import debug_verbose_print
from Typhon.LanguageServer.utils import path_to_uri
from .utils import (
    ensure_exit,
    run_file_dir,
    start_initialize_open_typhon_connection_client,
)


inlay_hint_file = run_file_dir / "inlay_hint_showcase.typh"


async def request_inlay_hints(
    client: LanguageClient,
    uri: str,
    end_line: int,
    end_character: int,
) -> list[types.InlayHint]:
    async with asyncio.timeout(10):
        result = await client.text_document_inlay_hint_async(
            types.InlayHintParams(
                text_document=types.TextDocumentIdentifier(uri=uri),
                range=types.Range(
                    start=types.Position(line=0, character=0),
                    end=types.Position(line=end_line, character=end_character),
                ),
            )
        )
    debug_verbose_print(f"Received inlay hint result: {result}")
    assert result is not None
    return list(result)


def test_inlay_hint_response_received_e2e():
    async def run_test() -> None:
        client, _ = await start_initialize_open_typhon_connection_client(
            root_dir=run_file_dir,
            open_file=inlay_hint_file,
        )
        try:
            uri = path_to_uri(inlay_hint_file)
            lines = inlay_hint_file.read_text(encoding="utf-8").splitlines()
            hints = await request_inlay_hints(
                client,
                uri,
                end_line=max(len(lines), 0),
                end_character=0,
            )
            # At this stage we only verify end-to-end response delivery.
            assert isinstance(hints, list) and len(hints) > 0
        finally:
            await ensure_exit(client)

    asyncio.run(run_test())
