import ast

from lsprotocol import types

from ..Grammar.demangle import demangle_text
from ..Driver.debugging import debug_file_write
from ..SourceMap.ast_match_based_map import MatchBasedSourceMap
from ._utils.mapping import (
    lsp_position_to_pos,
    pos_to_lsp_position,
)


SIGNATURE_HELP_TRIGGER_CHARS = ["("]
SIGNATURE_HELP_RETRIGGER_CHARS = [","]

type SignatureHelpResult = types.SignatureHelp | None


def map_signature_help_request_position(
    position: types.Position,
    source_map: MatchBasedSourceMap | None,
) -> types.Position | None:
    if source_map is None:
        debug_file_write(
            lambda: "Signature help request mapper: source map is not available."
        )
        return None
    original_pos = lsp_position_to_pos(position)
    mapped_pos = source_map.origin_pos_to_unparsed_pos(
        original_pos.col_back(),
        prefer_right=True,
    )
    if mapped_pos is None:
        debug_file_write(
            lambda: f"Signature help request mapper: failed to map position {position}."
        )
        return None
    mapped_position = pos_to_lsp_position(mapped_pos)
    debug_file_write(
        lambda: f"Signature help request mapper: {position} -> {mapped_position}"
    )
    return mapped_position


def _demangle_documentation(
    documentation: str | types.MarkupContent | None,
    module: ast.Module | None,
) -> str | types.MarkupContent | None:
    if documentation is None:
        return None
    if isinstance(documentation, str):
        return demangle_text(documentation, module)
    return types.MarkupContent(
        kind=documentation.kind,
        value=demangle_text(documentation.value, module),
    )


def _demangle_parameter_info(
    param: types.ParameterInformation,
    old_label: str,
    module: ast.Module | None,
) -> types.ParameterInformation:
    label: str | tuple[int, int] = param.label
    if isinstance(label, str):
        label = demangle_text(label, module)
    else:
        # tuple[int, int]: offsets into the signature label.
        # Convert to a demangled string label because demangle_text may not
        # be compositional over concatenation.
        start, end = label
        if start <= len(old_label) and end <= len(old_label):
            label = demangle_text(old_label[start:end], module)
    return types.ParameterInformation(
        label=label,
        documentation=_demangle_documentation(param.documentation, module),
    )


def _demangle_signature_info(
    sig: types.SignatureInformation,
    module: ast.Module | None,
) -> types.SignatureInformation:
    old_label = sig.label
    new_label = demangle_text(old_label, module)
    parameters: list[types.ParameterInformation] | None = None
    if sig.parameters is not None:
        parameters = [
            _demangle_parameter_info(p, old_label, module) for p in sig.parameters
        ]
    return types.SignatureInformation(
        label=new_label,
        documentation=_demangle_documentation(sig.documentation, module),
        parameters=parameters,
        active_parameter=sig.active_parameter,
    )


def _demangle_signature_help(
    result: types.SignatureHelp,
    module: ast.Module | None,
) -> types.SignatureHelp:
    return types.SignatureHelp(
        signatures=[_demangle_signature_info(s, module) for s in result.signatures],
        active_signature=result.active_signature,
        active_parameter=result.active_parameter,
    )


def map_signature_help_result(
    result: SignatureHelpResult,
    module: ast.Module | None,
) -> SignatureHelpResult:
    if result is None:
        return None
    return _demangle_signature_help(result, module)
