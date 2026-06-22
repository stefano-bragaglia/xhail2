"""Grounding — built from a Problem + a clasp answer set."""
from __future__ import annotations

from xhail.core.config import Config
from xhail.core.parser.parser import parse_token
from xhail.core.terms.atom import Atom
from xhail.core.terms.clause import Clause
from xhail.core.terms.literal import Literal
from xhail.core.terms.scheme_term import SchemeTerm


# ---------------------------------------------------------------------------
# get_kernel helpers
# ---------------------------------------------------------------------------

def _build_kernel_clauses(grounding: Grounding, alpha: Atom, clauses: dict) -> None:
    for mode_h in grounding._problem.get_mode_hs():
        scheme = mode_h.get_scheme()
        if SchemeTerm.subsumes(scheme, alpha, grounding._facts):
            clause = _build_kernel_clause(grounding, alpha, mode_h, scheme)
            clauses[clause] = None


def _build_kernel_clause(grounding: Grounding, alpha: Atom, mode_h, scheme) -> Clause:
    head = Atom.Builder(alpha).set_weight(mode_h.weight).set_priority(mode_h.priority).build()
    builder = Clause.Builder().set_head(head)
    substitutes = SchemeTerm.find_substitutes(scheme, alpha)
    if substitutes:
        _expand_body(grounding, builder, substitutes)
    return builder.build()


def _expand_body(grounding: Grounding, builder: Clause.Builder, substitutes: set) -> None:
    level = 0
    usables = set(substitutes)
    used: set = set()
    while usables:
        level += 1
        next_: set = set()
        for mode_b in grounding._problem.get_mode_bs():
            _apply_mode_b(grounding, builder, mode_b, usables, next_, level)
        used |= usables
        usables = next_ - used


def _apply_mode_b(grounding: Grounding, builder: Clause.Builder, mode_b, usables: set, next_: set, level: int) -> None:
    scheme = mode_b.get_scheme()
    if mode_b.negated:
        found = SchemeTerm.generate_and_output(scheme, usables, grounding._table, grounding._facts)
        for atom, outputs in found.items():
            lit_atom = Atom.Builder(atom).set_weight(mode_b.weight).set_priority(mode_b.priority).build()
            builder.add_literal(Literal(lit_atom, negated=True, level=level))
            next_.update(outputs)
    else:
        matched, outputs = SchemeTerm.match_and_output(scheme, grounding._table.get(scheme, set()), usables)
        for atom in matched:
            lit_atom = Atom.Builder(atom).set_weight(mode_b.weight).set_priority(mode_b.priority).build()
            builder.add_literal(Literal(lit_atom, level=level))
        next_.update(outputs)


# ---------------------------------------------------------------------------
# get_generalisation helpers
# ---------------------------------------------------------------------------

def _generalise_clause(grounding: Grounding, clause: Clause) -> Clause:
    map_: dict = {}
    builder = Clause.Builder()
    _generalise_head(grounding, clause, builder, map_)
    _generalise_body(grounding, clause, builder, map_)
    return builder.build()


def _generalise_head(grounding: Grounding, clause: Clause, builder: Clause.Builder, map_: dict) -> None:
    atom = clause.head
    for mode_h in grounding._problem.get_mode_hs():
        scheme = mode_h.get_scheme()
        if SchemeTerm.subsumes(scheme, atom, grounding._facts):
            builder.set_head(scheme.generalises(atom, map_))


def _generalise_body(grounding: Grounding, clause: Clause, builder: Clause.Builder, map_: dict) -> None:
    for literal in clause.body:
        atom = literal.atom
        for mode_b in grounding._problem.get_mode_bs():
            scheme = mode_b.get_scheme()
            if SchemeTerm.subsumes(scheme, atom, grounding._facts):
                gen_atom = scheme.generalises(atom, map_)
                builder.add_literal(Literal(gen_atom, negated=literal.negated, level=literal.level))


# ---------------------------------------------------------------------------
# as_clauses helpers
# ---------------------------------------------------------------------------

def _has_literals(clauses: tuple) -> bool:
    return any(clause.body for clause in clauses)


def _emit_clause(result: dict, clause_id: int, clause: Clause) -> None:
    literals = clause.body
    result[f"% {clause}"] = None
    result[f"clause({clause_id})."] = None
    _emit_literal_facts(result, clause_id, literals)
    _emit_clause_levels(result, clause_id, clause, literals)
    _emit_minimize(result, clause_id, clause, literals)
    _emit_head_rule(result, clause_id, clause, literals)
    _emit_try_rules(result, clause_id, literals)


def _emit_literal_facts(result: dict, clause_id: int, literals: tuple) -> None:
    for lit_id, _ in enumerate(literals, start=1):
        result[f"literal({clause_id},{lit_id})."] = None


def _emit_clause_levels(result: dict, clause_id: int, clause: Clause, literals: tuple) -> None:
    for level in range(clause.get_levels()):
        result[f":-not clause_level({clause_id},{level}),clause_level({clause_id},{1 + level})."] = None
    result[f"clause_level({clause_id},0):-use_clause_literal({clause_id},0)."] = None
    for lit_id, lit in enumerate(literals, start=1):
        result[f"clause_level({clause_id},{lit.level}):-use_clause_literal({clause_id},{lit_id})."] = None


def _emit_minimize(result: dict, clause_id: int, clause: Clause, literals: tuple) -> None:
    head = clause.head
    result[f"#minimize[ use_clause_literal({clause_id},0) ={head.weight} @{head.priority} ]."] = None
    for lit_id, lit in enumerate(literals, start=1):
        result[f"#minimize[ use_clause_literal({clause_id},{lit_id}) ={lit.get_weight()} @{lit.get_priority()} ]."] = None


def _build_try_parts(clause_id: int, literals: tuple, types_set: dict) -> list:
    parts = []
    for lit_id, lit in enumerate(literals, start=1):
        vars_str = ("," + ",".join(str(v) for v in lit.get_variables())) if lit.has_variables() else ""
        parts.append(f"try_clause_literal({clause_id},{lit_id}{vars_str})")
        for t in lit.get_types():
            types_set[t] = None
    return parts


def _emit_head_rule(result: dict, clause_id: int, clause: Clause, literals: tuple) -> None:
    head = clause.head
    types_set: dict = {t: None for t in head.get_types()}
    try_parts = _build_try_parts(clause_id, literals, types_set)
    lits_str = ("," + ",".join(try_parts)) if try_parts else ""
    types_str = ("," + ",".join(types_set)) if types_set else ""
    result[f"{head}:-use_clause_literal({clause_id},0){lits_str}{types_str}."] = None


def _emit_try_rules(result: dict, clause_id: int, literals: tuple) -> None:
    for lit_id, lit in enumerate(literals, start=1):
        vars_str = ("," + ",".join(str(v) for v in lit.get_variables())) if lit.has_variables() else ""
        types_str = ("," + ",".join(lit.get_types())) if lit.has_types() else ""
        result[f"try_clause_literal({clause_id},{lit_id}{vars_str}):-use_clause_literal({clause_id},{lit_id}),{lit}{types_str}."] = None
        result[f"try_clause_literal({clause_id},{lit_id}{vars_str}):-not use_clause_literal({clause_id},{lit_id}){types_str}."] = None


# ---------------------------------------------------------------------------
# solve helpers
# ---------------------------------------------------------------------------

def _run_induction(grounding: Grounding, values, builder) -> object:
    from xhail.core.dialler import Dialler
    from xhail.core.entities.answers import time_induction
    dialler = Dialler(grounding._config, grounding, values)
    new_values, outputs = time_induction(1, dialler)
    for output in outputs:
        if builder.size() > 0 and grounding._config.terminate:
            break
        _process_induction_output(grounding, output, new_values, builder)
    return new_values


def _process_induction_output(grounding: Grounding, output, values, builder) -> None:
    from xhail.core.entities.answers import time_deduction_grounding
    from xhail.core import logger
    from xhail.core.logger import SIGNATURE
    from xhail.core.entities.answer import Answer
    hypothesis = time_deduction_grounding(grounding, output)
    if grounding._config.debug:
        logger.message(f"*** Info  ({SIGNATURE}): found Hypothesis: {' '.join(str(h) for h in hypothesis.get_hypotheses())}")
    builder.put(values, Answer.Builder(grounding).set_hypothesis(hypothesis).build())


# ---------------------------------------------------------------------------
# Grounding
# ---------------------------------------------------------------------------

class Grounding:

    class Builder:
        def __init__(self, problem) -> None:
            if problem is None:
                raise ValueError("problem must not be None")
            self._covered: set[Literal] = set()
            self._delta: set[Atom] = set()
            self._facts: set[Atom] = set()
            self._model: set[Atom] = set()
            self._problem = problem
            self._uncovered: set[Literal] = set()

        def add_atom(self, atom: Atom) -> Grounding.Builder:
            if atom is None:
                return self
            if atom.identifier.startswith("abduced_"):
                stripped = atom.identifier[len("abduced_"):]
                b = Atom.Builder(stripped)
                for t in atom.terms:
                    b.add_term(t)
                self._delta.add(b.build())
            else:
                self._facts.add(atom)
                if (self._problem._config.full
                        and self._problem.has_displays()
                        and self._problem.lookup(atom)):
                    self._model.add(atom)
            return self

        def add_atoms(self, atoms) -> Grounding.Builder:
            for atom in atoms:
                self.add_atom(atom)
            return self

        def remove_atom(self, atom: Atom) -> Grounding.Builder:
            if atom is None:
                return self
            if atom.identifier.startswith("abduced_"):
                stripped = atom.identifier[len("abduced_"):]
                b = Atom.Builder(stripped)
                for t in atom.terms:
                    b.add_term(t)
                self._delta.discard(b.build())
            else:
                self._facts.discard(atom)
                self._model.discard(atom)
            return self

        def remove_atoms(self, atoms) -> Grounding.Builder:
            for atom in atoms:
                self.remove_atom(atom)
            return self

        def parse(self, answer) -> Grounding.Builder:
            for s in answer:
                atom = parse_token(s)
                if atom is not None:
                    self.add_atom(atom)
            return self

        def build(self) -> Grounding:
            self._covered.clear()
            self._uncovered.clear()
            for example in self._problem.get_examples():
                atom = example.get_atom()
                lit = Literal(atom, negated=example.is_negated())
                if example.is_negated() != (atom in self._facts):
                    self._covered.add(lit)
                else:
                    self._uncovered.add(lit)
            return Grounding(self)

        def clear(self) -> Grounding.Builder:
            self._covered.clear()
            self._delta.clear()
            self._facts.clear()
            self._model.clear()
            self._uncovered.clear()
            return self

    def __init__(self, builder: Grounding.Builder) -> None:
        self._config: Config = builder._problem.get_config()
        self._count: int = len(builder._delta)
        self._covered: tuple[Literal, ...] = tuple(builder._covered)
        self._delta: tuple[Atom, ...] = tuple(builder._delta)
        self._facts: set[Atom] = set(builder._facts)
        self._generalisation: tuple[Clause, ...] | None = None
        self._kernel: tuple[Clause, ...] | None = None
        self._model: tuple[Atom, ...] = tuple(builder._model)
        self._problem = builder._problem
        self._table: dict = SchemeTerm.lookup(
            builder._problem.get_mode_hs(),
            builder._problem.get_mode_bs(),
            builder._facts,
        )
        self._uncovered: tuple[Literal, ...] = tuple(builder._uncovered)

    def as_bad_solution(self) -> str:
        prefix = ",".join(str(a) for a in self._delta) + "," if self._count > 0 else ""
        return f"bad_solution:-{prefix}number_abduced({self._count})."

    def as_clauses(self) -> tuple[str, ...]:
        clauses = self.get_generalisation()
        if not clauses:
            return ()
        result: dict[str, None] = {}
        result["{ use_clause_literal(V1,0) }:-clause(V1)."] = None
        if _has_literals(clauses):
            result["{ use_clause_literal(V1,V2) }:-clause(V1),literal(V1,V2)."] = None
        for clause_id, clause in enumerate(clauses):
            _emit_clause(result, clause_id, clause)
        return tuple(result)

    def get_background(self) -> tuple[str, ...]:
        return self._problem.get_background()

    def get_config(self) -> Config:
        return self._config

    def get_count(self) -> int:
        return self._count

    def get_covered(self) -> tuple[Literal, ...]:
        return self._covered

    def get_delta(self) -> tuple[Atom, ...]:
        return self._delta

    def get_displays(self):
        return self._problem.get_displays()

    def get_domains(self) -> tuple[str, ...]:
        return self._problem.get_domains()

    def get_examples(self):
        return self._problem.get_examples()

    def get_facts(self) -> set[Atom]:
        return self._facts

    def get_filters(self) -> tuple[str, ...]:
        result: set[str] = {"#hide.", "#show use_clause_literal/2."}
        for d in self._problem.get_displays():
            result.add(f"#show {d.get_identifier()}/{d.get_arity()}.")
        for e in self._problem.get_examples():
            a = e.get_atom()
            result.add(f"#show {a.identifier}/{a.get_arity()}.")
        return tuple(sorted(result))

    def get_generalisation(self) -> tuple[Clause, ...]:
        if self._generalisation is None:
            clauses: dict[Clause, None] = {}
            for clause in self.get_kernel():
                clauses[_generalise_clause(self, clause)] = None
            self._generalisation = tuple(clauses)
        return self._generalisation

    def get_kernel(self) -> tuple[Clause, ...]:
        if self._kernel is None:
            clauses: dict[Clause, None] = {}
            for alpha in self._delta:
                _build_kernel_clauses(self, alpha, clauses)
            self._kernel = tuple(clauses)
        return self._kernel

    def get_mode_bs(self):
        return self._problem.get_mode_bs()

    def get_mode_hs(self):
        return self._problem.get_mode_hs()

    def get_model(self) -> tuple[Atom, ...]:
        return self._model

    def get_problem(self):
        return self._problem

    def get_table(self) -> dict:
        return self._table

    def get_uncovered(self) -> tuple[Literal, ...]:
        return self._uncovered

    def has_background(self) -> bool:
        return self._problem.has_background()

    def has_covered(self) -> bool:
        return bool(self._covered)

    def has_delta(self) -> bool:
        return bool(self._delta)

    def has_displays(self) -> bool:
        return self._problem.has_displays()

    def has_domains(self) -> bool:
        return self._problem.has_domains()

    def has_examples(self) -> bool:
        return self._problem.has_examples()

    def has_generalisation(self) -> bool:
        return bool(self.get_generalisation())

    def has_kernel(self) -> bool:
        return bool(self.get_kernel())

    def has_model(self) -> bool:
        return bool(self._model)

    def has_modes(self) -> bool:
        return self._problem.has_modes()

    def has_uncovered(self) -> bool:
        return bool(self._uncovered)

    def lookup(self, atom: Atom) -> bool:
        return self._problem.lookup(atom)

    def needs_induction(self) -> bool:
        return bool(self.get_generalisation())

    def save(self, it: int, stream) -> bool:
        from xhail.core.utils import save_grounding
        return save_grounding(self, it, stream)

    def solve(self, values, builder):
        if self.needs_induction():
            return _run_induction(self, values, builder)
        from xhail.core.entities.answer import Answer
        from xhail.core.entities.values import Values
        builder.put(Values(), Answer.Builder(self).build())
        return values
