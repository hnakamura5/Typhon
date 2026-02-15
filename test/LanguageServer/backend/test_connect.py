import asyncio
from Typhon.LanguageServer.client.pyright import (
    create_pyright_client,
    start_pyright_client,
)
from Typhon.LanguageServer.client.pyrefly import (
    create_pyrefly_client,
    start_pyrefly_client,
)


def test_connect_pyright():
    async def run_test():
        client = create_pyright_client()
        await start_pyright_client(client)
        client.exit(None)
        await client.stop()

    asyncio.run(run_test())


def test_connect_pyrefly():
    async def run_test():
        client = create_pyrefly_client()
        await start_pyrefly_client(client)
        client.exit(None)
        await client.stop()

    asyncio.run(run_test())
