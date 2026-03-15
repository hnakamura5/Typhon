import ast
from lsprotocol import types

from ..Driver.debugging import debug_verbose_print

from ._utils.mapping import lsp_range_to_range

from ..Transform.name_generator import is_builtin_name
from ..Grammar.parser import parse_string
from ..LanguageServer.parsed_buffer import LanguageServerParsedBuffer
from ..SourceMap import SourceMap
from ..SourceMap.datatype import Range
from ..SourceMap.source_ast_cache import SourceAstCache


def _get_reparse_unit(
    changed_range: Range, ast_cache: SourceAstCache
) -> ast.AST | None:
    node = ast_cache.source_range_to_node(changed_range, filter_node_type=ast.stmt)
    debug_verbose_print(
        lambda: (
            f"Node at changed range {changed_range}: {ast.dump(node) if node else None}"
        )
    )
    if node is None:
        return None
    # The most simple way. This does not require most of renaming.
    return ast_cache.outermost_enclosing(node, ast.stmt)
    # Find the innermost statement or expression containing the position
    if enclosing_function := ast_cache.innermost_enclosing(
        node, (ast.FunctionDef, ast.AsyncFunctionDef)
    ):
        return enclosing_function
    # Prefer function than class. Because function body itself is a scope.
    if enclosing_class := ast_cache.innermost_enclosing(node, ast.ClassDef):
        return enclosing_class
    top_level_stmt = ast_cache.outermost_enclosing(node, ast.stmt)
    return top_level_stmt


def _get_reparse_unit_range(
    changed_range: Range, ast_cache: SourceAstCache
) -> tuple[Range, ast.AST] | None:
    unit = _get_reparse_unit(changed_range, ast_cache)
    if unit is None:
        return None
    unit_range = Range.from_ast_node(unit)
    if unit_range is None:
        return None
    return unit_range, unit


def _get_reparse_unit_range_adjusted(
    changed_range: Range, ast_cache: SourceAstCache
) -> tuple[Range, ast.AST] | None:
    unit_and_range = _get_reparse_unit_range(changed_range, ast_cache)
    if unit_and_range is None:
        return None
    # TODO: Adjust the range when changed position is near the edge of the unit
    return unit_and_range


def _get_reparse_replace_target(
    changed_range: Range, ast_mapping: SourceMap, filter_type: type[ast.AST]
) -> ast.AST | None:
    # TODO: If the position is contained in several target?
    target = ast_mapping.origin_range_to_origin_node(changed_range, filter_type)
    return target


class PositionAdjuster(ast.NodeVisitor):
    def __init__(self, line_offset: int, column_offset: int):
        self.line_offset = line_offset
        self.column_offset = column_offset

    def visit(self, node: ast.AST):
        if lineno := getattr(node, "lineno", None):
            setattr(node, "lineno", lineno + self.line_offset)
            if col_offset := getattr(node, "col_offset", None):
                new_col_offset = (
                    col_offset + self.column_offset if lineno == 1 else col_offset
                )
                setattr(node, "col_offset", new_col_offset)
        self.generic_visit(node)


def _adjust_positions_of_reparsed_unit(
    reparsed_unit: ast.AST,
    original_unit_range: Range,
):
    PositionAdjuster(
        line_offset=original_unit_range.start.line,
        column_offset=original_unit_range.start.column,
    ).visit(reparsed_unit)


class NodeReplacer(ast.NodeTransformer):
    def __init__(self, target: ast.AST, replacement: ast.stmt | list[ast.stmt]):
        self.target = target
        self.replacement = replacement
        self.replaced = False

    def visit(self, node: ast.AST):
        debug_verbose_print(
            lambda: f"  Visiting node {ast.dump(node)} is_target={node is self.target}"
        )
        if node is self.target:
            self.replaced = True
            return self.replacement
        return super().visit(node)


def _filter_remove_builtin_import(body: list[ast.stmt]) -> list[ast.stmt]:
    result: list[ast.stmt] = []
    for stmt in body:
        if isinstance(stmt, ast.Import):
            if len(stmt.names) == 1 and is_builtin_name(stmt.names[0].name):
                continue
        if isinstance(stmt, ast.ImportFrom):
            if stmt.module is not None and is_builtin_name(stmt.module):
                continue
        result.append(stmt)
    return result


def _replace_to_reparsed_unit(
    original_ast: ast.Module,
    reparsed_result: ast.AST,
    replace_target: ast.AST,
) -> ast.Module | None:
    if not isinstance(reparsed_result, ast.Module):
        return None
    filtered_body = _filter_remove_builtin_import(reparsed_result.body)
    replacer = NodeReplacer(replace_target, filtered_body)
    new_ast = replacer.visit(original_ast)
    # TODO: Merge or replace the same class (by record)
    if not replacer.replaced:
        return None
    if not isinstance(new_ast, ast.Module):
        return None
    return new_ast


def _reparce_range_and_replace(
    original_transformed: ast.Module,
    changed_source_code: str,
    changed_range: Range,
    ast_cache: SourceAstCache,
    ast_mapping: SourceMap,
) -> ast.Module | None:
    debug_verbose_print(
        lambda: (
            f"Starting reparsing for changed range {changed_range}, source code: {changed_range.of_string(changed_source_code)}"
        )
    )
    reparse_unit_and_range = _get_reparse_unit_range_adjusted(changed_range, ast_cache)
    if reparse_unit_and_range is None:
        return None
    debug_verbose_print(
        lambda: (
            f"Reparse unit range for changed range {changed_range}: {reparse_unit_and_range[0]}"
        )
    )
    reparse_unit_range, reparse_unit = reparse_unit_and_range
    origin_source_reparse_part = reparse_unit_range.of_string(changed_source_code)
    if not origin_source_reparse_part:
        return None
    debug_verbose_print(
        lambda: (
            f"Origin source code for reparse unit range {reparse_unit_range}:\n {origin_source_reparse_part}"
        )
    )
    replace_target = _get_reparse_replace_target(
        reparse_unit_range, ast_mapping, type(reparse_unit)
    )
    if replace_target is None:
        return None
    debug_verbose_print(
        lambda: (
            f"Replace target for reparse unit range {reparse_unit_range}: {replace_target}"
        )
    )
    reparsed_result = parse_string(origin_source_reparse_part, "exec")
    if reparsed_result is None:
        return None
    debug_verbose_print(
        lambda: (
            f"Reparsed AST for reparse unit range {reparse_unit_range}: {ast.dump(reparsed_result)}"
        )
    )
    _adjust_positions_of_reparsed_unit(reparsed_result, reparse_unit_range)
    # TODO: Adjust positions in ast_cache and source map (nodes after changed position). To make it faster, should we split the source map's interval tree per top level statement?
    # TODO: Adjust name binding with around? No need?
    return _replace_to_reparsed_unit(
        original_transformed, reparsed_result, replace_target
    )


def try_reparse_range(
    parsed_buffer: LanguageServerParsedBuffer,
    original_uri: str,
    changed_source_code: str,
    changed_lsp_range: types.Range,
) -> ast.AST | None:
    original_transformed_module = parsed_buffer.get_module(original_uri)
    if original_transformed_module is None:
        return None
    changed_range = lsp_range_to_range(changed_lsp_range)
    ast_cache = parsed_buffer.get_source_ast_cache(original_uri)
    mapping = parsed_buffer.get_mapping(original_uri)
    if ast_cache is None or mapping is None:
        return None
    result = _reparce_range_and_replace(
        original_transformed_module,
        changed_source_code,
        changed_range,
        ast_cache,
        mapping,
    )
    if result is None:
        return None
    parsed_buffer.reload_from_parsed_module(
        original_uri, result, changed_source_code, ast_cache.source_file_path
    )
    return result
