#!/usr/bin/env python
"""Generate docs/cli.md from the live CLI.

Run (from the repo root):
    uv run python scripts/gen_cli_docs.py

Subprocesses the installed `noaaplotter --help` for the app + each command.
The captured output is normalised (line endings, ANSI escapes, box-drawing
chars, trailing whitespace) so the result is byte-identical on Windows,
macOS, and Linux — the committed docs/cli.md never drifts by host, and CI
can deterministically re-run this script and compare.
"""

from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]  # repo root

# Deterministic, host-independent help output from rich / Typer.
_DETERMINISTIC_ENV = {**os.environ, "TERM": "dumb", "NO_COLOR": "1", "COLUMNS": "80"}

# ANSI SGR colour escapes (e.g. ESC[1;33m ... ESC[0m). Build the ESC byte
# explicitly so the pattern is unambiguous.
_ESC = "\x1b"
_ANSI_RE = re.compile(_ESC + r"\[[0-9;]*m")

# Windows CRLF, old-Mac CR, or Unix LF → single LF.
_CRLF_RE = re.compile("\r\n|\r|\n")

# rich sometimes renders rounded box-drawing chars and sometimes straight ones
# depending on host/width. Map the rounded set to the straight set so the
# output is byte-identical on every platform.
_BOX_ROUNDED = "╭╮╯╰"
_BOX_STRAIGHT = "┌┐┘└"
_BOX = str.maketrans(dict(zip(_BOX_ROUNDED, _BOX_STRAIGHT)))


def _clean(text: str) -> str:
    """Normalise captured CLI output to deterministic, portable text."""
    text = _CRLF_RE.sub("\n", text)                         # line endings
    text = _ANSI_RE.sub("", text)                            # drop ANSI colours
    text = text.translate(_BOX)                              # box-drawing chars
    text = "\n".join(line.rstrip() for line in text.split("\n"))  # trailing spaces
    return text.strip() + "\n"


def _cli_exe() -> list[str]:
    """Return the argv prefix that runs the installed `noaaplotter` CLI."""
    env_dir = os.environ.get("VIRTUAL_ENV") or str(REPO_ROOT / ".venv")
    base = pathlib.Path(env_dir)
    for sub in ("Scripts", "bin"):
        for name in ("noaaplotter", "noaaplotter.exe"):
            p = base / sub / name
            if p.is_file():
                return [str(p)]
    return [sys.executable, "-m", "noaaplotter"]  # any env with the package


def _run(args: list[str]) -> str:
    out = subprocess.run(
        _cli_exe() + args,
        capture_output=True, text=True, timeout=30,
        cwd=str(REPO_ROOT), env=_DETERMINISTIC_ENV,
    )
    return _clean((out.stdout or "") + (out.stderr or ""))


_LEADS = {
    "download-data": (
        "Download weather data to a Parquet file — a NOAA station **or** a "
        "coordinate-based source (Open-Meteo, CDS/ERA5)."
    ),
    "plot-daily": (
        "Create a daily temperature/precipitation plot vs. climate: static PNG "
        "(matplotlib, default) or interactive HTML (Plotly). Records show as "
        "red (high) / blue (low) ticks and a 7-day rolling precipitation sum "
        "is included. `--full-series` embeds the entire record for Plotly."
    ),
    "plot-monthly": (
        "Create a monthly temperature/precipitation bar chart."
    ),
}

_COMMANDS = ["download-data", "plot-daily", "plot-monthly"]

_HEADER = """<!--
  GENERATED. Do not hand-edit the code blocks — change the CLI, then run:

      uv run python scripts/gen_cli_docs.py

  This script captures the exact `--help` output from the installed CLI (via a
  subprocess) and normalises it so the text is byte-identical on Windows,
  macOS, and Linux. CI re-runs it and fails the build if docs/cli.md drifted.
-->

# CLI reference

`noaaplotter` is a Typer application. Every command also accepts `-h` /
`--help`, and the app supports `--install-completion` / `--show-completion`
for shell integration.

The console blocks below are verbatim from the running CLI, so they always
match the installed version.

!!! tip
    Run any command with `--help` for the options of that specific command.
"""


def main() -> None:
    print("CLI prefix:", " ".join(_cli_exe()))
    out = [_HEADER]

    out += [
        "## `noaaplotter --help`",
        "",
        "```console",
        _run(["--help"]).rstrip(),
        "```",
        "",
    ]

    for c in _COMMANDS:
        out += [
            f"## `noaaplotter {c}`",
            "",
            _LEADS.get(c, ""),
            "",
            "```console",
            _run([c, "--help"]).rstrip(),
            "```",
            "",
        ]

    text = "\n".join(out)
    path = REPO_ROOT / "docs" / "cli.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"Wrote {path} ({len(text)} chars, {len(_COMMANDS)} commands + app)")


if __name__ == "__main__":
    main()
