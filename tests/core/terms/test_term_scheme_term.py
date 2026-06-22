import pytest
from abc import ABC

from xhail.core.terms.scheme_term import SchemeTerm
from xhail.core.terms.term import Term


def test_term_is_abstract_base():
    assert issubclass(Term, ABC)


def test_term_subclass_needs_no_abstract_methods():
    class Concrete(Term):
        pass

    assert isinstance(Concrete(), Term)


def test_scheme_term_is_abstract():
    with pytest.raises(TypeError):
        SchemeTerm()  # type: ignore[abstract]


def test_scheme_term_subclass_without_generalises_cannot_be_instantiated():
    class Incomplete(SchemeTerm):
        pass

    with pytest.raises(TypeError):
        Incomplete()


def test_scheme_term_subclass_with_generalises_can_be_instantiated():
    class Concrete(SchemeTerm):
        def generalises(self, *args, **kwargs):
            return NotImplemented

    assert isinstance(Concrete(), SchemeTerm)
