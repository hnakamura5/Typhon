from cattrs.converters import Converter


import sys
import json
import logging
import traceback
from typing import Any, Optional, Union
from lsprotocol import types
from cattrs.gen import make_dict_structure_fn
from pygls.lsp.client import LanguageClient
from pygls.protocol import default_converter

from ...Driver.debugging import is_debug_verbose


def client_converter_bugfix(client: LanguageClient) -> None:
    """
    Customize the client's cattrs converter to ignore unknown notebook fields.
    """
    converter: Converter = client.protocol._converter  # type: ignore
    # customize cattrs to ignore unknown fields
    # pyrefly may return newer LSP fields than the local lsprotocol supports.
    # Do NOT override structure hooks (it breaks camelCase<->snake_case mapping),
    # Making the result all None.
    # converter.register_structure_hook_factory(
    #     lambda cls: hasattr(cls, "__attrs_attrs__"),
    #     lambda cls: make_dict_structure_fn(  # type: ignore
    #         cls,
    #         converter,
    #         _cattrs_forbid_extra_keys=False,  # type: ignore
    #     ),
    # )

    # lsprotocol 2025.0.0 lacks a structure hook for the optional notebook filter union.
    # This is required to handle `notebookDocumentSync.notebookSelector[*].notebook`.
    NotebookDocumentFilterOptional = Optional[
        Union[
            str,
            types.NotebookDocumentFilterNotebookType,
            types.NotebookDocumentFilterScheme,
            types.NotebookDocumentFilterPattern,
        ]
    ]

    def _notebook_document_filter_hook(object_: Any, _: type) -> Any:
        if object_ is None:
            return None
        if isinstance(object_, str):
            return object_
        if isinstance(object_, dict):
            if "notebookType" in object_:
                return converter.structure(
                    object_, types.NotebookDocumentFilterNotebookType
                )
            if "scheme" in object_:
                return converter.structure(object_, types.NotebookDocumentFilterScheme)
            if "pattern" in object_:
                return converter.structure(object_, types.NotebookDocumentFilterPattern)
        return converter.structure(object_, types.NotebookDocumentFilterNotebookType)

    converter.register_structure_hook(
        NotebookDocumentFilterOptional, _notebook_document_filter_hook
    )


def create_pyrefly_client() -> LanguageClient:
    client = LanguageClient("pyrefly-language-client", "v0.1.4")

    client_converter_bugfix(client)
    return client


async def start_pyrefly_client(client: LanguageClient):
    original_structure = client.protocol.structure_message
    if is_debug_verbose():

        def leaf_structure_message(data: Any):
            logger = logging.getLogger("pygls.client.pyrefly")
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
        logger = logging.getLogger("pygls.client.pyrefly")
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

    await client.start_io(  # type: ignore
        sys.executable, "-m", "pyrefly", "lsp", "--verbose"
    )


def configure_pyrefly_client_option(
    param: types.InitializeParams,
) -> types.InitializeParams:
    # No special configuration needed for Pyrefly
    return param
