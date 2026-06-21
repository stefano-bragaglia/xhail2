from types import SimpleNamespace

from xhail.core.terms.atom import Atom
from xhail.core.terms.number import Number
from xhail.core.terms.placemarker import Placemarker, Type
from xhail.core.terms.quotation import Quotation
from xhail.core.terms.scheme import Scheme
from xhail.core.terms.scheme_term import SchemeTerm
from xhail.core.terms.variable import Variable


# --- subsumes ---


def test_subsumes_scheme_zero_arity():
    assert SchemeTerm.subsumes(Scheme("foo"), Atom("foo"), set())


def test_subsumes_scheme_identifier_mismatch():
    assert not SchemeTerm.subsumes(Scheme("foo"), Atom("bar"), set())


def test_subsumes_scheme_arity_mismatch():
    pm = Placemarker("t", Type.INPUT)
    assert not SchemeTerm.subsumes(Scheme("foo", (pm,)), Atom("foo"), set())


def test_subsumes_scheme_non_atom():
    assert not SchemeTerm.subsumes(Scheme("foo"), Number(1), set())


def test_subsumes_placemarker_via_fact():
    pm = Placemarker("t", Type.INPUT)
    fact = Atom("t", (Number(1),))
    assert SchemeTerm.subsumes(pm, Number(1), {fact})


def test_subsumes_placemarker_variable():
    pm = Placemarker("t", Type.INPUT)
    assert not SchemeTerm.subsumes(pm, Variable("X"), set())


def test_subsumes_placemarker_atom_identity():
    pm = Placemarker("t", Type.INPUT)
    # Atom with same identifier and arity 1 subsumes the placemarker
    assert SchemeTerm.subsumes(pm, Atom("t", (Number(1),)), set())


def test_subsumes_placemarker_atom_wrong_identifier():
    pm = Placemarker("t", Type.INPUT)
    assert not SchemeTerm.subsumes(pm, Atom("u", (Number(1),)), set())


def test_subsumes_placemarker_atom_wrong_arity():
    pm = Placemarker("t", Type.INPUT)
    assert not SchemeTerm.subsumes(pm, Atom("t"), set())


def test_subsumes_other_type():
    # Number is not Scheme or Placemarker
    assert not SchemeTerm.subsumes(Number(1), Number(1), set())


def test_subsumes_scheme_with_placemarker_via_type_fact():
    pm = Placemarker("t", Type.INPUT)
    scheme = Scheme("foo", (pm,))
    atom = Atom("foo", (Number(1),))
    type_fact = Atom("t", (Number(1),))
    assert SchemeTerm.subsumes(scheme, atom, {atom, type_fact})


def test_subsumes_scheme_with_placemarker_no_fact():
    pm = Placemarker("t", Type.INPUT)
    scheme = Scheme("foo", (pm,))
    atom = Atom("foo", (Number(1),))
    assert not SchemeTerm.subsumes(scheme, atom, {atom})


# --- find_substitutes ---


def test_find_substitutes_non_atom():
    assert SchemeTerm.find_substitutes(Scheme("foo"), Number(1)) == set()


def test_find_substitutes_identifier_mismatch():
    assert SchemeTerm.find_substitutes(Scheme("foo"), Atom("bar")) == set()


def test_find_substitutes_arity_mismatch():
    pm = Placemarker("t", Type.INPUT)
    assert SchemeTerm.find_substitutes(Scheme("foo", (pm,)), Atom("foo")) == set()


def test_find_substitutes_input_collected():
    pm = Placemarker("t", Type.INPUT)
    s = Scheme("foo", (pm,))
    assert SchemeTerm.find_substitutes(s, Atom("foo", (Number(1),))) == {Number(1)}


def test_find_substitutes_output_not_collected():
    pm = Placemarker("t", Type.OUTPUT)
    s = Scheme("foo", (pm,))
    assert SchemeTerm.find_substitutes(s, Atom("foo", (Number(1),))) == set()


def test_find_substitutes_constant_not_collected():
    pm = Placemarker("t", Type.CONSTANT)
    s = Scheme("foo", (pm,))
    assert SchemeTerm.find_substitutes(s, Atom("foo", (Number(1),))) == set()


def test_find_substitutes_nested():
    pm = Placemarker("t", Type.INPUT)
    inner = Scheme("bar", (pm,))
    outer = Scheme("foo", (inner,))
    candidate = Atom("foo", (Atom("bar", (Number(1),)),))
    assert SchemeTerm.find_substitutes(outer, candidate) == {Number(1)}


def test_find_substitutes_no_terms():
    assert SchemeTerm.find_substitutes(Scheme("foo"), Atom("foo")) == set()


# --- match_and_output ---


def test_match_and_output_empty():
    matched, outputs = SchemeTerm.match_and_output(Scheme("foo"), [], set())
    assert matched == set()
    assert outputs == set()


def test_match_and_output_identifier_mismatch_skipped():
    matched, outputs = SchemeTerm.match_and_output(Scheme("foo"), [Atom("bar")], set())
    assert matched == set()
    assert outputs == set()


def test_match_and_output_zero_arity_match():
    atom = Atom("foo")
    matched, outputs = SchemeTerm.match_and_output(Scheme("foo"), [atom], set())
    assert matched == {atom}
    assert outputs == set()


def test_match_and_output_output_term_collected():
    pm = Placemarker("t", Type.OUTPUT)
    scheme = Scheme("foo", (pm,))
    atom = Atom("foo", (Number(1),))
    matched, outputs = SchemeTerm.match_and_output(scheme, [atom], set())
    assert matched == {atom}
    assert outputs == {Number(1)}


def test_match_and_output_input_in_substitutes():
    pm = Placemarker("t", Type.INPUT)
    scheme = Scheme("foo", (pm,))
    atom = Atom("foo", (Number(1),))
    matched, outputs = SchemeTerm.match_and_output(scheme, [atom], {Number(1)})
    assert matched == {atom}
    assert outputs == set()


def test_match_and_output_input_not_in_substitutes():
    pm = Placemarker("t", Type.INPUT)
    scheme = Scheme("foo", (pm,))
    atom = Atom("foo", (Number(1),))
    matched, outputs = SchemeTerm.match_and_output(scheme, [atom], set())
    assert matched == set()
    assert outputs == set()


def test_match_and_output_number_match():
    scheme = Scheme("foo", (Number(3),))
    atom = Atom("foo", (Number(3),))
    matched, _ = SchemeTerm.match_and_output(scheme, [atom], set())
    assert atom in matched


def test_match_and_output_number_mismatch():
    scheme = Scheme("foo", (Number(3),))
    atom = Atom("foo", (Number(4),))
    matched, _ = SchemeTerm.match_and_output(scheme, [atom], set())
    assert matched == set()


def test_match_and_output_quotation_match():
    scheme = Scheme("foo", (Quotation('"hi"'),))
    atom = Atom("foo", (Quotation('"hi"'),))
    matched, _ = SchemeTerm.match_and_output(scheme, [atom], set())
    assert atom in matched


def test_match_and_output_quotation_mismatch():
    scheme = Scheme("foo", (Quotation('"hi"'),))
    atom = Atom("foo", (Quotation('"bye"'),))
    matched, _ = SchemeTerm.match_and_output(scheme, [atom], set())
    assert matched == set()


def test_match_and_output_nested_scheme():
    inner = Scheme("bar", (Placemarker("t", Type.OUTPUT),))
    outer = Scheme("foo", (inner,))
    atom = Atom("foo", (Atom("bar", (Number(1),)),))
    matched, outputs = SchemeTerm.match_and_output(outer, [atom], set())
    assert atom in matched
    assert outputs == {Number(1)}


def test_match_and_output_multiple_atoms():
    pm = Placemarker("t", Type.OUTPUT)
    scheme = Scheme("foo", (pm,))
    a1 = Atom("foo", (Number(1),))
    a2 = Atom("foo", (Number(2),))
    a3 = Atom("bar", (Number(3),))
    matched, outputs = SchemeTerm.match_and_output(scheme, [a1, a2, a3], set())
    assert matched == {a1, a2}
    assert outputs == {Number(1), Number(2)}


# --- generate_and_output ---


def test_generate_and_output_no_terms():
    scheme = Scheme("foo")
    result = SchemeTerm.generate_and_output(scheme, set(), {})
    assert result == {Atom("foo"): set()}


def test_generate_and_output_number_term():
    scheme = Scheme("foo", (Number(3),))
    result = SchemeTerm.generate_and_output(scheme, set(), {})
    assert result == {Atom("foo", (Number(3),)): set()}


def test_generate_and_output_quotation_term():
    scheme = Scheme("foo", (Quotation('"hi"'),))
    result = SchemeTerm.generate_and_output(scheme, set(), {})
    assert result == {Atom("foo", (Quotation('"hi"'),)): set()}


def test_generate_and_output_input_substitutes():
    pm = Placemarker("t", Type.INPUT)
    scheme = Scheme("foo", (pm,))
    result = SchemeTerm.generate_and_output(scheme, {Number(1), Number(2)}, {})
    assert set(result.keys()) == {Atom("foo", (Number(1),)), Atom("foo", (Number(2),))}
    assert all(v == set() for v in result.values())


def test_generate_and_output_input_empty_substitutes():
    pm = Placemarker("t", Type.INPUT)
    scheme = Scheme("foo", (pm,))
    result = SchemeTerm.generate_and_output(scheme, set(), {})
    assert result == {}


def test_generate_and_output_output_unwraps():
    pm = Placemarker("t", Type.OUTPUT)
    scheme = Scheme("foo", (pm,))
    # candidate identifier matches placemarker → unwrap to inner term
    candidate = Atom("t", (Number(1),))
    result = SchemeTerm.generate_and_output(scheme, set(), {pm: {candidate}})
    assert Atom("foo", (Number(1),)) in result
    assert result[Atom("foo", (Number(1),))] == {Number(1)}


def test_generate_and_output_output_no_unwrap():
    pm = Placemarker("t", Type.OUTPUT)
    scheme = Scheme("foo", (pm,))
    # candidate identifier differs → use whole atom
    candidate = Atom("bar", (Number(1),))
    result = SchemeTerm.generate_and_output(scheme, set(), {pm: {candidate}})
    assert Atom("foo", (candidate,)) in result
    assert result[Atom("foo", (candidate,))] == {candidate}


def test_generate_and_output_constant_no_output():
    pm = Placemarker("t", Type.CONSTANT)
    scheme = Scheme("foo", (pm,))
    candidate = Atom("t", (Number(1),))
    result = SchemeTerm.generate_and_output(scheme, set(), {pm: {candidate}})
    # utilise = Number(1) (unwrapped), but is_output=False so outputs set is empty
    assert result.get(Atom("foo", (Number(1),))) == set()


def test_generate_and_output_facts_filter():
    scheme = Scheme("foo")
    existing = Atom("foo")
    result = SchemeTerm.generate_and_output(scheme, set(), {}, facts={existing})
    assert result == {}


def test_generate_and_output_facts_filter_partial():
    pm = Placemarker("t", Type.INPUT)
    scheme = Scheme("foo", (pm,))
    a1 = Atom("foo", (Number(1),))
    a2 = Atom("foo", (Number(2),))
    result = SchemeTerm.generate_and_output(scheme, {Number(1), Number(2)}, {}, facts={a1})
    assert a1 not in result
    assert a2 in result


# --- lookup ---


def test_lookup_empty_modes():
    assert SchemeTerm.lookup([], [], {Atom("foo")}) == {}


def test_lookup_registers_scheme_and_placemarker():
    pm = Placemarker("t", Type.INPUT)
    scheme = Scheme("foo", (pm,))
    mode = SimpleNamespace(scheme=scheme)
    result = SchemeTerm.lookup([mode], [], set())
    assert scheme in result
    assert pm in result


def test_lookup_populates_scheme_with_matching_facts():
    pm = Placemarker("t", Type.INPUT)
    scheme = Scheme("foo", (pm,))
    mode = SimpleNamespace(scheme=scheme)
    atom = Atom("foo", (Number(1),))
    type_fact = Atom("t", (Number(1),))
    result = SchemeTerm.lookup([mode], [], {atom, type_fact})
    assert atom in result[scheme]


def test_lookup_populates_placemarker_with_type_facts():
    pm = Placemarker("t", Type.INPUT)
    scheme = Scheme("foo", (pm,))
    mode = SimpleNamespace(scheme=scheme)
    type_fact = Atom("t", (Number(1),))
    result = SchemeTerm.lookup([mode], [], {type_fact})
    assert type_fact in result[pm]


def test_lookup_mode_b_also_registered():
    scheme = Scheme("bar")
    mode = SimpleNamespace(scheme=scheme)
    atom = Atom("bar")
    result = SchemeTerm.lookup([], [mode], {atom})
    assert scheme in result
    assert atom in result[scheme]
