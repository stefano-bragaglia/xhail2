from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from xhail.core.terms.atom import Atom, Builder
from xhail.core.terms.placemarker import CONSTANT_STRING, INPUT_STRING, OUTPUT_STRING, Placemarker
from xhail.core.terms.scheme_term import SchemeTerm

if TYPE_CHECKING:
    from xhail.core.terms.term import Term


@dataclass(frozen=True)
class Scheme(SchemeTerm):
    identifier: str
    terms: tuple[SchemeTerm, ...] = ()
    negated: bool = False

    def __post_init__(self) -> None:
        s = self.identifier
        if not s or not ('a' <= s[0] <= 'z'):
            raise ValueError(f"Scheme identifier must start with 'a'-'z', got: {s!r}")

    def __str__(self) -> str:
        result = "not " if self.negated else ""
        result += self.identifier
        if self.terms:
            result += f"({','.join(str(t) for t in self.terms)})"
        return result

    def __iter__(self):
        return iter(self.terms)

    def get_arity(self) -> int:
        return len(self.terms)

    def get_term(self, index: int) -> SchemeTerm:
        if index < 0 or index >= len(self.terms):
            raise IndexError(f"Index {index} out of range for scheme of arity {len(self.terms)}")
        return self.terms[index]

    def is_negated(self) -> bool:
        return self.negated

    def is_placemarker(self) -> bool:
        return self.identifier in (CONSTANT_STRING, INPUT_STRING, OUTPUT_STRING) and len(self.terms) in (1, 2)

    def generalises(self, *args, **kwargs) -> Term | None:
        if len(args) == 1:
            return self._generalises_set(args[0])
        atom, map_ = args
        if not isinstance(atom, Atom):
            return None
        return self._generalises_map(atom, map_)

    def _generalises_set(self, variables: set) -> Term | None:
        builder = Builder(self.identifier).set_scheme(self)
        for term in self.terms:
            nested = term.generalises(variables)
            if nested is None:
                return None
            builder.add_term(nested)
        return builder.build()

    def _generalises_map(self, atom: Atom, map_: dict) -> Term | None:
        if atom.identifier != self.identifier or len(atom.terms) != len(self.terms):
            return None
        builder = Builder(atom).clear_terms()
        for i, scheme_term in enumerate(self.terms):
            nested = scheme_term.generalises(atom.terms[i], map_)
            if nested is None:
                return None
            builder.add_term(nested)
        return builder.build()

    def _collect_placemarkers(self, seen: dict) -> None:
        for term in self.terms:
            if isinstance(term, Placemarker):
                seen[term] = None
            elif isinstance(term, Scheme):
                term._collect_placemarkers(seen)

    def get_placemarkers(self) -> tuple[Placemarker, ...]:
        seen: dict[Placemarker, None] = {}
        self._collect_placemarkers(seen)
        return tuple(seen)

    def has_placemarkers(self) -> bool:
        return bool(self.get_placemarkers())

    def get_types(self) -> tuple[str, ...]:
        return tuple(f"{pm.identifier}(V{i + 1})" for i, pm in enumerate(self.get_placemarkers()))

    def get_variables(self) -> tuple[str, ...]:
        return tuple(f"V{i + 1}" for i in range(len(self.get_placemarkers())))

    def _term_matches(self, scheme_term: SchemeTerm, atom_term: Term) -> bool:
        if isinstance(scheme_term, Placemarker):
            return True
        if isinstance(scheme_term, Scheme):
            return scheme_term.matches(atom_term)
        if type(scheme_term) is not type(atom_term):
            return False
        return scheme_term == atom_term  # Number or Quotation: value equality via __eq__

    def matches(self, candidate: Term) -> bool:
        if not isinstance(candidate, Atom):
            return False
        if candidate.identifier != self.identifier or len(candidate.terms) != len(self.terms):
            return False
        return all(self._term_matches(st, ct) for st, ct in zip(self.terms, candidate.terms))
