"""Order rays and the set of every real.

Isabelle `Set_Interval.thy` defines `atMost` as `{..u} = {x. x <= u}` and
`atLeast` as `{l..} = {x. l <= x}`. Membership is `atMost_iff` and
`atLeast_iff`. Inclusion of two rays of the same kind is `atMost_subset_iff`
or `atLeast_subset_iff`, and equality of those rays is `atMost_eq_iff` or
`atLeast_eq_iff`. `real` is a `linordered_field`, hence `no_top` and `no_bot`,
so `infinite_Iic` and `infinite_Ici` say those rays are not finite, and
`not_UNIV_eq_Iic` and `not_UNIV_eq_Ici` separate them from `UNIV`.

`UNIV_def` is `{x. True}`. On this carrier `{x. x = x}` and `{x. x <= x}` are
that set: a real is related to itself. `subset_UNIV` puts every set inside it.
`infinite_UNIV_char_0` says the carrier is not a finite enumeration.

`less_add_one` supplies the witness one above or one below a bound. The kernel
checks that shift with the same real comparison it already uses.

`Int_atMost` meets two down-rays. `atMost_Int_atLeast` meets a down-ray and an
up-ray at the same bound and returns the singleton. `atLeastatMost_empty_iff`
makes that meet empty when the lower bound fails to sit at or below the upper
bound. A proper overlap is the two-sided interval named by those rays:
`atLeastAtMost` is `{l..u} = {l..} ∩ {..u}`, `greaterThanAtMost` is
`{l<..u}`, `atLeastLessThan` is `{l..<u}`, and `greaterThanLessThan` is
`{l<..<u}`. The same closed bound stays the singleton. `Int_UNIV_left` and
`Int_UNIV_right` absorb the carrier.

`cSup_atMost` says the supremum of `{..x}` is `x`. The kernel checks the two
premises on a down-ray: `atMost_iff` and `order_refl` make the bound a member,
and `bdd_above_Iic` makes that same bound an upper bound. `cSup_eq_maximum`
then names the bound as the supremum. That case contains its bound, so the
Archimedean bisection stays outside that rule.

`lessThan` is `{..<u} = {x. x < u}`. The bound is not a member, by
`less_irrefl`. The set is nonempty by `less_add_one`, and `bdd_above_Iio`
says the bound is an upper bound. The supremum is built by the bisection in
the proof of `complete_real`: `of_int_floor_le` gives a rational that fails to
be an upper bound, `le_of_int_ceiling` gives a rational that is one, and each
midpoint keeps the half on which that predicate changes. The width is the
initial gap divided by a power of two. `reals_Archimedean2` puts that gap
below 1. The endpoint sequences are Cauchy, `eq_Real` identifies them, and
`le_RealI` with `Real_leI` identifies that real with the bound.
`cSup_lessThan` is the name of that fact. `greaterThan` is not bounded above.

A closed upper end of an interval is a member, so `cSup_eq_maximum` names it.
`cSup_atLeastAtMost` needs the lower bound at or below the upper bound.
`cSup_greaterThanAtMost` needs the lower bound strictly below. An open upper
end is not a member. `cSup_atLeastLessThan` and `cSup_greaterThanLessThan`
name that supremum, and the kernel builds it by the same bisection, because
membership in the interval decides the upper-bound predicate.

A boolean connective inside one predicate reduces by the Collect lemmas in
`Set.thy`. `Collect_conj_eq` meets the two sides, and `Collect_conj_eq2`
meets the two separations of one finite domain. `Collect_disj_eq` unions two
sides when both are finite enumerations. `Collect_neg_eq` sends the
complement of a ray to the opposite ray, by `Compl_atMost`, `Compl_atLeast`,
`Compl_lessThan`, and `Compl_greaterThan`. `Compl_UNIV_eq` sends the
complement of the set of every real to the empty set. A connective whose
sides this kernel cannot settle stays outside. Implication stays outside.

Core Lean 4.36.0, with no imports, does not resolve `Set.Iic`, `Set.Ici`,
`Set.Iio`, `Set.Ioi`, or `Set.univ`. This module does not import Lean or
Isabelle, and it does not use Octave.
"""

from __future__ import annotations

from dataclasses import dataclass

from pgi.math.collect import CollectForm, _term_of_form
from pgi.math.kernel import KernelError, NotExact
from pgi.math.quant import Pred
from pgi.math.rational import Ratio
from pgi.math.real import (
    RealForm,
    _add_forms,
    _canonical,
    _enclose,
    _qadd,
    _qcmp,
    _qdiv,
    _qsub,
    _scale,
    _sub_forms,
    compare_reals,
    eval_real,
    real_of_rat,
    real_trace,
    show_form,
    show_ratio,
)
from pgi.math.set import (
    SetTheorem,
    SupTheorem,
    _quantity,
    canonical,
    contains_set,
    eval_set,
    set_empty,
    set_insert,
    set_inter,
    set_sup,
    set_union,
    set_value_rule,
)
from pgi.math.syntax import App, Term, Var, pretty
from pgi.model import Rule

_OPEN_SET = "this set is not settled"
_OPEN_QUANT = "this quantifier is not settled"
_NOT_FINITE = "this comprehension is not a finite enumeration"
_UNBOUNDED = "this set is not bounded above"
_INTERVAL_KINDS = frozenset({
    "atLeastAtMost",
    "greaterThanAtMost",
    "atLeastLessThan",
    "greaterThanLessThan",
})
_OPEN_UPPER = frozenset({"atLeastLessThan", "greaterThanLessThan"})
_OPEN_LOWER = frozenset({"greaterThanAtMost", "greaterThanLessThan"})


@dataclass(frozen=True)
class Ray:
    kind: str
    bound: RealForm | None
    form: CollectForm


@dataclass(frozen=True)
class RayTheorem:
    kind: str
    bound: RealForm | None
    form: CollectForm
    rule: str
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _ray_ok(self.kind, self.bound, self.form, self.rule):
            raise KernelError(f"{self.rule} does not justify this set")


@dataclass(frozen=True)
class RaySubsetTheorem:
    left_kind: str
    left_bound: RealForm | None
    right_kind: str
    right_bound: RealForm | None
    finite: tuple[RealForm, ...] | None
    holds: bool
    witness: RealForm | None
    rule: str
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _subset_ok(self):
            raise KernelError(f"{self.rule} does not justify this inclusion")


@dataclass(frozen=True)
class RayEqTheorem:
    left_kind: str
    left_bound: RealForm | None
    right_kind: str
    right_bound: RealForm | None
    rule: str
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.rule != "Ray.eq" or not _rays_equal(self.left_kind, self.left_bound, self.right_kind, self.right_bound):
            raise KernelError("Ray.eq does not justify this equality")


@dataclass(frozen=True)
class RayQuantTheorem:
    kind: str
    holds: bool
    binder: str
    ray_kind: str
    bound: RealForm | None
    predicate: Pred
    witness: RealForm | None
    rule: str
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _quant_ok(self):
            raise KernelError(f"{self.rule} does not justify this quantifier")


@dataclass(frozen=True)
class RayMeetTheorem:
    left_kind: str
    left_bound: RealForm | None
    left_members: tuple[RealForm, ...]
    right_kind: str
    right_bound: RealForm | None
    right_members: tuple[RealForm, ...]
    result_kind: str
    result_bound: RealForm | None
    result_members: tuple[RealForm, ...]
    rule: str
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _meet_ok(self):
            raise KernelError(f"{self.rule} does not justify this intersection")


@dataclass(frozen=True)
class RaySupTheorem:
    form: RealForm
    source: CollectForm
    rule: str
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _sup_ok(self):
            raise KernelError(f"{self.rule} does not justify this least upper bound")


@dataclass(frozen=True)
class BisectTheorem:
    form: RealForm
    source: CollectForm
    rule: str
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _bisect_ok(self):
            raise KernelError(f"{self.rule} does not justify this least upper bound")


@dataclass(frozen=True)
class Interval:
    kind: str
    lower: RealForm
    upper: RealForm


@dataclass(frozen=True)
class IntervalTheorem:
    kind: str
    lower: RealForm
    upper: RealForm
    rule: str
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _interval_ok(self):
            raise KernelError(f"{self.rule} does not justify this interval")


@dataclass(frozen=True)
class IntervalSupTheorem:
    form: RealForm
    kind: str
    lower: RealForm
    upper: RealForm
    rule: str
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _interval_sup_ok(self):
            raise KernelError(f"{self.rule} does not justify this least upper bound")


@dataclass(frozen=True)
class ConnectiveTheorem:
    binder: str
    domain: Term
    predicate: Term
    rule: str
    kind: str
    bound: RealForm | None
    members: tuple[RealForm, ...]
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _connective_ok(self):
            raise KernelError(f"{self.rule} does not justify this comprehension")


def interpret(term: Term) -> tuple[object, tuple[str, ...]]:
    try:
        value = eval_set(term)
    except NotExact as exc:
        reduced = _from_intersection(term)
        if reduced is not None:
            return reduced
        reduced = _from_sup(term)
        if reduced is not None:
            return reduced
        if _connective_collect(term):
            return _from_connective(term)
        raise exc
    return value, ()


def ray_sup_rule(origin: Term, theorem: RaySupTheorem | BisectTheorem, prelude: tuple[str, ...] = ()) -> Rule:
    ray = classify(theorem.source)
    if ray is None:
        raise NotExact(_NOT_FINITE)
    lines = (*prelude, *_bound_trace(ray), *theorem.detail)
    return _quantity(origin, theorem.form, lines)


def ray_complete_rule(shown: str, form: CollectForm, prelude: tuple[str, ...] = ()) -> tuple[Rule, ...]:
    theorem = _ray_supremum(form)
    ray = classify(form)
    if ray is None:
        raise NotExact(_NOT_FINITE)
    lines = (*prelude, *_bound_trace(ray), *theorem.detail)
    bound = show_form(theorem.form)
    kind_name = "lessThan" if ray.kind == "lessThan" else "atMost"
    return (
        Rule(
            id="math.complete",
            layer="base",
            stage="quantity",
            title=f"{bound} is the least upper bound of {shown}",
            produces=f"complete({kind_name}({bound}))",
            detail_lines=lines,
        ),
    )


def ray_value_rule(origin: Term, form: CollectForm, prelude: tuple[str, ...] = ()) -> Rule | None:
    ray = classify(form)
    if ray is None:
        return None
    theorem = RayTheorem(ray.kind, ray.bound, ray.form, _ray_rule(ray.kind), _ray_detail(ray))
    lines = (*prelude, *_bound_trace(ray), *theorem.detail)
    title = pretty(origin)
    if ray.kind == "univ":
        return Rule(
            id="math.univ",
            layer="base",
            stage="quantity",
            title=f"{title} is the set of every real",
            produces="univ",
            detail_lines=lines,
        )
    shown = show_form(ray.bound)
    return Rule(
        id=f"math.{ray.kind}",
        layer="base",
        stage="quantity",
        title=f"{title} = {ray.kind}({shown})",
        produces=f"{ray.kind}({shown})",
        detail_lines=lines,
    )


def interval_value_rule(origin: Term, interval: Interval, prelude: tuple[str, ...] = ()) -> Rule:
    detail = _interval_detail(interval)
    IntervalTheorem(interval.kind, interval.lower, interval.upper, f"Set.{interval.kind}", detail)
    shown = _interval_atom(interval)
    lines = (*prelude, *detail)
    title = pretty(origin)
    return Rule(
        id=f"math.{interval.kind}",
        layer="base",
        stage="quantity",
        title=f"{title} = {shown}",
        produces=shown,
        detail_lines=lines,
    )


def interval_sup_rule(origin: Term, theorem: IntervalSupTheorem, prelude: tuple[str, ...] = ()) -> Rule:
    lines = (*prelude, *theorem.detail)
    return _quantity(origin, theorem.form, lines)


def interval_complete_rule(shown: str, interval: Interval, prelude: tuple[str, ...] = ()) -> tuple[Rule, ...]:
    theorem = _interval_supremum(interval)
    lines = (*prelude, *theorem.detail)
    bound = show_form(theorem.form)
    atom = _interval_atom(interval)
    return (
        Rule(
            id="math.complete",
            layer="base",
            stage="quantity",
            title=f"{bound} is the least upper bound of {shown}",
            produces=f"complete({atom})",
            detail_lines=lines,
        ),
    )


def ray_subset_rule(
    left: Term,
    right: Term,
    left_value: object,
    right_value: object,
    prelude: tuple[str, ...] = (),
) -> Rule:
    if not isinstance(left_value, CollectForm):
        raise NotExact("this expression is not a finite set")
    left_ray = _require_ray(left_value)
    right_kind, right_bound, finite = _inclusion_target(right_value)
    holds, witness = _subset_verdict(left_ray.kind, left_ray.bound, right_kind, right_bound, finite, _OPEN_SET)
    rule = "Ray.subset" if holds else "Ray.not_subset"
    detail = _subset_detail(holds, left_ray.kind, right_kind, witness)
    theorem = RaySubsetTheorem(
        left_ray.kind,
        left_ray.bound,
        right_kind,
        right_bound,
        finite,
        holds,
        witness,
        rule,
        detail,
    )
    return _subset_atom(left, right, holds, (*prelude, *theorem.detail))


def ray_equality_rules(title: str, left_value: object, right_value: object, prelude: tuple[str, ...] = ()) -> tuple[Rule, ...]:
    try:
        left_ray = classify(left_value) if isinstance(left_value, CollectForm) else None
        right_ray = classify(right_value) if isinstance(right_value, CollectForm) else None
    except NotExact as exc:
        return (_note(str(exc)),)
    if isinstance(left_value, CollectForm) and isinstance(right_value, CollectForm):
        if left_ray is None or right_ray is None:
            return (_note("this comprehension is not settled"),)
        if _rays_equal(left_ray.kind, left_ray.bound, right_ray.kind, right_ray.bound):
            theorem = RayEqTheorem(left_ray.kind, left_ray.bound, right_ray.kind, right_ray.bound, "Ray.eq", _eq_detail(left_ray.kind))
            return (
                Rule(
                    id="math.set.eq",
                    layer="base",
                    stage="quantity",
                    title=title,
                    produces=f"identity({title})",
                    detail_lines=(*prelude, *theorem.detail),
                ),
            )
        try:
            witness = _inequality_witness(left_ray.kind, left_ray.bound, right_ray.kind, right_ray.bound, _OPEN_SET)
        except NotExact as exc:
            return (_note(str(exc)),)
        return (_note(f"{title} is not a theorem. {show_form(witness)} is a member of one side and is outside the other."),)
    finite = left_value if isinstance(left_value, SetTheorem) else right_value if isinstance(right_value, SetTheorem) else None
    form = left_value if isinstance(left_value, CollectForm) else right_value if isinstance(right_value, CollectForm) else None
    ray = left_ray if isinstance(left_value, CollectForm) else right_ray
    if not isinstance(finite, SetTheorem) or not isinstance(form, CollectForm) or ray is None:
        return (_note("this comprehension is not settled"),)
    try:
        witness = _outside_finite(ray.kind, ray.bound, finite.members, _OPEN_SET)
    except NotExact as exc:
        return (_note(str(exc)),)
    shown = show_form(witness)
    return (_note(f"{title} is not a theorem. {shown} is a member of the order ray and is outside the finite enumeration."),)


def ray_quantifier_rules(
    kind: str,
    binder: str,
    shown: str,
    predicate: Pred,
    form: CollectForm,
    prelude: tuple[str, ...] = (),
) -> tuple[Rule, ...]:
    ray = _require_ray(form)
    holds, witness, rule, shape = _quant_verdict(kind, ray.kind, ray.bound, predicate, binder, _OPEN_QUANT)
    relation = _pred_text(predicate)
    detail = _quant_detail(kind, holds, ray.kind, witness, shape)
    theorem = RayQuantTheorem(kind, holds, binder, ray.kind, ray.bound, predicate, witness, rule, detail)
    return (_quant_atom(kind, holds, binder, shown, relation, (*prelude, *theorem.detail)),)


def classify(form: CollectForm) -> Ray | None:
    if _reflexive(form):
        return Ray("univ", None, form)
    if form.relation == "lt":
        return _strict_ray(form)
    if form.relation != "le":
        return None
    if _is_binder(form.left, form.binder) and not _mentions(form.right, form.binder):
        if contains_set(form.right):
            raise NotExact("a set does not enter this comprehension")
        return Ray("atMost", eval_real(form.right).form, form)
    if _is_binder(form.right, form.binder) and not _mentions(form.left, form.binder):
        if contains_set(form.left):
            raise NotExact("a set does not enter this comprehension")
        return Ray("atLeast", eval_real(form.left).form, form)
    return None


def _strict_ray(form: CollectForm) -> Ray | None:
    if _is_binder(form.left, form.binder) and _is_binder(form.right, form.binder):
        raise NotExact(
            "Isabelle less_irrefl: no real is strictly below itself. "
            "The comprehension is empty. complete_real assumes a member."
        )
    if _is_binder(form.left, form.binder) and not _mentions(form.right, form.binder):
        if contains_set(form.right):
            raise NotExact("a set does not enter this comprehension")
        return Ray("lessThan", eval_real(form.right).form, form)
    if _is_binder(form.right, form.binder) and not _mentions(form.left, form.binder):
        if contains_set(form.left):
            raise NotExact("a set does not enter this comprehension")
        return Ray("greaterThan", eval_real(form.left).form, form)
    return None


_OUTSIDE = "this boolean connective stays outside this rule"
_CONJ = "Isabelle Collect_conj_eq: {x. P x and Q x} = {x. P x} inter {x. Q x}."
_CONJ2 = "Isabelle Collect_conj_eq2: {x in A. P x and Q x} = {x in A. P x} inter {x in A. Q x}."
_DISJ = "Isabelle Collect_disj_eq: {x. P x or Q x} = {x. P x} union {x. Q x}."
_NEG = "Isabelle Collect_neg_eq: {x. not P x} = - {x. P x}."
_COMPLEMENT = {
    "atMost": (
        "greaterThan",
        "Isabelle Compl_atMost: the complement of an atMost ray is the greaterThan ray at the same bound.",
    ),
    "greaterThan": (
        "atMost",
        "Isabelle Compl_greaterThan: the complement of a greaterThan ray is the atMost ray at the same bound.",
    ),
    "atLeast": (
        "lessThan",
        "Isabelle Compl_atLeast: the complement of an atLeast ray is the lessThan ray at the same bound.",
    ),
    "lessThan": (
        "atLeast",
        "Isabelle Compl_lessThan: the complement of a lessThan ray is the atLeast ray at the same bound.",
    ),
}


def _connective_collect(term: Term) -> bool:
    if not isinstance(term, App) or term.op != "collect" or len(term.args) != 3:
        return False
    predicate = term.args[2]
    return isinstance(predicate, App) and predicate.op in {"and", "or", "not", "implies"}


def _from_connective(term: Term) -> tuple[object, tuple[str, ...]]:
    binder_term, domain, predicate = term.args
    if not isinstance(binder_term, Var) or not isinstance(predicate, App):
        raise NotExact(_OUTSIDE)
    value, detail = _reduce_connective(binder_term.name, domain, predicate)
    kind, bound, members = _connective_shape(value)
    ConnectiveTheorem(
        binder_term.name,
        domain,
        predicate,
        _connective_rule(domain, predicate),
        kind,
        bound,
        members,
        detail,
    )
    return value, detail


def _reduce_connective(binder: str, domain: Term, predicate: Term) -> tuple[object, tuple[str, ...]]:
    if predicate.op == "and":
        return _reduce_and(binder, domain, predicate)
    if predicate.op == "or":
        return _reduce_or(binder, domain, predicate)
    if predicate.op == "not":
        return _reduce_not(binder, domain, predicate)
    raise NotExact(_OUTSIDE)


def _reduce_and(binder: str, domain: Term, predicate: Term) -> tuple[object, tuple[str, ...]]:
    left, right = _two_atoms(predicate)
    left_value = eval_set(_side_collect(binder, domain, left))
    right_value = eval_set(_side_collect(binder, domain, right))
    if isinstance(left_value, SetTheorem) and isinstance(right_value, SetTheorem):
        line = _CONJ if _is_type(domain) else _CONJ2
        return set_inter(left_value, right_value), (line,)
    if not _is_type(domain):
        raise NotExact(_OUTSIDE)
    try:
        value, detail = _combine(left_value, right_value)
    except NotExact as exc:
        if str(exc) == _NOT_FINITE:
            raise NotExact(_OUTSIDE) from exc
        raise
    return value, (_CONJ, *detail)


def _reduce_or(binder: str, domain: Term, predicate: Term) -> tuple[object, tuple[str, ...]]:
    if not _is_type(domain):
        raise NotExact(_OUTSIDE)
    left, right = _two_atoms(predicate)
    left_value = eval_set(_side_collect(binder, domain, left))
    right_value = eval_set(_side_collect(binder, domain, right))
    if isinstance(left_value, SetTheorem) and isinstance(right_value, SetTheorem):
        return set_union(left_value, right_value), (_DISJ,)
    raise NotExact(_OUTSIDE)


def _reduce_not(binder: str, domain: Term, predicate: Term) -> tuple[object, tuple[str, ...]]:
    if not _is_type(domain) or len(predicate.args) != 1 or not _atomic_comparison(predicate.args[0]):
        raise NotExact(_OUTSIDE)
    inner = predicate.args[0]
    if not isinstance(inner, App) or len(inner.args) != 2:
        raise NotExact(_OUTSIDE)
    ray = classify(CollectForm(binder, inner.op, inner.args[0], inner.args[1]))
    if ray is None:
        raise NotExact(_OUTSIDE)
    if ray.kind == "univ":
        return set_empty(), (
            _NEG,
            "The predicate holds at every real, so the comprehension is UNIV.",
            "Isabelle Compl_UNIV_eq: - UNIV = {}.",
        )
    found = _COMPLEMENT.get(ray.kind)
    if found is None or ray.bound is None:
        raise NotExact(_OUTSIDE)
    kind, line = found
    return _synthetic(kind, ray.bound), (_NEG, line)


def _two_atoms(predicate: Term) -> tuple[Term, Term]:
    if len(predicate.args) != 2 or not _atomic_comparison(predicate.args[0]) or not _atomic_comparison(predicate.args[1]):
        raise NotExact(_OUTSIDE)
    return predicate.args[0], predicate.args[1]


def _atomic_comparison(term: Term) -> bool:
    return isinstance(term, App) and term.op in {"le", "eq", "lt"} and len(term.args) == 2


def _side_collect(binder: str, domain: Term, predicate: Term) -> Term:
    return App("collect", (Var(binder), domain, predicate))


def _is_type(domain: Term) -> bool:
    return isinstance(domain, App) and domain.op == "type" and not domain.args


def _connective_rule(domain: Term, predicate: Term) -> str:
    if predicate.op == "and" and not _is_type(domain):
        return "Collect.conj2"
    if predicate.op == "and":
        return "Collect.conj"
    if predicate.op == "or":
        return "Collect.disj"
    if predicate.op == "not":
        return "Collect.neg"
    raise KernelError("this boolean connective stays outside this rule")


def _connective_shape(value: object) -> tuple[str, RealForm | None, tuple[RealForm, ...]]:
    if isinstance(value, Interval):
        return value.kind, value.lower, (value.upper,)
    if isinstance(value, SetTheorem):
        return "finite", None, value.members
    if isinstance(value, CollectForm):
        ray = classify(value)
        if ray is None:
            raise NotExact(_OUTSIDE)
        return ray.kind, ray.bound, ()
    raise NotExact(_OUTSIDE)


def _connective_ok(theorem: ConnectiveTheorem) -> bool:
    if not theorem.binder or theorem.rule != _connective_rule(theorem.domain, theorem.predicate):
        return False
    if not isinstance(theorem.predicate, App):
        return False
    try:
        value, _detail = _reduce_connective(theorem.binder, theorem.domain, theorem.predicate)
        kind, bound, members = _connective_shape(value)
    except (NotExact, KernelError):
        return False
    return kind == theorem.kind and bound == theorem.bound and members == theorem.members


def _from_sup(term: Term) -> tuple[object, tuple[str, ...]] | None:
    if not isinstance(term, App) or term.op != "sup" or len(term.args) != 1:
        return None
    value, lines = interpret(term.args[0])
    if isinstance(value, SetTheorem):
        return set_sup(value), lines
    if isinstance(value, CollectForm):
        return _ray_supremum(value), lines
    if isinstance(value, Interval):
        return _interval_supremum(value), lines
    return None


def _ray_supremum(form: CollectForm) -> RaySupTheorem | BisectTheorem:
    ray = classify(form)
    if ray is None:
        raise NotExact(_NOT_FINITE)
    if ray.kind == "lessThan":
        if ray.bound is None:
            raise NotExact(_NOT_FINITE)
        detail = _bisect_detail(ray.bound)
        return BisectTheorem(ray.bound, form, "Ray.bisect", detail)
    if ray.kind != "atMost" or ray.bound is None:
        raise NotExact(_unbounded_message(ray))
    detail = _sup_detail(ray.bound)
    return RaySupTheorem(ray.bound, form, "Ray.sup", detail)


def _unbounded_message(ray: Ray) -> str:
    if ray.kind == "atLeast":
        _above(ray.bound, _OPEN_SET)
        return (
            f"{_UNBOUNDED}. Isabelle atLeast_iff and less_add_one give a member strictly above the bound. "
            "Orderings.no_top says a greater real exists. complete_real assumes a set bounded above."
        )
    if ray.kind == "greaterThan":
        _above(ray.bound, _OPEN_SET)
        return (
            f"{_UNBOUNDED}. Isabelle greaterThan_iff and less_add_one give a member strictly above the bound. "
            "Orderings.no_top says a greater real exists. complete_real assumes a set bounded above."
        )
    if ray.kind == "univ":
        _above(_zero(), _OPEN_SET)
        return (
            f"{_UNBOUNDED}. Isabelle UNIV_I and less_add_one give a member strictly above zero. "
            "Orderings.no_top says a greater real exists. complete_real assumes a set bounded above."
        )
    raise NotExact(_NOT_FINITE)


def _sup_detail(bound: RealForm) -> tuple[str, ...]:
    shown = show_form(bound)
    return (
        "Isabelle complete_real: a nonempty set of reals that is bounded above has a least upper bound.",
        "Isabelle atMost_iff and order_refl: the bound is a member, so the set is nonempty.",
        "Isabelle bdd_above_Iic: every member of an atMost ray is at most its bound.",
        "The bound is a member, so any upper bound is at least the bound.",
        "Isabelle cSup_eq_maximum: a member that bounds the set above is the supremum.",
        "Isabelle cSup_atMost: the supremum of an atMost ray is its bound.",
        "The Archimedean bisection in the proof of complete_real stays outside this rule.",
        f"The witness is {shown}.",
    )


def _sup_ok(theorem: RaySupTheorem) -> bool:
    if theorem.rule != "Ray.sup" or not _canonical(theorem.form):
        return False
    try:
        ray = classify(theorem.source)
    except (NotExact, KernelError):
        return False
    return ray is not None and ray.kind == "atMost" and ray.bound == theorem.form


def _bisect_ok(theorem: BisectTheorem) -> bool:
    if theorem.rule != "Ray.bisect" or not _canonical(theorem.form):
        return False
    try:
        ray = classify(theorem.source)
        if ray is None or ray.kind != "lessThan" or ray.bound != theorem.form:
            return False
        _certificate(ray.bound)
    except (NotExact, KernelError):
        return False
    return True


def _bisect_detail(bound: RealForm) -> tuple[str, ...]:
    cut = _certificate(bound)
    shown = show_form(bound)
    member = show_form(cut.member)
    return (
        "Isabelle complete_real: a nonempty set of reals that is bounded above has a least upper bound.",
        "Isabelle lessThan_def: {..<u} = {x. x < u}.",
        "Isabelle lessThan_iff: membership is the strict comparison with the bound.",
        "Isabelle less_irrefl: the bound is not a member of this set.",
        f"Isabelle less_add_one and Orderings.no_bot: {member} is strictly below the bound, so the set is nonempty.",
        "Isabelle bdd_above_Iio: every member of a lessThan ray is strictly below its bound, so the bound is an upper bound.",
        f"P q means every member is at most the rational q. For this ray, P q holds when the bound is at most q.",
        f"Isabelle of_int_floor_le: floor of one below the member is the rational {show_ratio(cut.low)}, and P fails there.",
        f"Isabelle le_of_int_ceiling: the ceiling of the bound is the rational {show_ratio(cut.high)}, and P holds there.",
        "avg is the midpoint. bisect keeps the half on which P changes: a failing midpoint raises the lower end, and a holding midpoint lowers the upper end.",
        f"After {cut.depth} steps the interval is [{show_ratio(cut.left)}, {show_ratio(cut.right)}].",
        f"The width is {show_ratio(cut.width)}, the initial gap {show_ratio(cut.initial)} divided by {2 ** cut.depth}.",
        "Isabelle reals_Archimedean2: for every positive rational r there is a natural number n with the gap over 2^n below r. This certificate uses r = 1.",
        "The lower endpoint stays strictly below the bound, and the upper endpoint stays at or above it.",
        "Isabelle cauchy: both endpoint sequences are Cauchy because that width vanishes.",
        "Isabelle eq_Real: the two Cauchy sequences are the same real.",
        "Isabelle le_RealI: the bound is at most every upper endpoint, so the bound is at most that real.",
        "Isabelle Real_leI: every lower endpoint is at most the bound, so that real is at most the bound.",
        "Isabelle cSup_lessThan: the supremum of a lessThan ray is its bound.",
        f"The witness is {shown}.",
    )


@dataclass(frozen=True)
class _Cut:
    member: RealForm
    low: Ratio
    high: Ratio
    left: Ratio
    right: Ratio
    depth: int
    width: Ratio
    initial: Ratio


def _certificate(bound: RealForm) -> _Cut:
    member = _below(bound, _OPEN_SET)
    return _cut_from(member, bound, lambda rational: _holds_upper(bound, rational))


def _cut_from(member: RealForm, bound: RealForm, holds) -> _Cut:
    shifted = _sub_forms(member, _one())
    low = _integer_bound(shifted, "floor")
    high = _integer_bound(bound, "ceiling")
    if holds(low) or not holds(high):
        raise KernelError("the floor and the ceiling left the upper-bound predicate")
    if _qcmp(low, high) >= 0:
        raise KernelError("the bisection started with an empty interval")
    left, right, depth = _bisect(low, high, holds)
    initial = _qsub(high, low)
    width = _qdiv(initial, Ratio(2**depth, 1))
    if _qsub(right, left) != width or _qcmp(width, Ratio(1, 1)) >= 0:
        raise KernelError("bisection width disagreed with the modulus")
    return _Cut(member, low, high, left, right, depth, width, initial)


def _bisect(low: Ratio, high: Ratio, holds) -> tuple[Ratio, Ratio, int]:
    initial = _qsub(high, low)
    left = low
    right = high
    depth = 0
    while depth < 64:
        width = _qdiv(initial, Ratio(2**depth, 1))
        if _qsub(right, left) != width:
            raise KernelError("bisection width disagreed with the modulus")
        if depth >= 1 and _qcmp(width, Ratio(1, 1)) < 0:
            return left, right, depth
        midpoint = _qdiv(_qadd(left, right), Ratio(2, 1))
        if holds(midpoint):
            right = midpoint
        else:
            left = midpoint
        depth += 1
        if holds(left) or not holds(right):
            raise KernelError("bisection left the upper-bound predicate")
    raise NotExact(_OPEN_SET)


def _holds_upper(bound: RealForm, rational: Ratio) -> bool:
    direction = compare_reals(bound, real_of_rat(rational).form)
    if direction == "open":
        raise NotExact(_OPEN_SET)
    return direction in {"lt", "eq"}


def _integer_bound(form: RealForm, mode: str) -> Ratio:
    for depth in (0, 1, 2, 4, 8, 16, 32, 48, 64):
        lower, upper = _enclose(form, depth)
        start = lower.num // lower.den
        stop = upper.num // upper.den
        if upper.num % upper.den:
            stop += 1
        if stop < start or stop - start > 8:
            continue
        found: int | None = None
        ambiguous = False
        for number in range(start - 1, stop + 2):
            verdict = _is_floor(form, number) if mode == "floor" else _is_ceiling(form, number)
            if verdict is None:
                ambiguous = True
                break
            if verdict:
                found = number
                break
        if ambiguous or found is None:
            continue
        return Ratio(found, 1)
    raise NotExact(_OPEN_SET)


def _is_floor(form: RealForm, number: int) -> bool | None:
    left = _decided(_integer_form(number), form)
    right = _decided(form, _integer_form(number + 1))
    if left is None or right is None:
        return None
    return left in {"lt", "eq"} and right == "lt"


def _is_ceiling(form: RealForm, number: int) -> bool | None:
    left = _decided(_integer_form(number - 1), form)
    right = _decided(form, _integer_form(number))
    if left is None or right is None:
        return None
    return left == "lt" and right in {"lt", "eq"}


def _decided(left: RealForm, right: RealForm) -> str | None:
    direction = compare_reals(left, right)
    if direction == "open":
        return None
    return direction


def _integer_form(number: int) -> RealForm:
    return real_of_rat(Ratio(number, 1)).form


def _from_intersection(term: Term) -> tuple[object, tuple[str, ...]] | None:
    if not isinstance(term, App) or term.op != "inter" or len(term.args) != 2:
        return None
    left_value, left_lines = interpret(term.args[0])
    right_value, right_lines = interpret(term.args[1])
    value, detail = _combine(left_value, right_value)
    return value, (*left_lines, *right_lines, *detail)


def _combine(left_value: object, right_value: object) -> tuple[object, tuple[str, ...]]:
    left = _meet_side(left_value)
    right = _meet_side(right_value)
    kind, bound, members, rule = _meet_result(left, right, _OPEN_SET)
    detail = _meet_detail(rule, bound, members)
    RayMeetTheorem(
        left[0],
        left[1],
        left[2],
        right[0],
        right[1],
        right[2],
        kind,
        bound,
        members,
        rule,
        detail,
    )
    if kind == "finite":
        return _finite_set(members), detail
    if kind in _INTERVAL_KINDS:
        if bound is None or len(members) != 1:
            raise KernelError("an interval needs both bounds")
        return Interval(kind, bound, members[0]), detail
    return _synthetic(kind, bound), detail


def _meet_side(value: object) -> tuple[str, RealForm | None, tuple[RealForm, ...]]:
    if isinstance(value, Interval):
        raise NotExact("this intersection stays outside this rule")
    if isinstance(value, SetTheorem):
        return "finite", None, value.members
    if isinstance(value, CollectForm):
        ray = classify(value)
        if ray is None:
            raise NotExact(_NOT_FINITE)
        return ray.kind, ray.bound, ()
    raise NotExact("union and intersection take sets")


def _meet_result(
    left: tuple[str, RealForm | None, tuple[RealForm, ...]],
    right: tuple[str, RealForm | None, tuple[RealForm, ...]],
    message: str,
) -> tuple[str, RealForm | None, tuple[RealForm, ...], str]:
    swapped = _absorb_univ(left, right, message)
    if swapped is not None:
        return swapped
    if left[0] == "finite" and right[0] != "finite":
        return _filter_finite(left[2], right[0], right[1], message), None, _kept(left[2], right[0], right[1], message), "Set.meet_filter"
    if right[0] == "finite" and left[0] != "finite":
        return "finite", None, _kept(right[2], left[0], left[1], message), "Set.meet_filter"
    if left[0] == "atMost" and right[0] == "atMost":
        return "atMost", _min(left[1], right[1], message), (), "Set.meet_atMost"
    if left[0] == "atLeast" and right[0] == "atLeast":
        return "atLeast", _max(left[1], right[1], message), (), "Set.meet_atLeast"
    if left[0] == "lessThan" and right[0] == "lessThan":
        return "lessThan", _min(left[1], right[1], message), (), "Set.meet_lessThan"
    if left[0] == "greaterThan" and right[0] == "greaterThan":
        return "greaterThan", _max(left[1], right[1], message), (), "Set.meet_greaterThan"
    same_side = _same_side_meet(left, right, message)
    if same_side is not None:
        return same_side
    if {left[0], right[0]} == {"atMost", "atLeast"}:
        upper = left[1] if left[0] == "atMost" else right[1]
        lower = left[1] if left[0] == "atLeast" else right[1]
        direction = _direction(lower, upper, message)
        if direction == "eq":
            return "finite", None, (upper,), "Set.meet_singleton"
        if direction == "gt":
            return "finite", None, (), "Set.meet_empty"
    if _is_two_sided(left[0], right[0]):
        return _two_sided(left, right, message)
    raise NotExact(_NOT_FINITE)


def _same_side_meet(
    left: tuple[str, RealForm | None, tuple[RealForm, ...]],
    right: tuple[str, RealForm | None, tuple[RealForm, ...]],
    message: str,
) -> tuple[str, RealForm | None, tuple[RealForm, ...], str] | None:
    pair = _ordered_bounds(left, right, "lessThan", "atMost")
    if pair is not None:
        opened, closed = pair
        if _direction(closed, opened, message) == "lt":
            return "atMost", closed, (), "Set.meet_less_closed"
        return "lessThan", opened, (), "Set.meet_less_closed"
    pair = _ordered_bounds(left, right, "greaterThan", "atLeast")
    if pair is not None:
        opened, closed = pair
        if _direction(closed, opened, message) == "gt":
            return "atLeast", closed, (), "Set.meet_greater_closed"
        return "greaterThan", opened, (), "Set.meet_greater_closed"
    return None


def _ordered_bounds(
    left: tuple[str, RealForm | None, tuple[RealForm, ...]],
    right: tuple[str, RealForm | None, tuple[RealForm, ...]],
    opened: str,
    closed: str,
) -> tuple[RealForm, RealForm] | None:
    if left[0] == opened and right[0] == closed and left[1] is not None and right[1] is not None:
        return left[1], right[1]
    if left[0] == closed and right[0] == opened and left[1] is not None and right[1] is not None:
        return right[1], left[1]
    return None


def _is_two_sided(left: str, right: str) -> bool:
    lowers = {"atLeast", "greaterThan"}
    uppers = {"atMost", "lessThan"}
    return (left in lowers and right in uppers) or (left in uppers and right in lowers)


def _two_sided(
    left: tuple[str, RealForm | None, tuple[RealForm, ...]],
    right: tuple[str, RealForm | None, tuple[RealForm, ...]],
    message: str,
) -> tuple[str, RealForm | None, tuple[RealForm, ...], str]:
    lower_kind = left[0] if left[0] in {"atLeast", "greaterThan"} else right[0]
    upper_kind = left[0] if left[0] in {"atMost", "lessThan"} else right[0]
    lower = left[1] if left[0] == lower_kind else right[1]
    upper = left[1] if left[0] == upper_kind else right[1]
    direction = _direction(lower, upper, message)
    strict = lower_kind == "greaterThan" or upper_kind == "lessThan"
    if direction == "gt" or (strict and direction == "eq"):
        return "finite", None, (), "Set.meet_open_empty"
    if direction != "lt" or lower is None or upper is None:
        raise NotExact(message)
    kind = _interval_kind(lower_kind, upper_kind)
    return kind, lower, (upper,), f"Set.meet_{kind}"


def _absorb_univ(
    left: tuple[str, RealForm | None, tuple[RealForm, ...]],
    right: tuple[str, RealForm | None, tuple[RealForm, ...]],
    message: str,
) -> tuple[str, RealForm | None, tuple[RealForm, ...], str] | None:
    if left[0] != "univ" and right[0] != "univ":
        return None
    other = right if left[0] == "univ" else left
    if other[0] == "univ":
        return "univ", None, (), "Set.meet_univ"
    if other[0] == "finite":
        return "finite", None, other[2], "Set.meet_univ"
    if other[0] in {"atMost", "atLeast", "lessThan", "greaterThan"}:
        return other[0], other[1], (), "Set.meet_univ"
    raise NotExact(message)


def _filter_finite(members: tuple[RealForm, ...], kind: str, bound: RealForm | None, message: str) -> str:
    _kept(members, kind, bound, message)
    return "finite"


def _kept(members: tuple[RealForm, ...], kind: str, bound: RealForm | None, message: str) -> tuple[RealForm, ...]:
    kept = []
    for member in members:
        if _in_ray(member, kind, bound, message):
            kept.append(member)
    return canonical(tuple(kept))


def _finite_set(members: tuple[RealForm, ...]) -> SetTheorem:
    current = set_empty()
    for member in members:
        element = eval_real(_term_of_form(member))
        if element.form != member:
            raise KernelError("a real did not round-trip through its term")
        current = set_insert(current, element)
    if current.members != members:
        raise KernelError("the filtered members changed")
    return current


def _synthetic(kind: str, bound: RealForm | None) -> CollectForm:
    binder = Var("_bound")
    if kind == "univ":
        return CollectForm("_bound", "eq", binder, binder)
    side = _term_of_form(bound)
    if kind == "atMost":
        return CollectForm("_bound", "le", binder, side)
    if kind == "lessThan":
        return CollectForm("_bound", "lt", binder, side)
    if kind == "greaterThan":
        return CollectForm("_bound", "lt", side, binder)
    return CollectForm("_bound", "le", side, binder)


def _require_ray(form: CollectForm) -> Ray:
    ray = classify(form)
    if ray is None:
        raise NotExact(_NOT_FINITE)
    return ray


def _inclusion_target(value: object) -> tuple[str, RealForm | None, tuple[RealForm, ...] | None]:
    if isinstance(value, SetTheorem):
        return "finite", None, value.members
    if isinstance(value, CollectForm):
        ray = _require_ray(value)
        return ray.kind, ray.bound, None
    raise NotExact("this expression is not a finite set")


def _subset_verdict(
    left_kind: str,
    left_bound: RealForm | None,
    right_kind: str,
    right_bound: RealForm | None,
    finite: tuple[RealForm, ...] | None,
    message: str,
) -> tuple[bool, RealForm | None]:
    if right_kind == "univ":
        return True, None
    if left_kind == "univ" and right_kind == "finite":
        return False, _outside_finite("univ", None, finite or (), message)
    if left_kind == "univ" and right_kind == "atMost":
        return False, _above(right_bound, message)
    if left_kind == "univ" and right_kind == "atLeast":
        return False, _below(right_bound, message)
    if left_kind == right_kind == "atMost":
        if _le(left_bound, right_bound, message):
            return True, None
        return False, left_bound
    if left_kind == right_kind == "atLeast":
        if _le(right_bound, left_bound, message):
            return True, None
        return False, left_bound
    if left_kind == "atMost" and right_kind == "atLeast":
        return False, _below(_min(left_bound, right_bound, message), message)
    if left_kind == "atLeast" and right_kind == "atMost":
        return False, _above(_max(left_bound, right_bound, message), message)
    if left_kind == right_kind == "lessThan":
        if _le(left_bound, right_bound, message):
            return True, None
        return False, right_bound
    if left_kind == right_kind == "greaterThan":
        if _le(right_bound, left_bound, message):
            return True, None
        return False, right_bound
    if right_kind == "finite":
        return False, _outside_finite(left_kind, left_bound, finite or (), message)
    if left_kind in {"lessThan", "greaterThan"} or right_kind in {"lessThan", "greaterThan"}:
        raise NotExact("this inclusion stays outside this rule")
    raise NotExact(_NOT_FINITE)


def _rays_equal(left_kind: str, left_bound: RealForm | None, right_kind: str, right_bound: RealForm | None) -> bool:
    if left_kind == "univ" and right_kind == "univ":
        return True
    if left_kind != right_kind or left_kind not in {"atMost", "atLeast", "lessThan", "greaterThan"}:
        return False
    try:
        return _direction(left_bound, right_bound, _OPEN_SET) == "eq"
    except NotExact:
        return False


def _inequality_witness(
    left_kind: str,
    left_bound: RealForm | None,
    right_kind: str,
    right_bound: RealForm | None,
    message: str,
) -> RealForm:
    holds, witness = _subset_verdict(left_kind, left_bound, right_kind, right_bound, None, message)
    if not holds and witness is not None:
        return witness
    holds, witness = _subset_verdict(right_kind, right_bound, left_kind, left_bound, None, message)
    if not holds and witness is not None:
        return witness
    if left_kind == right_kind == "atMost":
        return right_bound if _le(left_bound, right_bound, message) else left_bound
    if left_kind == right_kind == "atLeast":
        return left_bound if _le(right_bound, left_bound, message) else right_bound
    if left_kind == right_kind == "lessThan":
        return _min(left_bound, right_bound, message)
    if left_kind == right_kind == "greaterThan":
        return _max(left_bound, right_bound, message)
    raise NotExact(message)


def _quant_verdict(
    kind: str,
    ray_kind: str,
    bound: RealForm | None,
    predicate: Pred,
    binder: str,
    message: str,
) -> tuple[bool, RealForm | None, str, str]:
    shape, limit = _body_shape(predicate, binder, message)
    if kind == "all":
        holds, witness = _all_verdict(ray_kind, bound, shape, limit, message)
        rule = "Ball.ray" if holds else "Ball.ray_fails"
        return holds, witness, rule, shape
    if kind != "ex":
        raise NotExact(message)
    holds, witness = _ex_verdict(ray_kind, bound, shape, limit, message)
    rule = "Bex.ray" if holds else "Bex.ray_fails"
    return holds, witness, rule, shape


def _all_verdict(
    ray_kind: str,
    bound: RealForm | None,
    shape: str,
    limit: RealForm | None,
    message: str,
) -> tuple[bool, RealForm | None]:
    if shape == "refl":
        return True, None
    if ray_kind == "univ" and shape == "upper":
        return False, _above(limit, message)
    if ray_kind == "univ" and shape == "lower":
        return False, _below(limit, message)
    if ray_kind == "univ" and shape == "eq":
        return False, _above(limit, message)
    if ray_kind == "atMost" and shape == "upper":
        if _le(bound, limit, message):
            return True, None
        return False, bound
    if ray_kind == "atMost" and shape == "lower":
        return False, _below(_min(bound, limit, message), message)
    if ray_kind == "atMost" and shape == "eq":
        if _direction(limit, bound, message) == "eq":
            return False, _below(bound, message)
        return False, bound
    if ray_kind == "atLeast" and shape == "upper":
        return False, _above(_max(bound, limit, message), message)
    if ray_kind == "atLeast" and shape == "lower":
        if _le(limit, bound, message):
            return True, None
        return False, bound
    if ray_kind == "atLeast" and shape == "eq":
        if _direction(limit, bound, message) == "eq":
            return False, _above(bound, message)
        return False, bound
    raise NotExact(message)


def _ex_verdict(
    ray_kind: str,
    bound: RealForm | None,
    shape: str,
    limit: RealForm | None,
    message: str,
) -> tuple[bool, RealForm | None]:
    if shape == "refl":
        if ray_kind == "univ":
            return True, _zero()
        if ray_kind == "lessThan":
            return True, _below(bound, message)
        if ray_kind == "greaterThan":
            return True, _above(bound, message)
        return True, bound
    if ray_kind == "univ" and shape in {"upper", "lower", "eq"}:
        return True, limit
    if ray_kind == "atMost" and shape == "upper":
        return True, _min(bound, limit, message)
    if ray_kind == "atMost" and shape == "lower":
        if _le(limit, bound, message):
            return True, bound
        return False, None
    if ray_kind == "atMost" and shape == "eq":
        if _le(limit, bound, message):
            return True, limit
        return False, None
    if ray_kind == "atLeast" and shape == "upper":
        if _le(bound, limit, message):
            return True, bound
        return False, None
    if ray_kind == "atLeast" and shape == "lower":
        return True, _max(bound, limit, message)
    if ray_kind == "atLeast" and shape == "eq":
        if _le(bound, limit, message):
            return True, limit
        return False, None
    raise NotExact(message)


def _body_shape(predicate: Pred, binder: str, message: str) -> tuple[str, RealForm | None]:
    if predicate.op not in {"le", "eq"}:
        raise NotExact(message)
    if _is_binder(predicate.left, binder) and _is_binder(predicate.right, binder):
        return "refl", None
    if predicate.op == "le" and _is_binder(predicate.left, binder) and not _mentions(predicate.right, binder):
        return "upper", _closed_form(predicate.right, message)
    if predicate.op == "le" and _is_binder(predicate.right, binder) and not _mentions(predicate.left, binder):
        return "lower", _closed_form(predicate.left, message)
    if predicate.op == "eq" and _is_binder(predicate.left, binder) and not _mentions(predicate.right, binder):
        return "eq", _closed_form(predicate.right, message)
    if predicate.op == "eq" and _is_binder(predicate.right, binder) and not _mentions(predicate.left, binder):
        return "eq", _closed_form(predicate.left, message)
    raise NotExact(message)


def _closed_form(term: Term, message: str) -> RealForm:
    if contains_set(term):
        raise NotExact("a set does not enter this quantifier")
    try:
        return eval_real(term).form
    except NotExact:
        raise
    except KernelError as exc:
        raise NotExact(message) from exc


def _outside_finite(kind: str, bound: RealForm | None, members: tuple[RealForm, ...], message: str) -> RealForm:
    if kind == "univ":
        witness = _zero() if not members else _below(_minimum(members, message), message)
    elif kind == "atMost":
        floor = bound if not members else _min(bound, _minimum(members, message), message)
        witness = _below(floor, message)
    elif kind == "lessThan":
        floor = bound if not members else _min(bound, _minimum(members, message), message)
        witness = _below(floor, message)
    elif kind == "atLeast":
        cap = bound if not members else _max(bound, _maximum(members, message), message)
        witness = _above(cap, message)
    elif kind == "greaterThan":
        cap = bound if not members else _max(bound, _maximum(members, message), message)
        witness = _above(cap, message)
    else:
        raise NotExact(message)
    if not _in_ray(witness, kind, bound, message) or witness in members:
        raise NotExact(message)
    return witness


def _in_ray(form: RealForm, kind: str, bound: RealForm | None, message: str) -> bool:
    if kind == "univ":
        return True
    if kind == "atMost":
        return _le(form, bound, message)
    if kind == "lessThan":
        return _direction(form, bound, message) == "lt"
    if kind == "atLeast":
        return _le(bound, form, message)
    if kind == "greaterThan":
        return _direction(bound, form, message) == "lt"
    raise NotExact(message)


def _direction(left: RealForm | None, right: RealForm | None, message: str) -> str:
    if left is None or right is None:
        raise NotExact(message)
    direction = compare_reals(left, right)
    if direction == "open":
        raise NotExact(message)
    return direction


def _le(left: RealForm | None, right: RealForm | None, message: str) -> bool:
    return _direction(left, right, message) in {"lt", "eq"}


def _min(left: RealForm | None, right: RealForm | None, message: str) -> RealForm:
    if _direction(left, right, message) == "gt":
        return right
    return left


def _max(left: RealForm | None, right: RealForm | None, message: str) -> RealForm:
    if _direction(left, right, message) == "lt":
        return right
    return left


def _minimum(members: tuple[RealForm, ...], message: str) -> RealForm:
    found = members[0]
    for item in members[1:]:
        if _direction(item, found, message) == "lt":
            found = item
    return found


def _maximum(members: tuple[RealForm, ...], message: str) -> RealForm:
    found = members[0]
    for item in members[1:]:
        if _direction(item, found, message) == "gt":
            found = item
    return found


def _above(form: RealForm | None, message: str) -> RealForm:
    if form is None:
        raise NotExact(message)
    witness = _add_forms(form, _one())
    if compare_reals(form, witness) != "lt":
        raise NotExact(message)
    return witness


def _below(form: RealForm | None, message: str) -> RealForm:
    if form is None:
        raise NotExact(message)
    witness = _sub_forms(form, _one())
    if compare_reals(witness, form) != "lt":
        raise NotExact(message)
    return witness


def _one() -> RealForm:
    return real_of_rat(Ratio(1, 1)).form


def _zero() -> RealForm:
    return real_of_rat(Ratio(0, 1)).form


def _ray_rule(kind: str) -> str:
    if kind == "atMost":
        return "Set.atMost"
    if kind == "atLeast":
        return "Set.atLeast"
    if kind == "lessThan":
        return "Set.lessThan"
    if kind == "greaterThan":
        return "Set.greaterThan"
    if kind == "univ":
        return "Set.univ"
    raise KernelError(kind)


def _ray_ok(kind: str, bound: RealForm | None, form: CollectForm, rule: str) -> bool:
    if rule != _ray_rule(kind):
        return False
    try:
        found = classify(form)
    except (NotExact, KernelError):
        return False
    if found is None or found.kind != kind or found.bound != bound:
        return False
    if kind == "univ":
        return bound is None
    return bound is not None and _canonical(bound)


def _subset_ok(theorem: RaySubsetTheorem) -> bool:
    if theorem.rule not in {"Ray.subset", "Ray.not_subset"}:
        return False
    if theorem.finite is not None and theorem.finite != canonical(theorem.finite):
        return False
    try:
        holds, witness = _subset_verdict(
            theorem.left_kind,
            theorem.left_bound,
            theorem.right_kind,
            theorem.right_bound,
            theorem.finite,
            _OPEN_SET,
        )
    except (NotExact, KernelError):
        return False
    if theorem.holds != holds or theorem.witness != witness:
        return False
    return theorem.rule == ("Ray.subset" if holds else "Ray.not_subset")


def _quant_ok(theorem: RayQuantTheorem) -> bool:
    if theorem.kind not in {"all", "ex"} or not theorem.binder or theorem.predicate is None:
        return False
    if theorem.bound is not None and not _canonical(theorem.bound):
        return False
    try:
        holds, witness, rule, _shape = _quant_verdict(
            theorem.kind,
            theorem.ray_kind,
            theorem.bound,
            theorem.predicate,
            theorem.binder,
            _OPEN_QUANT,
        )
    except (NotExact, KernelError):
        return False
    return theorem.holds == holds and theorem.witness == witness and theorem.rule == rule


def _meet_ok(theorem: RayMeetTheorem) -> bool:
    left = (theorem.left_kind, theorem.left_bound, theorem.left_members)
    right = (theorem.right_kind, theorem.right_bound, theorem.right_members)
    if theorem.left_kind != "finite" and theorem.left_members:
        return False
    if theorem.right_kind != "finite" and theorem.right_members:
        return False
    if not all(_canonical(item) for item in theorem.left_members + theorem.right_members + theorem.result_members):
        return False
    try:
        kind, bound, members, rule = _meet_result(left, right, _OPEN_SET)
    except (NotExact, KernelError):
        return False
    return (
        theorem.result_kind == kind
        and theorem.result_bound == bound
        and theorem.result_members == members
        and theorem.rule == rule
    )


def _reflexive(form: CollectForm) -> bool:
    return (
        form.relation in {"le", "eq"}
        and _is_binder(form.left, form.binder)
        and _is_binder(form.right, form.binder)
    )


def _is_binder(term: Term, binder: str) -> bool:
    return isinstance(term, Var) and term.name == binder


def _mentions(term: Term, binder: str) -> bool:
    if isinstance(term, Var):
        return term.name == binder
    if isinstance(term, App):
        return any(_mentions(arg, binder) for arg in term.args)
    return False


def _pred_text(predicate: Pred) -> str:
    symbol = "<=" if predicate.op == "le" else "="
    return f"{pretty(predicate.left)} {symbol} {pretty(predicate.right)}"


def _bound_trace(ray: Ray) -> tuple[str, ...]:
    if ray.bound is None:
        return ()
    side = ray.form.right if ray.kind in {"atMost", "lessThan"} else ray.form.left
    if contains_set(side):
        return ()
    try:
        return real_trace(eval_real(side))
    except (NotExact, KernelError):
        return ()


def _ray_detail(ray: Ray) -> tuple[str, ...]:
    if ray.kind == "univ":
        return (
            "Isabelle UNIV_def: UNIV = {x. True}.",
            "A real is equal to itself, and it is less than or equal to itself.",
            "Isabelle Collect_cong: both predicates agree with that fact at every real.",
            "Finite_Set.infinite_UNIV_char_0: the set of every real is not a finite enumeration.",
            "This set is not bounded above. complete_real assumes a set that is bounded above.",
        )
    if ray.kind == "atMost":
        named = "Isabelle atMost_def: {..u} = {x. x <= u}."
        member = "Isabelle atMost_iff: membership is the comparison with the bound."
        infinite = "Set_Interval.infinite_Iic: this down-ray is not a finite enumeration."
        bound_line = "Isabelle cSup_atMost: the least upper bound of this down-ray is its bound."
    elif ray.kind == "lessThan":
        named = "Isabelle lessThan_def: {..<u} = {x. x < u}."
        member = "Isabelle lessThan_iff: membership is the strict comparison with the bound."
        infinite = "Set_Interval.infinite_Iio: this open down-ray is not a finite enumeration."
        bound_line = "Isabelle less_irrefl: the bound is not a member. Isabelle cSup_lessThan: the least upper bound of this open down-ray is that bound."
    elif ray.kind == "greaterThan":
        named = "Isabelle greaterThan_def: {l<..} = {x. l < x}."
        member = "Isabelle greaterThan_iff: membership is the strict comparison with the bound."
        infinite = "Set_Interval.infinite_Ioi: this open up-ray is not a finite enumeration."
        bound_line = "This set is not bounded above. complete_real assumes a set that is bounded above."
    else:
        named = "Isabelle atLeast_def: {l..} = {x. l <= x}."
        member = "Isabelle atLeast_iff: membership is the comparison with the bound."
        infinite = "Set_Interval.infinite_Ici: this up-ray is not a finite enumeration."
        bound_line = "This set is not bounded above. complete_real assumes a set that is bounded above."
    lines = [
        named,
        member,
        infinite,
        f"The bound is {show_form(ray.bound)}.",
        bound_line,
    ]
    if ray.kind != "lessThan":
        lines.append("The Archimedean bisection in the proof of complete_real stays outside this rule.")
    return tuple(lines)


def _subset_detail(holds: bool, left_kind: str, right_kind: str, witness: RealForm | None) -> tuple[str, ...]:
    if holds and right_kind == "univ":
        return (
            "Isabelle subset_UNIV: every set is contained in UNIV.",
            "Isabelle UNIV_I: every real is a member of that set.",
        )
    if holds and left_kind == "atMost":
        return (
            "Isabelle atMost_subset_iff: {..x} is contained in {..y} when x <= y.",
            "Isabelle order_trans carries a member of the smaller ray into the larger one.",
            "Isabelle atMost_iff: membership is the comparison with the bound.",
        )
    if holds and left_kind == "atLeast":
        return (
            "Isabelle atLeast_subset_iff: {x..} is contained in {y..} when y <= x.",
            "Isabelle order_trans carries a member of the higher ray into the lower one.",
            "Isabelle atLeast_iff: membership is the comparison with the bound.",
        )
    if holds and left_kind == "lessThan":
        return (
            "Isabelle lessThan_subset_iff: {..<x} is contained in {..<y} when x <= y.",
            "Isabelle lessThan_iff: membership is the strict comparison with the bound.",
        )
    if holds and left_kind == "greaterThan":
        return (
            "Isabelle greaterThan_subset_iff: {x<..} is contained in {y<..} when y <= x.",
            "Isabelle greaterThan_iff: membership is the strict comparison with the bound.",
        )
    shown = show_form(witness) if witness is not None else ""
    if right_kind == "finite":
        if left_kind == "univ":
            reason = "Finite_Set.infinite_UNIV_char_0: the set of every real is not a finite enumeration."
        elif left_kind == "atMost":
            reason = "Set_Interval.infinite_Iic: a down-ray is not a finite enumeration."
        elif left_kind == "lessThan":
            reason = "Set_Interval.infinite_Iio: an open down-ray is not a finite enumeration."
        elif left_kind == "greaterThan":
            reason = "Set_Interval.infinite_Ioi: an open up-ray is not a finite enumeration."
        else:
            reason = "Set_Interval.infinite_Ici: an up-ray is not a finite enumeration."
        return (
            reason,
            "Finite_Set.finite_subset: a subset of a finite set is finite.",
            "Isabelle less_add_one: one more than a real is strictly above it, and one less is strictly below it.",
            f"{shown} is a member of the ray and is outside the finite enumeration.",
        )
    if left_kind == "univ" and right_kind == "atMost":
        named = "Set_Interval.not_UNIV_le_Iic: UNIV is not contained in an atMost ray."
    elif left_kind == "univ" and right_kind == "atLeast":
        named = "Set_Interval.not_UNIV_le_Ici: UNIV is not contained in an atLeast ray."
    elif left_kind == "atMost" and right_kind == "atMost":
        named = "Isabelle atMost_subset_iff: the inclusion holds when the left bound is at most the right bound."
    elif left_kind == "atLeast" and right_kind == "atLeast":
        named = "Isabelle atLeast_subset_iff: the inclusion holds when the right bound is at most the left bound."
    elif left_kind == "lessThan" and right_kind == "lessThan":
        named = "Isabelle lessThan_subset_iff: the inclusion holds when the left bound is at most the right bound."
    elif left_kind == "greaterThan" and right_kind == "greaterThan":
        named = "Isabelle greaterThan_subset_iff: the inclusion holds when the right bound is at most the left bound."
    elif left_kind == "atMost":
        named = "Set_Interval.not_Iic_le_Ici: an atMost ray is not contained in an atLeast ray."
    else:
        named = "Set_Interval.not_Ici_le_Iic: an atLeast ray is not contained in an atMost ray."
    return (
        named,
        "Isabelle less_add_one: one more than a real is strictly above it, and one less is strictly below it.",
        f"{shown} is a member of the left set and is outside the right set.",
    )


def _eq_detail(kind: str) -> tuple[str, ...]:
    if kind == "univ":
        return (
            "Isabelle UNIV_def: UNIV = {x. True}.",
            "Isabelle Collect_cong: both reflexive predicates agree with that fact.",
            "The two comprehensions are the set of every real.",
        )
    if kind == "atMost":
        named = "Isabelle atMost_eq_iff: two atMost rays are equal when their bounds are equal."
    elif kind == "lessThan":
        named = "Isabelle lessThan_eq_iff: two lessThan rays are equal when their bounds are equal."
    elif kind == "greaterThan":
        named = "Isabelle greaterThan_eq_iff: two greaterThan rays are equal when their bounds are equal."
    else:
        named = "Isabelle atLeast_eq_iff: two atLeast rays are equal when their bounds are equal."
    return (
        named,
        "Isabelle order_antisym: the two inclusions of the bounds give one bound.",
    )


def _interval_kind(lower_kind: str, upper_kind: str) -> str:
    if lower_kind == "atLeast" and upper_kind == "atMost":
        return "atLeastAtMost"
    if lower_kind == "greaterThan" and upper_kind == "atMost":
        return "greaterThanAtMost"
    if lower_kind == "atLeast" and upper_kind == "lessThan":
        return "atLeastLessThan"
    if lower_kind == "greaterThan" and upper_kind == "lessThan":
        return "greaterThanLessThan"
    raise KernelError("these rays do not bound an interval")


def _interval_atom(interval: Interval) -> str:
    return f"{interval.kind}({show_form(interval.lower)}, {show_form(interval.upper)})"


def _interval_ok(theorem: IntervalTheorem) -> bool:
    if theorem.kind not in _INTERVAL_KINDS or theorem.rule != f"Set.{theorem.kind}":
        return False
    if not _canonical(theorem.lower) or not _canonical(theorem.upper):
        return False
    try:
        _interval_ready(theorem.kind, theorem.lower, theorem.upper)
    except (NotExact, KernelError):
        return False
    return True


def _interval_sup_ok(theorem: IntervalSupTheorem) -> bool:
    if theorem.kind not in _INTERVAL_KINDS or theorem.form != theorem.upper:
        return False
    if not _canonical(theorem.form) or not _canonical(theorem.lower) or not _canonical(theorem.upper):
        return False
    open_upper = theorem.kind in _OPEN_UPPER
    if open_upper and theorem.rule != "Interval.bisect":
        return False
    if not open_upper and theorem.rule != "Interval.sup":
        return False
    try:
        _interval_ready(theorem.kind, theorem.lower, theorem.upper)
        if open_upper:
            _interval_cut(theorem.kind, theorem.lower, theorem.upper)
    except (NotExact, KernelError):
        return False
    return True


def _interval_ready(kind: str, lower: RealForm, upper: RealForm) -> None:
    if kind not in _INTERVAL_KINDS:
        raise NotExact(_OPEN_SET)
    if _direction(lower, upper, _OPEN_SET) != "lt":
        raise KernelError("the interval is empty")
    if kind in _OPEN_UPPER:
        if _direction(upper, upper, _OPEN_SET) != "eq":
            raise KernelError("the upper bound was not related to itself")
        _interval_member(kind, lower, upper)
        return
    if not _in_interval(kind, lower, upper, upper):
        raise KernelError("the upper bound left the interval")


def _interval_supremum(interval: Interval) -> IntervalSupTheorem:
    _interval_ready(interval.kind, interval.lower, interval.upper)
    if interval.kind in _OPEN_UPPER:
        detail = _interval_bisect_detail(interval)
        return IntervalSupTheorem(interval.upper, interval.kind, interval.lower, interval.upper, "Interval.bisect", detail)
    detail = _interval_closed_detail(interval)
    return IntervalSupTheorem(interval.upper, interval.kind, interval.lower, interval.upper, "Interval.sup", detail)


def _interval_closed_detail(interval: Interval) -> tuple[str, ...]:
    upper = show_form(interval.upper)
    if interval.kind == "atLeastAtMost":
        named = "Isabelle cSup_atLeastAtMost: when the lower bound is at most the upper bound, the supremum of {l..u} is the upper bound."
        bounded = "Isabelle bdd_above_Icc: this closed interval is bounded above by its upper bound."
    else:
        named = "Isabelle cSup_greaterThanAtMost: when the lower bound is strictly below the upper bound, the supremum of {l<..u} is the upper bound."
        bounded = "Isabelle bdd_above_Ioc: this interval is bounded above by its upper bound."
    return (
        *_interval_fact(interval),
        "Isabelle order_refl: the upper bound compares with itself.",
        "The upper bound is a member of this interval.",
        bounded,
        "The upper bound is a member, so any upper bound is at least the bound.",
        "Isabelle cSup_eq_maximum: a member that bounds the set above is the supremum.",
        named,
        "The Archimedean bisection in the proof of complete_real stays outside this rule.",
        f"The witness is {upper}.",
    )


def _interval_bisect_detail(interval: Interval) -> tuple[str, ...]:
    member, cut = _interval_cut(interval.kind, interval.lower, interval.upper)
    shown = show_form(interval.upper)
    if interval.kind == "atLeastLessThan":
        named = "Isabelle cSup_atLeastLessThan: when the lower bound is strictly below the upper bound, the supremum of {l..<u} is the upper bound."
        bounded = "Isabelle bdd_above_Ico: every member is strictly below the upper bound, so that bound is an upper bound."
    else:
        named = "Isabelle cSup_greaterThanLessThan: when the lower bound is strictly below the upper bound, the supremum of {l<..<u} is the upper bound."
        bounded = "Isabelle bdd_above_Ioo: every member is strictly below the upper bound, so that bound is an upper bound."
    return (
        "Isabelle complete_real: a nonempty set of reals that is bounded above has a least upper bound.",
        *_interval_fact(interval),
        "Isabelle less_irrefl: the upper bound is not a member of this interval.",
        f"The member {show_form(member)} shows the interval is nonempty.",
        bounded,
        "The interval is the intersection of its lower ray with the lessThan ray of the upper bound.",
        "P q means every member is at most the rational q. For this interval, P q holds when the upper bound is at most q.",
        f"Isabelle of_int_floor_le: floor of one below the member is the rational {show_ratio(cut.low)}, and P fails there.",
        f"Isabelle le_of_int_ceiling: the ceiling of the upper bound is the rational {show_ratio(cut.high)}, and P holds there.",
        "avg is the midpoint. bisect keeps the half on which P changes: a failing midpoint raises the lower end, and a holding midpoint lowers the upper end.",
        f"After {cut.depth} steps the bracket is [{show_ratio(cut.left)}, {show_ratio(cut.right)}].",
        f"The width is {show_ratio(cut.width)}, the initial gap {show_ratio(cut.initial)} divided by {2 ** cut.depth}.",
        "Isabelle reals_Archimedean2: for every positive rational r there is a natural number n with the gap over 2^n below r. This certificate uses r = 1.",
        "Each failing endpoint was checked against a member of the interval that sits strictly above it.",
        "The lower endpoint stays strictly below the upper bound, and the upper endpoint stays at or above it.",
        "Isabelle cauchy: both endpoint sequences are Cauchy because that width vanishes.",
        "Isabelle eq_Real: the two Cauchy sequences are the same real.",
        "Isabelle le_RealI: the upper bound is at most every upper endpoint, so the upper bound is at most that real.",
        "Isabelle Real_leI: every lower endpoint is at most the upper bound, so that real is at most the upper bound.",
        "Isabelle cSup_eq_non_empty: the three checked conditions name the supremum.",
        named,
        f"The witness is {shown}.",
    )


def _interval_cut(kind: str, lower: RealForm, upper: RealForm) -> tuple[RealForm, _Cut]:
    member = _interval_member(kind, lower, upper)
    cut = _cut_from(member, upper, lambda rational: _interval_holds(kind, lower, upper, rational))
    return member, cut


def _interval_holds(kind: str, lower: RealForm, upper: RealForm, rational: Ratio) -> bool:
    if _holds_upper(upper, rational):
        return True
    _exceeding_member(kind, lower, upper, rational)
    return False


def _interval_member(kind: str, lower: RealForm, upper: RealForm) -> RealForm:
    if kind not in _OPEN_UPPER:
        raise KernelError("a closed upper bound does not use the bisection")
    if kind == "atLeastLessThan":
        if not _in_interval(kind, lower, upper, lower):
            raise KernelError("the lower bound left the interval")
        return lower
    mid = _half(_add_forms(lower, upper))
    if not _in_interval(kind, lower, upper, mid):
        raise NotExact(_OPEN_SET)
    return mid


def _exceeding_member(kind: str, lower: RealForm, upper: RealForm, rational: Ratio) -> RealForm:
    if kind not in _OPEN_UPPER:
        raise KernelError("a closed upper bound does not use the bisection")
    cut = real_of_rat(rational).form
    if kind == "atLeastLessThan" and _direction(cut, lower, _OPEN_SET) == "lt":
        if _in_interval(kind, lower, upper, lower) and _direction(cut, lower, _OPEN_SET) == "lt":
            return lower
    base = cut if _le(lower, cut, _OPEN_SET) else lower
    mid = _half(_add_forms(base, upper))
    if _in_interval(kind, lower, upper, mid) and _direction(cut, mid, _OPEN_SET) == "lt":
        return mid
    raise NotExact(_OPEN_SET)


def _in_interval(kind: str, lower: RealForm, upper: RealForm, form: RealForm) -> bool:
    if kind in _OPEN_LOWER:
        lower_ok = _direction(lower, form, _OPEN_SET) == "lt"
    else:
        lower_ok = _le(lower, form, _OPEN_SET)
    if kind in _OPEN_UPPER:
        upper_ok = _direction(form, upper, _OPEN_SET) == "lt"
    else:
        upper_ok = _le(form, upper, _OPEN_SET)
    return lower_ok and upper_ok


def _half(form: RealForm) -> RealForm:
    return _scale(form, Ratio(1, 2))


def _interval_detail(interval: Interval) -> tuple[str, ...]:
    lines = list(_interval_fact(interval))
    lower = show_form(interval.lower)
    upper = show_form(interval.upper)
    lines.append(f"The lower bound is {lower}. The upper bound is {upper}.")
    if interval.kind in _OPEN_UPPER:
        if interval.kind == "atLeastLessThan":
            lines.append("Isabelle cSup_atLeastLessThan: the least upper bound is the upper bound, and that bound is not a member.")
        else:
            lines.append("Isabelle cSup_greaterThanLessThan: the least upper bound is the upper bound, and that bound is not a member.")
    else:
        if interval.kind == "atLeastAtMost":
            lines.append("Isabelle cSup_atLeastAtMost: the least upper bound is the upper bound, and that bound is a member.")
        else:
            lines.append("Isabelle cSup_greaterThanAtMost: the least upper bound is the upper bound, and that bound is a member.")
        lines.append("The Archimedean bisection in the proof of complete_real stays outside this rule.")
    return tuple(lines)


def _interval_fact(interval: Interval) -> tuple[str, ...]:
    if interval.kind == "atLeastAtMost":
        return (
            "Isabelle atLeastAtMost_def: {l..u} is the intersection of {l..} and {..u}.",
            "Isabelle atLeastAtMost_iff: a real is in the interval when it meets the lower bound and the upper bound.",
        )
    if interval.kind == "greaterThanAtMost":
        return (
            "Isabelle greaterThanAtMost_def: {l<..u} is the intersection of {l<..} and {..u}.",
            "Isabelle greaterThanAtMost_iff: a real is in the interval when it is strictly above the lower bound and meets the upper bound.",
        )
    if interval.kind == "atLeastLessThan":
        return (
            "Isabelle atLeastLessThan_def: {l..<u} is the intersection of {l..} and {..<u}.",
            "Isabelle atLeastLessThan_iff: a real is in the interval when it meets the lower bound and is strictly below the upper bound.",
        )
    return (
        "Isabelle greaterThanLessThan_def: {l<..<u} is the intersection of {l<..} and {..<u}.",
        "Isabelle greaterThanLessThan_iff: a real is in the interval when it is strictly above the lower bound and strictly below the upper bound.",
    )


def _meet_detail(rule: str, bound: RealForm | None, members: tuple[RealForm, ...]) -> tuple[str, ...]:
    if rule == "Set.meet_atMost":
        return (
            "Isabelle Int_atMost: the intersection of two atMost rays is atMost of the smaller bound.",
            f"The bound is {show_form(bound)}.",
        )
    if rule == "Set.meet_atLeast":
        return (
            "Isabelle atLeast_iff: a real is in an up-ray when it meets that bound.",
            "A real is in both up-rays when it meets the greater bound.",
            f"The bound is {show_form(bound)}.",
        )
    if rule == "Set.meet_lessThan":
        return (
            "Isabelle lessThan_iff: a real is in both open down-rays when it is strictly below both bounds, hence strictly below the smaller one.",
            f"The bound is {show_form(bound)}.",
        )
    if rule == "Set.meet_greaterThan":
        return (
            "Isabelle greaterThan_iff: a real is in both open up-rays when it is strictly above both bounds, hence strictly above the greater one.",
            f"The bound is {show_form(bound)}.",
        )
    if rule == "Set.meet_less_closed":
        return (
            "Isabelle lessThan_iff and atMost_iff: the stricter of the two upper bounds is the intersection.",
            f"The bound is {show_form(bound)}.",
        )
    if rule == "Set.meet_greater_closed":
        return (
            "Isabelle greaterThan_iff and atLeast_iff: the stricter of the two lower bounds is the intersection.",
            f"The bound is {show_form(bound)}.",
        )
    if rule == "Set.meet_open_empty":
        return (
            "Isabelle lessThan_iff and greaterThan_iff read the open rays.",
            "The lower bound is not strictly below the upper bound, so no real is in both.",
            "The intersection is empty.",
        )
    if rule in {f"Set.meet_{kind}" for kind in _INTERVAL_KINDS}:
        upper = members[0] if members else None
        return (
            *_interval_fact(Interval(rule.removeprefix("Set.meet_"), bound, upper)),
            f"The lower bound is {show_form(bound)} and the upper bound is {show_form(upper)}.",
        )
    if rule == "Set.meet_univ":
        return (
            "Isabelle Int_UNIV_left and Int_UNIV_right: intersection with UNIV leaves the other set.",
            "Isabelle Int_commute: the order of the two sides does not matter.",
        )
    if rule == "Set.meet_singleton":
        return (
            "Isabelle atMost_Int_atLeast: atMost of a bound met with atLeast of that same bound is the singleton.",
            "Isabelle order_antisym: the two comparisons give equality with the bound.",
            f"The member is {show_form(members[0])}.",
        )
    if rule == "Set.meet_empty":
        return (
            "Isabelle atLeastatMost_empty_iff: {a..b} is empty when a is not less than or equal to b.",
            "Isabelle Int_commute: the order of the two rays does not matter.",
            "The intersection is empty.",
        )
    shown = ", ".join(show_form(item) for item in members) if members else ""
    return (
        "Isabelle Int_iff: a member of an intersection is a member of both sets.",
        "Isabelle atMost_iff and atLeast_iff read the ray.",
        "Finite_Set.finite_Int: the intersection of a finite set with any set is finite.",
        f"The members are {{{shown}}}.",
    )


def _quant_detail(kind: str, holds: bool, ray_kind: str, witness: RealForm | None, shape: str) -> tuple[str, ...]:
    if ray_kind == "univ":
        head = "Isabelle ball_UNIV: a universal over UNIV is an unbounded universal." if kind == "all" else "Isabelle bex_UNIV: an existential over UNIV is an unbounded existential."
    elif ray_kind == "atMost":
        head = "Isabelle atMost_iff: membership in the down-ray is the comparison with its bound."
    elif ray_kind == "lessThan":
        head = "Isabelle lessThan_iff: membership in the open down-ray is the strict comparison with its bound."
    elif ray_kind == "greaterThan":
        head = "Isabelle greaterThan_iff: membership in the open up-ray is the strict comparison with its bound."
    elif ray_kind == "atLeast":
        head = "Isabelle atLeast_iff: membership in the up-ray is the comparison with its bound."
    else:
        raise KernelError(ray_kind)
    if holds and kind == "all":
        return (
            head,
            "Isabelle ballI: the predicate follows from membership by the order on the bound.",
            "The members are not listed.",
        )
    if holds:
        shown = show_form(witness) if witness is not None else ""
        return (
            head,
            "Isabelle bexI: the witness is a member and the predicate holds there.",
            f"The witness is {shown}.",
        )
    if kind == "all":
        shown = show_form(witness) if witness is not None else ""
        return (
            head,
            "Isabelle ball_simps: a failed bounded universal has a member where the predicate fails.",
            f"The counterexample is {shown}.",
        )
    if shape == "eq":
        return (
            head,
            "The closed term is outside the ray.",
            "No member equals that term.",
        )
    return (
        head,
        "Isabelle atLeastatMost_empty_iff: the set of reals between the two bounds is empty when the lower bound is above the upper bound.",
        "No member satisfies the predicate.",
    )


def _subset_atom(left: Term, right: Term, holds: bool, lines: tuple[str, ...]) -> Rule:
    atom_left = pretty(left)
    atom_right = pretty(right)
    if holds:
        return Rule(
            id="math.subset",
            layer="base",
            stage="quantity",
            title=f"{atom_left} subset {atom_right}",
            produces=f"subset({atom_left},{atom_right})",
            detail_lines=lines,
        )
    return Rule(
        id="math.not_subset",
        layer="base",
        stage="quantity",
        title=f"not ({atom_left} subset {atom_right})",
        produces=f"not_subset({atom_left},{atom_right})",
        detail_lines=lines,
    )


def _quant_atom(kind: str, holds: bool, binder: str, shown: str, relation: str, lines: tuple[str, ...]) -> Rule:
    if kind == "all":
        atom = f"all({binder} in {shown}, {relation})" if holds else f"not_all({binder} in {shown}, {relation})"
        rule_id = "math.ball" if holds else "math.not_ball"
        title = f"all {binder} in {shown}. {relation}" if holds else f"not (all {binder} in {shown}. {relation})"
    else:
        atom = f"ex({binder} in {shown}, {relation})" if holds else f"not_ex({binder} in {shown}, {relation})"
        rule_id = "math.bex" if holds else "math.not_bex"
        title = f"ex {binder} in {shown}. {relation}" if holds else f"not (ex {binder} in {shown}. {relation})"
    return Rule(
        id=rule_id,
        layer="base",
        stage="quantity",
        title=title,
        produces=atom,
        detail_lines=lines,
    )


def _note(text: str) -> Rule:
    return Rule(
        id="math.open",
        layer="base",
        stage="check",
        title=text,
        produces=f"open({text})",
        detail_lines=(text,),
    )
