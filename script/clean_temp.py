# Clean all temporary directories of Typhon.
# Targets to clean:
# - .typhon
# - .typhon-server
# This recursively cleans up them.

import shutil
from pathlib import Path

from ._util import get_project_root


def clean_temp_dirs():
    project_root = get_project_root()
    for temp_dir in [".typhon", ".typhon-server"]:
        for dir_path in Path(project_root).rglob(temp_dir):
            if dir_path.is_dir():
                print(f"Removing temporary directory: {dir_path}")
                shutil.rmtree(dir_path)


if __name__ == "__main__":
    clean_temp_dirs()
