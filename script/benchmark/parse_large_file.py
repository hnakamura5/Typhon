from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from time import perf_counter

from script._util import get_project_root
from src.Typhon.Grammar.parser import parse_file
from src.Typhon.Grammar.unparse_custom import unparse_custom
from src.Typhon.SourceMap.ast_match_based_map import map_from_translated
from src.Typhon.Transform.transform import transform


@dataclass
class PhaseTimes:
    parse_ms: float
    transform_ms: float
    unparse_ms: float
    map_ms: float
    write_ms: float
    total_ms: float


def generate_large_typhon_source(target_lines: int) -> str:
    lines: list[str] = ["# Auto-generated benchmark source."]
    idx = 0
    while len(lines) < target_lines:
        lines.extend(
            [
                f"def bench_func_{idx}(x: int) -> int {{",
                f"    var y = x + {idx % 17}",
                "    if (y > 10) {",
                "        y = y - 3",
                "    }",
                "    return y",
                "}",
                f"let bench_value_{idx} = bench_func_{idx}({idx % 23})",
                "",
            ]
        )
        idx += 1
    return "\n".join(lines) + "\n"


def _run_one_iteration(
    source_file: Path,
    source_text: str,
    translated_file: Path,
    run_mapping: bool,
) -> PhaseTimes:
    begin = perf_counter()

    t0 = perf_counter()
    module = parse_file(source_file.as_posix(), verbose=False)
    t1 = perf_counter()

    transform(module, ignore_error=True)
    t2 = perf_counter()

    translated = unparse_custom(module)
    t3 = perf_counter()

    if run_mapping:
        map_from_translated(
            module,
            source_text,
            source_file.as_posix(),
            translated,
        )
    t4 = perf_counter()

    translated_file.write_text(translated, encoding="utf-8")
    t5 = perf_counter()

    end = perf_counter()
    return PhaseTimes(
        parse_ms=(t1 - t0) * 1000,
        transform_ms=(t2 - t1) * 1000,
        unparse_ms=(t3 - t2) * 1000,
        map_ms=(t4 - t3) * 1000,
        write_ms=(t5 - t4) * 1000,
        total_ms=(end - begin) * 1000,
    )


def _format_stats(label: str, values: list[float]) -> str:
    return (
        f"{label}: avg={mean(values):8.2f} ms "
        f"min={min(values):8.2f} ms max={max(values):8.2f} ms"
    )


def run_benchmark(
    line_count: int,
    iterations: int,
    warmup: int,
    output_dir: Path,
    run_mapping: bool,
) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)

    source_file = output_dir / f"generated_{line_count}_lines.typh"
    translated_file = output_dir / f"generated_{line_count}_lines.py"

    source_text = generate_large_typhon_source(line_count)
    source_file.write_text(source_text, encoding="utf-8")

    print(f"Generated source: {source_file}")
    print(f"Generated line count: {len(source_text.splitlines())}")
    print(f"Output translated file: {translated_file}")
    print(
        f"Benchmark config: iterations={iterations}, warmup={warmup}, run_mapping={run_mapping}"
    )

    for idx in range(warmup):
        _run_one_iteration(
            source_file=source_file,
            source_text=source_text,
            translated_file=translated_file,
            run_mapping=run_mapping,
        )
        print(f"Warmup {idx + 1}/{warmup} completed.")

    runs: list[PhaseTimes] = []
    for idx in range(iterations):
        result = _run_one_iteration(
            source_file=source_file,
            source_text=source_text,
            translated_file=translated_file,
            run_mapping=run_mapping,
        )
        runs.append(result)
        print(f"Run {idx + 1}/{iterations}: total={result.total_ms:.2f} ms")

    parse_values = [r.parse_ms for r in runs]
    transform_values = [r.transform_ms for r in runs]
    unparse_values = [r.unparse_ms for r in runs]
    map_values = [r.map_ms for r in runs]
    write_values = [r.write_ms for r in runs]
    total_values = [r.total_ms for r in runs]

    print("\n=== Benchmark Summary ===")
    print(_format_stats("parse", parse_values))
    print(_format_stats("transform", transform_values))
    print(_format_stats("unparse", unparse_values))
    print(_format_stats("map", map_values))
    print(_format_stats("write", write_values))
    print(_format_stats("total", total_values))

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark parse/transform/unparse for a generated large Typhon source file."
        )
    )
    parser.add_argument(
        "--lines",
        type=int,
        default=1_000,
        help="Number of lines for generated Typhon source.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=3,
        help="Number of measured benchmark iterations.",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=1,
        help="Number of warmup iterations before measurement.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(get_project_root()) / "temp" / "benchmark",
        help="Directory to place generated benchmark input and translated output.",
    )
    parser.add_argument(
        "--skip-mapping",
        action="store_true",
        help="Skip source-map generation benchmark phase.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.lines <= 0:
        print("--lines must be > 0")
        return 2
    if args.iterations <= 0:
        print("--iterations must be > 0")
        return 2
    if args.warmup < 0:
        print("--warmup must be >= 0")
        return 2

    return run_benchmark(
        line_count=args.lines,
        iterations=args.iterations,
        warmup=args.warmup,
        output_dir=args.output_dir,
        run_mapping=not args.skip_mapping,
    )


if __name__ == "__main__":
    raise SystemExit(main())
