from ..SourceMap.datatype import Range


def diag_error_file_position(
    error_type: str,
    file_path: str,
    position: Range,
    source_lines: list[str] | None,
    rule: str | None,
    message: str,
):
    # Range is 0-based, but line numbers displayed are 1-based
    return (
        f"{error_type}: {file_path}:{position.start.line + 1}:{position.start.column + 1}{rule if rule else ''}\n"
        f"  {message}"
    )


def positioned_source_code(
    source_lines: list[str],
    range_in_source: Range,
):
    result = ""
    len_in_digit = len(str(range_in_source.end.line)) + 1
    for line_num in range(range_in_source.start.line, range_in_source.end.line + 1):
        if line_num >= 0 and line_num < len(source_lines):
            result += f"    {line_num + 1:<{len_in_digit}}|  {source_lines[line_num]}\n"
            if (
                range_in_source.start.line == range_in_source.end.line
                and line_num == range_in_source.start.line
            ):
                indicator_line = " " * (range_in_source.start.column + len_in_digit + 7)
                indicator_line += "^" * max(
                    1, range_in_source.end.column - range_in_source.start.column
                )
                result += f"{indicator_line}\n"
    return result
