from typing import Callable, cast, ParamSpec
from pathlib import Path
import os


TYPHON_EXT = ".typh"
TYPHON_TEMP_DIR = ".typhon"
TYPHON_SERVER_TEMP_DIR = ".typhon-server"


def shorthand[T](
    normal_name: str,
    normal: T | None,
    shorthand_name: str,
    shorthand: T | None,
    default: T | None = None,
) -> T:
    if normal is not None and shorthand is not None:
        raise ValueError(
            f"Cannot provide both {normal_name} and {shorthand_name}(shorthand) arguments."
        )
    if normal is None:
        if shorthand is None:
            if default is None:
                raise ValueError(
                    f"At least one of {normal_name} or {shorthand_name}(shorthand) must be provided."
                )
            return default
        return shorthand
    return normal


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


def copy_type[**P, T](
    _: Callable[P, T],
) -> Callable[[Callable[..., T]], Callable[P, T]]:
    def decorator(f: Callable[..., T]) -> Callable[P, T]:
        return cast(Callable[P, T], f)

    return decorator


# Canonicalize path to be used as dictionary key.
# For windows, convert all to lower case and resolve.
def canonicalize_path(path: Path) -> str:
    return Path(os.path.normcase(str(path))).resolve().as_posix()
