"""Tests for match recorder TOML append formatting."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


RECORDER_PATH = Path(__file__).resolve().parents[1] / "match_recorder.py"
SPEC = importlib.util.spec_from_file_location("match_recorder", RECORDER_PATH)
assert SPEC and SPEC.loader
match_recorder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = match_recorder
SPEC.loader.exec_module(match_recorder)


def test_append_match_separates_entries_with_blank_line(tmp_path: Path) -> None:
    matches_path = tmp_path / "matches.toml"
    matches_path.write_text('[[match]]\nid = "0001"\n', encoding="utf-8")

    match_recorder.append_match(matches_path, '[[match]]\nid = "0002"\n')

    assert matches_path.read_text(encoding="utf-8") == (
        '[[match]]\nid = "0001"\n\n[[match]]\nid = "0002"\n'
    )


def test_append_match_does_not_duplicate_existing_blank_line(tmp_path: Path) -> None:
    matches_path = tmp_path / "matches.toml"
    matches_path.write_text('[[match]]\nid = "0001"\n\n', encoding="utf-8")

    match_recorder.append_match(matches_path, '[[match]]\nid = "0002"\n')

    assert matches_path.read_text(encoding="utf-8") == (
        '[[match]]\nid = "0001"\n\n[[match]]\nid = "0002"\n'
    )


def test_append_match_handles_missing_trailing_newline(tmp_path: Path) -> None:
    matches_path = tmp_path / "matches.toml"
    matches_path.write_text('[[match]]\nid = "0001"', encoding="utf-8")

    match_recorder.append_match(matches_path, '[[match]]\nid = "0002"\n')

    assert matches_path.read_text(encoding="utf-8") == (
        '[[match]]\nid = "0001"\n\n[[match]]\nid = "0002"\n'
    )


def test_append_match_handles_empty_file(tmp_path: Path) -> None:
    matches_path = tmp_path / "matches.toml"
    matches_path.write_text("", encoding="utf-8")

    match_recorder.append_match(matches_path, '[[match]]\nid = "0001"\n')

    assert matches_path.read_text(encoding="utf-8") == '[[match]]\nid = "0001"\n'
