import asyncio
from lsprotocol import types
from .utils import start_typhon_connection_client


def test_connect():
    async def run_test():
        client = await start_typhon_connection_client()
        # Exit immediately
        client.exit(None)
        await client.stop()

    asyncio.run(run_test())


def test_initialize():
    async def run_test():
        client = await start_typhon_connection_client()
        result = await client.initialize_async(
            types.InitializeParams(
                process_id=None,
                root_uri=None,
                capabilities=types.ClientCapabilities(),
            )
        )
        assert result is not None
        assert result.capabilities is not None
        # Exit immediately
        client.exit(None)
        await client.stop()

    asyncio.run(run_test())
