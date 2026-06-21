import pytest

from xhail.core.statements.display import Display
from xhail.core.statements.example import Example
from xhail.core.terms.atom import Atom
from xhail.core.terms.number import Number


# --- Display ---


def test_display_str():
    assert str(Display("foo")) == "#display foo/1."
    assert str(Display("foo", 0)) == "#display foo/0."
    assert str(Display("foo", 3)) == "#display foo/3."


def test_display_eq():
    assert Display("foo") == Display("foo")
    assert Display("foo", 2) == Display("foo", 2)
    assert Display("foo") != Display("bar")
    assert Display("foo", 1) != Display("foo", 2)


def test_display_hash():
    assert hash(Display("foo")) == hash(Display("foo"))
    assert len({Display("foo"), Display("foo"), Display("bar")}) == 2


def test_display_immutable():
    with pytest.raises((AttributeError, TypeError)):
        Display("foo").identifier = "bar"  # type: ignore[misc]


def test_display_invalid_identifier():
    with pytest.raises(ValueError):
        Display("Foo")
    with pytest.raises(ValueError):
        Display("")


def test_display_invalid_arity():
    with pytest.raises(ValueError):
        Display("foo", -1)


def test_display_lt_by_identifier():
    assert Display("a") < Display("b")
    assert not Display("b") < Display("a")


def test_display_lt_reversed_arity():
    assert Display("foo", 3) < Display("foo", 1)
    assert not Display("foo", 1) < Display("foo", 3)


def test_display_not_lt_equal():
    assert not Display("foo") < Display("foo")


def test_display_get_identifier_arity():
    assert Display("foo", 2).get_identifier() == "foo"
    assert Display("foo", 2).get_arity() == 2


def test_display_as_clauses_arity_zero():
    assert Display("foo", 0).as_clauses() == "display_fact(foo):-foo."


def test_display_as_clauses_arity_one():
    assert Display("foo", 1).as_clauses() == "display_fact(foo(V1)):-foo(V1)."


def test_display_as_clauses_arity_two():
    assert Display("foo", 2).as_clauses() == "display_fact(foo(V1,V2)):-foo(V1,V2)."


# --- Example ---


def test_example_str_default():
    assert str(Example(Atom("foo"))) == "#example foo."


def test_example_str_negated():
    assert str(Example(Atom("foo"), negated=True)) == "#example not foo."


def test_example_str_with_weight():
    assert str(Example(Atom("foo"), weight=3)) == "#example foo =3."


def test_example_str_weight_one_not_shown():
    # weight=1 explicitly set (defeasible) — still not printed since ==1
    assert str(Example(Atom("foo"), weight=1)) == "#example foo."


def test_example_str_with_priority():
    assert str(Example(Atom("foo"), priority=2)) == "#example foo @2."


def test_example_str_full():
    ex = Example(Atom("foo"), negated=True, weight=3, priority=2)
    assert str(ex) == "#example not foo =3 @2."


def test_example_eq():
    assert Example(Atom("foo")) == Example(Atom("foo"))
    assert Example(Atom("foo"), weight=None) != Example(Atom("foo"), weight=1)
    assert Example(Atom("foo"), negated=True) != Example(Atom("foo"))
    assert Example(Atom("foo"), priority=2) != Example(Atom("foo"))


def test_example_hash():
    assert hash(Example(Atom("foo"))) == hash(Example(Atom("foo")))
    assert len({Example(Atom("foo")), Example(Atom("foo")), Example(Atom("bar"))}) == 2


def test_example_immutable():
    with pytest.raises((AttributeError, TypeError)):
        Example(Atom("foo")).negated = True  # type: ignore[misc]


def test_example_defeasible_false():
    assert not Example(Atom("foo")).defeasible
    assert not Example(Atom("foo")).is_defeasible()


def test_example_defeasible_true():
    assert Example(Atom("foo"), weight=3).defeasible
    assert Example(Atom("foo"), weight=1).is_defeasible()


def test_example_get_atom():
    a = Atom("foo")
    assert Example(a).get_atom() is a


def test_example_get_priority():
    assert Example(Atom("foo"), priority=5).get_priority() == 5


def test_example_get_weight_default():
    assert Example(Atom("foo")).get_weight() == 1


def test_example_get_weight_explicit():
    assert Example(Atom("foo"), weight=7).get_weight() == 7


def test_example_is_negated():
    assert not Example(Atom("foo")).is_negated()
    assert Example(Atom("foo"), negated=True).is_negated()


def test_example_as_clauses_non_defeasible():
    lines = Example(Atom("foo")).as_clauses()
    assert lines[0] == "% #example foo."
    assert lines[1] == "#maximize[ foo =1 @1 ]."
    assert lines[2] == ":-not foo."


def test_example_as_clauses_non_defeasible_negated():
    lines = Example(Atom("foo"), negated=True).as_clauses()
    assert lines[0] == "% #example not foo."
    assert lines[1] == "#maximize[ not foo =1 @1 ]."
    assert lines[2] == ":-foo."


def test_example_as_clauses_defeasible_length():
    lines = Example(Atom("foo"), weight=3).as_clauses()
    assert len(lines) == 2


def test_example_as_clauses_defeasible_content():
    lines = Example(Atom("foo"), weight=3, priority=2).as_clauses()
    assert lines[0] == "% #example foo =3 @2."
    assert lines[1] == "#maximize[ foo =3 @2 ]."


def test_example_as_clauses_with_atom_terms():
    atom = Atom("foo", (Number(1),))
    lines = Example(atom).as_clauses()
    assert lines[1] == "#maximize[ foo(1) =1 @1 ]."
    assert lines[2] == ":-not foo(1)."


def test_example_defeasible_weight_one_no_constraint():
    # defeasible with weight=1: two lines only, no constraint
    lines = Example(Atom("foo"), weight=1).as_clauses()
    assert len(lines) == 2
    assert lines[1] == "#maximize[ foo =1 @1 ]."
