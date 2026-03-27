import ast
import copy
from typing import Callable, Sequence

from lsprotocol import types

from ..Transform.name_generator import is_reserved_typh_name
from ..Grammar.demangle import DEMANGLE_FALLBACK_NAME, demangle_text
from ..SourceMap.ast_match_based_map import MatchBasedSourceMap
from ._utils.mapping import (
    lsp_range_to_range,
    map_translated_uri_and_name_range_to_original,
    range_to_lsp_range,
)
from ._utils.path import canonicalize_uri


type DocumentSymbolResult = (
    Sequence[types.DocumentSymbol] | Sequence[types.SymbolInformation] | None
)
type WorkspaceSymbolItem = types.SymbolInformation | types.WorkspaceSymbol
type WorkspaceSymbolResult = Sequence[WorkspaceSymbolItem] | None


def _is_visible_symbol_name(raw_name: str, demangled_name: str) -> bool:
    if is_reserved_typh_name(raw_name):
        return False
    if is_reserved_typh_name(demangled_name):
        return False
    return demangled_name != DEMANGLE_FALLBACK_NAME


def _map_document_symbol(
    symbol: types.DocumentSymbol,
    module: ast.Module | None,
    source_map: MatchBasedSourceMap,
) -> types.DocumentSymbol | None:
    mapped_selection = source_map.unparsed_range_to_origin_range(
        lsp_range_to_range(symbol.selection_range)
    )
    if mapped_selection is None:
        return None
    mapped_range = source_map.unparsed_range_to_origin_range(
        lsp_range_to_range(symbol.range)
    )
    if mapped_range is None:
        mapped_range = mapped_selection
    demangled_name = demangle_text(symbol.name, module)
    if not _is_visible_symbol_name(symbol.name, demangled_name):
        return None

    mapped_symbol = copy.deepcopy(symbol)
    mapped_symbol.name = demangled_name
    if mapped_symbol.detail is not None:
        mapped_symbol.detail = demangle_text(mapped_symbol.detail, module)
    mapped_symbol.range = range_to_lsp_range(mapped_range)
    mapped_symbol.selection_range = range_to_lsp_range(mapped_selection)
    mapped_children: list[types.DocumentSymbol] = []
    for child in symbol.children or []:
        if mapped_child := _map_document_symbol(child, module, source_map):
            mapped_children.append(mapped_child)
    mapped_symbol.children = mapped_children if mapped_children else None
    return mapped_symbol


def _map_symbol_information(
    symbol: types.SymbolInformation,
    mapping: Callable[[str], MatchBasedSourceMap | None],
    translated_uri_to_original_uri: dict[str, str],
    get_module: Callable[[str], ast.Module | None],
) -> types.SymbolInformation | None:
    mapped_location = map_translated_uri_and_name_range_to_original(
        symbol.location.uri,
        symbol.location.range,
        mapping,
        translated_uri_to_original_uri,
    )
    if mapped_location is None:
        return None
    original_uri, mapped_range = mapped_location
    module = get_module(original_uri)
    demangled_name = demangle_text(symbol.name, module)
    if not _is_visible_symbol_name(symbol.name, demangled_name):
        return None

    mapped_symbol = copy.deepcopy(symbol)
    mapped_symbol.name = demangled_name
    if mapped_symbol.container_name is not None:
        mapped_symbol.container_name = demangle_text(
            mapped_symbol.container_name,
            module,
        )
    mapped_symbol.location = types.Location(uri=original_uri, range=mapped_range)
    return mapped_symbol


def _map_location_uri_only_symbol_information(
    symbol: types.WorkspaceSymbol,
    location: types.LocationUriOnly,
    translated_uri_to_original_uri: dict[str, str],
    get_module: Callable[[str], ast.Module | None],
) -> types.WorkspaceSymbol | None:
    original_uri = translated_uri_to_original_uri.get(canonicalize_uri(location.uri))
    if original_uri is None:
        return None
    module = get_module(original_uri)
    demangled_name = demangle_text(symbol.name, module)
    if not _is_visible_symbol_name(symbol.name, demangled_name):
        return None
    mapped_symbol = copy.deepcopy(symbol)
    mapped_symbol.name = demangled_name
    mapped_symbol.location = types.LocationUriOnly(uri=original_uri)
    return mapped_symbol


def _map_workspace_symbol(
    symbol: types.WorkspaceSymbol,
    mapping: Callable[[str], MatchBasedSourceMap | None],
    translated_uri_to_original_uri: dict[str, str],
    get_module: Callable[[str], ast.Module | None],
) -> types.WorkspaceSymbol | None:
    location = symbol.location
    if isinstance(location, types.LocationUriOnly):
        return _map_location_uri_only_symbol_information(
            symbol,
            location,
            translated_uri_to_original_uri,
            get_module,
        )
    mapped_location = map_translated_uri_and_name_range_to_original(
        location.uri,
        location.range,
        mapping,
        translated_uri_to_original_uri,
    )
    if mapped_location is None:
        return None
    original_uri, mapped_range = mapped_location
    module = get_module(original_uri)
    demangled_name = demangle_text(symbol.name, module)
    if not _is_visible_symbol_name(symbol.name, demangled_name):
        return None
    mapped_symbol = copy.deepcopy(symbol)
    mapped_symbol.name = demangled_name
    mapped_symbol.location = types.Location(uri=original_uri, range=mapped_range)
    return mapped_symbol


# TODO: Some symbol is missing, we may be better to compute symbols in Typhon's translator.
def map_document_symbol_result(
    document_symbol_result: DocumentSymbolResult,
    module: ast.Module | None,
    source_map: MatchBasedSourceMap | None,
    mapping: Callable[[str], MatchBasedSourceMap | None],
    translated_uri_to_original_uri: dict[str, str],
    get_module: Callable[[str], ast.Module | None],
) -> DocumentSymbolResult:
    if document_symbol_result is None:
        return None
    if len(document_symbol_result) == 0:
        return []
    if isinstance(document_symbol_result[0], types.DocumentSymbol):
        if source_map is None:
            return []
        mapped_symbols: list[types.DocumentSymbol] = []
        for symbol in document_symbol_result:
            if not isinstance(symbol, types.DocumentSymbol):  # sanity check
                continue
            if mapped_symbol := _map_document_symbol(symbol, module, source_map):
                mapped_symbols.append(mapped_symbol)
        return mapped_symbols

    mapped_informations: list[types.SymbolInformation] = []
    for symbol in document_symbol_result:
        if not isinstance(symbol, types.SymbolInformation):  # sanity check
            continue
        if mapped_symbol := _map_symbol_information(
            symbol,
            mapping,
            translated_uri_to_original_uri,
            get_module,
        ):
            mapped_informations.append(mapped_symbol)
    return mapped_informations


def map_workspace_symbol_result(
    workspace_symbol_result: WorkspaceSymbolResult,
    mapping: Callable[[str], MatchBasedSourceMap | None],
    translated_uri_to_original_uri: dict[str, str],
    get_module: Callable[[str], ast.Module | None],
) -> WorkspaceSymbolResult:
    if workspace_symbol_result is None:
        return None
    if len(workspace_symbol_result) == 0:
        return []

    mapped_symbols: list[WorkspaceSymbolItem] = []
    for symbol in workspace_symbol_result:
        if isinstance(symbol, types.SymbolInformation):
            mapped = _map_symbol_information(
                symbol,
                mapping,
                translated_uri_to_original_uri,
                get_module,
            )
            if mapped is not None:
                mapped_symbols.append(mapped)
            continue
        else:  # WorkspaceSymbol
            mapped = _map_workspace_symbol(
                symbol,
                mapping,
                translated_uri_to_original_uri,
                get_module,
            )
            if mapped is not None:
                mapped_symbols.append(mapped)
    return mapped_symbols
