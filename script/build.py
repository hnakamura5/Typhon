import sys
import subprocess
import os
from pathlib import Path
from ._util import get_project_root


def build_grammar():
    output = subprocess.run(
        [
            sys.executable,
            "-m",
            "pegen",
            f"{get_project_root()}/src/Typhon/Grammar/typhon.gram",
            "-o",
            f"{get_project_root()}/src/Typhon/Grammar/_typhon_parser.py",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if output.returncode != 0:
        print("Error building grammar:", output.stderr.decode())
        sys.exit(output.returncode)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "format",
            f"{get_project_root()}/src/Typhon/Grammar/_typhon_parser.py",
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _type_check(source_file: str) -> bool:
    output = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyright",
            source_file,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if output.returncode != 0:
        print("Type check failed:", output.stderr.decode())
        return False
    print("Type check passed.", output.stdout.decode())
    return True


def install_editable_package():
    output = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-e",
            f"{get_project_root()}/.",
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print(output.stdout.decode())
    print(output.stderr.decode())


def clean_grammar():
    os.remove(f"{get_project_root()}/src/Typhon/Grammar/_typhon_parser.py")


def package_build():
    clean_build()
    output = subprocess.run(
        [
            "uv",
            "build",
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print(output.stdout.decode())
    print(output.stderr.decode())


def clean_build():
    dist_path = Path(get_project_root()) / "dist"
    if dist_path.exists() and dist_path.is_dir():
        for item in dist_path.iterdir():
            item.unlink()


def setup() -> None:
    build_grammar()
    install_editable_package()


if __name__ == "__main__":
    build_grammar()
    package_build()
    install_editable_package()
