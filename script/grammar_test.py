import subprocess
import sys
from pathlib import Path
from .util import get_project_root
from .build import build_grammar, type_check


def gather_directory(dir_path: Path) -> list[str]:
    test_py_files = dir_path.glob("*.py")
    test_files = [
        str(file)
        for file in test_py_files
        if file.is_file() and file.name != "__init__.py"
    ]
    return test_files


def gather_grammar_tests() -> list[str]:
    root = get_project_root()
    grammar_test_dir = Path(root) / "test" / "Grammar"
    if not grammar_test_dir.exists():
        print(f"Grammar test directory {grammar_test_dir} does not exist.")
        return []
    return gather_directory(grammar_test_dir)


def gather_scope_tests() -> list[str]:
    root = get_project_root()
    scope_test_dir = Path(root) / "test" / "Scope"
    if not scope_test_dir.exists():
        print(f"Scope test directory {scope_test_dir} does not exist.")
        return []
    return gather_directory(scope_test_dir)


def run_all_tests() -> int:
    build_grammar()
    test_files = gather_grammar_tests() + gather_scope_tests()
    if not test_files:
        print("No tests were found to run.")
        return 1

    # print(f"Running tests {test_files} in {dir_path}")
    result = subprocess.run(
        [sys.executable, "-m", "pytest"] + test_files,
    )
    return result.returncode


if __name__ == "__main__":
    exit(run_all_tests())
