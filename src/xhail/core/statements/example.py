from __future__ import annotations

from dataclasses import dataclass

from xhail.core.terms.atom import Atom

KEYWORD = "#example"
WEIGHT_OP = "="
PRIORITY_OP = "@"


@dataclass(frozen=True)
class Example:
    atom: Atom
    negated: bool = False
    weight: int | None = None
    priority: int = 1

    @property
    def defeasible(self) -> bool:
        return self.weight is not None

    def __str__(self) -> str:
        parts = [KEYWORD]
        if self.negated:
            parts.append("not")
        parts.append(str(self.atom))
        if self.weight is not None and self.weight != 1:
            parts.append(f"{WEIGHT_OP}{self.weight}")
        if self.priority != 1:
            parts.append(f"{PRIORITY_OP}{self.priority}")
        return " ".join(parts) + "."

    def as_clauses(self) -> tuple[str, ...]:
        yes = "not " if self.negated else ""
        not_ = "" if self.negated else "not "
        w = self.weight if self.weight is not None else 1
        lines: list[str] = [
            f"% {self}",
            f"#maximize[ {yes}{self.atom} ={w} @{self.priority} ].",
        ]
        if not self.defeasible:
            lines.append(f":-{not_}{self.atom}.")
        return tuple(lines)

    def get_atom(self) -> Atom:
        return self.atom

    def get_priority(self) -> int:
        return self.priority

    def get_weight(self) -> int:
        return self.weight if self.weight is not None else 1

    def is_negated(self) -> bool:
        return self.negated

    def is_defeasible(self) -> bool:
        return self.defeasible
