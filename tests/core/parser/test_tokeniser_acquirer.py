import io

from xhail.core.entities.values import Values
from xhail.core.parser.acquirer import Acquirer
from xhail.core.parser.tokeniser import Tokeniser


def _s(text: str) -> io.BytesIO:
    return io.BytesIO(text.encode())


# --- Tokeniser ---


def test_tokeniser_empty():
    assert Tokeniser(_s("")).next() is None


def test_tokeniser_eof_idempotent():
    tok = Tokeniser(_s(""))
    assert tok.next() is None
    assert tok.next() is None


def test_tokeniser_single_word():
    tok = Tokeniser(_s("foo"))
    assert tok.next() == "foo"
    assert tok.next() is None


def test_tokeniser_multiple_words():
    tok = Tokeniser(_s("foo bar baz"))
    assert tok.next() == "foo"
    assert tok.next() == "bar"
    assert tok.next() == "baz"


def test_tokeniser_newline_sep():
    tok = Tokeniser(_s("foo\nbar"))
    assert tok.next() == "foo"
    assert tok.next() == "bar"


def test_tokeniser_cr_sep():
    tok = Tokeniser(_s("foo\rbar"))
    assert tok.next() == "foo"
    assert tok.next() == "bar"


def test_tokeniser_leading_whitespace():
    assert Tokeniser(_s("   foo")).next() == "foo"


def test_tokeniser_trailing_whitespace():
    tok = Tokeniser(_s("foo   "))
    assert tok.next() == "foo"
    assert tok.next() is None


def test_tokeniser_clasp_keywords():
    tok = Tokeniser(_s("SATISFIABLE UNSATISFIABLE OPTIMUM FOUND"))
    assert tok.next() == "SATISFIABLE"
    assert tok.next() == "UNSATISFIABLE"
    assert tok.next() == "OPTIMUM"
    assert tok.next() == "FOUND"


def test_tokeniser_optimization_line():
    tok = Tokeniser(_s("Optimization: 5 2 1"))
    assert tok.next() == "Optimization:"
    assert tok.next() == "5"
    assert tok.next() == "2"
    assert tok.next() == "1"


# --- Acquirer ---


def test_acquirer_unknown():
    values, answers = Acquirer(_s("UNKNOWN")).parse()
    assert values == Values()
    assert answers == set()


def test_acquirer_unsatisfiable():
    values, answers = Acquirer(_s("UNSATISFIABLE")).parse()
    assert values == Values()
    assert answers == set()


def test_acquirer_satisfiable():
    values, answers = Acquirer(_s("foo bar SATISFIABLE")).parse()
    assert values == Values()
    assert frozenset({"foo", "bar"}) in answers


def test_acquirer_satisfiable_answer_count():
    _, answers = Acquirer(_s("foo SATISFIABLE")).parse()
    assert len(answers) == 1


def test_acquirer_optimization_values():
    values, _ = Acquirer(_s("foo Optimization: 5 2 OPTIMUM FOUND")).parse()
    assert values == Values("5 2")


def test_acquirer_optimization_answer():
    _, answers = Acquirer(_s("foo Optimization: 5 2 OPTIMUM FOUND")).parse()
    assert frozenset({"foo"}) in answers
    assert len(answers) == 1


def test_acquirer_two_answers_better_wins():
    stream = "foo Optimization: 5 bar Optimization: 3 OPTIMUM FOUND"
    values, answers = Acquirer(_s(stream)).parse()
    assert values == Values("3")
    assert frozenset({"bar"}) in answers


def test_acquirer_two_answers_worse_dropped():
    stream = "foo Optimization: 5 bar Optimization: 3 OPTIMUM FOUND"
    _, answers = Acquirer(_s(stream)).parse()
    assert frozenset({"foo"}) not in answers
    assert len(answers) == 1


def test_acquirer_equal_values_both_kept():
    stream = "foo Optimization: 5 bar Optimization: 5 OPTIMUM FOUND"
    values, answers = Acquirer(_s(stream)).parse()
    assert values == Values("5")
    assert len(answers) == 2


def test_acquirer_equal_values_content():
    stream = "foo Optimization: 5 bar Optimization: 5 OPTIMUM FOUND"
    _, answers = Acquirer(_s(stream)).parse()
    assert frozenset({"foo"}) in answers
    assert frozenset({"bar"}) in answers


def test_acquirer_empty_stream_returns_partial():
    values, answers = Acquirer(_s("")).parse()
    assert values == Values()
    assert answers == set()
