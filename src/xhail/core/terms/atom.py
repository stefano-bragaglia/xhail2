from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from xhail.core.terms.placemarker import CONSTANT_STRING, INPUT_STRING, OUTPUT_STRING
from xhail.core.terms.term import Term
from xhail.core.terms.variable import Variable

if TYPE_CHECKING:
    from xhail.core.terms.scheme_term import SchemeTerm


@dataclass(frozen=True)
class Atom(Term):
    identifier: str
    terms: tuple[Term, ...] = ()
    weight: int = 1
    priority: int = 1
    scheme: SchemeTerm | None = None

    def __post_init__(self) -> None:
        s = self.identifier
        if not s or not ('a' <= s[0] <= 'z'):
            raise ValueError(f"Atom identifier must start with 'a'-'z', got: {s!r}")

    def __str__(self) -> str:
        if not self.terms:
            return self.identifier
        return f"{self.identifier}({','.join(str(t) for t in self.terms)})"

    def __iter__(self):
        return iter(self.terms)

    def __lt__(self, other: Atom) -> bool:
        if self.identifier != other.identifier:
            return self.identifier < other.identifier
        if len(self.terms) != len(other.terms):
            return len(self.terms) > len(other.terms)  # reversed: more terms sorts first
        for s, o in zip(self.terms, other.terms):
            if str(s) != str(o):
                return str(s) > str(o)  # reversed: higher str sorts first
        return False

    def get_arity(self) -> int:
        return len(self.terms)

    def get_term(self, index: int) -> Term:
        if index < 0 or index >= len(self.terms):
            raise IndexError(f"Index {index} out of range for atom of arity {len(self.terms)}")
        return self.terms[index]

    def _collect_variables(self, seen: dict) -> None:
        for term in self.terms:
            if isinstance(term, Variable):
                seen[term] = None
            elif isinstance(term, Atom):
                term._collect_variables(seen)

    def get_variables(self) -> tuple[Variable, ...]:
        seen: dict[Variable, None] = {}
        self._collect_variables(seen)
        return tuple(seen)

    def has_variables(self) -> bool:
        return bool(self.get_variables())

    def get_types(self) -> tuple[str, ...]:
        return tuple(f"{v.type.identifier}({v.identifier})" for v in self.get_variables())

    def has_types(self) -> bool:
        return self.has_variables()

    def is_placemarker(self) -> bool:
        return self.identifier in (CONSTANT_STRING, INPUT_STRING, OUTPUT_STRING) and len(self.terms) == 1


class Builder:
    def __init__(self, source) -> None:
        if isinstance(source, str):
            s = source
            if not s or not ('a' <= s[0] <= 'z'):
                raise ValueError(f"Atom identifier must start with 'a'-'z', got: {s!r}")
            self._identifier = s
            self._terms: list[Term] = []
            self._weight = 1
            self._priority = 1
            self._scheme = None
        else:
            self._identifier = source.identifier
            self._terms = list(source.terms)
            self._weight = source.weight
            self._priority = source.priority
            self._scheme = source.scheme

    def add_term(self, term: Term) -> Builder:
        self._terms.append(term)
        return self

    def clear_terms(self) -> Builder:
        self._terms.clear()
        return self

    def set_scheme(self, scheme) -> Builder:
        self._scheme = scheme
        return self

    def set_weight(self, weight: int) -> Builder:
        self._weight = weight
        return self

    def set_priority(self, priority: int) -> Builder:
        self._priority = priority
        return self

    def clone(self) -> Builder:
        b = Builder(self._identifier)
        b._terms = list(self._terms)
        b._weight = self._weight
        b._priority = self._priority
        b._scheme = self._scheme
        return b

    def build(self) -> Atom:
        return Atom(self._identifier, tuple(self._terms), self._weight, self._priority, self._scheme)


Atom.Builder = Builder  # type: ignore[attr-defined]
