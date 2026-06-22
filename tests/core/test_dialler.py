"""Tests for xhail.core.dialler."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import xhail.core.dialler as dialler_module
from xhail.core.dialler import (
    Dialler,
    _IGNORED_WARNINGS,
    _handle_errors,
    _handle_line,
    _log_command,
    _make_temp,
    _parse_target,
    _process_error,
    _read_clasp,
    _run_gringo,
    _write_source,
    calls,
)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_config(*, debug=False, mute=False, output=True, kill=0, gringo="/bin/gringo", clasp="/bin/clasp"):
    cfg = MagicMock()
    cfg.debug = debug
    cfg.mute = mute
    cfg.output = output
    cfg.kill = kill
    cfg.gringo = gringo
    cfg.clasp = clasp
    return cfg


def _make_solvable(save_return=True):
    s = MagicMock()
    s.save.return_value = save_return
    return s


@pytest.fixture(autouse=True)
def reset_calls():
    original = dialler_module._calls
    yield
    dialler_module._calls = original


# ---------------------------------------------------------------------------
# calls()
# ---------------------------------------------------------------------------

def test_calls_initial():
    dialler_module._calls = 0
    assert calls() == 0


def test_calls_returns_current():
    dialler_module._calls = 7
    assert calls() == 7


# ---------------------------------------------------------------------------
# _make_temp
# ---------------------------------------------------------------------------

def test_make_temp_creates_file():
    p = _make_temp()
    assert p.exists()
    p.unlink(missing_ok=True)


def test_make_temp_returns_path():
    p = _make_temp()
    assert isinstance(p, Path)
    p.unlink(missing_ok=True)


def test_make_temp_each_call_unique():
    p1 = _make_temp()
    p2 = _make_temp()
    assert p1 != p2
    p1.unlink(missing_ok=True)
    p2.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# _process_error
# ---------------------------------------------------------------------------

def test_process_error_output_true_is_noop():
    # output=True: no exception, no side effects
    _process_error("some error", output=True)


def test_process_error_output_false_calls_logger():
    with patch("xhail.core.logger.error", side_effect=SystemExit(-1)):
        with pytest.raises(SystemExit):
            _process_error("bad thing", output=False)


# ---------------------------------------------------------------------------
# _handle_line
# ---------------------------------------------------------------------------

def test_handle_line_accumulates_when_message_nonempty():
    result = _handle_line("extra detail", "ERROR started", mute=False)
    assert result == "ERROR started\n  extra detail"


def test_handle_line_starts_error():
    result = _handle_line("ERROR: something went wrong", "", mute=False)
    assert result == "something went wrong"


def test_handle_line_ignored_warning_bad_solution():
    result = _handle_line("% warning: bad_solution/0 is never defined", "", mute=False)
    assert result == ""


def test_handle_line_ignored_warning_number_abduced():
    result = _handle_line("% warning: number_abduced/2 is never defined", "", mute=False)
    assert result == ""


def test_handle_line_real_warning_calls_logger(capsys):
    with patch("xhail.core.logger.warning") as mock_warn:
        result = _handle_line("% warning: something unexpected", "", mute=True)
    assert result == ""
    mock_warn.assert_called_once_with(True, "something unexpected")


def test_handle_line_other_prints_to_stderr(capsys):
    result = _handle_line("just some gringo output", "", mute=False)
    assert result == ""
    captured = capsys.readouterr()
    assert "just some gringo output" in captured.err


def test_handle_line_empty_message_other_returns_empty():
    result = _handle_line("whatever", "", mute=False)
    assert result == ""


def test_ignored_warnings_set():
    assert "bad_solution/0 is never defined" in _IGNORED_WARNINGS
    assert "number_abduced/2 is never defined" in _IGNORED_WARNINGS


# ---------------------------------------------------------------------------
# _handle_errors
# ---------------------------------------------------------------------------

def test_handle_errors_empty_file(tmp_path):
    f = tmp_path / "err.txt"
    f.write_text("")
    _handle_errors(f, mute=False)  # no exception


def test_handle_errors_warning_filtered(tmp_path):
    f = tmp_path / "err.txt"
    f.write_text("% warning: bad_solution/0 is never defined\n")
    _handle_errors(f, mute=False)  # no exception, no logger call


def test_handle_errors_real_warning_forwarded(tmp_path):
    f = tmp_path / "err.txt"
    f.write_text("% warning: something unexpected\n")
    with patch("xhail.core.logger.warning") as mock_warn:
        _handle_errors(f, mute=False)
    mock_warn.assert_called_once_with(False, "something unexpected")


def test_handle_errors_error_line_calls_logger_error(tmp_path):
    f = tmp_path / "err.txt"
    f.write_text("ERROR: something bad happened\n")
    with patch("xhail.core.logger.error", side_effect=SystemExit(-1)) as mock_err:
        with pytest.raises(SystemExit):
            _handle_errors(f, mute=False)
    mock_err.assert_called_once_with("something bad happened")


def test_handle_errors_multiline_error_accumulated(tmp_path):
    f = tmp_path / "err.txt"
    f.write_text("ERROR: first line\nsecond line\nthird line\n")
    with patch("xhail.core.logger.error", side_effect=SystemExit(-1)) as mock_err:
        with pytest.raises(SystemExit):
            _handle_errors(f, mute=False)
    mock_err.assert_called_once_with("first line\n  second line\n  third line")


def test_handle_errors_other_line_to_stderr(tmp_path, capsys):
    f = tmp_path / "err.txt"
    f.write_text("some other output\n")
    _handle_errors(f, mute=False)
    captured = capsys.readouterr()
    assert "some other output" in captured.err


def test_handle_errors_blank_lines_skipped(tmp_path):
    # blank line in file → if line: is False → branch 86->84 covered
    f = tmp_path / "err.txt"
    f.write_text("\nsome output\n")
    _handle_errors(f, mute=False)


def test_handle_errors_oserror_path(tmp_path):
    missing = tmp_path / "nonexistent_errors_file.txt"
    with patch("xhail.core.logger.error", side_effect=SystemExit(-1)):
        with pytest.raises(SystemExit):
            _handle_errors(missing, mute=False)


# ---------------------------------------------------------------------------
# _write_source
# ---------------------------------------------------------------------------

def test_write_source_success(tmp_path):
    source = tmp_path / "source.tmp"
    source.write_text("")
    solvable = _make_solvable()
    result = _write_source(solvable, 0, source, output=True)
    assert result is True
    solvable.save.assert_called_once()
    args = solvable.save.call_args[0]
    assert args[0] == 0


def test_write_source_failure_output_true(tmp_path):
    source = tmp_path / "source.tmp"
    solvable = MagicMock()
    solvable.save.side_effect = OSError("disk full")
    result = _write_source(solvable, 0, source, output=True)
    assert result is False


def test_write_source_failure_output_false(tmp_path):
    source = tmp_path / "source.tmp"
    solvable = MagicMock()
    solvable.save.side_effect = OSError("disk full")
    with patch("xhail.core.logger.error", side_effect=SystemExit(-1)):
        with pytest.raises(SystemExit):
            _write_source(solvable, 0, source, output=False)


# ---------------------------------------------------------------------------
# _parse_target
# ---------------------------------------------------------------------------

def test_parse_target_empty_file_returns_result(tmp_path):
    target = tmp_path / "target.tmp"
    target.write_bytes(b"UNKNOWN\n")
    result = _parse_target(target, output=True)
    assert result is not None
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_parse_target_failure_output_true(tmp_path):
    target = tmp_path / "nonexistent.tmp"
    result = _parse_target(target, output=True)
    assert result is None


# ---------------------------------------------------------------------------
# Dialler.__init__
# ---------------------------------------------------------------------------

def test_dialler_init_none_config():
    with pytest.raises(ValueError, match="config"):
        Dialler(None, _make_solvable())


def test_dialler_init_none_solvable():
    with pytest.raises(ValueError, match="solvable"):
        Dialler(_make_config(), None)


def test_dialler_init_creates_temp_files():
    cfg = _make_config()
    sol = _make_solvable()
    d = Dialler(cfg, sol)
    assert d._source.exists()
    assert d._middle.exists()
    assert d._errors.exists()
    assert d._target.exists()


def test_dialler_init_gringo_cmd():
    cfg = _make_config(gringo="/usr/bin/gringo")
    sol = _make_solvable()
    d = Dialler(cfg, sol)
    assert d._gringo_cmd[0] == "/usr/bin/gringo"
    assert d._gringo_cmd[1] == str(d._source)


def test_dialler_init_clasp_cmd_no_values():
    cfg = _make_config(clasp="/usr/bin/clasp")
    sol = _make_solvable()
    d = Dialler(cfg, sol)
    assert d._clasp_cmd[0] == "/usr/bin/clasp"
    assert d._clasp_cmd[1] == str(d._middle)
    assert "--verbose=0" in d._clasp_cmd
    assert "--opt-mode=optN" in d._clasp_cmd


def test_dialler_init_clasp_cmd_no_opt_bound():
    cfg = _make_config(clasp="/usr/bin/clasp")
    sol = _make_solvable()
    d = Dialler(cfg, sol)
    assert len(d._clasp_cmd) == 4


def test_dialler_init_clasp_cmd_with_values():
    from xhail.core.entities.values import Values
    cfg = _make_config(clasp="/usr/bin/clasp")
    sol = _make_solvable()
    v = Values()
    d = Dialler(cfg, sol, values=v)
    assert any(a.startswith("--opt-bound=") for a in d._clasp_cmd)


def test_dialler_init_stores_flags():
    cfg = _make_config(debug=True, mute=True, output=False, kill=30)
    sol = _make_solvable()
    d = Dialler(cfg, sol)
    assert d._debug is True
    assert d._mute is True
    assert d._output is False
    assert d._kill == 30


# ---------------------------------------------------------------------------
# Dialler.execute
# ---------------------------------------------------------------------------

def test_execute_negative_iter_raises():
    cfg = _make_config()
    sol = _make_solvable()
    d = Dialler(cfg, sol)
    with pytest.raises(ValueError, match="iter_"):
        d.execute(-1)


def test_execute_increments_calls():
    cfg = _make_config()
    sol = _make_solvable()
    d = Dialler(cfg, sol)
    dialler_module._calls = 0
    with patch("xhail.core.dialler._write_source", return_value=False):
        d.execute(0)
    assert dialler_module._calls == 1


def test_execute_increments_calls_even_on_write_failure():
    cfg = _make_config()
    sol = _make_solvable()
    d = Dialler(cfg, sol)
    dialler_module._calls = 0
    with patch("xhail.core.dialler._write_source", return_value=False):
        result = d.execute(0)
    assert dialler_module._calls == 1
    assert result == (None, set())


def test_execute_write_failure_returns_fallback():
    cfg = _make_config()
    sol = _make_solvable()
    d = Dialler(cfg, sol)
    with patch("xhail.core.dialler._write_source", return_value=False):
        values, outputs = d.execute(0)
    assert values is None
    assert outputs == set()


def test_execute_gringo_failure_returns_fallback():
    cfg = _make_config()
    sol = _make_solvable()
    d = Dialler(cfg, sol)
    with patch("xhail.core.dialler._write_source", return_value=True), \
         patch("xhail.core.dialler._run_gringo", return_value=False):
        values, outputs = d.execute(0)
    assert values is None
    assert outputs == set()


def test_execute_clasp_failure_returns_fallback():
    cfg = _make_config()
    sol = _make_solvable()
    d = Dialler(cfg, sol)
    with patch("xhail.core.dialler._write_source", return_value=True), \
         patch("xhail.core.dialler._run_gringo", return_value=True), \
         patch("xhail.core.dialler._read_clasp", return_value=(None, set())):
        values, outputs = d.execute(0)
    assert values is None
    assert outputs == set()


def test_execute_happy_path_returns_acquirer_result():
    from xhail.core.entities.values import Values
    expected_values = Values()
    expected_outputs: set[frozenset[str]] = {frozenset({"a", "b"})}
    cfg = _make_config()
    sol = _make_solvable()
    d = Dialler(cfg, sol)
    with patch("xhail.core.dialler._write_source", return_value=True), \
         patch("xhail.core.dialler._run_gringo", return_value=True), \
         patch("xhail.core.dialler._read_clasp", return_value=(expected_values, expected_outputs)):
        values, outputs = d.execute(0)
    assert values is expected_values
    assert outputs is expected_outputs


# ---------------------------------------------------------------------------
# _log_command
# ---------------------------------------------------------------------------

def test_log_command_debug_false_no_output(capsys):
    _log_command(False, ["gringo", "source.lp"])
    assert capsys.readouterr().out == ""


def test_log_command_debug_true_prints_command(capsys):
    _log_command(True, ["gringo", "source.lp"])
    out = capsys.readouterr().out
    assert "gringo" in out
    assert "source.lp" in out


# ---------------------------------------------------------------------------
# _handle_errors OSError path
# ---------------------------------------------------------------------------

def test_handle_errors_oserror_calls_logger_error(tmp_path):
    missing = tmp_path / "nonexistent_errors.txt"
    with patch("xhail.core.logger.error", side_effect=SystemExit(-1)):
        with pytest.raises(SystemExit):
            _handle_errors(missing, mute=False)


# ---------------------------------------------------------------------------
# _run_gringo
# ---------------------------------------------------------------------------

def test_run_gringo_success(tmp_path):
    middle = tmp_path / "middle.tmp"
    errors = tmp_path / "errors.tmp"
    errors.write_text("")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = None
        result = _run_gringo(["echo", ""], middle, errors, debug=False, mute=False, output=True, kill=0)
    assert result is True


def test_run_gringo_oserror_returns_false(tmp_path):
    middle = tmp_path / "middle.tmp"
    errors = tmp_path / "errors.tmp"
    errors.write_text("")
    with patch("subprocess.run", side_effect=OSError("no such file")):
        result = _run_gringo(["no_such_binary"], middle, errors, debug=False, mute=False, output=True, kill=0)
    assert result is False


def test_run_gringo_timeout_returns_false(tmp_path):
    import subprocess
    middle = tmp_path / "middle.tmp"
    errors = tmp_path / "errors.tmp"
    errors.write_text("")
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=["gringo"], timeout=1)):
        result = _run_gringo(["gringo"], middle, errors, debug=False, mute=False, output=True, kill=1)
    assert result is False


# ---------------------------------------------------------------------------
# _read_clasp
# ---------------------------------------------------------------------------

def test_read_clasp_success(tmp_path):
    target = tmp_path / "target.tmp"
    target.write_bytes(b"UNKNOWN\n")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = None
        values, outputs = _read_clasp(["echo", ""], target, debug=False, output=True, kill=0)
    assert isinstance(outputs, (set, frozenset))


def test_read_clasp_oserror_returns_fallback(tmp_path):
    target = tmp_path / "target.tmp"
    with patch("subprocess.run", side_effect=OSError("no such file")):
        values, outputs = _read_clasp(["no_such_binary"], target, debug=False, output=True, kill=0)
    assert values is None
    assert outputs == set()


def test_read_clasp_timeout_returns_fallback(tmp_path):
    import subprocess
    target = tmp_path / "target.tmp"
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=["clasp"], timeout=1)):
        values, outputs = _read_clasp(["clasp"], target, debug=False, output=True, kill=1)
    assert values is None
    assert outputs == set()


# ---------------------------------------------------------------------------
# Dialler.__init__ OSError path (covers lines 157-159)
# ---------------------------------------------------------------------------

def test_dialler_init_make_temp_oserror():
    with patch("xhail.core.dialler._make_temp", side_effect=OSError("disk full")), \
         patch("xhail.core.logger.error", side_effect=SystemExit(-1)):
        with pytest.raises(SystemExit):
            Dialler(_make_config(), _make_solvable())
