from typing import Sequence
import attrs
import enum
import operator
import ast
from functools import reduce
from lsprotocol import types
from pygls.workspace import TextDocument

from ..Typing.pyright import filter_ignore_message
from ..Grammar.typhon_ast import is_internal_name
from ..Grammar.syntax_errors import get_syntax_error_in_module
from ..Grammar.tokenizer_custom import TokenInfo
from ..Driver.debugging import debug_file_write_verbose
from ..SourceMap.ast_match_based_map import MatchBasedSourceMap
from ..SourceMap.datatype import Range, Pos
from ._utils.mapping import range_to_lsp_range, lsp_range_to_range


def map_diagnostic(
    diagnostic: types.Diagnostic,
    source_map: MatchBasedSourceMap | None,
) -> types.Diagnostic:
    # Map the diagnostic position back to the original source code
    mapped_range = (
        source_map.unparsed_range_to_origin_range(lsp_range_to_range(diagnostic.range))
        if source_map
        else None
    )
    if mapped_range is None:
        debug_file_write_verbose(
            f"Could not map diagnostic range {diagnostic.range}, range={lsp_range_to_range(diagnostic.range)} source_map={source_map}"
        )
        mapped_range = Range(
            start=Pos(line=0, column=0),
            end=Pos(line=0, column=0),
        )
    debug_file_write_verbose(
        f"Mapped diagnostic range from {diagnostic.range} to {mapped_range}"
    )
    return types.Diagnostic(
        range=range_to_lsp_range(mapped_range),
        severity=diagnostic.severity,
        code=diagnostic.code,
        code_description=diagnostic.code_description,
        source="Typhon Language Server",
        message=diagnostic.message,
        tags=diagnostic.tags,
        related_information=diagnostic.related_information,
        data=diagnostic.data,
    )


def map_and_add_diagnostics(
    mapped_uri: str | None,
    diagnostic_params: types.PublishDiagnosticsParams,
    module: ast.Module | None,
    source_map: MatchBasedSourceMap | None,
) -> types.PublishDiagnosticsParams:
    syntax_errors = get_syntax_error_in_module(module) if module else None
    diagnostics: list[types.Diagnostic] = []
    debug_file_write_verbose(
        f"Mapping and adding diagnostics for URI {diagnostic_params.uri}, mapped_uri={mapped_uri}, syntax_errors={syntax_errors}, module={module} source_map={source_map}"
    )
    for syntax_error in syntax_errors if syntax_errors else []:
        debug_file_write_verbose(f"Adding syntax error diagnostic: {syntax_error}")
        diagnostics.append(
            types.Diagnostic(
                range=range_to_lsp_range(Range.from_syntax_error(syntax_error)),
                severity=types.DiagnosticSeverity.Error,
                message=str(syntax_error),
                source="Typhon Language Server (Syntax Error)",
            )
        )
    for diagnostic in diagnostic_params.diagnostics:
        debug_file_write_verbose(f"Mapping backend diagnostic: {diagnostic}")
        if filter_ignore_message(diagnostic.message):
            debug_file_write_verbose(
                f"Ignoring diagnostic with message: {diagnostic.message}"
            )
            continue
        mapped_diagnostic = map_diagnostic(
            diagnostic,
            source_map=source_map,
        )
        diagnostics.append(mapped_diagnostic)

    return types.PublishDiagnosticsParams(
        uri=mapped_uri if mapped_uri else diagnostic_params.uri,
        diagnostics=list(
            sorted(
                diagnostics,
                key=lambda diag: (
                    diag.range.start.line,
                    diag.range.start.character,
                    diag.range.end.line,
                    diag.range.end.character,
                ),
            )
        ),
    )
