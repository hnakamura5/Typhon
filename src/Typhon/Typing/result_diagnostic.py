from dataclasses import dataclass
from enum import Enum
from ..SourceMap.datatype import Range
from ..SourceMap import SourceMap
from pathlib import Path
from ..Driver.utils import canonicalize_path
from ..Driver.debugging import debug_print
from ..Driver.diagnostic import diag_error_file_position, positioned_source_code


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

    def to_string(self, source_map: SourceMap | None = None) -> str:
        message = self.message.replace("\xa0", " ")
        rule = f" ({self.rule})" if self.rule else ""
        file_path = self.file_path
        pos = self.pos
        if source_map is not None:
            file_path = source_map.source_file
            origin_pos = source_map.unparsed_range_to_origin(self.pos)
            if origin_pos is not None:
                pos = origin_pos
                debug_print(
                    f"Mapped diagnostic position from\n    {self.pos}\n  to origin position\n    {pos}"
                )
        return diag_error_file_position(
            self.severity.value,
            file_path,
            pos,
            rule,
            message,
        )


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

    def make_output_message(
        self,
        output_error: bool = True,
        output_warning: bool = True,
        output_info: bool = True,
        output_summary_even_no_diag: bool = True,
        source_maps: dict[str, SourceMap | None] = {},
    ) -> str:
        diags: list[str] = []
        for diag in self.diagnostics:
            if (
                (diag.severity == Severity.ERROR and output_error)
                or (diag.severity == Severity.WARNING and output_warning)
                or (diag.severity == Severity.INFO and output_info)
            ):
                source_map = source_maps.get(
                    canonicalize_path(Path(diag.file_path)), None
                )
                diags.append(diag.to_string(source_map))
                debug_print(
                    f"diag file: {canonicalize_path(Path(diag.file_path))} source_map: {source_map is not None}, source_maps keys: {list(source_maps.keys())}"
                )
                if source_map is not None:
                    position_diag = source_position_diagnostic(diag, source_map)
                    if position_diag:
                        diags.append("")
                        diags.append(position_diag)
        summary = self.summary()
        if not diags:
            return summary if output_summary_even_no_diag else ""
        lines = diags + [summary] if output_summary_even_no_diag else diags
        return "\n".join(lines)


def source_position_diagnostic(
    diag: Diagnostic,
    source_map: SourceMap,
) -> str:
    range_in_source = source_map.unparsed_range_to_origin(diag.pos)
    if range_in_source is None:
        return ""
    source_lines = source_map.source_code.splitlines()
    return positioned_source_code(source_lines, range_in_source)
