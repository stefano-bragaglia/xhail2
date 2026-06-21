from __future__ import annotations

from dataclasses import dataclass

from xhail.core.terms.atom import Atom
from xhail.core.terms.literal import Literal


@dataclass(frozen=True)
class Clause:
    head: Atom | None = None
    body: tuple[Literal, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "body", tuple(dict.fromkeys(self.body)))

    def __str__(self) -> str:
        head_str = str(self.head) if self.head else ""
        if self.body or not self.head:
            return head_str + ":-" + ",".join(str(lit) for lit in self.body) + "."
        return head_str + "."

    def __iter__(self):
        return iter(self.body)

    def get_head(self) -> Atom | None:
        return self.head

    def get_size(self) -> int:
        return len(self.body)

    def get_body(self, index: int) -> Literal:
        if index < 1 or index > len(self.body):
            raise IndexError(f"Index {index} out of range for clause body of size {len(self.body)}")
        return self.body[index - 1]

    def get_levels(self) -> int:
        return max((lit.level for lit in self.body), default=0)


class Builder:
    def __init__(self) -> None:
        self._body: dict[Literal, None] = {}
        self._head: Atom | None = None

    def add_literal(self, literal: Literal) -> Builder:
        self._body[literal] = None
        return self

    def add_literals(self, literals) -> Builder:
        for lit in literals:
            self._body[lit] = None
        return self

    def clear_body(self) -> Builder:
        self._body.clear()
        return self

    def remove_literal(self, literal: Literal) -> Builder:
        self._body.pop(literal, None)
        return self

    def remove_literals(self, literals) -> Builder:
        for lit in literals:
            self._body.pop(lit, None)
        return self

    def set_head(self, head: Atom) -> Builder:
        self._head = head
        return self

    def build(self) -> Clause:
        return Clause(self._head, tuple(self._body))


Clause.Builder = Builder  # type: ignore[attr-defined]
