import pytest

from xhail.core.terms.atom import Atom, Builder
from xhail.core.terms.number import Number
from xhail.core.terms.placemarker import CONSTANT_STRING, Placemarker, Type
from xhail.core.terms.quotation import Quotation
from xhail.core.terms.scheme import Scheme
from xhail.core.terms.variable import Variable


# --- Atom ---


def test_atom_str_no_terms():
    assert str(Atom("foo")) == "foo"


def test_atom_str_with_terms():
    assert str(Atom("foo", (Number(1), Number(2)))) == "foo(1,2)"


def test_atom_eq():
    assert Atom("foo") == Atom("foo")
    assert Atom("foo", (Number(1),)) == Atom("foo", (Number(1),))
    assert Atom("foo") != Atom("bar")
    assert Atom("foo", (Number(1),)) != Atom("foo", (Number(2),))


def test_atom_hash():
    assert hash(Atom("foo")) == hash(Atom("foo"))
    assert len({Atom("foo"), Atom("foo"), Atom("bar")}) == 2


def test_atom_immutable():
    with pytest.raises((AttributeError, TypeError)):
        Atom("foo").identifier = "bar"  # type: ignore[misc]


def test_atom_invalid_identifier():
    with pytest.raises(ValueError):
        Atom("Foo")
    with pytest.raises(ValueError):
        Atom("")
    with pytest.raises(ValueError):
        Atom("1foo")


def test_atom_get_arity():
    assert Atom("foo").get_arity() == 0
    assert Atom("foo", (Number(1), Number(2))).get_arity() == 2


def test_atom_get_term():
    a = Atom("foo", (Number(1), Number(2)))
    assert a.get_term(0) == Number(1)
    assert a.get_term(1) == Number(2)


def test_atom_get_term_out_of_bounds():
    with pytest.raises(IndexError):
        Atom("foo").get_term(0)
    with pytest.raises(IndexError):
        Atom("foo", (Number(1),)).get_term(-1)


def test_atom_iter():
    a = Atom("foo", (Number(1), Number(2)))
    assert list(a) == [Number(1), Number(2)]


def test_atom_lt_by_identifier():
    assert Atom("a") < Atom("b")
    assert not Atom("b") < Atom("a")


def test_atom_lt_reversed_arity():
    # higher arity sorts first (less-than)
    assert Atom("foo", (Number(1), Number(2))) < Atom("foo", (Number(1),))
    assert not Atom("foo", (Number(1),)) < Atom("foo", (Number(1), Number(2)))


def test_atom_lt_reversed_term_str():
    # higher str sorts first (less-than)
    assert Atom("foo", (Number(9),)) < Atom("foo", (Number(1),))


def test_atom_not_lt_equal():
    assert not Atom("foo") < Atom("foo")


def test_atom_get_variables_empty():
    assert Atom("foo").get_variables() == ()


def test_atom_get_variables_flat():
    pm = Placemarker("t", Type.INPUT)
    v = Variable("X", pm)
    assert Atom("foo", (v,)).get_variables() == (v,)


def test_atom_get_variables_nested():
    pm = Placemarker("t", Type.INPUT)
    v = Variable("X", pm)
    inner = Atom("bar", (v,))
    outer = Atom("foo", (inner,))
    assert outer.get_variables() == (v,)


def test_atom_get_variables_deduped():
    pm = Placemarker("t", Type.INPUT)
    v = Variable("X", pm)
    a = Atom("foo", (v, v))
    assert a.get_variables() == (v,)


def test_atom_has_variables():
    pm = Placemarker("t", Type.INPUT)
    v = Variable("X", pm)
    assert not Atom("foo").has_variables()
    assert Atom("foo", (v,)).has_variables()


def test_atom_get_types():
    pm = Placemarker("t", Type.INPUT)
    v = Variable("X", pm)
    assert Atom("foo", (v,)).get_types() == ("t(X)",)


def test_atom_is_placemarker_true():
    assert Atom(CONSTANT_STRING, (Number(1),)).is_placemarker()


def test_atom_is_placemarker_false():
    assert not Atom("foo").is_placemarker()
    assert not Atom(CONSTANT_STRING).is_placemarker()  # needs exactly 1 term


# --- Atom.Builder ---


def test_builder_from_str():
    b = Builder("foo")
    assert b.build() == Atom("foo")


def test_builder_from_atom():
    a = Atom("foo", (Number(1),), weight=2, priority=3)
    b = Builder(a)
    assert b.build() == a


def test_builder_add_term_returns_self():
    b = Builder("foo")
    assert b.add_term(Number(1)) is b


def test_builder_add_term_chains():
    a = Builder("foo").add_term(Number(1)).add_term(Number(2)).build()
    assert a == Atom("foo", (Number(1), Number(2)))


def test_builder_clear_terms():
    b = Builder("foo")
    b.add_term(Number(1))
    b.clear_terms()
    assert b.build() == Atom("foo")


def test_builder_set_scheme():
    s = Scheme("bar")
    b = Builder("foo").set_scheme(s)
    assert b.build().scheme is s


def test_builder_clone_independent():
    b = Builder("foo").add_term(Number(1))
    c = b.clone()
    c.add_term(Number(2))
    assert b.build() == Atom("foo", (Number(1),))
    assert c.build() == Atom("foo", (Number(1), Number(2)))


def test_builder_identity_equality():
    b1 = Builder("foo")
    b2 = Builder("foo")
    assert b1 != b2  # identity, not value


# --- Scheme ---


def test_scheme_str_simple():
    assert str(Scheme("foo")) == "foo"


def test_scheme_str_with_terms():
    assert str(Scheme("foo", (Number(1), Number(2)))) == "foo(1,2)"


def test_scheme_str_negated():
    assert str(Scheme("foo", negated=True)) == "not foo"
    assert str(Scheme("foo", (Number(1),), negated=True)) == "not foo(1)"


def test_scheme_eq():
    assert Scheme("foo") == Scheme("foo")
    assert Scheme("foo", (Number(1),)) == Scheme("foo", (Number(1),))
    assert Scheme("foo") != Scheme("bar")
    assert Scheme("foo") != Scheme("foo", negated=True)


def test_scheme_hash():
    assert hash(Scheme("foo")) == hash(Scheme("foo"))
    assert len({Scheme("foo"), Scheme("foo"), Scheme("bar")}) == 2


def test_scheme_immutable():
    with pytest.raises((AttributeError, TypeError)):
        Scheme("foo").identifier = "bar"  # type: ignore[misc]


def test_scheme_invalid_identifier():
    with pytest.raises(ValueError):
        Scheme("Foo")
    with pytest.raises(ValueError):
        Scheme("")


def test_scheme_get_arity():
    assert Scheme("foo").get_arity() == 0
    assert Scheme("foo", (Number(1), Number(2))).get_arity() == 2


def test_scheme_get_term():
    s = Scheme("foo", (Number(1), Number(2)))
    assert s.get_term(0) == Number(1)
    with pytest.raises(IndexError):
        s.get_term(5)


def test_scheme_is_negated():
    assert not Scheme("foo").is_negated()
    assert Scheme("foo", negated=True).is_negated()


def test_scheme_is_placemarker():
    from xhail.core.terms.placemarker import INPUT_STRING
    assert Scheme(INPUT_STRING, (Scheme("foo"),)).is_placemarker()
    assert not Scheme("foo").is_placemarker()


def test_scheme_iter():
    s = Scheme("foo", (Number(1), Number(2)))
    assert list(s) == [Number(1), Number(2)]


# --- Scheme.generalises ---


def test_scheme_generalises_set_no_terms():
    s = Scheme("foo")
    variables: set = set()
    result = s.generalises(variables)
    assert isinstance(result, Atom)
    assert result.identifier == "foo"
    assert result.terms == ()
    assert result.scheme is s


def test_scheme_generalises_set_with_number():
    s = Scheme("foo", (Number(3),))
    result = s.generalises(set())
    assert isinstance(result, Atom)
    assert result.terms == (Number(3),)


def test_scheme_generalises_set_with_placemarker():
    pm = Placemarker("t", Type.INPUT)
    s = Scheme("foo", (pm,))
    variables: set = set()
    result = s.generalises(variables)
    assert isinstance(result, Atom)
    assert len(result.terms) == 1
    assert isinstance(result.terms[0], Variable)
    assert len(variables) == 1


def test_scheme_generalises_map_match():
    pm = Placemarker("t", Type.INPUT)
    s = Scheme("foo", (pm,))
    atom = Atom("foo", (Number(1),))
    map_: dict = {}
    result = s.generalises(atom, map_)
    assert isinstance(result, Atom)
    assert isinstance(result.terms[0], Variable)
    assert map_[Number(1)] is result.terms[0]


def test_scheme_generalises_map_identifier_mismatch():
    s = Scheme("foo")
    assert s.generalises(Atom("bar"), {}) is None


def test_scheme_generalises_map_arity_mismatch():
    s = Scheme("foo", (Number(1),))
    assert s.generalises(Atom("foo"), {}) is None


def test_scheme_generalises_map_non_atom():
    assert Scheme("foo").generalises(Number(1), {}) is None


# --- Scheme.get_placemarkers / get_types / get_variables ---


def test_scheme_get_placemarkers_flat():
    pm = Placemarker("t", Type.INPUT)
    s = Scheme("foo", (pm, Number(1)))
    assert s.get_placemarkers() == (pm,)


def test_scheme_get_placemarkers_nested():
    pm1 = Placemarker("t", Type.INPUT)
    pm2 = Placemarker("u", Type.OUTPUT)
    inner = Scheme("bar", (pm2,))
    outer = Scheme("foo", (pm1, inner))
    assert outer.get_placemarkers() == (pm1, pm2)


def test_scheme_get_types():
    pm1 = Placemarker("t", Type.INPUT)
    pm2 = Placemarker("u", Type.OUTPUT)
    s = Scheme("foo", (pm1, pm2))
    assert s.get_types() == ("t(V1)", "u(V2)")


def test_scheme_get_variables():
    pm1 = Placemarker("t", Type.INPUT)
    pm2 = Placemarker("u", Type.OUTPUT)
    s = Scheme("foo", (pm1, pm2))
    assert s.get_variables() == ("V1", "V2")


# --- Scheme.matches ---


def test_scheme_matches_no_terms():
    assert Scheme("foo").matches(Atom("foo"))


def test_scheme_matches_with_placemarker():
    pm = Placemarker("t", Type.INPUT)
    s = Scheme("foo", (pm,))
    assert s.matches(Atom("foo", (Number(1),)))
    assert s.matches(Atom("foo", (Quotation('"hi"'),)))


def test_scheme_matches_number_exact():
    s = Scheme("foo", (Number(3),))
    assert s.matches(Atom("foo", (Number(3),)))
    assert not s.matches(Atom("foo", (Number(4),)))


def test_scheme_matches_quotation_exact():
    s = Scheme("foo", (Quotation('"hi"'),))
    assert s.matches(Atom("foo", (Quotation('"hi"'),)))
    assert not s.matches(Atom("foo", (Quotation('"bye"'),)))


def test_scheme_matches_identifier_mismatch():
    assert not Scheme("foo").matches(Atom("bar"))


def test_scheme_matches_arity_mismatch():
    assert not Scheme("foo", (Number(1),)).matches(Atom("foo"))


def test_scheme_matches_not_atom():
    assert not Scheme("foo").matches(Number(1))


def test_scheme_matches_nested():
    inner = Scheme("bar", (Placemarker("t", Type.INPUT),))
    outer = Scheme("foo", (inner,))
    assert outer.matches(Atom("foo", (Atom("bar", (Number(1),)),)))
    assert not outer.matches(Atom("foo", (Atom("baz", (Number(1),)),)))


# --- Placemarker.decode (now testable) ---


def test_placemarker_decode_input_outer():
    result = Placemarker("foo", Type.INPUT).decode()
    assert isinstance(result, Scheme)
    assert result.identifier == "internal_input_par"
    assert len(result.terms) == 1


def test_placemarker_decode_input_inner():
    inner = Placemarker("foo", Type.INPUT).decode().terms[0]
    assert isinstance(inner, Scheme)
    assert inner.identifier == "foo"


def test_placemarker_decode_constant():
    result = Placemarker("bar", Type.CONSTANT).decode()
    assert isinstance(result, Scheme)
    assert result.identifier == "internal_const_par"
    assert result.terms[0].identifier == "bar"
