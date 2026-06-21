from __future__ import annotations

import sys
from dataclasses import dataclass

from xhail.core.terms.scheme import Scheme

CONSTRAINT_OP = ":"
KEYWORD = "#modeb"
PRIORITY_OP = "@"
SEPARATOR_OP = "-"
WEIGHT_OP = "="


@dataclass(frozen=True)
class ModeB:
    scheme: Scheme
    negated: bool = False
    upper: int = sys.maxsize
    weight: int = 1
    priority: int = 1

    def __str__(self) -> str:
        parts = [KEYWORD]
        if self.negated:
            parts.append("not")
        parts.append(str(self.scheme))
        if self.upper != sys.maxsize:
            parts.append(f"{CONSTRAINT_OP}{self.upper}")
        if self.weight != 1:
            parts.append(f"{WEIGHT_OP}{self.weight}")
        if self.priority != 1:
            parts.append(f"{PRIORITY_OP}{self.priority}")
        return " ".join(parts) + "."

    def get_scheme(self) -> Scheme:
        return self.scheme

    def get_upper(self) -> int:
        return self.upper

    def get_weight(self) -> int:
        return self.weight

    def get_priority(self) -> int:
        return self.priority

    def is_negated(self) -> bool:
        return self.negated
