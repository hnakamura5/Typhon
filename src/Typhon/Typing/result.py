from dataclasses import dataclass
from enum import Enum
from ..SourceMap.datatype import Range


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Diagnostic:
    file_path: str
    severity: Severity
    message: str
    pos: Range
    rule: str

    def to_string(self) -> str:
        return diagnostic_to_string(self)


@dataclass
class TypeCheckResult:
    returncode: int
    stderr: str
    files_analyzed: int
    num_errors: int
    num_warnings: int
    num_info: int
    time_in_sec: float
    diagnostics: list[Diagnostic]

    def is_successful(self) -> bool:
        return self.returncode == 0 and self.num_errors == 0

    def summary(self) -> str:
        return f"errors: {self.num_errors}, warnings: {self.num_warnings}, info: {self.num_info}"

    def to_string(
        self,
        output_error: bool = True,
        output_warning: bool = True,
        output_info: bool = True,
        output_summary_even_no_diag: bool = True,
    ) -> str:
        return result_to_string(
            self,
            output_error,
            output_warning,
            output_info,
            output_summary_even_no_diag,
        )


def diagnostic_to_string(diag: Diagnostic) -> str:
    message = diag.message.replace("\xa0", " ")
    rule = f" ({diag.rule})" if diag.rule else ""
    return (
        f"{diag.severity.value}: {diag.file_path}:{diag.pos.start.line}:{diag.pos.start.column}{rule}\n"
        f"  {message}"
    )


def result_to_string(
    result: TypeCheckResult,
    output_error: bool = True,
    output_warning: bool = True,
    output_info: bool = True,
    output_summary_even_no_diag: bool = True,
) -> str:
    diags = [
        diagnostic_to_string(diag)
        for diag in result.diagnostics
        if (
            (diag.severity == Severity.ERROR and output_error)
            or (diag.severity == Severity.WARNING and output_warning)
            or (diag.severity == Severity.INFO and output_info)
        )
    ]
    summary = f"errors: {result.num_errors}, warnings: {result.num_warnings}, info: {result.num_info}"
    if not diags:
        return summary if output_summary_even_no_diag else ""
    lines = diags + [summary] if output_summary_even_no_diag else diags
    return "\n".join(lines)
