import asyncio
from lsprotocol import types
from pygls.lsp.client import LanguageClient
from pathlib import Path

from src.Typhon.Driver.debugging import debug_file_write, debug_verbose_print
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
        assert len(response.data) == 5 * 27
        assert_tokens(lines, tokens)
        debug_file_write("Semantic token test completed successfully.\n")
        await client.shutdown_async(None)

    asyncio.run(run_test())


def assert_tokens(
    lines: list[str],
    tokens: list[SemanticToken],
) -> None:
    # [SemanticToken(line=0, offset=7, length=2, start_col=7, end_col=9, text='re', tok_type='namespace', tok_modifiers=[]), SemanticToken(line=1, offset=5, length=7, start_col=5, end_col=12, text='pathlib', tok_type='namespace', tok_modifiers=[]), SemanticToken(line=1, offset=8, length=4, start_col=20, end_col=24, text='Path', tok_type='class', tok_modifiers=[]), SemanticToken(line=3, offset=6, length=1, start_col=6, end_col=7, text='C', tok_type='class', tok_modifiers=[<TokenModifier.declaration: 1>]), SemanticToken(line=4, offset=8, length=1, start_col=8, end_col=9, text='x', tok_type='property', tok_modifiers=[<TokenModifier.readonly: 4>, <TokenModifier.static: 8>, <TokenModifier.modification: 128>]), SemanticToken(line=4, offset=2, length=3, start_col=11, end_col=14, text='int', tok_type='class', tok_modifiers=[<TokenModifier.abstract: 32>, <TokenModifier.async_: 64>]), SemanticToken(line=5, offset=8, length=8, start_col=8, end_col=16, text='__init__', tok_type='method', tok_modifiers=[<TokenModifier.declaration: 1>, <TokenModifier.modification: 128>]), SemanticToken(line=6, offset=8, length=4, start_col=8, end_col=12, text='self', tok_type='selfParameter', tok_modifiers=[<TokenModifier.documentation: 256>]), SemanticToken(line=10, offset=4, length=3, start_col=4, end_col=7, text='fun', tok_type='function', tok_modifiers=[<TokenModifier.declaration: 1>]), SemanticToken(line=10, offset=7, length=4, start_col=14, end_col=18, text='Path', tok_type='class', tok_modifiers=[]), SemanticToken(line=12, offset=18, length=4, start_col=18, end_col=22, text='open', tok_type='function', tok_modifiers=[<TokenModifier.abstract: 32>, <TokenModifier.async_: 64>]), SemanticToken(line=12, offset=1, length=3, start_col=23, end_col=26, text='str', tok_type='class', tok_modifiers=[<TokenModifier.abstract: 32>, <TokenModifier.async_: 64>]), SemanticToken(line=12, offset=1, length=4, start_col=27, end_col=31, text='file', tok_type='parameter', tok_modifiers=[<TokenModifier.documentation: 256>]), SemanticToken(line=12, offset=-17, length=1, start_col=14, end_col=15, text='f', tok_type='variable', tok_modifiers=[]), SemanticToken(line=13, offset=12, length=7, start_col=12, end_col=19, text='content', tok_type='variable', tok_modifiers=[]), SemanticToken(line=13, offset=3, length=1, start_col=22, end_col=23, text='f', tok_type='variable', tok_modifiers=[]), SemanticToken(line=14, offset=12, length=1, start_col=12, end_col=13, text='m', tok_type='variable', tok_modifiers=[]), SemanticToken(line=14, offset=3, length=2, start_col=16, end_col=18, text='re', tok_type='namespace', tok_modifiers=[]), SemanticToken(line=14, offset=35, length=7, start_col=53, end_col=60, text='content', tok_type='variable', tok_modifiers=[]), SemanticToken(line=15, offset=8, length=5, start_col=8, end_col=13, text='print', tok_type='function', tok_modifiers=[<TokenModifier.abstract: 32>, <TokenModifier.async_: 64>]), SemanticToken(line=15, offset=11, length=1, start_col=24, end_col=25, text='m', tok_type='variable', tok_modifiers=[]), SemanticToken(line=18, offset=4, length=6, start_col=4, end_col=10, text='my_dir', tok_type='variable', tok_modifiers=[]), SemanticToken(line=18, offset=2, length=4, start_col=12, end_col=16, text='Path', tok_type='class', tok_modifiers=[]), SemanticToken(line=18, offset=3, length=4, start_col=19, end_col=23, text='Path', tok_type='class', tok_modifiers=[]), SemanticToken(line=18, offset=1, length=8, start_col=24, end_col=32, text='__file__', tok_type='variable', tok_modifiers=[]), SemanticToken(line=19, offset=0, length=3, start_col=0, end_col=3, text='fun', tok_type='function', tok_modifiers=[]), SemanticToken(line=19, offset=1, length=6, start_col=4, end_col=10, text='my_dir', tok_type='variable', tok_modifiers=[])]
    assert_semantic_token(lines, tokens[0], "namespace", "re", 0, 7)
    assert_semantic_token(lines, tokens[1], "namespace", "pathlib", 1, 5)
    assert_semantic_token(lines, tokens[2], "class", "Path", 1, 20)
    assert_semantic_token(lines, tokens[3], "class", "C", 3, 6)
    assert_semantic_token(lines, tokens[4], "property", "x", 4, 8)
    assert_semantic_token(lines, tokens[5], "class", "int", 4, 11)
    assert_semantic_token(lines, tokens[6], "method", "__init__", 5, 8)
    assert_semantic_token(lines, tokens[7], "selfParameter", "self", 6, 8)
    assert_semantic_token(lines, tokens[8], "function", "fun", 10, 4)
    assert_semantic_token(lines, tokens[9], "class", "Path", 10, 14)
    assert_semantic_token(lines, tokens[10], "variable", "f", 12, 14)
    assert_semantic_token(lines, tokens[11], "function", "open", 12, 18)
    assert_semantic_token(lines, tokens[12], "class", "str", 12, 23)
    assert_semantic_token(lines, tokens[13], "parameter", "file", 12, 27)
    assert_semantic_token(lines, tokens[14], "variable", "content", 13, 12)
    assert_semantic_token(lines, tokens[15], "variable", "f", 13, 22)
    assert_semantic_token(lines, tokens[16], "variable", "m", 14, 12)
    assert_semantic_token(lines, tokens[17], "namespace", "re", 14, 16)
    assert_semantic_token(lines, tokens[18], "variable", "content", 14, 53)
    assert_semantic_token(lines, tokens[19], "function", "print", 15, 8)
    assert_semantic_token(lines, tokens[20], "variable", "m", 15, 24)
    assert_semantic_token(lines, tokens[21], "variable", "my_dir", 18, 4)
    assert_semantic_token(lines, tokens[22], "class", "Path", 18, 12)
    assert_semantic_token(lines, tokens[23], "class", "Path", 18, 19)
    assert_semantic_token(lines, tokens[24], "variable", "__file__", 18, 24)
    assert_semantic_token(lines, tokens[25], "function", "fun", 19, 0)
    assert_semantic_token(lines, tokens[26], "variable", "my_dir", 19, 4)
