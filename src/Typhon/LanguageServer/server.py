from typing import Any, override
import ast
import traceback
from ..Grammar.tokenizer_custom import TokenInfo, TokenizerCustom, tokenizer_for_string
from ..Grammar.parser import parse_tokenizer
from pygls.lsp.server import LanguageServer as PyglsLanguageServer
from pygls.workspace import TextDocument
from lsprotocol import types

from ..Driver.debugging import debug_file_write, debug_file_write_verbose

from .semantic_tokens import (
    TokenTypes,
    TokenModifier,
    SemanticToken,
    ast_tokens_to_semantic_tokens,
    semantic_legend,
)


class LanguageServer(PyglsLanguageServer):
    @override
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        PyglsLanguageServer.__init__(self, *args, **kwargs)  # type: ignore
        self.ast_modules: dict[str, ast.Module | None] = {}
        self.token_infos: dict[str, list[TokenInfo]] = {}
        self.semantic_tokens: dict[str, list[SemanticToken]] = {}
        self.semantic_tokens_encoded: dict[str, list[int]] = {}

    def reload(self, doc: TextDocument, uri: str) -> None:
        try:
            source = doc.source
            tokenizer = tokenizer_for_string(source)
            self.token_infos[uri] = tokenizer.read_all_tokens()
            ast_node = parse_tokenizer(tokenizer)
            if not isinstance(ast_node, ast.Module):
                ast_node = None
            self.ast_modules[uri] = ast_node
            semantic_tokens, encoded = ast_tokens_to_semantic_tokens(
                ast_node,
                self.token_infos[uri],
                doc,
            )
            self.semantic_tokens[uri] = semantic_tokens
            self.semantic_tokens_encoded[uri] = encoded
        except Exception as e:
            self.ast_modules[uri] = None
            self.token_infos[uri] = []
            self.semantic_tokens[uri] = []
            self.semantic_tokens_encoded[uri] = []
            debug_file_write(f"Error reloading document {uri}: {e}")
            # dump traceback to debug log
            traceback_str = traceback.format_exc()
            debug_file_write_verbose(f"Traceback:\n{traceback_str}")


server = LanguageServer("typhon-language-server", "v0.1.3")


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: LanguageServer, params: types.DidOpenTextDocumentParams):
    """Parse each document when it is opened"""
    uri = params.text_document.uri
    doc = ls.workspace.get_text_document(uri)
    ls.reload(doc, uri)


@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: LanguageServer, params: types.DidOpenTextDocumentParams):
    """Parse each document when it is changed"""
    uri = params.text_document.uri
    doc = ls.workspace.get_text_document(uri)
    ls.reload(doc, uri)


@server.feature(types.TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL, semantic_legend())
def semantic_tokens_full(ls: LanguageServer, params: types.SemanticTokensParams):
    uri = params.text_document.uri
    return types.SemanticTokens(data=ls.semantic_tokens_encoded.get(uri, []))
