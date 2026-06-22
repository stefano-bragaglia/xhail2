"""Tests for xhail.core.config."""
from __future__ import annotations

from pathlib import Path

import pytest

from xhail.core.config import Config


# --- name derivation ---

def test_name_no_sources_is_stdin():
    assert Config().name == "stdin"


def test_name_from_first_source_stem(tmp_path):
    f = tmp_path / "example.pl"
    f.write_text("")
    assert Config(sources=(f,)).name == "example"


def test_name_no_extension(tmp_path):
    f = tmp_path / "myfile"
    f.write_text("")
    assert Config(sources=(f,)).name == "myfile"


def test_name_hidden_file_stem_empty(tmp_path):
    f = tmp_path / ".pl"
    f.write_text("")
    assert Config(sources=(f,)).name == "file"


def test_name_uses_first_source_only(tmp_path):
    a = tmp_path / "alpha.pl"
    b = tmp_path / "beta.pl"
    a.write_text("")
    b.write_text("")
    assert Config(sources=(a, b)).name == "alpha"


# --- source validation ---

def test_nonexistent_source_raises(tmp_path):
    with pytest.raises(ValueError):
        Config(sources=(tmp_path / "missing.pl",))


def test_directory_source_raises(tmp_path):
    with pytest.raises(ValueError):
        Config(sources=(tmp_path,))


def test_valid_source_accepted(tmp_path):
    f = tmp_path / "ok.pl"
    f.write_text("")
    cfg = Config(sources=(f,))
    assert cfg.sources == (f,)


# --- has_sources ---

def test_has_sources_false_when_empty():
    assert not Config().has_sources()


def test_has_sources_true_when_set(tmp_path):
    f = tmp_path / "a.pl"
    f.write_text("")
    assert Config(sources=(f,)).has_sources()


# --- defaults ---

def test_default_all_false():
    assert Config().all is False


def test_default_blind_false():
    assert Config().blind is False


def test_default_clasp_none():
    assert Config().clasp is None


def test_default_debug_false():
    assert Config().debug is False


def test_default_full_false():
    assert Config().full is False


def test_default_gringo_none():
    assert Config().gringo is None


def test_default_help_false():
    assert Config().help_ is False


def test_default_iterations_zero():
    assert Config().iterations == 0


def test_default_kill_zero():
    assert Config().kill == 0


def test_default_mute_false():
    assert Config().mute is False


def test_default_output_false():
    assert Config().output is False


def test_default_prettify_false():
    assert Config().prettify is False


def test_default_search_false():
    assert Config().search is False


def test_default_terminate_false():
    assert Config().terminate is False


def test_default_version_false():
    assert Config().version is False


# --- mutability (Finder assigns clasp/gringo post-construction) ---

def test_clasp_assignable():
    cfg = Config()
    cfg.clasp = Path("/usr/bin/clasp")
    assert cfg.clasp == Path("/usr/bin/clasp")


def test_gringo_assignable():
    cfg = Config()
    cfg.gringo = Path("/usr/bin/gringo")
    assert cfg.gringo == Path("/usr/bin/gringo")


# --- __str__ ---

def test_str_empty_when_defaults():
    assert str(Config()) == ""


def test_str_all_flag():
    assert " -a" in str(Config(all=True))


def test_str_blind_flag():
    assert " -b" in str(Config(blind=True))


def test_str_clasp_flag():
    assert " -c /p/clasp" in str(Config(clasp=Path("/p/clasp")))


def test_str_debug_flag():
    assert " -d" in str(Config(debug=True))


def test_str_full_flag():
    assert " -f" in str(Config(full=True))


def test_str_gringo_flag():
    assert " -g /p/gringo" in str(Config(gringo=Path("/p/gringo")))


def test_str_help_flag():
    assert " -h" in str(Config(help_=True))


def test_str_iterations_flag():
    assert " -i 3" in str(Config(iterations=3))


def test_str_iterations_zero_omitted():
    assert " -i" not in str(Config(iterations=0))


def test_str_kill_flag():
    assert " -k 30" in str(Config(kill=30))


def test_str_kill_zero_omitted():
    assert " -k" not in str(Config(kill=0))


def test_str_mute_flag():
    assert " -m" in str(Config(mute=True))


def test_str_prettify_flag():
    assert " -p" in str(Config(prettify=True))


def test_str_search_flag():
    assert " -s" in str(Config(search=True))


def test_str_version_flag():
    assert " -v" in str(Config(version=True))


def test_str_output_omitted():
    assert "-o" not in str(Config(output=True))


def test_str_terminate_omitted():
    assert "-t" not in str(Config(terminate=True))


def test_str_sources_appended(tmp_path):
    f = tmp_path / "a.pl"
    f.write_text("")
    assert str(f) in str(Config(sources=(f,)))


def test_str_flag_order(tmp_path):
    f = tmp_path / "x.pl"
    f.write_text("")
    s = str(Config(all=True, blind=True, clasp=Path("/c"), debug=True, sources=(f,)))
    assert s.index("-a") < s.index("-b") < s.index("-c") < s.index("-d")


def test_str_starts_with_space_when_flags_set():
    s = str(Config(all=True))
    assert s.startswith(" ")


# --- equality ---

def test_equal_configs():
    assert Config(all=True) == Config(all=True)


def test_unequal_configs():
    assert Config(all=True) != Config(blind=True)


def test_name_excluded_from_equality(tmp_path):
    a = tmp_path / "alpha.pl"
    b = tmp_path / "beta.pl"
    a.write_text("")
    b.write_text("")
    # same flags, different sources → different name but also different sources → not equal
    # test that name field itself doesn't affect equality of identical configs
    c1 = Config()
    c2 = Config()
    c2.name = "custom"  # direct mutation
    assert c1 == c2
