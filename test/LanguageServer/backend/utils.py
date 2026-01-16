from lsprotocol.types import InitializeResult


import asyncio
from pathlib import Path

from lsprotocol import types
from pygls.lsp.client import LanguageClient

sample_dir = Path(__file__).parent / "sample"
sample_dir_uri = sample_dir.resolve().as_uri()


def assert_capabilities_equal(
    cl: types.ClientCapabilities, se: types.ServerCapabilities
):
    assert cl.text_document == se.text_document_sync


async def assert_initialize_process(
    client: LanguageClient,
    capabilities: types.ClientCapabilities = types.ClientCapabilities(),
) -> types.ServerCapabilities:
    try:
        params = types.InitializeParams(
            process_id=None,
            workspace_folders=[
                types.WorkspaceFolder(
                    uri=sample_dir.resolve().as_uri(),
                    name="sample",
                )
            ],
            capabilities=capabilities,
        )
        # Wait for the initialize response with a timeout
        async with asyncio.timeout(10):
            response: InitializeResult = await client.initialize_async(params)

        print(f"Initialization response: {response}\n")

        assert response is not None
        assert response.capabilities is not None

        client.initialized(types.InitializedParams())
        print("Initialization finished.\n")
        return response.capabilities
    except Exception as e:
        assert False, f"Initialization failed: {e}"


async def ensure_exit(client: LanguageClient) -> None:
    try:
        if client.protocol and getattr(client.protocol, "transport", None):
            client.exit(None)
            await client.stop()
    except Exception:
        pass
