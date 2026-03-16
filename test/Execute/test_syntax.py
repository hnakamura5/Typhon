from pathlib import Path
import pytest

from Typhon.Driver.debugging import debug_print
from Typhon.Driver.run import run_file

from .file_check_util import assert_file_stderr, assert_file_stdout


# Test to run .typh files in test/Syntax directory.
# This is test for translation and run_file functionality.
RUN_EXPR_TESTS = sorted((Path(__file__).parent / "Syntax" / "Expr").glob("*.typh"))
RUN_STMT_TESTS = sorted((Path(__file__).parent / "Syntax" / "Stmt").glob("*.typh"))
RUN_MATCH_TESTS = sorted((Path(__file__).parent / "Syntax" / "Match").glob("*.typh"))


@pytest.mark.parametrize("test_file", RUN_EXPR_TESTS, ids=lambda p: p.name)
def test_syntax_expr(test_file: Path):
    result = run_file(test_file, capture_output=True)
    debug_print(f"Test file: {test_file} result:\n{result}")
    assert result.returncode == 0
    assert_file_stdout(test_file, result.stdout)
    assert_file_stderr(test_file, result.stderr)


@pytest.mark.parametrize("test_file", RUN_STMT_TESTS, ids=lambda p: p.name)
def test_syntax_stmt(test_file: Path):
    result = run_file(test_file, capture_output=True)
    debug_print(f"Test file: {test_file} result:\n{result}")
    assert result.returncode == 0
    assert_file_stdout(test_file, result.stdout)
    assert_file_stderr(test_file, result.stderr)

@pytest.mark.parametrize("test_file", RUN_MATCH_TESTS, ids=lambda p: p.name)
def test_syntax_match(test_file: Path):
    result = run_file(test_file, capture_output=True)
    debug_print(f"Test file: {test_file} result:\n{result}")
    assert result.returncode == 0
    assert_file_stdout(test_file, result.stdout)
    assert_file_stderr(test_file, result.stderr)
