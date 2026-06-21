from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from xhail.core.terms.term import Term

if TYPE_CHECKING:
    from xhail.core.terms.placemarker import Placemarker


@dataclass(frozen=True)
class Variable(Term):
    identifier: str
    type: Placemarker | None = None

    def __post_init__(self) -> None:
        s = self.identifier
        if not s or (s[0] != '_' and not ('A' <= s[0] <= 'Z')):
            raise ValueError(f"Variable identifier must start with '_' or 'A'-'Z', got: {s!r}")

    def __str__(self) -> str:
        return self.identifier
