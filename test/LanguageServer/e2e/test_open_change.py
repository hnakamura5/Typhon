import asyncio
from lsprotocol import types
from .utils import start_typhon_connection_client, sample_dir, sample_file


async def run_test():
    client = await start_typhon_connection_client()
    result = await client.initialize_async(
        types.InitializeParams(
            process_id=None,
            root_uri=None,
            capabilities=types.ClientCapabilities(),
        )
    )
    assert result is not None
    assert result.capabilities is not None
    # Open
    client.text_document_did_open(
        types.DidOpenTextDocumentParams(
            text_document=types.TextDocumentItem(
                uri=sample_file.resolve().as_uri(),
                language_id="typhon",
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
                uri=sample_file.resolve().as_uri(),
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
                uri=sample_file.resolve().as_uri(),
            )
        )
    )
    await client.shutdown_async(None)


def test_open_change():
    asyncio.run(run_test())
