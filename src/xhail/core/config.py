"""Config dataclass holding all CLI flags and derived state."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    all: bool = False
    blind: bool = False
    clasp: Path | None = None
    debug: bool = False
    full: bool = False
    gringo: Path | None = None
    help_: bool = False
    iterations: int = 0
    kill: int = 0
    mute: bool = False
    output: bool = False
    prettify: bool = False
    search: bool = False
    sources: tuple[Path, ...] = ()
    terminate: bool = False
    version: bool = False
    name: str = field(init=False, compare=False, hash=False, repr=False, default="")

    def __post_init__(self) -> None:
        self.name = _derive_name(self.sources)
        for src in self.sources:
            if not src.exists() or src.is_dir():
                raise ValueError(f"source '{src}' is not accessible")

    def has_sources(self) -> bool:
        return bool(self.sources)

    def __str__(self) -> str:
        parts = _flags_abcd(self) + _flags_fgh(self) + _flags_ikm(self) + _flags_psv(self)
        return "".join(parts) + "".join(f" {src}" for src in self.sources)


def _derive_name(sources: tuple[Path, ...]) -> str:
    if not sources:
        return "stdin"
    filename = sources[0].name
    pos = filename.rfind(".")
    stem = filename[:pos] if pos >= 0 else filename
    return stem if stem else "file"


def _flags_abcd(config: Config) -> list[str]:
    parts: list[str] = []
    if config.all:
        parts.append(" -a")
    if config.blind:
        parts.append(" -b")
    if config.clasp:
        parts.append(f" -c {config.clasp}")
    if config.debug:
        parts.append(" -d")
    return parts


def _flags_fgh(config: Config) -> list[str]:
    parts: list[str] = []
    if config.full:
        parts.append(" -f")
    if config.gringo:
        parts.append(f" -g {config.gringo}")
    if config.help_:
        parts.append(" -h")
    return parts


def _flags_ikm(config: Config) -> list[str]:
    parts: list[str] = []
    if config.iterations > 0:
        parts.append(f" -i {config.iterations}")
    if config.kill > 0:
        parts.append(f" -k {config.kill}")
    if config.mute:
        parts.append(" -m")
    return parts


def _flags_psv(config: Config) -> list[str]:
    parts: list[str] = []
    if config.prettify:
        parts.append(" -p")
    if config.search:
        parts.append(" -s")
    if config.version:
        parts.append(" -v")
    return parts
