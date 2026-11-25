#!/usr/bin/env python3
"""Fold the CHANGELOG.md "Unreleased" section into the new version heading.

Run from the release workflow (and available by hand):

    python scripts/fold_changelog.py 1.2.0 [--date 2026-11-25]

Effects on CHANGELOG.md:
  * ``## Unreleased`` becomes ``## <version> — <date>``
  * a fresh, empty ``## Unreleased`` section is inserted above it

The script is deliberately a no-op (exit 0) when there is nothing to fold:
either the file has no ``## Unreleased`` heading, or its body is empty or
just the placeholder line. Maintenance releases (dependency bumps only)
then leave the changelog untouched instead of creating an empty heading.
"""
import argparse
import datetime as dt
import re
import sys
from pathlib import Path

CHANGELOG = Path(__file__).resolve().parents[1] / "CHANGELOG.md"
HEADING = "## Unreleased"
PLACEHOLDERS = {"", "_nothing yet._", "_nothing yet_", "<!-- add entries here -->"}


def fold(text: str, version: str, date: str) -> tuple[str, bool]:
    """Return (new_text, changed). Pure function — easy to test."""
    m = re.search(rf"^{re.escape(HEADING)}[ \t]*$", text, re.MULTILINE)
    if not m:
        return text, False

    body_start = m.end()
    nxt = re.search(r"^## ", text[body_start:], re.MULTILINE)
    body_end = body_start + nxt.start() if nxt else len(text)
    body = text[body_start:body_end]

    if body.strip().lower() in PLACEHOLDERS:
        return text, False

    body = body.strip("\n")
    new_section = (
        f"{HEADING}\n\n_Nothing yet._\n\n"
        f"## {version} — {date}\n\n{body}\n\n"
    )
    return text[: m.start()] + new_section + text[body_end:], True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("version", help="version being released, e.g. 1.2.0")
    ap.add_argument("--date", default=dt.date.today().isoformat(),
                    help="release date (default: today, YYYY-MM-DD)")
    ap.add_argument("--file", default=str(CHANGELOG), help=argparse.SUPPRESS)
    args = ap.parse_args()

    path = Path(args.file)
    text = path.read_text(encoding="utf-8")
    new_text, changed = fold(text, args.version, args.date)
    if not changed:
        print("CHANGELOG.md: nothing under '## Unreleased' — not modified.")
        return 0

    path.write_text(new_text, encoding="utf-8", newline="\n")
    heads = re.findall(r"^## .+$", new_text, re.MULTILINE)
    print(f"CHANGELOG.md: folded into '## {args.version} — {args.date}'")
    print("headings now:", ", ".join(h.lstrip("# ").strip() for h in heads[:4]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
