import sys

import pytest

from xhail.core.entities.values import Values


# --- sentinel Values() ---


def test_values_default_str():
    assert str(Values()) == str(sys.maxsize)


def test_values_default_get_value():
    assert Values().get_value(0) == sys.maxsize


def test_values_default_eq_and_hash():
    assert Values() == Values()
    assert hash(Values()) == hash(Values())


def test_values_default_lt_real():
    assert Values("0") < Values()
    assert not (Values() < Values("0"))


# --- Values(source) construction ---


def test_values_str():
    assert str(Values("5 2 1")) == "5 2 1"


def test_values_strips_outer_whitespace():
    assert str(Values("  5 2 1  ")) == "5 2 1"


def test_values_empty_raises():
    with pytest.raises(ValueError):
        Values("")


def test_values_blank_raises():
    with pytest.raises(ValueError):
        Values("  ")


# --- get_value ---


def test_values_get_value():
    values = Values("5 2 1")
    assert values.get_value(0) == 5
    assert values.get_value(1) == 2
    assert values.get_value(2) == 1


def test_values_get_value_oob():
    with pytest.raises(IndexError):
        Values("5 2 1").get_value(3)


# --- __eq__ / __hash__ ---


def test_values_eq_same():
    assert Values("5 2 1") == Values("5 2 1")


def test_values_eq_diff():
    assert Values("5 2 1") != Values("5 2 2")


def test_values_hash_same():
    assert hash(Values("3")) == hash(Values("3"))


def test_values_not_eq_other_type():
    assert Values("1") != 1


# --- __lt__ ---


def test_values_lt_same_is_false():
    assert not (Values("5 2 1") < Values("5 2 1"))


def test_values_lt_lexicographic_true():
    assert Values("3 1") < Values("3 2")


def test_values_lt_lexicographic_false():
    assert not (Values("3 2") < Values("3 1"))


def test_values_lt_first_element():
    assert Values("1") < Values("2")
    assert not (Values("2") < Values("1"))


# --- matches ---


def test_values_matches_true():
    assert Values("5 2 1").matches("5 2 1")


def test_values_matches_false():
    assert not Values("5 2 1").matches("5 2 2")


def test_values_matches_strips():
    assert Values("5 2 1").matches("  5 2 1  ")


def test_values_matches_empty_raises():
    with pytest.raises(ValueError):
        Values("5 2 1").matches("")
