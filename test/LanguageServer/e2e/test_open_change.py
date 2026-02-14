import asyncio
from lsprotocol import types
from .utils import start_typhon_connection_client, run_file_dir, semtok_file
from ..initialize_params_example import initialize_params_example


async def run_test():
    client = await start_typhon_connection_client()
    result = await client.initialize_async(initialize_params_example(run_file_dir))
    assert result is not None
    assert result.capabilities is not None
    client.initialized(types.InitializedParams())
    # Open
    client.text_document_did_open(
        types.DidOpenTextDocumentParams(
            text_document=types.TextDocumentItem(
                uri=semtok_file.resolve().as_uri(),
                language_id="typhon",
                version=1,
                text=semtok_file.read_text(),
            )
        )
    )
    # Change
    new_content = semtok_file.read_text() + "\n"
    client.text_document_did_change(
        types.DidChangeTextDocumentParams(
            text_document=types.VersionedTextDocumentIdentifier(
                uri=semtok_file.resolve().as_uri(),
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
                uri=semtok_file.resolve().as_uri(),
            )
        )
    )
    await client.shutdown_async(None)


def test_open_change():
    asyncio.run(run_test())
