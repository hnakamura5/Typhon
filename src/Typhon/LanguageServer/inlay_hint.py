import ast
import copy
import re
from collections.abc import Sequence

from lsprotocol import types

from ..Transform.name_generator import get_final_name
from ..Driver.debugging import debug_file_write_verbose
from ..SourceMap.ast_match_based_map import MatchBasedSourceMap
from ..SourceMap.datatype import Pos, Range
from ._utils.demangle import (
    demangle_text,
)
from ._utils.mapping import (
    lsp_position_to_pos,
    pos_to_lsp_position,
    lsp_range_to_range,
    range_to_lsp_range,
)


type InlayHintResult = Sequence[types.InlayHint] | None


def map_inlay_hint_request_params(
    params: types.InlayHintParams,
    source_map: MatchBasedSourceMap | None,
) -> types.InlayHintParams | None:
    if source_map is None:
        return None
    mapped_start = source_map.origin_pos_to_unparsed_pos(
        lsp_position_to_pos(params.range.start),
        prefer_right=False,
    )
    if mapped_start is None:
        # Set to beginning of the file
        mapped_start = Pos(line=0, column=0)
    mapped_end = source_map.origin_pos_to_unparsed_pos(
        lsp_position_to_pos(params.range.end),
        prefer_right=True,
    )
    if mapped_end is None:
        # Set to end of the file
        mapped_end = source_map.unparsed_code_end_pos()
    # TODO: Possible performance issue of range mapping is too large if begin and end are applied.
    mapped_params = copy.deepcopy(params)
    # Compute the hints inside the range.
    mapped_params.range = range_to_lsp_range(Range(start=mapped_start, end=mapped_end))
    return mapped_params


def _map_inlay_hint_position_for_param(
    position: types.Position,
    source_map: MatchBasedSourceMap,
) -> types.Position | None:
    # Small hack: position points begin of the paramter expr (hint comes for positional parameters). One character back should be '(' or ',' token, which should be a direct part of the Call node.
    pos = lsp_position_to_pos(position)
    call_node = source_map.unparsed_pos_to_unparsed_node(pos.col_back(), ast.Call)
    debug_file_write_verbose(
        f"Mapping inlay hint parameter hint position {position}, got unparsed node {ast.dump(call_node) if call_node is not None else None}"
    )
    if isinstance(call_node, ast.Call):
        for arg in call_node.args:
            if arg_range := Range.from_ast_node(arg):
                if arg_range.contains(pos):
                    mapped_arg_node = source_map.unparsed_node_to_origin_node(arg)
                    if mapped_arg_node is not None:
                        if mapped_range := Range.from_ast_node(mapped_arg_node):
                            return pos_to_lsp_position(mapped_range.start)
                    break
    return None


InlayHintLabel = str | Sequence[types.InlayHintLabelPart]
InlayHintTooltip = str | types.MarkupContent | None


def _demangle_inlay_hint_tooltip(
    tooltip: InlayHintTooltip,
    module: ast.Module | None,
) -> InlayHintTooltip:
    if isinstance(tooltip, str):
        return demangle_text(tooltip, module)
    if isinstance(tooltip, types.MarkupContent):
        return types.MarkupContent(
            kind=tooltip.kind,
            value=demangle_text(tooltip.value, module),
        )
    return tooltip


def _demangle_inlay_hint_label(
    label: InlayHintLabel,
    module: ast.Module | None,
) -> InlayHintLabel:
    if isinstance(label, str):
        return demangle_text(label, module)

    result: list[types.InlayHintLabelPart] = []
    for part in label:
        part_tooltip = part.tooltip
        if isinstance(part_tooltip, str):
            part_tooltip = demangle_text(part_tooltip, module)
        elif isinstance(part_tooltip, types.MarkupContent):
            part_tooltip = types.MarkupContent(
                kind=part_tooltip.kind,
                value=demangle_text(part_tooltip.value, module),
            )
        result.append(
            types.InlayHintLabelPart(
                value=demangle_text(part.value, module),
                tooltip=part_tooltip,
                location=part.location,
                command=part.command,
            )
        )
    return result


def _adjust_final_type_adhoc_form(
    source_map: MatchBasedSourceMap, name_node: ast.Name, label: InlayHintLabel
) -> tuple[ast.Name, InlayHintLabel]:
    if (
        name_node.id == get_final_name()
        and isinstance(label, str)
        and label.startswith("[")
    ):
        # Ad hoc hook for Final type parameter hint for let decl, which should be mapped to the position before the type parameter.
        debug_file_write_verbose(
            f"Adjusting inlay hint for Final type parameter for name node {ast.dump(name_node)} with label {label} to label {get_final_name() + label} adjusted for Final name"
        )
        if pos := Pos.from_node_end(name_node):
            pos = Pos(
                line=pos.line, column=pos.column - len(get_final_name()) - len(": ")
            )
            decl_name_node = source_map.origin_pos_to_origin_node(pos, ast.Name)
            if isinstance(decl_name_node, ast.Name):
                return decl_name_node, ": " + get_final_name() + label
    return name_node, label


def _map_inlay_hint_for_type(
    hint: types.InlayHint,
    module: ast.Module | None,
    source_map: MatchBasedSourceMap,
) -> types.InlayHint | None:
    pos = lsp_position_to_pos(hint.position)
    # Anchor is name of declaration or return type annotation anchor, both of them are ast.Name before the position.
    name_node = source_map.unparsed_pos_to_origin_node(
        pos.col_back(),
        ast.Name,
    )
    debug_file_write_verbose(
        f"Mapping inlay hint type hint request position {hint.position}, got node {ast.dump(name_node) if name_node is not None else None}@{Range.from_ast_node(name_node) if name_node is not None else None}"
    )
    if isinstance(name_node, ast.Name):
        name_node, label = _adjust_final_type_adhoc_form(
            source_map, name_node, hint.label
        )
        if name_node_pos := Pos.from_node_end(name_node):
            if isinstance(label, str):
                label = demangle_text(label, module)
            else:
                label = _demangle_inlay_hint_label(label, module)
            debug_file_write_verbose(
                f"Mapping inlay hint type for name node {ast.dump(name_node)} with label '{label}' at last to position {pos} with name node position {name_node_pos}"
            )
            return types.InlayHint(
                position=pos_to_lsp_position(name_node_pos),
                label=label,
                kind=types.InlayHintKind.Type,
                text_edits=hint.text_edits,
                tooltip=_demangle_inlay_hint_tooltip(hint.tooltip, module),
                padding_left=hint.padding_left,
                padding_right=hint.padding_right,
                data=hint.data,
            )
    return None


def _map_inlay_hint_demangle_and_position(
    hint: types.InlayHint,
    module: ast.Module | None,
    source_map: MatchBasedSourceMap,
) -> types.InlayHint | None:
    kind = hint.kind
    # Call argument hints: retrieve.
    if kind == types.InlayHintKind.Parameter:
        if mapped_arg_pos := _map_inlay_hint_position_for_param(
            hint.position, source_map
        ):
            return types.InlayHint(
                position=mapped_arg_pos,
                label=_demangle_inlay_hint_label(hint.label, module),
                kind=hint.kind,
                text_edits=_map_inlay_hint_text_edits(hint.text_edits, source_map),
                tooltip=_demangle_inlay_hint_tooltip(hint.tooltip, module),
                padding_left=hint.padding_left,
                padding_right=hint.padding_right,
                data=hint.data,
            )
    # Variable/return related hint anchors.
    if kind == types.InlayHintKind.Type:
        if mapped_hint := _map_inlay_hint_for_type(hint, module, source_map):
            return mapped_hint
    # For safety, remove this hint if we cannot map the position.
    debug_file_write_verbose(
        f"Mapping inlay hint failed position {hint.position} for hint kind {kind} to original source."
    )
    return None


def _map_inlay_hint_text_edits(
    text_edits: Sequence[types.TextEdit] | None,
    source_map: MatchBasedSourceMap,
) -> list[types.TextEdit] | None:
    if text_edits is None:
        return None
    mapped_text_edits: list[types.TextEdit] = []
    for edit in text_edits:
        mapped_range = source_map.unparsed_range_to_origin_range(
            lsp_range_to_range(edit.range)
        )
        if mapped_range is None:
            continue
        mapped_text_edits.append(
            types.TextEdit(
                range=range_to_lsp_range(mapped_range),
                new_text=edit.new_text,
            )
        )
    return mapped_text_edits


def _map_inlay_hint(
    hint: types.InlayHint,
    module: ast.Module | None,
    source_map: MatchBasedSourceMap,
) -> types.InlayHint | None:
    if mapped_hint := _map_inlay_hint_demangle_and_position(hint, module, source_map):
        # Successfully mapped hint position.
        return mapped_hint
    return None


def map_inlay_hints_result(
    hints: InlayHintResult,
    module: ast.Module | None,
    source_map: MatchBasedSourceMap | None,
) -> InlayHintResult:
    if hints is None:
        return None
    if source_map is None:
        return []
    mapped_hints: list[types.InlayHint] = []
    for hint in hints:
        if mapped := _map_inlay_hint(hint, module, source_map):
            debug_file_write_verbose(
                f"Mapped inlay hint from {hint} to position {mapped.position}"
            )
            mapped_hints.append(mapped)
    return mapped_hints
