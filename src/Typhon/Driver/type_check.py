import sys
from pathlib import Path
import subprocess
from .debugging import debug_print


def type_check(py_file_or_dir: Path, strict: bool = False) -> bool:
    output = subprocess.run(
        [sys.executable, "-m", "basedpyright", str(py_file_or_dir)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print(output.stdout.decode())
    if len(output.stderr) > 0:
        return False
    return True
