import asyncio
from collections.abc import Sequence

from lsprotocol import types
from pygls.lsp.client import LanguageClient

from Typhon.Driver.debugging import debug_verbose_print
from Typhon.LanguageServer._utils.path import path_to_uri
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


def _assert_no_mangled_name_in_labels(hints: Sequence[types.InlayHint]) -> None:
    for hint in hints:
        assert "_typh_" not in _label_to_text(hint.label)


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
            _assert_no_mangled_name_in_labels(hints)
            # Keep this in sync with the final response logged in private/server.log.
            assert len(hints) == 16

            # def add(x: int, y: int) { ... }
            _assert_hint_exists(
                hints,
                kind=types.InlayHintKind.Type,
                line=0,
                character=23,
                label_contains="-> int",
            )
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
            _assert_hint_exists(
                hints,
                kind=types.InlayHintKind.Type,
                line=4,
                character=9,
                label_contains=": int",
            )
            # var out = ...
            _assert_hint_exists(
                hints,
                kind=types.InlayHintKind.Type,
                line=5,
                character=7,
                label_contains="int",
            )
            # var rec = ...
            _assert_hint_exists(
                hints,
                kind=types.InlayHintKind.Type,
                line=7,
                character=7,
                label_contains=": {| a: int, b: int |}",
            )
            _assert_hint_exists(
                hints,
                kind=types.InlayHintKind.Type,
                line=7,
                character=13,
                label_contains=": int",
            )
            _assert_hint_exists(
                hints,
                kind=types.InlayHintKind.Type,
                line=7,
                character=20,
                label_contains=": int",
            )

            # let (c: int, d) = ...
            _assert_hint_exists(
                hints,
                kind=types.InlayHintKind.Type,
                line=9,
                character=14,
                label_contains=": Final",  # TODO: "Final" is not ideal. Should modify backend basedpyright.
            )

            # for (let i in range(0, 10)) { ... }
            _assert_hint_exists(
                hints,
                kind=types.InlayHintKind.Type,
                line=11,
                character=10,
                label_contains=": Final",  # TODO: "Final" is not ideal. Should modify backend basedpyright.
            )

            # let j = i
            _assert_hint_exists(
                hints,
                kind=types.InlayHintKind.Type,
                line=12,
                character=9,
                label_contains=": int",
            )

            # out = add(out, j)
            _assert_hint_exists(
                hints,
                kind=types.InlayHintKind.Type,
                line=13,
                character=7,
                label_contains=": int",
            )
            _assert_hint_exists(
                hints,
                kind=types.InlayHintKind.Parameter,
                line=5,
                character=14,
                label_contains="x=",
            )
            _assert_hint_exists(
                hints,
                kind=types.InlayHintKind.Parameter,
                line=5,
                character=21,
                label_contains="y=",
            )
            _assert_hint_exists(
                hints,
                kind=types.InlayHintKind.Parameter,
                line=13,
                character=14,
                label_contains="x=",
            )
            _assert_hint_exists(
                hints,
                kind=types.InlayHintKind.Parameter,
                line=13,
                character=19,
                label_contains="y=",
            )
        finally:
            await ensure_exit(client)

    asyncio.run(run_test())
