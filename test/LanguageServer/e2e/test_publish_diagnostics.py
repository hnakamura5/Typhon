import asyncio
from typing import Sequence
from lsprotocol import types
from pygls.lsp.client import LanguageClient

from src.Typhon.Driver.debugging import debug_file_write_verbose, debug_verbose_print
from src.Typhon.LanguageServer.utils import canonicalize_uri, path_to_uri
from .utils import (
    EventHandlerAssertTunnel,
    diag_file,
    start_initialize_open_typhon_connection_client,
    type_error_dir,
)


class DiagnosticsAssertion:
    def __init__(self, diagnostics: Sequence[types.Diagnostic]):
        self.diagnostics = diagnostics
        self.current_diagnostic_index = 0

    def assert_next(
        self,
        severity: types.DiagnosticSeverity,
        expected_message_substring: str,
        start_line: int | None = None,
        start_col: int | None = None,
        end_line: int | None = None,
        end_col: int | None = None,
    ):
        diagnostic = self.diagnostics[self.current_diagnostic_index]
        debug_verbose_print(
            f"Asserting diagnostic expecting {self.current_diagnostic_index} with message '{diagnostic.message}' contains '{expected_message_substring}' at ({(start_line, start_col)}-{(end_line, end_col)}) with severity {diagnostic.severity},\n  got message '{diagnostic.message}' with severity {diagnostic.severity} at range {diagnostic.range}"
        )
        assert diagnostic.severity == severity, (
            f"Expected diagnostic severity to be '{severity}', got '{diagnostic.severity}'"
        )
        assert expected_message_substring in diagnostic.message, (
            f"Expected diagnostic message to contain '{expected_message_substring}', got '{diagnostic.message}'"
        )
        assert start_line is None or diagnostic.range.start.line == start_line
        assert start_col is None or diagnostic.range.start.character == start_col
        assert end_line is None or diagnostic.range.end.line == end_line
        assert end_col is None or diagnostic.range.end.character == end_col
        self.current_diagnostic_index += 1

    def assert_end(self):
        assert self.current_diagnostic_index == len(self.diagnostics), (
            f"Expected no more diagnostics, but got {len(self.diagnostics) - self.current_diagnostic_index} more"
        )


def assert_diagnostics(diagnostics: Sequence[types.Diagnostic]):
    da = DiagnosticsAssertion(diagnostics)
    # Assignment type mismatch (let user_id: int = "A")
    da.assert_next(
        types.DiagnosticSeverity.Error,
        'is not assignable to declared type "int"',
        start_line=3,
        start_col=19,
        end_line=3,
        end_col=22,
    )
    # reassignment type mismatch (score = "high")
    da.assert_next(
        types.DiagnosticSeverity.Error,
        'is not assignable to declared type "int"',
        start_line=7,
        start_col=8,
        end_line=7,
        end_col=14,
    )
    # argument type mismatch (add(1, "2"))
    da.assert_next(
        types.DiagnosticSeverity.Error,
        'cannot be assigned to parameter "y"',
        start_line=13,
        start_col=18,
        end_line=13,
        end_col=21,
    )
    # unknown inferred type warning (sum2)
    da.assert_next(
        types.DiagnosticSeverity.Error,
        'Type of "sum2" is unknown',
        start_line=16,
        start_col=4,
        end_line=16,
        end_col=8,
    )
    # missing argument (add(1))
    da.assert_next(
        types.DiagnosticSeverity.Error,
        'Argument missing for parameter "y"',
        start_line=16,
        start_col=11,
        end_line=16,
        end_col=17,
    )
    # return type mismatch (bad_flag)
    da.assert_next(
        types.DiagnosticSeverity.Error,
        'is not assignable to return type "bool"',
        start_line=20,
        start_col=8,
        end_line=20,
        end_col=12,
    )
    # list element type mismatch
    da.assert_next(
        types.DiagnosticSeverity.Error,
        'is not assignable to declared type "list[int]"',
        start_line=24,
        start_col=28,
        end_line=24,
        end_col=31,
    )
    # function type assignment mismatch
    da.assert_next(
        types.DiagnosticSeverity.Error,
        "is not assignable to declared type",
        start_line=28,
        start_col=27,
        end_line=28,
        end_col=52,
    )
    # argument type mismatch (double("10"))
    da.assert_next(
        types.DiagnosticSeverity.Error,
        'cannot be assigned to parameter "n"',
        start_line=29,
        start_col=15,
        end_line=29,
        end_col=19,
    )
    # Data record field/type mismatch
    da.assert_next(
        types.DiagnosticSeverity.Error,
        "is not assignable to declared type",
        start_line=32,
        start_col=32,
        end_line=32,
        end_col=52,
    )
    # Syntax error
    da.assert_next(
        types.DiagnosticSeverity.Error,
        "expected ')'",
        start_line=35,
        start_col=20,
        end_line=35,
        end_col=21,
    )
    da.assert_end()
    debug_verbose_print("All diagnostics assertions passed.")


def test_publish_diagnostics_for_type_errors():
    tunnel = EventHandlerAssertTunnel()

    def on_before_initialize(client: LanguageClient):
        @client.feature(types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)  # type: ignore
        def on_publish_diagnostics(params: types.PublishDiagnosticsParams):
            debug_file_write_verbose(
                f"Received diagnostics for {params.uri}: {params.diagnostics}"
            )
            try:
                assert canonicalize_uri(params.uri) == path_to_uri(diag_file)
                assert len(params.diagnostics) > 0
                # Check that at least one diagnostic has the expected type error message
                assert_diagnostics(params.diagnostics)
                tunnel.finish()
            except Exception as e:
                tunnel.error_occurred(e)

    async def run_test():
        client, _ = await start_initialize_open_typhon_connection_client(
            root_dir=type_error_dir,
            open_file=diag_file,
            on_before_initialize=on_before_initialize,
        )
        await tunnel.waiter(10)
        await client.shutdown_async(None)
        assert tunnel.done, "Expected to receive diagnostics, but timed out waiting."

    asyncio.run(run_test())
