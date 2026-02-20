import copy
from os import path
from lsprotocol.types import SemanticTokens
from typing import Any, Sequence, override, Protocol, Final
import ast
import traceback
from pathlib import Path
import asyncio

from pygls.lsp.server import LanguageServer as PyglsLanguageServer
from pygls.lsp.client import LanguageClient
from pygls.workspace import TextDocument
from lsprotocol import types


from ..Grammar.tokenizer_custom import TokenInfo, tokenizer_for_string
from ..Grammar.parser import parse_tokenizer
from ..Grammar.unparse_custom import unparse_custom
from ..Transform.transform import transform
from ..Driver.debugging import (
    debug_file_write,
    debug_file_write_verbose,
    is_debug_mode,
)
from ..Utils.path import (
    TYPHON_EXT,
    TYPHON_SERVER_TEMP_DIR,
    output_dir_for_server_workspace,
    default_server_output_dir,
    mkdir_and_setup_init_py,
)
from ..Driver.type_check import write_config
from ..SourceMap.ast_match_based_map import map_from_translated
from ..SourceMap.ast_match_based_map import MatchBasedSourceMap
from .client import create_language_client, start_language_client
from .semantic_tokens import (
    SemanticToken,
    ast_tokens_to_semantic_tokens,
    encode_semantic_tokens,
    semantic_legend,
    map_semantic_tokens,
    semantic_legends_of_initialized_response,
    semantic_token_capabilities,
)
from .diagnostics import (
    map_and_add_diagnostics,
)
from .hover import (
    demangle_hover_names,
    map_hover,
    map_hover_position,
)
from .definition import (
    map_definition_request_position,
    map_definition_result,
    map_type_definition_request_position,
    map_type_definition_result,
)
from .utils import (
    canonicalize_uri,
    uri_to_path,
    path_to_uri,
    clone_and_map_initialize_param,
)


class URIContainer(Protocol):
    uri: str


class URIMappableParams(Protocol):
    text_document: Final[URIContainer]


class LanguageServer(PyglsLanguageServer):
    @override
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        PyglsLanguageServer.__init__(self, *args, **kwargs)  # type: ignore
        # Key URIs is original typhon document URI.
        self.ast_modules: dict[str, ast.Module | None] = {}
        self.token_infos: dict[str, list[TokenInfo]] = {}
        self.semantic_tokens: dict[str, list[SemanticToken]] = {}
        self.semantic_tokens_encoded: dict[str, Sequence[int]] = {}
        self.backend_client: LanguageClient = create_language_client()
        self.mapping: dict[str, MatchBasedSourceMap] = {}
        self.client_semantic_legend: dict[int, str] = {}
        self.translated_uri_to_original_uri: dict[str, str] = {}
        self.preload_task: asyncio.Task[None] | None = None
        self.preloaded_uris: set[str] = set()

    def reload(self, uri: str) -> str | None:
        doc: TextDocument = self.workspace.get_text_document(uri)
        return self.reload_from_source(uri, doc.source, Path(doc.path))

    def reload_from_source(self, uri: str, source: str, doc_path: Path) -> str | None:
        try:
            uri = canonicalize_uri(uri)
            self.translated_uri_to_original_uri.setdefault(
                self.get_translated_file_uri(uri), uri
            )
            debug_file_write(
                f"Reloading document uri={uri} translated uri={self.get_translated_file_uri(uri)} source: {source.strip()[:50]}..."
            )
            tokenizer = tokenizer_for_string(source)
            self.token_infos[uri] = tokenizer.read_all_tokens()
            ast_node = parse_tokenizer(tokenizer)
            if not isinstance(ast_node, ast.Module):
                ast_node = None
            debug_file_write(
                f"Parsed AST for {uri}: {ast.dump(ast_node) if ast_node else 'None'}"
            )
            if ast_node:
                transform(ast_node, ignore_error=True)
            self.ast_modules[uri] = ast_node
            semantic_tokens, encoded = ast_tokens_to_semantic_tokens(
                ast_node, self.token_infos[uri]
            )
            self.semantic_tokens[uri] = semantic_tokens
            self.semantic_tokens_encoded[uri] = encoded
            if not ast_node:
                return None
            # Write translated file to server temporal directory
            translate_file_path, root = self.get_translated_file_path_and_root(doc_path)
            unparsed = unparse_custom(ast_node)
            mapping = map_from_translated(
                ast_node, source, doc_path.as_posix(), unparsed
            )
            if mapping:
                self.mapping[uri] = mapping
            self.setup_container_directories(translate_file_path, root)
            # Setup the server directory
            server_temp_dir = output_dir_for_server_workspace(root) if root else None
            write_config(
                server_temp_dir
                if server_temp_dir
                else default_server_output_dir(doc_path.as_posix())
            )
            with open(translate_file_path, "w", encoding="utf-8") as f:
                debug_file_write(
                    f"Writing translated file to {translate_file_path}, length={len(unparsed)}"
                )
                f.write(unparsed)
            return unparsed
        except Exception as e:
            self.ast_modules[uri] = None
            self.token_infos[uri] = []
            self.semantic_tokens[uri] = []
            self.semantic_tokens_encoded[uri] = []
            debug_file_write(f"Error reloading document {uri}: {e}")
            # dump traceback to debug log
            traceback_str = traceback.format_exc()
            debug_file_write_verbose(f"Traceback:\n{traceback_str}")

    def on_initialize_backend(self, init_result: types.InitializeResult) -> None:
        if semantic_token_provider := init_result.capabilities.semantic_tokens_provider:
            legend = semantic_token_provider.legend
            self.client_semantic_legend = semantic_legends_of_initialized_response(
                legend
            )
            debug_file_write(
                f"Client semantic token legend: {self.client_semantic_legend}"
            )

    def server_workspace_root(self) -> Path | None:
        if self.workspace.root_path:
            return output_dir_for_server_workspace(Path(self.workspace.root_path))
        else:
            return None

    def get_translated_file_path_and_root(self, src: Path) -> tuple[Path, Path | None]:
        """
        Translated path is obtained by replacing workspace root with server temporal directory.
        """
        for uri, folder in self.workspace.folders.items():
            folder_path = uri_to_path(folder.uri)
            try:
                relative_path = src.relative_to(folder_path)
                py_name = relative_path.parent / (relative_path.stem + ".py")
                server_dir = output_dir_for_server_workspace(folder_path)
                return server_dir / py_name, folder_path
            except ValueError:
                continue
        # No workspace, use default path for single file mode
        server_dir = default_server_output_dir(src.as_posix())
        return server_dir / src.name, None

    def get_translated_file_uri(self, src_uri: str) -> str:
        src_path = uri_to_path(src_uri)
        translated_path, _ = self.get_translated_file_path_and_root(src_path)
        uri = path_to_uri(translated_path)
        return uri

    def get_original_file_uri(self, translated_uri: str) -> str | None:
        return self.translated_uri_to_original_uri.get(
            canonicalize_uri(translated_uri), None
        )

    def setup_container_directories(self, file: Path, root: Path | None) -> None:
        """
        Create directory and __init__.py for all parent folders until workspace root.
        """
        if not root:
            return
        workspace_root = Path(root)
        parent = file.parent
        while parent != workspace_root and not parent.exists():
            mkdir_and_setup_init_py(parent)

    def clone_params_map_uri[T: URIMappableParams](self, param: T) -> T:
        cloned_param = copy.deepcopy(param)
        cloned_param.text_document.uri = self.get_translated_file_uri(
            cloned_param.text_document.uri
        )
        return cloned_param

    def _iter_workspace_typhon_files(self) -> list[Path]:
        files: list[Path] = []
        for folder in self.workspace.folders.values():
            folder_path = uri_to_path(folder.uri)
            if not folder_path.exists():
                continue
            for file_path in folder_path.rglob(f"*{TYPHON_EXT}"):
                if TYPHON_SERVER_TEMP_DIR in file_path.parts:
                    continue
                files.append(file_path)
        return files

    def schedule_workspace_preload(self) -> None:
        if self.preload_task and not self.preload_task.done():
            debug_file_write("Workspace preload is already running.")
            return
        self.preload_task = asyncio.create_task(self.preload_workspace())

    async def preload_workspace(self) -> None:
        files = self._iter_workspace_typhon_files()
        if not files:
            debug_file_write(
                f"No Typhon files found for preload in {self.workspace.folders}."
            )
            return
        debug_file_write(f"Starting workspace preload for {len(files)} file(s).")
        for file_path in files:
            await asyncio.sleep(0)
            try:
                uri = canonicalize_uri(path_to_uri(file_path))
                if uri in self.preloaded_uris:
                    continue
                if uri in self.ast_modules:
                    continue
                source = file_path.read_text(encoding="utf-8")
                self.reload_from_source(uri, source, file_path)
                self.preloaded_uris.add(uri)
            except Exception as e:
                debug_file_write(f"Preload failed for {file_path}: {e}")
        debug_file_write("Workspace preload completed.")


server = LanguageServer("typhon-language-server", "v0.1.4")
client = server.backend_client


@server.feature(types.INITIALIZE)
async def lsp_server_initialize(ls: LanguageServer, params: types.InitializeParams):
    try:
        debug_file_write(f"Initializing with params: {params}\n")
        # await start_pyright_client(ls.backend_client)
        await start_language_client(ls.backend_client)
        debug_file_write("Backend client started.\n")
        # Clone the params and modify workspace root to server workspace root.
        cloned_params = clone_and_map_initialize_param(params)
        debug_file_write(f"Initializing backend with cloned params: {cloned_params}\n")
        initialize_result = await ls.backend_client.initialize_async(cloned_params)
        debug_file_write(f"Backend initialize result: {initialize_result}\n")
        ls.on_initialize_backend(initialize_result)
        # Helpful for diagnosing why semanticTokens requests hang.
        try:
            caps = getattr(initialize_result, "capabilities", None)
            stp = getattr(caps, "semantic_tokens_provider", None) if caps else None
            debug_file_write(f"Backend semanticTokensProvider: {stp}")
        except Exception as e:
            debug_file_write(f"Failed to inspect backend capabilities: {e}")
    except Exception as e:
        debug_file_write(f"Error during initialization: {e}")


@server.feature(types.INITIALIZED)
def lsp_client_initialized(ls: LanguageServer, params: types.InitializedParams):
    try:
        debug_file_write(f"Sending initialized notification to backend {params}")
        ls.backend_client.initialized(params)
        ls.schedule_workspace_preload()
    except Exception as e:
        debug_file_write(f"Error during initialized notification: {e}")


@client.feature(types.WORKSPACE_CONFIGURATION)  # type: ignore
async def on_workspace_configuration(
    ls_client: LanguageClient, params: types.ConfigurationParams
):
    debug_file_write(f"Backend requested configuration: {params}")
    try:
        result = await server.workspace_configuration_async(params)
        return result
    except Exception as e:
        debug_file_write(f"Error fetching configuration: {e}")
        # Backends like Pyright expect a list with the same length as params.items.
        return [{}] * len(params.items)


@server.feature(types.TEXT_DOCUMENT_DIAGNOSTIC)
async def on_text_document_diagnostic(
    ls: LanguageServer, params: types.DocumentDiagnosticParams
):
    debug_file_write(f"Server requested diagnostics: {params}")
    # Typhon currently focuses on semantic tokens and does not surface backend diagnostics.
    # Forwarding diagnostics can be expensive and may delay semantic token responses.
    return None


@client.feature(types.CLIENT_REGISTER_CAPABILITY)  # type: ignore
async def on_register_capability(
    ls_client: LanguageClient, params: types.RegistrationParams
):
    debug_file_write(f"Backend requested registerCapability: {params}")
    # Basedpyright may dynamically register pull diagnostics.
    # VS Code then immediately starts issuing `textDocument/diagnostic` requests,
    # which can be expensive and can starve other requests (like semanticTokens).
    # Typhon currently doesn't surface these diagnostics anyway, so drop them.
    filtered = tuple(
        r for r in params.registrations if r.method != "textDocument/diagnostic"
    )
    if len(filtered) != len(params.registrations):
        debug_file_write("Dropping dynamic registration(s) for textDocument/diagnostic")
    if not filtered:
        return None
    return await server.client_register_capability_async(
        types.RegistrationParams(registrations=filtered)
    )


@client.feature(types.CLIENT_UNREGISTER_CAPABILITY)  # type: ignore
async def on_unregister_capability(
    ls_client: LanguageClient, params: types.UnregistrationParams
):
    debug_file_write(f"Backend requested unregisterCapability: {params}")
    filtered = tuple(
        u for u in params.unregisterations if u.method != "textDocument/diagnostic"
    )
    if len(filtered) != len(params.unregisterations):
        debug_file_write(
            "Dropping dynamic unregistration(s) for textDocument/diagnostic"
        )
    if not filtered:
        return None
    return await server.client_unregister_capability_async(
        types.UnregistrationParams(unregisterations=filtered)
    )


@client.feature(types.WORKSPACE_WORKSPACE_FOLDERS)  # type: ignore
async def on_workspace_folders(ls_client: LanguageClient, params: None):
    debug_file_write("Backend requested workspace folders")
    return await server.workspace_workspace_folders_async(None)


@client.feature(types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)  # type: ignore
async def on_publish_diagnostics(
    ls_client: LanguageClient, params: types.PublishDiagnosticsParams
):
    original_uri = server.get_original_file_uri(params.uri)
    module = server.ast_modules.get(original_uri) if original_uri else None
    debug_file_write(
        f"Backend published diagnostics: {params} original_uri={original_uri}   module={module}"
    )
    server.text_document_publish_diagnostics(
        map_and_add_diagnostics(
            original_uri,
            params,
            module,
            server.mapping.get(original_uri, None) if original_uri else None,
        )
    )


# Define handlers for debug logging from backend
@client.feature(types.WINDOW_LOG_MESSAGE)  # type: ignore
async def on_backend_log(ls_client: LanguageClient, log_params: types.LogMessageParams):
    debug_file_write(f"[Backend Log] {log_params.message}")


@server.feature(types.WORKSPACE_DID_CHANGE_WATCHED_FILES)
def did_change_watched_files(
    ls: LanguageServer, params: types.DidChangeWatchedFilesParams
):
    debug_file_write(f"Relaying didChangeWatchedFiles to backend: {params}")
    uri_changed_params = types.DidChangeWatchedFilesParams(
        changes=[
            types.FileEvent(
                uri=ls.get_translated_file_uri(change.uri),
                # uri=ls.get_translated_file_uri(change.uri),
                type=change.type,
            )
            for change in params.changes
        ]
    )
    ls.backend_client.workspace_did_change_watched_files(uri_changed_params)


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: LanguageServer, params: types.DidOpenTextDocumentParams):
    try:
        uri = params.text_document.uri
        unparsed = ls.reload(uri)
        cloned_params = ls.clone_params_map_uri(params)
        cloned_params.text_document.language_id = "python"
        cloned_params.text_document.text = unparsed if unparsed is not None else ""
        debug_file_write(f"Did open called for {uri}, translated to {cloned_params}")
        ls.backend_client.text_document_did_open(cloned_params)
    except Exception as e:
        debug_file_write(f"Error during document open: {e}")


@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: LanguageServer, params: types.DidChangeTextDocumentParams):
    """Parse each document when it is changed"""
    try:
        uri = params.text_document.uri
        ls.reload(uri)
        cloned_params = ls.clone_params_map_uri(params)
        debug_file_write(f"Did change called for {uri}, translated to {cloned_params}")
        ls.backend_client.text_document_did_change(cloned_params)
    except Exception as e:
        debug_file_write(f"Error during document change: {e}")


@server.feature(types.TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL, semantic_legend())
async def semantic_tokens_full(ls: LanguageServer, params: types.SemanticTokensParams):
    uri = canonicalize_uri(params.text_document.uri)
    try:
        debug_file_write(f"Semantic tokens requested {params}")
        cloned_params = ls.clone_params_map_uri(params)
        debug_file_write(f"Translated URI for semantic tokens: {cloned_params}")
        semantic_tokens: (
            SemanticTokens | None
        ) = await ls.backend_client.text_document_semantic_tokens_full_async(
            cloned_params,
        )
        debug_file_write(f"Received semantic tokens: {semantic_tokens}")
        if not semantic_tokens:
            return None
        if (mapping := ls.mapping.get(uri)) is None:
            return None
        mapped = map_semantic_tokens(
            semantic_tokens, mapping, ls.client_semantic_legend
        )
        debug_file_write(f"Mapped semantic tokens: {mapped}")
        return mapped
    except Exception as e:
        debug_file_write(
            f"Error during semantic tokens retrieval: {type(e).__name__}: {e}"
        )
        # Fall back to precomputed rough semantic tokens (encoded).
        if (mapping := ls.mapping.get(uri)) is not None:
            try:
                fallback = encode_semantic_tokens(ls.semantic_tokens.get(uri, []))
                debug_file_write(f"Fallback: {fallback}")
                return map_semantic_tokens(fallback, mapping, ls.client_semantic_legend)
            except Exception as mapping_error:
                debug_file_write(f"Fallback mapping failed: {mapping_error}")
        return encode_semantic_tokens(ls.semantic_tokens.get(uri, []))


@server.feature(types.TEXT_DOCUMENT_HOVER)
async def hover(ls: LanguageServer, params: types.HoverParams):
    uri = canonicalize_uri(params.text_document.uri)
    try:
        debug_file_write(f"Hover requested: {params}")
        cloned_params = ls.clone_params_map_uri(params)
        mapping = ls.mapping.get(uri)
        mapped_position = map_hover_position(params.position, mapping)
        if mapped_position is None:
            debug_file_write(
                "Hover mapping failed for request position. Skipping hover."
            )
            return None
        cloned_params.position = mapped_position
        debug_file_write(f"Translated hover params: {cloned_params}")
        hover_result = await ls.backend_client.text_document_hover_async(cloned_params)
        debug_file_write(f"Received hover result: {hover_result}")
        if hover_result is None:
            return None
        mapped_hover = map_hover(hover_result, mapping)
        if mapped_hover is None:
            debug_file_write("Hover mapping failed for response range. Skipping hover.")
            return None
        return demangle_hover_names(mapped_hover, ls.ast_modules.get(uri))
    except Exception as e:
        debug_file_write(f"Error during hover retrieval: {type(e).__name__}: {e}")
        return None


@server.feature(types.TEXT_DOCUMENT_DEFINITION)
async def definition(ls: LanguageServer, params: types.DefinitionParams):
    uri = canonicalize_uri(params.text_document.uri)
    try:
        debug_file_write(f"Definition requested: {params}")
        cloned_params = ls.clone_params_map_uri(params)
        mapping = ls.mapping.get(uri)
        mapped_position = map_definition_request_position(params.position, mapping)
        if mapped_position is None:
            debug_file_write("Definition mapping failed for request position.")
            return None
        cloned_params.position = mapped_position
        debug_file_write(f"Translated definition params: {cloned_params}")
        definition_result = await ls.backend_client.text_document_definition_async(
            cloned_params
        )
        debug_file_write(f"Received definition result: {definition_result}")
        return map_definition_result(
            definition_result,
            ls.mapping,
            ls.translated_uri_to_original_uri,
        )
    except Exception as e:
        debug_file_write(f"Error during definition retrieval: {type(e).__name__}: {e}")
        return None


@server.feature(types.TEXT_DOCUMENT_TYPE_DEFINITION)
async def type_definition(ls: LanguageServer, params: types.TypeDefinitionParams):
    uri = canonicalize_uri(params.text_document.uri)
    try:
        debug_file_write(f"Type definition requested: {params}")
        cloned_params = ls.clone_params_map_uri(params)
        mapping = ls.mapping.get(uri)
        mapped_position = map_type_definition_request_position(params.position, mapping)
        if mapped_position is None:
            debug_file_write("Type definition mapping failed for request position.")
            return None
        cloned_params.position = mapped_position
        debug_file_write(f"Translated type definition params: {cloned_params}")
        type_definition_result = (
            await ls.backend_client.text_document_type_definition_async(cloned_params)
        )
        debug_file_write(f"Received type definition result: {type_definition_result}")
        return map_type_definition_result(
            type_definition_result,
            ls.mapping,
            ls.translated_uri_to_original_uri,
        )
    except Exception as e:
        debug_file_write(
            f"Error during type definition retrieval: {type(e).__name__}: {e}"
        )
        return None
