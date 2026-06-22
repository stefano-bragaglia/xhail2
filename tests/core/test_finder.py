"""Tests for xhail.core.finder."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from xhail.core.finder import (
    Finder,
    _check_line,
    _check_output,
    _is_valid_executable,
    _is_valid_match,
    _matches,
)


# --- _matches ---

def test_matches_exact():
    assert _matches("clasp", "clasp") is True


def test_matches_exe_suffix():
    assert _matches("clasp.exe", "clasp") is True


def test_matches_different_name():
    assert _matches("clingo", "clasp") is False


def test_matches_partial_with_extension():
    assert _matches("clasp.tar.gz", "clasp") is False


# --- _is_valid_executable ---

def test_is_valid_executable_none():
    assert _is_valid_executable(None) is False


def test_is_valid_executable_nonexistent(tmp_path):
    assert _is_valid_executable(tmp_path / "missing") is False


def test_is_valid_executable_not_executable(tmp_path):
    f = tmp_path / "test.sh"
    f.write_text("#!/bin/sh")
    assert _is_valid_executable(f) is False


def test_is_valid_executable_executable(tmp_path):
    f = tmp_path / "test.sh"
    f.write_text("#!/bin/sh")
    f.chmod(0o755)
    assert _is_valid_executable(f) is True


# --- _is_valid_match ---

def test_is_valid_match_empty_tuple():
    assert _is_valid_match(()) is False


def test_is_valid_match_empty_string():
    assert _is_valid_match(("",)) is False


def test_is_valid_match_blank_string():
    assert _is_valid_match(("   ",)) is False


def test_is_valid_match_valid_single():
    assert _is_valid_match(("clasp",)) is True


def test_is_valid_match_valid_multi():
    assert _is_valid_match(("clasp", " 3.")) is True


# --- _check_line ---

def test_check_line_single_pattern_found():
    assert _check_line("clasp version 3.2", ("clasp",)) is True


def test_check_line_single_pattern_not_found():
    assert _check_line("gringo version 3.2", ("clasp",)) is False


def test_check_line_two_patterns_in_order():
    assert _check_line("clasp version 3.2", ("clasp", " 3.")) is True


def test_check_line_last_pattern_determines_result():
    # Even if earlier patterns are missing, the last one's presence/absence decides.
    # "missing" not found (pos=-1), next search for "clasp" starts at max(0,-1)=0 → found.
    # ponytail: tests the asymmetric early-exit from Java's indexOf(-1) → max(0,-1)=0 reset
    assert _check_line("clasp version 3.2", ("missing", "clasp")) is True


def test_check_line_last_pattern_absent():
    # "clasp" found, then "missing" not found → pos=-1 → False
    assert _check_line("clasp version 3.2", ("clasp", "missing")) is False


def test_check_line_empty_line():
    assert _check_line("", ("clasp",)) is False


def test_check_line_case_sensitive():
    # _check_output lowercases before calling _check_line; here we test raw sensitivity
    assert _check_line("CLASP VERSION 3.2", ("clasp",)) is False


# --- _check_output ---

def test_check_output_single_line_match():
    assert _check_output("clasp version 3.2\n", ("clasp",)) is True


def test_check_output_single_line_no_match():
    assert _check_output("gringo version 3.2\n", ("clasp",)) is False


def test_check_output_match_on_second_line():
    assert _check_output("gringo 4.0\nclasp 3.2\n", ("clasp", " 3.")) is True


def test_check_output_empty_string():
    assert _check_output("", ("clasp",)) is False


def test_check_output_lowercases_line():
    # "CLASP 3.2" lowercased → "clasp 3.2" → matches "clasp"
    assert _check_output("CLASP 3.2\n", ("clasp",)) is True


# --- Finder.is_found ---

def test_is_found_vacuously_true():
    assert Finder(" 3.").is_found() is True


def test_is_found_false_initially():
    assert Finder(" 3.", "clasp").is_found() is False


def test_is_found_false_with_multiple_apps():
    assert Finder(" 3.", "clasp", "gringo").is_found() is False


# --- Finder.get ---

def test_get_blank_raises():
    with pytest.raises(ValueError):
        Finder(" 3.", "clasp").get("")


def test_get_whitespace_raises():
    with pytest.raises(ValueError):
        Finder(" 3.", "clasp").get("   ")


def test_get_unknown_name_returns_none():
    assert Finder(" 3.", "clasp").get("gringo") is None


# --- Finder.test ---

def test_test_blank_name_raises():
    with pytest.raises(ValueError):
        Finder(" 3.", "clasp").test("", None)


def test_test_name_not_in_apps_raises():
    with pytest.raises(ValueError):
        Finder(" 3.", "clasp").test("gringo", None)


def test_test_file_none_returns_false():
    assert Finder(" 3.", "clasp").test("clasp", None) is False


def test_test_already_registered_returns_true(tmp_path):
    finder = Finder(" 3.", "clasp")
    finder._results["clasp"] = tmp_path / "clasp"
    f = tmp_path / "clasp"
    f.write_text("")
    assert finder.test("clasp", f) is True


def test_test_registers_matching_executable(tmp_path):
    script = tmp_path / "myapp"
    script.write_text("#!/bin/sh\necho 'myapp version 3.2'")
    script.chmod(0o755)
    finder = Finder(" 3.", "myapp")
    assert finder.test("myapp", script) is True
    assert finder.get("myapp") == script


# --- Finder.find ---

def test_find_already_found_returns_true():
    finder = Finder(" 3.")  # no apps → vacuously found
    assert finder.find(Path("/nonexistent"), recurse=False) is True


def test_find_nonexistent_path_returns_false():
    assert Finder(" 3.", "clasp").find(Path("/nonexistent/path/xyz"), recurse=False) is False


def test_find_discovers_executable(tmp_path):
    script = tmp_path / "myapp"
    script.write_text("#!/bin/sh\necho 'myapp version 3.2'")
    script.chmod(0o755)
    finder = Finder(" 3.", "myapp")
    assert finder.find(tmp_path, recurse=False) is True
    assert finder.get("myapp") == script


def test_find_no_recurse_misses_subdir(tmp_path):
    subdir = tmp_path / "sub"
    subdir.mkdir()
    script = subdir / "myapp"
    script.write_text("#!/bin/sh\necho 'myapp version 3.2'")
    script.chmod(0o755)
    assert Finder(" 3.", "myapp").find(tmp_path, recurse=False) is False


def test_find_recurse_finds_in_subdir(tmp_path):
    subdir = tmp_path / "sub"
    subdir.mkdir()
    script = subdir / "myapp"
    script.write_text("#!/bin/sh\necho 'myapp version 3.2'")
    script.chmod(0o755)
    finder = Finder(" 3.", "myapp")
    assert finder.find(tmp_path, recurse=True) is True
    assert finder.get("myapp") == script


# --- Finder.check (static) ---

def test_check_python_executable():
    assert Finder.check(Path(sys.executable), "python") is True


def test_check_nonexistent_executable():
    assert Finder.check(Path("/nonexistent/binary"), "test") is False


def test_check_pattern_not_in_output():
    assert Finder.check(Path(sys.executable), "nonexistent_xyz_string") is False


def test_check_empty_match_returns_false():
    # _is_valid_match(()) is False → check returns False without running subprocess
    assert Finder.check(Path(sys.executable)) is False
