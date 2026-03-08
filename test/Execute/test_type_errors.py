from pathlib import Path
import pytest

from Typhon.Driver.debugging import debug_print
from Typhon.Driver.translate import translate_and_run_type_check_file
from Typhon.Utils.path import prepare_default_output_file
from test.Execute.file_check_util import assert_file_stderr


TYPE_ERROR_TESTS = sorted((Path(__file__).parent / "TypeErrorTest").glob("*.typh"))


@pytest.mark.parametrize("test_file", TYPE_ERROR_TESTS, ids=lambda p: p.name)
def test_typh_type_errors(test_file: Path):
    print(f"Running type error test file: {test_file}")
    output_file = prepare_default_output_file(test_file)
    type_check_result = translate_and_run_type_check_file(test_file, output_file)
    debug_print(
        lambda: f"Type check result for {test_file}: {type_check_result.summary()}"
    )
    assert not type_check_result.is_successful()
    assert type_check_result.num_errors > 0
    assert_file_stderr(test_file, type_check_result.make_output_message())
