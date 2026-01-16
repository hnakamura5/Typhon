from .utils import copy_type
from typing import BinaryIO, override
from pathlib import Path
import logging


_debug = False
_debug_verbose = False
_debug_first_error = False
_debug_log_file: Path | None = None


def set_debug_mode(debug: bool):
    global _debug
    _debug = debug


def set_debug_verbose(verbose: bool):
    global _debug_verbose
    _debug_verbose = verbose
    if verbose:
        set_debug_mode(True)


def set_debug_first_error(first_error: bool):
    global _debug_first_error
    _debug_first_error = first_error


def set_debug_log_file(
    log_file: str | None, verbose: bool = False, append: bool = False
):
    global _debug_log_file
    _debug_log_file = Path(log_file) if log_file else None
    if _debug_log_file is not None:
        if verbose:
            set_debug_verbose(True)
        set_debug_mode(True)
        mode = "a" if append else "w"
        with _debug_log_file.open(mode) as f:
            f.write("=== Typhon Debug Log ===\n")


def is_debug_mode() -> bool:
    return _debug


def is_debug_verbose() -> bool:
    return _debug_verbose


# Whether to stop transformation at the first error encountered.
def is_debug_first_error() -> bool:
    return _debug_first_error


def get_debug_log_file() -> Path | None:
    return _debug_log_file


@copy_type(print)
def debug_print(*arg, **kwargs) -> None:  # type: ignore
    if _debug:
        if _debug_log_file is not None:
            with _debug_log_file.open("a") as log_file:
                print(*arg, file=log_file, **kwargs)  # type: ignore
        else:
            print(*arg, **kwargs)  # type: ignore


@copy_type(print)
def debug_verbose_print(*arg, **kwargs) -> None:  # type: ignore
    if _debug_verbose:
        if _debug_log_file is not None:
            with _debug_log_file.open("a") as log_file:
                print(*arg, file=log_file, **kwargs)  # type: ignore
        else:
            print(*arg, **kwargs)  # type: ignore


@copy_type(print)
def debug_file_write(*arg, **kwargs) -> None:  # type: ignore
    if _debug:
        if _debug_log_file is not None:
            with _debug_log_file.open("a") as log_file:
                print(*arg, file=log_file, **kwargs)  # type: ignore


@copy_type(print)
def debug_file_write_verbose(*arg, **kwargs) -> None:  # type: ignore
    if _debug_verbose:
        if _debug_log_file is not None:
            with _debug_log_file.open("a") as log_file:
                print(*arg, file=log_file, **kwargs)  # type: ignore


type ReadableBuffer = bytes | bytearray | memoryview


# Bypass binaryIO class stdio to log
class BinaryIOLogger(BinaryIO):
    def __init__(self, pipe: BinaryIO):
        self._pipe = pipe

    def fileno(self) -> int:
        return self._pipe.fileno()

    def isatty(self) -> bool:
        return self._pipe.isatty()

    def write(self, data: ReadableBuffer) -> int:
        # Log the data being written
        if _debug_log_file is not None:
            with _debug_log_file.open("a") as log_file:
                log_file.write(f"Writing {data}\n")
                log_file.flush()
        return self._pipe.write(data)

    def flush(self) -> None:
        self._pipe.flush()

    def read(self, n: int = -1) -> bytes:
        data = self._pipe.read(n)
        if _debug_log_file is not None:
            with _debug_log_file.open("a") as log_file:
                log_file.write(f"Read {data}\n")
                log_file.flush()
        return data

    def close(self) -> None:
        if _debug_log_file is not None:
            with _debug_log_file.open("a") as log_file:
                log_file.write("Closing pipe.\n")
                log_file.flush()
        self._pipe.close()

    @override
    def readline(self, limit: int = -1) -> bytes:
        line = self._pipe.readline(limit)
        if _debug_log_file is not None:
            with _debug_log_file.open("a") as log_file:
                log_file.write(f"Read line {line}\n")
                log_file.flush()
        return line


def get_project_root() -> Path:
    current = Path(__file__).resolve()
    for _ in range(10):
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find project root with pyproject.toml")


def debug_setup_logging(verbose: bool = True, append: bool = True) -> None:
    set_debug_log_file(
        str(get_project_root() / "private" / "server.log"),
        verbose=verbose,
        append=append,
    )
    set_debug_mode(True)
    set_debug_verbose(verbose)
    if (log_file := get_debug_log_file()) is not None:
        logging.basicConfig(
            filename=log_file,
            level=logging.DEBUG,
            filemode="w",
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
