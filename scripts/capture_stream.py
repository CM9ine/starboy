#!/usr/bin/env python3
"""Capture a Claude Code stream-json response without modifying stdout."""

from __future__ import annotations

import argparse
import subprocess
import sys
import threading
from pathlib import Path


def copy_stderr(source: object, destination: Path) -> None:
    with destination.open("wb") as output:
        while chunk := source.read(8192):  # type: ignore[union-attr]
            output.write(chunk)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt")
    parser.add_argument("output_path", type=Path)
    args = parser.parse_args()

    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path = args.output_path.with_name(args.output_path.name + ".stderr")
    process = subprocess.Popen(
        [
            "claude",
            "--print",
            "--output-format",
            "stream-json",
            "--verbose",
            "--permission-mode",
            "bypassPermissions",
            args.prompt,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdout is not None
    assert process.stderr is not None

    stderr_thread = threading.Thread(
        target=copy_stderr, args=(process.stderr, stderr_path), daemon=True
    )
    stderr_thread.start()

    lines = 0
    with args.output_path.open("wb") as output:
        for line in iter(process.stdout.readline, b""):
            output.write(line)
            output.flush()
            lines += 1

    exit_code = process.wait()
    stderr_thread.join()
    print(f"exit code: {exit_code}")
    print(f"lines captured: {lines}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
