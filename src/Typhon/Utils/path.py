from pathlib import Path
import os


TYPHON_EXT = ".typh"
TYPHON_TEMP_DIR = ".typhon"
TYPHON_SERVER_TEMP_DIR = ".typhon-server"


def default_output_dir(source: str) -> Path:
    return Path(source).parent / TYPHON_TEMP_DIR


def output_dir_for_workspace(workspace: Path) -> Path:
    return workspace / TYPHON_SERVER_TEMP_DIR


def default_server_output_dir(source: str) -> Path:
    return Path(source).parent / TYPHON_SERVER_TEMP_DIR


def output_dir_for_server_workspace(workspace: Path) -> Path:
    return workspace / TYPHON_SERVER_TEMP_DIR


def prepare_default_output_file(source: Path) -> Path:
    temp_output_dir = default_output_dir(source.as_posix())
    temp_output_dir.mkdir(exist_ok=True)
    output_file = temp_output_dir / (source.stem + ".py")
    return output_file


def prepare_default_server_output_file(source: Path) -> Path:
    temp_output_dir = default_server_output_dir(source.as_posix())
    temp_output_dir.mkdir(exist_ok=True)
    output_file = temp_output_dir / (source.stem + ".py")
    return output_file


def mkdir_and_setup_init_py(dir: Path) -> None:
    if not dir.exists():
        dir.mkdir(parents=True, exist_ok=True)
    init_file = dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text("# Init file_for Typhon module.", encoding="utf-8")


# Canonicalize path to be used as dictionary key.
# For windows, convert all to lower case and resolve.
def canonicalize_path(path: Path) -> str:
    return Path(os.path.normcase(str(path))).resolve().as_posix()


def get_project_root() -> Path:
    current = Path(__file__).resolve()
    for _ in range(10):
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find project root with pyproject.toml")