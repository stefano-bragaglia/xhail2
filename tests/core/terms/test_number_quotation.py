import pytest

from xhail.core.terms.number import Number
from xhail.core.terms.quotation import Quotation


# --- Number ---


def test_number_value():
    assert Number(42).value == 42


def test_number_str():
    assert str(Number(42)) == "42"
    assert str(Number(-1)) == "-1"


def test_number_eq():
    assert Number(3) == Number(3)
    assert Number(3) != Number(4)


def test_number_hash():
    assert hash(Number(3)) == hash(Number(3))
    assert len({Number(3), Number(3), Number(4)}) == 2


def test_number_immutable():
    n = Number(1)
    with pytest.raises((AttributeError, TypeError)):
        n.value = 2  # type: ignore[misc]


def test_number_generalises_set_returns_self():
    n = Number(7)
    assert n.generalises(set()) is n


def test_number_generalises_term_map_matching():
    n = Number(7)
    assert n.generalises(Number(7), {}) is n


def test_number_generalises_term_map_mismatch():
    assert Number(7).generalises(Number(8), {}) is None


def test_number_generalises_term_map_wrong_type():
    from xhail.core.terms.quotation import Quotation
    assert Number(7).generalises(Quotation('"x"'), {}) is None


# --- Quotation ---


def test_quotation_content():
    assert Quotation('"hello"').content == '"hello"'


def test_quotation_str():
    assert str(Quotation('"hello"')) == '"hello"'


def test_quotation_eq():
    assert Quotation('"a"') == Quotation('"a"')
    assert Quotation('"a"') != Quotation('"b"')


def test_quotation_hash():
    assert hash(Quotation('"a"')) == hash(Quotation('"a"'))
    assert len({Quotation('"a"'), Quotation('"a"'), Quotation('"b"')}) == 2


def test_quotation_immutable():
    q = Quotation('"x"')
    with pytest.raises((AttributeError, TypeError)):
        q.content = '"y"'  # type: ignore[misc]


def test_quotation_invalid_no_quotes():
    with pytest.raises(ValueError):
        Quotation("hello")


def test_quotation_invalid_too_short():
    with pytest.raises(ValueError):
        Quotation('"')


def test_quotation_invalid_empty():
    with pytest.raises(ValueError):
        Quotation("")


def test_quotation_generalises_set_returns_self():
    q = Quotation('"hi"')
    assert q.generalises(set()) is q


def test_quotation_generalises_term_map_matching():
    q = Quotation('"hi"')
    assert q.generalises(Quotation('"hi"'), {}) is q


def test_quotation_generalises_term_map_mismatch():
    assert Quotation('"hi"').generalises(Quotation('"bye"'), {}) is None


def test_quotation_generalises_term_map_wrong_type():
    assert Quotation('"hi"').generalises(Number(1), {}) is None
