import asyncio
from collections.abc import Sequence

from lsprotocol import types
from pygls.lsp.client import LanguageClient

from Typhon.Driver.debugging import debug_verbose_print
from Typhon.LanguageServer._utils.path import canonicalize_uri, path_to_uri
from .utils import (
    ensure_exit,
    open_file_in_client,
    start_initialize_open_typhon_connection_client,
    sample_workspace,
    main_file,
    feature_file,
)


type DocumentSymbolItem = types.DocumentSymbol | types.SymbolInformation


async def request_document_symbols(
    client: LanguageClient,
    uri: str,
) -> list[DocumentSymbolItem]:
    async with asyncio.timeout(10):
        result = await client.text_document_document_symbol_async(
            types.DocumentSymbolParams(
                text_document=types.TextDocumentIdentifier(uri=uri),
            )
        )
    debug_verbose_print(lambda: f"Received document symbol result: {result}")
    return list(result) if result else []


async def request_workspace_symbols(
    client: LanguageClient,
    query: str,
) -> list[types.SymbolInformation | types.WorkspaceSymbol]:
    async with asyncio.timeout(10):
        result = await client.workspace_symbol_async(
            types.WorkspaceSymbolParams(query=query)
        )
    debug_verbose_print(lambda: f"Received workspace symbol result: {result}")
    return list(result) if result else []


def _flatten_document_symbol_names(symbols: Sequence[DocumentSymbolItem]) -> list[str]:
    names: list[str] = []
    for symbol in symbols:
        if isinstance(symbol, types.DocumentSymbol):
            names.append(symbol.name)
            names.extend(_flatten_document_symbol_names(symbol.children or []))
            continue
        names.append(symbol.name)
    return names


def _find_document_symbol_location(
    symbols: Sequence[DocumentSymbolItem],
    name: str,
) -> tuple[str, types.Range] | None:
    for symbol in symbols:
        if isinstance(symbol, types.DocumentSymbol):
            if symbol.name == name:
                return path_to_uri(feature_file), symbol.selection_range
            if symbol.children:
                nested = _find_document_symbol_location(symbol.children, name)
                if nested is not None:
                    return nested
            continue
        if symbol.name == name:
            return symbol.location.uri, symbol.location.range
    return None


def test_document_symbol_feature_file_mapped_and_demangled():
    async def run_test() -> None:
        client, _ = await start_initialize_open_typhon_connection_client(
            root_dir=sample_workspace,
            open_file=feature_file,
        )
        try:
            symbols = await request_document_symbols(client, path_to_uri(feature_file))
            assert len(symbols) > 0
            names = _flatten_document_symbol_names(symbols)
            assert "greet" in names
            assert "Greeter" in names
            assert "typed_message" in names
            assert all("_typh_" not in name for name in names)

            greet_location = _find_document_symbol_location(symbols, "greet")
            assert greet_location is not None
            greet_uri, greet_range = greet_location
            assert canonicalize_uri(greet_uri) == canonicalize_uri(
                path_to_uri(feature_file)
            )
            assert greet_range.start.line == 2
            assert greet_range.start.character == 4
            assert greet_range.end.character == 9
        finally:
            await ensure_exit(client)

    asyncio.run(run_test())


def _workspace_symbol_location(
    symbol: types.SymbolInformation | types.WorkspaceSymbol,
) -> tuple[str, types.Range | None] | None:
    if isinstance(symbol, types.SymbolInformation):
        return symbol.location.uri, symbol.location.range
    if isinstance(symbol.location, types.Location):
        return symbol.location.uri, symbol.location.range
    # LocationUriOnly does not have range information
    return symbol.location.uri, None


def assert_symbols_contains(
    symbols: Sequence[types.SymbolInformation | types.WorkspaceSymbol],
    name: str,
    expected_uri: str,
    expected_range: types.Range | None = None,
) -> None:
    for symbol in symbols:
        if symbol.name != name:
            continue
        location = _workspace_symbol_location(symbol)
        if location is None:
            continue
        uri, source_range = location
        if canonicalize_uri(uri) != canonicalize_uri(expected_uri):
            continue
        if expected_range is not None and source_range is not None:
            if source_range.start.line != expected_range.start.line:
                continue
            if source_range.start.character != expected_range.start.character:
                continue
            if source_range.end.character != expected_range.end.character:
                continue
        return
    assert False, (
        f"Expected to find symbol with name '{name}' at '{expected_uri}' with range '{expected_range}' in {symbols}, but not found."
    )


def test_workspace_symbol_query_mapped_and_demangled():
    async def run_test() -> None:
        client, _ = await start_initialize_open_typhon_connection_client(
            root_dir=sample_workspace,
            open_file=main_file,
        )
        try:
            open_file_in_client(client, feature_file)
            symbols = await request_workspace_symbols(client, "greet")
            # Sometimes the symbol is not immediately available, wait and retry.
            retry_count = 0
            while len(symbols) == 0 and retry_count < 5:
                symbols = await request_workspace_symbols(client, "greet")
                retry_count += 1
                await asyncio.sleep(0.1)
            assert all("_typh_" not in symbol.name for symbol in symbols)
            expected_uri = canonicalize_uri(path_to_uri(feature_file))
            assert_symbols_contains(
                symbols,
                "greet",
                expected_uri,
                types.Range(
                    start=types.Position(line=2, character=4),
                    end=types.Position(line=2, character=9),
                ),
            )
            assert_symbols_contains(
                symbols,
                "Greeter",
                expected_uri,
                types.Range(
                    start=types.Position(line=8, character=6),
                    end=types.Position(line=8, character=13),
                ),
            )

        finally:
            await ensure_exit(client)

    asyncio.run(run_test())
