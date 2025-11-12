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
    for subdir in dir_path.iterdir():
        if subdir.is_dir():
            test_files.extend(gather_directory(subdir))
    return test_files


def gather_test_in_grammar_test_dir(dir_name: str) -> list[str]:
    root = get_project_root()
    dir_path = Path(root) / "test" / "grammar" / dir_name
    if not dir_path.exists():
        return []
    return gather_directory(dir_path)


def gather_tokenizer_tests() -> list[str]:
    return gather_test_in_grammar_test_dir("Tokenizer")


def gather_parser_tests() -> list[str]:
    return gather_test_in_grammar_test_dir("Parser")


def gather_scope_tests() -> list[str]:
    return gather_test_in_grammar_test_dir("Scope")


def gather_utils_tests() -> list[str]:
    return gather_test_in_grammar_test_dir("Utils")


def gather_sourcemap_tests() -> list[str]:
    return gather_test_in_grammar_test_dir("SourceMap")


def run_all_tests() -> int:
    build_grammar()

    # First of all run tokenizer tests.
    if (
        subprocess.run(
            [sys.executable, "-m", "pytest"] + gather_tokenizer_tests()
        ).returncode
        != 0
    ):  # Failed
        return 1

    test_files = (
        gather_parser_tests()
        + gather_scope_tests()
        + gather_utils_tests()
        + gather_sourcemap_tests()
    )
    if not test_files:
        print("No tests were found to run.")
        return 1

    # print(f"Running tests {test_files} in {dir_path}")
    result = subprocess.run(
        [sys.executable, "-m", "pytest"] + test_files,
    )
    return result.returncode


def run_single_grammar_test(test_dir_name: str) -> int:
    build_grammar()
    result = subprocess.run(
        [sys.executable, "-m", "pytest"]
        + gather_test_in_grammar_test_dir(test_dir_name),
    )
    return result.returncode


if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_dir_name = sys.argv[1]
        exit(run_single_grammar_test(test_dir_name))
    else:
        exit(run_all_tests())
