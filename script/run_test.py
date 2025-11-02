import subprocess
import sys
from pathlib import Path
from .util import get_project_root
from .build import build_grammar, type_check


def run_all_tests() -> int:
    build_grammar()

    test_dir = Path(get_project_root()) / "test" / "execute"
    # First of all run tokenizer tests.
    return subprocess.run(
        [sys.executable, "-m", "pytest", str(test_dir / "run_typh_test.py")],
    ).returncode


if __name__ == "__main__":
    exit(run_all_tests())
