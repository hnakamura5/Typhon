from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
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
    typecheck_ms: float
    pyrefly_ms: float
    total_ms: float


def generate_large_typhon_source(target_lines: int) -> str:
    lines: list[str] = [
        "# Auto-generated benchmark source.",
        "# Includes a broad set of syntax elements and non-trivial data flow.",
        "",
        "class BenchState {",
        "    var base: int;",
        "    var history: list[int];",
        "",
        "    def __init__(base: int) {",
        "        self.base = base",
        "        self.history = []",
        "    }",
        "",
        "    def update(delta: int) -> int {",
        "        self.base = self.base + delta",
        "        self.history.append(self.base)",
        "        return self.base",
        "    }",
        "",
        "    def tail_sum(limit: int) -> int {",
        "        var acc = 0",
        "        for (let v in self.history) {",
        "            if (v > limit) {",
        "                acc = acc + v",
        "            }",
        "        }",
        "        return acc",
        "    }",
        "}",
        "",
        "def bench_seed_mix(x: int, seed: int) -> int {",
        "    var total = x + seed",
        "    var i = 0",
        "    while (i < 3) {",
        "        total = total + (i * seed)",
        "        i = i + 1",
        "    }",
        "",
        "    match (total % 4) {",
        "        case (0) {",
        "            total = total + 7",
        "        }",
        "        case (1) {",
        "            total = total - 3",
        "        }",
        "        case (_) {",
        "            total = total + 1",
        "        }",
        "    }",
        "",
        "    return total",
        "}",
    ]
    idx = 0
    while len(lines) < target_lines:
        lines.extend(
            [
                "",
                f"def bench_func_{idx}(x: int, seed: int) -> int {{",
                "    var state = BenchState(seed)",
                "    var values = [x, seed, x + seed, (x * 2) - seed]",
                "    var acc = 0",
                "",
                "    for (let v in values) {",
                "        if (v % 2 == 0) {",
                "            acc = acc + state.update(v // 2)",
                "        } elif (v > 0) {",
                "            acc = acc + state.update(v)",
                "        } else {",
                "            acc = acc + state.update(1)",
                "        }",
                "    }",
                "",
                "    var folded = 0",
                "    let stream = (for (let n in range(0, 6))",
                "                     if (n % 2 == 0)",
                "                         yield bench_seed_mix(n + acc, seed))",
                "    for (let item in stream) {",
                "        folded = folded + item",
                "    }",
                "",
                "    try {",
                f"        folded = folded // (seed - {(idx % 5) - 2})",
                "    } except (ZeroDivisionError) {",
                "        folded = folded + state.tail_sum(acc // 3)",
                "    } finally {",
                "        folded = folded + 1",
                "    }",
                "",
                "    match (folded % 3) {",
                "        case (0) {",
                "            folded = folded + acc",
                "        }",
                "        case (1) {",
                "            folded = folded - acc // 2",
                "        }",
                "        case (_) {",
                "            folded = folded + seed",
                "        }",
                "    }",
                "",
                "    return folded",
                "}",
                f"let bench_value_{idx} = bench_func_{idx}({idx % 23}, {(idx % 11) + 1})",
                f"let bench_check_{idx} = bench_seed_mix(bench_value_{idx}, {(idx % 7) + 2})",
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
    run_typecheck: bool,
    run_pyrefly: bool,
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

    if run_typecheck:
        subprocess.run(
            ["basedpyright", translated_file.as_posix()],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    t6 = perf_counter()

    end = perf_counter()

    pyrefly_ms = 0.0
    if run_pyrefly:
        pyrefly_t0 = perf_counter()
        pyrefly_run = subprocess.run(
            [
                sys.executable,
                "-m",
                "pyrefly",
                "check",
                "--output-format",
                "json",
                translated_file.as_posix(),
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        pyrefly_t1 = perf_counter()
        pyrefly_ms = (pyrefly_t1 - pyrefly_t0) * 1000
    return PhaseTimes(
        parse_ms=(t1 - t0) * 1000,
        transform_ms=(t2 - t1) * 1000,
        unparse_ms=(t3 - t2) * 1000,
        map_ms=(t4 - t3) * 1000,
        write_ms=(t5 - t4) * 1000,
        typecheck_ms=(t6 - t5) * 1000,
        pyrefly_ms=pyrefly_ms,
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
    run_typecheck: bool,
    run_pyrefly: bool,
) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)

    source_file = output_dir / f"generated_{line_count}_lines.typh"
    translated_file = output_dir / f"generated_{line_count}_lines.py"

    if run_typecheck and shutil.which("basedpyright") is None:
        print("basedpyright command not found; skipping type-check phase.")
        run_typecheck = False
    if run_pyrefly and shutil.which("pyrefly") is None:
        print("pyrefly command not found; skipping pyrefly reference phase.")
        run_pyrefly = False

    source_text = generate_large_typhon_source(line_count)
    source_file.write_text(source_text, encoding="utf-8")

    print(f"Generated source: {source_file}")
    print(f"Generated line count: {len(source_text.splitlines())}")
    print(f"Output translated file: {translated_file}")
    print(
        "Benchmark config: "
        f"iterations={iterations}, warmup={warmup}, "
        f"run_mapping={run_mapping}, run_typecheck={run_typecheck}, "
        f"run_pyrefly={run_pyrefly}"
    )

    for idx in range(warmup):
        _run_one_iteration(
            source_file=source_file,
            source_text=source_text,
            translated_file=translated_file,
            run_mapping=run_mapping,
            run_typecheck=run_typecheck,
            run_pyrefly=run_pyrefly,
        )
        print(f"Warmup {idx + 1}/{warmup} completed.")

    runs: list[PhaseTimes] = []
    for idx in range(iterations):
        result = _run_one_iteration(
            source_file=source_file,
            source_text=source_text,
            translated_file=translated_file,
            run_mapping=run_mapping,
            run_typecheck=run_typecheck,
            run_pyrefly=run_pyrefly,
        )
        runs.append(result)
        print(f"Run {idx + 1}/{iterations}: total={result.total_ms:.2f} ms")

    parse_values = [r.parse_ms for r in runs]
    transform_values = [r.transform_ms for r in runs]
    unparse_values = [r.unparse_ms for r in runs]
    map_values = [r.map_ms for r in runs]
    write_values = [r.write_ms for r in runs]
    typecheck_values = [r.typecheck_ms for r in runs]
    pyrefly_values = [r.pyrefly_ms for r in runs]
    total_values = [r.total_ms for r in runs]

    print("\n=== Benchmark Summary ===")
    print(_format_stats("parse", parse_values))
    print(_format_stats("transform", transform_values))
    print(_format_stats("unparse", unparse_values))
    print(_format_stats("map", map_values))
    print(_format_stats("write", write_values))
    print(_format_stats("typecheck", typecheck_values))
    print(_format_stats("pyrefly(ref: not included in total)", pyrefly_values))
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
    parser.add_argument(
        "--skip-typecheck",
        action="store_true",
        help="Skip generated Python type-check benchmark phase (basedpyright).",
    )
    parser.add_argument(
        "--skip-pyrefly",
        action="store_true",
        help="Skip pyrefly reference timing phase (not included in total).",
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
        run_typecheck=not args.skip_typecheck,
        run_pyrefly=not args.skip_pyrefly,
    )


if __name__ == "__main__":
    raise SystemExit(main())
