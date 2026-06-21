from __future__ import annotations

from dataclasses import dataclass

from xhail.core.terms.scheme_term import SchemeTerm
from xhail.core.terms.term import Term


@dataclass(frozen=True)
class Quotation(Term, SchemeTerm):
    content: str

    def __post_init__(self) -> None:
        c = self.content.strip()
        if len(c) < 2 or not c.startswith('"') or not c.endswith('"'):
            raise ValueError(f"Quotation content must be a double-quoted string, got: {self.content!r}")

    def __str__(self) -> str:
        return self.content

    def generalises(self, *args, **kwargs) -> Term | None:
        if len(args) == 1:  # generalises(set[Variable]) -> Term
            return self
        term, _ = args  # generalises(Term, dict[Term, Variable]) -> Term | None
        if isinstance(term, Quotation) and term.content == self.content:
            return self
        return None
