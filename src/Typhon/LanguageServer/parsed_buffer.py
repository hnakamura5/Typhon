import ast
from typing import Sequence

from ..Grammar.tokenizer_custom import TokenInfo
from ..SourceMap.ast_match_based_map import MatchBasedSourceMap
from ..SourceMap.source_ast_cache import SourceAstCache
from .semantic_tokens import SemanticToken


class LanguageServerParsedBuffer:
    """Container for per-document parse and mapping artifacts."""

    def __init__(self) -> None:
        self.parsed_ast_modules: dict[str, ast.Module | None] = {}
        self.ast_modules: dict[str, ast.Module | None] = {}
        self.source_ast_caches: dict[str, SourceAstCache] = {}
        self.token_infos: dict[str, list[TokenInfo]] = {}
        self.semantic_tokens: dict[str, list[SemanticToken]] = {}
        self.semantic_tokens_encoded: dict[str, Sequence[int]] = {}
        self.mappings: dict[str, MatchBasedSourceMap] = {}
        self.translated_sources: dict[str, str] = {}

    def get_module(self, original_uri: str | None) -> ast.Module | None:
        if original_uri is None:
            return None
        return self.ast_modules.get(original_uri, None)

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

    def set_parsed_module(self, original_uri: str, module: ast.Module | None) -> None:
        self.parsed_ast_modules[original_uri] = module

    def set_module(self, original_uri: str, module: ast.Module | None) -> None:
        self.ast_modules[original_uri] = module

    def has_module(self, original_uri: str) -> bool:
        return original_uri in self.ast_modules

    def set_source_ast_cache(
        self, original_uri: str, source_ast_cache: SourceAstCache
    ) -> None:
        self.source_ast_caches[original_uri] = source_ast_cache

    def set_token_infos(self, original_uri: str, token_infos: list[TokenInfo]) -> None:
        self.token_infos[original_uri] = token_infos

    def get_token_infos(self, original_uri: str | None) -> list[TokenInfo]:
        if original_uri is None:
            return []
        return self.token_infos.get(original_uri, [])

    def set_semantic_tokens(
        self,
        original_uri: str,
        semantic_tokens: list[SemanticToken],
        semantic_tokens_encoded: Sequence[int],
    ) -> None:
        self.semantic_tokens[original_uri] = semantic_tokens
        self.semantic_tokens_encoded[original_uri] = semantic_tokens_encoded

    def get_semantic_tokens(self, original_uri: str | None) -> list[SemanticToken]:
        if original_uri is None:
            return []
        return self.semantic_tokens.get(original_uri, [])

    def set_mapping(self, original_uri: str, mapping: MatchBasedSourceMap) -> None:
        self.mappings[original_uri] = mapping

    def set_translated_source(self, original_uri: str, source: str) -> None:
        self.translated_sources[original_uri] = source

    def get_translated_source(self, original_uri: str | None) -> str | None:
        if original_uri is None:
            return None
        return self.translated_sources.get(original_uri, None)
