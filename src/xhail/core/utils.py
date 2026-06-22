"""Utils — serialise Problem and Grounding to ASP streams."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import TextIO

from xhail.core import logger


# --- dump helpers ---

def _dump_displays(problem, stream: TextIO) -> None:
    if not problem.has_displays():
        return
    for display in problem.get_displays():
        print(str(display), file=stream)
    print(file=stream)


def _dump_background(problem, stream: TextIO) -> None:
    if not problem.has_background() and not problem.has_domains():
        return
    print("%% B. Background", file=stream)
    for s in problem.get_domains():
        print(s, file=stream)
    for s in problem.get_background():
        print(s, file=stream)
    print(file=stream)


def _dump_examples(problem, stream: TextIO) -> None:
    if not problem.has_examples():
        return
    print("%% E. Examples", file=stream)
    for example in problem.get_examples():
        print(str(example), file=stream)
    print(file=stream)


def _dump_modes(problem, stream: TextIO) -> None:
    if not problem.has_modes():
        return
    print("%% M. Modes", file=stream)
    for mode in problem.get_mode_hs():
        print(str(mode), file=stream)
    for mode in problem.get_mode_bs():
        print(str(mode), file=stream)
    print(file=stream)


# --- save helpers ---

def _write_filters(solvable, stream: TextIO) -> None:
    for f in solvable.get_filters():
        print(f, file=stream)
    print(file=stream)


def _write_background(solvable, stream: TextIO) -> None:
    print("%%% B. Background", file=stream)
    for s in solvable.get_domains():
        print(s, file=stream)
    for s in solvable.get_background():
        print(s, file=stream)


def _write_examples(solvable, stream: TextIO) -> None:
    print("%%% E. Examples", file=stream)
    for example in solvable.get_examples():
        for s in example.as_clauses():
            print(s, file=stream)


def _should_print(stmt: str, it: int) -> bool:
    return it > 0 or not stmt.startswith("number_abduced(")


def _write_inflation(problem, it: int, stream: TextIO) -> None:
    if it > 0:
        print(":-bad_solution.", file=stream)
        print("number_abduced(V):-V:=#sum[ number_abduced(_,W) =W ].", file=stream)
    for mode in problem.get_mode_hs():
        for stmt in mode.as_clauses():
            if _should_print(stmt, it):
                print(stmt, file=stream)


def _save_temp(saver, solvable, it: int, path: Path) -> bool:
    try:
        folder = Path("temp").resolve()
        folder.mkdir(exist_ok=True)
        file = folder / path.name
        try:
            with open(file, "w") as f:
                return saver(solvable, it, f)
        except OSError:
            logger.error(f"cannot write to '{path.name}' file (do we have rights?)")
    except OSError as exc:
        logger.warning(False, "cannot create 'temp' folder (do we have rights?)")
        print(exc, file=sys.stderr)
    return False


# --- public functions ---

def dump(problem, stream: TextIO) -> bool:
    try:
        _dump_displays(problem, stream)
        _dump_background(problem, stream)
        _dump_examples(problem, stream)
        _dump_modes(problem, stream)
        return True
    except Exception:
        logger.error("cannot stream data to process")
    return False


def save_problem(problem, it: int, stream: TextIO) -> bool:
    try:
        _write_filters(problem, stream)
        _write_background(problem, stream)
        for s in problem.get_refinements():
            print(s, file=stream)
        print(file=stream)
        _write_examples(problem, stream)
        print(file=stream)
        print("%%% I. Inflation", file=stream)
        _write_inflation(problem, it, stream)
        print(file=stream)
        return True
    except Exception:
        logger.error("cannot stream data to process")
    return False


def save_grounding(grounding, it: int, stream: TextIO) -> bool:
    try:
        _write_filters(grounding, stream)
        _write_background(grounding, stream)
        print(file=stream)
        _write_examples(grounding, stream)
        print(file=stream)
        print("%%% C. Compression", file=stream)
        for s in grounding.as_clauses():
            print(s, file=stream)
        print(file=stream)
        return True
    except Exception:
        logger.error("cannot stream data to process")
    return False


def save_temp_problem(problem, it: int, path: Path) -> bool:
    return _save_temp(save_problem, problem, it, path)


def save_temp_grounding(grounding, it: int, path: Path) -> bool:
    return _save_temp(save_grounding, grounding, it, path)
