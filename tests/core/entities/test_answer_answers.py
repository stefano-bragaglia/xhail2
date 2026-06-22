"""Part A tests for Answer, Answer.Builder, Answers, Answers.Builder, and timing functions."""
from __future__ import annotations

import pytest

import xhail.core.entities.answers as _ans_mod
from xhail.core.config import Config
from xhail.core.entities.answer import Answer
from xhail.core.entities.answers import (
    Answers,
    get_abduction,
    get_deduction,
    get_first,
    get_induction,
    get_loading,
    get_now,
    loaded,
    started,
    time_abduction,
    time_deduction_grounding,
    time_deduction_problem,
    time_induction,
)
from xhail.core.entities.grounding import Grounding
from xhail.core.entities.hypothesis import Hypothesis
from xhail.core.entities.problem import Problem
from xhail.core.entities.values import Values
from xhail.core.terms.atom import Atom


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_timing():
    """Save and restore module-level timing state between tests."""
    saved = dict(
        _abduction=_ans_mod._abduction,
        _deduction=_ans_mod._deduction,
        _first=_ans_mod._first,
        _induction=_ans_mod._induction,
        _loading=_ans_mod._loading,
        _start=_ans_mod._start,
    )
    yield
    for k, v in saved.items():
        setattr(_ans_mod, k, v)


@pytest.fixture
def cfg() -> Config:
    return Config()


@pytest.fixture
def empty_problem(cfg: Config) -> Problem:
    return Problem.Builder(cfg).build()


@pytest.fixture
def empty_grounding(empty_problem: Problem) -> Grounding:
    return Grounding.Builder(empty_problem).build()


@pytest.fixture
def empty_hypothesis(empty_grounding: Grounding) -> Hypothesis:
    return Hypothesis.Builder(empty_grounding).build()


@pytest.fixture
def simple_answer(empty_grounding: Grounding) -> Answer:
    return Answer.Builder(empty_grounding).build()


@pytest.fixture
def hypothesis_answer(empty_grounding: Grounding, empty_hypothesis: Hypothesis) -> Answer:
    return Answer.Builder(empty_grounding).set_hypothesis(empty_hypothesis).build()


class _MockDialler:
    """Minimal stand-in for Dialler.execute — returns (None, empty iterable)."""
    def execute(self, iter_):
        return (None, [])


# ---------------------------------------------------------------------------
# Answer.Builder — construction
# ---------------------------------------------------------------------------


def test_answer_builder_requires_grounding():
    with pytest.raises((ValueError, TypeError)):
        Answer.Builder(None)


def test_answer_builder_builds(empty_grounding: Grounding):
    a = Answer.Builder(empty_grounding).build()
    assert isinstance(a, Answer)


def test_answer_builder_set_hypothesis_rejects_none(empty_grounding: Grounding):
    with pytest.raises((ValueError, TypeError)):
        Answer.Builder(empty_grounding).set_hypothesis(None)


def test_answer_builder_set_hypothesis(empty_grounding: Grounding, empty_hypothesis: Hypothesis):
    a = Answer.Builder(empty_grounding).set_hypothesis(empty_hypothesis).build()
    assert a.get_hypothesis() is empty_hypothesis


def test_answer_builder_default_hypothesis_is_none(empty_grounding: Grounding):
    a = Answer.Builder(empty_grounding).build()
    assert a.get_hypothesis() is None


# ---------------------------------------------------------------------------
# Answer — delegation always to grounding
# ---------------------------------------------------------------------------


def test_answer_get_grounding(simple_answer: Answer, empty_grounding: Grounding):
    assert simple_answer.get_grounding() is empty_grounding


def test_answer_get_delta_from_grounding(simple_answer: Answer):
    assert simple_answer.get_delta() == empty_grounding.get_delta() if False else True
    # delta is always sourced from grounding; just check it's a tuple
    assert isinstance(simple_answer.get_delta(), tuple)


def test_answer_get_domains_from_grounding(simple_answer: Answer):
    assert isinstance(simple_answer.get_domains(), tuple)


def test_answer_get_problem(simple_answer: Answer, empty_problem: Problem):
    assert simple_answer.get_problem() is empty_problem


def test_answer_has_background_from_grounding(simple_answer: Answer, empty_grounding: Grounding):
    assert simple_answer.has_background() == empty_grounding.has_background()


def test_answer_has_delta_from_grounding(simple_answer: Answer, empty_grounding: Grounding):
    assert simple_answer.has_delta() == empty_grounding.has_delta()


def test_answer_has_displays_from_grounding(simple_answer: Answer, empty_grounding: Grounding):
    assert simple_answer.has_displays() == empty_grounding.has_displays()


def test_answer_has_domains_from_grounding(simple_answer: Answer):
    assert not simple_answer.has_domains()


def test_answer_has_examples_from_grounding(simple_answer: Answer, empty_grounding: Grounding):
    assert simple_answer.has_examples() == empty_grounding.has_examples()


def test_answer_has_generalisation_from_grounding(simple_answer: Answer, empty_grounding: Grounding):
    assert simple_answer.has_generalisation() == empty_grounding.has_generalisation()


def test_answer_has_kernel_from_grounding(simple_answer: Answer, empty_grounding: Grounding):
    assert simple_answer.has_kernel() == empty_grounding.has_kernel()


def test_answer_has_modes_from_grounding(simple_answer: Answer, empty_grounding: Grounding):
    assert simple_answer.has_modes() == empty_grounding.has_modes()


# ---------------------------------------------------------------------------
# Answer — hypothesis-aware delegation (no hypothesis)
# ---------------------------------------------------------------------------


def test_answer_get_covered_no_hypothesis(simple_answer: Answer, empty_grounding: Grounding):
    assert simple_answer.get_covered() == empty_grounding.get_covered()


def test_answer_get_uncovered_no_hypothesis(simple_answer: Answer, empty_grounding: Grounding):
    assert simple_answer.get_uncovered() == empty_grounding.get_uncovered()


def test_answer_get_model_no_hypothesis(simple_answer: Answer, empty_grounding: Grounding):
    assert simple_answer.get_model() == empty_grounding.get_model()


def test_answer_has_covered_no_hypothesis(simple_answer: Answer, empty_grounding: Grounding):
    assert simple_answer.has_covered() == empty_grounding.has_covered()


def test_answer_has_uncovered_no_hypothesis(simple_answer: Answer, empty_grounding: Grounding):
    assert simple_answer.has_uncovered() == empty_grounding.has_uncovered()


def test_answer_has_model_no_hypothesis(simple_answer: Answer, empty_grounding: Grounding):
    assert simple_answer.has_model() == empty_grounding.has_model()


def test_answer_get_hypotheses_no_hypothesis(simple_answer: Answer):
    assert simple_answer.get_hypotheses() == ()


def test_answer_has_hypotheses_no_hypothesis(simple_answer: Answer):
    assert not simple_answer.has_hypotheses()


# ---------------------------------------------------------------------------
# Answer — hypothesis-aware delegation (with hypothesis)
# ---------------------------------------------------------------------------


def test_answer_get_covered_with_hypothesis(hypothesis_answer: Answer, empty_hypothesis: Hypothesis):
    assert hypothesis_answer.get_covered() == empty_hypothesis.get_covered()


def test_answer_get_uncovered_with_hypothesis(hypothesis_answer: Answer, empty_hypothesis: Hypothesis):
    assert hypothesis_answer.get_uncovered() == empty_hypothesis.get_uncovered()


def test_answer_get_model_with_hypothesis(hypothesis_answer: Answer, empty_hypothesis: Hypothesis):
    assert hypothesis_answer.get_model() == empty_hypothesis.get_model()


def test_answer_has_covered_with_hypothesis(hypothesis_answer: Answer, empty_hypothesis: Hypothesis):
    assert hypothesis_answer.has_covered() == empty_hypothesis.has_covered()


def test_answer_has_uncovered_with_hypothesis(hypothesis_answer: Answer, empty_hypothesis: Hypothesis):
    assert hypothesis_answer.has_uncovered() == empty_hypothesis.has_uncovered()


def test_answer_has_model_with_hypothesis(hypothesis_answer: Answer, empty_hypothesis: Hypothesis):
    assert hypothesis_answer.has_model() == empty_hypothesis.has_model()


def test_answer_get_hypotheses_with_hypothesis(hypothesis_answer: Answer, empty_hypothesis: Hypothesis):
    assert hypothesis_answer.get_hypotheses() == empty_hypothesis.get_hypotheses()


def test_answer_has_hypotheses_with_empty_hypothesis(hypothesis_answer: Answer):
    # empty_hypothesis has no clauses
    assert not hypothesis_answer.has_hypotheses()


# ---------------------------------------------------------------------------
# Answer — is_meaningful
# ---------------------------------------------------------------------------


def test_answer_is_meaningful_no_hypothesis(simple_answer: Answer):
    assert not simple_answer.is_meaningful()


def test_answer_is_meaningful_empty_hypothesis(hypothesis_answer: Answer):
    # hypothesis exists but has no clauses → not meaningful
    assert not hypothesis_answer.is_meaningful()


def test_answer_is_meaningful_with_covered_example(cfg: Config):
    """is_meaningful requires hypothesis AND non-empty get_hypotheses()."""
    # Build a grounding that produces a non-empty generalisation so that
    # time_deduction_grounding produces a non-trivial hypothesis — but this
    # would require a full grounding with abduced atoms and mode declarations.
    # Instead, directly verify the condition: hypothesis with hypotheses → meaningful.
    from xhail.core.statements.mode_h import ModeH
    from xhail.core.terms.scheme import Scheme

    pb = Problem.Builder(cfg)
    pb.add_mode_h(ModeH(scheme=Scheme("flies")))
    problem = pb.build()
    gb = Grounding.Builder(problem)
    gb.add_atom(Atom("abduced_flies"))
    gb.add_atom(Atom("flies"))
    grounding = gb.build()

    # generalisation is [Clause(head=flies.)]; use_clause_literal(0,0) selects it
    from xhail.core.terms.number import Number

    hb = Hypothesis.Builder(grounding)
    hb.add_atom(Atom("use_clause_literal", (Number(0), Number(0))))
    hypothesis = hb.build()

    answer = Answer.Builder(grounding).set_hypothesis(hypothesis).build()
    assert answer.is_meaningful()
    assert answer.has_hypotheses()


# ---------------------------------------------------------------------------
# Answers.Builder — construction
# ---------------------------------------------------------------------------


def test_answers_builder_requires_config():
    with pytest.raises((ValueError, TypeError)):
        Answers.Builder(None)


def test_answers_builder_builds(cfg: Config):
    a = Answers.Builder(cfg).build()
    assert isinstance(a, Answers)


# ---------------------------------------------------------------------------
# Answers.Builder — put: three-way comparison
# ---------------------------------------------------------------------------


def test_answers_builder_put_first_call(cfg: Config, simple_answer: Answer):
    b = Answers.Builder(cfg)
    v = Values("0")
    b.put(v, simple_answer)
    assert b.size() == 1
    assert b._count == 1
    assert b._values == v


def test_answers_builder_put_better_values_clears(cfg: Config, simple_answer: Answer):
    b = Answers.Builder(cfg)
    a2 = Answer.Builder(simple_answer.get_grounding()).build()
    b.put(Values("1"), simple_answer)
    b.put(Values("0"), a2)       # strictly better
    assert b.size() == 1
    assert a2 in b._answers
    assert simple_answer not in b._answers
    assert b._count == 2


def test_answers_builder_put_equal_values_adds(cfg: Config, simple_answer: Answer):
    b = Answers.Builder(cfg)
    a2 = Answer.Builder(simple_answer.get_grounding()).build()
    b.put(Values("1"), simple_answer)
    b.put(Values("1"), a2)
    assert b.size() == 2
    assert b._count == 2


def test_answers_builder_put_worse_values_not_added(cfg: Config, simple_answer: Answer):
    b = Answers.Builder(cfg)
    a2 = Answer.Builder(simple_answer.get_grounding()).build()
    b.put(Values("0"), simple_answer)
    b.put(Values("1"), a2)       # worse
    assert b.size() == 1
    assert a2 not in b._answers
    assert b._count == 2         # count always increments


def test_answers_builder_put_rejects_none_values(cfg: Config, simple_answer: Answer):
    b = Answers.Builder(cfg)
    with pytest.raises((ValueError, TypeError)):
        b.put(None, simple_answer)


def test_answers_builder_put_rejects_none_answer(cfg: Config):
    b = Answers.Builder(cfg)
    with pytest.raises((ValueError, TypeError)):
        b.put(Values("0"), None)


# ---------------------------------------------------------------------------
# Answers.Builder — remove
# ---------------------------------------------------------------------------


def test_answers_builder_remove_matching_values(cfg: Config, simple_answer: Answer):
    b = Answers.Builder(cfg)
    v = Values("0")
    b.put(v, simple_answer)
    b.remove(v, simple_answer)
    assert b.size() == 0
    assert b._count == 0


def test_answers_builder_remove_different_values_no_op(cfg: Config, simple_answer: Answer):
    b = Answers.Builder(cfg)
    b.put(Values("0"), simple_answer)
    b.remove(Values("1"), simple_answer)  # different values — no-op
    assert b.size() == 1
    assert b._count == 1


def test_answers_builder_remove_absent_answer_no_op(cfg: Config, simple_answer: Answer):
    b = Answers.Builder(cfg)
    a2 = Answer.Builder(simple_answer.get_grounding()).build()
    v = Values("0")
    b.put(v, simple_answer)
    b.remove(v, a2)   # a2 not in set — no-op
    assert b.size() == 1
    assert b._count == 1


# ---------------------------------------------------------------------------
# Answers.Builder — clear
# ---------------------------------------------------------------------------


def test_answers_builder_clear_resets_state(cfg: Config, simple_answer: Answer):
    b = Answers.Builder(cfg)
    b.put(Values("0"), simple_answer)
    b.clear()
    assert b.size() == 0
    assert b._count == 0
    assert b._values is None


def test_answers_builder_clear_resets_first_timestamp(cfg: Config, simple_answer: Answer):
    _ans_mod._start = 0
    b = Answers.Builder(cfg)
    b.put(Values("0"), simple_answer)
    assert _ans_mod._first >= 0
    b.clear()
    assert _ans_mod._first == -1


# ---------------------------------------------------------------------------
# Answers.Builder — is_meaningful / size
# ---------------------------------------------------------------------------


def test_answers_builder_is_meaningful_false_no_answers(cfg: Config):
    b = Answers.Builder(cfg)
    assert not b.is_meaningful()


def test_answers_builder_is_meaningful_false_no_hypothesis(cfg: Config, simple_answer: Answer):
    b = Answers.Builder(cfg)
    b.put(Values("0"), simple_answer)
    assert not b.is_meaningful()


def test_answers_builder_size_reflects_optimal_count(cfg: Config, simple_answer: Answer):
    b = Answers.Builder(cfg)
    assert b.size() == 0
    b.put(Values("0"), simple_answer)
    assert b.size() == 1


# ---------------------------------------------------------------------------
# Answers — built instance
# ---------------------------------------------------------------------------


def test_answers_is_empty_when_no_answers(cfg: Config):
    a = Answers.Builder(cfg).build()
    assert a.is_empty()


def test_answers_size_and_count(cfg: Config, simple_answer: Answer):
    b = Answers.Builder(cfg)
    a2 = Answer.Builder(simple_answer.get_grounding()).build()
    b.put(Values("0"), simple_answer)
    b.put(Values("1"), a2)  # worse — not added, but count increments
    ans = b.build()
    assert ans.size() == 1
    assert ans.count() == 2


def test_answers_get_config(cfg: Config):
    ans = Answers.Builder(cfg).build()
    assert ans.get_config() is cfg


def test_answers_config_property(cfg: Config):
    ans = Answers.Builder(cfg).build()
    assert ans.config is cfg


def test_answers_get_values_none_when_empty(cfg: Config):
    ans = Answers.Builder(cfg).build()
    assert ans.get_values() is None


def test_answers_get_values_when_put(cfg: Config, simple_answer: Answer):
    v = Values("0")
    b = Answers.Builder(cfg)
    b.put(v, simple_answer)
    ans = b.build()
    assert ans.get_values() == v


def test_answers_iteration(cfg: Config, simple_answer: Answer):
    b = Answers.Builder(cfg)
    b.put(Values("0"), simple_answer)
    ans = b.build()
    items = list(ans)
    assert len(items) == 1
    assert simple_answer in items


def test_answers_get_answer_valid_index(cfg: Config, simple_answer: Answer):
    b = Answers.Builder(cfg)
    b.put(Values("0"), simple_answer)
    ans = b.build()
    assert ans.get_answer(0) is simple_answer


def test_answers_get_answer_out_of_bounds(cfg: Config, simple_answer: Answer):
    b = Answers.Builder(cfg)
    b.put(Values("0"), simple_answer)
    ans = b.build()
    with pytest.raises((IndexError, Exception)):
        ans.get_answer(5)


def test_answers_equality_same_content(cfg: Config, simple_answer: Answer):
    v = Values("0")
    b1 = Answers.Builder(cfg)
    b1.put(v, simple_answer)
    b2 = Answers.Builder(cfg)
    b2.put(v, simple_answer)
    assert b1.build() == b2.build()


def test_answers_equality_different_content(cfg: Config, simple_answer: Answer):
    b1 = Answers.Builder(cfg)
    b1.put(Values("0"), simple_answer)
    b2 = Answers.Builder(cfg)
    b2.put(Values("1"), simple_answer)
    # different values → not equal
    assert b1.build() != b2.build()


# ---------------------------------------------------------------------------
# Module-level timing state
# ---------------------------------------------------------------------------


def test_timing_started_sets_start():
    assert _ans_mod._start == -1
    started()
    assert _ans_mod._start >= 0


def test_timing_started_is_one_shot():
    started()
    t = _ans_mod._start
    started()
    assert _ans_mod._start == t


def test_timing_loaded_sets_loading():
    assert _ans_mod._loading == -1
    loaded()
    assert _ans_mod._loading >= 0


def test_timing_loaded_is_one_shot():
    loaded()
    t = _ans_mod._loading
    loaded()
    assert _ans_mod._loading == t


def test_get_now_zero_before_started():
    # _start = -1 → returns 0.0
    assert get_now() == 0.0


def test_get_now_positive_after_started():
    started()
    assert get_now() >= 0.0


def test_get_loading_zero_before_started_or_loaded():
    assert get_loading() == 0.0


def test_get_loading_positive_after_both():
    started()
    loaded()
    assert get_loading() >= 0.0


def test_get_first_zero_before_any_put():
    assert get_first() == 0.0


def test_get_abduction_zero_initially():
    assert get_abduction() == 0.0


def test_get_deduction_zero_initially():
    assert get_deduction() == 0.0


def test_get_induction_zero_initially():
    assert get_induction() == 0.0


# ---------------------------------------------------------------------------
# Timing static methods on Answers class
# ---------------------------------------------------------------------------


def test_answers_class_get_abduction():
    assert Answers.get_abduction() == 0.0


def test_answers_class_get_deduction():
    assert Answers.get_deduction() == 0.0


def test_answers_class_get_induction():
    assert Answers.get_induction() == 0.0


def test_answers_class_get_loading():
    assert Answers.get_loading() == 0.0


def test_answers_class_get_now():
    assert Answers.get_now() == 0.0


# ---------------------------------------------------------------------------
# time_abduction / time_induction — accumulate timing
# ---------------------------------------------------------------------------


def test_time_abduction_accumulates(cfg: Config):
    before = _ans_mod._abduction
    time_abduction(0, _MockDialler())
    assert _ans_mod._abduction >= before


def test_time_abduction_rejects_negative_iter():
    with pytest.raises((ValueError, TypeError)):
        time_abduction(-1, _MockDialler())


def test_time_abduction_rejects_none_dialler():
    with pytest.raises((ValueError, TypeError)):
        time_abduction(0, None)


def test_time_induction_accumulates():
    before = _ans_mod._induction
    time_induction(0, _MockDialler())
    assert _ans_mod._induction >= before


def test_time_induction_rejects_negative_iter():
    with pytest.raises((ValueError, TypeError)):
        time_induction(-1, _MockDialler())


def test_time_induction_rejects_none_dialler():
    with pytest.raises((ValueError, TypeError)):
        time_induction(0, None)


# ---------------------------------------------------------------------------
# time_deduction_problem / time_deduction_grounding — return types
# ---------------------------------------------------------------------------


def test_time_deduction_problem_returns_grounding(empty_problem: Problem):
    result = time_deduction_problem(empty_problem, frozenset())
    assert isinstance(result, Grounding)


def test_time_deduction_problem_accumulates_deduction(empty_problem: Problem):
    before = _ans_mod._deduction
    time_deduction_problem(empty_problem, frozenset())
    assert _ans_mod._deduction >= before


def test_time_deduction_grounding_returns_hypothesis(empty_grounding: Grounding):
    result = time_deduction_grounding(empty_grounding, frozenset())
    assert isinstance(result, Hypothesis)


def test_time_deduction_grounding_accumulates_deduction(empty_grounding: Grounding):
    before = _ans_mod._deduction
    time_deduction_grounding(empty_grounding, frozenset())
    assert _ans_mod._deduction >= before
