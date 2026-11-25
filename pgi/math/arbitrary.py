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
meets the two separations of one finite domain. A nested conjunction is
associated and then met, so an interval may be met with a further ray.
`Collect_disj_eq` unions two sides when both are finite enumerations, or
when the two rays or intervals cover a single admitted set: one ray, one
interval, a singleton, the empty set, or UNIV. A union that leaves a gap
is the union of those admitted pieces, in order, by `Un_iff`. `Collect_neg_eq`
sends the complement of a ray to the opposite ray, by `Compl_atMost`,
`Compl_atLeast`, `Compl_lessThan`, and `Compl_greaterThan`. The complement
of a two-sided interval is the two outer rays. The complement of a finite
set is the open rays and open intervals around its members, by
`linorder_neq_iff` and `Compl_insert`. A double negation is `double_compl`.
`Compl_UNIV_eq` sends the complement of the set of every real to the empty
set. `imp_conv_disj` rewrites implication as the disjunction of the negated
antecedent with the consequent. A connective whose sides this kernel cannot
settle stays outside. A predicate that is not affine in the binder, such as
`{x. x * x <= 2}`, stays outside the bisection.

A comparison that is affine in the binder is moved to a standard ray by
cancelling a shared summand and a nonzero coefficient, by `add_le_cancel_left`,
`add_le_cancel_right`, `mult_le_cancel_left_pos`, and `mult_le_cancel_left_neg`.
An identically true comparison is UNIV. An identically false comparison is
empty, except `x < x`, which stays the `less_irrefl` refusal. An affine
equality with a nonzero coefficient is the singleton of the cancelled bound.
A comparison that is a polynomial in the binder, with rational coefficients,
is settled by a checked sign chart. Square-free factoring and a Sturm
sequence isolate the real roots. A root that is a nested square root is
kept in that form. Otherwise the root is a real algebraic number: a
primitive irreducible integer polynomial together with the index of that
real root. `{x. x * x * x <= 2}` is `atMost(root(x^3 - 2, 1))`. `{x. x * x * x * x <= 2}`
is `atLeastAtMost(-sqrt(sqrt(2)), sqrt(sqrt(2)))`. A quadratic whose
coefficients are not all rational still uses the quadratic formula when
the discriminant can be formed as a nonnegative radicand. A discriminant
whose square root the kernel cannot form, and a polynomial whose
coefficients are not all rational and whose degree is greater than two,
stay outside that rule, and their upper-bound predicates stay outside the
bisection.

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
    _div_form,
    _enclose,
    _is_rational,
    _mul_forms,
    _neg_form,
    _ratio,
    _sqrt_of_form,
    _qadd,
    _qcmp,
    _qdiv,
    _qsub,
    form_of_algebraic,
    try_radical_form,
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
from pgi.math.syntax import App, Term, Var, pretty, rewrite_ge_gt
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
class RayJoinTheorem:
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
        if not _join_ok(self):
            raise KernelError(f"{self.rule} does not justify this union")


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
class Cover:
    pieces: tuple[tuple[str, RealForm | None, tuple[RealForm, ...]], ...]

    def __post_init__(self) -> None:
        if not _cover_ok(self.pieces):
            raise KernelError("this union of intervals is not admitted")


@dataclass(frozen=True)
class CoverSupTheorem:
    form: RealForm
    pieces: tuple[tuple[str, RealForm | None, tuple[RealForm, ...]], ...]
    rule: str
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _cover_sup_ok(self):
            raise KernelError(f"{self.rule} does not justify this least upper bound")


@dataclass(frozen=True)
class CoverMemberTheorem:
    form: RealForm
    pieces: tuple[tuple[str, RealForm | None, tuple[RealForm, ...]], ...]
    holds: bool
    rule: str
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _cover_member_ok(self):
            raise KernelError(f"{self.rule} does not justify this membership")


@dataclass(frozen=True)
class PolySignTheorem:
    binder: str
    relation: str
    left: Term
    right: Term
    kind: str
    bound: RealForm | None
    members: tuple[RealForm, ...]
    pieces: tuple[tuple[str, RealForm | None, tuple[RealForm, ...]], ...]
    roots: tuple[RealForm, ...]
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _poly_sign_ok(self):
            raise KernelError("Poly.sign does not justify this sign chart")


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
    pieces: tuple[tuple[str, RealForm | None, tuple[RealForm, ...]], ...] = ()

    def __post_init__(self) -> None:
        if not _connective_ok(self):
            raise KernelError(f"{self.rule} does not justify this comprehension")


def interpret(term: Term) -> tuple[object, tuple[str, ...]]:
    term, order_lines = rewrite_ge_gt(term)
    try:
        value = eval_set(term)
    except NotExact as exc:
        reduced = _from_intersection(term)
        if reduced is not None:
            return reduced
        reduced = _from_union(term)
        if reduced is not None:
            return reduced
        reduced = _from_sup(term)
        if reduced is not None:
            return reduced
        if _connective_collect(term):
            value, detail = _from_connective(term)
            return value, (*order_lines, *detail)
        raise exc
    if isinstance(value, CollectForm):
        reduced = _from_polynomial(value)
        if reduced is not None:
            return reduced[0], (*order_lines, *reduced[1])
    return value, order_lines


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
        found = _strict_ray(form)
        if found is not None:
            return found
        return _affine_ray(form)
    if form.relation == "eq":
        return _affine_ray(form)
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
    return _affine_ray(form)


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
_IMP = "Isabelle HOL.imp_conv_disj: (P --> Q) = (~P | Q)."
_DOUBLE = "Isabelle double_compl: - (- A) = A."
_AFFINE = (
    "The comparison is affine in the binder.",
    "Isabelle add_le_cancel_left and add_le_cancel_right move a shared summand.",
    "Isabelle mult_le_cancel_left_pos cancels a positive coefficient.",
    "Isabelle mult_le_cancel_left_neg flips the comparison when the coefficient is negative.",
)
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
    kind, bound, members, pieces = _connective_shape(value)
    ConnectiveTheorem(
        binder_term.name,
        domain,
        predicate,
        _connective_rule(domain, predicate),
        kind,
        bound,
        members,
        detail,
        pieces,
    )
    return value, detail


def _reduce_connective(binder: str, domain: Term, predicate: Term) -> tuple[object, tuple[str, ...]]:
    if predicate.op == "and":
        return _reduce_and(binder, domain, predicate)
    if predicate.op == "or":
        return _reduce_or(binder, domain, predicate)
    if predicate.op == "not":
        return _reduce_not(binder, domain, predicate)
    if predicate.op == "implies":
        return _reduce_implies(binder, domain, predicate)
    raise NotExact(_OUTSIDE)


def _reduce_and(binder: str, domain: Term, predicate: Term) -> tuple[object, tuple[str, ...]]:
    if len(predicate.args) != 2:
        raise NotExact(_OUTSIDE)
    left_value, left_detail = _side_value(binder, domain, predicate.args[0])
    right_value, right_detail = _side_value(binder, domain, predicate.args[1])
    if isinstance(left_value, SetTheorem) and isinstance(right_value, SetTheorem):
        line = _CONJ if _is_type(domain) else _CONJ2
        return set_inter(left_value, right_value), (line, *left_detail, *right_detail)
    if not _is_type(domain):
        raise NotExact(_OUTSIDE)
    try:
        value, detail = _combine(left_value, right_value)
    except NotExact as exc:
        if str(exc) in {_NOT_FINITE, "this intersection stays outside this rule"}:
            raise NotExact(_OUTSIDE) from exc
        raise
    return value, (_CONJ, *left_detail, *right_detail, *detail)


def _reduce_or(binder: str, domain: Term, predicate: Term) -> tuple[object, tuple[str, ...]]:
    if not _is_type(domain) or len(predicate.args) != 2:
        raise NotExact(_OUTSIDE)
    left_value, left_detail = _side_value(binder, domain, predicate.args[0])
    right_value, right_detail = _side_value(binder, domain, predicate.args[1])
    if isinstance(left_value, SetTheorem) and isinstance(right_value, SetTheorem):
        return set_union(left_value, right_value), (_DISJ, *left_detail, *right_detail)
    try:
        value, detail = _join(left_value, right_value)
    except NotExact as exc:
        raise NotExact(_OUTSIDE) from exc
    return value, (_DISJ, *left_detail, *right_detail, *detail)


def _reduce_implies(binder: str, domain: Term, predicate: Term) -> tuple[object, tuple[str, ...]]:
    if not _is_type(domain) or len(predicate.args) != 2:
        raise NotExact(_OUTSIDE)
    disjunction = App("or", (App("not", (predicate.args[0],)), predicate.args[1]))
    value, detail = _reduce_or(binder, domain, disjunction)
    return value, (_IMP, *detail)


def _reduce_not(binder: str, domain: Term, predicate: Term) -> tuple[object, tuple[str, ...]]:
    if not _is_type(domain) or len(predicate.args) != 1:
        raise NotExact(_OUTSIDE)
    inner = predicate.args[0]
    if not isinstance(inner, App):
        raise NotExact(_OUTSIDE)
    inner, order_lines = rewrite_ge_gt(inner)
    if inner.op in {"and", "or", "not", "implies"}:
        value, detail = _reduce_connective(binder, domain, inner)
        try:
            complemented, extra = _complement(value)
        except NotExact as exc:
            raise NotExact(_OUTSIDE) from exc
        return complemented, (_NEG, *order_lines, *detail, *extra)
    if not _atomic_comparison(inner) or len(inner.args) != 2:
        raise NotExact(_OUTSIDE)
    ray = classify(CollectForm(binder, inner.op, inner.args[0], inner.args[1]))
    if ray is None:
        try:
            value = eval_set(_side_collect(binder, domain, inner))
            complemented, extra = _complement(value)
        except NotExact as exc:
            raise NotExact(_OUTSIDE) from exc
        return complemented, (_NEG, *order_lines, *extra)
    if ray.kind == "univ":
        return set_empty(), (
            _NEG,
            *order_lines,
            "The predicate holds at every real, so the comprehension is UNIV.",
            "Isabelle Compl_UNIV_eq: - UNIV = {}.",
        )
    found = _COMPLEMENT.get(ray.kind)
    if found is None or ray.bound is None:
        raise NotExact(_OUTSIDE)
    kind, line = found
    return _synthetic(kind, ray.bound), (_NEG, *order_lines, line)


def _side_value(binder: str, domain: Term, predicate: Term) -> tuple[object, tuple[str, ...]]:
    predicate, order_lines = rewrite_ge_gt(predicate)
    if isinstance(predicate, App) and predicate.op in {"and", "or", "not", "implies"}:
        value, detail = _reduce_connective(binder, domain, predicate)
        return value, (*order_lines, *detail)
    if not _atomic_comparison(predicate):
        raise NotExact(_OUTSIDE)
    return eval_set(_side_collect(binder, domain, predicate)), order_lines


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
    if predicate.op == "implies":
        return "Collect.imp"
    raise KernelError("this boolean connective stays outside this rule")


def _connective_shape(
    value: object,
) -> tuple[str, RealForm | None, tuple[RealForm, ...], tuple[tuple[str, RealForm | None, tuple[RealForm, ...]], ...]]:
    if isinstance(value, Cover):
        return "cover", None, (), value.pieces
    if isinstance(value, Interval):
        return value.kind, value.lower, (value.upper,), ()
    if isinstance(value, SetTheorem):
        return "finite", None, value.members, ()
    if isinstance(value, CollectForm):
        ray = classify(value)
        if ray is None:
            raise NotExact(_OUTSIDE)
        return ray.kind, ray.bound, (), ()
    raise NotExact(_OUTSIDE)


def _connective_ok(theorem: ConnectiveTheorem) -> bool:
    if not theorem.binder or theorem.rule != _connective_rule(theorem.domain, theorem.predicate):
        return False
    if not isinstance(theorem.predicate, App):
        return False
    try:
        value, _detail = _reduce_connective(theorem.binder, theorem.domain, theorem.predicate)
        kind, bound, members, pieces = _connective_shape(value)
    except (NotExact, KernelError):
        return False
    return (
        kind == theorem.kind
        and bound == theorem.bound
        and members == theorem.members
        and pieces == theorem.pieces
    )


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
    if isinstance(value, Cover):
        return _cover_supremum(value), lines
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


def _from_union(term: Term) -> tuple[object, tuple[str, ...]] | None:
    if not isinstance(term, App) or term.op != "union" or len(term.args) != 2:
        return None
    left_value, left_lines = interpret(term.args[0])
    right_value, right_lines = interpret(term.args[1])
    value, detail = _join(left_value, right_value)
    return value, (*left_lines, *right_lines, *detail)


def cover_value_rule(origin: Term, cover: Cover, prelude: tuple[str, ...] = ()) -> Rule:
    shown = _cover_atom(cover)
    detail = _cover_detail(cover)
    lines = (*prelude, *detail)
    title = pretty(origin)
    return Rule(
        id="math.cover",
        layer="base",
        stage="quantity",
        title=f"{title} = {shown}",
        produces=shown,
        detail_lines=lines,
    )


def cover_sup_rule(origin: Term, theorem: CoverSupTheorem, prelude: tuple[str, ...] = ()) -> Rule:
    lines = (*prelude, *theorem.detail)
    return _quantity(origin, theorem.form, lines)


def cover_member_rule(left: Term, right: Term, element, cover: Cover, prelude: tuple[str, ...] = ()) -> Rule:
    from pgi.math.set import _element_parts
    from pgi.model import Rule as _Rule

    real_form, _real, _embedded = _element_parts(element)
    holds = _in_cover(real_form, cover.pieces, _OPEN_SET)
    detail = (
        "Isabelle Un_iff: a real is in the union when it is in one side.",
        f"{show_form(real_form)} {'lies in' if holds else 'lies in no piece of'} {_cover_atom(cover)}.",
    )
    CoverMemberTheorem(real_form, cover.pieces, holds, "Cover.member", detail)
    atom_left = show_form(real_form)
    atom_right = pretty(right)
    if holds:
        return _Rule(
            id="math.member",
            layer="base",
            stage="quantity",
            title=f"{pretty(left)} is a member of {pretty(right)}",
            produces=f"member({atom_left},{atom_right})",
            detail_lines=(*prelude, *detail),
        )
    return _Rule(
        id="math.not_member",
        layer="base",
        stage="quantity",
        title=f"{pretty(left)} is not a member of {pretty(right)}",
        produces=f"not_member({atom_left},{atom_right})",
        detail_lines=(*prelude, *detail),
    )



def interval_member_rule(left: Term, right: Term, element, interval: Interval, prelude: tuple[str, ...] = ()) -> Rule:
    from pgi.math.set import _element_parts

    real_form, _real, _embedded = _element_parts(element)
    holds = _in_interval(interval.kind, interval.lower, interval.upper, real_form)
    detail = (
        *_interval_fact(interval),
        f"{show_form(real_form)} {'lies in' if holds else 'does not lie in'} {_interval_atom(interval)}.",
    )
    atom_left = show_form(real_form)
    atom_right = pretty(right)
    if holds:
        return Rule(
            id="math.member",
            layer="base",
            stage="quantity",
            title=f"{pretty(left)} is a member of {pretty(right)}",
            produces=f"member({atom_left},{atom_right})",
            detail_lines=(*prelude, *detail),
        )
    return Rule(
        id="math.not_member",
        layer="base",
        stage="quantity",
        title=f"{pretty(left)} is not a member of {pretty(right)}",
        produces=f"not_member({atom_left},{atom_right})",
        detail_lines=(*prelude, *detail),
    )



def _join_covers(left_value: object, right_value: object) -> tuple[object, tuple[str, ...]]:
    pieces = _normalize_pieces((*_as_pieces(left_value), *_as_pieces(right_value)))
    value = _from_pieces(pieces)
    detail = (
        "Isabelle Collect_disj_eq, or Un_iff: a real is in the union when it is in one side.",
        "The two sides leave a gap, so the union is those admitted pieces in order.",
        f"The union is {_pieces_atom(pieces)}.",
    )
    return value, detail


def _meet_covers(left_value: object, right_value: object) -> tuple[object, tuple[str, ...]]:
    collected: list[tuple[str, RealForm | None, tuple[RealForm, ...]]] = []
    for left in _as_pieces(left_value):
        for right in _as_pieces(right_value):
            try:
                kind, bound, members, _rule = _meet_result(left, right, _OPEN_SET)
            except NotExact:
                continue
            if kind == "finite" and not members:
                continue
            collected.append((kind, bound, members))
    pieces = _normalize_pieces(tuple(collected))
    value = _from_pieces(pieces)
    detail = (
        "Isabelle Int_iff: a member of an intersection is a member of both sets.",
        "Each piece of the first union is met with each piece of the second, and empty meets are dropped.",
        f"The intersection is {_pieces_atom(pieces)}.",
    )
    return value, detail


def _as_pieces(value: object) -> tuple[tuple[str, RealForm | None, tuple[RealForm, ...]], ...]:
    if isinstance(value, Cover):
        return value.pieces
    if isinstance(value, SetTheorem):
        if not value.members:
            return ()
        return (("finite", None, value.members),)
    if isinstance(value, Interval):
        return ((value.kind, value.lower, (value.upper,)),)
    if isinstance(value, CollectForm):
        ray = classify(value)
        if ray is None:
            raise NotExact(_OUTSIDE)
        return ((ray.kind, ray.bound, ()),)
    raise NotExact("union and intersection take sets")


def _from_pieces(pieces: tuple[tuple[str, RealForm | None, tuple[RealForm, ...]], ...]) -> object:
    if not pieces:
        return set_empty()
    if len(pieces) == 1:
        kind, bound, members = pieces[0]
        if kind == "finite":
            return _finite_set(members)
        if kind in _INTERVAL_KINDS:
            if bound is None or len(members) != 1:
                raise KernelError("an interval needs both bounds")
            return Interval(kind, bound, members[0])
        return _synthetic(kind, bound)
    return Cover(pieces)


def _normalize_pieces(
    pieces: tuple[tuple[str, RealForm | None, tuple[RealForm, ...]], ...],
) -> tuple[tuple[str, RealForm | None, tuple[RealForm, ...]], ...]:
    intervals: list[tuple[str, RealForm | None, tuple[RealForm, ...]]] = []
    points: list[RealForm] = []
    for kind, bound, members in pieces:
        if kind == "univ":
            return (("univ", None, ()),)
        if kind == "finite":
            points.extend(members)
            continue
        intervals.append((kind, bound, members))
    intervals = _merge_interval_list(intervals)
    leftover: list[RealForm] = []
    for point in _sorted_forms(points):
        attached = False
        next_intervals: list[tuple[str, RealForm | None, tuple[RealForm, ...]]] = []
        index = 0
        while index < len(intervals):
            current = intervals[index]
            if _in_piece(point, current, _OPEN_SET):
                attached = True
                next_intervals.extend(intervals[index:])
                break
            if index + 1 < len(intervals) and _point_fills(point, current, intervals[index + 1]):
                merged = _merge_two_pieces(current, ("finite", None, (point,)))
                merged = _merge_two_pieces(merged, intervals[index + 1])
                next_intervals.append(merged)
                next_intervals.extend(intervals[index + 2 :])
                attached = True
                break
            closed = _close_with_point(current, point)
            if closed is not None:
                next_intervals.append(closed)
                next_intervals.extend(intervals[index + 1 :])
                attached = True
                break
            next_intervals.append(current)
            index += 1
        if attached:
            intervals = _merge_interval_list(next_intervals)
        else:
            leftover.append(point)
    grouped = _place_points(tuple(intervals), tuple(leftover))
    return grouped


def _merge_interval_list(
    intervals: list[tuple[str, RealForm | None, tuple[RealForm, ...]]],
) -> list[tuple[str, RealForm | None, tuple[RealForm, ...]]]:
    if not intervals:
        return []
    ordered = list(intervals)
    for index in range(len(ordered)):
        least = index
        for cursor in range(index + 1, len(ordered)):
            left_low, _ = _piece_ends(ordered[cursor], _OPEN_SET)
            right_low, _ = _piece_ends(ordered[least], _OPEN_SET)
            if _lower_first(left_low, right_low, _OPEN_SET) and left_low != right_low:
                least = cursor
            elif left_low == right_low:
                continue
        ordered[index], ordered[least] = ordered[least], ordered[index]
    merged: list[tuple[str, RealForm | None, tuple[RealForm, ...]]] = [ordered[0]]
    for item in ordered[1:]:
        previous = merged[-1]
        if _pieces_connect(previous, item):
            merged[-1] = _merge_two_pieces(previous, item)
        else:
            merged.append(item)
    return merged


def _place_points(
    intervals: tuple[tuple[str, RealForm | None, tuple[RealForm, ...]], ...],
    points: tuple[RealForm, ...],
) -> tuple[tuple[str, RealForm | None, tuple[RealForm, ...]], ...]:
    if not intervals:
        if not points:
            return ()
        return (("finite", None, canonical(points)),)
    placed: list[tuple[str, RealForm | None, tuple[RealForm, ...]]] = []
    remaining = list(points)
    for item in intervals:
        before: list[RealForm] = []
        later: list[RealForm] = []
        low, _high = _piece_ends(item, _OPEN_SET)
        for point in remaining:
            if low[0] is not None and _direction(point, low[1], _OPEN_SET) == "lt":
                before.append(point)
            else:
                later.append(point)
        if before:
            placed.append(("finite", None, canonical(tuple(before))))
        placed.append(item)
        remaining = later
    if remaining:
        placed.append(("finite", None, canonical(tuple(remaining))))
    return tuple(placed)


def _pieces_connect(
    left: tuple[str, RealForm | None, tuple[RealForm, ...]],
    right: tuple[str, RealForm | None, tuple[RealForm, ...]],
) -> bool:
    if left[0] == "finite" or right[0] == "finite":
        return False
    left_low, left_high = _piece_ends(left, _OPEN_SET)
    right_low, right_high = _piece_ends(right, _OPEN_SET)
    if _lower_first(left_low, right_low, _OPEN_SET):
        return _ends_connect(left_high, right_low, _OPEN_SET)
    return _ends_connect(right_high, left_low, _OPEN_SET)


def _merge_two_pieces(
    left: tuple[str, RealForm | None, tuple[RealForm, ...]],
    right: tuple[str, RealForm | None, tuple[RealForm, ...]],
) -> tuple[str, RealForm | None, tuple[RealForm, ...]]:
    if left[0] == "finite" or right[0] == "finite":
        raise KernelError("a finite piece does not merge as an interval")
    low, high, _rule = _merged_ends(left, right, _OPEN_SET)
    kind, bound, members = _from_ends(low, high, _OPEN_SET)
    return kind, bound, members


def _close_with_point(
    piece: tuple[str, RealForm | None, tuple[RealForm, ...]],
    point: RealForm,
) -> tuple[str, RealForm | None, tuple[RealForm, ...]] | None:
    if piece[0] == "finite":
        return None
    low, high = _piece_ends(piece, _OPEN_SET)
    if high[0] is True and high[1] is not None and _direction(point, high[1], _OPEN_SET) == "eq":
        kind, bound, members = _from_ends(low, (False, high[1]), _OPEN_SET)
        return kind, bound, members
    if low[0] is True and low[1] is not None and _direction(point, low[1], _OPEN_SET) == "eq":
        kind, bound, members = _from_ends((False, low[1]), high, _OPEN_SET)
        return kind, bound, members
    return None


def _point_fills(
    point: RealForm,
    left: tuple[str, RealForm | None, tuple[RealForm, ...]],
    right: tuple[str, RealForm | None, tuple[RealForm, ...]],
) -> bool:
    if left[0] == "finite" or right[0] == "finite":
        return False
    _left_low, left_high = _piece_ends(left, _OPEN_SET)
    right_low, _right_high = _piece_ends(right, _OPEN_SET)
    if left_high[0] is None or right_low[0] is None:
        return False
    if _direction(left_high[1], right_low[1], _OPEN_SET) != "eq":
        return False
    if not (left_high[0] and right_low[0]):
        return False
    return _direction(point, left_high[1], _OPEN_SET) == "eq"


def _piece_ends(
    piece: tuple[str, RealForm | None, tuple[RealForm, ...]],
    message: str,
) -> tuple[tuple[bool | None, RealForm | None], tuple[bool | None, RealForm | None]]:
    kind, bound, members = piece
    if kind == "finite":
        if not members:
            raise NotExact(message)
        low = members[0]
        high = members[0]
        for item in members[1:]:
            if _direction(item, low, message) == "lt":
                low = item
            if _direction(item, high, message) == "gt":
                high = item
        return (False, low), (False, high)
    return _as_ends(kind, bound, members, message)


def _piece_sort_key(piece: tuple[str, RealForm | None, tuple[RealForm, ...]]) -> tuple[int, str, str]:
    low, _high = _piece_ends(piece, _OPEN_SET)
    if low[0] is None:
        return (0, "", "")
    return (1, show_form(low[1]), "0" if not low[0] else "1")


def _sorted_forms(forms: list[RealForm]) -> list[RealForm]:
    unique: list[RealForm] = []
    for item in forms:
        if all(_direction(item, seen, _OPEN_SET) != "eq" for seen in unique):
            unique.append(item)

    def key(form: RealForm) -> tuple[int, str]:
        return (0, show_form(form))

    # sort by real order, not display
    ordered = list(unique)
    for index in range(len(ordered)):
        least = index
        for cursor in range(index + 1, len(ordered)):
            if _direction(ordered[cursor], ordered[least], _OPEN_SET) == "lt":
                least = cursor
        ordered[index], ordered[least] = ordered[least], ordered[index]
    return ordered


def _in_piece(
    form: RealForm,
    piece: tuple[str, RealForm | None, tuple[RealForm, ...]],
    message: str,
) -> bool:
    kind, bound, members = piece
    if kind == "finite":
        return any(_direction(form, item, message) == "eq" for item in members)
    return _in_side(form, kind, bound, members, message)


def _in_cover(
    form: RealForm,
    pieces: tuple[tuple[str, RealForm | None, tuple[RealForm, ...]], ...],
    message: str,
) -> bool:
    return any(_in_piece(form, piece, message) for piece in pieces)


def _cover_ok(pieces: tuple[tuple[str, RealForm | None, tuple[RealForm, ...]], ...]) -> bool:
    if len(pieces) < 2:
        return False
    previous = None
    for piece in pieces:
        kind, bound, members = piece
        if kind == "univ":
            return False
        if kind == "finite":
            if not members or members != canonical(members) or not all(_canonical(item) for item in members):
                return False
        elif kind in _INTERVAL_KINDS:
            if bound is None or len(members) != 1 or not _canonical(bound) or not _canonical(members[0]):
                return False
            if _direction(bound, members[0], _OPEN_SET) != "lt":
                return False
        elif kind in {"atMost", "atLeast", "lessThan", "greaterThan"}:
            if bound is None or members or not _canonical(bound):
                return False
        else:
            return False
        if previous is not None:
            if not _lower_first(_piece_ends(previous, _OPEN_SET)[0], _piece_ends(piece, _OPEN_SET)[0], _OPEN_SET):
                return False
            if _pieces_connect(previous, piece):
                return False
        previous = piece
    return True


def _cover_atom(cover: Cover) -> str:
    return _pieces_atom(cover.pieces)


def _pieces_atom(pieces: tuple[tuple[str, RealForm | None, tuple[RealForm, ...]], ...]) -> str:
    if not pieces:
        return "set({})"
    return " union ".join(_piece_atom(*piece) for piece in pieces)


def _piece_atom(kind: str, bound: RealForm | None, members: tuple[RealForm, ...]) -> str:
    if kind == "finite":
        shown = ", ".join(show_form(item) for item in members)
        return "set({" + shown + "})"
    if kind == "univ":
        return "univ"
    if kind in _INTERVAL_KINDS:
        return f"{kind}({show_form(bound)}, {show_form(members[0])})"
    return f"{kind}({show_form(bound)})"


def _cover_detail(cover: Cover) -> tuple[str, ...]:
    return (
        "Isabelle Un_iff: a real is in the union when it is in one side.",
        "The pieces are disjoint admitted rays or intervals, stored in order from the left.",
        f"The union is {_cover_atom(cover)}.",
    )


def _cover_supremum(cover: Cover) -> CoverSupTheorem:
    form, rule, detail = _cover_sup_data(cover.pieces)
    return CoverSupTheorem(form, cover.pieces, rule, detail)


def _cover_sup_data(
    pieces: tuple[tuple[str, RealForm | None, tuple[RealForm, ...]], ...],
) -> tuple[RealForm, str, tuple[str, ...]]:
    last = pieces[-1]
    kind, bound, members = last
    if kind in {"atLeast", "greaterThan", "univ"}:
        raise NotExact(
            f"{_UNBOUNDED}. The right-hand piece of this union is not bounded above. "
            "Isabelle Un_iff puts a member of that piece in the union. complete_real assumes a set bounded above."
        )
    if kind == "finite":
        form = members[-1]
        for item in members:
            if _direction(item, form, _OPEN_SET) == "gt":
                form = item
        detail = (
            "Isabelle Un_iff: a real is in the union when it is in one side.",
            "Every earlier piece lies to the left of this finite last piece.",
            "Isabelle cSup_eq_Max: the least upper bound of a nonempty finite set is its maximum.",
            f"The bound is {show_form(form)}.",
        )
        return form, "Cover.sup", detail
    if kind == "atMost" or (kind in _INTERVAL_KINDS and kind not in _OPEN_UPPER):
        form = bound if kind == "atMost" else members[0]
        detail = (
            "Isabelle Un_iff: a real is in the union when it is in one side.",
            "Every earlier piece lies to the left of this last piece, so the least upper bound is the upper bound of that piece.",
            "The last piece contains its upper bound, so cSup_eq_maximum applies to that piece.",
            f"The bound is {show_form(form)}.",
        )
        return form, "Cover.sup", detail
    form = bound if kind == "lessThan" else members[0]
    detail = (
        "Isabelle Un_iff: a real is in the union when it is in one side.",
        "Every earlier piece lies to the left of this last piece, so the least upper bound is the open upper bound of that piece.",
        *_bisect_detail(form),
    )
    return form, "Cover.bisect", detail


def _cover_sup_ok(theorem: CoverSupTheorem) -> bool:
    if not _canonical(theorem.form) or not _cover_ok(theorem.pieces):
        return False
    try:
        form, rule, _detail = _cover_sup_data(theorem.pieces)
    except (NotExact, KernelError):
        return False
    return form == theorem.form and rule == theorem.rule


def _cover_member_ok(theorem: CoverMemberTheorem) -> bool:
    if not _canonical(theorem.form) or not _cover_ok(theorem.pieces):
        return False
    try:
        holds = _in_cover(theorem.form, theorem.pieces, _OPEN_SET)
    except (NotExact, KernelError):
        return False
    return holds == theorem.holds and theorem.rule == "Cover.member"


def _complement_finite(members: tuple[RealForm, ...]) -> tuple[object, tuple[str, ...]]:
    if not members:
        return _synthetic("univ", None), (
            "Isabelle Compl_empty: - {} = UNIV.",
            _DOUBLE,
        )
    points = _sorted_forms(list(members))
    pieces: list[tuple[str, RealForm | None, tuple[RealForm, ...]]] = [("lessThan", points[0], ())]
    for index in range(len(points) - 1):
        left, right = points[index], points[index + 1]
        if _direction(left, right, _OPEN_SET) != "lt":
            raise KernelError("the finite members were not strictly increasing")
        pieces.append(("greaterThanLessThan", left, (right,)))
    pieces.append(("greaterThan", points[-1], ()))
    value = _from_pieces(_normalize_pieces(tuple(pieces)))
    detail = (
        "Isabelle Collect_neg_eq: {x. not P x} = - {x. P x}.",
        "Isabelle linorder_neq_iff: (x ≠ a) = (x < a ∨ a < x).",
        "Isabelle Compl_insert: the complement of an insertion is the complement of the rest, punctured at the new point.",
        f"The complement is {_pieces_atom(_as_pieces(value))}.",
    )
    return value, detail


def _complement_piece(
    piece: tuple[str, RealForm | None, tuple[RealForm, ...]],
) -> tuple[object, tuple[str, ...]]:
    kind, bound, members = piece
    if kind == "finite":
        return _complement_finite(members)
    if kind in _COMPLEMENT:
        opposite, line = _COMPLEMENT[kind]
        return _synthetic(opposite, bound), (
            "Isabelle Collect_neg_eq: {x. not P x} = - {x. P x}.",
            line,
            _DOUBLE,
        )
    if kind not in _INTERVAL_KINDS or bound is None or len(members) != 1:
        raise NotExact(_OUTSIDE)
    upper = members[0]
    left_kind = "lessThan" if kind not in _OPEN_LOWER else "atMost"
    right_kind = "greaterThan" if kind not in _OPEN_UPPER else "atLeast"
    pieces = _normalize_pieces(((left_kind, bound, ()), (right_kind, upper, ())))
    value = _from_pieces(pieces)
    detail = (
        "Isabelle Collect_neg_eq: {x. not P x} = - {x. P x}.",
        "The complement of a two-sided interval is the down-ray strictly below the lower end, union the up-ray strictly above the upper end, with each end closed when that end of the interval was open.",
        f"The complement is {_pieces_atom(pieces)}.",
        _DOUBLE,
    )
    return value, detail


def _complement_cover(cover: Cover) -> tuple[object, tuple[str, ...]]:
    value: object | None = None
    lines: tuple[str, ...] = (
        "Isabelle Compl_Un: - (A ∪ B) = -A ∩ -B.",
        "The complement of the union is the intersection of the complements of the pieces.",
    )
    for piece in cover.pieces:
        complemented, extra = _complement_piece(piece)
        lines = (*lines, *extra)
        if value is None:
            value = complemented
        else:
            value, meet_detail = _combine(value, complemented)
            lines = (*lines, *meet_detail)
    if value is None:
        return set_empty(), lines
    return value, lines


def _from_polynomial(form: CollectForm) -> tuple[object, tuple[str, ...]] | None:
    try:
        value, roots, detail = _polynomial_set(form.binder, form.relation, form.left, form.right)
    except (NotExact, KernelError):
        return None
    if value is None:
        return None
    kind, bound, members, pieces = _connective_shape(value)
    PolySignTheorem(
        form.binder,
        form.relation,
        form.left,
        form.right,
        kind,
        bound,
        members,
        pieces,
        roots,
        detail,
    )
    return value, detail


def _polynomial_set(
    binder: str,
    relation: str,
    left: Term,
    right: Term,
) -> tuple[object, tuple[RealForm, ...], tuple[str, ...]]:
    left_poly = _poly_term(left, binder)
    right_poly = _poly_term(right, binder)
    if left_poly is None or right_poly is None:
        raise NotExact(_NOT_FINITE)
    coeffs = _poly_trim(_poly_add(left_poly, _poly_neg(right_poly)))
    if len(coeffs) <= 2:
        raise NotExact(_NOT_FINITE)
    rat_coeffs = _as_rat_coeffs(coeffs)
    if rat_coeffs is not None:
        return _rational_poly_set(rat_coeffs, relation)
    if len(coeffs) == 3:
        try:
            return _quadratic_set(coeffs, relation)
        except NotExact:
            pass
    return _algebraic_poly_set(coeffs, relation)



def _as_rat_coeffs(coeffs: tuple[RealForm, ...]) -> tuple[Ratio, ...] | None:
    if any(not _is_rational(coeff) for coeff in coeffs):
        return None
    return tuple(coeff.constant for coeff in coeffs)


def _rational_poly_set(
    coeffs: tuple[Ratio, ...],
    relation: str,
) -> tuple[object, tuple[RealForm, ...], tuple[str, ...]]:
    from pgi.math.algebraic import (
        from_ratio_coeffs,
        integer_poly,
        leading_sign,
        roots_of_rational_polynomial,
        sign_at,
        AlgebraicReal,
    )

    # Roots are unchanged by a unit. The sign chart must use the original leading sign.
    signed = integer_poly(coeffs)
    poly = from_ratio_coeffs(coeffs)
    found = roots_of_rational_polynomial(poly)
    converted: list[tuple[RealForm, int]] = []
    for root, multiplicity in found:
        if isinstance(root, Ratio):
            form = real_of_rat(root).form
        elif isinstance(root, AlgebraicReal):
            form = try_radical_form(root.coeffs, root.index)
            if form is None:
                form = form_of_algebraic(root.coeffs, root.index)
        else:
            raise KernelError("an unexpected root kind")
        converted.append((form, multiplicity))
    roots = tuple(form for form, _mult in converted)
    for form in roots:
        _check_root_rational(poly, form)
    value = _chart_set(relation, converted, signed)
    shown_roots = ", ".join(show_form(form) for form in roots) if roots else "none"
    detail = (
        "The comparison is a polynomial in the binder.",
        "Yun square-free factorization and a Sturm sequence isolate the real roots.",
        "Each irrational root is a checked real algebraic number: a primitive irreducible integer polynomial together with the index of that real root.",
        "When that root is an admitted radical, the radical form is kept after it is checked against the minimal polynomial.",
        "The sign chart is checked at a rational point in each complementary interval.",
        f"The real roots are {shown_roots}.",
        f"The set is {_value_atom(value)}.",
    )
    return value, roots, detail


def _check_root_rational(poly: tuple[int, ...], form: RealForm) -> None:
    from pgi.math.algebraic import _divides_int, eval_int
    from pgi.math.real import _algebra_poly_eval

    if _is_rational(form):
        if eval_int(poly, form.constant).num != 0:
            raise KernelError("a constructed root did not vanish in the polynomial")
        return
    if form.algebras:
        _coeff, minpoly, _index = form.algebras[0]
        if not _divides_int(minpoly, poly):
            raise KernelError("a constructed root did not vanish in the polynomial")
        return
    total = _algebra_poly_eval(poly, form)
    if not _is_rational(total) or total.constant.num != 0:
        raise KernelError("a constructed root did not vanish in the polynomial")


def _chart_set(
    relation: str,
    roots: list[tuple[RealForm, int]],
    poly: tuple[int, ...],
) -> object:
    from pgi.math.algebraic import sign_at

    if relation not in {"eq", "lt", "le"}:
        raise NotExact(_NOT_FINITE)
    forms = [form for form, _mult in roots]
    if relation == "eq":
        return _finite_set(tuple(forms)) if forms else set_empty()
    points = _sign_test_points(forms)
    signs = [sign_at(poly, point) for point in points]
    if any(sign == 0 for sign in signs):
        raise KernelError("a sign-chart test point was a root")
    if forms and len(signs) != len(forms) + 1:
        raise KernelError("the sign chart was missing an interval")
    if not forms:
        positive = signs[0] > 0
        return _constant_sign(relation, positive)
    value: object | None = None
    # Open intervals around the roots.
    for index, sign in enumerate(signs):
        if sign > 0:
            continue
        lower = None if index == 0 else forms[index - 1]
        upper = None if index == len(forms) else forms[index]
        closed = relation == "le"
        piece = _chart_piece(lower, upper, closed)
        value = piece if value is None else _join(value, piece)[0]
    if relation == "le":
        # Isolated even-multiplicity roots in a positive region.
        for index, (form, multiplicity) in enumerate(roots):
            left_sign = signs[index]
            right_sign = signs[index + 1]
            if left_sign > 0 and right_sign > 0:
                if multiplicity % 2 != 0:
                    raise KernelError("an odd-multiplicity root did not change sign")
                piece = _finite_set((form,))
                value = piece if value is None else _join(value, piece)[0]
            elif left_sign == right_sign and multiplicity % 2 != 0:
                raise KernelError("an odd-multiplicity root did not change sign")
            elif left_sign != right_sign and multiplicity % 2 == 0:
                raise KernelError("an even-multiplicity root changed sign")
    return value if value is not None else set_empty()


def _chart_piece(lower: RealForm | None, upper: RealForm | None, closed: bool) -> object:
    if lower is None and upper is None:
        return _synthetic("univ", None)
    if lower is None:
        return _synthetic("atMost" if closed else "lessThan", upper)
    if upper is None:
        return _synthetic("atLeast" if closed else "greaterThan", lower)
    kind = "atLeastAtMost" if closed else "greaterThanLessThan"
    return Interval(kind, lower, upper)


def _sign_test_points(forms: list[RealForm]) -> list[Ratio]:
    if not forms:
        return [_ratio(0, 1)]
    points: list[Ratio] = []
    first_low, _ = _form_interval(forms[0])
    points.append(_qsub(first_low, _ratio(1, 1)))
    for left, right in zip(forms, forms[1:]):
        _, left_high = _form_interval(left)
        right_low, _ = _form_interval(right)
        if _qcmp(left_high, right_low) >= 0:
            raise KernelError("neighbouring real roots had overlapping isolating intervals")
        points.append(_qdiv(_qadd(left_high, right_low), _ratio(2, 1)))
    _, last_high = _form_interval(forms[-1])
    points.append(_qadd(last_high, _ratio(1, 1)))
    return points


def _form_interval(form: RealForm) -> tuple[Ratio, Ratio]:
    if _is_rational(form):
        return form.constant, form.constant
    return _enclose(form, 8)



def _algebraic_poly_set(
    coeffs: tuple[RealForm, ...],
    relation: str,
) -> tuple[object, tuple[RealForm, ...], tuple[str, ...]]:
    from pgi.math.algfield import is_root_of_poly, roots_of_algebraic_polynomial, sign_at_algebraic
    from pgi.math.real import algebraic_of_form

    if relation not in {"eq", "lt", "le"}:
        raise NotExact(_NOT_FINITE)
    alg_coeffs = tuple(algebraic_of_form(coeff) for coeff in coeffs)
    found = roots_of_algebraic_polynomial(alg_coeffs)
    converted: list[tuple[RealForm, int]] = []
    for root, multiplicity in found:
        from pgi.math.algebraic import AlgebraicReal
        from pgi.math.rational import Ratio as Rat

        if isinstance(root, Rat):
            form = real_of_rat(root).form
        elif isinstance(root, AlgebraicReal):
            form = try_radical_form(root.coeffs, root.index)
            if form is None:
                form = form_of_algebraic(root.coeffs, root.index)
        else:
            raise KernelError("an unexpected root kind")
        converted.append((form, multiplicity))
    # Infer multiplicity parity from a sign chart of the original polynomial.
    forms = [form for form, _mult in converted]
    points = _sign_test_points(forms)
    signs = [sign_at_algebraic(alg_coeffs, point) for point in points]
    if any(sign == 0 for sign in signs):
        raise KernelError("a sign-chart test point was a root")
    if forms and len(signs) != len(forms) + 1:
        raise KernelError("the sign chart was missing an interval")
    adjusted: list[tuple[RealForm, int]] = []
    if not forms:
        adjusted = []
    else:
        for index, (form, _mult) in enumerate(converted):
            left_sign, right_sign = signs[index], signs[index + 1]
            if left_sign == right_sign:
                adjusted.append((form, 2))
            else:
                adjusted.append((form, 1))
    # Reuse the integer-chart builder by passing a dummy poly and pre-checked signs?
    # Build the set directly from signs and forms.
    value = _chart_from_signs(relation, adjusted, signs)
    roots = tuple(form for form, _mult in adjusted)
    shown_roots = ", ".join(show_form(form) for form in roots) if roots else "none"
    detail = (
        "The comparison is a polynomial in the binder, with algebraic coefficients.",
        "A resultant (the norm, or a multiple of the norm) reduces the predicate to a rational polynomial.",
        "A Sturm sequence isolates the candidate real roots. A candidate is kept only when it is checked to vanish in the original polynomial.",
        "Isolating intervals are refined until every sign in the chart is certain.",
        "When a root is an admitted radical, the radical form is kept after it is checked against the minimal polynomial.",
        f"The real roots are {shown_roots}.",
        f"The set is {_value_atom(value)}.",
    )
    return value, roots, detail


def _chart_from_signs(
    relation: str,
    roots: list[tuple[RealForm, int]],
    signs: list[int],
) -> object:
    if relation not in {"eq", "lt", "le"}:
        raise NotExact(_NOT_FINITE)
    forms = [form for form, _mult in roots]
    if relation == "eq":
        return _finite_set(tuple(forms)) if forms else set_empty()
    if not forms:
        positive = signs[0] > 0
        return _constant_sign(relation, positive)
    value: object | None = None
    for index, sign in enumerate(signs):
        if sign > 0:
            continue
        lower = None if index == 0 else forms[index - 1]
        upper = None if index == len(forms) else forms[index]
        closed = relation == "le"
        piece = _chart_piece(lower, upper, closed)
        value = piece if value is None else _join(value, piece)[0]
    if relation == "le":
        for index, (form, multiplicity) in enumerate(roots):
            left_sign = signs[index]
            right_sign = signs[index + 1]
            if left_sign > 0 and right_sign > 0:
                if multiplicity % 2 != 0:
                    raise KernelError("an odd-multiplicity root did not change sign")
                piece = _finite_set((form,))
                value = piece if value is None else _join(value, piece)[0]
            elif left_sign == right_sign and multiplicity % 2 != 0:
                raise KernelError("an odd-multiplicity root did not change sign")
            elif left_sign != right_sign and multiplicity % 2 == 0:
                raise KernelError("an even-multiplicity root changed sign")
    return value if value is not None else set_empty()


def _quadratic_set(

    coeffs: tuple[RealForm, ...],
    relation: str,
) -> tuple[object, tuple[RealForm, ...], tuple[str, ...]]:
    c, b, a = coeffs
    leading = compare_reals(a, _zero())
    if leading not in {"lt", "gt"}:
        raise NotExact(_NOT_FINITE)
    disc = _sub_forms(_mul_forms(b, b), _mul_forms(_from_int(4), _mul_forms(a, c)))
    disc_dir = compare_reals(disc, _zero())
    if disc_dir == "open":
        raise NotExact(_NOT_FINITE)
    if disc_dir == "lt":
        roots: tuple[RealForm, ...] = ()
        # sign is the leading coefficient everywhere
        positive = leading == "gt"
        value = _constant_sign(relation, positive)
        detail = (
            "The comparison is a quadratic in the binder.",
            "The discriminant is negative, so there is no real root.",
            "The sign of the quadratic is the sign of the leading coefficient at every real.",
            f"The set is {_value_atom(value)}.",
        )
        return value, roots, detail
    two_a = _mul_forms(_from_int(2), a)
    if disc_dir == "eq":
        root = _div_form(_neg_form(b), two_a)
        _check_root(coeffs, root)
        roots = (root,)
        value = _double_root_sign(relation, leading == "gt", root)
        detail = (
            "The comparison is a quadratic in the binder.",
            "The discriminant is zero, so there is a repeated real root.",
            "Substituting the root returns 0, by the quadratic formula and real_sqrt_pow2.",
            f"The root is {show_form(root)}.",
            f"The set is {_value_atom(value)}.",
        )
        return value, roots, detail
    sqrt_disc = _sqrt_of_form(disc)
    if _mul_forms(sqrt_disc, sqrt_disc) != _canonical(disc) and _mul_forms(sqrt_disc, sqrt_disc) != disc:
        # still accept if compare says equal
        if compare_reals(_mul_forms(sqrt_disc, sqrt_disc), disc) != "eq":
            raise NotExact(_NOT_FINITE)
    left_root = _div_form(_sub_forms(_neg_form(b), sqrt_disc), two_a)
    right_root = _div_form(_add_forms(_neg_form(b), sqrt_disc), two_a)
    _check_root(coeffs, left_root)
    _check_root(coeffs, right_root)
    if _direction(left_root, right_root, _OPEN_SET) == "gt":
        left_root, right_root = right_root, left_root
    if _direction(left_root, right_root, _OPEN_SET) != "lt":
        raise NotExact(_OPEN_SET)
    roots = (left_root, right_root)
    # midpoint sign must agree with the leading coefficient (opens up => midpoint negative)
    mid = _div_form(_add_forms(left_root, right_root), _from_int(2))
    mid_sign = compare_reals(_poly_eval(coeffs, mid), _zero())
    if leading == "gt" and mid_sign != "lt":
        raise KernelError("the quadratic did not change sign between its roots")
    if leading == "lt" and mid_sign != "gt":
        raise KernelError("the quadratic did not change sign between its roots")
    value = _two_root_sign(relation, leading == "gt", left_root, right_root)
    detail = (
        "The comparison is a quadratic in the binder.",
        "Isabelle exists_sqrt and the quadratic formula give the two real roots when the discriminant is positive.",
        "Substituting each root returns 0, and the square of the constructed square root of the discriminant is the discriminant, by real_sqrt_pow2.",
        "A quadratic changes sign only at those roots. The sign between the roots was checked at the midpoint.",
        f"The roots are {show_form(left_root)} and {show_form(right_root)}.",
        f"The set is {_value_atom(value)}.",
    )
    return value, roots, detail


def _constant_sign(relation: str, positive: bool) -> object:
    # p never zero; sign is constant
    if relation == "eq":
        return set_empty()
    if relation == "lt":
        return set_empty() if positive else _synthetic("univ", None)
    if relation == "le":
        return set_empty() if positive else _synthetic("univ", None)
    raise NotExact(_NOT_FINITE)


def _double_root_sign(relation: str, opens_up: bool, root: RealForm) -> object:
    if relation == "eq":
        return _finite_set((root,))
    if relation == "lt":
        return set_empty() if opens_up else Cover((("lessThan", root, ()), ("greaterThan", root, ())))
    if relation == "le":
        return _finite_set((root,)) if opens_up else _synthetic("univ", None)
    raise NotExact(_NOT_FINITE)


def _two_root_sign(relation: str, opens_up: bool, left: RealForm, right: RealForm) -> object:
    # opens_up: p <= 0 on [left, right], p >= 0 outside
    inside_closed = Interval("atLeastAtMost", left, right)
    inside_open = Interval("greaterThanLessThan", left, right)
    outside_closed = Cover((("atMost", left, ()), ("atLeast", right, ())))
    outside_open = Cover((("lessThan", left, ()), ("greaterThan", right, ())))
    points = _finite_set((left, right))
    if relation == "eq":
        return points
    if relation == "lt":
        return inside_open if opens_up else outside_open
    if relation == "le":
        return inside_closed if opens_up else outside_closed
    raise NotExact(_NOT_FINITE)


def _check_root(coeffs: tuple[RealForm, ...], root: RealForm) -> None:
    if compare_reals(_poly_eval(coeffs, root), _zero()) != "eq":
        raise KernelError("a constructed root did not vanish in the polynomial")


def _poly_term(term: Term, binder: str) -> tuple[RealForm, ...] | None:
    if _is_binder(term, binder):
        return (_zero(), _one())
    if not _mentions(term, binder):
        if contains_set(term):
            return None
        try:
            return (eval_real(term).form,)
        except (NotExact, KernelError):
            return None
    if not isinstance(term, App):
        return None
    if term.op == "neg" and len(term.args) == 1:
        body = _poly_term(term.args[0], binder)
        return None if body is None else _poly_neg(body)
    if term.op in {"add", "sub"} and len(term.args) == 2:
        left = _poly_term(term.args[0], binder)
        right = _poly_term(term.args[1], binder)
        if left is None or right is None:
            return None
        if term.op == "add":
            return _poly_add(left, right)
        return _poly_add(left, _poly_neg(right))
    if term.op == "mul" and len(term.args) == 2:
        left = _poly_term(term.args[0], binder)
        right = _poly_term(term.args[1], binder)
        if left is None or right is None:
            return None
        return _poly_mul(left, right)
    if term.op == "div" and len(term.args) == 2:
        if _mentions(term.args[1], binder) or contains_set(term.args[1]):
            return None
        body = _poly_term(term.args[0], binder)
        if body is None:
            return None
        try:
            divisor = eval_real(term.args[1]).form
            return tuple(_div_form(coeff, divisor) for coeff in body)
        except (NotExact, KernelError):
            return None
    return None


def _poly_add(left: tuple[RealForm, ...], right: tuple[RealForm, ...]) -> tuple[RealForm, ...]:
    size = max(len(left), len(right))
    padded_left = left + (_zero(),) * (size - len(left))
    padded_right = right + (_zero(),) * (size - len(right))
    return tuple(_add_forms(a, b) for a, b in zip(padded_left, padded_right))


def _poly_neg(coeffs: tuple[RealForm, ...]) -> tuple[RealForm, ...]:
    return tuple(_neg_form(coeff) for coeff in coeffs)


def _poly_mul(left: tuple[RealForm, ...], right: tuple[RealForm, ...]) -> tuple[RealForm, ...]:
    acc = [_zero()] * (len(left) + len(right) - 1)
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            acc[i + j] = _add_forms(acc[i + j], _mul_forms(a, b))
    return tuple(acc)


def _poly_trim(coeffs: tuple[RealForm, ...]) -> tuple[RealForm, ...]:
    index = len(coeffs)
    while index > 1 and compare_reals(coeffs[index - 1], _zero()) == "eq":
        index -= 1
    return coeffs[:index]


def _poly_eval(coeffs: tuple[RealForm, ...], value: RealForm) -> RealForm:
    total = _zero()
    power = _one()
    for coeff in coeffs:
        total = _add_forms(total, _mul_forms(coeff, power))
        power = _mul_forms(power, value)
    return total


def _from_int(number: int) -> RealForm:
    return real_of_rat(Ratio(number, 1)).form


def _value_atom(value: object) -> str:
    if isinstance(value, Cover):
        return _cover_atom(value)
    if isinstance(value, Interval):
        return _interval_atom(value)
    if isinstance(value, SetTheorem):
        shown = ", ".join(show_form(item) for item in value.members)
        return "set({" + shown + "})"
    if isinstance(value, CollectForm):
        ray = classify(value)
        if ray is None:
            return "this set"
        if ray.kind == "univ":
            return "univ"
        return f"{ray.kind}({show_form(ray.bound)})"
    return "this set"


def _poly_sign_ok(theorem: PolySignTheorem) -> bool:
    try:
        value, roots, _detail = _polynomial_set(theorem.binder, theorem.relation, theorem.left, theorem.right)
        kind, bound, members, pieces = _connective_shape(value)
    except (NotExact, KernelError):
        return False
    return (
        kind == theorem.kind
        and bound == theorem.bound
        and members == theorem.members
        and pieces == theorem.pieces
        and roots == theorem.roots
    )


def affine_verdict(binder: str, relation: str, left: Term, right: Term) -> tuple[str, RealForm | None] | None:

    if relation == "lt" and _is_binder(left, binder) and _is_binder(right, binder):
        return None
    left_aff = _affine_parts(left, binder)
    right_aff = _affine_parts(right, binder)
    if left_aff is None or right_aff is None:
        return None
    slope = _sub_forms(left_aff[0], right_aff[0])
    direction = compare_reals(slope, _zero())
    if direction == "open":
        return None
    if direction == "eq":
        compared = compare_reals(left_aff[1], right_aff[1])
        if compared == "open":
            return None
        if _relation_holds(relation, compared):
            return "univ", None
        return "empty", None
    try:
        bound = _div_form(_sub_forms(right_aff[1], left_aff[1]), slope)
    except (NotExact, KernelError):
        return None
    flipped = direction == "lt"
    if relation == "eq":
        return "singleton", bound
    if relation == "le":
        return ("atLeast" if flipped else "atMost"), bound
    if relation == "lt":
        return ("greaterThan" if flipped else "lessThan"), bound
    return None


def _affine_ray(form: CollectForm) -> Ray | None:
    verdict = affine_verdict(form.binder, form.relation, form.left, form.right)
    if verdict is None:
        return None
    kind, bound = verdict
    if kind == "univ":
        return Ray("univ", None, form)
    if kind in {"atMost", "atLeast", "lessThan", "greaterThan"} and bound is not None:
        return Ray(kind, bound, form)
    return None


def _affine_parts(term: Term, binder: str) -> tuple[RealForm, RealForm] | None:
    if _is_binder(term, binder):
        return _one(), _zero()
    if not _mentions(term, binder):
        if contains_set(term):
            return None
        try:
            return _zero(), eval_real(term).form
        except (NotExact, KernelError):
            return None
    if not isinstance(term, App):
        return None
    if term.op == "neg" and len(term.args) == 1:
        found = _affine_parts(term.args[0], binder)
        if found is None:
            return None
        return _neg_form(found[0]), _neg_form(found[1])
    if term.op in {"add", "sub"} and len(term.args) == 2:
        left = _affine_parts(term.args[0], binder)
        right = _affine_parts(term.args[1], binder)
        if left is None or right is None:
            return None
        if term.op == "add":
            return _add_forms(left[0], right[0]), _add_forms(left[1], right[1])
        return _sub_forms(left[0], right[0]), _sub_forms(left[1], right[1])
    if term.op == "mul" and len(term.args) == 2:
        return _affine_scale(term.args[0], term.args[1], binder, divide=False)
    if term.op == "div" and len(term.args) == 2:
        return _affine_scale(term.args[0], term.args[1], binder, divide=True)
    return None


def _affine_scale(left: Term, right: Term, binder: str, *, divide: bool) -> tuple[RealForm, RealForm] | None:
    if divide:
        if _mentions(right, binder) or contains_set(right):
            return None
        body = _affine_parts(left, binder)
        if body is None:
            return None
        try:
            factor = eval_real(right).form
            return _div_form(body[0], factor), _div_form(body[1], factor)
        except (NotExact, KernelError):
            return None
    if _mentions(left, binder) and _mentions(right, binder):
        return None
    if not _mentions(left, binder):
        constant, body_term = left, right
    else:
        constant, body_term = right, left
    if contains_set(constant):
        return None
    body = _affine_parts(body_term, binder)
    if body is None:
        return None
    try:
        factor = eval_real(constant).form
        return _mul_forms(body[0], factor), _mul_forms(body[1], factor)
    except (NotExact, KernelError):
        return None


def _relation_holds(relation: str, compared: str) -> bool:
    if relation == "eq":
        return compared == "eq"
    if relation == "le":
        return compared in {"lt", "eq"}
    if relation == "lt":
        return compared == "lt"
    return False


def _affine_lines(form: CollectForm) -> tuple[str, ...]:
    if _reflexive(form):
        return ()
    if form.relation == "le":
        simple = (
            _is_binder(form.left, form.binder) and not _mentions(form.right, form.binder)
        ) or (
            _is_binder(form.right, form.binder) and not _mentions(form.left, form.binder)
        )
        if simple:
            return ()
    if form.relation == "lt":
        simple = (
            _is_binder(form.left, form.binder) and not _mentions(form.right, form.binder)
        ) or (
            _is_binder(form.right, form.binder) and not _mentions(form.left, form.binder)
        )
        if simple:
            return ()
    if affine_verdict(form.binder, form.relation, form.left, form.right) is None:
        return ()
    return _AFFINE


def _join(left_value: object, right_value: object) -> tuple[object, tuple[str, ...]]:
    if isinstance(left_value, Cover) or isinstance(right_value, Cover):
        return _join_covers(left_value, right_value)
    try:
        left = _meet_side(left_value)
        right = _meet_side(right_value)
        kind, bound, members, rule = _join_result(left, right, _OUTSIDE)
    except NotExact:
        return _join_covers(left_value, right_value)
    detail = _join_detail(rule, bound, members)
    RayJoinTheorem(
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


def _join_result(
    left: tuple[str, RealForm | None, tuple[RealForm, ...]],
    right: tuple[str, RealForm | None, tuple[RealForm, ...]],
    message: str,
) -> tuple[str, RealForm | None, tuple[RealForm, ...], str]:
    if left[0] == "univ" or right[0] == "univ":
        return "univ", None, (), "Set.join_univ"
    if left[0] == "finite" and right[0] == "finite":
        return "finite", None, canonical((*left[2], *right[2])), "Set.join_finite"
    if left[0] == "finite":
        return _join_finite(left[2], right, message)
    if right[0] == "finite":
        return _join_finite(right[2], left, message)
    low, high, rule = _merged_ends(left, right, message)
    kind, bound, members = _from_ends(low, high, message)
    return kind, bound, members, rule


def _join_finite(
    members: tuple[RealForm, ...],
    other: tuple[str, RealForm | None, tuple[RealForm, ...]],
    message: str,
) -> tuple[str, RealForm | None, tuple[RealForm, ...], str]:
    if other[0] == "univ":
        return "univ", None, (), "Set.join_univ"
    for member in members:
        if not _in_side(member, other[0], other[1], other[2], message):
            raise NotExact(message)
    return other[0], other[1], other[2], "Set.join_absorb"


def _merged_ends(
    left: tuple[str, RealForm | None, tuple[RealForm, ...]],
    right: tuple[str, RealForm | None, tuple[RealForm, ...]],
    message: str,
) -> tuple[tuple[bool | None, RealForm | None], tuple[bool | None, RealForm | None], str]:
    left_low, left_high = _as_ends(left[0], left[1], left[2], message)
    right_low, right_high = _as_ends(right[0], right[1], right[2], message)
    if _lower_first(left_low, right_low, message):
        first_high, second_low = left_high, right_low
    else:
        first_high, second_low = right_high, left_low
    if not _ends_connect(first_high, second_low, message):
        raise NotExact(message)
    return _weaker_lower(left_low, right_low, message), _weaker_upper(left_high, right_high, message), "Set.join_cover"


def _interval_side_meet(
    left: tuple[str, RealForm | None, tuple[RealForm, ...]],
    right: tuple[str, RealForm | None, tuple[RealForm, ...]],
    message: str,
) -> tuple[str, RealForm | None, tuple[RealForm, ...], str]:
    left_low, left_high = _as_ends(left[0], left[1], left[2], message)
    right_low, right_high = _as_ends(right[0], right[1], right[2], message)
    low = _stricter_lower(left_low, right_low, message)
    high = _stricter_upper(left_high, right_high, message)
    kind, bound, members = _from_ends(low, high, message)
    if kind == "finite" and not members:
        return kind, bound, members, "Set.meet_open_empty"
    if kind == "finite":
        return kind, bound, members, "Set.meet_singleton"
    if kind in _INTERVAL_KINDS:
        return kind, bound, members, f"Set.meet_{kind}"
    if kind in {"atMost", "atLeast", "lessThan", "greaterThan"}:
        return kind, bound, members, f"Set.meet_{kind}"
    if kind == "univ":
        return kind, bound, members, "Set.meet_univ"
    raise NotExact(message)


def _as_ends(
    kind: str,
    bound: RealForm | None,
    members: tuple[RealForm, ...],
    message: str,
) -> tuple[tuple[bool | None, RealForm | None], tuple[bool | None, RealForm | None]]:
    if kind == "univ":
        return (None, None), (None, None)
    if kind == "atMost":
        return (None, None), (False, bound)
    if kind == "lessThan":
        return (None, None), (True, bound)
    if kind == "atLeast":
        return (False, bound), (None, None)
    if kind == "greaterThan":
        return (True, bound), (None, None)
    if kind in _INTERVAL_KINDS:
        if bound is None or len(members) != 1:
            raise NotExact(message)
        return (kind in _OPEN_LOWER, bound), (kind in _OPEN_UPPER, members[0])
    raise NotExact(message)


def _from_ends(
    low: tuple[bool | None, RealForm | None],
    high: tuple[bool | None, RealForm | None],
    message: str,
) -> tuple[str, RealForm | None, tuple[RealForm, ...]]:
    if low[0] is None and high[0] is None:
        return "univ", None, ()
    if low[0] is None:
        kind = "lessThan" if high[0] else "atMost"
        if high[1] is None:
            raise NotExact(message)
        return kind, high[1], ()
    if high[0] is None:
        kind = "greaterThan" if low[0] else "atLeast"
        if low[1] is None:
            raise NotExact(message)
        return kind, low[1], ()
    compared = _direction(low[1], high[1], message)
    if compared == "gt" or (compared == "eq" and (low[0] or high[0])):
        return "finite", None, ()
    if compared == "eq":
        return "finite", None, (low[1],)
    kind = _interval_kind("greaterThan" if low[0] else "atLeast", "lessThan" if high[0] else "atMost")
    if low[1] is None or high[1] is None:
        raise NotExact(message)
    return kind, low[1], (high[1],)


def _lower_first(
    left: tuple[bool | None, RealForm | None],
    right: tuple[bool | None, RealForm | None],
    message: str,
) -> bool:
    if left[0] is None:
        return True
    if right[0] is None:
        return False
    compared = _direction(left[1], right[1], message)
    if compared == "lt":
        return True
    if compared == "gt":
        return False
    return not left[0]


def _ends_connect(
    first_high: tuple[bool | None, RealForm | None],
    second_low: tuple[bool | None, RealForm | None],
    message: str,
) -> bool:
    if first_high[0] is None or second_low[0] is None:
        return True
    compared = _direction(first_high[1], second_low[1], message)
    if compared == "gt":
        return True
    if compared == "lt":
        return False
    return not (first_high[0] and second_low[0])


def _weaker_lower(
    left: tuple[bool | None, RealForm | None],
    right: tuple[bool | None, RealForm | None],
    message: str,
) -> tuple[bool | None, RealForm | None]:
    if left[0] is None or right[0] is None:
        return (None, None)
    compared = _direction(left[1], right[1], message)
    if compared == "lt":
        return left
    if compared == "gt":
        return right
    return (left[0] and right[0], left[1])


def _weaker_upper(
    left: tuple[bool | None, RealForm | None],
    right: tuple[bool | None, RealForm | None],
    message: str,
) -> tuple[bool | None, RealForm | None]:
    if left[0] is None or right[0] is None:
        return (None, None)
    compared = _direction(left[1], right[1], message)
    if compared == "gt":
        return left
    if compared == "lt":
        return right
    return (left[0] and right[0], left[1])


def _stricter_lower(
    left: tuple[bool | None, RealForm | None],
    right: tuple[bool | None, RealForm | None],
    message: str,
) -> tuple[bool | None, RealForm | None]:
    if left[0] is None:
        return right
    if right[0] is None:
        return left
    compared = _direction(left[1], right[1], message)
    if compared == "gt":
        return left
    if compared == "lt":
        return right
    return (left[0] or right[0], left[1])


def _stricter_upper(
    left: tuple[bool | None, RealForm | None],
    right: tuple[bool | None, RealForm | None],
    message: str,
) -> tuple[bool | None, RealForm | None]:
    if left[0] is None:
        return right
    if right[0] is None:
        return left
    compared = _direction(left[1], right[1], message)
    if compared == "lt":
        return left
    if compared == "gt":
        return right
    return (left[0] or right[0], left[1])


def _complement(value: object) -> tuple[object, tuple[str, ...]]:
    if isinstance(value, SetTheorem) and not value.members:
        return _synthetic("univ", None), (
            "Isabelle Compl_empty: - {} = UNIV.",
            _DOUBLE,
        )
    if isinstance(value, Cover):
        return _complement_cover(value)
    if isinstance(value, Interval):
        return _complement_piece((value.kind, value.lower, (value.upper,)))
    if isinstance(value, SetTheorem):
        return _complement_finite(value.members)
    if not isinstance(value, CollectForm):
        raise NotExact(_OUTSIDE)
    ray = classify(value)
    if ray is None:
        raise NotExact(_OUTSIDE)
    if ray.kind == "univ":
        return set_empty(), (
            "The predicate holds at every real, so the comprehension is UNIV.",
            "Isabelle Compl_UNIV_eq: - UNIV = {}.",
        )
    found = _COMPLEMENT.get(ray.kind)
    if found is None or ray.bound is None:
        raise NotExact(_OUTSIDE)
    kind, line = found
    return _synthetic(kind, ray.bound), (line, _DOUBLE)


def _join_ok(theorem: RayJoinTheorem) -> bool:
    left = (theorem.left_kind, theorem.left_bound, theorem.left_members)
    right = (theorem.right_kind, theorem.right_bound, theorem.right_members)
    allowed = {"finite", "univ", "atMost", "atLeast", "lessThan", "greaterThan", *_INTERVAL_KINDS}
    if theorem.left_kind not in allowed or theorem.right_kind not in allowed:
        return False
    if theorem.left_kind not in {"finite", *_INTERVAL_KINDS} and theorem.left_members:
        return False
    if theorem.right_kind not in {"finite", *_INTERVAL_KINDS} and theorem.right_members:
        return False
    if not all(_canonical(item) for item in theorem.left_members + theorem.right_members + theorem.result_members):
        return False
    try:
        kind, bound, members, rule = _join_result(left, right, _OUTSIDE)
    except (NotExact, KernelError):
        return False
    return (
        theorem.result_kind == kind
        and theorem.result_bound == bound
        and theorem.result_members == members
        and theorem.rule == rule
    )


def _join_detail(rule: str, bound: RealForm | None, members: tuple[RealForm, ...]) -> tuple[str, ...]:
    if rule == "Set.join_univ":
        return (
            "Isabelle Un_UNIV_left and Un_UNIV_right: union with UNIV is UNIV.",
            "Isabelle Un_iff: a real is in the union when it is in one side.",
        )
    if rule == "Set.join_finite":
        return (
            "Isabelle Un_def: a union collects the members of either set.",
            "Isabelle Un_iff: membership in a union is membership in one side.",
            "finite_Un: a union of finite sets is finite.",
        )
    if rule == "Set.join_absorb":
        return (
            "Isabelle Un_iff: a real is in the union when it is in one side.",
            "Every listed member already lies in the other set, so the union is that set.",
        )
    if rule == "Set.join_cover":
        if bound is None and not members:
            return (
                "Isabelle Un_iff: a real is in the union when it is in one side.",
                "These two rays cover every real, so their union is UNIV.",
            )
        shown = show_form(bound) if bound is not None else ""
        extra = f" The upper bound is {show_form(members[0])}." if members else ""
        return (
            "Isabelle Un_iff: a real is in the union when it is in one side.",
            "The two sides overlap or touch, so their union is one admitted ray or interval.",
            f"The bound is {shown}.{extra}" if shown else "The union is that admitted set.",
        )
    return (
        "Isabelle Un_iff: a real is in the union when it is in one side.",
    )


def _combine(left_value: object, right_value: object) -> tuple[object, tuple[str, ...]]:
    if isinstance(left_value, Cover) or isinstance(right_value, Cover):
        return _meet_covers(left_value, right_value)
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
        return value.kind, value.lower, (value.upper,)
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
    if left[0] in _INTERVAL_KINDS or right[0] in _INTERVAL_KINDS:
        if left[0] == "finite":
            return "finite", None, _kept(left[2], right[0], right[1], message, right[2]), "Set.meet_filter"
        if right[0] == "finite":
            return "finite", None, _kept(right[2], left[0], left[1], message, left[2]), "Set.meet_filter"
        return _interval_side_meet(left, right, message)
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
    if other[0] in _INTERVAL_KINDS:
        return other[0], other[1], other[2], "Set.meet_univ"
    raise NotExact(message)


def _filter_finite(members: tuple[RealForm, ...], kind: str, bound: RealForm | None, message: str) -> str:
    _kept(members, kind, bound, message)
    return "finite"


def _kept(
    members: tuple[RealForm, ...],
    kind: str,
    bound: RealForm | None,
    message: str,
    side_members: tuple[RealForm, ...] = (),
) -> tuple[RealForm, ...]:
    kept = []
    for member in members:
        if _in_side(member, kind, bound, side_members, message):
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


def _in_side(
    form: RealForm,
    kind: str,
    bound: RealForm | None,
    members: tuple[RealForm, ...],
    message: str,
) -> bool:
    if kind in _INTERVAL_KINDS:
        if bound is None or len(members) != 1:
            raise NotExact(message)
        return _in_interval(kind, bound, members[0], form)
    return _in_ray(form, kind, bound, message)


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
    if theorem.left_kind not in {"finite", *_INTERVAL_KINDS} and theorem.left_members:
        return False
    if theorem.right_kind not in {"finite", *_INTERVAL_KINDS} and theorem.right_members:
        return False
    if theorem.left_kind in _INTERVAL_KINDS and len(theorem.left_members) != 1:
        return False
    if theorem.right_kind in _INTERVAL_KINDS and len(theorem.right_members) != 1:
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
            *_affine_lines(ray.form),
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
    lines.extend(_affine_lines(ray.form))
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
