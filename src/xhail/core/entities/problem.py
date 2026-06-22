"""Problem — central aggregation class for the XHAIL abduction/induction loop."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from xhail.core.config import Config
from xhail.core.parser.parser import parse_display, parse_example, parse_mode_b, parse_mode_h
from xhail.core.parser.splitter import Splitter
from xhail.core.statements.display import Display
from xhail.core.statements.example import Example
from xhail.core.statements.mode_b import ModeB
from xhail.core.statements.mode_h import ModeH
from xhail.core.terms.atom import Atom

if TYPE_CHECKING:
    from xhail.core.terms.scheme import Scheme


# ---------------------------------------------------------------------------
# add_background / remove_background helpers
# ---------------------------------------------------------------------------

def _warn_keyword(config: Config, stmt: str) -> bool:
    for prefix in ("#compute", "#hide", "#show"):
        if stmt.startswith(prefix):
            from xhail.core import logger
            logger.warning(config.mute, f"'{prefix}' statements are not supported and will be ignored")
            return True
    return False


def _try_add(stmt: str, keyword: str, parser, target: dict) -> bool:
    if not (stmt.startswith(keyword) and stmt.endswith(".")):
        return False
    result = parser(stmt[len(keyword):-1].strip())
    if result is not None:
        target[result] = None
    return True


def _add_stmt_to(builder: Problem.Builder, stmt: str) -> bool:
    return (_try_add(stmt, "#display", parse_display, builder._displays)
            or _try_add(stmt, "#example", parse_example, builder._examples))


def _add_mode_to(builder: Problem.Builder, stmt: str) -> bool:
    return (_try_add(stmt, "#modeb", parse_mode_b, builder._mode_bs)
            or _try_add(stmt, "#modeh", parse_mode_h, builder._mode_hs))


def _add_plain(builder: Problem.Builder, stmt: str) -> None:
    if stmt.startswith("#domain"):
        builder._domains[stmt] = None
    else:
        builder._background[stmt] = None


def _try_remove(stmt: str, keyword: str, parser, target: dict) -> bool:
    if not (stmt.startswith(keyword) and stmt.endswith(".")):
        return False
    result = parser(stmt[len(keyword):-1].strip())
    if result is not None:
        target.pop(result, None)
    return True


def _remove_stmt_from(builder: Problem.Builder, stmt: str) -> bool:
    return (_try_remove(stmt, "#display", parse_display, builder._displays)
            or _try_remove(stmt, "#example", parse_example, builder._examples))


def _remove_mode_from(builder: Problem.Builder, stmt: str) -> bool:
    return (_try_remove(stmt, "#modeb", parse_mode_b, builder._mode_bs)
            or _try_remove(stmt, "#modeh", parse_mode_h, builder._mode_hs))


def _remove_plain(builder: Problem.Builder, stmt: str) -> None:
    if stmt.startswith("#domain"):
        builder._domains.pop(stmt, None)
    else:
        builder._background.pop(stmt, None)


def _remove_plain(builder: Problem.Builder, stmt: str) -> None:
    if stmt.startswith("#domain"):
        builder._domains.pop(stmt, None)
    else:
        builder._background.pop(stmt, None)


# ---------------------------------------------------------------------------
# get_filters helpers
# ---------------------------------------------------------------------------

def _filter_displays_examples(problem: Problem, result: set) -> None:
    for d in problem._displays:
        result.add(f"#show {d.get_identifier()}/{d.get_arity()}.")
    for e in problem._examples:
        a = e.get_atom()
        result.add(f"#show {a.identifier}/{a.get_arity()}.")


def _filter_mode_h(mode: ModeH, result: set) -> None:
    s: Scheme = mode.get_scheme()
    result.add(f"#show {s.identifier}/{s.get_arity()}.")
    result.add(f"#show abduced_{s.identifier}/{s.get_arity()}.")
    for pm in s.get_placemarkers():
        result.add(f"#show {pm.identifier}/1.")


def _filter_mode_b(mode: ModeB, result: set) -> None:
    s: Scheme = mode.get_scheme()
    result.add(f"#show {s.identifier}/{s.get_arity()}.")
    for pm in s.get_placemarkers():
        result.add(f"#show {pm.identifier}/1.")


# ---------------------------------------------------------------------------
# solve() helpers — all local-import Grounding/Answers/Dialler/Values
# ---------------------------------------------------------------------------

def _has_content(problem: Problem) -> bool:
    return bool(problem._background or problem._examples or problem._mode_hs or problem._mode_bs)


def _run_solve_loop(problem: Problem, builder) -> None:
    iter_ = 0
    generalisations: set = set()
    while not builder.is_meaningful() and iter_ <= problem._config.iterations:
        _run_iteration(problem, iter_, builder, generalisations)
        iter_ += 1


def _run_iteration(problem: Problem, iter_: int, builder, generalisations: set) -> None:
    from xhail.core.dialler import Dialler
    from xhail.core.entities.answers import time_abduction
    from xhail.core.entities.values import Values
    if problem._config.debug:
        from xhail.core.utils import save_temp_problem
        save_temp_problem(problem, iter_, Path(f"{problem._config.name}_abd{iter_}.lp"))
    dialler = Dialler(problem._config, problem)
    _, outputs = time_abduction(iter_, dialler)
    values = Values()
    iit = 0
    for output in outputs:
        if builder.size() > 0 and problem._config.terminate:
            break
        iit, values = _process_output(problem, output, iter_, iit, builder, generalisations, values)


def _process_output(problem: Problem, output, iter_: int, iit: int, builder, generalisations: set, values) -> tuple:
    from xhail.core.entities.answers import time_deduction_problem
    grounding = time_deduction_problem(problem, output)
    if problem._config.debug:
        iit = _log_debug_grounding(problem, grounding, iter_, iit)
    gen_set = frozenset(grounding.get_generalisation())
    if gen_set not in generalisations:
        values = grounding.solve(values, builder)
        problem._refinements.add(grounding.as_bad_solution())
        generalisations.add(gen_set)
    problem._count = builder.size()
    return iit, values


def _log_debug_grounding(problem: Problem, grounding, iter_: int, iit: int) -> int:
    from xhail.core import logger
    from xhail.core.logger import SIGNATURE
    logger.message(f"*** Info  ({SIGNATURE}): found Delta: {' '.join(str(a) for a in grounding.get_delta())}")
    logger.message(f"*** Info  ({SIGNATURE}): found Kernel: {' '.join(str(c) for c in grounding.get_kernel())}")
    logger.message(f"*** Info  ({SIGNATURE}): found Generalisation: {' '.join(str(c) for c in grounding.get_generalisation())}")
    if grounding.needs_induction():
        from xhail.core.utils import save_temp_grounding
        save_temp_grounding(grounding, iter_, Path(f"{problem._config.name}_abd{iter_}_ind{iit}.lp"))
        return iit + 1
    return iit


def _print_summary(problem: Problem, builder) -> None:
    from xhail.core.logger import SIGNATURE
    if builder.size() > 0 and problem._config.terminate:
        print(f"*** Info  ({SIGNATURE}): search for hypotheses terminated after the first match")
    if not builder.is_meaningful():
        print(f"*** Info  ({SIGNATURE}): no meaningful answers, try more iterations (--iter,-i <num>)")


# ---------------------------------------------------------------------------
# Problem
# ---------------------------------------------------------------------------

class Problem:

    class Builder:
        def __init__(self, config: Config) -> None:
            if config is None:
                raise ValueError("config must not be None")
            self._config: Config = config
            self._background: dict[str, None] = {}
            self._displays: dict[Display, None] = {}
            self._domains: dict[str, None] = {}
            self._examples: dict[Example, None] = {}
            self._mode_bs: dict[ModeB, None] = {}
            self._mode_hs: dict[ModeH, None] = {}

        def add_background(self, statement: str | None) -> Problem.Builder:
            if statement is None:
                return self
            statement = statement.strip()
            if not _warn_keyword(self._config, statement) \
                    and not _add_stmt_to(self, statement) \
                    and not _add_mode_to(self, statement):
                _add_plain(self, statement)
            return self

        def add_display(self, display: Display | None) -> Problem.Builder:
            if display is not None:
                self._displays[display] = None
            return self

        def add_example(self, example: Example | None) -> Problem.Builder:
            if example is not None:
                self._examples[example] = None
            return self

        def add_mode_b(self, mode: ModeB | None) -> Problem.Builder:
            if mode is not None:
                self._mode_bs[mode] = None
            return self

        def add_mode_h(self, mode: ModeH | None) -> Problem.Builder:
            if mode is not None:
                self._mode_hs[mode] = None
            return self

        def remove_background(self, statement: str | None) -> Problem.Builder:
            if statement is None:
                return self
            statement = statement.strip()
            if not _warn_keyword(self._config, statement) \
                    and not _remove_stmt_from(self, statement) \
                    and not _remove_mode_from(self, statement):
                _remove_plain(self, statement)
            return self

        def remove_display(self, display: Display | None) -> Problem.Builder:
            if display is not None:
                self._displays.pop(display, None)
            return self

        def remove_example(self, example: Example | None) -> Problem.Builder:
            if example is not None:
                self._examples.pop(example, None)
            return self

        def remove_mode_b(self, mode: ModeB | None) -> Problem.Builder:
            if mode is not None:
                self._mode_bs.pop(mode, None)
            return self

        def remove_mode_h(self, mode: ModeH | None) -> Problem.Builder:
            if mode is not None:
                self._mode_hs.pop(mode, None)
            return self

        def parse_stream(self, stream) -> Problem.Builder:
            for stmt in Splitter().parse(stream):
                self.add_background(stmt)
            return self

        def parse_path(self, path: Path) -> Problem.Builder:
            try:
                with open(path, "rb") as f:
                    self.parse_stream(f)
            except OSError:
                from xhail.core import logger
                logger.error(f"cannot find file '{path.name}'")
            return self

        def build(self) -> Problem:
            lookup: dict[str, set[int]] = {}
            for d in self._displays:
                arities = lookup.setdefault(d.get_identifier(), set())
                arities.add(d.get_arity())
            return Problem(self, lookup)

        def clear(self) -> Problem.Builder:
            self._background.clear()
            self._displays.clear()
            self._domains.clear()
            self._examples.clear()
            self._mode_bs.clear()
            self._mode_hs.clear()
            return self

        def clear_displays(self) -> Problem.Builder:
            self._displays.clear()
            return self

        def clear_examples(self) -> Problem.Builder:
            self._examples.clear()
            return self

        def clear_mode_bs(self) -> Problem.Builder:
            self._mode_bs.clear()
            return self

        def clear_mode_hs(self) -> Problem.Builder:
            self._mode_hs.clear()
            return self

    def __init__(self, builder: Problem.Builder, lookup: dict[str, set[int]]) -> None:
        self._background: tuple[str, ...] = tuple(builder._background)
        self._config: Config = builder._config
        self._displays: tuple[Display, ...] = tuple(builder._displays)
        self._domains: tuple[str, ...] = tuple(builder._domains)
        self._examples: tuple[Example, ...] = tuple(builder._examples)
        self._lookup: dict[str, set[int]] = lookup
        self._mode_bs: tuple[ModeB, ...] = tuple(builder._mode_bs)
        self._mode_hs: tuple[ModeH, ...] = tuple(builder._mode_hs)
        self._refinements: set[str] = set()
        self._count: int = 0

    def get_background(self) -> tuple[str, ...]:
        return self._background

    def get_config(self) -> Config:
        return self._config

    def get_displays(self) -> tuple[Display, ...]:
        return self._displays

    def get_domains(self) -> tuple[str, ...]:
        return self._domains

    def get_examples(self) -> tuple[Example, ...]:
        return self._examples

    def get_mode_bs(self) -> tuple[ModeB, ...]:
        return self._mode_bs

    def get_mode_hs(self) -> tuple[ModeH, ...]:
        return self._mode_hs

    def get_refinements(self) -> set[str]:
        return self._refinements

    def has_background(self) -> bool:
        return bool(self._background)

    def has_displays(self) -> bool:
        return bool(self._displays)

    def has_domains(self) -> bool:
        return bool(self._domains)

    def has_examples(self) -> bool:
        return bool(self._examples)

    def has_modes(self) -> bool:
        return bool(self._mode_bs or self._mode_hs)

    def lookup(self, atom: Atom) -> bool:
        arities = self._lookup.get(atom.identifier)
        return arities is not None and atom.get_arity() in arities

    def get_filters(self) -> tuple[str, ...]:
        result: set[str] = {"#hide."}
        _filter_displays_examples(self, result)
        for mode in self._mode_hs:
            _filter_mode_h(mode, result)
        for mode in self._mode_bs:
            _filter_mode_b(mode, result)
        return tuple(sorted(result))

    def save(self, it: int, stream) -> bool:
        from xhail.core.utils import save_problem
        return save_problem(self, it, stream)

    def count(self) -> int:
        return self._count

    def solve(self):
        from xhail.core.entities.answers import Answers
        builder = Answers.Builder(self._config)
        if _has_content(self):
            _run_solve_loop(self, builder)
        _print_summary(self, builder)
        return builder.build()
