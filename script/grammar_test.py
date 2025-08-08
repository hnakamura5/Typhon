import subprocess
import sys
from pathlib import Path
from .util import get_project_root
from .build import build_grammar, type_check


def run_grammar_tests():
    build_grammar()

    root = get_project_root()
    test_py_files = (Path(root) / "test" / "Grammar").glob("*.py")
    test_files = [
        str(file)
        for file in test_py_files
        if file.is_file() and file.name != "__init__.py"
    ]

    if not test_files:
        print("No test files found.")
        return

    # print(f"Running tests {test_files} in {root}/test/Grammar")
    result = subprocess.run(
        [sys.executable, "-m", "pytest"] + test_files,
    )
    return result.returncode


if __name__ == "__main__":
    exit(run_grammar_tests())
