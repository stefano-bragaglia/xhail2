"""Tests for xhail.core.logger."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import xhail.core.logger as logger
from xhail.core.logger import (
    ANSI_CYAN,
    ANSI_GREEN,
    ANSI_RED,
    ANSI_RESET,
    ANSI_WHITE,
    SIGNATURE,
    VERSION,
)


def _cfg(**kwargs):
    defaults = dict(
        blind=False,
        all=False,
        full=False,
        output=False,
        debug=False,
        kill=0,
        mute=False,
        gringo="/usr/bin/gringo",
        clasp="/usr/bin/clasp",
        sources=[],
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class _FakeAnswers:
    def __init__(self, config, optimal=1, total=1, empty=False, answer_list=None):
        self.config = config
        self._optimal = optimal
        self._total = total
        self._empty = empty
        self._list = answer_list or []

    def size(self):
        return self._optimal

    def count(self):
        return self._total

    def is_empty(self):
        return self._empty

    def __iter__(self):
        return iter(self._list)


def _fake_answer(hypotheses=(), uncovered=(), covered=(), model=(), delta=(), kernel=()):
    return SimpleNamespace(
        has_displays=lambda: bool(model),
        has_model=lambda: bool(model),
        get_model=lambda: model,
        has_delta=lambda: bool(delta),
        get_delta=lambda: delta,
        has_kernel=lambda: bool(kernel),
        get_kernel=lambda: kernel,
        has_hypotheses=lambda: bool(hypotheses),
        get_hypotheses=lambda: hypotheses,
        has_uncovered=lambda: bool(uncovered),
        get_uncovered=lambda: uncovered,
        has_covered=lambda: bool(covered),
        get_covered=lambda: covered,
    )


def _fake_modules():
    dialler = MagicMock()
    dialler.calls.return_value = 3
    answers_mod = MagicMock()
    answers_mod.Answers.get_loading.return_value = 0.1
    answers_mod.Answers.get_abduction.return_value = 0.2
    answers_mod.Answers.get_deduction.return_value = 0.3
    answers_mod.Answers.get_induction.return_value = 0.4
    answers_mod.Answers.get_now.return_value = 1.0
    answers_mod.Answers.get_first.return_value = 0.5
    return {"xhail.core.dialler": dialler, "xhail.core.entities.answers": answers_mod}


@pytest.fixture(autouse=True)
def reset_memory():
    logger.clear()
    yield
    logger.clear()


# --- constants ---

def test_signature():
    assert SIGNATURE == "xhail"


def test_version():
    assert VERSION == "1.0.0"


def test_ansi_reset():
    assert ANSI_RESET == "[0m"


def test_ansi_red():
    assert ANSI_RED == "[31m"


def test_ansi_green():
    assert ANSI_GREEN == "[32m"


def test_ansi_cyan():
    assert ANSI_CYAN == "[36m"


def test_ansi_white():
    assert ANSI_WHITE == "[37m"


# --- error ---

def test_error_exits_minus_one():
    with pytest.raises(SystemExit) as exc:
        logger.error("boom")
    assert exc.value.code == -1


def test_error_message_to_stderr(capsys):
    with pytest.raises(SystemExit):
        logger.error("something bad")
    assert "something bad" in capsys.readouterr().err


def test_error_info_to_stdout(capsys):
    with pytest.raises(SystemExit):
        logger.error("oops")
    captured = capsys.readouterr()
    assert "Info" in captured.out
    assert "--help" in captured.out


def test_error_signature_in_output(capsys):
    with pytest.raises(SystemExit):
        logger.error("x")
    captured = capsys.readouterr()
    assert SIGNATURE in captured.err
    assert SIGNATURE in captured.out


# --- warning ---

def test_warning_emits_to_stderr(capsys):
    logger.warning(False, "watch out")
    assert "watch out" in capsys.readouterr().err


def test_warning_deduplication(capsys):
    logger.warning(False, "once")
    logger.warning(False, "once")
    assert capsys.readouterr().err.count("once") == 1


def test_warning_muted(capsys):
    logger.warning(True, "silenced")
    assert capsys.readouterr().err == ""


def test_warning_clear_resets_dedup(capsys):
    logger.warning(False, "msg")
    logger.clear()
    logger.warning(False, "msg")
    assert capsys.readouterr().err.count("msg") == 2


def test_warning_different_messages_both_appear(capsys):
    logger.warning(False, "alpha")
    logger.warning(False, "beta")
    err = capsys.readouterr().err
    assert "alpha" in err
    assert "beta" in err


def test_warning_signature_in_output(capsys):
    logger.warning(False, "x")
    assert SIGNATURE in capsys.readouterr().err


# --- message ---

def test_message_prints_to_stdout(capsys):
    logger.message("hello world")
    assert "hello world" in capsys.readouterr().out


def test_message_none_prints_nothing(capsys):
    logger.message(None)
    assert capsys.readouterr().out == ""


def test_message_empty_string_prints(capsys):
    logger.message("")
    assert capsys.readouterr().out == "\n"


# --- help ---

def test_help_exits_one():
    with pytest.raises(SystemExit) as exc:
        logger.help()
    assert exc.value.code == 1


def test_help_contains_signature(capsys):
    with pytest.raises(SystemExit):
        logger.help()
    assert SIGNATURE in capsys.readouterr().out


def test_help_contains_usage(capsys):
    with pytest.raises(SystemExit):
        logger.help()
    assert "Usage" in capsys.readouterr().out


def test_help_contains_example(capsys):
    with pytest.raises(SystemExit):
        logger.help()
    assert "Example" in capsys.readouterr().out


def test_help_contains_all_flags(capsys):
    with pytest.raises(SystemExit):
        logger.help()
    out = capsys.readouterr().out
    for flag in (
        "--all", "--blind", "--clasp", "--debug", "--full",
        "--gringo", "--help", "--iter", "--kill", "--mute",
        "--prettify", "--search", "--terminate", "--version",
    ):
        assert flag in out, f"missing flag {flag}"


def test_help_uses_python_not_java(capsys):
    with pytest.raises(SystemExit):
        logger.help()
    out = capsys.readouterr().out
    assert "python" in out
    assert "java" not in out


# --- version ---

def test_version_exits_one():
    with pytest.raises(SystemExit) as exc:
        logger.version()
    assert exc.value.code == 1


def test_version_contains_signature(capsys):
    with pytest.raises(SystemExit):
        logger.version()
    assert SIGNATURE in capsys.readouterr().out


def test_version_contains_copyright(capsys):
    with pytest.raises(SystemExit):
        logger.version()
    assert "Copyright" in capsys.readouterr().out


def test_version_contains_gpl(capsys):
    with pytest.raises(SystemExit):
        logger.version()
    assert "GPL" in capsys.readouterr().out


# --- header ---

def test_header_prints_title(capsys):
    logger.header(_cfg())
    assert f"{SIGNATURE} {VERSION}" in capsys.readouterr().out


def test_header_colour_mode_emits_ansi_reset(capsys):
    logger.header(_cfg(blind=False))
    assert ANSI_RESET in capsys.readouterr().out


def test_header_colour_mode_emits_ansi_white(capsys):
    logger.header(_cfg(blind=False))
    assert ANSI_WHITE in capsys.readouterr().out


def test_header_blind_no_ansi(capsys):
    logger.header(_cfg(blind=True))
    out = capsys.readouterr().out
    assert ANSI_RESET not in out
    assert ANSI_WHITE not in out


# --- found ---

def test_found_shows_gringo(capsys):
    logger.found(_cfg(gringo="/path/gringo", clasp="/path/clasp"))
    assert "/path/gringo" in capsys.readouterr().out


def test_found_shows_clasp(capsys):
    logger.found(_cfg(gringo="/path/gringo", clasp="/path/clasp"))
    assert "/path/clasp" in capsys.readouterr().out


def test_found_python_not_java(capsys):
    logger.found(_cfg(gringo="/g", clasp="/c"))
    out = capsys.readouterr().out
    assert "python" in out
    assert "java" not in out


def test_found_flag_all(capsys):
    logger.found(_cfg(gringo="/g", clasp="/c", all=True))
    assert " -a" in capsys.readouterr().out


def test_found_flag_blind(capsys):
    logger.found(_cfg(gringo="/g", clasp="/c", blind=True))
    assert " -b" in capsys.readouterr().out


def test_found_flag_debug(capsys):
    logger.found(_cfg(gringo="/g", clasp="/c", debug=True))
    assert " -d" in capsys.readouterr().out


def test_found_flag_kill(capsys):
    logger.found(_cfg(gringo="/g", clasp="/c", kill=30))
    assert " -k 30" in capsys.readouterr().out


def test_found_flag_mute(capsys):
    logger.found(_cfg(gringo="/g", clasp="/c", mute=True))
    assert " -m" in capsys.readouterr().out


def test_found_no_flags_when_defaults(capsys):
    logger.found(_cfg(gringo="/g", clasp="/c"))
    out = capsys.readouterr().out
    for flag in (" -a", " -b", " -d", " -k", " -m"):
        assert flag not in out, f"unexpected flag {flag}"


def test_found_sources_in_command(capsys):
    logger.found(_cfg(gringo="/g", clasp="/c", sources=["/f/a.pl", "/f/b.pl"]))
    out = capsys.readouterr().out
    assert "/f/a.pl" in out
    assert "/f/b.pl" in out


# --- stamp: CSV output mode ---

def test_stamp_csv_header_to_stdout(capsys):
    cfg = _cfg(output=True)
    answers = _FakeAnswers(cfg, optimal=2, total=5)
    with patch.dict("sys.modules", _fake_modules()):
        logger.stamp(answers)
    out = capsys.readouterr().out
    assert "Problem" in out
    assert "Answers" in out
    assert "Calls" in out


def test_stamp_csv_data_to_stderr(capsys):
    cfg = _cfg(output=True)
    answers = _FakeAnswers(cfg, optimal=2, total=5)
    with patch.dict("sys.modules", _fake_modules()):
        logger.stamp(answers)
    assert "completed" in capsys.readouterr().err


# --- stamp: normal mode ---

def test_stamp_empty_shows_stats_not_answers(capsys):
    cfg = _cfg()
    answers = _FakeAnswers(cfg, optimal=0, total=0, empty=True)
    with patch.dict("sys.modules", _fake_modules()):
        logger.stamp(answers)
    out = capsys.readouterr().out
    assert "Answers" in out
    assert "Answer 1:" not in out


def test_stamp_shows_answer_section(capsys):
    cfg = _cfg()
    answer = _fake_answer(hypotheses=("h :- b.",))
    answers = _FakeAnswers(cfg, optimal=1, total=1, answer_list=[answer])
    with patch.dict("sys.modules", _fake_modules()):
        logger.stamp(answers)
    out = capsys.readouterr().out
    assert "Answer 1:" in out
    assert "hypothesis" in out
    assert "h :- b." in out


def test_stamp_not_all_shows_only_first(capsys):
    cfg = _cfg(all=False)
    a1 = _fake_answer(hypotheses=("h1.",))
    a2 = _fake_answer(hypotheses=("h2.",))
    answers = _FakeAnswers(cfg, optimal=2, total=2, answer_list=[a1, a2])
    with patch.dict("sys.modules", _fake_modules()):
        logger.stamp(answers)
    out = capsys.readouterr().out
    assert "Answer 1:" in out
    assert "Answer 2:" not in out


def test_stamp_all_flag_shows_all(capsys):
    cfg = _cfg(all=True)
    a1 = _fake_answer(hypotheses=("h1.",))
    a2 = _fake_answer(hypotheses=("h2.",))
    answers = _FakeAnswers(cfg, optimal=2, total=2, answer_list=[a1, a2])
    with patch.dict("sys.modules", _fake_modules()):
        logger.stamp(answers)
    out = capsys.readouterr().out
    assert "Answer 1:" in out
    assert "Answer 2:" in out


def test_stamp_remaining_note_when_multiple_optimal(capsys):
    cfg = _cfg(all=False)
    answers = _FakeAnswers(cfg, optimal=3, total=3, answer_list=[_fake_answer(), _fake_answer(), _fake_answer()])
    with patch.dict("sys.modules", _fake_modules()):
        logger.stamp(answers)
    out = capsys.readouterr().out
    assert "NB:" in out
    assert "omitted" in out


def test_stamp_no_remaining_note_single_optimal(capsys):
    cfg = _cfg(all=False)
    answers = _FakeAnswers(cfg, optimal=1, total=1, answer_list=[_fake_answer()])
    with patch.dict("sys.modules", _fake_modules()):
        logger.stamp(answers)
    assert "NB:" not in capsys.readouterr().out


def test_stamp_no_remaining_note_with_all_flag(capsys):
    cfg = _cfg(all=True)
    answers = _FakeAnswers(cfg, optimal=3, total=3, answer_list=[_fake_answer(), _fake_answer(), _fake_answer()])
    with patch.dict("sys.modules", _fake_modules()):
        logger.stamp(answers)
    assert "NB:" not in capsys.readouterr().out


def test_stamp_full_shows_kernel(capsys):
    cfg = _cfg(full=True)
    from xhail.core.terms.atom import Atom
    answer = _fake_answer(kernel=(Atom("foo"),), delta=(), model=())
    answers = _FakeAnswers(cfg, optimal=1, total=1, answer_list=[answer])
    with patch.dict("sys.modules", _fake_modules()):
        logger.stamp(answers)
    out = capsys.readouterr().out
    assert "kernel" in out
    assert "foo" in out


def test_stamp_full_shows_delta(capsys):
    cfg = _cfg(full=True)
    from xhail.core.terms.atom import Atom
    answer = _fake_answer(delta=(Atom("bar"),), model=())
    answers = _FakeAnswers(cfg, optimal=1, total=1, answer_list=[answer])
    with patch.dict("sys.modules", _fake_modules()):
        logger.stamp(answers)
    out = capsys.readouterr().out
    assert "delta" in out
    assert "bar" in out


def test_stamp_stats_always_shown(capsys):
    cfg = _cfg()
    answers = _FakeAnswers(cfg, optimal=0, total=0, empty=True)
    with patch.dict("sys.modules", _fake_modules()):
        logger.stamp(answers)
    out = capsys.readouterr().out
    assert "Answers" in out
    assert "Calls" in out
    assert "Time" in out


def test_stamp_colour_section_has_ansi_red(capsys):
    cfg = _cfg(blind=False)
    answer = _fake_answer()
    answers = _FakeAnswers(cfg, optimal=1, total=1, answer_list=[answer])
    with patch.dict("sys.modules", _fake_modules()):
        logger.stamp(answers)
    assert ANSI_RED in capsys.readouterr().out


def test_stamp_colour_stats_has_ansi_cyan(capsys):
    cfg = _cfg(blind=False)
    answers = _FakeAnswers(cfg, optimal=0, total=0, empty=True)
    with patch.dict("sys.modules", _fake_modules()):
        logger.stamp(answers)
    assert ANSI_CYAN in capsys.readouterr().out


def test_stamp_blind_no_ansi(capsys):
    cfg = _cfg(blind=True)
    answer = _fake_answer()
    answers = _FakeAnswers(cfg, optimal=1, total=1, answer_list=[answer])
    with patch.dict("sys.modules", _fake_modules()):
        logger.stamp(answers)
    out = capsys.readouterr().out
    for code in (ANSI_RED, ANSI_GREEN, ANSI_CYAN, ANSI_WHITE, ANSI_RESET):
        assert code not in out


def test_stamp_uncovered_dash_when_empty(capsys):
    cfg = _cfg()
    answer = _fake_answer(hypotheses=(), uncovered=())
    answers = _FakeAnswers(cfg, optimal=1, total=1, answer_list=[answer])
    with patch.dict("sys.modules", _fake_modules()):
        logger.stamp(answers)
    out = capsys.readouterr().out
    assert "uncovered" in out
    assert "    -" in out
