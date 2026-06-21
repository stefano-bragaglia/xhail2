from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from xhail.core.terms.atom import Atom

if TYPE_CHECKING:
    from xhail.core.terms.scheme_term import SchemeTerm
    from xhail.core.terms.variable import Variable


@dataclass(frozen=True)
class Literal:
    atom: Atom
    negated: bool = False
    level: int = 0

    def __post_init__(self) -> None:
        if self.level < 0:
            raise ValueError(f"Literal level must be >= 0, got: {self.level!r}")

    def __str__(self) -> str:
        return ("not " if self.negated else "") + str(self.atom)

    def __lt__(self, other: Literal) -> bool:
        if self.atom != other.atom:
            return self.atom < other.atom
        return other.negated < self.negated

    def get_atom(self) -> Atom:
        return self.atom

    def get_level(self) -> int:
        return self.level

    def is_negated(self) -> bool:
        return self.negated

    def get_priority(self) -> int:
        return self.atom.priority

    def get_weight(self) -> int:
        return self.atom.weight

    def get_scheme(self) -> SchemeTerm | None:
        return self.atom.scheme

    def has_variables(self) -> bool:
        return self.atom.has_variables()

    def get_variables(self) -> tuple[Variable, ...]:
        return self.atom.get_variables()

    def has_types(self) -> bool:
        return self.atom.has_types()

    def get_types(self) -> tuple[str, ...]:
        return self.atom.get_types()
