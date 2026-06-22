"""Dialler — runs gringo + clasp to find abduction/induction answer sets."""
from __future__ import annotations

import atexit
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from xhail.core.parser.acquirer import Acquirer

# ---------------------------------------------------------------------------
# Module-level state and constants
# ---------------------------------------------------------------------------

_calls: int = 0

_ERROR = "ERROR: "
_WARNING = "% warning: "
_IGNORED_WARNINGS: frozenset[str] = frozenset({
    "bad_solution/0 is never defined",
    "number_abduced/2 is never defined",
})


def calls() -> int:
    return _calls


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _make_temp() -> Path:
    fd, path_str = tempfile.mkstemp(prefix="xhail", suffix=".tmp")
    os.close(fd)
    p = Path(path_str)
    atexit.register(p.unlink, missing_ok=True)
    return p


def _log_command(debug: bool, cmd: list) -> None:
    if debug:
        from xhail.core.logger import SIGNATURE
        print(f"*** Info  ({SIGNATURE}): calling '{' '.join(cmd)}'")


def _process_error(msg: str, output: bool) -> None:
    if not output:
        from xhail.core import logger
        logger.error(msg)


def _write_source(solvable, iter_: int, source: Path, output: bool) -> bool:
    try:
        with open(source, "w", encoding="utf-8") as f:
            solvable.save(iter_, f)
        return True
    except Exception:
        _process_error("cannot write to 'gringo' process", output)
        return False


def _handle_line(line: str, message: str, mute: bool) -> str:
    if message:
        return message + "\n  " + line
    if line.startswith(_ERROR):
        return line[len(_ERROR):]
    if line.startswith(_WARNING):
        content = line[len(_WARNING):]
        if content not in _IGNORED_WARNINGS:
            from xhail.core import logger
            logger.warning(mute, content)
        return ""
    print(line, file=sys.stderr)
    return ""


def _handle_errors(errors_path: Path, mute: bool) -> None:
    message = ""
    try:
        with open(errors_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line:
                    message = _handle_line(line, message, mute)
    except OSError:
        _process_error("cannot read from child process' 'stderr'", False)
    if message:
        _process_error(message, False)


def _run_gringo(gringo_cmd: list, middle: Path, errors: Path, debug: bool, mute: bool, output: bool, kill: int) -> bool:
    _log_command(debug, gringo_cmd)
    try:
        timeout = kill if kill > 0 else None
        with open(middle, "wb") as mf, open(errors, "wb") as ef:
            subprocess.run(gringo_cmd, stdout=mf, stderr=ef, timeout=timeout, check=False)
        _handle_errors(errors, mute)
        return True
    except OSError:
        _process_error("cannot launch 'gringo' process", output)
    except subprocess.TimeoutExpired:
        _process_error("'gringo' process was interrupted", output)
    return False


def _build_commands(config, source: Path, middle: Path, values) -> tuple[list, list]:
    gringo = [str(config.gringo), str(source)]
    clasp = [str(config.clasp), str(middle), "--verbose=0", "--opt-mode=optN"]
    if values is not None:
        clasp.append(f"--opt-bound={values}")
    return gringo, clasp


def _parse_target(target: Path, output: bool) -> tuple | None:
    try:
        with open(target, "rb") as f:
            return Acquirer(f).parse()
    except Exception:
        _process_error("cannot read from 'clasp' process", output)
        return None


def _read_clasp(clasp_cmd: list, target: Path, debug: bool, output: bool, kill: int) -> tuple:
    _log_command(debug, clasp_cmd)
    try:
        timeout = kill if kill > 0 else None
        with open(target, "wb") as tf:
            subprocess.run(clasp_cmd, stdout=tf, timeout=timeout, check=False)
        result = _parse_target(target, output)
        return result if result is not None else (None, set())
    except OSError:
        _process_error("cannot launch 'clasp' process", output)
    except subprocess.TimeoutExpired:
        _process_error("'clasp' process was interrupted", output)
    return None, set()


# ---------------------------------------------------------------------------
# Dialler
# ---------------------------------------------------------------------------

class Dialler:

    def __init__(self, config, solvable, values=None) -> None:
        if config is None:
            raise ValueError("config must not be None")
        if solvable is None:
            raise ValueError("solvable must not be None")
        try:
            self._source = _make_temp()
            self._middle = _make_temp()
            self._errors = _make_temp()
            self._target = _make_temp()
        except OSError:
            from xhail.core import logger
            logger.error("cannot send data to processes")
        self._solvable = solvable
        self._debug = config.debug
        self._mute = config.mute
        self._output = config.output
        self._kill = config.kill
        self._gringo_cmd, self._clasp_cmd = _build_commands(config, self._source, self._middle, values)

    def execute(self, iter_: int) -> tuple:
        if iter_ < 0:
            raise ValueError(f"iter_ must be >= 0, got {iter_}")
        global _calls
        _calls += 1
        if not _write_source(self._solvable, iter_, self._source, self._output):
            return None, set()
        if not _run_gringo(self._gringo_cmd, self._middle, self._errors, self._debug, self._mute, self._output, self._kill):
            return None, set()
        return _read_clasp(self._clasp_cmd, self._target, self._debug, self._output, self._kill)
