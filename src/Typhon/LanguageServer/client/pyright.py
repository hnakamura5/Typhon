import sys
from typing import Any
import logging
import json
import traceback
from cattrs.gen import make_dict_structure_fn
from pygls.lsp.client import LanguageClient

from ...Driver.debugging import is_debug_verbose


_PENDING_SEMANTIC_TOKENS: set[Any] = set()


def create_pyright_client() -> LanguageClient:
    client = LanguageClient("pyright-language-client", "v0.1.3")
    return client


async def start_pyright_client(client: LanguageClient):
    original_structure = client.protocol.structure_message
    logger = logging.getLogger("pygls.client.pyright")

    def leaf_structure_message(data: Any):
        try:
            # Always log responses to semanticTokens/full, even when not in verbose mode.
            # This is critical for diagnosing hangs.
            try:
                if isinstance(data, dict) and "id" in data:
                    msg_id = data.get("id")
                    if msg_id in _PENDING_SEMANTIC_TOKENS:
                        _PENDING_SEMANTIC_TOKENS.discard(msg_id)
                        logger.warning(
                            "semanticTokens/full response received: id=%r keys=%s",
                            msg_id,
                            sorted(list(data.keys())),
                        )
            except Exception:
                # Never let debug logging break message handling.
                pass

            if is_debug_verbose():
                logger.debug(f"DEBUG: Raw data: {json.dumps(data, indent=2)}")
            return original_structure(data)
        except Exception:
            # If a response arrives but fails to deserialize, requests can look like they "hang".
            logger.error(f"DEBUG: Failed to deserialize: {data}")
            logger.error(traceback.format_exc())
            raise

    client.protocol.structure_message = leaf_structure_message

    # Also capture outgoing JSON. `structure_message` only sees inbound data.
    original_send_data = client.protocol._send_data  # type: ignore[attr-defined]

    def leaf_send_data(data: Any):
        try:
            # Track semanticTokens/full request IDs so we can confirm whether
            # a response ever arrives.
            try:
                method = getattr(data, "method", None)
                msg_id = getattr(data, "id", None)
                if method == "textDocument/semanticTokens/full" and msg_id is not None:
                    _PENDING_SEMANTIC_TOKENS.add(msg_id)
                    logger.warning(
                        "semanticTokens/full request sent: id=%r uri=%r",
                        msg_id,
                        getattr(getattr(data, "params", None), "text_document", None)
                        and getattr(getattr(data.params, "text_document"), "uri", None),
                    )
            except Exception:
                pass

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
        "sys.argv = ['basedpyright-langserver', '--stdio']; "
        "sys.exit(main())"
    )
    await client.start_io(  # type: ignore
        sys.executable,
        "-c",
        invoke_script,
    )
