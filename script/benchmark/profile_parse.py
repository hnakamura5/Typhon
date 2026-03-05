from __future__ import annotations

import argparse
import cProfile
import io
import pstats
from pathlib import Path
from typing import Literal
import ast

from script._util import get_project_root
from src.Typhon.Grammar.parser import parse_file
from src.Typhon.Grammar.unparse_custom import unparse_custom
from src.Typhon.SourceMap.ast_match_based_map import map_from_translated
from src.Typhon.Transform.transform import transform
from .parse_large_file import generate_large_typhon_source


def _prepare_source(
    input_file: Path | None, lines: int, output_dir: Path
) -> tuple[Path, str]:
    output_dir.mkdir(parents=True, exist_ok=True)

    if input_file is not None:
        source_file = input_file
        source_text = source_file.read_text(encoding="utf-8")
        return source_file, source_text

    source_file = output_dir / f"profile_generated_{lines}_lines.typh"
    source_text = generate_large_typhon_source(lines)
    source_file.write_text(source_text, encoding="utf-8")
    return source_file, source_text


def _run_parse(source_file: Path):
    return parse_file(source_file.as_posix(), verbose=False)


def _run_transform(module: ast.Module) -> None:
    transform(module, ignore_error=True)


def _run_unparse(module: ast.Module) -> str:
    return unparse_custom(module)


def _run_map(
    module: ast.Module, source_text: str, source_file: Path, translated: str
) -> None:
    map_from_translated(
        module,
        source_text,
        source_file.as_posix(),
        translated,
    )


def _run_phase(
    phase: Literal["parse", "transform", "unparse", "map", "all"],
    source_file: Path,
    source_text: str,
) -> None:
    if phase == "parse":
        _run_parse(source_file)
        return

    module = _run_parse(source_file)

    if phase == "transform":
        _run_transform(module)
        return

    _run_transform(module)
    translated = _run_unparse(module)

    if phase == "unparse":
        return

    _run_map(module, source_text, source_file, translated)


def _print_stats(
    profile: cProfile.Profile,
    *,
    sort_key: Literal["cumtime", "tottime"],
    limit: int,
) -> None:
    output = io.StringIO()
    stats = pstats.Stats(profile, stream=output)
    stats.strip_dirs().sort_stats(sort_key).print_stats(limit)
    print(output.getvalue())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Function-level profiler for Typhon parse/translate phases."
    )
    parser.add_argument(
        "--phase",
        choices=["parse", "transform", "unparse", "map", "all"],
        default="parse",
        help="Phase to profile.",
    )
    parser.add_argument(
        "--input-file",
        type=Path,
        default=None,
        help="Existing Typhon source file to profile.",
    )
    parser.add_argument(
        "--lines",
        type=int,
        default=1_000,
        help="Generated source line count when --input-file is omitted.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(get_project_root()) / "temp" / "benchmark",
        help="Output directory for generated source file.",
    )
    parser.add_argument(
        "--sort",
        choices=["cumtime", "tottime"],
        default="cumtime",
        help="Sort key for profile report.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Number of functions to display.",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=1,
        help="Warmup runs before profiling.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.lines <= 0:
        print("--lines must be > 0")
        return 2
    if args.limit <= 0:
        print("--limit must be > 0")
        return 2
    if args.warmup < 0:
        print("--warmup must be >= 0")
        return 2

    source_file, source_text = _prepare_source(
        input_file=args.input_file,
        lines=args.lines,
        output_dir=args.output_dir,
    )

    print(f"Profile source: {source_file}")
    print(f"Profile phase: {args.phase}")
    print(f"Line count: {len(source_text.splitlines())}")
    print(f"Warmup: {args.warmup}")

    for _ in range(args.warmup):
        _run_phase(args.phase, source_file, source_text)

    profile = cProfile.Profile()
    profile.enable()
    _run_phase(args.phase, source_file, source_text)
    profile.disable()

    print("\n=== cProfile (cumtime) ===")
    _print_stats(profile, sort_key="cumtime", limit=args.limit)
    print("\n=== cProfile (tottime) ===")
    _print_stats(profile, sort_key="tottime", limit=args.limit)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
