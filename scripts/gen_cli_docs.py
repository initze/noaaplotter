#!/usr/bin/env python
"""Generate docs/cli.md from the live CLI.

Run (from the repo root):
    uv run python scripts/gen_cli_docs.py

Subprocesses the installed `noaaplotter --help` for the app + each command.
This captures the exact text users see — the page can never drift from the
CLI. Regenerate after changing CLI options instead of hand-editing docs.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]  # repo root

# The console script lives in a venv. Find it via env, or fall back to `python -m`.
def _cli_exe() -> list[str]:
    # Prefer the venv's `noaaplotter` console script (Windows .exe).
    # We look for a `Scripts/noaaplotter(.exe)` on PATH or in the project venv.
    env_dir = os.environ.get("VIRTUAL_ENV") or str(REPO_ROOT / ".venv")
    base = pathlib.Path(env_dir)
    for sub in ("Scripts", "bin"):
        p = base / sub / "noaaplotter"
        if p.is_file():
            return [str(p)]
        p = base / sub / "noaaplotter.exe"
        if p.is_file():
            return [str(p)]
    # Fall back: `python -m noaaplotter` (works in any env that has the package).
    py = sys.executable
    return [py, "-m", "noaaplotter"]


def _run(args: list[str]) -> str:
    cmd = _cli_exe() + args
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=str(REPO_ROOT))
    text = (out.stdout or "") + (out.stderr or "")
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


LEADS = {
    "download-data": (
        "Download weather data to a Parquet file — NOAA station data **or** "
        "coordinate-based (Open-Meteo, CDS/ERA5)."
    ),
    "plot-daily": (
        "Create a daily temperature/precipitation plot vs. climate: static PNG "
        "(matplotlib, default) or interactive HTML (Plotly). Records are marked "
        "red/blue against the climate baseline."
    ),
    "plot-monthly": (
        "Create a monthly temperature/precipitation bar chart. Use "
        "`-anomaly` to show anomalies against a 30-day trailing mean."
    ),
}

HEADER = """<!--
  GENERATED. Do not hand-edit the code blocks — change the CLI, then run:

      uv run python scripts/gen_cli_docs.py

  This script captures the *exact* `--help` output from the installed CLI,
  so this page always matches what a user sees.
-->

# CLI reference

`noaaplotter` is a Typer application. Every command also accepts `-h` /
`--help`, and the app supports `--install-completion` / `--show-completion`
for shell integration.

The code blocks below are verbatim from the running CLI.

!!! tip
    Run any command with `--help` for the options of that command.
"""


def main() -> None:
    cli = _cli_exe()
    print("Using CLI:", " ".join(cli))

    out = [HEADER, ""]

    # App-level help.
    out += [
        "## `noaaplotter --help`",
        "",
        "```console",
        _run(["--help"]),
        "```",
        "",
    ]

    # Enumerate commands (from the app --help listing).
    help_text = _run(["--help"])
    commands = ["download-data", "plot-daily", "plot-monthly"]
    for c in commands:
        out += [
            f"## `noaaplotter {c}`",
            "",
            LEADS.get(c, ""),
            "",
            "```console",
            _run([c, "--help"]),
            "```",
            "",
        ]

    text = "\n".join(out)
    path = REPO_ROOT / "docs" / "cli.md"
    path.write_text(text, encoding="utf-8")
    print(f"Wrote {path} ({len(text)} chars)")


if __name__ == "__main__":
    main()
