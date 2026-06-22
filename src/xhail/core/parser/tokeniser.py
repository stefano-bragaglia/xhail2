from __future__ import annotations

import logging

_WHITESPACE = frozenset({" ", "\r", "\n"})


class Tokeniser:
    def __init__(self, stream) -> None:
        self._stream = stream
        self._done = False

    def _read_byte(self) -> int:
        try:
            byte = self._stream.read(1)
            return byte[0] if byte else -1
        except OSError:
            logging.error("cannot read from the input stream")
            return -1

    def _skip_ws(self) -> str | None:
        while True:
            raw = self._read_byte()
            if raw == -1:
                return None
            ch = chr(raw)
            if ch not in _WHITESPACE:
                return ch

    def _process_char(
        self, ch: str, buf: list, in_str: bool, in_esc: bool
    ) -> tuple[bool, bool, bool]:
        if in_esc:
            buf.append(ch)
            return in_str, False, False
        if not in_str and ch in _WHITESPACE:
            return False, False, True
        buf.append(ch)
        if in_str:
            return ch != '"', ch == "\\", False
        return ch == '"', False, False

    def _collect_token(self, first: str) -> str:
        buf = [first]
        in_str, in_esc = False, False
        while True:
            raw = self._read_byte()
            if raw == -1:
                break
            in_str, in_esc, done = self._process_char(chr(raw), buf, in_str, in_esc)
            if done:
                break
        return "".join(buf)

    def next(self) -> str | None:
        if self._done:
            return None
        ch = self._skip_ws()
        if ch is None:
            self._done = True
            return None
        return self._collect_token(ch)
