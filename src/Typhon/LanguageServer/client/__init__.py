from ...Driver.configs import get_language_backend
from pygls.lsp.client import LanguageClient
from .pyrefly import create_pyrefly_client, start_pyrefly_client
from .pyright import create_pyright_client, start_pyright_client


def create_language_client() -> LanguageClient:
    _lsp_backend = get_language_backend()
    if _lsp_backend == "pyrefly":
        return create_pyrefly_client()
    elif _lsp_backend == "pyright":
        return create_pyright_client()


async def start_language_client(client: LanguageClient):
    _lsp_backend = get_language_backend()
    if _lsp_backend == "pyrefly":
        await start_pyrefly_client(client)
    elif _lsp_backend == "pyright":
        await start_pyright_client(client)
