from ...Driver.configs import get_language_backend
from pygls.lsp.client import LanguageClient
from lsprotocol import types
from .pyrefly import (
    create_pyrefly_client,
    start_pyrefly_client,
    configure_pyrefly_client_option,
)
from .pyright import (
    create_pyright_client,
    start_pyright_client,
    configure_pyright_client_option,
)


def create_language_client() -> LanguageClient:
    _lsp_backend = get_language_backend()
    match _lsp_backend:
        case "pyrefly":
            return create_pyrefly_client()
        case "pyright":
            return create_pyright_client()


async def start_language_client(client: LanguageClient):
    _lsp_backend = get_language_backend()
    match _lsp_backend:
        case "pyrefly":
            await start_pyrefly_client(client)
        case "pyright":
            await start_pyright_client(client)


def configure_language_client_option(
    param: types.InitializeParams,
) -> types.InitializeParams:
    _lsp_backend = get_language_backend()
    match _lsp_backend:
        case "pyrefly":
            return configure_pyrefly_client_option(param)
        case "pyright":
            return configure_pyright_client_option(param)
