import pytest

from xhail.core.terms.number import Number
from xhail.core.terms.placemarker import Placemarker, Type
from xhail.core.terms.variable import Variable


# --- Variable ---


def test_variable_identifier():
    assert Variable("X").identifier == "X"


def test_variable_type_defaults_none():
    assert Variable("X").type is None


def test_variable_with_type():
    pm = Placemarker("t", Type.INPUT)
    assert Variable("X", pm).type is pm


def test_variable_str():
    assert str(Variable("Xyz")) == "Xyz"
    assert str(Variable("_")) == "_"


def test_variable_eq():
    assert Variable("X") == Variable("X")
    assert Variable("X") != Variable("Y")
    pm = Placemarker("t", Type.INPUT)
    assert Variable("X", pm) != Variable("X")


def test_variable_hash():
    assert hash(Variable("X")) == hash(Variable("X"))
    assert len({Variable("X"), Variable("X"), Variable("Y")}) == 2


def test_variable_immutable():
    with pytest.raises((AttributeError, TypeError)):
        Variable("X").identifier = "Y"  # type: ignore[misc]


def test_variable_invalid_lowercase():
    with pytest.raises(ValueError):
        Variable("x")


def test_variable_invalid_digit():
    with pytest.raises(ValueError):
        Variable("1X")


def test_variable_invalid_empty():
    with pytest.raises(ValueError):
        Variable("")


def test_variable_valid_underscore():
    assert Variable("_foo").identifier == "_foo"


def test_variable_valid_uppercase():
    assert Variable("ABC").identifier == "ABC"


# --- Type enum ---


def test_type_str():
    assert str(Type.CONSTANT) == "$"
    assert str(Type.INPUT) == "+"
    assert str(Type.OUTPUT) == "-"


def test_type_internal():
    assert Type.CONSTANT.internal == "internal_const_par"
    assert Type.INPUT.internal == "internal_input_par"
    assert Type.OUTPUT.internal == "internal_output_par"


# --- Placemarker ---


def test_placemarker_identifier():
    assert Placemarker("foo").identifier == "foo"


def test_placemarker_type_defaults_constant():
    assert Placemarker("foo").type == Type.CONSTANT


def test_placemarker_type_input():
    assert Placemarker("foo", Type.INPUT).type == Type.INPUT


def test_placemarker_str():
    assert str(Placemarker("foo")) == "$foo"
    assert str(Placemarker("foo", Type.INPUT)) == "+foo"
    assert str(Placemarker("foo", Type.OUTPUT)) == "-foo"


def test_placemarker_eq():
    assert Placemarker("foo") == Placemarker("foo")
    assert Placemarker("foo") != Placemarker("bar")
    assert Placemarker("foo", Type.INPUT) != Placemarker("foo", Type.OUTPUT)


def test_placemarker_hash():
    assert hash(Placemarker("foo")) == hash(Placemarker("foo"))
    assert len({Placemarker("foo"), Placemarker("foo", Type.INPUT)}) == 2


def test_placemarker_immutable():
    with pytest.raises((AttributeError, TypeError)):
        Placemarker("foo").identifier = "bar"  # type: ignore[misc]


def test_placemarker_invalid_uppercase():
    with pytest.raises(ValueError):
        Placemarker("Foo")


def test_placemarker_invalid_empty():
    with pytest.raises(ValueError):
        Placemarker("")


def test_placemarker_invalid_digit():
    with pytest.raises(ValueError):
        Placemarker("1foo")


# --- generalises(set) ---


def test_generalises_set_mints_v1():
    pm = Placemarker("t", Type.INPUT)
    variables: set[Variable] = set()
    result = pm.generalises(variables)
    assert str(result) == "V1"
    assert result in variables


def test_generalises_set_mints_sequentially():
    pm = Placemarker("t", Type.INPUT)
    variables: set[Variable] = set()
    pm.generalises(variables)
    result = pm.generalises(variables)
    assert str(result) == "V2"
    assert len(variables) == 2


def test_generalises_set_result_carries_type():
    pm = Placemarker("t", Type.OUTPUT)
    result = pm.generalises(set())
    assert result.type is pm  # type: ignore[union-attr]


# --- generalises(term, map) ---


def test_generalises_map_input_mints_v1():
    pm = Placemarker("t", Type.INPUT)
    n = Number(1)
    map_: dict = {}
    result = pm.generalises(n, map_)
    assert str(result) == "V1"
    assert map_[n] is result


def test_generalises_map_input_caches():
    pm = Placemarker("t", Type.INPUT)
    n = Number(1)
    map_: dict = {}
    r1 = pm.generalises(n, map_)
    r2 = pm.generalises(n, map_)
    assert r1 is r2


def test_generalises_map_output_mints():
    pm = Placemarker("t", Type.OUTPUT)
    n = Number(1)
    map_: dict = {}
    result = pm.generalises(n, map_)
    assert str(result) == "V1"
    assert map_[n] is result


def test_generalises_map_constant_passthrough():
    pm = Placemarker("t", Type.CONSTANT)
    n = Number(42)
    result = pm.generalises(n, {})
    assert result is n
