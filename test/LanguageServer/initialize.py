import sys
import asyncio
from lsprotocol import types
from pygls.lsp.client import LanguageClient


async def start():
    client = LanguageClient("typhon-language-client", "v0.1.3")
    async with asyncio.timeout(10):
        await client.start_io(  # type: ignore
            sys.executable,
            "-m",
            "Typhon",
            "lsp",
        )
        # Exit immediately
        client.exit(None)
        await client.stop()


def test_initialize():
    asyncio.run(start())
