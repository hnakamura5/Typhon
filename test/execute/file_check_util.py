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


# Assert the expected result in the docstring """result ... """ matches the stdout
def assert_file_stdout(source_code: Path, stdout: str):
    expected_output = extract_results(source_code, "stdout")
    normalized_stdout = "\n".join(stdout.splitlines())
    normalized_expected = "\n".join(expected_output.splitlines())
    assert normalized_expected == normalized_stdout, (
        f"{source_code.name}: stdout does not match expected.\n"
        f"Expected:\n{normalized_expected}\n\n"
        f"Expected(repr):\n{repr(expected_output)}\n\n"
        f"Got:\n{normalized_stdout}\n\n"
        f"Got(repr):\n{repr(stdout)}"
    )


def assert_file_stderr(source_code: Path, stderr: str):
    expected_output = extract_results(source_code, "stderr")
    normalized_stderr = "\n".join(stderr.splitlines())
    normalized_expected = "\n".join(expected_output.splitlines())
    assert normalized_expected == normalized_stderr, (
        f"{source_code.name}: stderr does not match expected.\n"
        f"Expected:\n{normalized_expected}\n\n"
        f"Expected(repr):\n{repr(expected_output)}\n\n"
        f"Got:\n{normalized_stderr}\n\n"
        f"Got(repr):\n{repr(stderr)}"
    )
