from pathlib import Path
from ...src.Typhon.Driver.run import run_file
from ...src.Typhon.Driver.debugging import debug_print
from .file_check_util import assert_file_stdout


# Test to run .typh files in test/RunFileTest directory.
# This is test for translation and run_file functionality.
def test_typh_tests():
    test_dir = Path(__file__).parent / "RunFileTest"
    for test in test_dir.glob("*.typh"):
        result = run_file(test, capture_output=True)
        debug_print(f"Test file: {test} result:\n{result}")
        assert_file_stdout(test, result.stdout)
