from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from xhail.core.terms.scheme_term import SchemeTerm
from xhail.core.terms.variable import Variable

if TYPE_CHECKING:
    from xhail.core.terms.term import Term


class Type(Enum):
    CONSTANT = ("$", "internal_const_par")
    INPUT = ("+", "internal_input_par")
    OUTPUT = ("-", "internal_output_par")

    def __init__(self, symbol: str, internal: str) -> None:
        self.symbol = symbol
        self.internal = internal

    def __str__(self) -> str:
        return self.symbol


CONSTANT_STRING = "internal_const_par"
INPUT_STRING = "internal_input_par"
OUTPUT_STRING = "internal_output_par"


@dataclass(frozen=True)
class Placemarker(SchemeTerm):
    identifier: str
    type: Type = Type.CONSTANT

    def __post_init__(self) -> None:
        s = self.identifier
        if not s or not ('a' <= s[0] <= 'z'):
            raise ValueError(f"Placemarker identifier must start with 'a'-'z', got: {s!r}")

    def __str__(self) -> str:
        return f"{self.type}{self.identifier}"

    def decode(self) -> SchemeTerm:
        from xhail.core.terms.scheme import Scheme  # ponytail: local import, Scheme exists from step 4 onward
        return Scheme(self.type.internal, (Scheme(self.identifier),))

    def generalises(self, *args, **kwargs) -> Term:
        if len(args) == 1:
            variables: set[Variable] = args[0]
            var = Variable(f"V{1 + len(variables)}", self)
            variables.add(var)
            return var
        term, map_ = args
        if self.type in (Type.INPUT, Type.OUTPUT):
            var = map_.get(term)
            if var is None:
                var = Variable(f"V{1 + len(map_)}", self)
                map_[term] = var
            return var
        return term
