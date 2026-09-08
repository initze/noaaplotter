#!/usr/bin/env python3
"""Bump the package version in pyproject.toml and print the new version.

The current version is read from the file (source of truth), so this always
works relative to whatever version is currently set:

    python scripts/bump_version.py --patch    # 0.6.0 -> 0.6.1
    python scripts/bump_version.py --minor    # 0.6.0 -> 0.7.0
    python scripts/bump_version.py --major    # 0.6.0 -> 1.0.0

Stdlib only; used directly by .github/workflows/create_release.yml.
"""

import argparse
import re
from pathlib import Path

VERSION_RE = re.compile(r'(?m)^version\s*=\s*"\d+\.\d+\.\d+"')


def bump_version(text: str, mode: str) -> str:
    """Return the new version string, given the file content and a bump mode."""
    match = re.search(r'version\s*=\s*"(\d+)\.(\d+)\.(\d+)"', text)
    if match is None:
        raise SystemExit('ERROR: no `version = "X.Y.Z"` line found in pyproject.toml')
    major, minor, patch = (int(g) for g in match.groups())
    if mode == "major":
        major, minor, patch = major + 1, 0, 0
    elif mode == "minor":
        minor, patch = minor + 1, 0
    else:  # patch
        patch += 1
    return f"{major}.{minor}.{patch}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--major", action="store_const", dest="mode", const="major")
    group.add_argument("--minor", action="store_const", dest="mode", const="minor")
    group.add_argument("--patch", action="store_const", dest="mode", const="patch")
    parser.add_argument("--file", default="pyproject.toml", help="Path to pyproject.toml")
    args = parser.parse_args()

    path = Path(args.file)
    text = path.read_text(encoding="utf-8")
    new_version = bump_version(text, args.mode)
    new_text, n_subs = VERSION_RE.subn(f'version = "{new_version}"', text, count=1)
    if n_subs != 1:
        raise SystemExit(f"ERROR: could not write version in {path}")
    path.write_text(new_text, encoding="utf-8")
    print(new_version)


if __name__ == "__main__":
    main()
