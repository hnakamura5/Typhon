import asyncio
from lsprotocol import types
from pygls.lsp.client import LanguageClient
from pathlib import Path

from Typhon.Driver.debugging import debug_file_write, debug_verbose_print
from Typhon.LanguageServer._utils.path import path_to_uri
from .utils import (
    run_file_dir,
    semtok_file,
    hello_file,
    start_initialize_open_typhon_connection_client,
    ensure_exit,
)
from Typhon.LanguageServer.semantic_tokens import (
    semantic_legend,
    SemanticToken,
    decode_semantic_tokens,
    get_semantic_token_text,
    semantic_legends_of_initialized_response,
    semantic_token_capabilities,
)


def assert_semantic_token(
    lines: list[str],
    token: SemanticToken,
    expected_token_type: str,
    expected_text: str,
    expected_line: int,
    expected_start_col: int,
) -> None:
    token_text = get_semantic_token_text(token, lines)
    debug_verbose_print(
        f"Asserting semantic token: {token} with text '{token_text}', where expected text is '{expected_text}', line {expected_line}, start_col {expected_start_col}, token_type {expected_token_type}"
    )
    assert token_text == expected_text, (
        f"Expected text '{expected_text}', got '{token_text}'"
    )
    assert token.line == expected_line, (
        f"Expected line {expected_line}, got {token.line}"
    )
    assert token.start_col == expected_start_col, (
        f"Expected start_col {expected_start_col}, got {token.start_col}"
    )
    assert token.tok_type == expected_token_type, (
        f"Expected token_type {expected_token_type}, got {token.tok_type}"
    )


async def access_semantic_tokens_of_uri(
    client: LanguageClient,
    uri: str,
    legend: types.SemanticTokensLegend | None = None,
) -> tuple[types.SemanticTokens, list[SemanticToken]]:
    async with asyncio.timeout(10):
        # Request semantic tokens
        params = types.SemanticTokensParams(
            text_document=types.TextDocumentIdentifier(uri=uri),
        )
        print(f"Requesting semantic tokens with params: {params}\n")
        response = await client.text_document_semantic_tokens_full_async(params)
        assert response is not None
        assert isinstance(response, types.SemanticTokens)
        tokens = decode_semantic_tokens(
            response, semantic_legends_of_initialized_response(legend) if legend else {}
        )
        print(
            f"params:{params}\n  response:\n  {response}\n  semantic tokens:\n  {tokens}"
        )
        return response, tokens


def test_semantic_tokens_small():
    async def run_test():
        target_file_uri = path_to_uri(hello_file)
        (
            client,
            initialize_result,
        ) = await start_initialize_open_typhon_connection_client(
            run_file_dir, hello_file
        )
        response, tokens = await access_semantic_tokens_of_uri(
            client, target_file_uri, semantic_legend()
        )
        text = Path.from_uri(target_file_uri).read_text()
        lines = text.splitlines()
        # Verify expected tokens
        print(
            f"  texts:\n  {[get_semantic_token_text(token, lines) for token in tokens]}"
        )
        assert len(response.data) == 5 * 2
        assert_tokens_small(lines, tokens)
        debug_file_write("Semantic token test completed successfully.\n")
        await client.shutdown_async(None)

    asyncio.run(run_test())


def assert_tokens_small(
    lines: list[str],
    tokens: list[SemanticToken],
) -> None:
    assert_semantic_token(lines, tokens[0], "variable", "__name__", 0, 4)
    assert_semantic_token(lines, tokens[1], "function", "print", 1, 4)


def test_semantic_tokens():
    async def run_test():
        target_file_uri = path_to_uri(semtok_file)
        (
            client,
            initialize_result,
        ) = await start_initialize_open_typhon_connection_client(
            run_file_dir, semtok_file
        )
        response, tokens = await access_semantic_tokens_of_uri(
            client, target_file_uri, semantic_legend()
        )
        text = Path.from_uri(target_file_uri).read_text()
        lines = text.splitlines()
        # Verify expected tokens
        print(
            f"  texts:\n  {[get_semantic_token_text(token, lines) for token in tokens]}"
        )
        assert_tokens(lines, tokens)
        debug_file_write("Semantic token test completed successfully.\n")
        await client.shutdown_async(None)

    asyncio.run(run_test())


def assert_tokens(
    lines: list[str],
    tokens: list[SemanticToken],
) -> None:
    i = 0

    def next_token() -> SemanticToken:
        nonlocal i
        token = tokens[i]
        i += 1
        return token

    def assert_next_is_end():
        assert i == len(tokens), (
            f"Expected all tokens to be consumed, but {len(tokens) - i} remain."
        )

    debug_verbose_print(f"Total tokens: {len(tokens)}")
    for t in tokens:
        debug_verbose_print(
            f'"{t.tok_type}", "{get_semantic_token_text(t, lines)}", {t.line}, {t.start_col}'
        )

    assert_semantic_token(lines, next_token(), "namespace", "re", 0, 7)
    assert_semantic_token(lines, next_token(), "namespace", "pathlib", 1, 5)
    assert_semantic_token(lines, next_token(), "class", "Path", 1, 20)
    assert_semantic_token(lines, next_token(), "class", "C", 3, 6)
    assert_semantic_token(lines, next_token(), "property", "x", 4, 8)
    assert_semantic_token(lines, next_token(), "class", "int", 4, 11)
    assert_semantic_token(lines, next_token(), "method", "__init__", 5, 8)
    assert_semantic_token(lines, next_token(), "selfParameter", "self", 6, 8)
    assert_semantic_token(lines, next_token(), "property", "x", 6, 13)
    assert_semantic_token(lines, next_token(), "function", "fun", 10, 4)
    assert_semantic_token(lines, next_token(), "parameter", "file", 10, 8)
    assert_semantic_token(lines, next_token(), "class", "Path", 10, 14)
    assert_semantic_token(lines, next_token(), "variable", "f", 12, 14)
    assert_semantic_token(lines, next_token(), "function", "open", 12, 18)
    assert_semantic_token(lines, next_token(), "class", "str", 12, 23)
    assert_semantic_token(lines, next_token(), "parameter", "file", 12, 27)
    assert_semantic_token(lines, next_token(), "variable", "content", 13, 12)
    assert_semantic_token(lines, next_token(), "variable", "f", 13, 22)
    assert_semantic_token(lines, next_token(), "method", "read", 13, 24)
    assert_semantic_token(lines, next_token(), "variable", "m", 14, 12)
    assert_semantic_token(lines, next_token(), "namespace", "re", 14, 16)
    assert_semantic_token(lines, next_token(), "function", "match", 14, 19)
    assert_semantic_token(lines, next_token(), "variable", "content", 14, 53)
    assert_semantic_token(lines, next_token(), "function", "print", 15, 8)
    assert_semantic_token(lines, next_token(), "variable", "m", 15, 24)
    assert_semantic_token(lines, next_token(), "method", "group", 15, 27)
    assert_semantic_token(lines, next_token(), "variable", "my_dir", 18, 4)
    assert_semantic_token(lines, next_token(), "class", "Path", 18, 12)
    assert_semantic_token(lines, next_token(), "class", "Path", 18, 19)
    assert_semantic_token(lines, next_token(), "variable", "__file__", 18, 24)
    assert_semantic_token(lines, next_token(), "property", "parent", 18, 34)
    assert_semantic_token(lines, next_token(), "property", "parent", 18, 41)
    assert_semantic_token(lines, next_token(), "variable", "my_dir", 19, 4)
    assert_semantic_token(lines, next_token(), "method", "exists", 19, 11)
    assert_semantic_token(lines, next_token(), "variable", "typh_path", 20, 8)
    assert_semantic_token(lines, next_token(), "variable", "my_dir", 20, 20)
    assert_semantic_token(lines, next_token(), "function", "fun", 21, 9)
    assert_semantic_token(lines, next_token(), "variable", "typh_path", 21, 13)
    assert_semantic_token(lines, next_token(), "function", "print", 21, 31)
    assert_semantic_token(lines, next_token(), "variable", "x", 24, 5)
    assert_semantic_token(lines, next_token(), "variable", "y", 24, 8)
    assert_semantic_token(lines, next_token(), "variable", "ab", 25, 4)
    assert_semantic_token(lines, next_token(), "property", "a", 25, 11)
    assert_semantic_token(lines, next_token(), "typeParameter", "int", 25, 14)
    assert_semantic_token(lines, next_token(), "class", "int", 25, 14)
    assert_semantic_token(lines, next_token(), "property", "b", 25, 19)
    assert_semantic_token(lines, next_token(), "typeParameter", "int", 25, 22)
    assert_semantic_token(lines, next_token(), "class", "int", 25, 22)
    # TODO: Now duplicated tokens for record fields. As property and as parameter.
    assert_semantic_token(lines, next_token(), "property", "a", 25, 33)
    assert_semantic_token(lines, next_token(), "selfParameter", "a", 25, 33)
    assert_semantic_token(lines, next_token(), "property", "b", 25, 40)
    assert_semantic_token(lines, next_token(), "selfParameter", "b", 25, 40)
    assert_semantic_token(lines, next_token(), "variable", "a", 26, 6)
    assert_semantic_token(lines, next_token(), "variable", "b", 26, 10)
    assert_semantic_token(lines, next_token(), "variable", "ab", 26, 15)
    assert_next_is_end()
