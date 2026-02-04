import asyncio

from lsprotocol import types
from pygls.lsp.client import LanguageClient

from .utils import sample_dir, assert_initialize_process, ensure_exit, sample_file
from src.Typhon.Driver.debugging import (
    debug_setup_logging,
)
from src.Typhon.LanguageServer.client.pyright import (
    create_pyright_client,
    start_pyright_client,
)
from src.Typhon.LanguageServer.client.pyrefly import (
    create_pyrefly_client,
    start_pyrefly_client,
)
from src.Typhon.LanguageServer.semantic_tokens import (
    decode_semantic_tokens,
    get_semantic_token_text,
    SemanticToken,
    TOKEN_TYPES,
    semantic_legend,
    semantic_legends_of_initialized_response,
    semantic_token_capabilities,
    pyrefly_semantic_legend,
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


async def assert_semantic_tokens(
    client: LanguageClient, legend: types.SemanticTokensLegend | None = None
) -> tuple[types.SemanticTokens, list[SemanticToken], list[str]]:
    uri = sample_file.resolve().as_uri()
    async with asyncio.timeout(10):
        # Open
        open_params = types.DidOpenTextDocumentParams(
            types.TextDocumentItem(
                uri=uri,
                language_id="python",
                version=1,
                text=sample_file.read_text(),
            )
        )
        client.text_document_did_open(open_params)
        print(f"Opened document: {open_params}\n")
        # Request semantic tokens
        params = types.SemanticTokensParams(
            text_document=types.TextDocumentIdentifier(uri=uri),
        )
        response = await client.text_document_semantic_tokens_full_async(params)
        assert response is not None
        assert isinstance(response, types.SemanticTokens)
        tokens = decode_semantic_tokens(
            response, semantic_legends_of_initialized_response(legend) if legend else {}
        )
        print(
            f"params:{params}\ntext:\n{sample_file.read_text()}\nresponse:\n{response}\nsemantic tokens:\n{tokens}\ntexts:\n{[get_semantic_token_text(token, sample_file.read_text().splitlines()) for token in tokens]}\n"
        )
        lines = sample_file.read_text().splitlines()
        return response, tokens, lines


def test_semantic_tokens_pyright():
    async def run_test():
        client = create_pyright_client()
        await start_pyright_client(client)
        try:
            initialized_result = await assert_initialize_process(
                client, semantic_token_capabilities()
            )
            semantic_token_provider = initialized_result.semantic_tokens_provider
            assert semantic_token_provider, "Semantic tokens provider is None"
            response, tokens, lines = await assert_semantic_tokens(
                client, semantic_token_provider.legend
            )
            # Verify expected tokens
            assert len(response.data) == 5 * 5
            assert_semantic_token(lines, tokens[0], "function", "main", 0, 4)
            assert_semantic_token(lines, tokens[1], "function", "print", 1, 4)
            assert_semantic_token(lines, tokens[2], "class", "int", 1, 20)
            assert_semantic_token(lines, tokens[3], "variable", "__name__", 4, 3)
            assert_semantic_token(lines, tokens[4], "function", "main", 5, 4)
            await client.shutdown_async(None)
        finally:
            await ensure_exit(client)

    asyncio.run(run_test())


def test_semantic_tokens_pyrefly():
    async def run_test():
        client = create_pyrefly_client()
        await start_pyrefly_client(client)
        try:
            initialized_result = await assert_initialize_process(
                client, semantic_token_capabilities()
            )
            semantic_token_provider = initialized_result.semantic_tokens_provider
            # assert semantic_token_provider, "Semantic tokens provider is None"
            # assert semantic_token_provider is None, (
            #     "Pyrefly currently does not support semantic tokens in capabilities"
            # )
            legend: types.SemanticTokensLegend = (
                semantic_token_provider.legend
                if semantic_token_provider and semantic_token_provider.legend
                else pyrefly_semantic_legend()
            )
            response, tokens, lines = await assert_semantic_tokens(client, legend)
            # Verify expected tokens
            assert len(response.data) == 4 * 5
            assert_semantic_token(lines, tokens[0], "function", "main", 0, 4)
            assert_semantic_token(lines, tokens[1], "function", "print", 1, 4)
            assert_semantic_token(lines, tokens[2], "class", "int", 1, 20)
            assert_semantic_token(lines, tokens[3], "function", "main", 5, 4)

            await client.shutdown_async(None)
        finally:
            await ensure_exit(client)

    asyncio.run(run_test())
