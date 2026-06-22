"""Part A tests for Hypothesis and Hypothesis.Builder."""
from __future__ import annotations

import pytest

from xhail.core.config import Config
from xhail.core.entities.grounding import Grounding
from xhail.core.entities.hypothesis import Hypothesis
from xhail.core.entities.problem import Problem
from xhail.core.statements.display import Display
from xhail.core.statements.example import Example
from xhail.core.statements.mode_b import ModeB
from xhail.core.statements.mode_h import ModeH
from xhail.core.terms.atom import Atom
from xhail.core.terms.number import Number
from xhail.core.terms.placemarker import Placemarker, Type
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
def empty_grounding(empty_problem) -> Grounding:
    return Grounding.Builder(empty_problem).build()


@pytest.fixture
def hbuilder(empty_grounding) -> Hypothesis.Builder:
    return Hypothesis.Builder(empty_grounding)


@pytest.fixture
def simple_grounding(cfg) -> Grounding:
    """Grounding with generalisation: [Clause(head=flies)] — no body."""
    scheme = Scheme("flies")
    pb = Problem.Builder(cfg)
    pb.add_mode_h(ModeH(scheme=scheme))
    problem = pb.build()
    gb = Grounding.Builder(problem)
    gb.add_atom(Atom("abduced_flies"))
    gb.add_atom(Atom("flies"))
    return gb.build()


@pytest.fixture
def body_grounding(cfg) -> Grounding:
    """Grounding with generalisation: [Clause(head=flies(V1), body=[bird(V1)])]."""
    pm = Placemarker("x", Type.INPUT)
    scheme_h = Scheme("flies", (pm,))
    scheme_b = Scheme("bird", (pm,))
    pb = Problem.Builder(cfg)
    pb.add_mode_h(ModeH(scheme=scheme_h))
    pb.add_mode_b(ModeB(scheme=scheme_b))
    problem = pb.build()
    tweety = Atom("tweety")
    gb = Grounding.Builder(problem)
    gb.add_atom(Atom("abduced_flies", (tweety,)))
    gb.add_atom(Atom("flies", (tweety,)))
    gb.add_atom(Atom("bird", (tweety,)))
    gb.add_atom(Atom("x", (tweety,)))  # for subsumes(PM_x, tweety, facts)
    return gb.build()


# ---------------------------------------------------------------------------
# Builder construction
# ---------------------------------------------------------------------------

def test_builder_requires_grounding():
    with pytest.raises((ValueError, TypeError)):
        Hypothesis.Builder(None)


def test_builder_builds_hypothesis(hbuilder):
    assert isinstance(hbuilder.build(), Hypothesis)


# ---------------------------------------------------------------------------
# add_atom — routing
# ---------------------------------------------------------------------------

def test_add_use_clause_literal_goes_to_literals(hbuilder):
    ucl = Atom("use_clause_literal", (Number(0), Number(0)))
    hbuilder.add_atom(ucl)
    h = hbuilder.build()
    assert ucl in list(h)  # __iter__ yields literals


def test_add_plain_atom_goes_to_facts(hbuilder, empty_grounding):
    atom = Atom("bird")
    hbuilder.add_atom(atom)
    # facts are not directly exposed, but we can check via coverage
    # with a positive example, covered iff atom in facts
    cfg_ex = Config()
    pb = Problem.Builder(cfg_ex)
    pb.add_example(Example(Atom("bird")))
    problem = pb.build()
    g = Grounding.Builder(problem).build()
    hb = Hypothesis.Builder(g)
    hb.add_atom(Atom("bird"))
    h = hb.build()
    assert h.has_covered()


def test_add_use_clause_literal_arity_1_goes_to_facts(hbuilder):
    # use_clause_literal with arity 1 (not 2) is treated as plain fact
    atom = Atom("use_clause_literal", (Number(0),))
    hbuilder.add_atom(atom)
    h = hbuilder.build()
    assert atom not in list(h)  # not in literals


def test_add_none_atom_ignored(hbuilder):
    hbuilder.add_atom(None)
    h = hbuilder.build()
    assert list(h) == []


def test_add_atom_to_model_when_full_and_displayed(cfg):
    atom = Atom("bird", (Atom("tweety"),))
    cfg_full = Config(full=True)
    pb = Problem.Builder(cfg_full)
    pb.add_display(Display("bird", 1))
    problem = pb.build()
    g = Grounding.Builder(problem).build()
    hb = Hypothesis.Builder(g)
    hb.add_atom(atom)
    h = hb.build()
    assert h.has_model()
    assert atom in h.get_model()


def test_add_atom_not_in_model_when_not_full(cfg):
    cfg_nf = Config(full=False)
    pb = Problem.Builder(cfg_nf)
    pb.add_display(Display("bird", 1))
    problem = pb.build()
    g = Grounding.Builder(problem).build()
    hb = Hypothesis.Builder(g)
    hb.add_atom(Atom("bird", (Atom("tweety"),)))
    h = hb.build()
    assert not h.has_model()


# ---------------------------------------------------------------------------
# add_atoms / remove_atom / remove_atoms
# ---------------------------------------------------------------------------

def test_add_atoms(hbuilder):
    ucl0 = Atom("use_clause_literal", (Number(0), Number(0)))
    ucl1 = Atom("use_clause_literal", (Number(0), Number(1)))
    hbuilder.add_atoms([ucl0, ucl1])
    h = hbuilder.build()
    literals = list(h)
    assert ucl0 in literals
    assert ucl1 in literals


def test_remove_use_clause_literal(hbuilder):
    ucl = Atom("use_clause_literal", (Number(0), Number(0)))
    hbuilder.add_atom(ucl)
    hbuilder.remove_atom(ucl)
    h = hbuilder.build()
    assert ucl not in list(h)


def test_remove_plain_atom_from_facts(cfg):
    pb = Problem.Builder(cfg)
    pb.add_example(Example(Atom("bird")))
    problem = pb.build()
    g = Grounding.Builder(problem).build()
    hb = Hypothesis.Builder(g)
    hb.add_atom(Atom("bird"))
    hb.remove_atom(Atom("bird"))
    h = hb.build()
    assert not h.has_covered()


def test_remove_atoms(hbuilder):
    ucl0 = Atom("use_clause_literal", (Number(0), Number(0)))
    ucl1 = Atom("use_clause_literal", (Number(0), Number(1)))
    hbuilder.add_atoms([ucl0, ucl1])
    hbuilder.remove_atoms([ucl0, ucl1])
    h = hbuilder.build()
    assert list(h) == []


def test_remove_none_atom_ignored(hbuilder):
    ucl = Atom("use_clause_literal", (Number(0), Number(0)))
    hbuilder.add_atom(ucl)
    hbuilder.remove_atom(None)
    h = hbuilder.build()
    assert ucl in list(h)


# ---------------------------------------------------------------------------
# parse
# ---------------------------------------------------------------------------

def test_parse_use_clause_literal(hbuilder):
    hbuilder.parse(frozenset({"use_clause_literal(0,0)"}))
    h = hbuilder.build()
    literals = list(h)
    assert len(literals) == 1
    assert literals[0].identifier == "use_clause_literal"


def test_parse_plain_atom(hbuilder):
    hbuilder.parse(frozenset({"bird(tweety)"}))
    h = hbuilder.build()
    assert list(h) == []  # plain atom not in literals


def test_parse_unparseable_skipped(hbuilder):
    hbuilder.parse(frozenset({"!!!invalid!!!"}))
    h = hbuilder.build()
    assert list(h) == []


# ---------------------------------------------------------------------------
# clear
# ---------------------------------------------------------------------------

def test_clear_removes_literals(hbuilder):
    ucl = Atom("use_clause_literal", (Number(0), Number(0)))
    hbuilder.add_atom(ucl)
    hbuilder.clear()
    h = hbuilder.build()
    assert list(h) == []


def test_clear_removes_model(cfg):
    cfg_full = Config(full=True)
    pb = Problem.Builder(cfg_full)
    pb.add_display(Display("bird", 1))
    problem = pb.build()
    g = Grounding.Builder(problem).build()
    hb = Hypothesis.Builder(g)
    hb.add_atom(Atom("bird", (Atom("tweety"),)))
    hb.clear()
    h = hb.build()
    assert not h.has_model()


def test_clear_preserves_facts(cfg):
    pb = Problem.Builder(cfg)
    pb.add_example(Example(Atom("bird")))
    problem = pb.build()
    g = Grounding.Builder(problem).build()
    hb = Hypothesis.Builder(g)
    hb.add_atom(Atom("bird"))
    hb.clear()
    h = hb.build()
    # facts are preserved: positive example should still be covered
    assert h.has_covered()


# ---------------------------------------------------------------------------
# build — coverage computation
# ---------------------------------------------------------------------------

def test_positive_example_covered_when_in_facts(cfg):
    pb = Problem.Builder(cfg)
    pb.add_example(Example(Atom("fly")))
    problem = pb.build()
    g = Grounding.Builder(problem).build()
    hb = Hypothesis.Builder(g)
    hb.add_atom(Atom("fly"))
    h = hb.build()
    assert h.has_covered()
    assert not h.has_uncovered()


def test_positive_example_uncovered_when_not_in_facts(cfg):
    pb = Problem.Builder(cfg)
    pb.add_example(Example(Atom("fly")))
    problem = pb.build()
    g = Grounding.Builder(problem).build()
    hb = Hypothesis.Builder(g)
    h = hb.build()
    assert not h.has_covered()
    assert h.has_uncovered()


def test_negative_example_covered_when_not_in_facts(cfg):
    pb = Problem.Builder(cfg)
    pb.add_example(Example(Atom("fly"), negated=True))
    problem = pb.build()
    g = Grounding.Builder(problem).build()
    hb = Hypothesis.Builder(g)
    h = hb.build()
    assert h.has_covered()


def test_negative_example_uncovered_when_in_facts(cfg):
    pb = Problem.Builder(cfg)
    pb.add_example(Example(Atom("fly"), negated=True))
    problem = pb.build()
    g = Grounding.Builder(problem).build()
    hb = Hypothesis.Builder(g)
    hb.add_atom(Atom("fly"))
    h = hb.build()
    assert not h.has_covered()
    assert h.has_uncovered()


def test_build_resets_coverage_each_call(cfg):
    pb = Problem.Builder(cfg)
    pb.add_example(Example(Atom("fly")))
    problem = pb.build()
    g = Grounding.Builder(problem).build()
    hb = Hypothesis.Builder(g)
    hb.add_atom(Atom("fly"))
    h1 = hb.build()
    assert h1.has_covered()
    hb.clear()
    h2 = hb.build()
    assert not h2.has_covered()


# ---------------------------------------------------------------------------
# Hypothesis — __iter__
# ---------------------------------------------------------------------------

def test_iter_yields_use_clause_literal_atoms(hbuilder):
    ucl = Atom("use_clause_literal", (Number(0), Number(0)))
    hbuilder.add_atom(ucl)
    h = hbuilder.build()
    assert ucl in list(h)


def test_iter_empty_when_no_literals(hbuilder):
    h = hbuilder.build()
    assert list(h) == []


# ---------------------------------------------------------------------------
# Hypothesis — get_hypotheses() — head only
# ---------------------------------------------------------------------------

def test_get_hypotheses_empty_when_no_ucl_atoms(simple_grounding):
    hb = Hypothesis.Builder(simple_grounding)
    h = hb.build()
    assert h.get_hypotheses() == ()


def test_get_hypotheses_head_only(simple_grounding):
    hb = Hypothesis.Builder(simple_grounding)
    # clause 0, literal 0 → selects head
    hb.add_atom(Atom("use_clause_literal", (Number(0), Number(0))))
    h = hb.build()
    hypotheses = h.get_hypotheses()
    assert len(hypotheses) == 1
    assert hypotheses[0].head is not None
    assert hypotheses[0].head.identifier == "flies"
    assert hypotheses[0].body == ()


def test_get_hypotheses_cached(simple_grounding):
    hb = Hypothesis.Builder(simple_grounding)
    hb.add_atom(Atom("use_clause_literal", (Number(0), Number(0))))
    h = hb.build()
    assert h.get_hypotheses() is h.get_hypotheses()


def test_get_hypotheses_skips_out_of_range_clause(simple_grounding):
    hb = Hypothesis.Builder(simple_grounding)
    # clause_id=99 doesn't exist in generalisation
    hb.add_atom(Atom("use_clause_literal", (Number(99), Number(0))))
    h = hb.build()
    assert h.get_hypotheses() == ()


def test_get_hypotheses_skips_body_without_head(simple_grounding):
    hb = Hypothesis.Builder(simple_grounding)
    # Only literal_id=1 with no literal_id=0 for the same clause — no head created
    hb.add_atom(Atom("use_clause_literal", (Number(0), Number(1))))
    h = hb.build()
    assert h.get_hypotheses() == ()


def test_has_hypotheses_true_when_ucl_selected(simple_grounding):
    hb = Hypothesis.Builder(simple_grounding)
    hb.add_atom(Atom("use_clause_literal", (Number(0), Number(0))))
    h = hb.build()
    assert h.has_hypotheses()


def test_has_hypotheses_false_initially(simple_grounding):
    hb = Hypothesis.Builder(simple_grounding)
    h = hb.build()
    assert not h.has_hypotheses()


# ---------------------------------------------------------------------------
# Hypothesis — get_hypotheses() — with body literal and type constraint
# ---------------------------------------------------------------------------

def test_get_hypotheses_with_body_literal(body_grounding):
    hb = Hypothesis.Builder(body_grounding)
    hb.add_atom(Atom("use_clause_literal", (Number(0), Number(0))))
    hb.add_atom(Atom("use_clause_literal", (Number(0), Number(1))))
    h = hb.build()
    hypotheses = h.get_hypotheses()
    assert len(hypotheses) == 1
    assert hypotheses[0].head.identifier == "flies"
    assert hypotheses[0].body


def test_get_hypotheses_body_includes_bird(body_grounding):
    hb = Hypothesis.Builder(body_grounding)
    hb.add_atom(Atom("use_clause_literal", (Number(0), Number(0))))
    hb.add_atom(Atom("use_clause_literal", (Number(0), Number(1))))
    h = hb.build()
    body_ids = {lit.atom.identifier for lit in h.get_hypotheses()[0].body}
    assert "bird" in body_ids


def test_get_hypotheses_type_constraint_added(body_grounding):
    hb = Hypothesis.Builder(body_grounding)
    hb.add_atom(Atom("use_clause_literal", (Number(0), Number(0))))
    hb.add_atom(Atom("use_clause_literal", (Number(0), Number(1))))
    h = hb.build()
    body_ids = {lit.atom.identifier for lit in h.get_hypotheses()[0].body}
    assert "x" in body_ids


# ---------------------------------------------------------------------------
# Hypothesis — delegation methods
# ---------------------------------------------------------------------------

def test_get_covered(cfg):
    pb = Problem.Builder(cfg)
    pb.add_example(Example(Atom("fly")))
    problem = pb.build()
    g = Grounding.Builder(problem).build()
    hb = Hypothesis.Builder(g)
    hb.add_atom(Atom("fly"))
    h = hb.build()
    assert isinstance(h.get_covered(), tuple)
    assert h.has_covered()


def test_get_uncovered(cfg):
    pb = Problem.Builder(cfg)
    pb.add_example(Example(Atom("fly")))
    problem = pb.build()
    g = Grounding.Builder(problem).build()
    h = Hypothesis.Builder(g).build()
    assert isinstance(h.get_uncovered(), tuple)
    assert h.has_uncovered()


def test_get_model_is_tuple(hbuilder):
    h = hbuilder.build()
    assert isinstance(h.get_model(), tuple)


def test_get_grounding(empty_grounding):
    h = Hypothesis.Builder(empty_grounding).build()
    assert h.get_grounding() is empty_grounding


def test_get_config(cfg, empty_grounding):
    h = Hypothesis.Builder(empty_grounding).build()
    assert h.get_config() is cfg


def test_get_examples_delegates(cfg):
    pb = Problem.Builder(cfg)
    pb.add_example(Example(Atom("fly")))
    problem = pb.build()
    g = Grounding.Builder(problem).build()
    h = Hypothesis.Builder(g).build()
    assert h.has_examples()


def test_get_background_delegates(cfg):
    pb = Problem.Builder(cfg)
    pb.add_background("bird(tweety).")
    problem = pb.build()
    g = Grounding.Builder(problem).build()
    h = Hypothesis.Builder(g).build()
    assert h.has_background()
    assert "bird(tweety)." in h.get_background()


def test_get_displays_delegates(cfg):
    pb = Problem.Builder(cfg)
    pb.add_display(Display("bird", 1))
    problem = pb.build()
    g = Grounding.Builder(problem).build()
    h = Hypothesis.Builder(g).build()
    assert h.has_displays()


def test_get_delta_delegates(hbuilder):
    h = hbuilder.build()
    assert isinstance(h.get_delta(), tuple)


def test_get_generalisation_delegates(simple_grounding):
    h = Hypothesis.Builder(simple_grounding).build()
    assert h.get_generalisation() == simple_grounding.get_generalisation()
    assert h.has_generalisation()


def test_get_kernel_delegates(simple_grounding):
    h = Hypothesis.Builder(simple_grounding).build()
    assert h.get_kernel() == simple_grounding.get_kernel()
    assert h.has_kernel()


def test_get_problem_delegates(empty_grounding, empty_problem):
    h = Hypothesis.Builder(empty_grounding).build()
    assert h.get_problem() is empty_problem


def test_has_domains_false_when_none(empty_grounding):
    h = Hypothesis.Builder(empty_grounding).build()
    assert not h.has_domains()


def test_has_modes_false_when_no_modes(empty_grounding):
    h = Hypothesis.Builder(empty_grounding).build()
    assert not h.has_modes()
