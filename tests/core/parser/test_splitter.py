import io

from xhail.core.parser.splitter import Splitter


def _parse(text: str) -> tuple[str, ...]:
    return Splitter().parse(io.BytesIO(text.encode()))


# --- basic ---


def test_empty():
    assert _parse("") == ()


def test_whitespace_only():
    assert _parse("   \n\t  ") == ()


def test_single_statement():
    assert _parse("foo.") == ("foo.",)


def test_statement_trailing_newline():
    assert _parse("foo.\n") == ("foo.",)


def test_eof_without_dot():
    assert _parse("foo") == ("foo",)


def test_two_statements():
    assert _parse("foo. bar.") == ("foo.", "bar.")


def test_statement_order():
    assert _parse("foo. bar. baz.") == ("foo.", "bar.", "baz.")


def test_deduplication():
    assert _parse("foo. foo.") == ("foo.",)


# --- whitespace collapsing ---


def test_space_collapsed_without_keyword():
    assert _parse("foo bar.") == ("foobar.",)


def test_space_after_not():
    assert _parse("not foo.") == ("not foo.",)


def test_space_after_example():
    assert _parse("#example foo.") == ("#example foo.",)


def test_space_after_modeb():
    assert _parse("#modeb foo.") == ("#modeb foo.",)


def test_space_after_modeh():
    assert _parse("#modeh foo.") == ("#modeh foo.",)


def test_space_after_display():
    assert _parse("#display foo/1.") == ("#display foo/1.",)


def test_space_after_hide():
    assert _parse("#hide foo.") == ("#hide foo.",)


# --- comments ---


def test_comment_only():
    assert _parse("% just a comment\n") == ()


def test_single_line_comment():
    assert _parse("foo. % comment\nbar.") == ("foo.", "bar.")


def test_comment_at_eof():
    assert _parse("foo. % comment") == ("foo.",)


def test_multi_line_comment():
    assert _parse("foo. %* multi *% bar.") == ("foo.", "bar.")


def test_multi_line_comment_spanning_lines():
    assert _parse("foo. %*\nmulti\nline\n*% bar.") == ("foo.", "bar.")


def test_multi_line_comment_double_star():
    assert _parse("foo. %** still comment *% bar.") == ("foo.", "bar.")


# --- strings ---


def test_quoted_string():
    assert _parse('foo("hello").') == ('foo("hello").',)


def test_quoted_string_with_escape():
    assert _parse('foo("he\\"llo").') == ('foo("he\\"llo").',)


def test_quoted_string_with_space():
    assert _parse('foo("hello world").') == ('foo("hello world").',)


# --- dot sequences ---


def test_dot_dot():
    assert _parse("1..3.") == ("1..3.",)
