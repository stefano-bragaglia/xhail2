from __future__ import annotations

import logging
import sys

from xhail.core.statements.display import Display
from xhail.core.statements.example import Example
from xhail.core.statements.mode_b import ModeB
from xhail.core.statements.mode_h import ModeH
from xhail.core.terms.atom import Atom
from xhail.core.terms.number import Number
from xhail.core.terms.placemarker import Placemarker, Type
from xhail.core.terms.quotation import Quotation
from xhail.core.terms.scheme import Scheme
from xhail.core.terms.variable import Variable


class ParserError(Exception):
    pass


class Parser:
    def __init__(self, source: str) -> None:
        self._source = source
        self._pos = -1
        self._current: str | None = None
        self._advance()

    def _advance(self) -> None:
        self._pos += 1
        self._current = self._source[self._pos] if self._pos < len(self._source) else None

    def _skip(self) -> None:
        while self._current is not None and self._current <= " ":
            self._advance()

    # --- char predicates ---

    def _is_ident_char(self, ch: str) -> bool:
        return ch.isalpha() or ch.isdigit() or ch == "_"

    def _is_variable_start(self, ch: str) -> bool:
        return ch.isupper() or ch == "_"

    def _is_number_start(self, ch: str) -> bool:
        return ch.isdigit() or ch == "-"

    def _is_placemarker_start(self, ch: str) -> bool:
        return ch in ("+", "-", "$")

    # --- number sub-helpers ---

    def _consume_minus(self) -> bool:
        if self._current == "-":
            self._advance()
            self._skip()
            return True
        return False

    def _collect_digits(self) -> str:
        digits = []
        while self._current is not None and self._current.isdigit():
            digits.append(self._current)
            self._advance()
        return "".join(digits)

    # --- punctuation consumers ---

    def _parse_char(self, ch: str, name: str) -> None:
        self._skip()
        if self._current is None:
            raise ParserError(f"expected '{name}' but EOF found in '{self._source}'")
        if self._current != ch:
            raise ParserError(f"expected '{name}' but '{self._current}' found in '{self._source}'")
        self._advance()

    def _parse_left_paren(self) -> None:
        self._parse_char("(", "(")

    def _parse_right_paren(self) -> None:
        self._parse_char(")", ")")

    def _parse_comma(self) -> None:
        self._parse_char(",", ",")

    def _parse_colon(self) -> None:
        self._parse_char(":", ":")

    def _parse_dash(self) -> None:
        self._parse_char("-", "-")

    def _parse_slash(self) -> None:
        self._parse_char("/", "/")

    def _parse_equal(self) -> None:
        self._parse_char("=", "=")

    def _parse_at(self) -> None:
        self._parse_char("@", "@")

    # --- leaf parsers ---

    def _parse_identifier(self) -> str:
        self._skip()
        if self._current is None:
            raise ParserError(f"expected 'a..z' but EOF found in '{self._source}'")
        if not self._current.islower():
            raise ParserError(f"expected 'a..z' but '{self._current}' found in '{self._source}'")
        chars = []
        while self._current is not None and self._is_ident_char(self._current):
            chars.append(self._current)
            self._advance()
        return "".join(chars)

    def _parse_variable(self) -> Variable:
        self._skip()
        if self._current is None:
            raise ParserError(f"expected 'A..Z' or '_' but EOF found in '{self._source}'")
        if not self._is_variable_start(self._current):
            raise ParserError(f"expected 'A..Z' or '_' but '{self._current}' found in '{self._source}'")
        chars = []
        while self._current is not None and self._is_ident_char(self._current):
            chars.append(self._current)
            self._advance()
        return Variable("".join(chars))

    def _parse_number(self) -> Number:
        self._skip()
        if self._current is None:
            raise ParserError(f"expected '-' or '0..9' but EOF found in '{self._source}'")
        negative = self._consume_minus()
        if self._current is None:
            raise ParserError(f"expected '0..9' but EOF found in '{self._source}'")
        if not self._current.isdigit():
            raise ParserError(f"expected '0..9' but '{self._current}' found in '{self._source}'")
        value = int(self._collect_digits())
        return Number(-value if negative else value)

    def _parse_quotation(self) -> Quotation:
        self._skip()
        if self._current != '"':
            raise ParserError(f"expected '\"' but '{self._current}' found in '{self._source}'")
        chars = [self._current]
        self._advance()
        while self._current is not None and self._current != '"':
            chars.append(self._current)
            self._advance()
        if self._current is None:
            raise ParserError(f"expected '\"' but EOF found in '{self._source}'")
        chars.append(self._current)
        self._advance()
        return Quotation("".join(chars))

    def _parse_placemarker(self) -> Placemarker:
        self._skip()
        if self._current is None:
            raise ParserError(f"expected 'TERM' but EOF found in '{self._source}'")
        if self._current == "+":
            pm_type = Type.INPUT
        elif self._current == "-":
            pm_type = Type.OUTPUT
        elif self._current == "$":
            pm_type = Type.CONSTANT
        else:
            raise ParserError(f"expected '+', '-' or '$' but '{self._current}' found in '{self._source}'")
        self._advance()
        return Placemarker(self._parse_identifier(), pm_type)

    # --- dispatch helpers ---

    def _dispatch_term(self):
        ch = self._current
        if ch.islower():
            return self._parse_atom()
        if self._is_variable_start(ch):
            return self._parse_variable()
        if self._is_number_start(ch):
            return self._parse_number()
        if ch == '"':
            return self._parse_quotation()
        return None

    def _dispatch_ground_term(self):
        ch = self._current
        if ch.islower():
            return self._parse_atom()
        if self._is_number_start(ch):
            return self._parse_number()
        if ch == '"':
            return self._parse_quotation()
        return None

    def _dispatch_scheme_term(self):
        ch = self._current
        if ch.islower():
            return self._parse_scheme()
        if self._is_placemarker_start(ch):
            return self._parse_placemarker()
        if ch.isdigit():
            return self._parse_number()
        if ch == '"':
            return self._parse_quotation()
        return None

    # --- compound parsers ---

    def _parse_term(self):
        self._skip()
        if self._current is None:
            raise ParserError(f"expected 'TERM' but EOF found in '{self._source}'")
        result = self._dispatch_term()
        if result is None:
            raise ParserError(f"expected 'TERM' but '{self._current}' found in '{self._source}'")
        return result

    def _parse_ground_term(self):
        self._skip()
        if self._current is None:
            raise ParserError(f"expected 'TERM' but EOF found in '{self._source}'")
        result = self._dispatch_ground_term()
        if result is None:
            raise ParserError(f"expected 'TERM' but '{self._current}' found in '{self._source}'")
        return result

    def _parse_scheme_term(self):
        self._skip()
        if self._current is None:
            raise ParserError(f"expected 'SCHEMETERM' but EOF found in '{self._source}'")
        result = self._dispatch_scheme_term()
        if result is None:
            raise ParserError(f"expected 'SCHEMETERM' but '{self._current}' found in '{self._source}'")
        return result

    def _parse_atom(self) -> Atom:
        identifier = self._parse_identifier()
        self._skip()
        if self._current != "(":
            return Atom(identifier)
        self._parse_left_paren()
        terms = [self._parse_term()]
        self._skip()
        while self._current == ",":
            self._parse_comma()
            terms.append(self._parse_term())
            self._skip()
        self._parse_right_paren()
        return Atom(identifier, tuple(terms))

    def _parse_ground_atom(self) -> Atom:
        identifier = self._parse_identifier()
        self._skip()
        if self._current != "(":
            return Atom(identifier)
        self._parse_left_paren()
        terms = [self._parse_ground_term()]
        self._skip()
        while self._current == ",":
            self._parse_comma()
            terms.append(self._parse_ground_term())
            self._skip()
        self._parse_right_paren()
        return Atom(identifier, tuple(terms))

    def _parse_scheme(self) -> Scheme:
        identifier = self._parse_identifier()
        self._skip()
        if self._current != "(":
            return Scheme(identifier)
        self._parse_left_paren()
        terms = [self._parse_scheme_term()]
        self._skip()
        while self._current == ",":
            self._parse_comma()
            terms.append(self._parse_scheme_term())
            self._skip()
        self._parse_right_paren()
        return Scheme(identifier, tuple(terms))

    def _parse_answer(self) -> set[Atom]:
        self._skip()
        result: set[Atom] = set()
        while self._current is not None and self._current.islower():
            result.add(self._parse_ground_atom())
            self._skip()
        return result

    def _parse_display(self) -> Display:
        identifier = self._parse_identifier()
        self._parse_slash()
        if self._current is None:
            raise ParserError(f"expected '0..9' but EOF found in '{self._source}'")
        if not self._current.isdigit():
            raise ParserError(f"expected '0..9' but '{self._current}' found in '{self._source}'")
        number = self._parse_number()
        return Display(identifier, number.value)

    def _parse_example(self) -> Example:
        atom = self._parse_ground_atom()
        negated = atom.identifier == "not"
        if negated:
            atom = self._parse_ground_atom()
        weight = None
        if self._current == "=":
            self._parse_equal()
            weight = self._parse_number().value
        priority = 1
        if self._current == "@":
            self._parse_at()
            priority = self._parse_number().value
        return Example(atom, negated, weight, priority)

    def _parse_mode_b(self) -> ModeB:
        scheme = self._parse_scheme()
        negated = scheme.identifier == "not"
        if negated:
            scheme = self._parse_scheme()
        upper = sys.maxsize
        if self._current == ":":
            self._parse_colon()
            upper = self._parse_number().value
        weight = 1
        if self._current == "=":
            self._parse_equal()
            weight = self._parse_number().value
        priority = 1
        if self._current == "@":
            self._parse_at()
            priority = self._parse_number().value
        return ModeB(scheme, negated, upper, weight, priority)

    def _parse_mode_h(self) -> ModeH:
        scheme = self._parse_scheme()
        lower = 0
        upper = sys.maxsize
        if self._current == ":":
            self._parse_colon()
            value = self._parse_number().value
            if self._current == "-":
                lower = value
                self._parse_dash()
                upper = self._parse_number().value
            else:
                upper = value
        weight = 1
        if self._current == "=":
            self._parse_equal()
            weight = self._parse_number().value
        priority = 1
        if self._current == "@":
            self._parse_at()
            priority = self._parse_number().value
        return ModeH(scheme, lower, upper, weight, priority)

    def _parse_eof(self) -> None:
        self._skip()
        if self._current is not None:
            raise ParserError(f"expected EOF but '{self._current}' found in '{self._source}'")


# --- public API ---


def parse_token(source: str) -> Atom | None:
    try:
        parser = Parser(source)
        result = parser._parse_ground_atom()
        parser._parse_eof()
        return result
    except ParserError as exc:
        logging.error(str(exc))
        return None


def parse_answer(source: str) -> set[Atom] | None:
    try:
        parser = Parser(source)
        result = parser._parse_answer()
        parser._parse_eof()
        return result
    except ParserError as exc:
        logging.error(str(exc))
        return None


def parse_display(source: str) -> Display | None:
    try:
        parser = Parser(source)
        result = parser._parse_display()
        parser._parse_eof()
        return result
    except ParserError as exc:
        logging.error(str(exc))
        return None


def parse_example(source: str) -> Example | None:
    try:
        parser = Parser(source)
        result = parser._parse_example()
        parser._parse_eof()
        return result
    except ParserError as exc:
        logging.error(str(exc))
        return None


def parse_mode_b(source: str) -> ModeB | None:
    try:
        parser = Parser(source)
        result = parser._parse_mode_b()
        parser._parse_eof()
        return result
    except ParserError as exc:
        logging.error(str(exc))
        return None


def parse_mode_h(source: str) -> ModeH | None:
    try:
        parser = Parser(source)
        result = parser._parse_mode_h()
        parser._parse_eof()
        return result
    except ParserError as exc:
        logging.error(str(exc))
        return None
