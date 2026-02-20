import ast
import copy
from pathlib import Path

from lsprotocol import types
from pygls import uris

from ..Driver.debugging import (
    debug_file_write,
    debug_file_write_verbose,
    is_debug_mode,
)
from ..SourceMap.ast_match_based_map import MatchBasedSourceMap
from ..Utils.path import output_dir_for_server_workspace
from .client import configure_language_client_option
from ..SourceMap.datatype import Range, Pos


def uri_to_path(uri: str) -> Path:
    fs_path = uris.to_fs_path(uri)
    if fs_path is None:
        raise ValueError(f"Could not convert URI to path: {uri}")
    return Path(fs_path)


def path_to_uri(path: Path) -> str:
    # Use pathlib's implementation to get canonical Windows file URIs like:
    #   file:///c:/Users/...  (not file:///c%3A/Users/...)
    # Some LSP backends treat these as different URIs and may ignore requests.
    try:
        return path.resolve().as_uri()
    except Exception as e:
        raise ValueError(f"Could not convert path to URI: {path}") from e


def canonicalize_uri(uri: str) -> str:
    return path_to_uri(uri_to_path(uri))


def clone_and_map_initialize_param(
    params: types.InitializeParams,
) -> types.InitializeParams:
    cloned_params = copy.deepcopy(params)
    cloned_params = configure_language_client_option(cloned_params)
    # Modify workspace folders to server workspace folders.
    if params.workspace_folders:
        debug_file_write(f"Workspace folders: {params.workspace_folders}")
        cloned_params.workspace_folders = [
            types.WorkspaceFolder(
                uri=path_to_uri(output_dir_for_server_workspace(uri_to_path(f.uri))),
                name=f.name,
            )
            for f in params.workspace_folders
        ]
    # Setup the deprecated root_uri and root_path as well.
    if params.root_uri:
        cloned_params.root_uri = path_to_uri(
            output_dir_for_server_workspace(uri_to_path(params.root_uri))
        )
        cloned_params.root_uri = None
    if params.root_path:
        # `rootPath` is deprecated but some servers still consult it.
        # Keep it as a native filesystem path on Windows.
        cloned_params.root_path = str(
            output_dir_for_server_workspace(Path(params.root_path))
        )
        cloned_params.root_path = None
    # Debug trace handling
    if is_debug_mode():
        cloned_params.trace = types.TraceValue.Verbose
    return cloned_params


def range_to_lsp_range(r: Range) -> types.Range:
    return types.Range(
        start=pos_to_lsp_position(r.start),
        end=pos_to_lsp_position(r.end),
    )


def lsp_range_to_range(r: types.Range) -> Range:
    return Range(
        start=lsp_position_to_pos(r.start),
        end=lsp_position_to_pos(r.end),
    )


def lsp_position_to_pos(position: types.Position) -> Pos:
    return Pos(line=position.line, column=position.character)


def pos_to_lsp_position(pos: Pos) -> types.Position:
    return types.Position(line=pos.line, character=pos.column)


def to_point_range(position: types.Position) -> Range:
    pos = lsp_position_to_pos(position)
    return Range(start=pos, end=pos)


def map_name_request_position_to_unparsed(
    position: types.Position,
    source_map: MatchBasedSourceMap | None,
    debug_prefix: str,
) -> types.Position | None:
    if source_map is None:
        return None
    mapped_name = source_map.origin_pos_to_unparsed_node(
        lsp_position_to_pos(position),
        ast.Name,
    )
    if not isinstance(mapped_name, ast.Name):
        debug_file_write_verbose(
            f"{debug_prefix} request position is not mapped as ast.Name: {position}"
        )
        return None
    mapped_range = Range.from_ast_node(mapped_name)
    if mapped_range is None:
        return None
    return pos_to_lsp_position(mapped_range.start)


def map_name_unparsed_range_to_original_range(
    original_uri: str,
    source_range: types.Range,
    mapping: dict[str, MatchBasedSourceMap],
) -> types.Range | None:
    result = None
    # When jumping (0, 0), possible to jump top of the file.
    # TODO: More precise way?
    if source_range.start.line == 0 and source_range.start.character == 0:
        result = source_range
    source_map = mapping.get(original_uri)
    if source_map is None:
        return result

    mapped_name = source_map.unparsed_pos_to_origin_node(
        lsp_position_to_pos(source_range.start),
        ast.Name,
    )
    if not isinstance(mapped_name, ast.Name):
        return result
    mapped_range = Range.from_ast_node(mapped_name)
    if mapped_range is None:
        return result
    mapped_position = pos_to_lsp_position(mapped_range.start)
    mapped_back = source_map.origin_pos_to_unparsed_node(
        lsp_position_to_pos(mapped_position),
        ast.Name,
    )
    if not isinstance(mapped_back, ast.Name):
        return result
    return range_to_lsp_range(mapped_range)
