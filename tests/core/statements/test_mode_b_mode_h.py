import sys

import pytest

from xhail.core.statements.mode_b import ModeB
from xhail.core.statements.mode_h import ModeH
from xhail.core.terms.placemarker import Placemarker, Type
from xhail.core.terms.scheme import Scheme


def _scheme(name: str = "foo") -> Scheme:
    return Scheme(name)


def _scheme_with_pm() -> Scheme:
    return Scheme("foo", (Placemarker("t", Type.INPUT),))


# --- ModeB ---


def test_mode_b_str_default():
    assert str(ModeB(_scheme())) == "#modeb foo."


def test_mode_b_str_negated():
    assert str(ModeB(_scheme(), negated=True)) == "#modeb not foo."


def test_mode_b_str_upper():
    assert str(ModeB(_scheme(), upper=3)) == "#modeb foo :3."


def test_mode_b_str_weight():
    assert str(ModeB(_scheme(), weight=2)) == "#modeb foo =2."


def test_mode_b_str_priority():
    assert str(ModeB(_scheme(), priority=2)) == "#modeb foo @2."


def test_mode_b_str_full():
    mb = ModeB(_scheme(), negated=True, upper=5, weight=3, priority=2)
    assert str(mb) == "#modeb not foo :5 =3 @2."


def test_mode_b_str_unlimited_upper_not_shown():
    assert f":{ sys.maxsize}" not in str(ModeB(_scheme()))


def test_mode_b_eq():
    assert ModeB(_scheme()) == ModeB(_scheme())
    assert ModeB(_scheme(), negated=True) != ModeB(_scheme())
    assert ModeB(_scheme(), upper=3) != ModeB(_scheme())
    assert ModeB(_scheme(), weight=2) != ModeB(_scheme())


def test_mode_b_eq_priority():
    assert ModeB(_scheme(), priority=2) != ModeB(_scheme())
    assert ModeB(_scheme("foo")) != ModeB(_scheme("bar"))


def test_mode_b_hash():
    assert hash(ModeB(_scheme())) == hash(ModeB(_scheme()))
    assert len({ModeB(_scheme()), ModeB(_scheme()), ModeB(_scheme("bar"))}) == 2


def test_mode_b_immutable():
    with pytest.raises((AttributeError, TypeError)):
        ModeB(_scheme()).negated = True  # type: ignore[misc]


def test_mode_b_accessors():
    mb = ModeB(_scheme(), negated=True, upper=4, weight=3, priority=2)
    assert mb.get_scheme() == _scheme()
    assert mb.get_upper() == 4
    assert mb.get_weight() == 3


def test_mode_b_accessors_priority_negated():
    mb = ModeB(_scheme(), negated=True, priority=5)
    assert mb.get_priority() == 5
    assert mb.is_negated() is True


def test_mode_b_not_negated():
    assert ModeB(_scheme()).is_negated() is False


# --- ModeH ---


def test_mode_h_str_default():
    assert str(ModeH(_scheme())) == "#modeh foo."


def test_mode_h_str_lower_nonzero():
    assert str(ModeH(_scheme(), lower=1)) == f"#modeh foo :1-{sys.maxsize}."


def test_mode_h_str_upper_set():
    assert str(ModeH(_scheme(), upper=3)) == "#modeh foo :0-3."


def test_mode_h_str_weight():
    assert str(ModeH(_scheme(), weight=2)) == "#modeh foo =2."


def test_mode_h_str_priority():
    assert str(ModeH(_scheme(), priority=2)) == "#modeh foo @2."


def test_mode_h_str_full():
    mh = ModeH(_scheme(), lower=1, upper=5, weight=3, priority=2)
    assert str(mh) == "#modeh foo :1-5 =3 @2."


def test_mode_h_str_unlimited_not_shown():
    result = str(ModeH(_scheme()))
    assert ":" not in result


def test_mode_h_eq_ignores_id():
    mh1 = ModeH(_scheme())
    mh2 = ModeH(_scheme())
    assert mh1 != mh2 or mh1 == mh2  # ids differ but equality holds
    assert mh1 == mh2


def test_mode_h_id_autoincrement():
    mh1 = ModeH(_scheme())
    mh2 = ModeH(_scheme())
    assert mh2.id == mh1.id + 1


def test_mode_h_hash_ignores_id():
    mh1 = ModeH(_scheme())
    mh2 = ModeH(_scheme())
    assert hash(mh1) == hash(mh2)


def test_mode_h_immutable():
    with pytest.raises((AttributeError, TypeError)):
        ModeH(_scheme()).lower = 1  # type: ignore[misc]


def test_mode_h_accessors():
    mh = ModeH(_scheme(), lower=1, upper=5, weight=3, priority=2)
    assert mh.get_scheme() == _scheme()
    assert mh.get_lower() == 1
    assert mh.get_upper() == 5


def test_mode_h_accessors_weight_priority():
    mh = ModeH(_scheme(), weight=3, priority=2)
    assert mh.get_weight() == 3
    assert mh.get_priority() == 2


def test_mode_h_as_clauses_no_placemarkers_length():
    lines = ModeH(_scheme()).as_clauses()
    assert len(lines) == 5


def test_mode_h_as_clauses_no_placemarkers_comment():
    mh = ModeH(_scheme())
    lines = mh.as_clauses()
    assert lines[0] == "% #modeh foo."


def test_mode_h_as_clauses_no_placemarkers_choice():
    mh = ModeH(_scheme())
    lines = mh.as_clauses()
    assert lines[1] == f"0 {{ abduced_foo }} {sys.maxsize}."


def test_mode_h_as_clauses_no_placemarkers_minimize_derive():
    mh = ModeH(_scheme())
    lines = mh.as_clauses()
    assert lines[2] == "#minimize[ abduced_foo =1 @1 ]."
    assert lines[3] == "foo:-abduced_foo."


def test_mode_h_as_clauses_no_placemarkers_count():
    mh = ModeH(_scheme())
    lines = mh.as_clauses()
    assert lines[4] == f"number_abduced({mh.id},V):-V:=#count{{ abduced_foo }}."


def test_mode_h_as_clauses_with_placemarker_comment():
    mh = ModeH(_scheme_with_pm())
    lines = mh.as_clauses()
    assert lines[0] == "% #modeh foo(+t)."


def test_mode_h_as_clauses_with_placemarker_choice():
    mh = ModeH(_scheme_with_pm())
    lines = mh.as_clauses()
    assert lines[1] == f"0 {{ abduced_foo(V1) :t(V1) }} {sys.maxsize}."


def test_mode_h_as_clauses_with_placemarker_minimize():
    mh = ModeH(_scheme_with_pm())
    lines = mh.as_clauses()
    assert lines[2] == "#minimize[ abduced_foo(V1) =1 @1 :t(V1) ]."


def test_mode_h_as_clauses_with_placemarker_derive():
    mh = ModeH(_scheme_with_pm())
    lines = mh.as_clauses()
    assert lines[3] == "foo(V1):-abduced_foo(V1),t(V1)."


def test_mode_h_as_clauses_with_placemarker_count():
    mh = ModeH(_scheme_with_pm())
    lines = mh.as_clauses()
    assert lines[4] == f"number_abduced({mh.id},V):-V:=#count{{ abduced_foo(V1) :t(V1) }}."


def test_mode_h_as_clauses_custom_lower_upper():
    mh = ModeH(_scheme(), lower=1, upper=3, weight=2, priority=3)
    lines = mh.as_clauses()
    assert lines[1] == "1 { abduced_foo } 3."
    assert lines[2] == "#minimize[ abduced_foo =2 @3 ]."
