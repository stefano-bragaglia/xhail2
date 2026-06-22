"""Tests for xhail.application."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from xhail.application import (
    _build_problem,
    _handle_exception,
    _handle_timeout,
    _parse_args,
    _report_missing,
    _search_paths,
    _solve,
)


# ---------------------------------------------------------------------------
# _parse_args
# ---------------------------------------------------------------------------

def test_parse_args_defaults():
    cfg = _parse_args([])
    assert cfg.all is False
    assert cfg.blind is False
    assert cfg.debug is False


def test_parse_args_boolean_flags():
    cfg = _parse_args(["-a", "-b", "-d", "-f", "-m", "-o", "-p", "-s", "-t"])
    assert cfg.all is True
    assert cfg.blind is True
    assert cfg.debug is True


def test_parse_args_long_flags():
    cfg = _parse_args(["--all", "--blind", "--debug"])
    assert cfg.all is True
    assert cfg.blind is True
    assert cfg.debug is True


def test_parse_args_help_flag():
    cfg = _parse_args(["-h"])
    assert cfg.help_ is True


def test_parse_args_version_flag():
    cfg = _parse_args(["-v"])
    assert cfg.version is True


def test_parse_args_clasp_and_gringo():
    cfg = _parse_args(["-c", "/usr/bin/clasp", "-g", "/usr/bin/gringo"])
    assert cfg.clasp == Path("/usr/bin/clasp")
    assert cfg.gringo == Path("/usr/bin/gringo")


def test_parse_args_kill_and_iter():
    cfg = _parse_args(["-k", "30", "-i", "5"])
    assert cfg.kill == 30
    assert cfg.iterations == 5


def test_parse_args_invalid_source_calls_logger(tmp_path):
    missing = tmp_path / "nonexistent.pl"
    with patch("xhail.core.logger.error", side_effect=SystemExit(-1)):
        with pytest.raises(SystemExit):
            _parse_args([str(missing)])


# ---------------------------------------------------------------------------
# _report_missing
# ---------------------------------------------------------------------------

def _make_finder(gringo=None, clasp=None):
    f = MagicMock()
    f.get.side_effect = lambda name: gringo if name == "gringo" else clasp
    return f


def test_report_missing_gringo_only():
    finder = _make_finder(gringo=None, clasp=Path("/usr/bin/clasp"))
    with patch("xhail.core.logger.error", side_effect=SystemExit(-1)) as mock_err:
        with pytest.raises(SystemExit):
            _report_missing(finder)
    msg = mock_err.call_args[0][0]
    assert "gringo" in msg
    assert "clasp" not in msg


def test_report_missing_clasp_only():
    finder = _make_finder(gringo=Path("/usr/bin/gringo"), clasp=None)
    with patch("xhail.core.logger.error", side_effect=SystemExit(-1)) as mock_err:
        with pytest.raises(SystemExit):
            _report_missing(finder)
    msg = mock_err.call_args[0][0]
    assert "clasp" in msg
    assert "gringo" not in msg


def test_report_missing_both():
    finder = _make_finder(gringo=None, clasp=None)
    with patch("xhail.core.logger.error", side_effect=SystemExit(-1)) as mock_err:
        with pytest.raises(SystemExit):
            _report_missing(finder)
    msg = mock_err.call_args[0][0]
    assert "gringo" in msg
    assert "clasp" in msg


# ---------------------------------------------------------------------------
# _search_paths
# ---------------------------------------------------------------------------

def test_search_paths_returns_true_when_found():
    finder = MagicMock()
    finder.find.return_value = True
    finder.get.return_value = Path("/usr/bin/gringo")
    config = MagicMock()
    with patch("xhail.core.logger.message"):
        result = _search_paths(finder, config)
    assert result is True


def test_search_paths_tries_root_when_paths_fail():
    finder = MagicMock()
    finder.find.return_value = False
    finder.get.return_value = None
    config = MagicMock()
    with patch("xhail.core.logger.message"):
        _search_paths(finder, config)
    calls = finder.find.call_args_list
    assert any(c[0][1] is True for c in calls)


# ---------------------------------------------------------------------------
# _handle_timeout
# ---------------------------------------------------------------------------

def _make_config(output=False, kill=10):
    cfg = MagicMock()
    cfg.output = output
    cfg.kill = kill
    return cfg


def test_handle_timeout_logs_message():
    config = _make_config(output=False, kill=10)
    problem = MagicMock()
    with patch("xhail.core.logger.message") as mock_msg:
        _handle_timeout(config, problem, 10)
    assert mock_msg.called
    assert "10" in mock_msg.call_args[0][0]


def test_handle_timeout_no_output_skips_stats(capsys):
    config = _make_config(output=False, kill=5)
    problem = MagicMock()
    with patch("xhail.core.logger.message"):
        _handle_timeout(config, problem, 5)
    captured = capsys.readouterr()
    assert "interrupted" not in captured.out
    assert "interrupted" not in captured.err


def test_handle_timeout_with_output_prints_stats(capsys):
    config = _make_config(output=True, kill=5)
    problem = MagicMock()
    problem.count.return_value = 3
    with patch("xhail.core.logger.message"), \
         patch("xhail.core.dialler.calls", return_value=2), \
         patch("xhail.core.entities.answers.Answers.get_loading", return_value=0.1), \
         patch("xhail.core.entities.answers.Answers.get_abduction", return_value=0.2), \
         patch("xhail.core.entities.answers.Answers.get_deduction", return_value=0.3), \
         patch("xhail.core.entities.answers.Answers.get_induction", return_value=0.4):
        _handle_timeout(config, problem, 5)
    captured = capsys.readouterr()
    assert "interrupted" in captured.err


# ---------------------------------------------------------------------------
# _handle_exception
# ---------------------------------------------------------------------------

def test_handle_exception_calls_logger_error():
    try:
        raise RuntimeError("test error")
    except RuntimeError as e:
        with patch("xhail.core.logger.error", side_effect=SystemExit(-1)) as mock_err:
            with pytest.raises(SystemExit):
                _handle_exception(e)
    msg = mock_err.call_args[0][0]
    assert "test error" in msg


def test_handle_exception_includes_traceback():
    try:
        raise ValueError("bad value")
    except ValueError as e:
        with patch("xhail.core.logger.error", side_effect=SystemExit(-1)) as mock_err:
            with pytest.raises(SystemExit):
                _handle_exception(e)
    msg = mock_err.call_args[0][0]
    assert "unexpected runtime error" in msg


# ---------------------------------------------------------------------------
# _build_problem
# ---------------------------------------------------------------------------

def test_build_problem_from_sources(tmp_path):
    src = tmp_path / "test.pl"
    src.write_text("")
    config = MagicMock()
    config.has_sources.return_value = True
    config.sources = (src,)
    mock_problem = MagicMock()
    mock_builder = MagicMock()
    mock_builder.build.return_value = mock_problem
    with patch("xhail.core.entities.problem.Problem.Builder", return_value=mock_builder), \
         patch("xhail.core.logger.message"), \
         patch("xhail.core.entities.answers.loaded"):
        result = _build_problem(config)
    assert result is mock_problem
    mock_builder.parse_path.assert_called_once_with(src)


def test_build_problem_from_stdin():
    config = MagicMock()
    config.has_sources.return_value = False
    mock_problem = MagicMock()
    mock_builder = MagicMock()
    mock_builder.build.return_value = mock_problem
    mock_stdin = MagicMock()
    with patch("xhail.core.entities.problem.Problem.Builder", return_value=mock_builder), \
         patch("xhail.core.logger.message"), \
         patch("xhail.core.entities.answers.loaded"), \
         patch("sys.stdin") as mock_sys_stdin:
        mock_sys_stdin.buffer = mock_stdin
        result = _build_problem(config)
    assert result is mock_problem
    mock_builder.parse_stream.assert_called_once_with(mock_stdin)


# ---------------------------------------------------------------------------
# _solve
# ---------------------------------------------------------------------------

def test_solve_calls_stamp_on_success():
    config = MagicMock()
    config.kill = 0
    problem = MagicMock()
    mock_answers = MagicMock()
    problem.solve.return_value = mock_answers
    with patch("xhail.core.logger.stamp") as mock_stamp:
        _solve(config, problem)
    mock_stamp.assert_called_once_with(mock_answers)


def test_solve_timeout_calls_handle_timeout():
    config = MagicMock()
    config.kill = 1
    problem = MagicMock()
    problem.solve.side_effect = lambda: __import__("time").sleep(10)
    with patch("xhail.application._handle_timeout") as mock_timeout:
        _solve(config, problem)
    assert mock_timeout.called


def test_solve_exception_calls_handle_exception():
    config = MagicMock()
    config.kill = 0
    problem = MagicMock()
    problem.solve.side_effect = RuntimeError("solver exploded")
    with patch("xhail.application._handle_exception") as mock_exc:
        _solve(config, problem)
    assert mock_exc.called


# ---------------------------------------------------------------------------
# main integration (prettify path — avoids solver)
# ---------------------------------------------------------------------------

def test_main_help_exits(tmp_path):
    from xhail.application import main
    with patch("xhail.core.logger.help", side_effect=SystemExit(0)):
        with pytest.raises(SystemExit):
            main(["-h"])


def test_main_version_exits(tmp_path):
    from xhail.application import main
    with patch("xhail.core.logger.version", side_effect=SystemExit(0)):
        with pytest.raises(SystemExit):
            main(["-v"])


def test_main_prettify_calls_dump(tmp_path):
    src = tmp_path / "test.pl"
    src.write_text("")
    from xhail.application import main
    with patch("xhail.core.logger.header"), \
         patch("xhail.core.logger.message"), \
         patch("xhail.core.entities.answers.loaded"), \
         patch("xhail.core.utils.dump") as mock_dump:
        main(["-p", str(src)])
    assert mock_dump.called
