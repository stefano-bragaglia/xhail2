from __future__ import annotations

import logging

_SPACE_KEYWORDS = frozenset({
    "not", "#compute", "#const", "#display", "#domain",
    "#example", "#external", "#hide", "#modeb", "#modeh", "#show",
})


class Splitter:
    def __init__(self) -> None:
        self._stream = None
        self._statement = ""
        self._statements: dict[str, None] = {}
        self._state = self._normal

    def parse(self, stream) -> tuple[str, ...]:
        self._statements = {}
        self._statement = ""
        self._stream = stream
        self._state = self._normal
        while True:
            if self._state():
                break
        return tuple(self._statements)

    def _read_char(self) -> str | None:
        try:
            byte = self._stream.read(1)
            return chr(byte[0]) if byte else None
        except OSError:
            logging.error("cannot read from the input stream")
            return None

    def _save(self) -> None:
        if self._statement:
            self._statements[self._statement] = None

    def _needs_space(self) -> bool:
        return bool(self._statement) and any(
            map(self._statement.endswith, _SPACE_KEYWORDS)
        )

    def _normal_space(self) -> None:
        if self._needs_space():
            self._statement += " "

    def _normal_special(self, ch: str) -> None:
        if ch == '"':
            self._statement += ch
            self._state = self._string
        elif ch == ".":
            self._statement += ch
            self._state = self._dot
        elif ch == "%":
            self._state = self._comment
        else:
            self._statement += ch

    def _normal(self) -> bool:
        ch = self._read_char()
        if ch is None:
            self._save()
            self._state = self._eof
        elif ch in ("\t", " "):
            self._normal_space()
        elif ch not in ("\n", "\r", "\f"):
            self._normal_special(ch)
        return False

    def _dot_flush(self, ch: str | None) -> None:
        self._save()
        self._statement = ""
        if ch is None:
            self._state = self._eof
        elif ch == '"':
            self._statement = ch
            self._state = self._string
        elif ch == "%":
            self._state = self._comment
        else:
            self._state = self._normal

    def _dot(self) -> bool:
        ch = self._read_char()
        if ch is None or ch in ("\n", "\r", "\f", "\t", " ", '"', "%"):
            self._dot_flush(ch)
        elif ch == ".":
            self._statement += ch
            self._state = self._normal
        else:
            self._save()
            self._statement = ch
            self._state = self._normal
        return False

    def _string(self) -> bool:
        ch = self._read_char()
        if ch is None:
            self._save()
            self._state = self._eof
        elif ch == "\\":
            self._statement += ch
            self._state = self._escape
        elif ch == '"':
            self._statement += ch
            self._state = self._normal
        else:
            self._statement += ch
        return False

    def _escape(self) -> bool:
        ch = self._read_char()
        if ch is None:
            self._save()
            self._state = self._eof
        else:
            self._statement += ch
            self._state = self._string
        return False

    def _comment(self) -> bool:
        ch = self._read_char()
        if ch is None:
            self._save()
            self._state = self._eof
        elif ch == "\n":
            self._state = self._normal
        elif ch == "*":
            self._state = self._comment_multi
        else:
            self._state = self._comment_single
        return False

    def _comment_single(self) -> bool:
        ch = self._read_char()
        if ch is None:
            self._save()
            self._state = self._eof
        elif ch == "\n":
            self._state = self._normal
        return False

    def _comment_multi(self) -> bool:
        ch = self._read_char()
        if ch is None:
            self._save()
            self._state = self._eof
        elif ch == "*":
            self._state = self._comment_over
        return False

    def _comment_over(self) -> bool:
        ch = self._read_char()
        if ch is None:
            self._save()
            self._state = self._eof
        elif ch == "%":
            self._state = self._normal
        elif ch != "*":
            self._state = self._comment_multi
        return False

    def _eof(self) -> bool:
        return True
