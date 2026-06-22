from __future__ import annotations

import logging

from xhail.core.entities.values import Values
from xhail.core.parser.parser import ParserError
from xhail.core.parser.tokeniser import Tokeniser

_KEYWORDS = frozenset(
    {"FOUND", "Optimization:", "OPTIMUM", "SATISFIABLE", "UNKNOWN", "UNSATISFIABLE"}
)


class Acquirer:
    def __init__(self, stream) -> None:
        self._tokeniser = Tokeniser(stream)
        self._token: str | None = self._tokeniser.next()
        self._values = Values()
        self._answers: set[frozenset[str]] = set()
        self._atoms: set[str] = set()

    def parse(self) -> tuple[Values, set[frozenset[str]]]:
        self._answers = set()
        try:
            if self._token == "UNKNOWN":
                self._parse_keyword("UNKNOWN")
            elif self._token == "UNSATISFIABLE":
                self._parse_keyword("UNSATISFIABLE")
            else:
                self._parse_answer()
            self._parse_eof()
        except ParserError as exc:
            logging.error(str(exc))
        return self._values, self._answers

    def _parse_keyword(self, expected: str) -> None:
        if self._token is None:
            raise ParserError(f"expected '{expected}' but EOF found")
        if self._token != expected:
            raise ParserError(f"expected '{expected}' but '{self._token}' found")
        self._token = self._tokeniser.next()

    def _collect_atoms(self) -> None:
        self._atoms = set()
        while self._token is not None and self._token not in _KEYWORDS:
            self._atoms.add(self._token)
            self._token = self._tokeniser.next()

    def _parse_answer(self) -> None:
        self._collect_atoms()
        if self._token == "SATISFIABLE":
            self._parse_keyword("SATISFIABLE")
            self._answers.add(frozenset(self._atoms))
        else:
            self._parse_keyword("Optimization:")
            self._parse_values()

    def _collect_values_str(self) -> str:
        parts: list[str] = []
        while self._token is not None and self._token.isdigit():
            parts.append(self._token)
            self._token = self._tokeniser.next()
        return " ".join(parts)

    def _update_best(self, found: Values) -> None:
        if found < self._values:
            self._answers.clear()
            self._values = found
        if not (self._values < found):
            self._answers.add(frozenset(self._atoms))

    def _parse_values(self) -> None:
        if self._token is None:
            raise ParserError("expected NUMBER but EOF found")
        if not self._token.isdigit():
            raise ParserError(f"expected NUMBER but '{self._token}' found")
        self._update_best(Values(self._collect_values_str()))
        if self._token == "OPTIMUM":
            self._parse_keyword("OPTIMUM")
            self._parse_keyword("FOUND")
        else:
            self._parse_nested()

    def _parse_nested(self) -> None:
        self._collect_atoms()
        self._parse_keyword("Optimization:")
        self._parse_values()

    def _parse_eof(self) -> None:
        if self._token is not None:
            raise ParserError(f"expected EOF but '{self._token}' found")
