import asyncio
from pathlib import Path

from .utils import (
    ensure_exit,
    start_initialize_open_typhon_connection_client,
)


sample_workspace = Path(__file__).resolve().parent / "sample_workspace"
open_file = sample_workspace / "main.typh"


async def wait_until_paths_exist(
    paths: list[Path], timeout_seconds: float = 10.0
) -> None:
    async with asyncio.timeout(timeout_seconds):
        while True:
            if all(path.exists() for path in paths):
                return
            await asyncio.sleep(0.05)


def test_workspace_preload_translates_all_workspace_typhon_files():
    async def run_test() -> None:
        translated_root = sample_workspace / ".typhon-server"
        if translated_root.exists():  # Clean up from previous test runs
            for file in translated_root.rglob("*"):
                if file.is_file():
                    file.unlink()
            translated_root.rmdir()
        expected_paths = [
            translated_root / "main.py",
            translated_root / "pkg" / "math.py",
            translated_root / "pkg" / "nested" / "feature.py",
        ]
        client, _ = await start_initialize_open_typhon_connection_client(
            root_dir=sample_workspace,
            open_file=open_file,
        )
        try:
            await wait_until_paths_exist(expected_paths)
            for expected_path in expected_paths:
                assert expected_path.exists(), (
                    f"Expected translated file: {expected_path}"
                )
        finally:
            await ensure_exit(client)

    asyncio.run(run_test())
