# -*- coding: utf-8 -*-
"""Unit tests for scripts/fold_changelog.py (the release-time changelog fold).

The script runs inside the release workflow right before the version commit,
so a regression here would either lose release notes or add empty headings.
Pure-function tests, no network or repo state needed.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "fold_changelog", ROOT / "scripts" / "fold_changelog.py")
fold_changelog = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fold_changelog)

fold = fold_changelog.fold

SAMPLE = """# Changelog

All notable changes.

## Unreleased

- **A new thing.** Does stuff.
- **Another thing.** More stuff.

## 1.1.0 — 2026-10-13

- old entry

## 0.6.3

- older entry
"""


def test_fold_moves_entries_under_new_version_heading():
    new, changed = fold(SAMPLE, "1.2.0", "2026-12-01")

    assert changed
    assert "## 1.2.0 — 2026-12-01" in new
    # fresh empty section above the folded one
    assert new.index("## Unreleased") < new.index("## 1.2.0 — 2026-12-01")
    assert new.split("## Unreleased", 1)[1].split("## 1.2.0", 1)[0].strip() == \
        "_Nothing yet._"
    # entries landed under the new heading, not under Unreleased
    version_block = new.split("## 1.2.0 — 2026-12-01", 1)[1].split("## 1.1.0", 1)[0]
    assert "A new thing" in version_block
    assert "Another thing" in version_block
    # older sections untouched and still ordered below
    assert new.index("## 1.1.0") < new.index("## 0.6.3")
    assert "- old entry" in new and "- older entry" in new


def test_fold_is_noop_when_unreleased_is_empty():
    text = SAMPLE.replace(
        "- **A new thing.** Does stuff.\n- **Another thing.** More stuff.\n",
        "_Nothing yet._\n")
    new, changed = fold(text, "1.2.1", "2026-12-02")

    assert changed is False
    assert new == text


def test_fold_is_noop_without_unreleased_heading():
    text = "# Changelog\n\n## 1.0.0\n\n- stuff\n"
    new, changed = fold(text, "1.2.0", "2026-12-01")

    assert changed is False
    assert new == text


def test_fold_preserves_text_after_the_unreleased_block():
    new, changed = fold(SAMPLE, "1.2.0", "2026-12-01")

    assert changed
    assert new.endswith("- older entry\n")
    assert new.count("## 0.6.3") == 1
    assert new.count("## Unreleased") == 1


def test_repo_changelog_is_foldable_or_empty():
    """The checked-in CHANGELOG.md must end up in one of the two valid states."""
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## Unreleased" in text
    _, changed = fold(text, "9.9.9", "2099-01-01")
    if changed:
        # entries were pending: the fold must have produced a version heading
        assert "## 9.9.9" in _


CRLF = chr(13) + chr(10)


def test_fold_file_preserves_crlf(tmp_path):
    """A CRLF working copy must not be rewritten to LF (whole-file diff)."""
    p = tmp_path / "CHANGELOG.md"
    p.write_bytes(SAMPLE.replace("\n", CRLF).encode("utf-8"))

    assert fold_changelog.fold_file(p, "1.2.0", "2026-12-01")

    data = p.read_bytes()
    assert data.count(CRLF.encode()) == data.count(b"\n")   # no bare LF
    assert b"## 1.2.0" in data


def test_fold_file_preserves_lf(tmp_path):
    p = tmp_path / "CHANGELOG.md"
    p.write_text(SAMPLE, encoding="utf-8", newline="\n")

    assert fold_changelog.fold_file(p, "1.2.0", "2026-12-01")

    data = p.read_bytes()
    assert chr(13).encode() not in data
    assert b"## 1.2.0" in data


def test_fold_file_noop_keeps_file_byte_identical(tmp_path):
    p = tmp_path / "CHANGELOG.md"
    text = SAMPLE.replace(
        "- **A new thing.** Does stuff.\n- **Another thing.** More stuff.\n",
        "_Nothing yet._\n")
    p.write_bytes(text.replace("\n", CRLF).encode("utf-8"))
    before = p.read_bytes()

    assert fold_changelog.fold_file(p, "1.2.1", "2026-12-02") is False
    assert p.read_bytes() == before
