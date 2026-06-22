"""Finder — locates versioned executables (gringo, clasp) on the filesystem."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _matches(filename: str, name: str) -> bool:
    return filename in (name, name + ".exe")


def _is_valid_executable(executable: Path | None) -> bool:
    return bool(executable) and executable.exists() and os.access(executable, os.X_OK)


def _is_valid_match(match: tuple[str, ...]) -> bool:
    return bool(match) and bool(" ".join(match).strip())


def _check_line(line: str, match: tuple[str, ...]) -> bool:
    pos = 0
    for pattern in match:
        idx = line.find(pattern, max(0, pos))
        pos = idx + len(pattern) if idx >= 0 else -1
    return pos >= 0


def _check_output(output: str, match: tuple[str, ...]) -> bool:
    for line in output.splitlines():
        if _check_line(line.lower(), match):
            return True
    return False


class Finder:
    def __init__(self, version: str, *apps: str) -> None:
        self._version = version
        self._apps: set[str] = set(apps)
        self._results: dict[str, Path] = {}

    def is_found(self) -> bool:
        return len(self._results) == len(self._apps)

    def get(self, name: str) -> Path | None:
        if not name.strip():
            raise ValueError("name must not be blank")
        return self._results.get(name)

    def test(self, name: str, file: Path | None) -> bool:
        if not name.strip() or name not in self._apps:
            raise ValueError(f"'{name}' is not a registered app")
        if name in self._results:
            return True
        if file is None:
            return False
        return self._try_register(name, file.name, file)

    def find(self, path: Path, recurse: bool) -> bool:
        if self.is_found():
            return True
        if not path or not path.exists():
            return False
        return self._walk(path, recurse)

    def _walk(self, path: Path, recurse: bool) -> bool:
        for root, _dirs, files in os.walk(path, topdown=True, followlinks=True):
            for filename in files:
                self._check_file(Path(root) / filename)
                if self.is_found():
                    return True
            if not recurse:
                break
        return self.is_found()

    def _check_file(self, filepath: Path) -> bool:
        for name in self._apps:
            if self._try_register(name, filepath.name, filepath):
                return True
        return False

    def _try_register(self, name: str, filename: str, filepath: Path) -> bool:
        if name in self._results:
            return False
        if not _matches(filename, name):
            return False
        if not os.access(filepath, os.X_OK):
            return False
        if not self.check(filepath, name, self._version):
            return False
        self._results[name] = filepath
        return self.is_found()

    @staticmethod
    def check(executable: Path, *match: str) -> bool:
        if not _is_valid_executable(executable) or not _is_valid_match(match):
            return False
        try:
            proc = subprocess.run(
                [str(executable), "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return _check_output(proc.stdout, match)
        except (OSError, subprocess.TimeoutExpired):
            return False
