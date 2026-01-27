import asyncio
from lsprotocol import types
from pygls.lsp.client import LanguageClient
from pathlib import Path

from src.Typhon.Driver.debugging import debug_file_write
from src.Typhon.LanguageServer.utils import path_to_uri
from .utils import (
    sample_dir,
    sample_file,
    small_sample_file,
    start_initialize_open_typhon_connection_client,
    ensure_exit,
)
from src.Typhon.LanguageServer.semantic_tokens import (
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
        target_file_uri = path_to_uri(small_sample_file)
        (
            client,
            initialize_result,
        ) = await start_initialize_open_typhon_connection_client(
            sample_dir, small_sample_file
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
        target_file_uri = path_to_uri(sample_file)
        (
            client,
            initialize_result,
        ) = await start_initialize_open_typhon_connection_client(
            sample_dir, sample_file
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
        assert len(response.data) == 5 * 39
        assert_tokens(lines, tokens)
        debug_file_write("Semantic token test completed successfully.\n")
        await client.shutdown_async(None)

    asyncio.run(run_test())


def assert_tokens(
    lines: list[str],
    tokens: list[SemanticToken],
) -> None:
    assert_semantic_token(lines, tokens[0], "function", "main", 0, 4)
    assert_semantic_token(lines, tokens[1], "function", "print", 1, 4)
    assert_semantic_token(lines, tokens[2], "class", "int", 1, 20)
    assert_semantic_token(lines, tokens[3], "variable", "__name__", 4, 3)
    assert_semantic_token(lines, tokens[4], "function", "main", 5, 4)
