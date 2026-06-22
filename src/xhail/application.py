"""Application — CLI entry point for xhail²."""
from __future__ import annotations

import sys
from pathlib import Path

_PATHS: tuple[Path, ...] = (
    Path("/Library/Gringo/"), Path("/Library/Clasp/"),
    Path("/usr/bin/gringo/"), Path("/usr/bin/clasp/"),
    Path("/usr/bin/"), Path("/usr/local/gringo/"),
    Path("/usr/local/clasp/"), Path("/usr/local/"),
    Path("/opt/bin/"), Path("/opt/local/"), Path("/opt/clasp/"),
    Path("/opt/gringo/"), Path("/opt/local/gringo/"),
    Path("/opt/local/clasp/"), Path("C:\\Gringo\\"), Path("C:\\Clasp\\"),
)
_ROOT: Path = Path(Path(".").resolve().root)


def _parse_args(argv=None):
    import argparse
    from xhail.core.config import Config
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("-a", "--all", dest="all_flag", action="store_true", default=False)
    p.add_argument("-b", "--blind", action="store_true", default=False)
    p.add_argument("-c", "--clasp", type=Path, default=None)
    p.add_argument("-d", "--debug", action="store_true", default=False)
    p.add_argument("-f", "--full", action="store_true", default=False)
    p.add_argument("-g", "--gringo", type=Path, default=None)
    p.add_argument("-h", "--help", dest="help_", action="store_true", default=False)
    p.add_argument("-i", "--iter", dest="iterations", type=int, default=0)
    p.add_argument("-k", "--kill", type=int, default=0)
    p.add_argument("-m", "--mute", action="store_true", default=False)
    p.add_argument("-o", "--output", action="store_true", default=False)
    p.add_argument("-p", "--prettify", action="store_true", default=False)
    p.add_argument("-s", "--search", action="store_true", default=False)
    p.add_argument("-t", "--terminate", action="store_true", default=False)
    p.add_argument("-v", "--version", dest="version_flag", action="store_true", default=False)
    p.add_argument("sources", nargs="*", type=Path)
    ns = p.parse_args(argv)
    try:
        return Config(
            all=ns.all_flag,
            blind=ns.blind,
            clasp=ns.clasp,
            debug=ns.debug,
            full=ns.full,
            gringo=ns.gringo,
            help_=ns.help_,
            iterations=ns.iterations,
            kill=ns.kill,
            mute=ns.mute,
            output=ns.output,
            prettify=ns.prettify,
            search=ns.search,
            sources=tuple(ns.sources),
            terminate=ns.terminate,
            version=ns.version_flag,
        )
    except ValueError as e:
        from xhail.core import logger
        logger.error(str(e))


def _search_paths(finder, config) -> bool:
    from xhail.core import logger
    logger.message("Locating needed applications...")
    found = any(finder.find(p, False) for p in _PATHS)
    if not found:
        found = finder.find(_ROOT, True)
    config.gringo = finder.get("gringo")
    config.clasp = finder.get("clasp")
    return found


def _report_missing(finder) -> None:
    from xhail.core import logger
    from xhail.core.logger import SIGNATURE
    message = ""
    if finder.get("gringo") is None:
        message = f"'gringo v3.*' needed to run {SIGNATURE}"
    if finder.get("clasp") is None:
        if message:
            message += f"\n*** ERROR ({SIGNATURE}): 'clasp v3.*' needed to run {SIGNATURE}"
        else:
            message = f"'clasp v3.*' needed to run {SIGNATURE}"
    logger.error(message)


def _run_finder(config) -> None:
    from xhail.core.finder import Finder
    finder = Finder(" 3.", "gringo", "clasp")
    finder.test("gringo", config.gringo)
    finder.test("clasp", config.clasp)
    if not finder.is_found() and config.search:
        found = _search_paths(finder, config)
        if found:
            from xhail.core import logger
            logger.found(config)
    if not finder.is_found():
        _report_missing(finder)


def _build_problem(config):
    from xhail.core import logger
    from xhail.core.entities.answers import loaded
    from xhail.core.entities.problem import Problem
    builder = Problem.Builder(config)
    if config.has_sources():
        for path in config.sources:
            logger.message(f"Reading from '{path}'...")
            builder.parse_path(path)
    else:
        logger.message("Reading from 'stdin'...")
        builder.parse_stream(sys.stdin.buffer)
    problem = builder.build()
    loaded()
    return problem


def _handle_timeout(config, problem, kill) -> None:
    from xhail.core import logger
    from xhail.core.logger import SIGNATURE
    from xhail.core.dialler import calls as _calls
    from xhail.core.entities.answers import Answers
    logger.message(f"*** Info  ({SIGNATURE}): solving interrupted after {kill} second/s")
    if config.output:
        print("Problem,Answers,Calls,Loading,Abduction,Deduction,Induction,Wall")
        print(
            f"interrupted,{problem.count()},{_calls()},"
            f"{Answers.get_loading():.3f},{Answers.get_abduction():.3f},"
            f"{Answers.get_deduction():.3f},{Answers.get_induction():.3f},"
            f"{float(kill):.3f}",
            file=sys.stderr,
        )


def _handle_exception(e: Exception) -> None:
    import traceback
    from xhail.core import logger
    frames = "".join(f"\n    {line.strip()}" for line in traceback.format_tb(e.__traceback__))
    logger.error(f"unexpected runtime error:\n  {e}{frames}")


def _solve(config, problem) -> None:
    from concurrent.futures import CancelledError, ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(problem.solve)
        try:
            timeout = float(config.kill) if config.kill > 0 else None
            answers = future.result(timeout=timeout)
            from xhail.core import logger
            logger.stamp(answers)
        except CancelledError:
            from xhail.core import logger
            from xhail.core.logger import SIGNATURE
            logger.message(f"*** Info  ({SIGNATURE}): computation was cancelled")
        except TimeoutError:
            _handle_timeout(config, problem, config.kill)
        except Exception as e:
            _handle_exception(e)


def main(argv=None) -> None:
    from xhail.core.entities.answers import started as _answers_started
    _answers_started()
    config = _parse_args(argv)
    from xhail.core import logger
    if config.help_:
        logger.help()
    if config.version:
        logger.version()
    logger.header(config)
    if not config.prettify:
        _run_finder(config)
    problem = _build_problem(config)
    if config.prettify:
        print()
        from xhail.core.utils import dump
        dump(problem, sys.stderr)
    else:
        _solve(config, problem)
