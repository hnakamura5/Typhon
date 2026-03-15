import ast
import copy

from ..Transform.transform import transform
from ..Grammar.unparse_custom import unparse_custom
from ..SourceMap.ast_match_based_map import MatchBasedSourceMap, map_from_translated
from ..SourceMap.source_ast_cache import SourceAstCache


class LanguageServerParsedBuffer:
    def __init__(self) -> None:
        # All the keys are original_uri, the uri of typhon source file.
        self.parsed_ast_modules: dict[str, ast.Module | None] = {}
        self.ast_modules: dict[str, ast.Module | None] = {}
        self.source_ast_caches: dict[str, SourceAstCache] = {}
        self.mappings: dict[str, MatchBasedSourceMap] = {}
        self.translated_sources: dict[str, str] = {}

    def get_module(self, original_uri: str | None) -> ast.Module | None:
        if original_uri is None:
            return None
        return self.ast_modules.get(original_uri, None)

    def has_module(self, original_uri: str) -> bool:
        return original_uri in self.ast_modules

    def get_parsed_module(self, original_uri: str | None) -> ast.Module | None:
        if original_uri is None:
            return None
        return self.parsed_ast_modules.get(original_uri, None)

    def get_source_ast_cache(self, original_uri: str | None) -> SourceAstCache | None:
        if original_uri is None:
            return None
        return self.source_ast_caches.get(original_uri, None)

    def get_mapping(self, original_uri: str | None) -> MatchBasedSourceMap | None:
        if original_uri is None:
            return None
        return self.mappings.get(original_uri, None)

    def get_translated_source(self, original_uri: str | None) -> str | None:
        if original_uri is None:
            return None
        return self.translated_sources.get(original_uri, None)

    def _set_parsed_module(self, original_uri: str, module: ast.Module | None) -> None:
        self.parsed_ast_modules[original_uri] = module

    def _set_module(self, original_uri: str, module: ast.Module | None) -> None:
        self.ast_modules[original_uri] = module

    def _set_source_ast_cache(
        self, original_uri: str, source_ast_cache: SourceAstCache
    ) -> None:
        self.source_ast_caches[original_uri] = source_ast_cache

    def _set_mapping(self, original_uri: str, mapping: MatchBasedSourceMap) -> None:
        self.mappings[original_uri] = mapping

    def _set_translated_source(self, original_uri: str, source: str) -> None:
        self.translated_sources[original_uri] = source

    def reload_from_parsed_module(
        self,
        original_uri: str,
        module_before_transform: ast.Module,
        source_code: str,
        source_file_path: str,
    ) -> tuple[ast.Module, str] | None:
        """
        Reload the buffer content. Responsible to all workflow for parsed module.
        Returns the transformed module and the unparsed source code on success.
        """
        module_before_transform_snap = copy.deepcopy(module_before_transform)
        module_to_transform = module_before_transform_snap
        self._set_parsed_module(original_uri, module_before_transform_snap)
        self._set_source_ast_cache(
            original_uri,
            SourceAstCache(
                module_before_transform_snap,
                source_code,
                source_file_path,
            ),
        )
        transform(module_to_transform, ignore_error=True)
        self._set_module(original_uri, module_to_transform)
        unparsed = unparse_custom(module_to_transform)
        mapping = map_from_translated(
            module_to_transform, source_code, source_file_path, unparsed
        )
        if mapping is not None:
            self._set_mapping(original_uri, mapping)
        self._set_translated_source(original_uri, unparsed)
        return module_to_transform, unparsed
