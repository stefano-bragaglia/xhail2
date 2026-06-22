"""Part A tests for Problem and Problem.Builder — no solve() (needs Grounding/Answers/Dialler)."""
from __future__ import annotations

import io
from unittest.mock import MagicMock, patch

import pytest

from xhail.core.config import Config
from xhail.core.entities.problem import Problem
from xhail.core.statements.display import Display
from xhail.core.statements.example import Example
from xhail.core.statements.mode_b import ModeB
from xhail.core.statements.mode_h import ModeH
from xhail.core.terms.atom import Atom
from xhail.core.terms.placemarker import Placemarker, Type
from xhail.core.terms.scheme import Scheme


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def cfg() -> Config:
    return Config()


@pytest.fixture
def builder(cfg) -> Problem.Builder:
    return Problem.Builder(cfg)


# ---------------------------------------------------------------------------
# Builder construction
# ---------------------------------------------------------------------------

def test_builder_requires_config():
    with pytest.raises((ValueError, TypeError)):
        Problem.Builder(None)


def test_builder_builds_empty_problem(builder):
    p = builder.build()
    assert isinstance(p, Problem)


def test_empty_problem_no_background(builder):
    assert not builder.build().has_background()


def test_empty_problem_no_displays(builder):
    assert not builder.build().has_displays()


def test_empty_problem_no_domains(builder):
    assert not builder.build().has_domains()


def test_empty_problem_no_examples(builder):
    assert not builder.build().has_examples()


def test_empty_problem_no_modes(builder):
    assert not builder.build().has_modes()


# ---------------------------------------------------------------------------
# add_background — None / plain / domain
# ---------------------------------------------------------------------------

def test_add_background_none_is_ignored(builder):
    builder.add_background(None)
    p = builder.build()
    assert not p.has_background()


def test_add_background_whitespace_only_is_ignored(builder):
    # empty after strip → goes to background dict but as ""
    # Java strips and then routes; an empty string falls through to background.add("")
    # Not a real-world case, but must not crash.
    builder.add_background("   ")
    builder.build()  # must not crash


def test_add_background_plain_statement(builder):
    builder.add_background("bird(tweety).")
    p = builder.build()
    assert p.has_background()
    assert "bird(tweety)." in p.get_background()


def test_add_background_domain(builder):
    builder.add_background("#domain animal(X).")
    p = builder.build()
    assert p.has_domains()
    assert "#domain animal(X)." in p.get_domains()
    assert not p.has_background()


def test_add_background_domain_stored_verbatim(builder):
    stmt = "#domain foo(X)."
    builder.add_background(stmt)
    assert stmt in builder.build().get_domains()


# ---------------------------------------------------------------------------
# add_background — keyword routing (#compute/#hide/#show → warning)
# ---------------------------------------------------------------------------

def test_add_background_compute_not_stored(builder):
    builder.add_background("#compute { foo }.")
    p = builder.build()
    assert not p.has_background()
    assert not p.has_domains()


def test_add_background_hide_not_stored(builder):
    builder.add_background("#hide.")
    p = builder.build()
    assert not p.has_background()


def test_add_background_show_not_stored(builder):
    builder.add_background("#show foo/1.")
    p = builder.build()
    assert not p.has_background()


# ---------------------------------------------------------------------------
# add_background — #display routing
# ---------------------------------------------------------------------------

def test_add_background_display(builder):
    builder.add_background("#display foo/1.")
    p = builder.build()
    assert p.has_displays()
    assert Display("foo", 1) in p.get_displays()


def test_add_background_display_requires_trailing_dot(builder):
    # Without the dot it goes to background, not displays
    builder.add_background("#display foo/1")
    p = builder.build()
    assert not p.has_displays()
    assert p.has_background()


# ---------------------------------------------------------------------------
# add_background — #example routing
# ---------------------------------------------------------------------------

def test_add_background_example(builder):
    builder.add_background("#example foo.")
    p = builder.build()
    assert p.has_examples()
    assert Example(Atom("foo")) in p.get_examples()


def test_add_background_example_requires_trailing_dot(builder):
    builder.add_background("#example foo")
    p = builder.build()
    assert not p.has_examples()


# ---------------------------------------------------------------------------
# add_background — #modeb / #modeh routing
# ---------------------------------------------------------------------------

def test_add_background_modeb(builder):
    scheme = Scheme("bar")
    builder.add_background(f"#modeb {scheme}.")
    p = builder.build()
    assert p.has_modes()
    assert any(m.get_scheme() == scheme for m in p.get_mode_bs())


def test_add_background_modeh(builder):
    scheme = Scheme("baz")
    builder.add_background(f"#modeh {scheme}.")
    p = builder.build()
    assert p.has_modes()
    assert any(m.get_scheme() == scheme for m in p.get_mode_hs())


# ---------------------------------------------------------------------------
# Direct add/remove methods
# ---------------------------------------------------------------------------

def test_add_display_direct(builder):
    d = Display("foo", 2)
    builder.add_display(d)
    assert Display("foo", 2) in builder.build().get_displays()


def test_add_display_none_is_ignored(builder):
    builder.add_display(None)
    assert not builder.build().has_displays()


def test_add_example_direct(builder):
    e = Example(Atom("bird"))
    builder.add_example(e)
    assert e in builder.build().get_examples()


def test_add_example_none_is_ignored(builder):
    builder.add_example(None)
    assert not builder.build().has_examples()


def test_add_mode_b_direct(builder):
    m = ModeB(scheme=Scheme("body"))
    builder.add_mode_b(m)
    assert m in builder.build().get_mode_bs()


def test_add_mode_h_direct(builder):
    m = ModeH(scheme=Scheme("head"))
    builder.add_mode_h(m)
    assert m in builder.build().get_mode_hs()


def test_remove_display(builder):
    d = Display("foo", 1)
    builder.add_display(d)
    builder.remove_display(d)
    assert not builder.build().has_displays()


def test_remove_example(builder):
    e = Example(Atom("foo"))
    builder.add_example(e)
    builder.remove_example(e)
    assert not builder.build().has_examples()


def test_remove_mode_b(builder):
    m = ModeB(scheme=Scheme("bar"))
    builder.add_mode_b(m)
    builder.remove_mode_b(m)
    assert not builder.build().get_mode_bs()


def test_remove_mode_h(builder):
    m = ModeH(scheme=Scheme("baz"))
    builder.add_mode_h(m)
    builder.remove_mode_h(m)
    assert not builder.build().get_mode_hs()


# ---------------------------------------------------------------------------
# remove_background mirrors add_background
# ---------------------------------------------------------------------------

def test_remove_background_plain(builder):
    builder.add_background("bird(tweety).")
    builder.remove_background("bird(tweety).")
    assert not builder.build().has_background()


def test_remove_background_display(builder):
    builder.add_background("#display foo/1.")
    builder.remove_background("#display foo/1.")
    assert not builder.build().has_displays()


def test_remove_background_example(builder):
    builder.add_background("#example foo.")
    builder.remove_background("#example foo.")
    assert not builder.build().has_examples()


def test_remove_background_domain(builder):
    builder.add_background("#domain animal(X).")
    builder.remove_background("#domain animal(X).")
    assert not builder.build().has_domains()


def test_remove_background_none_is_ignored(builder):
    builder.add_background("bird(tweety).")
    builder.remove_background(None)
    assert builder.build().has_background()


# ---------------------------------------------------------------------------
# clear methods
# ---------------------------------------------------------------------------

def test_clear_all(builder):
    builder.add_background("bird(tweety).")
    builder.add_display(Display("foo", 1))
    builder.add_example(Example(Atom("foo")))
    builder.clear()
    p = builder.build()
    assert not p.has_background()
    assert not p.has_displays()
    assert not p.has_examples()


def test_clear_displays(builder):
    builder.add_display(Display("foo", 1))
    builder.clear_displays()
    assert not builder.build().has_displays()


def test_clear_examples(builder):
    builder.add_example(Example(Atom("foo")))
    builder.clear_examples()
    assert not builder.build().has_examples()


def test_clear_mode_bs(builder):
    builder.add_mode_b(ModeB(scheme=Scheme("bar")))
    builder.clear_mode_bs()
    assert not builder.build().get_mode_bs()


def test_clear_mode_hs(builder):
    builder.add_mode_h(ModeH(scheme=Scheme("baz")))
    builder.clear_mode_hs()
    assert not builder.build().get_mode_hs()


# ---------------------------------------------------------------------------
# Problem.lookup
# ---------------------------------------------------------------------------

def test_lookup_true_for_displayed_atom(builder):
    builder.add_display(Display("bird", 1))
    p = builder.build()
    assert p.lookup(Atom("bird", (Atom("tweety"),)))


def test_lookup_false_for_wrong_arity(builder):
    builder.add_display(Display("bird", 1))
    p = builder.build()
    assert not p.lookup(Atom("bird"))  # arity 0, display is arity 1


def test_lookup_false_for_unknown_identifier(builder):
    p = builder.build()
    assert not p.lookup(Atom("bird"))


def test_lookup_true_for_arity_zero(builder):
    builder.add_display(Display("fact", 0))
    p = builder.build()
    assert p.lookup(Atom("fact"))


# ---------------------------------------------------------------------------
# Problem.get_filters
# ---------------------------------------------------------------------------

def test_get_filters_always_has_hide(builder):
    p = builder.build()
    assert "#hide." in p.get_filters()


def test_get_filters_sorted(builder):
    builder.add_display(Display("zoo", 1))
    builder.add_display(Display("ant", 0))
    filters = builder.build().get_filters()
    assert filters == tuple(sorted(filters))


def test_get_filters_includes_display(builder):
    builder.add_display(Display("bird", 1))
    p = builder.build()
    assert "#show bird/1." in p.get_filters()


def test_get_filters_includes_example(builder):
    builder.add_example(Example(Atom("fly")))
    p = builder.build()
    assert "#show fly/0." in p.get_filters()


def test_get_filters_includes_modeh_scheme_and_abduced(builder):
    scheme = Scheme("head")
    builder.add_mode_h(ModeH(scheme=scheme))
    p = builder.build()
    filters = p.get_filters()
    assert "#show head/0." in filters
    assert "#show abduced_head/0." in filters


def test_get_filters_includes_modeh_placemarkers(builder):
    pm = Placemarker("x", Type.INPUT)
    scheme = Scheme("head", (pm,))
    builder.add_mode_h(ModeH(scheme=scheme))
    p = builder.build()
    assert "#show x/1." in p.get_filters()


def test_get_filters_includes_modeb_scheme(builder):
    scheme = Scheme("body")
    builder.add_mode_b(ModeB(scheme=scheme))
    p = builder.build()
    assert "#show body/0." in p.get_filters()


def test_get_filters_includes_modeb_placemarkers(builder):
    pm = Placemarker("y", Type.OUTPUT)
    scheme = Scheme("body", (pm,))
    builder.add_mode_b(ModeB(scheme=scheme))
    p = builder.build()
    assert "#show y/1." in p.get_filters()


# ---------------------------------------------------------------------------
# Problem.save
# ---------------------------------------------------------------------------

def test_save_returns_true(builder):
    builder.add_background("bird(tweety).")
    p = builder.build()
    stream = io.StringIO()
    assert p.save(0, stream) is True


def test_save_writes_hide_filter(builder):
    p = builder.build()
    stream = io.StringIO()
    p.save(0, stream)
    assert "#hide." in stream.getvalue()


def test_save_writes_background(builder):
    builder.add_background("bird(tweety).")
    p = builder.build()
    stream = io.StringIO()
    p.save(0, stream)
    assert "bird(tweety)." in stream.getvalue()


# ---------------------------------------------------------------------------
# Problem.count / get_refinements
# ---------------------------------------------------------------------------

def test_count_initial_zero(builder):
    p = builder.build()
    assert p.count() == 0


def test_get_refinements_initially_empty(builder):
    p = builder.build()
    assert p.get_refinements() == set()


# ---------------------------------------------------------------------------
# Problem.get_config
# ---------------------------------------------------------------------------

def test_get_config_returns_config(cfg, builder):
    p = builder.build()
    assert p.get_config() is cfg


# ---------------------------------------------------------------------------
# Builder.parse_stream
# ---------------------------------------------------------------------------

def test_parse_stream_plain_statement(builder):
    stream = io.BytesIO(b"bird(tweety).")
    builder.parse_stream(stream)
    p = builder.build()
    assert p.has_background()


def test_parse_stream_display(builder):
    stream = io.BytesIO(b"#display bird/1.")
    builder.parse_stream(stream)
    p = builder.build()
    assert p.has_displays()
    assert Display("bird", 1) in p.get_displays()


def test_parse_stream_multiple_statements(builder):
    src = b"bird(tweety). flies(tweety)."
    builder.parse_stream(io.BytesIO(src))
    p = builder.build()
    assert "bird(tweety)." in p.get_background()
    assert "flies(tweety)." in p.get_background()


# ---------------------------------------------------------------------------
# Deduplication (insertion-ordered sets)
# ---------------------------------------------------------------------------

def test_duplicate_background_stored_once(builder):
    builder.add_background("bird(tweety).")
    builder.add_background("bird(tweety).")
    p = builder.build()
    assert p.get_background().count("bird(tweety).") == 1


def test_duplicate_display_stored_once(builder):
    builder.add_display(Display("foo", 1))
    builder.add_display(Display("foo", 1))
    assert len(builder.build().get_displays()) == 1


# ---------------------------------------------------------------------------
# None-guard tests for add_mode_b / add_mode_h
# ---------------------------------------------------------------------------

def test_add_mode_b_none_is_ignored(builder):
    builder.add_mode_b(None)
    assert not builder.build().has_modes()


def test_add_mode_h_none_is_ignored(builder):
    builder.add_mode_h(None)
    assert not builder.build().has_modes()


# ---------------------------------------------------------------------------
# None-guard tests for remove_display/remove_example/remove_mode_b/remove_mode_h
# ---------------------------------------------------------------------------

def test_remove_display_none_is_ignored(builder):
    d = Display("foo", 1)
    builder.add_display(d)
    builder.remove_display(None)
    assert builder.build().has_displays()


def test_remove_example_none_is_ignored(builder):
    e = Example(Atom("bird"))
    builder.add_example(e)
    builder.remove_example(None)
    assert builder.build().has_examples()


def test_remove_mode_b_none_is_ignored(builder):
    m = ModeB(scheme=Scheme("bar"))
    builder.add_mode_b(m)
    builder.remove_mode_b(None)
    assert builder.build().get_mode_bs()


def test_remove_mode_h_none_is_ignored(builder):
    m = ModeH(scheme=Scheme("baz"))
    builder.add_mode_h(m)
    builder.remove_mode_h(None)
    assert builder.build().get_mode_hs()


# ---------------------------------------------------------------------------
# _try_add / _try_remove when parser returns None
# ---------------------------------------------------------------------------

def test_add_background_display_bad_content_not_stored(builder):
    # parse_display("") raises ParserError → returns None → display not stored
    builder.add_background("#display .")
    assert not builder.build().has_displays()


def test_remove_background_display_bad_content_no_crash(builder):
    # parse_display("") returns None → no-op, must not crash
    builder.remove_background("#display .")


# ---------------------------------------------------------------------------
# _has_content and _print_summary (module-level helpers)
# ---------------------------------------------------------------------------

def test_has_content_true_with_background(cfg):
    from xhail.core.entities.problem import _has_content
    pb = Problem.Builder(cfg)
    pb.add_background("bird(tweety).")
    assert _has_content(pb.build())


def test_has_content_false_when_empty(cfg):
    from xhail.core.entities.problem import _has_content
    assert not _has_content(Problem.Builder(cfg).build())


def test_print_summary_terminate_message(capsys):
    from xhail.core.entities.problem import _print_summary
    cfg_terminate = Config(terminate=True)
    problem = Problem.Builder(cfg_terminate).build()
    mock_builder = MagicMock()
    mock_builder.size.return_value = 1
    mock_builder.is_meaningful.return_value = True
    _print_summary(problem, mock_builder)
    assert "terminated" in capsys.readouterr().out


def test_print_summary_no_meaningful_message(cfg, capsys):
    from xhail.core.entities.problem import _print_summary
    problem = Problem.Builder(cfg).build()
    mock_builder = MagicMock()
    mock_builder.size.return_value = 0
    mock_builder.is_meaningful.return_value = False
    _print_summary(problem, mock_builder)
    assert "meaningful" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Builder.parse_path — OSError
# ---------------------------------------------------------------------------

def test_parse_path_oserror_calls_logger(builder, tmp_path):
    missing = tmp_path / "nonexistent.lp"
    with patch("xhail.core.logger.error", side_effect=SystemExit(-1)):
        with pytest.raises(SystemExit):
            builder.parse_path(missing)
