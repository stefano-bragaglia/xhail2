from __future__ import annotations

from dataclasses import dataclass

from xhail.core.terms.scheme_term import SchemeTerm
from xhail.core.terms.term import Term


@dataclass(frozen=True)
class Number(Term, SchemeTerm):
    value: int

    def __str__(self) -> str:
        return str(self.value)

    def generalises(self, *args, **kwargs) -> Term | None:
        if len(args) == 1:  # generalises(set[Variable]) -> Term
            return self
        term, _ = args  # generalises(Term, dict[Term, Variable]) -> Term | None
        if isinstance(term, Number) and term.value == self.value:
            return self
        return None
