from __future__ import annotations

import itertools
import sys
from dataclasses import dataclass, field

from xhail.core.terms.scheme import Scheme

CONSTRAINT_OP = ":"
KEYWORD = "#modeh"
PRIORITY_OP = "@"
SEPARATOR_OP = "-"
WEIGHT_OP = "="

_counter = itertools.count()


@dataclass(frozen=True)
class ModeH:
    scheme: Scheme
    lower: int = 0
    upper: int = sys.maxsize
    weight: int = 1
    priority: int = 1
    id: int = field(init=False, compare=False, hash=False, default=0)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", next(_counter))

    def __str__(self) -> str:
        parts = [KEYWORD, str(self.scheme)]
        if self.lower != 0 or self.upper != sys.maxsize:
            parts.append(f"{CONSTRAINT_OP}{self.lower}{SEPARATOR_OP}{self.upper}")
        if self.weight != 1:
            parts.append(f"{WEIGHT_OP}{self.weight}")
        if self.priority != 1:
            parts.append(f"{PRIORITY_OP}{self.priority}")
        return " ".join(parts) + "."

    def as_clauses(self) -> tuple[str, ...]:
        variables: set = set()
        atom = str(self.scheme.generalises(variables))
        types_list = self.scheme.get_types()
        types = (" :" + " :".join(types_list)) if types_list else ""
        lst = ("," + ",".join(types_list)) if types_list else ""
        return (
            f"% {self}",
            f"{self.lower} {{ abduced_{atom}{types} }} {self.upper}.",
            f"#minimize[ abduced_{atom} ={self.weight} @{self.priority}{types} ].",
            f"{atom}:-abduced_{atom}{lst}.",
            f"number_abduced({self.id},V):-V:=#count{{ abduced_{atom}{types} }}.",
        )

    def get_scheme(self) -> Scheme:
        return self.scheme

    def get_lower(self) -> int:
        return self.lower

    def get_upper(self) -> int:
        return self.upper

    def get_weight(self) -> int:
        return self.weight

    def get_priority(self) -> int:
        return self.priority
