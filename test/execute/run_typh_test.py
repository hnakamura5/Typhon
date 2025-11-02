from pathlib import Path
from ...src.Typhon.Driver.run import run_file
from .file_check_util import assert_file_output


# Test to run .typh files in test/RunFileTest directory.
# This is test for translation and run_file functionality.
def test_typh_tests():
    test_dir = Path(__file__).parent / "RunFileTest"
    for test in test_dir.glob("*.typh"):
        result = run_file(test, capture_output=True)
        assert_file_output(test, result.stdout)
