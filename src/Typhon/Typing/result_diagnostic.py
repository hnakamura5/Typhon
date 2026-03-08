from dataclasses import dataclass
import ast
from enum import Enum
from sys import orig_argv

from Typhon.Grammar.demangle import demangle_text
from ..SourceMap.datatype import Range
from ..SourceMap import SourceMap
from pathlib import Path
from ..Utils.path import canonicalize_path
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
    source_lines: list[str] | None

    def to_string(self) -> str:
        message = self.message.replace("\xa0", " ")
        rule = f" ({self.rule})" if self.rule else ""
        result = diag_error_file_position(
            self.severity.value,
            self.file_path,
            self.pos,
            source_lines=None,
            rule=rule,
            message=message,
        )
        if self.source_lines is not None:
            position_diag = positioned_source_code(self.source_lines, self.pos)
            if position_diag:
                result += "\n\n" + position_diag
        return result

    def demangle(
        self, module: ast.Module | None, source_map: SourceMap | None
    ) -> "Diagnostic":
        file_path = self.file_path
        pos = self.pos
        source_lines = self.source_lines
        if source_map:
            file_path = source_map.source_file
            if origin_pos := source_map.unparsed_range_to_origin_range(self.pos):
                pos = origin_pos
            source_lines = source_map.source_code.splitlines()
        return Diagnostic(
            file_path=file_path,
            severity=self.severity,
            message=demangle_text(
                self.message,
                module,
            ),
            pos=pos,
            rule=self.rule,
            source_lines=source_lines,
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
        output_summary_even_no_diag: bool = False,
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
                diags.append(diag.to_string())
                debug_print(
                    lambda: (
                        f"diag file: {canonicalize_path(Path(diag.file_path))} source_map: {source_map is not None}, source_maps keys: {list(source_maps.keys())}"
                    )
                )
                if source_map is not None and diag.source_lines is None:
                    position_diag = source_position_diagnostic(diag, source_map)
                    debug_print(
                        lambda: (
                            f"Position diagnostic for diag at {diag.pos} with source map: {position_diag}"
                        )
                    )
                    if position_diag:
                        diags.append("")
                        diags.append(position_diag)
        summary = self.summary()
        if not diags:
            return summary if output_summary_even_no_diag else ""
        lines = diags + [summary] if output_summary_even_no_diag else diags
        return "\n".join(lines)

    @staticmethod
    def merge(results: list["TypeCheckResult"]) -> "TypeCheckResult":
        return TypeCheckResult(
            returncode=max(result.returncode for result in results),
            stderr="\n".join(result.stderr for result in results),
            files_analyzed=sum(result.files_analyzed for result in results),
            num_errors=sum(result.num_errors for result in results),
            num_warnings=sum(result.num_warnings for result in results),
            num_info=sum(result.num_info for result in results),
            time_in_sec=sum(result.time_in_sec for result in results),
            diagnostics=[diag for result in results for diag in result.diagnostics],
        )


def source_position_diagnostic(
    diag: Diagnostic,
    source_map: SourceMap,
) -> str:
    range_in_source = source_map.unparsed_range_to_origin_range(diag.pos)
    range_in_source = source_map.unparsed_range_to_origin_range(diag.pos)
    if range_in_source is None:
        return ""
    source_lines = source_map.source_code.splitlines()
    return positioned_source_code(source_lines, range_in_source)
