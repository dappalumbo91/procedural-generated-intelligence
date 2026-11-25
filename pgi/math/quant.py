"""Bounded quantifiers over a finite enumeration, and a small unbounded fragment.

Isabelle HOL.thy defines `All` and `Ex`. The rules used here are `allI`,
`spec`, `exI`, and the axiom `impI`. `refl` is the equality axiom `t = t`.
Set.thy defines `Ball` and `Bex`, with `ballI`, `bspec`, `bexI`,
`ball_empty`, `bex_empty`, `ball_simps`, `bex_simps`, and `ex_in_conv`.

A bounded quantifier is decided by checking `<=` or `=` at each member.
The empty universal holds and the empty existential fails. That vacuous
body is not evaluated. An open comparison leaves the quantifier open.

An unbounded quantifier stays open except for three shapes. A variable
related to itself is `allI` together with `refl`. An equality whose other
side is a closed term is `exI` at that term. The leastness shape holds by
`bspec` when the bound is a member, and `spec` refutes it at the maximum
when the bound is strictly above that maximum.

`complete_real` is the least-upper-bound statement. For a finite enumeration
the witness is the maximum. `Max_in`, `Max_ge`, and `Max_le_iff` check the
bounded claims. For an atMost ray the witness is the bound, by `cSup_atMost`.
For a lessThan ray the witness is the bound, by the Archimedean bisection.
For a two-sided interval the witness is the upper bound: a closed upper end
by `cSup_eq_maximum`, and an open upper end by the same bisection.
An up-ray and the set of every real are not bounded above.
Separation of a finite enumeration, and the singleton equality comprehension,
are a separate primitive. An unbounded predicate over all reals stays outside
that primitive.

Core Lean 4.36.0 resolves `Exists`, `And`, `Not`, `Iff`, `True`, `False`,
and `Decidable`. `forall` is a keyword there. This module does not import
Lean or Isabelle, and it does not use Octave.
"""

from __future__ import annotations

from dataclasses import dataclass

from pgi.math.kernel import KernelError, NotExact, trace
from pgi.math.rational import Ratio
from pgi.math.real import (
    RealForm,
    _add_forms,
    _canonical,
    _div_form,
    _mul_forms,
    _neg_form,
    _sub_forms,
    compare_reals,
    _sqrt_of_form,
    real_of_rat,
    show_form,
)
from pgi.math.set import (
    SetTheorem,
    canonical,
    contains_set,
    eval_set,
    maximum,
    set_trace,
    show_set,
)
from pgi.math.syntax import App, IntLit, Term, Var, closed, parse_term, pretty
from pgi.model import Rule


class _FreeVariable(Exception):
    pass


class _OpenPredicate(Exception):
    pass


class _Rejected(Exception):
    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.text = text


@dataclass(frozen=True)
class Pred:
    op: str
    left: Term
    right: Term


@dataclass(frozen=True)
class QuantTheorem:
    mode: str
    kind: str
    holds: bool
    binder: str
    members: tuple[RealForm, ...]
    predicate: Pred | None
    witness: RealForm | None
    bound: RealForm | None
    rule: str
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _justified_quant(self):
            raise KernelError(f"{self.rule} does not justify this quantifier")


@dataclass(frozen=True)
class CompleteTheorem:
    members: tuple[RealForm, ...]
    witness: RealForm
    rule: str
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _justified_complete(self):
            raise KernelError(f"{self.rule} does not justify this least upper bound")


def is_quantifier(body: str) -> bool:
    text = body.strip()
    return text.startswith(("all ", "ex ")) or text.startswith(("complete ", "complete{"))


def quantifier_rules(body: str, anchors: dict, substitute) -> tuple[Rule, ...]:
    try:
        return _dispatch(body, anchors, substitute)
    except NotExact as exc:
        return (_note(str(exc)),)
    except _FreeVariable:
        return (_note("a free variable stays open"),)
    except _OpenPredicate:
        return (_note("this quantifier is not settled"),)
    except _Rejected as exc:
        return (_note(exc.text),)


def _dispatch(body: str, anchors: dict, substitute) -> tuple[Rule, ...]:
    text = body.strip().replace("≤", "<=")
    if text.startswith("complete ") or text.startswith("complete{"):
        argument = text[len("complete") :].strip()
        return _complete(argument, anchors, substitute)
    if text.startswith("all "):
        return _quantifier("all", text[4:].strip(), body, anchors, substitute)
    if text.startswith("ex "):
        return _quantifier("ex", text[3:].strip(), body, anchors, substitute)
    raise _Rejected(f"{body} is not a theorem")


def _quantifier(kind: str, text: str, body: str, anchors: dict, substitute) -> tuple[Rule, ...]:
    parts = _split_token(text, ".")
    if parts is None:
        raise _Rejected(f"{body} is not a theorem")
    head, predicate_text = parts
    named = _split_name(head)
    if named is None:
        raise _Rejected(f"{body} is not a theorem")
    binder, rest = named
    if rest.startswith("in "):
        return _bounded(kind, binder, rest[3:].strip(), predicate_text, anchors, substitute)
    if rest == "":
        return _unbounded(kind, binder, predicate_text, anchors, substitute)
    raise _Rejected(f"{body} is not a theorem")


def _bounded(kind: str, binder: str, set_text: str, predicate_text: str, anchors: dict, substitute) -> tuple[Rule, ...]:
    term = parse_term(set_text)
    if term is None:
        raise _Rejected(f"{set_text} is not a theorem")
    body, lines = _rewrite(term, anchors, substitute, frozenset({binder}))
    if not closed(body):
        raise _FreeVariable()
    if not contains_set(body):
        raise NotExact("this expression is not a finite set")
    from pgi.math.arbitrary import interpret, ray_quantifier_rules
    from pgi.math.collect import CollectForm

    value, extra = interpret(body)
    predicate, prelude = _parse_pred(predicate_text, anchors, substitute, frozenset({binder}))
    detail_head = (*lines, *extra, *prelude)
    if isinstance(value, CollectForm):
        return ray_quantifier_rules(kind, binder, pretty(term), predicate, value, detail_head)
    if not isinstance(value, SetTheorem):
        raise NotExact("this expression is not a finite set")
    base = value
    detail_head = (*detail_head, *set_trace(base))
    shown = show_set(base.members)
    relation = _pred_text(predicate)
    if not base.members:
        holds = kind == "all"
        rule = "Ball.holds" if holds else "Bex.fails"
        theorem = QuantTheorem(
            "bounded",
            kind,
            holds,
            binder,
            (),
            predicate,
            None,
            None,
            rule,
            _empty_detail(kind),
        )
        return (_bounded_rule(kind, holds, binder, shown, relation, theorem, detail_head),)
    holds, witness = _bounded_verdict(kind, base.members, binder, predicate)
    rule = _bounded_rule_name(kind, holds)
    theorem = QuantTheorem(
        "bounded",
        kind,
        holds,
        binder,
        base.members,
        predicate,
        witness,
        None,
        rule,
        _bounded_detail(kind, holds, witness),
    )
    return (_bounded_rule(kind, holds, binder, shown, relation, theorem, detail_head),)


def _unbounded(kind: str, binder: str, predicate_text: str, anchors: dict, substitute) -> tuple[Rule, ...]:
    if _split_token(predicate_text, "-->") is not None:
        if kind != "all":
            raise _Rejected("this unbounded quantifier is not settled")
        return _leastness(binder, predicate_text, anchors, substitute)
    predicate, prelude = _parse_pred(predicate_text, anchors, substitute, frozenset({binder}))
    if _reflexive(predicate, binder):
        return _uniform(kind, binder, predicate, prelude)
    side = _closed_side(predicate, binder) if kind == "ex" and predicate.op == "eq" else None
    if side is not None:
        return _witness_equality(binder, predicate, side, prelude)
    raise _Rejected("this unbounded quantifier is not settled")


def _uniform(kind: str, binder: str, predicate: Pred, prelude: tuple[str, ...]) -> tuple[Rule, ...]:
    relation = _pred_text(predicate)
    if kind == "all":
        theorem = QuantTheorem(
            "uniform",
            "all",
            True,
            binder,
            (),
            predicate,
            None,
            None,
            "Ball.holds",
            _uniform_all_detail(predicate.op),
        )
        return (_plain_rule("math.ball", f"all {binder}. {relation}", f"all({binder}, {relation})", theorem, prelude),)
    witness = _zero()
    theorem = QuantTheorem(
        "uniform",
        "ex",
        True,
        binder,
        (),
        predicate,
        witness,
        None,
        "Bex.holds",
        _uniform_ex_detail(predicate.op),
    )
    return (_plain_rule("math.bex", f"ex {binder}. {relation}", f"ex({binder}, {relation})", theorem, prelude),)


def _witness_equality(binder: str, predicate: Pred, side: Term, prelude: tuple[str, ...]) -> tuple[Rule, ...]:
    witness = _form_of(side, {})
    relation = _pred_text(predicate)
    theorem = QuantTheorem(
        "witness",
        "ex",
        True,
        binder,
        (),
        predicate,
        witness,
        None,
        "Bex.holds",
        (
            "Isabelle exI: a witness of the predicate proves the existential.",
            f"The witness is {show_form(witness)}.",
            "Core Lean 4.36 resolves Exists.",
        ),
    )
    return (_plain_rule("math.bex", f"ex {binder}. {relation}", f"ex({binder}, {relation})", theorem, prelude),)


def _leastness(binder: str, predicate_text: str, anchors: dict, substitute) -> tuple[Rule, ...]:
    sides = _split_token(predicate_text, "-->")
    if sides is None:
        raise _Rejected("this unbounded quantifier is not settled")
    antecedent, consequent = sides
    antecedent = _strip_wrap(antecedent)
    if not antecedent.startswith("all "):
        raise _Rejected("this unbounded quantifier is not settled")
    inner_parts = _split_token(antecedent[4:].strip(), ".")
    if inner_parts is None:
        raise _Rejected("this unbounded quantifier is not settled")
    named = _split_name(inner_parts[0])
    if named is None or not named[1].startswith("in "):
        raise _Rejected("this unbounded quantifier is not settled")
    inner, set_text = named[0], named[1][3:].strip()
    if inner == binder:
        raise _Rejected("this unbounded quantifier is not settled")
    relation = _split_cmp(inner_parts[1])
    if relation is None or relation[0] != "le":
        raise _Rejected("this unbounded quantifier is not settled")
    left = parse_term(relation[1].strip())
    right = parse_term(relation[2].strip())
    if not isinstance(left, Var) or left.name != inner or not isinstance(right, Var) or right.name != binder:
        raise _Rejected("this unbounded quantifier is not settled")
    consequent_rel = _split_cmp(consequent)
    if consequent_rel is None or consequent_rel[0] != "le":
        raise _Rejected("this unbounded quantifier is not settled")
    bound_term = parse_term(consequent_rel[1].strip())
    bound_right = parse_term(consequent_rel[2].strip())
    if bound_term is None or not isinstance(bound_right, Var) or bound_right.name != binder:
        raise _Rejected("this unbounded quantifier is not settled")
    protected = frozenset({binder, inner})
    base, lines = _read_set(set_text, anchors, substitute, protected)
    rewritten, prelude = _rewrite(bound_term, anchors, substitute, protected)
    if _frees(rewritten):
        raise _FreeVariable()
    if contains_set(rewritten):
        raise NotExact("a set does not enter this quantifier")
    bound = _form_of(rewritten, {})
    shown = show_set(base.members)
    phrase = f"(all {inner} in {shown}. {inner} <= {binder}) --> {pretty(rewritten)} <= {binder}"
    interior = f"(all {inner} in {shown}, {inner} <= {binder}) --> {pretty(rewritten)} <= {binder}"
    detail_head = (*lines, *prelude)
    if not base.members:
        raise _Rejected("the empty set makes this leastness statement vacuous, so it stays open")
    if bound in base.members:
        theorem = QuantTheorem(
            "least",
            "all",
            True,
            binder,
            base.members,
            None,
            None,
            bound,
            "Ball.least",
            (
                "Isabelle impI: the implication follows by deriving the consequent from the premise.",
                "Isabelle allI: the outer quantifier is proved for an arbitrary upper bound.",
                "Isabelle bspec: the bound is a member, so every upper bound of the set is at least that member.",
                "Isabelle Max_le_iff is the finite form of that leastness. This direction uses membership.",
            ),
        )
        return (
            _plain_rule(
                "math.ball",
                f"all {binder}. {phrase}",
                f"all({binder}, {interior})",
                theorem,
                detail_head,
            ),
        )
    found = maximum(base.members)
    if found is None:
        raise _Rejected("the order of these elements is not settled")
    direction = compare_reals(bound, found)
    if direction == "open":
        raise _OpenPredicate()
    if direction == "gt":
        theorem = QuantTheorem(
            "refute",
            "all",
            False,
            binder,
            base.members,
            None,
            found,
            bound,
            "Ball.fails",
            (
                "Isabelle spec: a universal fails at a witness where the predicate fails.",
                f"The witness is {show_form(found)}.",
                "Isabelle Max_ge: every member is less than or equal to the maximum, so the bounded premise holds there.",
                "The bound is strictly above that maximum.",
            ),
        )
        return (
            _plain_rule(
                "math.not_ball",
                f"not (all {binder}. {phrase})",
                f"not_all({binder}, {interior})",
                theorem,
                detail_head,
            ),
        )
    raise _Rejected("this leastness statement stays open")


def _complete(text: str, anchors: dict, substitute) -> tuple[Rule, ...]:
    term = parse_term(text)
    if term is None:
        raise _Rejected(f"{text} is not a theorem")
    body, lines = _rewrite(term, anchors, substitute, frozenset())
    if not closed(body):
        raise _FreeVariable()
    if not contains_set(body):
        raise NotExact("this expression is not a finite set")
    from pgi.math.arbitrary import Interval, interpret, interval_complete_rule, ray_complete_rule
    from pgi.math.collect import CollectForm

    value, extra = interpret(body)
    head = (*lines, *extra)
    if isinstance(value, Interval):
        return interval_complete_rule(pretty(term), value, head)
    if isinstance(value, CollectForm):
        return ray_complete_rule(pretty(term), value, head)
    if not isinstance(value, SetTheorem):
        raise NotExact("this expression is not a finite set")
    base = value
    if not base.members:
        raise NotExact("complete_real assumes a member. The empty set has none")
    found = maximum(base.members)
    if found is None:
        raise NotExact("the order of these elements is not settled")
    detail = _complete_detail(base.members, found)
    theorem = CompleteTheorem(base.members, found, "Ball.complete", detail)
    shown = show_set(base.members)
    return (
        Rule(
            id="math.complete",
            layer="base",
            stage="quantity",
            title=f"{show_form(found)} is the least upper bound of {shown}",
            produces=f"complete({shown})",
            detail_lines=(*head, *set_trace(base), *theorem.detail),
        ),
    )


def _read_set(text: str, anchors: dict, substitute, protected: frozenset[str]) -> tuple[SetTheorem, tuple[str, ...]]:
    term = parse_term(text)
    if term is None:
        raise _Rejected(f"{text} is not a theorem")
    body, prelude = _rewrite(term, anchors, substitute, protected)
    if not closed(body):
        raise _FreeVariable()
    if not contains_set(body):
        raise NotExact("this expression is not a finite set")
    value = eval_set(body)
    from pgi.math.collect import CollectForm

    if isinstance(value, CollectForm):
        raise NotExact("this comprehension is not a finite enumeration")
    if not isinstance(value, SetTheorem):
        raise NotExact("this expression is not a finite set")
    return value, (*prelude, *set_trace(value))


def _parse_pred(text: str, anchors: dict, substitute, protected: frozenset[str]) -> tuple[Pred, tuple[str, ...]]:
    relation = _split_cmp(text)
    if relation is None:
        raise _Rejected(f"{text.strip()} is not a theorem")
    op, left_text, right_text = relation
    left = parse_term(left_text.strip())
    right = parse_term(right_text.strip())
    if left is None or right is None:
        raise _Rejected(f"{text.strip()} is not a theorem")
    left_body, left_lines = _rewrite(left, anchors, substitute, protected)
    right_body, right_lines = _rewrite(right, anchors, substitute, protected)
    binder_names = set(protected)
    if not _frees(left_body) <= binder_names or not _frees(right_body) <= binder_names:
        raise _FreeVariable()
    if contains_set(left_body) or contains_set(right_body):
        raise NotExact("a set does not enter this quantifier")
    return Pred(op, left_body, right_body), (*left_lines, *right_lines)


def _rewrite(term: Term, anchors: dict, substitute, protected: frozenset[str]) -> tuple[Term, tuple[str, ...]]:
    kept = {name: theorem for name, theorem in anchors.items() if name not in protected}
    rewritten = substitute(term, kept)
    body = rewritten.formula.right
    prelude = trace(rewritten) if rewritten.rule != "Eq.refl" else ()
    return body, prelude


def _bounded_verdict(kind: str, members: tuple[RealForm, ...], binder: str, predicate: Pred) -> tuple[bool, RealForm | None]:
    if kind == "ex":
        saw_open = False
        for member in members:
            try:
                ok = _holds(predicate, binder, member)
            except _OpenPredicate:
                saw_open = True
                continue
            if ok:
                return True, member
        if saw_open:
            raise _OpenPredicate()
        return False, None
    failed: RealForm | None = None
    for member in members:
        if not _holds(predicate, binder, member):
            if failed is None:
                failed = member
    if failed is not None:
        return False, failed
    return True, None


def _holds(predicate: Pred, binder: str, member: RealForm) -> bool:
    left = _form_of(predicate.left, {binder: member})
    right = _form_of(predicate.right, {binder: member})
    if predicate.op == "eq":
        return left == right
    direction = compare_reals(left, right)
    if direction == "open":
        raise _OpenPredicate()
    return direction in {"lt", "eq"}


def _form_of(term: Term, env: dict[str, RealForm]) -> RealForm:
    if isinstance(term, IntLit):
        return real_of_rat(Ratio(term.n, 1)).form
    if isinstance(term, Var):
        if term.name in env:
            return env[term.name]
        raise _FreeVariable()
    if not isinstance(term, App):
        raise _FreeVariable()
    if contains_set(term):
        raise NotExact("a set does not enter this quantifier")
    if term.op == "sqrt":
        return _sqrt_of_form(_form_of(term.args[0], env))
    if term.op == "root":
        from pgi.math.real import form_of_algebraic

        if len(term.args) < 4 or not all(isinstance(arg, IntLit) for arg in term.args):
            raise NotExact("this algebraic number stays outside")
        values = tuple(arg.n for arg in term.args)
        return form_of_algebraic(values[2:-1], values[-1], Ratio(values[0], values[1]))
    if term.op == "neg":
        return _neg_form(_form_of(term.args[0], env))
    if len(term.args) != 2:
        raise NotExact("this predicate is outside this quantifier")
    left = _form_of(term.args[0], env)
    right = _form_of(term.args[1], env)
    if term.op == "add":
        return _add_forms(left, right)
    if term.op == "sub":
        return _sub_forms(left, right)
    if term.op == "mul":
        return _mul_forms(left, right)
    if term.op == "div":
        return _div_form(left, right)
    raise NotExact("this predicate is outside this quantifier")


def _justified_quant(theorem: QuantTheorem) -> bool:
    if not _members_ok(theorem.members):
        return False
    if theorem.kind not in {"all", "ex"} or not theorem.binder:
        return False
    try:
        if theorem.mode == "bounded":
            return _justified_bounded(theorem)
        if theorem.mode == "uniform":
            return _justified_uniform(theorem)
        if theorem.mode == "witness":
            return _justified_witness(theorem)
        if theorem.mode == "least":
            return _justified_least(theorem)
        if theorem.mode == "refute":
            return _justified_refute(theorem)
    except (NotExact, _FreeVariable, _OpenPredicate, KernelError):
        return False
    return False


def _justified_bounded(theorem: QuantTheorem) -> bool:
    if theorem.predicate is None or theorem.bound is not None:
        return False
    holds, witness = _bounded_verdict(theorem.kind, theorem.members, theorem.binder, theorem.predicate)
    if theorem.holds != holds or theorem.witness != witness:
        return False
    return theorem.rule == _bounded_rule_name(theorem.kind, holds)


def _justified_uniform(theorem: QuantTheorem) -> bool:
    predicate = theorem.predicate
    if predicate is None or theorem.members or theorem.bound is not None:
        return False
    if not _reflexive(predicate, theorem.binder):
        return False
    if theorem.kind == "all":
        return theorem.holds and theorem.witness is None and theorem.rule == "Ball.holds"
    if theorem.kind != "ex" or not theorem.holds or theorem.rule != "Bex.holds":
        return False
    zero = _zero()
    return theorem.witness == zero and _holds(predicate, theorem.binder, zero)


def _justified_witness(theorem: QuantTheorem) -> bool:
    predicate = theorem.predicate
    if predicate is None or predicate.op != "eq" or theorem.kind != "ex":
        return False
    if theorem.members or theorem.bound is not None or not theorem.holds or theorem.rule != "Bex.holds":
        return False
    side = _closed_side(predicate, theorem.binder)
    if side is None or theorem.witness is None:
        return False
    return _form_of(side, {}) == theorem.witness


def _justified_least(theorem: QuantTheorem) -> bool:
    if theorem.predicate is not None or theorem.witness is not None or theorem.bound is None:
        return False
    if theorem.kind != "all" or not theorem.holds or theorem.rule != "Ball.least":
        return False
    return _canonical(theorem.bound) and theorem.bound in theorem.members


def _justified_refute(theorem: QuantTheorem) -> bool:
    if theorem.predicate is not None or theorem.bound is None or theorem.witness is None:
        return False
    if theorem.kind != "all" or theorem.holds or theorem.rule != "Ball.fails":
        return False
    if theorem.bound in theorem.members or not _canonical(theorem.bound):
        return False
    found = maximum(theorem.members)
    if found is None or found != theorem.witness:
        return False
    return compare_reals(theorem.bound, found) == "gt"


def _justified_complete(theorem: CompleteTheorem) -> bool:
    if theorem.rule != "Ball.complete" or not _members_ok(theorem.members):
        return False
    if not theorem.members or not _canonical(theorem.witness):
        return False
    found = maximum(theorem.members)
    return found is not None and found == theorem.witness


def _members_ok(members: tuple[RealForm, ...]) -> bool:
    if not all(_canonical(form) for form in members):
        return False
    return members == canonical(members)


def _bounded_rule_name(kind: str, holds: bool) -> str:
    if kind == "all":
        return "Ball.holds" if holds else "Ball.fails"
    return "Bex.holds" if holds else "Bex.fails"


def _bounded_rule(
    kind: str,
    holds: bool,
    binder: str,
    shown: str,
    relation: str,
    theorem: QuantTheorem,
    prelude: tuple[str, ...],
) -> Rule:
    if kind == "all":
        atom = f"all({binder} in {shown}, {relation})" if holds else f"not_all({binder} in {shown}, {relation})"
        rule_id = "math.ball" if holds else "math.not_ball"
        title = f"all {binder} in {shown}. {relation}" if holds else f"not (all {binder} in {shown}. {relation})"
    else:
        atom = f"ex({binder} in {shown}, {relation})" if holds else f"not_ex({binder} in {shown}, {relation})"
        rule_id = "math.bex" if holds else "math.not_bex"
        title = f"ex {binder} in {shown}. {relation}" if holds else f"not (ex {binder} in {shown}. {relation})"
    return _plain_rule(rule_id, title, atom, theorem, prelude)


def _plain_rule(rule_id: str, title: str, atom: str, theorem: QuantTheorem, prelude: tuple[str, ...]) -> Rule:
    return Rule(
        id=rule_id,
        layer="base",
        stage="quantity",
        title=title,
        produces=atom,
        detail_lines=(*prelude, *theorem.detail),
    )


def _empty_detail(kind: str) -> tuple[str, ...]:
    if kind == "all":
        return (
            "Isabelle ball_empty: the universal over the empty set holds.",
            "Isabelle ball_simps records the same empty case.",
            "The body is not evaluated.",
        )
    return (
        "Isabelle bex_empty: the existential over the empty set fails.",
        "Isabelle bex_simps records the same empty case.",
        "The body is not evaluated.",
    )


def _bounded_detail(kind: str, holds: bool, witness: RealForm | None) -> tuple[str, ...]:
    if kind == "all" and holds:
        return (
            "Isabelle Ball: a bounded universal is the implication from membership.",
            "Isabelle ballI: the predicate was checked at every member.",
        )
    if kind == "all":
        shown = show_form(witness) if witness is not None else ""
        return (
            "Isabelle ball_simps: the negation of a bounded universal is a bounded existential of the negation.",
            f"The counterexample is {shown}.",
            "Isabelle bexI: the counterexample is a member and the predicate fails there.",
        )
    if holds:
        shown = show_form(witness) if witness is not None else ""
        return (
            "Isabelle bexI: the witness is a member and the predicate holds there.",
            f"The witness is {shown}.",
            "Core Lean 4.36 resolves Exists.",
        )
    return (
        "Isabelle bex_simps: the negation of a bounded existential is a bounded universal of the negation.",
        "Isabelle ballI: the predicate fails at every member.",
    )


def _uniform_all_detail(op: str) -> tuple[str, ...]:
    if op == "le":
        return (
            "Isabelle All: a universal is a predicate true of every element.",
            "Isabelle allI: a proof for an arbitrary element yields the universal.",
            "Isabelle axiom refl gives x = x, and Real.thy defines x <= y as x < y or x = y.",
        )
    return (
        "Isabelle All: a universal is a predicate true of every element.",
        "Isabelle allI: a proof for an arbitrary element yields the universal.",
        "Isabelle axiom refl: t = t.",
    )


def _uniform_ex_detail(op: str) -> tuple[str, ...]:
    reason = "Isabelle axiom refl: t = t."
    if op == "le":
        reason = "The witness satisfies x <= x because x = x, and Real.thy defines x <= y as x < y or x = y."
    return (
        "Isabelle exI: a witness of the predicate proves the existential.",
        "The witness is 0.",
        reason,
        "Core Lean 4.36 resolves Exists.",
    )


def _complete_detail(members: tuple[RealForm, ...], found: RealForm) -> tuple[str, ...]:
    lines = [
        "Isabelle complete_real: a nonempty set of reals that is bounded above has a least upper bound.",
        "Isabelle ex_in_conv: the enumeration is nonempty because it has a member.",
        "Isabelle ballI and Max_ge: every member is less than or equal to the maximum.",
        "Isabelle bexI and Max_in: the maximum is a member.",
        "Isabelle Max_le_iff: the maximum is less than or equal to an upper bound exactly when every member is. This direction uses bspec at that member.",
        "Isabelle bspec: a bounded universal applies to each member.",
        "Isabelle cSup_eq_maximum: a member that bounds the set above is the supremum.",
        "Isabelle cSup_eq_Max: the supremum of a finite nonempty set is its maximum.",
        "The proof for an arbitrary set stays outside this rule.",
        f"The witness is the class {show_form(found)}."
        if found.terms or found.towers or found.nests or found.pairs or found.deeps or found.highs or found.peaks or found.crests or found.summits or found.apexes or found.shells or found.folds
        else f"The witness is {show_form(found)}.",
    ]
    if len(members) == 1:
        lines.append("Isabelle cSup_singleton: the supremum of a singleton is its element.")
    return tuple(lines)


def _reflexive(predicate: Pred, binder: str) -> bool:
    return (
        isinstance(predicate.left, Var)
        and isinstance(predicate.right, Var)
        and predicate.left.name == binder
        and predicate.right.name == binder
        and predicate.op in {"le", "eq"}
    )


def _closed_side(predicate: Pred, binder: str) -> Term | None:
    if isinstance(predicate.left, Var) and predicate.left.name == binder and binder not in _frees(predicate.right):
        return predicate.right
    if isinstance(predicate.right, Var) and predicate.right.name == binder and binder not in _frees(predicate.left):
        return predicate.left
    return None


def _pred_text(predicate: Pred) -> str:
    symbol = "<=" if predicate.op == "le" else "="
    return f"{pretty(predicate.left)} {symbol} {pretty(predicate.right)}"


def _zero() -> RealForm:
    return real_of_rat(Ratio(0, 1)).form


def _frees(term: Term) -> set[str]:
    if isinstance(term, Var):
        return {term.name}
    if isinstance(term, App):
        found: set[str] = set()
        for arg in term.args:
            found |= _frees(arg)
        return found
    return set()


def _split_name(text: str) -> tuple[str, str] | None:
    parts = text.strip().split(None, 1)
    if not parts or not _is_name(parts[0]):
        return None
    rest = parts[1].strip() if len(parts) > 1 else ""
    return parts[0], rest


def _is_name(token: str) -> bool:
    if not token:
        return False
    if not (token[0].isalpha() or token[0] == "_"):
        return False
    return all(char.isalnum() or char == "_" for char in token)


def _strip_wrap(text: str) -> str:
    body = text.strip()
    if len(body) >= 2 and body[0] == "(" and body[-1] == ")" and _wraps(body):
        return body[1:-1].strip()
    return body


def _wraps(text: str) -> bool:
    depth = 0
    for index, char in enumerate(text):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index == len(text) - 1
    return False


def _split_cmp(text: str) -> tuple[str, str, str] | None:
    depth = 0
    le_at: int | None = None
    eq_at: int | None = None
    index = 0
    while index < len(text):
        char = text[index]
        if char in "{(":
            depth += 1
            index += 1
            continue
        if char in "})":
            depth -= 1
            index += 1
            continue
        if depth == 0 and text.startswith("<=", index):
            if le_at is not None:
                return None
            le_at = index
            index += 2
            continue
        if depth == 0 and text.startswith("-->", index):
            index += 3
            continue
        if depth == 0 and char == "=":
            if eq_at is not None:
                return None
            eq_at = index
        index += 1
    if le_at is not None and eq_at is not None:
        return None
    if le_at is not None:
        return "le", text[:le_at], text[le_at + 2 :]
    if eq_at is not None:
        return "eq", text[:eq_at], text[eq_at + 1 :]
    return None


def _split_token(text: str, token: str) -> tuple[str, str] | None:
    depth = 0
    found: int | None = None
    index = 0
    while index < len(text):
        char = text[index]
        if char in "{(":
            depth += 1
            index += 1
            continue
        if char in "})":
            depth -= 1
            index += 1
            continue
        if depth == 0 and text.startswith(token, index):
            if found is not None:
                return None
            found = index
            index += len(token)
            continue
        index += 1
    if found is None:
        return None
    return text[:found].strip(), text[found + len(token) :].strip()


def _note(text: str) -> Rule:
    return Rule(
        id="math.open",
        layer="base",
        stage="check",
        title=text,
        produces=f"open({text})",
        detail_lines=(text,),
    )
