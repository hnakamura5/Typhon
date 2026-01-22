import sys
import asyncio
from lsprotocol import types
from pygls.lsp.client import LanguageClient
from pathlib import Path
from src.Typhon.LanguageServer.utils import path_to_uri
from src.Typhon.Driver.utils import get_project_root

sample_dir = Path(__file__).parent / "sample"
sample_file = sample_dir / "sample1.typh"
sample_file_uri = sample_file.resolve().as_uri()


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
    capabilities: types.ClientCapabilities = types.ClientCapabilities(),
    workspace_folders: list[types.WorkspaceFolder] | None = None,
    open_file: Path = sample_file,
) -> LanguageClient:
    client = await start_typhon_connection_client()
    open_file_uri = path_to_uri(open_file)
    if workspace_folders is None:
        workspace_folders = [
            types.WorkspaceFolder(
                uri=path_to_uri(sample_dir),
                name="test",
            )
        ]
    async with asyncio.timeout(10):
        initialize_result = await client.initialize_async(
            types.InitializeParams(
                process_id=None,
                capabilities=capabilities,
                root_uri=path_to_uri(sample_dir),
                workspace_folders=workspace_folders,
            )
        )
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
    return client


async def ensure_exit(client: LanguageClient) -> None:
    try:
        if client.protocol and getattr(client.protocol, "transport", None):
            client.exit(None)
            await client.stop()
    except Exception:
        pass
