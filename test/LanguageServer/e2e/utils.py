import sys
import asyncio
from lsprotocol import types
from pygls.lsp.client import LanguageClient
from pathlib import Path
from src.Typhon.LanguageServer.utils import path_to_uri
from src.Typhon.Driver.utils import get_project_root

from ..initialize_params_example import initialize_params_example

sample_dir = get_project_root() / "test" / "execute" / "RunFileTest"
sample_file = sample_dir / "semantic_token_showcase.typh"
small_sample_file = sample_dir / "hello.typh"
sample_file_uri = sample_file.resolve().as_uri()
small_sample_file_uri = small_sample_file.resolve().as_uri()


def assert_capabilities_equal(
    cl: types.ClientCapabilities, se: types.ServerCapabilities
):
    assert (not cl.text_document or cl.text_document == se.text_document_sync) and (
        not cl.workspace or cl.workspace == se.workspace
    )


async def start_typhon_connection_client() -> LanguageClient:
    client = LanguageClient("typhon-language-client", "v0.1.3")
    async with asyncio.timeout(10):
        await client.start_io(  # type: ignore
            sys.executable,
            "-m",
            "Typhon",
            "lsp",
        )
    return client


async def start_initialize_open_typhon_connection_client(
    root_dir: Path = sample_dir,
    open_file: Path = sample_file,
) -> tuple[LanguageClient, types.InitializeResult]:
    client = await start_typhon_connection_client()
    open_file_uri = path_to_uri(open_file)

    async with asyncio.timeout(10):
        initialize_result = await client.initialize_async(
            initialize_params_example(root_dir)
        )
        client.initialized(types.InitializedParams())
        client.text_document_did_open(
            types.DidOpenTextDocumentParams(
                text_document=types.TextDocumentItem(
                    uri=open_file_uri,
                    language_id="typhon",
                    version=1,
                    text=open_file.read_text(),
                )
            )
        )
    # assert_capabilities_equal(capabilities, initialize_result.capabilities)
    return client, initialize_result


async def ensure_exit(client: LanguageClient) -> None:
    try:
        if client.protocol and getattr(client.protocol, "transport", None):
            client.exit(None)
            await client.stop()
    except Exception:
        pass
