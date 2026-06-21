from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    from xhail.core.terms.term import Term
    from xhail.core.terms.variable import Variable


class SchemeTerm(ABC):
    @overload
    def generalises(self, term: Term, map: dict[Term, Variable]) -> Term: ...

    @overload
    def generalises(self, variables: set[Variable]) -> Term: ...

    @abstractmethod
    def generalises(self, *args, **kwargs) -> Term: ...

    @staticmethod
    def subsumes(scheme, term, facts) -> bool:
        from xhail.core.terms.placemarker import Placemarker
        from xhail.core.terms.scheme import Scheme
        if isinstance(scheme, Scheme):
            return _subsumes_scheme(scheme, term, facts)
        if isinstance(scheme, Placemarker):
            return _subsumes_placemarker(scheme, term, facts)
        return False

    @staticmethod
    def lookup(mode_hs, mode_bs, facts):
        result = {}
        _register_modes(mode_hs, result)
        _register_modes(mode_bs, result)
        for scheme, part in result.items():
            for fact in facts:
                if SchemeTerm.subsumes(scheme, fact, facts):
                    part.add(fact)
        return result

    @staticmethod
    def find_substitutes(scheme, candidate):
        from xhail.core.terms.atom import Atom
        if not isinstance(candidate, Atom):
            return set()
        if candidate.identifier != scheme.identifier or candidate.get_arity() != scheme.get_arity():
            return set()
        result = set()
        _collect_substitutes(scheme, candidate, result)
        return result

    @staticmethod
    def match_and_output(scheme, atoms, substitutes):
        matched = set()
        outputs = set()
        for atom in atoms:
            output = _match_and_output_atom(scheme, atom, substitutes)
            if output is not None:
                matched.add(atom)
                outputs.update(output)
        return (matched, outputs)

    @staticmethod
    def generate_and_output(scheme, substitutes, table, facts=None):
        result = _generate_and_output_core(scheme, substitutes, table)
        if facts is None:
            return result
        return {atom: v for atom, v in result.items() if atom not in facts}


def _subsumes_scheme(scheme, term, facts):
    from xhail.core.terms.atom import Atom
    if not isinstance(term, Atom):
        return False
    if term.identifier != scheme.identifier or term.get_arity() != scheme.get_arity():
        return False
    return all(SchemeTerm.subsumes(scheme.get_term(i), term.get_term(i), facts) for i in range(scheme.get_arity()))


def _subsumes_placemarker(placemarker, term, facts):
    from xhail.core.terms.atom import Atom, Builder
    from xhail.core.terms.variable import Variable
    if isinstance(term, Variable):
        return False
    if Builder(placemarker.identifier).add_term(term).build() in facts:
        return True
    return isinstance(term, Atom) and term.identifier == placemarker.identifier and term.get_arity() == 1


def _register_modes(modes, result):
    for mode in modes:
        scheme = mode.scheme
        result[scheme] = set()
        for pm in scheme.get_placemarkers():
            if pm not in result:
                result[pm] = set()


def _collect_substitutes(scheme, atom, result):
    from xhail.core.terms.placemarker import Placemarker, Type
    from xhail.core.terms.scheme import Scheme
    for i in range(scheme.get_arity()):
        term = scheme.get_term(i)
        if isinstance(term, Placemarker):
            if term.type == Type.INPUT:
                result.add(atom.get_term(i))
        elif isinstance(term, Scheme):
            result.update(SchemeTerm.find_substitutes(term, atom.get_term(i)))


def _generate_and_output_core(scheme, substitutes, table):
    from xhail.core.terms.atom import Builder
    builders = {Builder(scheme.identifier): set()}
    for i in range(scheme.get_arity()):
        builders = _dispatch_term(scheme.get_term(i), builders, substitutes, table)
    return {b.build(): v for b, v in builders.items()}


def _dispatch_term(schemeterm, builders, substitutes, table):
    from xhail.core.terms.placemarker import Placemarker
    from xhail.core.terms.scheme import Scheme
    if isinstance(schemeterm, Placemarker):
        return _handle_placemarker(builders, schemeterm, substitutes, table)
    if isinstance(schemeterm, Scheme):
        return _handle_scheme_term(builders, schemeterm, substitutes, table)
    return _handle_fixed_term(builders, schemeterm)


def _handle_fixed_term(builders, schemeterm):
    temporary = {}
    for builder in list(builders.keys()):
        temporary[builder.add_term(schemeterm)] = set(builders[builder])
    return temporary


def _handle_placemarker(builders, placemarker, substitutes, table):
    from xhail.core.terms.placemarker import Type
    if placemarker.type == Type.INPUT:
        return _handle_input(builders, substitutes)
    return _handle_output_const(builders, placemarker, table)


def _handle_input(builders, substitutes):
    temporary = {}
    for builder in list(builders.keys()):
        for substitute in substitutes:
            temporary[builder.clone().add_term(substitute)] = set(builders[builder])
    return temporary


def _handle_output_const(builders, placemarker, table):
    from xhail.core.terms.placemarker import Type
    is_output = placemarker.type == Type.OUTPUT
    candidates = table.get(placemarker, set())
    temporary = {}
    for builder in list(builders.keys()):
        for candidate in candidates:
            utilise = _unwrap(candidate, placemarker)
            value = set(builders[builder])
            if is_output:
                value.add(utilise)
            temporary[builder.clone().add_term(utilise)] = value
    return temporary


def _unwrap(candidate, placemarker):
    if candidate.identifier == placemarker.identifier and candidate.get_arity() == 1:
        return candidate.get_term(0)
    return candidate


def _handle_scheme_term(builders, schemeterm, substitutes, table):
    returned = _generate_and_output_core(schemeterm, substitutes, table)
    temporary = {}
    for builder in list(builders.keys()):
        for atom, outputs in returned.items():
            value = set(builders[builder]) | outputs
            temporary[builder.clone().add_term(atom)] = value
    return temporary


def _match_and_output_atom(scheme, atom, substitutes):
    if atom.identifier != scheme.identifier or atom.get_arity() != scheme.get_arity():
        return None
    result = set()
    for i in range(scheme.get_arity()):
        output = _match_term(scheme.get_term(i), atom.get_term(i), substitutes)
        if output is None:
            return None
        result.update(output)
    return result


def _match_term(schemeterm, atom_term, substitutes):
    from xhail.core.terms.placemarker import Placemarker
    from xhail.core.terms.scheme import Scheme
    if isinstance(schemeterm, Placemarker):
        return _match_placemarker(schemeterm, atom_term, substitutes)
    if isinstance(schemeterm, Scheme):
        return _match_atom_to_scheme(schemeterm, atom_term, substitutes)
    return _match_fixed(schemeterm, atom_term)


def _match_placemarker(placemarker, atom_term, substitutes):
    from xhail.core.terms.placemarker import Type
    if placemarker.type == Type.INPUT:
        return None if atom_term not in substitutes else set()
    if placemarker.type == Type.OUTPUT:
        return {atom_term}
    return set()


def _match_atom_to_scheme(schemeterm, atom_term, substitutes):
    from xhail.core.terms.atom import Atom
    if not isinstance(atom_term, Atom):
        return None
    return _match_and_output_atom(schemeterm, atom_term, substitutes)


def _match_fixed(schemeterm, atom_term):
    if type(schemeterm) is not type(atom_term):
        return None
    return set() if schemeterm == atom_term else None
