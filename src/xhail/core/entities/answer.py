"""Answer — pairs a Grounding with an optional Hypothesis."""
from __future__ import annotations

from typing import TYPE_CHECKING

from xhail.core.entities.grounding import Grounding
from xhail.core.entities.hypothesis import Hypothesis

if TYPE_CHECKING:
    from xhail.core.terms.atom import Atom
    from xhail.core.terms.clause import Clause
    from xhail.core.terms.literal import Literal


class Answer:

    class Builder:
        def __init__(self, grounding: Grounding) -> None:
            if grounding is None:
                raise ValueError("grounding must not be None")
            self._grounding = grounding
            self._hypothesis: Hypothesis | None = None

        def set_hypothesis(self, hypothesis: Hypothesis) -> Answer.Builder:
            if hypothesis is None:
                raise ValueError("hypothesis must not be None")
            self._hypothesis = hypothesis
            return self

        def build(self) -> Answer:
            return Answer(self)

    def __init__(self, builder: Answer.Builder) -> None:
        self._grounding = builder._grounding
        self._hypothesis = builder._hypothesis

    # -- hypothesis-aware delegation ------------------------------------------

    def get_covered(self) -> tuple[Literal, ...]:
        if self._hypothesis is not None:
            return self._hypothesis.get_covered()
        return self._grounding.get_covered()

    def get_uncovered(self) -> tuple[Literal, ...]:
        if self._hypothesis is not None:
            return self._hypothesis.get_uncovered()
        return self._grounding.get_uncovered()

    def get_model(self) -> tuple[Atom, ...]:
        if self._hypothesis is not None:
            return self._hypothesis.get_model()
        return self._grounding.get_model()

    def has_covered(self) -> bool:
        if self._hypothesis is not None:
            return self._hypothesis.has_covered()
        return self._grounding.has_covered()

    def has_uncovered(self) -> bool:
        if self._hypothesis is not None:
            return self._hypothesis.has_uncovered()
        return self._grounding.has_uncovered()

    def has_model(self) -> bool:
        if self._hypothesis is not None:
            return self._hypothesis.has_model()
        return self._grounding.has_model()

    def get_hypotheses(self) -> tuple[Clause, ...]:
        if self._hypothesis is None:
            return ()
        return self._hypothesis.get_hypotheses()

    def has_hypotheses(self) -> bool:
        if self._hypothesis is None:
            return False
        return self._hypothesis.has_hypotheses()

    # -- always from grounding -------------------------------------------------

    def get_delta(self) -> tuple[Atom, ...]:
        return self._grounding.get_delta()

    def get_domains(self) -> tuple[str, ...]:
        return self._grounding.get_domains()

    def get_grounding(self) -> Grounding:
        return self._grounding

    def get_hypothesis(self) -> Hypothesis | None:
        return self._hypothesis

    def get_kernel(self) -> tuple[Clause, ...]:
        return self._grounding.get_kernel()

    def get_problem(self):
        return self._grounding.get_problem()

    def has_background(self) -> bool:
        return self._grounding.has_background()

    def has_delta(self) -> bool:
        return self._grounding.has_delta()

    def has_displays(self) -> bool:
        return self._grounding.has_displays()

    def has_domains(self) -> bool:
        return bool(self._grounding.get_domains())

    def has_examples(self) -> bool:
        return self._grounding.has_examples()

    def has_generalisation(self) -> bool:
        return self._grounding.has_generalisation()

    def has_kernel(self) -> bool:
        return self._grounding.has_kernel()

    def has_modes(self) -> bool:
        return self._grounding.has_modes()

    # -- meaningful -----------------------------------------------------------

    def is_meaningful(self) -> bool:
        return self._hypothesis is not None and bool(self._hypothesis.get_hypotheses())
