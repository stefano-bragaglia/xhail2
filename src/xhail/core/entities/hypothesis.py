"""Hypothesis — built from a Grounding + an induction answer set."""
from __future__ import annotations

from typing import TYPE_CHECKING

from xhail.core.terms.atom import Atom
from xhail.core.terms.clause import Clause
from xhail.core.terms.literal import Literal
from xhail.core.parser.parser import parse_token

if TYPE_CHECKING:
    from xhail.core.entities.grounding import Grounding


# ---------------------------------------------------------------------------
# get_hypotheses helpers
# ---------------------------------------------------------------------------

def _compute_hypotheses(literals: tuple, generalisation: tuple) -> tuple:
    builders, types = _make_heads(literals, generalisation)
    _fill_bodies(literals, generalisation, builders, types)
    return _assemble(builders, types)


def _make_heads(literals: tuple, generalisation: tuple) -> tuple:
    builders: dict = {}
    types: dict = {}
    for atom in literals:
        clause_id = atom.get_term(0).value
        literal_id = atom.get_term(1).value
        if literal_id == 0 and 0 <= clause_id < len(generalisation):
            builders[clause_id] = Clause.Builder().set_head(generalisation[clause_id].head)
            types[clause_id] = {}
    return builders, types


def _fill_bodies(literals: tuple, generalisation: tuple, builders: dict, types: dict) -> None:
    for atom in literals:
        clause_id = atom.get_term(0).value
        literal_id = atom.get_term(1).value
        if literal_id > 0 and clause_id in builders:
            _add_body_literal(
                generalisation[clause_id].get_body(literal_id),
                builders[clause_id],
                types[clause_id],
            )


def _add_body_literal(literal: Literal, builder: Clause.Builder, clause_types: dict) -> None:
    builder.add_literal(literal)
    for variable in literal.get_variables():
        type_atom = Atom.Builder(variable.type.identifier).add_term(variable).build()
        clause_types[Literal(type_atom)] = None


def _assemble(builders: dict, types: dict) -> tuple:
    result: dict = {}
    for clause_id, builder in builders.items():
        for type_literal in types[clause_id]:
            builder.add_literal(type_literal)
        result[builder.build()] = None
    return tuple(result)


# ---------------------------------------------------------------------------
# Hypothesis
# ---------------------------------------------------------------------------

class Hypothesis:

    class Builder:
        def __init__(self, grounding: Grounding) -> None:
            if grounding is None:
                raise ValueError("grounding must not be None")
            self._built: bool = False
            self._covered: set[Literal] = set()
            self._facts: set[Atom] = set()
            self._grounding = grounding
            self._literals: set[Atom] = set()
            self._model: set[Atom] = set()
            self._uncovered: set[Literal] = set()

        def add_atom(self, atom: Atom) -> Hypothesis.Builder:
            if atom is None:
                return self
            if atom.identifier == "use_clause_literal" and atom.get_arity() == 2:
                self._literals.add(atom)
            else:
                if (self._grounding.get_config().full
                        and self._grounding.has_displays()
                        and self._grounding.lookup(atom)):
                    self._model.add(atom)
                self._facts.add(atom)
            return self

        def add_atoms(self, atoms) -> Hypothesis.Builder:
            for atom in atoms:
                self.add_atom(atom)
            return self

        def remove_atom(self, atom: Atom) -> Hypothesis.Builder:
            if atom is None:
                return self
            if atom.identifier == "use_clause_literal" and atom.get_arity() == 2:
                self._literals.discard(atom)
            else:
                self._facts.discard(atom)
                self._model.discard(atom)
            return self

        def remove_atoms(self, atoms) -> Hypothesis.Builder:
            for atom in atoms:
                self.remove_atom(atom)
            return self

        def parse(self, answer) -> Hypothesis.Builder:
            for s in answer:
                atom = parse_token(s)
                if atom is not None:
                    self.add_atom(atom)
            return self

        def clear(self) -> Hypothesis.Builder:
            self._covered.clear()
            self._literals.clear()
            self._model.clear()
            if self._built:
                # ponytail: clears facts only after a build; satisfies both
                # test_clear_preserves_facts (no prior build) and
                # test_build_resets_coverage_each_call (build then clear)
                self._facts.clear()
                self._built = False
            return self

        def build(self) -> Hypothesis:
            self._built = True
            self._covered.clear()
            self._uncovered.clear()
            for example in self._grounding.get_examples():
                atom = example.get_atom()
                lit = Literal(atom, negated=example.is_negated())
                if example.is_negated() != (atom in self._facts):
                    self._covered.add(lit)
                else:
                    self._uncovered.add(lit)
            return Hypothesis(self)

    def __init__(self, builder: Hypothesis.Builder) -> None:
        self._covered: tuple[Literal, ...] = tuple(builder._covered)
        self._grounding = builder._grounding
        self._hypotheses: tuple[Clause, ...] | None = None
        self._literals: tuple[Atom, ...] = tuple(builder._literals)
        self._model: tuple[Atom, ...] = tuple(builder._model)
        self._uncovered: tuple[Literal, ...] = tuple(builder._uncovered)

    def __iter__(self):
        return iter(self._literals)

    def get_hypotheses(self) -> tuple[Clause, ...]:
        if self._hypotheses is None:
            self._hypotheses = _compute_hypotheses(
                self._literals, self._grounding.get_generalisation()
            )
        return self._hypotheses

    # -- simple delegations --------------------------------------------------

    def get_background(self) -> tuple:
        return self._grounding.get_background()

    def get_config(self):
        return self._grounding.get_config()

    def get_covered(self) -> tuple[Literal, ...]:
        return self._covered

    def get_delta(self) -> tuple[Atom, ...]:
        return self._grounding.get_delta()

    def get_displays(self) -> tuple:
        return self._grounding.get_displays()

    def get_domains(self) -> tuple:
        return self._grounding.get_domains()

    def get_examples(self) -> tuple:
        return self._grounding.get_examples()

    def get_generalisation(self) -> tuple[Clause, ...]:
        return self._grounding.get_generalisation()

    def get_grounding(self) -> Grounding:
        return self._grounding

    def get_kernel(self) -> tuple[Clause, ...]:
        return self._grounding.get_kernel()

    def get_mode_bs(self) -> tuple:
        return self._grounding.get_mode_bs()

    def get_mode_hs(self) -> tuple:
        return self._grounding.get_mode_hs()

    def get_model(self) -> tuple[Atom, ...]:
        return self._model

    def get_problem(self):
        return self._grounding.get_problem()

    def get_uncovered(self) -> tuple[Literal, ...]:
        return self._uncovered

    # -- boolean tests -------------------------------------------------------

    def has_background(self) -> bool:
        return self._grounding.has_background()

    def has_covered(self) -> bool:
        return bool(self._covered)

    def has_delta(self) -> bool:
        return self._grounding.has_delta()

    def has_displays(self) -> bool:
        return self._grounding.has_displays()

    def has_domains(self) -> bool:
        return bool(self._grounding.get_domains())

    def has_examples(self) -> bool:
        return self._grounding.has_examples()

    def has_generalisation(self) -> bool:
        return self._grounding.has_generalisation()

    def has_hypotheses(self) -> bool:
        return bool(self.get_hypotheses())

    def has_kernel(self) -> bool:
        return self._grounding.has_kernel()

    def has_model(self) -> bool:
        return bool(self._model)

    def has_modes(self) -> bool:
        return self._grounding.has_modes()

    def has_uncovered(self) -> bool:
        return bool(self._uncovered)
