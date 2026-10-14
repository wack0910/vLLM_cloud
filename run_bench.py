"""Load a YAML config and run the official `vllm bench serve` command.

No model loading, request generation, or metric calculation happens here.
Requires the same environment as the installed vLLM (which depends on PyYAML).
"""

from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
from pathlib import Path


def config_to_args(config: dict) -> list[str]:
    """Convert only enabled YAML options into official CLI arguments."""
    args: list[str] = []
    for key, value in config.items():
        if not isinstance(key, str) or not key or key.startswith("-"):
            raise ValueError(f"Invalid CLI option name: {key!r}")
        if value is None:
            continue
        option = "--" + key.replace("_", "-")
        if isinstance(value, bool):
            # These benchmark options are store_true flags: false means omit.
            if value:
                args.append(option)
        elif isinstance(value, dict):
            args.extend([option, json.dumps(value, ensure_ascii=False)])
        elif isinstance(value, list):
            if value:
                args.append(option)
                args.extend(str(item) for item in value)
        else:
            args.extend([option, str(value)])
    return args


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("bench.yaml"))
    parser.add_argument("--dry-run", action="store_true", help="Print command only")
    known, overrides = parser.parse_known_args()
    if overrides and overrides[0] == "--":
        overrides = overrides[1:]
    if "--config" in overrides:
        parser.error("Only one YAML config may be used.")
    try:
        import yaml
    except ImportError:
        parser.error("PyYAML is missing. Run in your installed vLLM environment.")

    try:
        with known.config.open(encoding="utf-8-sig") as handle:
            config = yaml.safe_load(handle)
        if not isinstance(config, dict):
            parser.error("The YAML file must contain a mapping of CLI options.")
        # Overrides appear last, so ordinary scalar CLI options take precedence.
        command = ["vllm", "bench", "serve", *config_to_args(config), *overrides]
    except (OSError, ValueError, yaml.YAMLError) as error:
        parser.error(str(error))

    print(shlex.join(command), flush=True)
    if known.dry_run:
        return 0
    executable = shutil.which("vllm")
    if executable is None:
        parser.error("vllm was not found on PATH. Activate your vLLM environment.")
    command[0] = executable
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
