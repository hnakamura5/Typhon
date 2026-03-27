import asyncio

from lsprotocol import types
from pygls.lsp.client import LanguageClient

from Typhon.LanguageServer._utils.path import path_to_uri
from .utils import (
    start_initialize_open_typhon_connection_client,
    ensure_exit,
    sample_workspace,
)


trigger_signature_help_file = sample_workspace / "trigger_signature_help.typh"

type SignatureHelpResult = types.SignatureHelp | None


async def request_signature_help(
    client: LanguageClient,
    uri: str,
    line: int,
    character: int,
    context: types.SignatureHelpContext | None = None,
) -> SignatureHelpResult:
    async with asyncio.timeout(10):
        return await client.text_document_signature_help_async(
            types.SignatureHelpParams(
                text_document=types.TextDocumentIdentifier(uri=uri),
                position=types.Position(line=line, character=character),
                context=context,
            )
        )


async def request_trigger_signature_help(
    client: LanguageClient,
    trigger_uri: str,
    line: int,
    character: int,
) -> SignatureHelpResult:
    client.text_document_did_change(
        types.DidChangeTextDocumentParams(
            text_document=types.VersionedTextDocumentIdentifier(
                version=2,
                uri=trigger_uri,
            ),
            content_changes=[
                types.TextDocumentContentChangePartial(
                    range=types.Range(
                        start=types.Position(line=line, character=character),
                        end=types.Position(line=line, character=character),
                    ),
                    text="()",
                    range_length=0,
                )
            ],
        )
    )
    result = await request_signature_help(
        client,
        trigger_uri,
        line=line,
        character=character + 1,
        context=types.SignatureHelpContext(
            trigger_kind=types.SignatureHelpTriggerKind.TriggerCharacter,
            trigger_character="(",
            is_retrigger=False,
        ),
    )
    return result


def assert_no_mangled_names(sig: types.SignatureInformation):
    assert "_typh_" not in sig.label, f"Mangled name in label: '{sig.label}'"
    if sig.documentation is not None:
        doc_text = (
            sig.documentation
            if isinstance(sig.documentation, str)
            else sig.documentation.value
        )
        assert "_typh_" not in doc_text, f"Mangled name in documentation: '{doc_text}'"
    if sig.parameters is not None:
        for param in sig.parameters:
            if isinstance(param.label, str):
                assert "_typh_" not in param.label, (
                    f"Mangled name in param label: '{param.label}'"
                )


def test_signature_help_trigger_paren_e2e():
    async def run_test() -> None:
        client, _ = await start_initialize_open_typhon_connection_client(
            root_dir=sample_workspace,
            open_file=trigger_signature_help_file,
        )
        try:
            trigger_uri = path_to_uri(trigger_signature_help_file)
            result = await request_trigger_signature_help(
                client,
                trigger_uri,
                line=4,
                character=17,
            )
            assert result is not None, "Signature help result is None"
            assert len(result.signatures) > 0, "No signatures returned"
            sig = result.signatures[0]
            assert_no_mangled_names(sig)
        finally:
            await ensure_exit(client)

    asyncio.run(run_test())
