from pathlib import Path

from src.Typhon.Driver.debugging import debug_print, set_debug_mode
from src.Typhon.Driver.run import run_directory

from .file_check_util import assert_file_stderr, assert_file_stdout


def test_typh_directory():
    set_debug_mode(True)
    test_dir = Path(__file__).parent / "RunDirTest" / "test_module"
    result = run_directory(test_dir, capture_output=True)
    debug_print(f"Test directory: {test_dir} result:\n{result}")
    assert_file_stdout(test_dir / "__main__.typh", result.stdout)
    assert_file_stderr(test_dir / "__main__.typh", result.stderr)
