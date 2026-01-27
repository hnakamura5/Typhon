import subprocess
import sys
from pathlib import Path
from ..util import get_project_root, gather_directory
from ..build import setup


def gather_lsp_tests() -> list[str]:
    root = get_project_root()
    dir_path = Path(root) / "test" / "LanguageServer"
    if not dir_path.exists():
        return []
    return gather_directory(dir_path)


def run_all_tests():
    test_files = gather_lsp_tests()
    if not test_files:
        print("No LSP tests were found to run.")
        return 1

    result = subprocess.run(
        [sys.executable, "-m", "pytest"] + test_files,
    )
    return result.returncode


if __name__ == "__main__":
    setup()
    exit(run_all_tests())
