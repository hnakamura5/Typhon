from pathlib import Path


# extract the result written in docstring """<tag>... """
def extract_results(source_code: Path, tag: str) -> str:
    result = ""
    with source_code.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    in_result_block = False

    for line in lines:
        if line.strip().startswith(f'"""{tag}'):
            in_result_block = True
            continue
        elif line.strip().startswith('"""') and in_result_block:
            in_result_block = False
            continue
        if in_result_block:
            result += line
    return result.strip()


# $FILE to be expanded to the source code path
def expand_variables_in_result(source_code: Path, result: str) -> str:
    return result.replace("$FILE", source_code.as_posix())


def print_diff_lines(expected: str, actual: str):
    expected_lines = expected.splitlines()
    actual_lines = actual.splitlines()
    if len(expected_lines) != len(actual_lines):
        print(
            f"Number of lines differ: expected {len(expected_lines)}, got {len(actual_lines)}"
        )
    max_lines = max(len(expected_lines), len(actual_lines))
    for i in range(max_lines):
        exp_line = expected_lines[i] if i < len(expected_lines) else "<no line>"
        act_line = actual_lines[i] if i < len(actual_lines) else "<no line>"
        if exp_line != act_line:
            print(f"Line {i + 1} differs:")
            print(f"Expected: {repr(exp_line)}")
            print(f"Actual:   {repr(act_line)}")


# Assert the expected result in the docstring """result ... """ matches the stdout
def assert_file_stdout(source_code: Path, stdout: str):
    expected_output = extract_results(source_code, "stdout")
    normalized_stdout = "\n".join(stdout.splitlines())
    normalized_expected = expand_variables_in_result(
        source_code, "\n".join(expected_output.splitlines())
    )
    assert normalized_expected == normalized_stdout, (
        f"{source_code.name}: stdout does not match expected.\n"
        f"Expected:\n{normalized_expected}\n\n"
        f"Expected(repr):\n{repr(expected_output)}\n\n"
        f"Got:\n{normalized_stdout}\n\n"
        f"Got(repr):\n{repr(stdout)}"
    )
    if normalized_expected != normalized_stdout:
        print_diff_lines(normalized_expected, normalized_stdout)


def assert_file_stderr(source_code: Path, stderr: str):
    expected_output = extract_results(source_code, "stderr")
    normalized_stderr = "\n".join(stderr.splitlines())
    normalized_expected = expand_variables_in_result(
        source_code, "\n".join(expected_output.splitlines())
    )
    assert normalized_expected == normalized_stderr, (
        f"{source_code.name}: stderr does not match expected.\n"
        f"Expected:\n{normalized_expected}\n\n"
        f"Expected(repr):\n{repr(expected_output)}\n\n"
        f"Got:\n{normalized_stderr}\n\n"
        f"Got(repr):\n{repr(stderr)}"
    )
    if normalized_expected != normalized_stderr:
        print_diff_lines(normalized_expected, normalized_stderr)
