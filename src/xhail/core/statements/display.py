from __future__ import annotations

from dataclasses import dataclass

KEYWORD = "#display"


@dataclass(frozen=True)
class Display:
    identifier: str
    arity: int = 1

    def __post_init__(self) -> None:
        s = self.identifier
        if not s or not ('a' <= s[0] <= 'z'):
            raise ValueError(f"Display identifier must start with 'a'-'z', got: {s!r}")
        if self.arity < 0:
            raise ValueError(f"Display arity must be >= 0, got: {self.arity!r}")

    def __str__(self) -> str:
        return f"{KEYWORD} {self.identifier}/{self.arity}."

    def __lt__(self, other: Display) -> bool:
        if self.identifier != other.identifier:
            return self.identifier < other.identifier
        return self.arity > other.arity

    def as_clauses(self) -> str:
        vars_str = ",".join(f"V{i}" for i in range(1, self.arity + 1))
        atom_str = f"{self.identifier}({vars_str})" if vars_str else self.identifier
        return f"display_fact({atom_str}):-{atom_str}."

    def get_identifier(self) -> str:
        return self.identifier

    def get_arity(self) -> int:
        return self.arity
