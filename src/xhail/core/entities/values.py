from __future__ import annotations

import sys


class Values:
    __slots__ = ("_source", "_values")

    def __init__(self, source: str | None = None) -> None:
        if source is None:
            self._source: str = str(sys.maxsize)
            self._values: tuple[int, ...] = (sys.maxsize,)
        else:
            self._source, self._values = self._parse(source)

    def _parse(self, source: str) -> tuple[str, tuple[int, ...]]:
        stripped = source.strip()
        if not stripped:
            raise ValueError("Values source must not be empty")
        try:
            return stripped, tuple(map(int, stripped.split()))
        except ValueError as exc:
            raise ValueError(f"not a valid Values source: {source!r}") from exc

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Values):
            return NotImplemented
        return self._source == other._source and self._values == other._values

    def __hash__(self) -> int:
        return hash((self._source, self._values))

    def __lt__(self, other: Values) -> bool:
        for a, b in zip(self._values, other._values):
            if a != b:
                return a < b
        return False

    def __str__(self) -> str:
        return self._source

    def matches(self, source: str) -> bool:
        stripped = source.strip()
        if not stripped:
            raise ValueError("Values source must not be empty")
        return self._source == stripped

    def get_value(self, index: int) -> int:
        return self._values[index]
