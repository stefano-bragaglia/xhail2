import pytest

from xhail.core.terms.atom import Atom
from xhail.core.terms.clause import Clause
from xhail.core.terms.literal import Literal
from xhail.core.terms.number import Number
from xhail.core.terms.placemarker import Placemarker, Type
from xhail.core.terms.scheme import Scheme
from xhail.core.terms.variable import Variable


# --- Literal ---


def test_literal_str_not_negated():
    assert str(Literal(Atom("foo"))) == "foo"


def test_literal_str_negated():
    assert str(Literal(Atom("foo"), negated=True)) == "not foo"


def test_literal_str_with_terms():
    assert str(Literal(Atom("foo", (Number(1),)))) == "foo(1)"


def test_literal_eq():
    assert Literal(Atom("foo")) == Literal(Atom("foo"))
    assert Literal(Atom("foo"), negated=True) != Literal(Atom("foo"))
    assert Literal(Atom("foo"), level=1) != Literal(Atom("foo"))
    assert Literal(Atom("foo")) != Literal(Atom("bar"))


def test_literal_hash():
    assert hash(Literal(Atom("foo"))) == hash(Literal(Atom("foo")))
    assert len({Literal(Atom("foo")), Literal(Atom("foo")), Literal(Atom("bar"))}) == 2


def test_literal_immutable():
    with pytest.raises((AttributeError, TypeError)):
        Literal(Atom("foo")).negated = True  # type: ignore[misc]


def test_literal_invalid_level():
    with pytest.raises(ValueError):
        Literal(Atom("foo"), level=-1)


def test_literal_lt_by_atom():
    assert Literal(Atom("a")) < Literal(Atom("b"))
    assert not Literal(Atom("b")) < Literal(Atom("a"))


def test_literal_lt_negated_before_non_negated():
    a = Atom("foo")
    assert Literal(a, negated=True) < Literal(a, negated=False)
    assert not Literal(a, negated=False) < Literal(a, negated=True)


def test_literal_not_lt_equal():
    assert not Literal(Atom("foo")) < Literal(Atom("foo"))


def test_literal_get_atom():
    a = Atom("foo")
    assert Literal(a).get_atom() is a


def test_literal_get_level():
    assert Literal(Atom("foo"), level=3).get_level() == 3


def test_literal_is_negated():
    assert not Literal(Atom("foo")).is_negated()
    assert Literal(Atom("foo"), negated=True).is_negated()


def test_literal_get_priority_weight():
    a = Atom("foo", weight=2, priority=5)
    lit = Literal(a)
    assert lit.get_weight() == 2
    assert lit.get_priority() == 5


def test_literal_get_scheme():
    s = Scheme("bar")
    a = Atom("foo", scheme=s)
    assert Literal(a).get_scheme() is s


def test_literal_get_scheme_none():
    assert Literal(Atom("foo")).get_scheme() is None


def test_literal_has_variables_false():
    assert not Literal(Atom("foo")).has_variables()


def test_literal_has_variables_true():
    pm = Placemarker("t", Type.INPUT)
    v = Variable("X", pm)
    assert Literal(Atom("foo", (v,))).has_variables()


def test_literal_get_variables():
    pm = Placemarker("t", Type.INPUT)
    v = Variable("X", pm)
    assert Literal(Atom("foo", (v,))).get_variables() == (v,)


def test_literal_has_types():
    pm = Placemarker("t", Type.INPUT)
    v = Variable("X", pm)
    assert Literal(Atom("foo", (v,))).has_types()


def test_literal_get_types():
    pm = Placemarker("t", Type.INPUT)
    v = Variable("X", pm)
    assert Literal(Atom("foo", (v,))).get_types() == ("t(X)",)


# --- Clause ---


def test_clause_str_headless_empty():
    assert str(Clause()) == ":-."


def test_clause_str_headless_with_body():
    lit = Literal(Atom("foo"))
    assert str(Clause(body=(lit,))) == ":-foo."


def test_clause_str_fact():
    assert str(Clause(head=Atom("foo"))) == "foo."


def test_clause_str_rule():
    lit = Literal(Atom("bar"))
    assert str(Clause(head=Atom("foo"), body=(lit,))) == "foo:-bar."


def test_clause_str_rule_two_body_literals():
    l1 = Literal(Atom("bar"))
    l2 = Literal(Atom("baz"))
    assert str(Clause(head=Atom("foo"), body=(l1, l2))) == "foo:-bar,baz."


def test_clause_str_negated_literal():
    lit = Literal(Atom("bar"), negated=True)
    assert str(Clause(body=(lit,))) == ":-not bar."


def test_clause_eq():
    lit = Literal(Atom("bar"))
    assert Clause(Atom("foo"), (lit,)) == Clause(Atom("foo"), (lit,))
    assert Clause(Atom("foo")) != Clause(Atom("baz"))
    assert Clause(Atom("foo"), (lit,)) != Clause(Atom("foo"))


def test_clause_hash():
    lit = Literal(Atom("bar"))
    assert hash(Clause(Atom("foo"), (lit,))) == hash(Clause(Atom("foo"), (lit,)))


def test_clause_immutable():
    with pytest.raises((AttributeError, TypeError)):
        Clause(Atom("foo")).head = Atom("bar")  # type: ignore[misc]


def test_clause_deduplicates_body():
    lit = Literal(Atom("foo"))
    c = Clause(body=(lit, lit))
    assert c.body == (lit,)


def test_clause_deduplication_preserves_order():
    l1 = Literal(Atom("bar"))
    l2 = Literal(Atom("baz"))
    c = Clause(body=(l1, l2, l1))
    assert c.body == (l1, l2)


def test_clause_get_head():
    a = Atom("foo")
    assert Clause(head=a).get_head() is a


def test_clause_get_head_none():
    assert Clause().get_head() is None


def test_clause_get_size():
    l1 = Literal(Atom("a"))
    l2 = Literal(Atom("b"))
    assert Clause().get_size() == 0
    assert Clause(body=(l1, l2)).get_size() == 2


def test_clause_get_body_1based():
    l1 = Literal(Atom("a"))
    l2 = Literal(Atom("b"))
    c = Clause(body=(l1, l2))
    assert c.get_body(1) is l1
    assert c.get_body(2) is l2


def test_clause_get_body_out_of_range():
    with pytest.raises(IndexError):
        Clause().get_body(1)
    with pytest.raises(IndexError):
        Clause(body=(Literal(Atom("a")),)).get_body(0)


def test_clause_iter():
    l1 = Literal(Atom("a"))
    l2 = Literal(Atom("b"))
    assert list(Clause(body=(l1, l2))) == [l1, l2]


def test_clause_get_levels_empty():
    assert Clause().get_levels() == 0


def test_clause_get_levels():
    l1 = Literal(Atom("a"), level=2)
    l2 = Literal(Atom("b"), level=5)
    l3 = Literal(Atom("c"), level=1)
    assert Clause(body=(l1, l2, l3)).get_levels() == 5


# --- Clause.Builder ---


def test_clause_builder_builds_empty():
    c = Clause.Builder().build()
    assert c == Clause()


def test_clause_builder_set_head():
    a = Atom("foo")
    c = Clause.Builder().set_head(a).build()
    assert c.head is a


def test_clause_builder_add_literal():
    lit = Literal(Atom("bar"))
    c = Clause.Builder().add_literal(lit).build()
    assert c.body == (lit,)


def test_clause_builder_returns_self():
    b = Clause.Builder()
    lit = Literal(Atom("foo"))
    assert b.add_literal(lit) is b


def test_clause_builder_deduplicates():
    lit = Literal(Atom("foo"))
    c = Clause.Builder().add_literal(lit).add_literal(lit).build()
    assert c.body == (lit,)


def test_clause_builder_add_literals():
    l1 = Literal(Atom("a"))
    l2 = Literal(Atom("b"))
    c = Clause.Builder().add_literals([l1, l2]).build()
    assert c.body == (l1, l2)


def test_clause_builder_remove_literal():
    l1 = Literal(Atom("a"))
    l2 = Literal(Atom("b"))
    c = Clause.Builder().add_literal(l1).add_literal(l2).remove_literal(l1).build()
    assert c.body == (l2,)


def test_clause_builder_remove_literals():
    l1 = Literal(Atom("a"))
    l2 = Literal(Atom("b"))
    l3 = Literal(Atom("c"))
    c = Clause.Builder().add_literals([l1, l2, l3]).remove_literals([l1, l3]).build()
    assert c.body == (l2,)


def test_clause_builder_clear_body():
    lit = Literal(Atom("foo"))
    c = Clause.Builder().add_literal(lit).clear_body().build()
    assert c.body == ()
