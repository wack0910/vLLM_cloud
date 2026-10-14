"""Task-specific /metrics recorder; NOT an official vLLM benchmark tool.

Uses Python standard library only. Run before the official benchmark, wait for
its first sample, and stop with Ctrl+C a few seconds after the benchmark ends.
Writes CSV and first/latest successful raw Prometheus snapshots.
"""

import argparse
import csv
from datetime import datetime, timezone
import math
from pathlib import Path
import re
import time
from urllib.request import urlopen


SAMPLE = re.compile(
    r'^([a-zA-Z_:][a-zA-Z0-9_:]*)(?:\{.*\})?\s+'
    r'([-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?|[-+]?Inf|NaN)(?:\s|$)'
)
SPECS = {
    "kv_cache_usage_pct": (
        ("vllm:kv_cache_usage_perc", "vllm:gpu_cache_usage_perc"), "max", 100
    ),
    "requests_running": (("vllm:num_requests_running",), "sum", 1),
    "requests_waiting": (("vllm:num_requests_waiting",), "sum", 1),
    "preemptions_total": (
        ("vllm:num_preemptions_total", "vllm:num_preemptions"), "sum", 1
    ),
    "prefix_hits_tokens_total": (
        ("vllm:prefix_cache_hits_total", "vllm:prefix_cache_hits",
         "vllm:gpu_prefix_cache_hits_total", "vllm:gpu_prefix_cache_hits"), "sum", 1
    ),
    "prefix_queries_tokens_total": (
        ("vllm:prefix_cache_queries_total", "vllm:prefix_cache_queries",
         "vllm:gpu_prefix_cache_queries_total", "vllm:gpu_prefix_cache_queries"), "sum", 1
    ),
}


def parse_prometheus(body):
    samples = {}
    for line in body.splitlines():
        match = SAMPLE.match(line.strip())
        if match:
            value = float(match.group(2))
            if math.isfinite(value):
                samples.setdefault(match.group(1), []).append(value)
    return samples


def summarize(samples):
    row = {}
    for column, (aliases, reduction, scale) in SPECS.items():
        values = next((samples[name] for name in aliases if name in samples), None)
        # Missing metrics stay blank: absence is not zero usage or zero hits.
        row[column] = "" if values is None else (
            (max(values) if reduction == "max" else sum(values)) * scale
        )
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000/metrics")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--samples", type=int, default=0,
                        help="Stop after N samples; 0 records until Ctrl+C.")
    args = parser.parse_args()
    if args.interval <= 0 or args.samples < 0:
        parser.error("interval must be positive and samples must be nonnegative")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.out.exists():
        parser.error("output already exists; choose a new run directory/file")
    fields = ["timestamp_utc", "elapsed_s", "fetch_ok", "error", *SPECS]
    start = time.monotonic()
    count = 0
    successes = 0
    print(f"Recording {args.url} -> {args.out}; stop with Ctrl+C", flush=True)
    try:
        with args.out.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            while not args.samples or count < args.samples:
                row = dict.fromkeys(fields, "")
                row.update(timestamp_utc=datetime.now(timezone.utc).isoformat(),
                           elapsed_s=round(time.monotonic() - start, 3), fetch_ok=0)
                try:
                    with urlopen(args.url, timeout=5) as response:
                        body = response.read().decode("utf-8")
                    row.update(summarize(parse_prometheus(body)), fetch_ok=1)
                    if successes == 0:
                        args.out.with_suffix(".start.prom").write_text(body, encoding="utf-8")
                        missing = [key for key in SPECS if row[key] == ""]
                        print(f"First sample saved; missing metrics: {missing}", flush=True)
                    args.out.with_suffix(".end.prom").write_text(body, encoding="utf-8")
                    successes += 1
                except Exception as exc:
                    row["error"] = f"{type(exc).__name__}: {exc}"
                    if count == 0 or count % 10 == 0:
                        print(row["error"], flush=True)
                writer.writerow(row)
                handle.flush()
                count += 1
                if not args.samples or count < args.samples:
                    time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    print(f"Saved {count} samples ({successes} successful) to {args.out}", flush=True)


if __name__ == "__main__":
    main()
