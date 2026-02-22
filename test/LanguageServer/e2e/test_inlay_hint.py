import asyncio
from collections.abc import Sequence

from lsprotocol import types
from pygls.lsp.client import LanguageClient

from Typhon.Driver.debugging import debug_verbose_print
from Typhon.LanguageServer.utils import path_to_uri
from .utils import (
    ensure_exit,
    run_file_dir,
    start_initialize_open_typhon_connection_client,
)


inlay_hint_file = run_file_dir / "inlay_hint_showcase.typh"


async def request_inlay_hints(
    client: LanguageClient,
    uri: str,
    end_line: int,
    end_character: int,
) -> list[types.InlayHint]:
    async with asyncio.timeout(10):
        result = await client.text_document_inlay_hint_async(
            types.InlayHintParams(
                text_document=types.TextDocumentIdentifier(uri=uri),
                range=types.Range(
                    start=types.Position(line=0, character=0),
                    end=types.Position(line=end_line, character=end_character),
                ),
            )
        )
    debug_verbose_print(f"Received inlay hint result: {result}")
    assert result is not None
    return list(result)


def _label_to_text(label: str | Sequence[types.InlayHintLabelPart]) -> str:
    if isinstance(label, str):
        return label
    return "".join(part.value for part in label)


def _assert_hint_exists(
    hints: Sequence[types.InlayHint],
    *,
    kind: types.InlayHintKind,
    line: int,
    character: int,
    label_contains: str,
) -> None:
    for hint in hints:
        if hint.kind != kind:
            continue
        if hint.position.line != line or hint.position.character != character:
            continue
        if label_contains in _label_to_text(hint.label):
            return

    observed = [
        (
            hint.kind,
            hint.position.line,
            hint.position.character,
            _label_to_text(hint.label),
        )
        for hint in hints
    ]
    assert False, (
        "Expected inlay hint was not found: "
        f"kind={kind}, pos=({line}, {character}), label_contains='{label_contains}'. "
        f"Observed={observed}"
    )


def test_inlay_hint_response_received_e2e():
    async def run_test() -> None:
        client, _ = await start_initialize_open_typhon_connection_client(
            root_dir=run_file_dir,
            open_file=inlay_hint_file,
        )
        try:
            uri = path_to_uri(inlay_hint_file)
            lines = inlay_hint_file.read_text(encoding="utf-8").splitlines()
            hints = await request_inlay_hints(
                client,
                uri,
                end_line=max(len(lines), 0),
                end_character=0,
            )
            assert isinstance(hints, list) and len(hints) > 0
            # add(1, 2)
            _assert_hint_exists(
                hints,
                kind=types.InlayHintKind.Parameter,
                line=4,
                character=16,
                label_contains="x=",
            )
            _assert_hint_exists(
                hints,
                kind=types.InlayHintKind.Parameter,
                line=4,
                character=19,
                label_contains="y=",
            )
            # var out = ...
            _assert_hint_exists(
                hints,
                kind=types.InlayHintKind.Type,
                line=5,
                character=7,
                label_contains="int",
            )
        finally:
            await ensure_exit(client)

    asyncio.run(run_test())
