from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    from xhail.core.terms.term import Term
    from xhail.core.terms.variable import Variable


class SchemeTerm(ABC):
    @overload
    def generalises(self, term: Term, map: dict[Term, Variable]) -> Term: ...

    @overload
    def generalises(self, variables: set[Variable]) -> Term: ...

    @abstractmethod
    def generalises(self, *args, **kwargs) -> Term: ...
