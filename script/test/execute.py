import subprocess
import sys
from pathlib import Path

from ._util import except_test_options, get_debug_options
from .._util import cleanup_temp_dirs, gather_directory, get_project_root
from ..build import setup


def gather_execute_tests() -> list[str]:
    dir_path = Path(get_project_root()) / "test" / "Execute"
    return gather_directory(dir_path, except_test_options(sys.argv[1:]))


def run_all_tests() -> int:
    cleanup_temp_dirs(Path(get_project_root()) / "test" / "Execute")
    test_files = gather_execute_tests()
    if not test_files:
        print("No Execute tests were found to run.")
        return 1

    return subprocess.run(
        [sys.executable, "-m", "pytest"] + get_debug_options(sys.argv[1:]) + test_files
    ).returncode


if __name__ == "__main__":
    setup()
    exit(run_all_tests())
