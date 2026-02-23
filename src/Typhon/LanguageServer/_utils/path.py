import copy
from pathlib import Path

from lsprotocol import types
from pygls import uris

from ...Driver.debugging import debug_file_write, is_debug_mode
from ...Utils.path import output_dir_for_server_workspace
from ..client import configure_language_client_option


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
