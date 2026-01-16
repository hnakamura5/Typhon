import asyncio
from pathlib import Path

from src.Typhon.LanguageServer.client.pyright import (
    create_pyright_client,
    start_pyright_client,
)
from src.Typhon.LanguageServer.client.pyrefly import (
    create_pyrefly_client,
    start_pyrefly_client,
)
from .utils import assert_initialize_process


def test_initialize_pyright():
    async def run_test():
        client = create_pyright_client()
        await start_pyright_client(client)
        try:
            await assert_initialize_process(client)
        finally:
            try:
                if client.protocol and getattr(client.protocol, "transport", None):
                    client.exit(None)
                    await client.stop()
            except Exception:
                pass

    asyncio.run(run_test())


def test_initialize_pyrefly():
    async def run_test():
        client = create_pyrefly_client()
        await start_pyrefly_client(client)
        try:
            await assert_initialize_process(client)
        finally:
            try:
                if client.protocol and getattr(client.protocol, "transport", None):
                    client.exit(None)
                    await client.stop()
            except Exception:
                pass

    asyncio.run(run_test())
