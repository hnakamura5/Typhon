from pathlib import Path
from ...src.Typhon.Driver.run import run_file, run_directory
from ...src.Typhon.Driver.debugging import debug_print
from .file_check_util import assert_file_stdout, assert_file_stderr


# Test to run .typh files in test/RunFileTest directory.
# This is test for translation and run_file functionality.
def test_typh_files():
    test_dir = Path(__file__).parent / "RunFileTest"
    for test in test_dir.glob("*.typh"):
        result = run_file(test, capture_output=True)
        debug_print(f"Test file: {test} result:\n{result}")
        assert_file_stdout(test, result.stdout)
        assert_file_stderr(test, result.stderr)


def test_typh_directory():
    test_dir = Path(__file__).parent / "RunDirTest" / "test_module"
    result = run_directory(test_dir, capture_output=True)
    debug_print(f"Test directory: {test_dir} result:\n{result}")
    assert_file_stdout(test_dir / "__main__.typh", result.stdout)
    assert_file_stderr(test_dir / "__main__.typh", result.stderr)
