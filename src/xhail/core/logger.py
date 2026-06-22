"""Output functions for the xhail application."""
from __future__ import annotations

import sys

ANSI_BLACK = "[30m"
ANSI_BLUE = "[34m"
ANSI_CYAN = "[36m"
ANSI_GREEN = "[32m"
ANSI_PURPLE = "[35m"
ANSI_RED = "[31m"
ANSI_RESET = "[0m"
ANSI_WHITE = "[37m"
ANSI_YELLOW = "[33m"

SIGNATURE = "xhail"
VERSION = "0.5.1"

_memory: set[str] = set()


def clear() -> None:
    _memory.clear()


def error(message: str) -> None:
    print(f"*** ERROR ({SIGNATURE}): {message}", file=sys.stderr)
    print(f"*** Info  ({SIGNATURE}): try '-h' or '--help' for usage information")
    sys.exit(-1)


def warning(mute: bool, message: str) -> None:
    if not mute and message not in _memory:
        _memory.add(message)
        print(f"* Warning ({SIGNATURE}): {message}", file=sys.stderr)


def message(message: str | None) -> None:
    if message is not None:
        print(message)


def header(config) -> None:
    _color(config, ANSI_RESET)
    print(f"{SIGNATURE} {VERSION}")
    print()
    _color(config, ANSI_WHITE)


def help() -> None:  # noqa: A001
    print(f"{SIGNATURE} {VERSION}")
    print()
    print(f"Usage:     python -m {SIGNATURE}  [options]  [files]")
    print()
    print("Options:")
    print()
    print("  --all,-a            : Print all the best answers")
    print("  --blind,-b          : Remove colours from the program output")
    print("  --clasp,-c <path>   : Use given <path> as path for clasp 3")
    print("  --debug,-d          : Leave temporary files in ./temp")
    print("  --full,-f           : Show a more detailed output")
    print("  --gringo,-g <path>  : Use given <path> as path for gringo 3")
    print("  --help,-h           : Print this help and exit")
    print("  --iter,-i <num>     : Run <num> iterations for non-minimal answers")
    print("  --kill,-k <num>     : Stop the program after <num> seconds")
    print("  --mute,-m           : Suppress warning messages")
    print("  --prettify,-p       : Nicely format current problem")
    print("  --search,-s         : Search for clasp 3 and gringo 3")
    print("  --terminate,-t      : Stop searching hypotheses after first match")
    print("  --version,-v        : Print version information and exit")
    print()
    print(f"Example:   python -m {SIGNATURE}  -c /Library/Clasp/clasp  -g /Library/Gringo/gringo  example.pl")
    print()
    sys.exit(1)


def version() -> None:
    print()
    print(f"{SIGNATURE} {VERSION}")
    print()
    print("Copyright (c) Stefano Bragaglia")
    print("Copyright (c) Oliver Ray")
    print()
    print("GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>")
    print(f"'{SIGNATURE}' is free software: you are free to change and redistribute it.")
    print("There is NO WARRANTY, to the extent permitted by law.")
    print()
    sys.exit(1)


def found(config) -> None:
    print(f"Using '{config.gringo}'...")
    print(f"Using '{config.clasp}'...")
    print()
    print("Next time try to invoke this python application with the following parameters:")
    print(_build_command(config))
    print()


def stamp(answers) -> None:
    config = answers.config
    if config.output:
        _stamp_output(answers, config)
    else:
        _stamp_answers(answers, config)
        _stamp_stats(answers, config)


# --- private helpers ---

def _color(config, code: str) -> None:
    if not config.blind:
        print(code, end="")


def _section(config, label: str) -> None:
    _color(config, ANSI_RED)
    print(label)


def _sub_section(config, label: str, content: str) -> None:
    _color(config, ANSI_GREEN)
    print(f"  {label}:")
    _color(config, ANSI_RESET)
    print(f"    {content}" if content else "    -")


def _stat(config, value: str) -> None:
    _color(config, ANSI_CYAN)
    print(value)


def _build_command(config) -> str:
    cmd = f"  {SIGNATURE} -c {config.clasp} -g {config.gringo}"
    cmd += _build_flags_a(config)
    cmd += _build_flags_b(config)
    for source in config.sources:
        cmd += f" {source}"
    return cmd


def _build_flags_a(config) -> str:
    flags = ""
    if config.all:
        flags += " -a"
    if config.blind:
        flags += " -b"
    if config.debug:
        flags += " -d"
    return flags


def _build_flags_b(config) -> str:
    flags = ""
    if config.kill > 0:
        flags += f" -k {config.kill}"
    if config.mute:
        flags += " -m"
    return flags


def _stamp_output(answers, config) -> None:
    from xhail.core.dialler import calls as _calls
    from xhail.core.entities.answers import Answers as _Answers
    print("Problem,Answers,Calls,Loading,Abduction,Deduction,Induction,Wall")
    print(
        f"completed,{answers.size()},{_calls()},{_Answers.get_loading():.3f},"
        f"{_Answers.get_abduction():.3f},{_Answers.get_deduction():.3f},"
        f"{_Answers.get_induction():.3f},{_Answers.get_now():.3f}",
        file=sys.stderr,
    )


def _stamp_answers(answers, config) -> None:
    if answers.is_empty():
        return
    for id_, answer in enumerate(answers, start=1):
        if id_ > 1 and not config.all:
            break
        _stamp_answer(id_, answer, config)
    _stamp_remaining(answers, config)


def _stamp_answer(id_: int, answer, config) -> None:
    _section(config, f"Answer {id_}:")
    if config.full:
        _stamp_full_model(answer, config)
    _stamp_answer_required(answer, config)
    if config.full:
        _sub_section(config, "covered", _join_sp(answer.get_covered()) if answer.has_covered() else "-")
    print()


def _stamp_answer_required(answer, config) -> None:
    _sub_section(config, "hypothesis", _join_nl(answer.get_hypotheses()) if answer.has_hypotheses() else "-")
    _sub_section(config, "uncovered", _join_sp(answer.get_uncovered()) if answer.has_uncovered() else "-")


def _stamp_full_model(answer, config) -> None:
    if answer.has_displays():
        _sub_section(config, "model", _join_sp(answer.get_model()) if answer.has_model() else "-")
    _sub_section(config, "delta", _join_sp(answer.get_delta()) if answer.has_delta() else "-")
    _sub_section(config, "kernel", _join_nl(answer.get_kernel()) if answer.has_kernel() else "-")


def _stamp_remaining(answers, config) -> None:
    remaining = answers.size() - 1
    if config.all or remaining <= 0:
        return
    _color(config, ANSI_RED)
    print("NB: ", end="")
    _color(config, ANSI_RESET)
    print(f"{remaining} additional optimal answer/s omitted ", end="")
    _color(config, ANSI_WHITE)
    print("(use '-a' to see them all)\n")


def _stamp_stats(answers, config) -> None:
    from xhail.core.dialler import calls as _calls
    from xhail.core.entities.answers import Answers as _Answers
    shown = answers.size() if config.all else (0 if answers.is_empty() else 1)
    _stat(config, f"Answers     : {answers.count()}")
    _stat(config, f"  optimal   : {answers.size()}")
    _stat(config, f"  shown     : {shown}")
    _stat(config, f"Calls       : {_calls()}")
    _stat(config, f"Time        : {_Answers.get_now():.3f}s  (loading: {_Answers.get_loading():.3f}s  1st answer: {_Answers.get_first():.3f}s)")
    _stat(config, f"  abduction : {_Answers.get_abduction():.3f}s")
    _stat(config, f"  deduction : {_Answers.get_deduction():.3f}s")
    _stat(config, f"  induction : {_Answers.get_induction():.3f}s\n")


def _join_sp(items) -> str:
    return " ".join(str(x) for x in items)


def _join_nl(items) -> str:
    return "\n    ".join(str(x) for x in items)
