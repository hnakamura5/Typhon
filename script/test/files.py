import subprocess
import sys
from pathlib import Path
from .._util import get_project_root, gather_directory
from ..build import setup


if __name__ == "__main__":
    setup()
    test_files = sys.argv[1:]
    if not test_files:
        print("No tests were found to run.")
        exit(1)

    result = subprocess.run(
        [sys.executable, "-m", "pytest"] + test_files,
    )
    exit(result.returncode)
