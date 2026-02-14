import sys
from pathlib import Path
from ..Typing.pyright import run_pyright, TypeCheckLevel, write_pyright_config
from ..Typing.result_diagnostic import TypeCheckResult


def write_config(
    output_dir: Path, level: TypeCheckLevel = "translate", overwrite: bool = False
):
    write_pyright_config(output_dir, level, overwrite)


def run_type_check(py_file_or_dir: Path, run_mode: bool = False) -> TypeCheckResult:
    # TODO: Now fixed to pyright, support other type checkers later.
    contained_dir = (
        py_file_or_dir.parent if py_file_or_dir.is_file() else py_file_or_dir
    )
    level = "script" if run_mode else "translate"
    write_config(contained_dir, level)
    return run_pyright(py_file_or_dir, level)


def type_check(source: str, level: TypeCheckLevel = "translate") -> None:
    """
    Runs type checking on the given Python source file or directory using Pyright.

    Usage:
        source: The Python source file or directory to be type checked.
        level: The type checking mode. Options are 'translate' for translated code, 'script' for script code. Default is 'translate'. Other levels include 'off', 'basic', 'strict', and 'all', which is Pyright configuration.

    Returns:
        bool: True if type checking passed without errors, False otherwise.
    """
    source_path = Path(source)
    result = run_pyright(source_path, level)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise RuntimeError("Type checking process failed.")
    output_message = result.make_output_message()
    if output_message:
        print(output_message, file=sys.stderr)
