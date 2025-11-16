import ast
from .datatype import Range, Pos, RangeIntervalTree
from ..Grammar.typhon_ast import get_pos_attributes_if_exists
from ..Driver.debugging import debug_print, debug_verbose_print
from ..SourceMap.ast_matching import match_ast


class MatchBasedSourceMap:
    def __init__(
        self,
        origin_to_unparsed: dict[ast.AST, ast.AST],
        unparsed_to_origin: dict[ast.AST, ast.AST],
        source_code: str,
        source_file: str,
    ):
        self.origin_to_unparsed = origin_to_unparsed
        self.unparsed_to_origin = unparsed_to_origin
        self.origin_interval_tree = RangeIntervalTree[ast.AST]()
        self.unparsed_interval_tree = RangeIntervalTree[ast.AST]()
        self.source_code = source_code
        self.source_file = source_file
        self._setup_interval_trees()

    def _setup_interval_trees(self):
        for origin_node, unparsed_node in self.origin_to_unparsed.items():
            origin_pos = get_pos_attributes_if_exists(origin_node)
            if origin_pos is not None:
                debug_verbose_print(
                    f"Adding to origin interval tree:\n  range={Range.from_pos_attr_may_not_end(origin_pos)}\n    {ast.dump(origin_node)}\n    pos: {origin_pos}"
                )
                self.origin_interval_tree.add(
                    Range.from_pos_attr_may_not_end(origin_pos), origin_node
                )
            unparsed_pos = get_pos_attributes_if_exists(unparsed_node)
            if unparsed_pos is not None:
                debug_verbose_print(
                    f"Adding to unparsed interval tree: range={Range.from_pos_attr_may_not_end(unparsed_pos)} {ast.dump(unparsed_node)}"
                )
                self.unparsed_interval_tree.add(
                    Range.from_pos_attr_may_not_end(unparsed_pos), unparsed_node
                )

    # Assume range in base_node, apply the offset of the range in base_node to result_node
    # TODO: This is valid range conversion only for very simple cases.
    def _apply_offset_range(
        self,
        range: Range,
        base_node: ast.AST,
        result_node: ast.AST,
    ) -> Range | None:
        base_pos_attr = get_pos_attributes_if_exists(base_node)
        if base_pos_attr is None:
            return None
        base_range = Range.from_pos_attr_may_not_end(base_pos_attr)
        result_pos_attr = get_pos_attributes_if_exists(result_node)
        if result_pos_attr is None:
            return None
        result_range = Range.from_pos_attr_may_not_end(result_pos_attr)
        range_offset = base_range.calc_offset(range)
        debug_verbose_print(
            f"Offsetting range:\n  base_range={base_range}\n  range={range}\n  offset={range_offset}\n  result_range={result_range}\n  apply_offset:{result_range.start.apply_offset(range_offset)}"
        )
        return result_range.start.apply_offset(range_offset)

    def _range_to(
        self,
        range: Range,
        interval_tree: RangeIntervalTree[ast.AST],
        mapping: dict[ast.AST, ast.AST],
    ) -> Range | None:
        nodes = interval_tree.minimal_containers(range)
        debug_verbose_print(f"Mapping range: {range} nodes: {nodes}")
        if nodes:
            if len(nodes) == 1:
                # The canonical node for the range
                node_range, node = nodes[0]
                if node in mapping:
                    debug_verbose_print(
                        f"node is one: {ast.dump(node)}\n  mapping to {ast.dump(mapping[node])}\n  range: {range}\n  node_range: {node_range}"
                    )
                    if node_range == range:
                        # If the range matches exactly, no need to apply offset
                        return Range.from_ast_node(mapping[node])
                    # Use offset mapping to precisely map the range inside the node
                    return self._apply_offset_range(range, node, mapping[node])
            else:
                # When multiple nodes are found, merge the ranges of all mapped nodes
                mapped_nodes = (mapping[node] for _, node in nodes if node in mapping)
                pos_attrs = (
                    pos_attr
                    for mapped_node in mapped_nodes
                    if (pos_attr := get_pos_attributes_if_exists(mapped_node))
                )
                debug_verbose_print(f"Found {len(nodes)} nodes for the given range.")
                return Range.merge_ranges(
                    Range.from_pos_attr_may_not_end(pos_attr) for pos_attr in pos_attrs
                )
        debug_verbose_print("No nodes found for the given range.")

    def unparsed_range_to_origin(
        self,
        range_unparsed: Range,
    ) -> Range | None:
        return self._range_to(
            range_unparsed,
            self.unparsed_interval_tree,
            self.unparsed_to_origin,
        )

    def unparsed_range_to_source_code(
        self,
        range_unparsed: Range,
    ) -> str | None:
        range_in_origin = self.unparsed_range_to_origin(range_unparsed)
        if range_in_origin is None:
            return None
        return range_in_origin.of_string(self.source_code)

    def origin_range_to_unparsed(
        self,
        range_origin: Range,
    ) -> Range | None:
        debug_verbose_print(f"Mapping origin range: {range_origin}")
        return self._range_to(
            range_origin,
            self.origin_interval_tree,
            self.origin_to_unparsed,
        )

    def origin_node_to_unparsed_range(
        self,
        origin_node: ast.AST,
    ) -> Range | None:
        range_origin = get_pos_attributes_if_exists(origin_node)
        if range_origin is None:
            return None
        range_origin_part = Range.from_pos_attr_may_not_end(range_origin)
        return self.origin_range_to_unparsed(range_origin_part)


def map_from_transformed_ast(
    origin_ast: ast.AST,
    unparsed_ast: ast.AST,
    source_code: str,
    source_file: str,
) -> MatchBasedSourceMap | None:
    mapping = match_ast(origin_ast, unparsed_ast)
    if mapping is None:
        return None
    return MatchBasedSourceMap(
        mapping.left_to_right, mapping.right_to_left, source_code, source_file
    )
