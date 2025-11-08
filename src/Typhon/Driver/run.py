import sys
import os
from pathlib import Path
import subprocess
from dataclasses import dataclass
from ..Grammar.parser import parse_file
from .utils import shorthand, TYPHON_EXT, copy_type, default_output_dir
from ..Transform.transform import transform
from .debugging import is_debug_mode, debug_print, is_debug_verbose
from .translate import translate_directory, translate_file
from ..Driver.type_check import run_type_check


@dataclass
class RunResult:
    stdout: str
    stderr: str
    returncode: int

    @staticmethod
    def from_subprocess_result(
        result: subprocess.CompletedProcess[bytes],
    ) -> "RunResult":
        return RunResult(
            stdout=result.stdout.decode() if result.stdout else "",
            stderr=result.stderr.decode() if result.stderr else "",
            returncode=result.returncode,
        )


def _run_file_by_exec(source: Path, *args: str):
    # TODO: temporal implementation. Switch to save and run style after source map is implemented, to be consistent with directory run.
    debug_print(f"Running source file: {source}")
    ast_tree = parse_file(source.as_posix(), verbose=is_debug_verbose())
    transform(ast_tree)
    code_object = compile(ast_tree, filename=source.as_posix(), mode="exec")
    # Run script as __main__, pass args as sys.argv.
    original_argv = sys.argv
    sys.argv = [source.as_posix()] + list(args)
    try:
        exec(code_object, {"__name__": "__main__", "__file__": source.as_posix()})
    finally:
        sys.argv = original_argv


# Run source file as script.
# Return RunResult containing stdout, stderr only if capture_output is True.
def run_file(source: Path, capture_output: bool, *args: str) -> RunResult:
    temp_output_dir = default_output_dir(source.as_posix())
    temp_output_dir.mkdir(exist_ok=True)
    output_file = temp_output_dir / (source.stem + ".py")
    # Translate source file to temp output file.
    translate_file(source, output_file)
    if not run_type_check(output_file, run_mode=True):
        return RunResult(
            stdout="",
            stderr="",
            returncode=1,
        )
    subprocess_args = [
        sys.executable,
        str(output_file),
    ] + list(args)
    debug_print(f"Running source file: {source} with args: {subprocess_args}")
    if capture_output:
        result = subprocess.run(
            subprocess_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    else:
        result = subprocess.run(
            subprocess_args,
        )
    return RunResult.from_subprocess_result(result)


def run_directory(source_dir: Path, capture_output: bool, *args: str) -> RunResult:
    temp_output_dir = default_output_dir(source_dir.as_posix())
    temp_output_dir.mkdir(exist_ok=True)
    module_output_dir = temp_output_dir / source_dir.name
    # Translate source directory to temp output directory as module.
    translate_directory(source_dir, module_output_dir)
    if not run_type_check(module_output_dir, run_mode=True):
        return RunResult(
            stdout="",
            stderr="",
            returncode=1,
        )
    subprocess_args = [
        sys.executable,
        "-m",
        module_output_dir.name,
    ] + list(args)
    # Set up environment with modified PYTHONPATH
    orig_pythonpath = os.environ.get("PYTHONPATH", "")
    if orig_pythonpath:
        orig_pythonpath = f":{orig_pythonpath}"
    subprocess_env = {
        **dict(os.environ),
        # Override PYTHONPATH to include temp_output_dir
        "PYTHONPATH": str(temp_output_dir.as_posix()) + orig_pythonpath,
    }
    debug_print(
        f"Running source directory: {source_dir} as module {module_output_dir.name} with args: {subprocess_args} env: {subprocess_env}"
    )
    if capture_output:
        result = subprocess.run(
            subprocess_args,
            env=subprocess_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    else:
        result = subprocess.run(
            subprocess_args,
            env=subprocess_env,
        )
    return RunResult.from_subprocess_result(result)


def run(source: str, *args: str):
    """
    Run the given source code.

    Single file as script, or directory as module.

    Usage:
        source: The Typhon source code to run.
        [args]: Additional arguments to pass to the script or module.
    """
    source_path = Path(source)

    debug_print(f"Run source: {source}")

    if source_path.is_file():
        if source_path.suffix != TYPHON_EXT:
            raise ValueError(f"Source file must have '{TYPHON_EXT}' extension.")
        result = run_file(source_path, capture_output=False, *args)
    elif source_path.is_dir():
        result = run_directory(source_path, capture_output=False, *args)
    else:
        raise ValueError("Source must be a valid file or directory path.")
    if result.returncode != 0:
        raise RuntimeError(
            f"Running script {source} failed with return code {result.returncode}."
        )
