import asyncio

from lsprotocol import types
from pygls.lsp.client import LanguageClient

from .utils import sample_dir, assert_initialize_process, ensure_exit
from src.Typhon.LanguageServer.client.pyright import (
    create_pyright_client,
    start_pyright_client,
)
from src.Typhon.LanguageServer.client.pyrefly import (
    create_pyrefly_client,
    start_pyrefly_client,
)


async def assert_open_change_close_process(
    client: LanguageClient,
) -> None:
    sample_file = sample_dir / "sample1.py"
    uri = sample_file.resolve().as_uri()
    async with asyncio.timeout(10):
        # Open
        client.text_document_did_open(
            types.DidOpenTextDocumentParams(
                text_document=types.TextDocumentItem(
                    uri=uri,
                    language_id="python",
                    version=1,
                    text=sample_file.read_text(),
                )
            )
        )
        # Change
        new_content = sample_file.read_text() + "\n"
        client.text_document_did_change(
            types.DidChangeTextDocumentParams(
                text_document=types.VersionedTextDocumentIdentifier(
                    uri=uri,
                    version=2,
                ),
                content_changes=[
                    types.TextDocumentContentChangeWholeDocument(
                        text=new_content,
                    )
                ],
            )
        )
        # Close
        client.text_document_did_close(
            types.DidCloseTextDocumentParams(
                text_document=types.TextDocumentIdentifier(
                    uri=uri,
                )
            )
        )

        await client.shutdown_async(None)


def test_open_change_close_pyright():
    async def run_test():
        client = create_pyright_client()
        await start_pyright_client(client)
        try:
            await assert_initialize_process(client)
            await assert_open_change_close_process(client)
        finally:
            await ensure_exit(client)

    asyncio.run(run_test())


def test_open_change_close_pyrefly():
    async def run_test():
        client = create_pyrefly_client()
        await start_pyrefly_client(client)
        try:
            await assert_initialize_process(client)
            await assert_open_change_close_process(client)
        finally:
            await ensure_exit(client)

    asyncio.run(run_test())
