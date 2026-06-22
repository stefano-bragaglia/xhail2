"""Answers — optimal answer set collection with nanosecond timing."""
from __future__ import annotations

import time as _time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from xhail.core.entities.grounding import Grounding
    from xhail.core.entities.hypothesis import Hypothesis

# ---------------------------------------------------------------------------
# Module-level timing state
# ---------------------------------------------------------------------------

_abduction: int = 0
_deduction: int = 0
_first: int = -1
_induction: int = 0
_loading: int = -1
_start: int = -1
_NORMALIZER: float = 1_000_000_000.0


# ---------------------------------------------------------------------------
# Lifecycle (one-shot)
# ---------------------------------------------------------------------------

def started() -> None:
    global _start
    if _start < 0:
        _start = _time.time_ns()


def loaded() -> None:
    global _loading
    if _loading < 0:
        _loading = _time.time_ns()


# ---------------------------------------------------------------------------
# Timing getters
# ---------------------------------------------------------------------------

def get_abduction() -> float:
    return _abduction / _NORMALIZER


def get_deduction() -> float:
    return _deduction / _NORMALIZER


def get_first() -> float:
    if _first < 0 or _start < 0:
        return 0.0
    return (_first - _start) / _NORMALIZER


def get_induction() -> float:
    return _induction / _NORMALIZER


def get_loading() -> float:
    if _loading < 0 or _start < 0:
        return 0.0
    return (_loading - _start) / _NORMALIZER


def get_now() -> float:
    if _start < 0:
        return 0.0
    return (_time.time_ns() - _start) / _NORMALIZER


# ---------------------------------------------------------------------------
# Timing computation functions
# ---------------------------------------------------------------------------

def time_abduction(iter_: int, dialler) -> tuple:
    if iter_ < 0:
        raise ValueError(f"iter_ must be >= 0, got {iter_}")
    if dialler is None:
        raise ValueError("dialler must not be None")
    global _abduction
    t = _time.time_ns()
    result = dialler.execute(iter_)
    _abduction += _time.time_ns() - t
    return result


def time_deduction_problem(problem, output) -> Grounding:
    from xhail.core.entities.grounding import Grounding as _Grounding
    global _deduction
    t = _time.time_ns()
    result = _Grounding.Builder(problem).parse(output).build()
    result.get_generalisation()
    _deduction += _time.time_ns() - t
    return result


def time_deduction_grounding(grounding, output) -> Hypothesis:
    from xhail.core.entities.hypothesis import Hypothesis as _Hypothesis
    global _deduction
    t = _time.time_ns()
    result = _Hypothesis.Builder(grounding).parse(output).build()
    result.get_hypotheses()
    _deduction += _time.time_ns() - t
    return result


def time_induction(iter_: int, dialler) -> tuple:
    if iter_ < 0:
        raise ValueError(f"iter_ must be >= 0, got {iter_}")
    if dialler is None:
        raise ValueError("dialler must not be None")
    global _induction
    t = _time.time_ns()
    result = dialler.execute(iter_)
    _induction += _time.time_ns() - t
    return result


# ---------------------------------------------------------------------------
# Answers
# ---------------------------------------------------------------------------

class Answers:

    class Builder:
        def __init__(self, config) -> None:
            if config is None:
                raise ValueError("config must not be None")
            self._answers: set = set()
            self._config = config
            self._count: int = 0
            self._values = None

        def put(self, values, answer) -> Answers.Builder:
            if values is None:
                raise ValueError("values must not be None")
            if answer is None:
                raise ValueError("answer must not be None")
            global _first
            if _first < 0:
                _first = _time.time_ns()
            if self._values is None:
                order = -1
            elif values < self._values:
                order = -1
            elif self._values < values:
                order = 1
            else:
                order = 0
            if order < 0:
                self._answers.clear()
                self._values = values
            if order <= 0:
                self._answers.add(answer)
            self._count += 1
            return self

        def remove(self, values, answer) -> Answers.Builder:
            if values is None:
                raise ValueError("values must not be None")
            if answer is None:
                raise ValueError("answer must not be None")
            if self._values is not None:
                equal = not (values < self._values) and not (self._values < values)
                if equal and answer in self._answers:
                    self._answers.discard(answer)
                    self._count -= 1
            return self

        def clear(self) -> Answers.Builder:
            global _first
            _first = -1
            self._answers.clear()
            self._count = 0
            self._values = None
            return self

        def is_meaningful(self) -> bool:
            return any(a.is_meaningful() for a in self._answers)

        def size(self) -> int:
            return len(self._answers)

        def build(self) -> Answers:
            return Answers(self)

    def __init__(self, builder: Answers.Builder) -> None:
        self._answers: tuple = tuple(builder._answers)
        self._config = builder._config
        self._count: int = builder._count
        self._values = builder._values

    def __iter__(self):
        return iter(self._answers)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Answers):
            return NotImplemented
        return (
            frozenset(self._answers) == frozenset(other._answers)
            and self._values == other._values
        )

    @property
    def config(self):
        return self._config

    def count(self) -> int:
        return self._count

    def get_answer(self, index: int):
        if index < 0 or index >= len(self._answers):
            raise IndexError(f"index {index} out of range [0, {len(self._answers)})")
        return self._answers[index]

    def get_answers(self) -> tuple:
        return self._answers

    def get_config(self):
        return self._config

    def get_values(self):
        return self._values

    def is_empty(self) -> bool:
        return len(self._answers) == 0

    def size(self) -> int:
        return len(self._answers)

    # Static delegates to module-level timing functions
    @staticmethod
    def get_abduction() -> float:
        return get_abduction()

    @staticmethod
    def get_deduction() -> float:
        return get_deduction()

    @staticmethod
    def get_first() -> float:
        return get_first()

    @staticmethod
    def get_induction() -> float:
        return get_induction()

    @staticmethod
    def get_loading() -> float:
        return get_loading()

    @staticmethod
    def get_now() -> float:
        return get_now()
