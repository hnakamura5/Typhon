import sys
import asyncio
import shutil
from dataclasses import dataclass
from typing import Callable
from lsprotocol import types
from pygls.lsp.client import LanguageClient
from pathlib import Path
from Typhon.LanguageServer._utils.path import path_to_uri, canonicalize_uri
from Typhon.Utils.path import get_project_root
from Typhon.Driver.debugging import (
    debug_file_write,
    debug_setup_logging,
    debug_verbose_print,
    is_debug_mode,
    is_debug_verbose,
)

from ..initialize_params_example import initialize_params_example

run_file_dir = get_project_root() / "test" / "Execute" / "RunFileTest"
semtok_file = run_file_dir / "semantic_token_showcase.typh"
hello_file = run_file_dir / "hello.typh"
semtok_file_uri = semtok_file.resolve().as_uri()
hello_file_uri = hello_file.resolve().as_uri()
type_error_dir = get_project_root() / "test" / "Execute" / "TypeErrorTest"
diag_file = type_error_dir / "diagnostic_showcase.typh"

e2e_dir = Path(__file__).resolve().parent
sample_workspace = e2e_dir / "sample_workspace"
main_file = sample_workspace / "main.typh"
feature_file = sample_workspace / "pkg" / "nested" / "feature.typh"
math_file = sample_workspace / "pkg" / "math.typh"


@dataclass(frozen=True)
class SampleWorkspaceFiles:
    root: Path
    main_file: Path
    feature_file: Path
    math_file: Path


def sample_workspace_files(root: Path) -> SampleWorkspaceFiles:
    return SampleWorkspaceFiles(
        root=root,
        main_file=root / "main.typh",
        feature_file=root / "pkg" / "nested" / "feature.typh",
        math_file=root / "pkg" / "math.typh",
    )


def copy_sample_workspace_to_temp() -> SampleWorkspaceFiles:
    temp_root = e2e_dir / "temp"
    temp_sample_workspace = temp_root / "sample_workspace"
    if temp_sample_workspace.exists():
        shutil.rmtree(temp_sample_workspace)
    temp_root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(sample_workspace, temp_sample_workspace)
    return sample_workspace_files(temp_sample_workspace)


def assert_capabilities_equal(
    cl: types.ClientCapabilities, se: types.ServerCapabilities
):
    assert (not cl.text_document or cl.text_document == se.text_document_sync) and (
        not cl.workspace or cl.workspace == se.workspace
    )


async def start_typhon_connection_client() -> LanguageClient:
    client = LanguageClient("typhon-language-client", "v0.1.4")
    debug_options = ["--debug-verbose"] if is_debug_verbose() else []
    async with asyncio.timeout(10):
        await client.start_io(  # type: ignore
            sys.executable, "-m", "Typhon", "lsp", *debug_options
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

    @client.feature(types.WORKSPACE_CONFIGURATION)  # type: ignore
    def on_configuration(params: types.ConfigurationParams):
        debug_verbose_print(f"Received configuration request: {params}")
        # BasedPyright-specific configuration to enable inlay hints for generic types
        result: list[dict[str, object]] = []
        for item in params.items:
            section = item.section
            if section == "basedpyright":
                result.append(
                    {
                        "inlayHints": {
                            "genericTypes": True,
                        }
                    }
                )
                continue
            if section == "basedpyright.analysis":
                result.append(
                    {
                        "inlayHints": {
                            "genericTypes": True,
                        }
                    }
                )
                continue
            result.append({})
        return result

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


def open_file_in_client(client: LanguageClient, file_path: Path):
    file_uri = path_to_uri(file_path)
    client.text_document_did_open(
        types.DidOpenTextDocumentParams(
            text_document=types.TextDocumentItem(
                uri=file_uri,
                language_id="typhon",
                version=1,
                text=file_path.read_text(),
            )
        )
    )


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


async def wait_file_exists(path: Path, timeout_seconds: int = 5):
    waited_seconds = 0
    while not path.exists():
        await asyncio.sleep(0.5)
        waited_seconds += 0.5
        if waited_seconds >= timeout_seconds:
            raise TimeoutError(f"Waited too long for file to exist: {path}")


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
