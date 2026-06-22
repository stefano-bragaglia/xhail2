"""Part A tests for Grounding and Grounding.Builder — no solve() (needs Dialler/Answers/Answer)."""
from __future__ import annotations

import io

import pytest

from xhail.core.config import Config
from xhail.core.entities.grounding import Grounding
from xhail.core.entities.problem import Problem
from xhail.core.statements.display import Display
from xhail.core.statements.example import Example
from xhail.core.statements.mode_h import ModeH
from xhail.core.terms.atom import Atom
from xhail.core.terms.scheme import Scheme


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def cfg() -> Config:
    return Config()


@pytest.fixture
def empty_problem(cfg) -> Problem:
    return Problem.Builder(cfg).build()


@pytest.fixture
def gbuilder(empty_problem) -> Grounding.Builder:
    return Grounding.Builder(empty_problem)


# ---------------------------------------------------------------------------
# Builder construction
# ---------------------------------------------------------------------------

def test_builder_requires_problem():
    with pytest.raises((ValueError, TypeError)):
        Grounding.Builder(None)


def test_builder_builds_grounding(gbuilder):
    assert isinstance(gbuilder.build(), Grounding)


# ---------------------------------------------------------------------------
# add_atom — plain atoms go to facts
# ---------------------------------------------------------------------------

def test_add_plain_atom_to_facts(gbuilder):
    gbuilder.add_atom(Atom("bird"))
    g = gbuilder.build()
    assert Atom("bird") in g.get_facts()


def test_add_plain_atom_not_in_delta(gbuilder):
    gbuilder.add_atom(Atom("bird"))
    g = gbuilder.build()
    assert not g.has_delta()


def test_add_none_atom_ignored(gbuilder):
    gbuilder.add_atom(None)
    g = gbuilder.build()
    assert not g.get_facts()


# ---------------------------------------------------------------------------
# add_atom — abduced_ atoms go to delta
# ---------------------------------------------------------------------------

def test_add_abduced_atom_to_delta(gbuilder):
    gbuilder.add_atom(Atom("abduced_flies"))
    g = gbuilder.build()
    assert g.has_delta()
    assert Atom("flies") in g.get_delta()


def test_abduced_prefix_stripped(gbuilder):
    gbuilder.add_atom(Atom("abduced_foo"))
    g = gbuilder.build()
    assert Atom("foo") in g.get_delta()
    assert not any(a.identifier.startswith("abduced_") for a in g.get_delta())


def test_abduced_atom_not_in_facts(gbuilder):
    gbuilder.add_atom(Atom("abduced_foo"))
    g = gbuilder.build()
    assert not g.get_facts()


def test_add_abduced_atom_preserves_terms(gbuilder):
    inner = Atom("tweety")
    abduced = Atom("abduced_flies", (inner,))
    gbuilder.add_atom(abduced)
    g = gbuilder.build()
    stripped = Atom("flies", (inner,))
    assert stripped in g.get_delta()


# ---------------------------------------------------------------------------
# add_atom — model routing (config.full + displays + lookup)
# ---------------------------------------------------------------------------

def test_atom_added_to_model_when_full_and_displayed(cfg):
    atom = Atom("bird", (Atom("tweety"),))
    cfg_full = Config(full=True)
    pb2 = Problem.Builder(cfg_full)
    pb2.add_display(Display("bird", 1))
    problem2 = pb2.build()
    gb2 = Grounding.Builder(problem2)
    gb2.add_atom(atom)
    g = gb2.build()
    assert atom in g.get_model()


def test_atom_not_in_model_when_not_full(cfg):
    pb = Problem.Builder(cfg)
    pb.add_display(Display("bird", 1))
    problem = pb.build()
    gb = Grounding.Builder(problem)
    atom = Atom("bird", (Atom("tweety"),))
    gb.add_atom(atom)
    g = gb.build()
    assert not g.has_model()


# ---------------------------------------------------------------------------
# add_atoms / remove_atom / remove_atoms
# ---------------------------------------------------------------------------

def test_add_atoms(gbuilder):
    gbuilder.add_atoms([Atom("a"), Atom("b")])
    g = gbuilder.build()
    assert Atom("a") in g.get_facts()
    assert Atom("b") in g.get_facts()


def test_remove_plain_atom(gbuilder):
    gbuilder.add_atom(Atom("bird"))
    gbuilder.remove_atom(Atom("bird"))
    g = gbuilder.build()
    assert not g.get_facts()


def test_remove_abduced_atom(gbuilder):
    gbuilder.add_atom(Atom("abduced_foo"))
    gbuilder.remove_atom(Atom("abduced_foo"))
    g = gbuilder.build()
    assert not g.has_delta()


def test_remove_atoms(gbuilder):
    gbuilder.add_atoms([Atom("a"), Atom("b")])
    gbuilder.remove_atoms([Atom("a"), Atom("b")])
    g = gbuilder.build()
    assert not g.get_facts()


def test_remove_none_atom_ignored(gbuilder):
    gbuilder.add_atom(Atom("bird"))
    gbuilder.remove_atom(None)
    g = gbuilder.build()
    assert Atom("bird") in g.get_facts()


# ---------------------------------------------------------------------------
# parse
# ---------------------------------------------------------------------------

def test_parse_answer_set(gbuilder):
    gbuilder.parse(frozenset({"bird(tweety)"}))
    g = gbuilder.build()
    assert g.get_facts()


def test_parse_abduced_atom(gbuilder):
    gbuilder.parse(frozenset({"abduced_flies(tweety)"}))
    g = gbuilder.build()
    assert g.has_delta()


# ---------------------------------------------------------------------------
# clear
# ---------------------------------------------------------------------------

def test_clear_removes_all(gbuilder):
    gbuilder.add_atom(Atom("bird"))
    gbuilder.add_atom(Atom("abduced_foo"))
    gbuilder.clear()
    g = gbuilder.build()
    assert not g.get_facts()
    assert not g.has_delta()


# ---------------------------------------------------------------------------
# build — coverage computation
# ---------------------------------------------------------------------------

def test_positive_example_covered_when_in_facts(cfg):
    pb = Problem.Builder(cfg)
    pb.add_example(Example(Atom("bird")))
    problem = pb.build()
    gb = Grounding.Builder(problem)
    gb.add_atom(Atom("bird"))
    g = gb.build()
    assert g.has_covered()
    assert not g.has_uncovered()


def test_positive_example_uncovered_when_not_in_facts(cfg):
    pb = Problem.Builder(cfg)
    pb.add_example(Example(Atom("bird")))
    problem = pb.build()
    gb = Grounding.Builder(problem)
    g = gb.build()
    assert not g.has_covered()
    assert g.has_uncovered()


def test_negative_example_covered_when_not_in_facts(cfg):
    pb = Problem.Builder(cfg)
    pb.add_example(Example(Atom("bird"), negated=True))
    problem = pb.build()
    gb = Grounding.Builder(problem)
    g = gb.build()
    assert g.has_covered()
    assert not g.has_uncovered()


def test_negative_example_uncovered_when_in_facts(cfg):
    pb = Problem.Builder(cfg)
    pb.add_example(Example(Atom("bird"), negated=True))
    problem = pb.build()
    gb = Grounding.Builder(problem)
    gb.add_atom(Atom("bird"))
    g = gb.build()
    assert not g.has_covered()
    assert g.has_uncovered()


def test_build_resets_coverage_each_call(cfg):
    pb = Problem.Builder(cfg)
    pb.add_example(Example(Atom("bird")))
    problem = pb.build()
    gb = Grounding.Builder(problem)
    gb.add_atom(Atom("bird"))
    g1 = gb.build()
    assert g1.has_covered()
    gb.clear()
    g2 = gb.build()
    assert not g2.has_covered()


# ---------------------------------------------------------------------------
# Grounding getters
# ---------------------------------------------------------------------------

def test_get_count_equals_delta_size(gbuilder):
    gbuilder.add_atom(Atom("abduced_a"))
    gbuilder.add_atom(Atom("abduced_b"))
    g = gbuilder.build()
    assert g.get_count() == 2


def test_get_config(cfg, empty_problem):
    g = Grounding.Builder(empty_problem).build()
    assert g.get_config() is cfg


def test_get_problem(empty_problem):
    g = Grounding.Builder(empty_problem).build()
    assert g.get_problem() is empty_problem


def test_get_facts_is_set(gbuilder):
    gbuilder.add_atom(Atom("bird"))
    g = gbuilder.build()
    assert isinstance(g.get_facts(), set)


def test_get_delta_is_tuple(gbuilder):
    gbuilder.add_atom(Atom("abduced_foo"))
    g = gbuilder.build()
    assert isinstance(g.get_delta(), tuple)


def test_has_delta_false_initially(gbuilder):
    g = gbuilder.build()
    assert not g.has_delta()


def test_has_model_false_when_not_full(gbuilder):
    gbuilder.add_atom(Atom("bird"))
    g = gbuilder.build()
    assert not g.has_model()


# ---------------------------------------------------------------------------
# Delegating getters
# ---------------------------------------------------------------------------

def test_get_background_delegates(cfg):
    pb = Problem.Builder(cfg)
    pb.add_background("bird(tweety).")
    problem = pb.build()
    g = Grounding.Builder(problem).build()
    assert "bird(tweety)." in g.get_background()
    assert g.has_background()


def test_get_displays_delegates(cfg):
    pb = Problem.Builder(cfg)
    pb.add_display(Display("bird", 1))
    problem = pb.build()
    g = Grounding.Builder(problem).build()
    assert Display("bird", 1) in g.get_displays()
    assert g.has_displays()


def test_get_examples_delegates(cfg):
    pb = Problem.Builder(cfg)
    pb.add_example(Example(Atom("fly")))
    problem = pb.build()
    g = Grounding.Builder(problem).build()
    assert g.has_examples()


def test_lookup_delegates(cfg):
    pb = Problem.Builder(cfg)
    pb.add_display(Display("bird", 1))
    problem = pb.build()
    g = Grounding.Builder(problem).build()
    assert g.lookup(Atom("bird", (Atom("tweety"),)))


# ---------------------------------------------------------------------------
# get_filters
# ---------------------------------------------------------------------------

def test_get_filters_has_hide(gbuilder):
    g = gbuilder.build()
    assert "#hide." in g.get_filters()


def test_get_filters_has_use_clause_literal(gbuilder):
    g = gbuilder.build()
    assert "#show use_clause_literal/2." in g.get_filters()


def test_get_filters_sorted(gbuilder):
    g = gbuilder.build()
    filters = g.get_filters()
    assert filters == tuple(sorted(filters))


def test_get_filters_includes_display(cfg):
    pb = Problem.Builder(cfg)
    pb.add_display(Display("bird", 1))
    problem = pb.build()
    g = Grounding.Builder(problem).build()
    assert "#show bird/1." in g.get_filters()


def test_get_filters_includes_example(cfg):
    pb = Problem.Builder(cfg)
    pb.add_example(Example(Atom("fly")))
    problem = pb.build()
    g = Grounding.Builder(problem).build()
    assert "#show fly/0." in g.get_filters()


def test_get_filters_no_abduced_shows(cfg):
    pb = Problem.Builder(cfg)
    pb.add_mode_h(ModeH(scheme=Scheme("head")))
    problem = pb.build()
    g = Grounding.Builder(problem).build()
    filters = g.get_filters()
    assert not any("abduced_" in f for f in filters)


# ---------------------------------------------------------------------------
# as_bad_solution
# ---------------------------------------------------------------------------

def test_as_bad_solution_empty_delta(gbuilder):
    g = gbuilder.build()
    assert g.as_bad_solution() == "bad_solution:-number_abduced(0)."


def test_as_bad_solution_with_delta(gbuilder):
    gbuilder.add_atom(Atom("abduced_foo"))
    g = gbuilder.build()
    result = g.as_bad_solution()
    assert result.startswith("bad_solution:-")
    assert "foo" in result
    assert "number_abduced(1)." in result


# ---------------------------------------------------------------------------
# get_kernel / get_generalisation — basic cases (no mode_h → empty)
# ---------------------------------------------------------------------------

def test_get_kernel_empty_when_no_delta(gbuilder):
    g = gbuilder.build()
    assert g.get_kernel() == ()


def test_get_kernel_empty_when_no_mode_h(gbuilder):
    gbuilder.add_atom(Atom("abduced_foo"))
    g = gbuilder.build()
    assert g.get_kernel() == ()


def test_get_kernel_cached(gbuilder):
    g = gbuilder.build()
    assert g.get_kernel() is g.get_kernel()


def test_get_generalisation_empty_when_no_kernel(gbuilder):
    g = gbuilder.build()
    assert g.get_generalisation() == ()


def test_get_generalisation_cached(gbuilder):
    g = gbuilder.build()
    assert g.get_generalisation() is g.get_generalisation()


def test_needs_induction_false_when_no_generalisation(gbuilder):
    g = gbuilder.build()
    assert not g.needs_induction()


def test_has_kernel_false_initially(gbuilder):
    g = gbuilder.build()
    assert not g.has_kernel()


def test_has_generalisation_false_initially(gbuilder):
    g = gbuilder.build()
    assert not g.has_generalisation()


# ---------------------------------------------------------------------------
# get_kernel — with mode_h that matches
# ---------------------------------------------------------------------------

def test_get_kernel_with_matching_mode_h(cfg):
    scheme = Scheme("flies")
    pb = Problem.Builder(cfg)
    pb.add_mode_h(ModeH(scheme=scheme))
    problem = pb.build()
    gb = Grounding.Builder(problem)
    gb.add_atom(Atom("abduced_flies"))
    gb.add_atom(Atom("flies"))
    g = gb.build()
    kernel = g.get_kernel()
    assert len(kernel) == 1
    assert kernel[0].head is not None
    assert kernel[0].head.identifier == "flies"


def test_get_generalisation_with_matching_mode_h(cfg):
    scheme = Scheme("flies")
    pb = Problem.Builder(cfg)
    pb.add_mode_h(ModeH(scheme=scheme))
    problem = pb.build()
    gb = Grounding.Builder(problem)
    gb.add_atom(Atom("abduced_flies"))
    gb.add_atom(Atom("flies"))
    g = gb.build()
    gen = g.get_generalisation()
    assert len(gen) == 1
    assert g.needs_induction()


# ---------------------------------------------------------------------------
# as_clauses — empty when no generalisation
# ---------------------------------------------------------------------------

def test_as_clauses_empty_when_no_generalisation(gbuilder):
    g = gbuilder.build()
    assert g.as_clauses() == ()


def test_as_clauses_with_generalisation(cfg):
    scheme = Scheme("flies")
    pb = Problem.Builder(cfg)
    pb.add_mode_h(ModeH(scheme=scheme))
    problem = pb.build()
    gb = Grounding.Builder(problem)
    gb.add_atom(Atom("abduced_flies"))
    gb.add_atom(Atom("flies"))
    g = gb.build()
    clauses = g.as_clauses()
    assert len(clauses) > 0
    assert any("use_clause_literal" in c for c in clauses)
    assert any("clause(0)." in c for c in clauses)


# ---------------------------------------------------------------------------
# save
# ---------------------------------------------------------------------------

def test_save_returns_true(gbuilder):
    g = gbuilder.build()
    stream = io.StringIO()
    assert g.save(0, stream) is True


def test_save_writes_hide_filter(gbuilder):
    g = gbuilder.build()
    stream = io.StringIO()
    g.save(0, stream)
    assert "#hide." in stream.getvalue()


def test_save_writes_use_clause_literal_filter(gbuilder):
    g = gbuilder.build()
    stream = io.StringIO()
    g.save(0, stream)
    assert "use_clause_literal" in stream.getvalue()
