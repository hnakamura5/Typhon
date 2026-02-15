import sys
import asyncio
from typing import Callable
from lsprotocol import types
from pygls.lsp.client import LanguageClient
from pathlib import Path
from Typhon.LanguageServer.utils import path_to_uri
from Typhon.Utils.path import get_project_root
from Typhon.Driver.debugging import debug_file_write, debug_verbose_print

from ..initialize_params_example import initialize_params_example

run_file_dir = get_project_root() / "test" / "Execute" / "RunFileTest"
semtok_file = run_file_dir / "semantic_token_showcase.typh"
hello_file = run_file_dir / "hello.typh"
semtok_file_uri = semtok_file.resolve().as_uri()
hello_file_uri = hello_file.resolve().as_uri()
type_error_dir = get_project_root() / "test" / "Execute" / "TypeErrorTest"
diag_file = type_error_dir / "diagnostic_showcase.typh"


def assert_capabilities_equal(
    cl: types.ClientCapabilities, se: types.ServerCapabilities
):
    assert (not cl.text_document or cl.text_document == se.text_document_sync) and (
        not cl.workspace or cl.workspace == se.workspace
    )


async def start_typhon_connection_client() -> LanguageClient:
    client = LanguageClient("typhon-language-client", "v0.1.4")
    async with asyncio.timeout(10):
        await client.start_io(  # type: ignore
            sys.executable,
            "-m",
            "Typhon",
            "lsp",
        )
    return client


async def start_initialize_open_typhon_connection_client(
    root_dir: Path = run_file_dir,
    open_file: Path = semtok_file,
    on_before_initialize: Callable[[LanguageClient], None] | None = None,
) -> tuple[LanguageClient, types.InitializeResult]:
    client = await start_typhon_connection_client()
    open_file_uri = path_to_uri(open_file)

    @client.feature(types.CLIENT_REGISTER_CAPABILITY)  # type: ignore
    def on_register_capability(params: types.RegistrationParams):
        debug_verbose_print(f"Received registration request: {params}")

    async with asyncio.timeout(10):
        if on_before_initialize:
            on_before_initialize(client)
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


class EventHandlerAssertTunnel:
    def __init__(self):
        self.done = False
        self.error: Exception | None = None

    def finish(self):
        self.done = True

    def error_occurred(self, error: Exception):
        self.error = error
        self.done = True

    async def waiter(self, second: int = 5):
        waited_seconds = 0
        while not self.done:
            await asyncio.sleep(1)
            waited_seconds += 1
            if waited_seconds >= second:
                raise TimeoutError("Waited too long for the event to occur.")
        if self.error:
            raise self.error
