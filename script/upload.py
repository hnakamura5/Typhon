import sys
import subprocess
import os
from pathlib import Path
from .util import get_project_root
from .build import package_build

# uvx twine upload --repository pypi dist/*


def upload_pypi():
    output = subprocess.run(
        [
            "uv",
            "twine",
            "upload",
            "--repository",
            "pypi",
            f"{get_project_root()}/dist/*",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if output.returncode != 0:
        print("Upload failed:", output.stderr.decode())
        sys.exit(output.returncode)
    print("Upload succeeded.", output.stdout.decode())


if __name__ == "__main__":
    package_build()
    upload_pypi()
