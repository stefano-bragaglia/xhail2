"""Tests for xhail.core.utils."""
from __future__ import annotations

import io
from pathlib import Path

from xhail.core.utils import (
    dump,
    save_grounding,
    save_problem,
    save_temp_grounding,
    save_temp_problem,
)


# --- duck-type stubs ---

class _Problem:
    def __init__(self, **kw):
        self._displays = kw.get("displays", [])
        self._background = kw.get("background", [])
        self._domains = kw.get("domains", [])
        self._examples = kw.get("examples", [])
        self._mode_hs = kw.get("mode_hs", [])
        self._mode_bs = kw.get("mode_bs", [])
        self._filters = kw.get("filters", [])
        self._refinements = kw.get("refinements", [])

    def has_displays(self): return bool(self._displays)
    def get_displays(self): return self._displays
    def has_background(self): return bool(self._background)
    def has_domains(self): return bool(self._domains)
    def get_domains(self): return self._domains
    def get_background(self): return self._background
    def has_examples(self): return bool(self._examples)
    def get_examples(self): return self._examples
    def has_modes(self): return bool(self._mode_hs) or bool(self._mode_bs)
    def get_mode_hs(self): return self._mode_hs
    def get_mode_bs(self): return self._mode_bs
    def get_filters(self): return self._filters
    def get_refinements(self): return self._refinements


class _Grounding:
    def __init__(self, **kw):
        self._filters = kw.get("filters", [])
        self._domains = kw.get("domains", [])
        self._background = kw.get("background", [])
        self._examples = kw.get("examples", [])
        self._clauses = kw.get("clauses", [])

    def get_filters(self): return self._filters
    def get_domains(self): return self._domains
    def get_background(self): return self._background
    def get_examples(self): return self._examples
    def as_clauses(self): return self._clauses


class _Example:
    def __init__(self, s, clauses=None):
        self._s = s
        self._clauses = clauses if clauses is not None else [s]

    def __str__(self): return self._s
    def as_clauses(self): return self._clauses


class _Mode:
    def __init__(self, s, clauses=None):
        self._s = s
        self._clauses = clauses if clauses is not None else [s]

    def __str__(self): return self._s
    def as_clauses(self): return self._clauses


# --- dump: empty problem ---

def test_dump_empty_returns_true():
    assert dump(_Problem(), io.StringIO()) is True


def test_dump_empty_no_output():
    s = io.StringIO()
    dump(_Problem(), s)
    assert s.getvalue() == ""


# --- dump: displays ---

def test_dump_displays_content():
    s = io.StringIO()
    dump(_Problem(displays=["#display foo/1."]), s)
    assert "#display foo/1." in s.getvalue()


def test_dump_displays_followed_by_blank_line():
    s = io.StringIO()
    dump(_Problem(displays=["#display foo/1."]), s)
    lines = s.getvalue().splitlines()
    assert lines[-1] == ""


def test_dump_no_displays_no_display_lines():
    s = io.StringIO()
    dump(_Problem(), s)
    assert "#display" not in s.getvalue()


# --- dump: background section ---

def test_dump_background_header():
    s = io.StringIO()
    dump(_Problem(background=["fact(a)."]), s)
    assert "%% B. Background" in s.getvalue()


def test_dump_background_content():
    s = io.StringIO()
    dump(_Problem(background=["fact(a)."]), s)
    assert "fact(a)." in s.getvalue()


def test_dump_domains_trigger_background_section():
    s = io.StringIO()
    dump(_Problem(domains=["#domain bird(X)."]), s)
    assert "%% B. Background" in s.getvalue()
    assert "#domain bird(X)." in s.getvalue()


def test_dump_no_background_no_section():
    s = io.StringIO()
    dump(_Problem(), s)
    assert "%% B. Background" not in s.getvalue()


def test_dump_domains_before_background():
    s = io.StringIO()
    dump(_Problem(domains=["#domain bird(X)."], background=["fact(a)."]), s)
    output = s.getvalue()
    assert output.index("#domain bird(X).") < output.index("fact(a).")


# --- dump: examples section ---

def test_dump_examples_header():
    s = io.StringIO()
    dump(_Problem(examples=[_Example("#example bird(tweety).")]), s)
    assert "%% E. Examples" in s.getvalue()


def test_dump_examples_uses_str():
    s = io.StringIO()
    dump(_Problem(examples=[_Example("#example bird(tweety).")]), s)
    assert "#example bird(tweety)." in s.getvalue()


def test_dump_no_examples_no_section():
    s = io.StringIO()
    dump(_Problem(), s)
    assert "%% E. Examples" not in s.getvalue()


# --- dump: modes section ---

def test_dump_modes_header():
    s = io.StringIO()
    dump(_Problem(mode_hs=[_Mode("#modeh(flies/1, 1, 1).")]), s)
    assert "%% M. Modes" in s.getvalue()


def test_dump_mode_h_content():
    s = io.StringIO()
    dump(_Problem(mode_hs=[_Mode("modeh_line")]), s)
    assert "modeh_line" in s.getvalue()


def test_dump_mode_b_content():
    s = io.StringIO()
    dump(_Problem(mode_bs=[_Mode("modeb_line")]), s)
    assert "modeb_line" in s.getvalue()


def test_dump_mode_h_before_mode_b():
    s = io.StringIO()
    dump(_Problem(mode_hs=[_Mode("modeh_line")], mode_bs=[_Mode("modeb_line")]), s)
    output = s.getvalue()
    assert output.index("modeh_line") < output.index("modeb_line")


def test_dump_no_modes_no_section():
    s = io.StringIO()
    dump(_Problem(), s)
    assert "%% M. Modes" not in s.getvalue()


# --- save_problem: structure ---

def test_save_problem_returns_true():
    assert save_problem(_Problem(), 0, io.StringIO()) is True


def test_save_problem_has_background_header():
    s = io.StringIO()
    save_problem(_Problem(), 0, s)
    assert "%%% B. Background" in s.getvalue()


def test_save_problem_has_examples_header():
    s = io.StringIO()
    save_problem(_Problem(), 0, s)
    assert "%%% E. Examples" in s.getvalue()


def test_save_problem_has_inflation_header():
    s = io.StringIO()
    save_problem(_Problem(), 0, s)
    assert "%%% I. Inflation" in s.getvalue()


def test_save_problem_section_order():
    s = io.StringIO()
    save_problem(_Problem(), 0, s)
    output = s.getvalue()
    assert output.index("%%% B. Background") < output.index("%%% E. Examples") < output.index("%%% I. Inflation")


def test_save_problem_writes_filters():
    p = _Problem(filters=["#hide.", "#show foo/1."])
    s = io.StringIO()
    save_problem(p, 0, s)
    output = s.getvalue()
    assert "#hide." in output
    assert "#show foo/1." in output


def test_save_problem_filters_before_background():
    p = _Problem(filters=["#hide."])
    s = io.StringIO()
    save_problem(p, 0, s)
    output = s.getvalue()
    assert output.index("#hide.") < output.index("%%% B. Background")


def test_save_problem_writes_domains():
    p = _Problem(domains=["#domain bird(X)."])
    s = io.StringIO()
    save_problem(p, 0, s)
    assert "#domain bird(X)." in s.getvalue()


def test_save_problem_writes_background():
    p = _Problem(background=["fact(a)."])
    s = io.StringIO()
    save_problem(p, 0, s)
    assert "fact(a)." in s.getvalue()


def test_save_problem_writes_refinements():
    p = _Problem(refinements=["bad_solution:-number_abduced(0)."])
    s = io.StringIO()
    save_problem(p, 0, s)
    assert "bad_solution:-number_abduced(0)." in s.getvalue()


def test_save_problem_refinements_after_background():
    p = _Problem(background=["fact(a)."], refinements=["ref."])
    s = io.StringIO()
    save_problem(p, 0, s)
    output = s.getvalue()
    assert output.index("fact(a).") < output.index("ref.")


def test_save_problem_writes_example_clauses():
    clauses = ["% #example foo.", "#maximize[ foo =1 @1 ].", ":-not foo."]
    p = _Problem(examples=[_Example("#example foo.", clauses)])
    s = io.StringIO()
    save_problem(p, 0, s)
    output = s.getvalue()
    for clause in clauses:
        assert clause in output


# --- save_problem: iteration guard ---

def test_save_problem_it0_no_bad_solution():
    s = io.StringIO()
    save_problem(_Problem(), 0, s)
    assert ":-bad_solution." not in s.getvalue()


def test_save_problem_it1_includes_bad_solution():
    s = io.StringIO()
    save_problem(_Problem(), 1, s)
    assert ":-bad_solution." in s.getvalue()


def test_save_problem_it1_includes_number_abduced_preamble():
    s = io.StringIO()
    save_problem(_Problem(), 1, s)
    assert "number_abduced(V):-V:=#sum[ number_abduced(_,W) =W ]." in s.getvalue()


def test_save_problem_it0_filters_number_abduced_mode_clauses():
    mode = _Mode("...", ["number_abduced(V):-#count[ a =1 ].", "other(V)."])
    s = io.StringIO()
    save_problem(_Problem(mode_hs=[mode]), 0, s)
    output = s.getvalue()
    assert "number_abduced(V):-#count" not in output
    assert "other(V)." in output


def test_save_problem_it1_includes_all_mode_clauses():
    mode = _Mode("...", ["number_abduced(V):-#count[ a =1 ].", "other(V)."])
    s = io.StringIO()
    save_problem(_Problem(mode_hs=[mode]), 1, s)
    output = s.getvalue()
    assert "number_abduced(V):-#count[ a =1 ]." in output
    assert "other(V)." in output


# --- save_grounding: structure ---

def test_save_grounding_returns_true():
    assert save_grounding(_Grounding(), 0, io.StringIO()) is True


def test_save_grounding_has_background_header():
    s = io.StringIO()
    save_grounding(_Grounding(), 0, s)
    assert "%%% B. Background" in s.getvalue()


def test_save_grounding_has_examples_header():
    s = io.StringIO()
    save_grounding(_Grounding(), 0, s)
    assert "%%% E. Examples" in s.getvalue()


def test_save_grounding_has_compression_header():
    s = io.StringIO()
    save_grounding(_Grounding(), 0, s)
    assert "%%% C. Compression" in s.getvalue()


def test_save_grounding_no_inflation_header():
    s = io.StringIO()
    save_grounding(_Grounding(), 0, s)
    assert "%%% I. Inflation" not in s.getvalue()


def test_save_grounding_section_order():
    s = io.StringIO()
    save_grounding(_Grounding(), 0, s)
    output = s.getvalue()
    assert output.index("%%% B. Background") < output.index("%%% E. Examples") < output.index("%%% C. Compression")


def test_save_grounding_writes_filters():
    g = _Grounding(filters=["#hide.", "#show use_clause_literal/2."])
    s = io.StringIO()
    save_grounding(g, 0, s)
    output = s.getvalue()
    assert "#hide." in output
    assert "#show use_clause_literal/2." in output


def test_save_grounding_writes_background():
    g = _Grounding(background=["fact(a)."])
    s = io.StringIO()
    save_grounding(g, 0, s)
    assert "fact(a)." in s.getvalue()


def test_save_grounding_writes_example_clauses():
    clauses = ["% #example foo.", "#maximize[ foo =1 @1 ]."]
    g = _Grounding(examples=[_Example("...", clauses)])
    s = io.StringIO()
    save_grounding(g, 0, s)
    output = s.getvalue()
    for clause in clauses:
        assert clause in output


def test_save_grounding_writes_as_clauses():
    g = _Grounding(clauses=["clause(0).", "literal(0,1)."])
    s = io.StringIO()
    save_grounding(g, 0, s)
    output = s.getvalue()
    assert "clause(0)." in output
    assert "literal(0,1)." in output


def test_save_grounding_it_does_not_affect_output():
    g = _Grounding()
    s0, s1 = io.StringIO(), io.StringIO()
    save_grounding(g, 0, s0)
    save_grounding(g, 1, s1)
    assert s0.getvalue() == s1.getvalue()


# --- save_temp_problem / save_temp_grounding ---

def test_save_temp_problem_creates_file(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    result = save_temp_problem(_Problem(), 0, Path("test_abd0.lp"))
    assert result is True
    assert (tmp_path / "temp" / "test_abd0.lp").exists()


def test_save_temp_problem_file_has_background_header(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    save_temp_problem(_Problem(), 0, Path("out.lp"))
    content = (tmp_path / "temp" / "out.lp").read_text()
    assert "%%% B. Background" in content


def test_save_temp_problem_reuses_existing_temp(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "temp").mkdir()
    result = save_temp_problem(_Problem(), 0, Path("test.lp"))
    assert result is True


def test_save_temp_grounding_creates_file(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    result = save_temp_grounding(_Grounding(), 0, Path("test_ind0.lp"))
    assert result is True
    assert (tmp_path / "temp" / "test_ind0.lp").exists()


def test_save_temp_grounding_file_has_compression_header(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    save_temp_grounding(_Grounding(), 0, Path("out.lp"))
    content = (tmp_path / "temp" / "out.lp").read_text()
    assert "%%% C. Compression" in content
