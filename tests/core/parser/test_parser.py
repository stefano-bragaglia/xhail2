import sys

from xhail.core.parser.parser import (
    ParserError,
    Parser,
    parse_answer,
    parse_display,
    parse_example,
    parse_mode_b,
    parse_mode_h,
    parse_token,
)
from xhail.core.statements.display import Display
from xhail.core.statements.example import Example
from xhail.core.statements.mode_b import ModeB
from xhail.core.statements.mode_h import ModeH
from xhail.core.terms.atom import Atom
from xhail.core.terms.number import Number
from xhail.core.terms.placemarker import Placemarker, Type
from xhail.core.terms.quotation import Quotation
from xhail.core.terms.scheme import Scheme
from xhail.core.terms.variable import Variable


# --- ParserError ---


def test_parser_error_is_exception():
    exc = ParserError("oops")
    assert isinstance(exc, Exception)
    assert str(exc) == "oops"


# --- parse_token ---


def test_parse_token_simple():
    assert parse_token("foo") == Atom("foo")


def test_parse_token_with_number():
    assert parse_token("foo(1)") == Atom("foo", (Number(1),))


def test_parse_token_negative_number():
    assert parse_token("foo(-42)") == Atom("foo", (Number(-42),))


def test_parse_token_zero():
    assert parse_token("foo(0)") == Atom("foo", (Number(0),))


def test_parse_token_with_quotation():
    assert parse_token('foo("hello")') == Atom("foo", (Quotation('"hello"'),))


def test_parse_token_nested_atom():
    assert parse_token("foo(bar)") == Atom("foo", (Atom("bar"),))


def test_parse_token_multi_term():
    result = parse_token("foo(a,b,c)")
    assert result == Atom("foo", (Atom("a"), Atom("b"), Atom("c")))


def test_parse_token_with_leading_whitespace():
    assert parse_token("  foo  ") == Atom("foo")


def test_parse_token_compound_identifier():
    assert parse_token("foo_bar123") == Atom("foo_bar123")


def test_parse_token_invalid_uppercase():
    assert parse_token("Foo") is None


def test_parse_token_variable_in_ground():
    assert parse_token("foo(X)") is None


def test_parse_token_trailing_junk():
    assert parse_token("foo bar") is None


def test_parse_token_empty():
    assert parse_token("") is None


def test_parse_token_deeply_nested():
    result = parse_token("a(b(c))")
    assert result == Atom("a", (Atom("b", (Atom("c"),)),))


def test_parse_token_mixed_terms():
    result = parse_token('a(b,1,"x")')
    assert result == Atom("a", (Atom("b"), Number(1), Quotation('"x"')))


# --- parse_answer ---


def test_parse_answer_empty_string():
    assert parse_answer("") == set()


def test_parse_answer_whitespace_only():
    assert parse_answer("   ") == set()


def test_parse_answer_single_atom():
    assert parse_answer("foo") == {Atom("foo")}


def test_parse_answer_multiple_atoms():
    result = parse_answer("foo bar baz")
    assert result == {Atom("foo"), Atom("bar"), Atom("baz")}


def test_parse_answer_atoms_with_terms():
    result = parse_answer("foo(1) bar")
    assert Atom("foo", (Number(1),)) in result
    assert Atom("bar") in result


def test_parse_answer_stops_at_non_lower():
    assert parse_answer("123") is None


def test_parse_answer_stops_mid_with_junk():
    assert parse_answer("foo 1") is None


# --- parse_display ---


def test_parse_display_arity_one():
    assert parse_display("foo/1") == Display("foo", 1)


def test_parse_display_arity_zero():
    assert parse_display("foo/0") == Display("foo", 0)


def test_parse_display_arity_two():
    assert parse_display("foo/2") == Display("foo", 2)


def test_parse_display_invalid_uppercase():
    assert parse_display("Foo/1") is None


def test_parse_display_missing_slash():
    assert parse_display("foo1") is None


def test_parse_display_negative_arity():
    assert parse_display("foo/-1") is None


def test_parse_display_eof_after_slash():
    assert parse_display("foo/") is None


# --- parse_example ---


def test_parse_example_simple():
    assert parse_example("foo") == Example(Atom("foo"))


def test_parse_example_negated():
    assert parse_example("not foo") == Example(Atom("foo"), negated=True)


def test_parse_example_with_weight():
    assert parse_example("foo =3") == Example(Atom("foo"), weight=3)


def test_parse_example_with_priority():
    assert parse_example("foo @2") == Example(Atom("foo"), priority=2)


def test_parse_example_full():
    result = parse_example("not foo =3@2")
    assert result == Example(Atom("foo"), negated=True, weight=3, priority=2)


def test_parse_example_with_terms():
    result = parse_example("foo(1)")
    assert result == Example(Atom("foo", (Number(1),)))


def test_parse_example_defeasible_weight_one():
    result = parse_example("foo =1")
    assert result is not None
    assert result.weight == 1
    assert result.is_defeasible()


def test_parse_example_invalid():
    assert parse_example("Foo") is None


# --- parse_mode_b ---


def test_parse_mode_b_simple():
    result = parse_mode_b("foo")
    assert result == ModeB(Scheme("foo"))


def test_parse_mode_b_with_input_pm():
    result = parse_mode_b("foo(+t)")
    assert result == ModeB(Scheme("foo", (Placemarker("t", Type.INPUT),)))


def test_parse_mode_b_with_output_pm():
    result = parse_mode_b("foo(-t)")
    assert result == ModeB(Scheme("foo", (Placemarker("t", Type.OUTPUT),)))


def test_parse_mode_b_negated():
    result = parse_mode_b("not foo(+t)")
    expected = ModeB(Scheme("foo", (Placemarker("t", Type.INPUT),)), negated=True)
    assert result == expected


def test_parse_mode_b_upper():
    result = parse_mode_b("foo :3")
    assert result == ModeB(Scheme("foo"), upper=3)


def test_parse_mode_b_weight():
    result = parse_mode_b("foo =2")
    assert result == ModeB(Scheme("foo"), weight=2)


def test_parse_mode_b_priority():
    result = parse_mode_b("foo @5")
    assert result == ModeB(Scheme("foo"), priority=5)


def test_parse_mode_b_full():
    result = parse_mode_b("not foo :3=2@1")
    expected = ModeB(Scheme("foo"), negated=True, upper=3, weight=2, priority=1)
    assert result == expected


def test_parse_mode_b_invalid():
    assert parse_mode_b("Foo") is None


# --- parse_mode_h ---


def test_parse_mode_h_simple():
    result = parse_mode_h("foo")
    assert result == ModeH(Scheme("foo"))


def test_parse_mode_h_with_pm():
    result = parse_mode_h("foo(+t)")
    assert result == ModeH(Scheme("foo", (Placemarker("t", Type.INPUT),)))


def test_parse_mode_h_upper_only():
    result = parse_mode_h("foo :3")
    assert result == ModeH(Scheme("foo"), upper=3)


def test_parse_mode_h_lower_upper():
    result = parse_mode_h("foo :1-3")
    assert result == ModeH(Scheme("foo"), lower=1, upper=3)


def test_parse_mode_h_weight():
    result = parse_mode_h("foo =2")
    assert result == ModeH(Scheme("foo"), weight=2)


def test_parse_mode_h_priority():
    result = parse_mode_h("foo @3")
    assert result == ModeH(Scheme("foo"), priority=3)


def test_parse_mode_h_full():
    result = parse_mode_h("foo :1-5=2@3")
    expected = ModeH(Scheme("foo"), lower=1, upper=5, weight=2, priority=3)
    assert result == expected


def test_parse_mode_h_invalid():
    assert parse_mode_h("Foo") is None


# --- Parser internals ---


def test_parser_advance_and_skip():
    parser = Parser("  foo")
    assert parser._current == " "
    parser._skip()
    assert parser._current == "f"


def test_parser_collect_digits():
    parser = Parser("123abc")
    assert parser._collect_digits() == "123"
    assert parser._current == "a"


def test_parser_consume_minus_true():
    parser = Parser("-5")
    assert parser._consume_minus() is True
    assert parser._current == "5"


def test_parser_consume_minus_false():
    parser = Parser("5")
    assert parser._consume_minus() is False
    assert parser._current == "5"


def test_parser_is_ident_char():
    parser = Parser("")
    assert parser._is_ident_char("a")
    assert parser._is_ident_char("Z")
    assert parser._is_ident_char("3")
    assert parser._is_ident_char("_")


def test_parser_is_ident_char_false():
    parser = Parser("")
    assert not parser._is_ident_char(".")
    assert not parser._is_ident_char(" ")
    assert not parser._is_ident_char("+")


def test_parser_is_variable_start():
    parser = Parser("")
    assert parser._is_variable_start("A")
    assert parser._is_variable_start("_")
    assert not parser._is_variable_start("a")
    assert not parser._is_variable_start("1")


def test_parser_is_placemarker_start():
    parser = Parser("")
    assert parser._is_placemarker_start("+")
    assert parser._is_placemarker_start("-")
    assert parser._is_placemarker_start("$")
    assert not parser._is_placemarker_start("a")


def test_parser_parse_variable():
    parser = Parser("Xyz")
    result = parser._parse_variable()
    assert result == Variable("Xyz")


def test_parser_parse_quotation():
    parser = Parser('"hello"')
    result = parser._parse_quotation()
    assert result == Quotation('"hello"')


def test_parser_parse_number_positive():
    parser = Parser("42")
    assert parser._parse_number() == Number(42)


def test_parser_parse_number_negative():
    parser = Parser("-7")
    assert parser._parse_number() == Number(-7)


def test_parser_scheme_with_two_placemarkers():
    result = parse_mode_h("foo(+s,-t)")
    expected_scheme = Scheme("foo", (Placemarker("s", Type.INPUT), Placemarker("t", Type.OUTPUT)))
    assert result == ModeH(expected_scheme)


def test_parser_nested_scheme():
    result = parse_mode_b("foo(bar(+t))")
    inner = Scheme("bar", (Placemarker("t", Type.INPUT),))
    expected = ModeB(Scheme("foo", (inner,)))
    assert result == expected


def test_parse_mode_h_upper_only_default_lower():
    result = parse_mode_h("foo :3")
    assert result is not None
    assert result.get_lower() == 0
    assert result.get_upper() == 3


def test_parse_mode_b_default_upper():
    result = parse_mode_b("foo")
    assert result is not None
    assert result.get_upper() == sys.maxsize
