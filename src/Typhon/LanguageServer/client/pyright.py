import sys
import copy
from typing import Any
import logging
import json
import traceback
from pathlib import Path
from cattrs.gen import make_dict_structure_fn
from pygls.lsp.client import LanguageClient
from lsprotocol import types
import random

from ...Driver.debugging import is_debug_verbose


_PENDING_SEMANTIC_TOKENS: set[Any] = set()


def create_pyright_client() -> LanguageClient:
    client = LanguageClient("pyright-language-client", "v0.1.4")
    return client


async def start_pyright_client(client: LanguageClient):
    original_structure = client.protocol.structure_message
    if is_debug_verbose():

        def leaf_structure_message(data: Any):
            logger = logging.getLogger("pygls.client.pyright")
            try:
                logger.debug(f"DEBUG: Raw data: {json.dumps(data, indent=2)}")
                result = original_structure(data)
                return result
            except Exception as e:
                logger.error(f"DEBUG: Failed to deserialize: {data}")
                logger.error(traceback.format_exc())
                raise e

        client.protocol.structure_message = leaf_structure_message

        # Also capture outgoing JSON. `structure_message` only sees inbound data.
        logger = logging.getLogger("pygls.client.pyright")
        original_send_data = client.protocol._send_data  # type: ignore[attr-defined]

        def leaf_send_data(data: Any):
            try:
                if is_debug_verbose():
                    logger.debug(f"DEBUG: Outgoing data: {data}")
            except Exception:
                logger.error("DEBUG: Failed to serialize outgoing data")
                logger.error(traceback.format_exc())
            return original_send_data(data)

        client.protocol._send_data = leaf_send_data  # type: ignore[attr-defined]

    invoke_script = (
        "import sys; "
        "from basedpyright.langserver import main; "
        "sys.argv = ['basedpyright-langserver', '--stdio', '--max-old-space-size=3072']; "
        "sys.exit(main())"
    )
    # '--cancellationReceive=file:{'private'}'
    await client.start_io(  # type: ignore
        sys.executable,
        "-c",
        invoke_script,
    )
    # basedpyright_langserver_cmd = (
    #     Path(sys.executable).parent
    #     / f"basedpyright-langserver{'' if sys.platform != 'win32' else '.exe'}"
    # )
    # await client.start_io(  # type: ignore
    #     str(basedpyright_langserver_cmd),
    #     "--stdio",
    #     "--max-old-space-size=3072",
    # )


def configure_pyright_client_option(
    param: types.InitializeParams,
) -> types.InitializeParams:
    # Configure Pyright-specific client options if needed.
    # For example, set specific capabilities or initialization options.
    # This is a placeholder for any Pyright-specific configuration.

    # basedpyright/packages/vscode-pyright/src/extension.ts

    # const clientOptions: LanguageClientOptions = {
    #     // Register the server for python source files.
    #     documentSelector: [
    #         { scheme: 'file', language: 'python' },
    #         { scheme: 'untitled', language: 'python' },
    #         { notebook: '*', language: 'python' },
    #     ],
    #     synchronize: {
    #         // Synchronize the setting section to the server.
    #         configurationSection: ['python', 'basedpyright'],
    #     },
    #     connectionOptions: { cancellationStrategy: cancellationStrategy },
    #     middleware: {...},
    #     initializationOptions: {
    #         diagnosticMode: workspace.getConfiguration('basedpyright.analysis').get('diagnosticMode'),
    #         disablePullDiagnostics: workspace.getConfiguration('basedpyright').get('disablePullDiagnostics'),
    #     },
    # }
    cloned_params = copy.deepcopy(param)
    # text_document = result.capabilities.text_document
    text_document = cloned_params.capabilities.text_document
    if text_document:
        # Whitelist
        cloned_params.capabilities.text_document = types.TextDocumentClientCapabilities(
            # semantic_tokens=semantic_token_capabilities().text_document.semantic_tokens,
            synchronization=text_document.synchronization,
            filters=text_document.filters,
            completion=text_document.completion,
            hover=text_document.hover,
            signature_help=text_document.signature_help,
            declaration=text_document.declaration,
            definition=text_document.definition,
            type_definition=text_document.type_definition,
            implementation=text_document.implementation,
            references=text_document.references,
            document_highlight=text_document.document_highlight,
            document_symbol=text_document.document_symbol,
            code_action=text_document.code_action,
            code_lens=text_document.code_lens,
            document_link=text_document.document_link,
            color_provider=text_document.color_provider,
            formatting=text_document.formatting,
            range_formatting=text_document.range_formatting,
            on_type_formatting=text_document.on_type_formatting,
            rename=text_document.rename,
            folding_range=text_document.folding_range,
            selection_range=text_document.selection_range,
            publish_diagnostics=text_document.publish_diagnostics,
            call_hierarchy=text_document.call_hierarchy,
            semantic_tokens=text_document.semantic_tokens,
            linked_editing_range=text_document.linked_editing_range,
            moniker=text_document.moniker,
            type_hierarchy=text_document.type_hierarchy,
            inline_value=text_document.inline_value,
            inlay_hint=text_document.inlay_hint,
            # diagnostic=text_document.diagnostic,  # TODO: This make crashing pyright?. Why?
            inline_completion=text_document.inline_completion,
        )
    workspace = cloned_params.capabilities.workspace
    if workspace:
        cloned_params.capabilities.workspace = types.WorkspaceClientCapabilities(
            apply_edit=workspace.apply_edit,
            workspace_edit=workspace.workspace_edit,
            did_change_configuration=workspace.did_change_configuration,
            did_change_watched_files=workspace.did_change_watched_files,
            symbol=workspace.symbol,
            execute_command=workspace.execute_command,
            # workspace_folders=workspace.workspace_folders,  # TODO: This make hanging pyright
            # workspace_folders=(
            #     types.WorkspaceFoldersServerCapabilities(  # type: ignore
            #         supported=True, change_notifications=True
            #     )
            #     if workspace.workspace_folders
            #     else None
            # ),  # TODO: type mismatch??? This make initialization fail
            configuration=workspace.configuration,
            semantic_tokens=workspace.semantic_tokens,
            code_lens=workspace.code_lens,
            file_operations=workspace.file_operations,
            inline_value=workspace.inline_value,
            inlay_hint=workspace.inlay_hint,
            diagnostics=workspace.diagnostics,
            folding_range=workspace.folding_range,
            text_document_content=workspace.text_document_content,
        )
    return cloned_params
