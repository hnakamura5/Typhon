from pathlib import Path
import pytest

from src.Typhon.Driver.debugging import debug_print
from src.Typhon.Driver.run import run_file

from .file_check_util import assert_file_stderr, assert_file_stdout


# Test to run .typh files in test/RunFileTest directory.
# This is test for translation and run_file functionality.
RUN_FILE_TESTS = sorted((Path(__file__).parent / "RunFileTest").glob("*.typh"))


@pytest.mark.parametrize("test_file", RUN_FILE_TESTS, ids=lambda p: p.name)
def test_typh_files(test_file: Path):
    result = run_file(test_file, capture_output=True)
    debug_print(f"Test file: {test_file} result:\n{result}")
    assert result.returncode == 0
    assert_file_stdout(test_file, result.stdout)
    assert_file_stderr(test_file, result.stderr)
