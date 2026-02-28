import subprocess
import sys
from pathlib import Path

from script.test._util import except_test_options, get_debug_options
from .._util import get_project_root, gather_directory
from ..build import setup


def gather_test_in_grammar_test_dir(filter_paths: list[str]) -> list[str]:
    dir_path = Path(get_project_root()) / "test" / "Grammar"
    return gather_directory(dir_path, filter_paths)


def gather_tokenizer_tests() -> list[str]:
    return gather_test_in_grammar_test_dir(["Tokenizer"])


def gather_parser_tests() -> list[str]:
    return gather_test_in_grammar_test_dir(["Parser"])


def gather_scope_tests() -> list[str]:
    return gather_test_in_grammar_test_dir(["Scope"])


def gather_utils_tests() -> list[str]:
    return gather_test_in_grammar_test_dir(["Utils"])


def gather_sourcemap_tests() -> list[str]:
    return gather_test_in_grammar_test_dir(["SourceMap"])


def run_all_tests() -> int:
    # First of all run tokenizer tests.
    if (
        subprocess.run(
            [sys.executable, "-m", "pytest"]
            + get_debug_options(sys.argv[1:])
            + gather_tokenizer_tests()
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
        [sys.executable, "-m", "pytest"] + get_debug_options(sys.argv[1:]) + test_files,
    )
    return result.returncode


def run_filtered_grammar_test(test_dir_name: list[str]) -> int:
    tests = gather_test_in_grammar_test_dir(test_dir_name)
    if not tests:
        print("No tests were found to run.")
        return 1
    result = subprocess.run(
        [sys.executable, "-m", "pytest"] + get_debug_options(sys.argv[1:]) + tests
    )
    return result.returncode


if __name__ == "__main__":
    setup()
    if len(except_test_options(sys.argv)) > 1:
        test_dir_name = except_test_options(sys.argv[1:])
        exit(run_filtered_grammar_test(test_dir_name))
    else:
        exit(run_all_tests())
