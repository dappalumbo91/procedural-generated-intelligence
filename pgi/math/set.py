"""Finite sets of the reals this kernel can already check.

Isabelle2025-2 `Set.thy` introduces `empty`, `insert`, and `member`.
`insert_iff` says membership in an insertion is equality with the new element
or membership in the rest. `empty_iff` says the empty set has no members.
`set_eqI` and `subset_antisym` identify two sets that have the same members.
`Un_iff` and `Int_iff` are the union and the intersection. `Finite_Set.thy`
builds `finite` from `finite.emptyI` and `finite.insertI`.

`complete_real` in `Real.thy` says a nonempty set of reals that is bounded
above has a least upper bound. `cSup_eq_maximum` says a member that is an
upper bound is that supremum. `Max_in` and `Max_ge` say the maximum of a
finite nonempty set is a member and bounds the rest. `cSup_eq_Max` identifies
the supremum of a finite nonempty set with that maximum.

Core Lean 4.36.0 resolves `EmptyCollection`, `Membership`, `Insert`, `Union`,
`Inter`, and `Singleton`. It does not resolve `Set` or `Finset`. This module
does not import Lean or Isabelle, and it does not use Octave.

Separation `{x in S. P x}` keeps the members of a finite enumeration that
satisfy `<=` or `=`. The equality shapes `{x. x = a}` and `{x. a = x}` are
the singleton of a closed term. An unbounded predicate over the reals stays
outside this rule, and so does the proof of `complete_real` for an arbitrary
set. Bounded quantifiers over an enumeration are a separate primitive. The
empty set is not a premise of `complete_real`.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cmp_to_key

from pgi.math.kernel import KernelError, NotExact
from pgi.math.real import (
    RealForm,
    RealTheorem,
    _canonical,
    compare_reals,
    eval_real,
    real_trace,
    show_form,
)
from pgi.math.syntax import App, Term, pretty, pretty_eq
from pgi.model import Rule

_SET_OPS = frozenset({"set", "union", "inter", "sup", "collect"})


@dataclass(frozen=True)
class SetTheorem:
    members: tuple[RealForm, ...]
    rule: str
    premises: tuple[SetTheorem, ...] = ()
    element: RealTheorem | None = None
    embedded: SupTheorem | None = None
    detail: tuple[str, ...] = ()
    binder: str = ""
    relation: str = ""
    left: Term | None = None
    right: Term | None = None

    def __post_init__(self) -> None:
        if not _justified_set(self):
            raise KernelError(f"{self.rule} does not justify {show_set(self.members)}")


@dataclass(frozen=True)
class SupTheorem:
    form: RealForm
    members: tuple[RealForm, ...]
    source: SetTheorem
    rule: str
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _justified_sup(self):
            raise KernelError(f"{self.rule} does not justify {show_form(self.form)}")


@dataclass(frozen=True)
class MemberTheorem:
    element: RealForm
    members: tuple[RealForm, ...]
    rule: str
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _justified_member(self):
            raise KernelError(f"{self.rule} does not justify membership")


@dataclass(frozen=True)
class SubsetTheorem:
    left: tuple[RealForm, ...]
    right: tuple[RealForm, ...]
    rule: str
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _justified_subset(self):
            raise KernelError(f"{self.rule} does not justify inclusion")


@dataclass(frozen=True)
class EqTheorem:
    left: tuple[RealForm, ...]
    right: tuple[RealForm, ...]
    rule: str
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.rule != "Set.eq" or self.left != self.right:
            raise KernelError("Set.eq does not justify these sets")
        if self.left != canonical(self.left) or self.right != canonical(self.right):
            raise KernelError("Set.eq does not justify these sets")
        if not _all_canonical(self.left) or not _all_canonical(self.right):
            raise KernelError("Set.eq does not justify these sets")


def contains_set(term: Term) -> bool:
    if isinstance(term, App):
        if term.op in _SET_OPS:
            return True
        return any(contains_set(arg) for arg in term.args)
    return False


def show_set(members: tuple[RealForm, ...]) -> str:
    return "{" + ", ".join(show_form(member) for member in members) + "}"


def require_set(term: Term) -> SetTheorem:
    if not contains_set(term):
        raise NotExact("this expression is not a finite set")
    value = eval_set(term)
    from pgi.math.collect import CollectForm

    if isinstance(value, CollectForm):
        raise NotExact("this comprehension is not a finite enumeration")
    if not isinstance(value, SetTheorem):
        raise NotExact("this expression is not a finite set")
    return value


def eval_element(term: Term) -> RealTheorem | SupTheorem:
    return _as_element(term)


def eval_set(term: Term):
    if not isinstance(term, App):
        raise NotExact("a set does not enter this operation")
    if term.op == "set":
        return _enumerate(term.args)
    if term.op == "union":
        return set_union(_as_set(term.args[0]), _as_set(term.args[1]))
    if term.op == "inter":
        return set_inter(_as_set(term.args[0]), _as_set(term.args[1]))
    if term.op == "sup":
        return set_sup(_as_set(term.args[0]))
    if term.op == "collect":
        from pgi.math.collect import eval_collect

        return eval_collect(term)
    raise NotExact("a set does not enter this operation")


def set_empty() -> SetTheorem:
    return SetTheorem(
        (),
        "Set.empty",
        (),
        None,
        None,
        (
            "Isabelle empty is the bottom set, and empty_iff says it has no members.",
            "Finite_Set.finite.emptyI: the empty set is finite.",
        ),
    )


def set_insert(base: SetTheorem, element: RealTheorem | SupTheorem) -> SetTheorem:
    form, real, embedded = _element_parts(element)
    members = canonical((*base.members, form))
    if form in base.members:
        growth = "Isabelle insert_absorb: a member inserted again is the same set."
    else:
        growth = "The element was not a member, so the enumeration grows by one."
    return SetTheorem(
        members,
        "Set.insert",
        (base,),
        real,
        embedded,
        (
            "Isabelle insert_iff: membership in an insertion is equality with the new element or membership in the rest.",
            growth,
            "Finite_Set.finite.insertI: inserting into a finite set stays finite.",
        ),
    )


def set_union(left: SetTheorem, right: SetTheorem) -> SetTheorem:
    return SetTheorem(
        canonical((*left.members, *right.members)),
        "Set.union",
        (left, right),
        None,
        None,
        (
            "Isabelle Un_def: a union collects the members of either set.",
            "Isabelle Un_iff: membership in a union is membership in one side.",
            "finite_Un: a union of finite sets is finite.",
        ),
    )


def set_inter(left: SetTheorem, right: SetTheorem) -> SetTheorem:
    shared = tuple(item for item in left.members if item in right.members)
    return SetTheorem(
        canonical(shared),
        "Set.inter",
        (left, right),
        None,
        None,
        (
            "Isabelle Int_def: an intersection collects the common members.",
            "Isabelle Int_iff: membership in an intersection is membership in both sides.",
            "finite_Int: an intersection of finite sets is finite.",
        ),
    )


def set_sup(base: SetTheorem) -> SupTheorem:
    if not base.members:
        raise NotExact("complete_real assumes a member. The empty set has none")
    found = maximum(base.members)
    if found is None:
        raise NotExact("the order of these elements is not settled")
    return SupTheorem(found, base.members, base, "Set.sup", _sup_detail(base.members, found))


def set_trace(theorem: SetTheorem) -> tuple[str, ...]:
    lines: list[str] = []
    for premise in theorem.premises:
        lines.extend(set_trace(premise))
    if theorem.element is not None:
        lines.extend(real_trace(theorem.element))
    if theorem.embedded is not None:
        lines.extend(sup_trace(theorem.embedded))
    lines.append(f"{theorem.rule}: {show_set(theorem.members)}")
    lines.extend(theorem.detail)
    return tuple(lines)


def sup_trace(theorem: SupTheorem) -> tuple[str, ...]:
    lines = list(set_trace(theorem.source))
    lines.append(f"{theorem.rule}: {show_form(theorem.form)}")
    lines.extend(theorem.detail)
    return tuple(lines)


def set_value_rule(origin: Term, result: SetTheorem | SupTheorem, prelude: tuple[str, ...] = ()) -> Rule:
    if isinstance(result, SupTheorem):
        lines = (*prelude, *sup_trace(result))
        return _quantity(origin, result.form, lines)
    shown = show_set(result.members)
    return Rule(
        id=_set_id(result.members),
        layer="base",
        stage="quantity",
        title=f"{pretty(origin)} = {shown}",
        produces=f"set({shown})",
        detail_lines=(*prelude, *set_trace(result)),
    )


def member_rule(
    left: Term,
    right: Term,
    element: RealTheorem | SupTheorem,
    base: SetTheorem,
    prelude: tuple[str, ...] = (),
) -> Rule:
    form, _real, embedded = _element_parts(element)
    holds = form in base.members
    rule = "Set.member" if holds else "Set.not_member"
    theorem = MemberTheorem(form, base.members, rule, _member_detail(form, base.members, holds))
    atom_left = pretty(left)
    atom_right = pretty(right)
    lines = (*prelude, *_element_trace(element, embedded), *set_trace(base), *theorem.detail)
    if holds:
        return Rule(
            id="math.member",
            layer="base",
            stage="quantity",
            title=f"{atom_left} in {atom_right}",
            produces=f"member({atom_left},{atom_right})",
            detail_lines=lines,
        )
    return Rule(
        id="math.not_member",
        layer="base",
        stage="quantity",
        title=f"not ({atom_left} in {atom_right})",
        produces=f"not_member({atom_left},{atom_right})",
        detail_lines=lines,
    )


def subset_rule(
    left: Term,
    right: Term,
    left_set: SetTheorem,
    right_set: SetTheorem,
    prelude: tuple[str, ...] = (),
) -> Rule:
    holds = all(item in right_set.members for item in left_set.members)
    rule = "Set.subset" if holds else "Set.not_subset"
    theorem = SubsetTheorem(left_set.members, right_set.members, rule, _subset_detail(left_set.members, right_set.members, holds))
    atom_left = pretty(left)
    atom_right = pretty(right)
    lines = (*prelude, *set_trace(left_set), *set_trace(right_set), *theorem.detail)
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


def set_equality_rules(
    left: Term,
    right: Term,
    left_value: SetTheorem | SupTheorem | RealTheorem,
    right_value: SetTheorem | SupTheorem | RealTheorem,
    prelude: tuple[str, ...] = (),
) -> tuple[Rule, ...]:
    from pgi.math.collect import CollectForm, collect_equality_rules

    if isinstance(left_value, CollectForm) or isinstance(right_value, CollectForm):
        return collect_equality_rules(left, right, left_value, right_value, prelude)
    title = f"{pretty(left)} = {pretty(right)}"
    left_kind = _kind(left_value)
    right_kind = _kind(right_value)
    lines = (*prelude, *_value_trace(left_value), *_value_trace(right_value))
    if left_kind == "set" and right_kind == "set":
        assert isinstance(left_value, SetTheorem) and isinstance(right_value, SetTheorem)
        if left_value.members == right_value.members:
            theorem = EqTheorem(left_value.members, right_value.members, "Set.eq")
            return (
                Rule(
                    id="math.set.eq",
                    layer="base",
                    stage="quantity",
                    title=title,
                    produces=f"identity({title})",
                    detail_lines=(
                        *lines,
                        "Isabelle set_eqI: two sets are equal when they have the same members.",
                        "Isabelle subset_antisym: the two inclusions give equality.",
                        *theorem.detail,
                    ),
                ),
            )
        witness = _eq_witness(left_value.members, right_value.members)
        return (_note(f"{title} is not a theorem. {witness}"),)
    if left_kind == "real" and right_kind == "real":
        left_form = _real_form(left_value)
        right_form = _real_form(right_value)
        if left_form == right_form:
            return (
                Rule(
                    id="math.set.eq",
                    layer="base",
                    stage="quantity",
                    title=title,
                    produces=f"identity({title})",
                    detail_lines=(
                        *lines,
                        "Isabelle cSup_eq_maximum exhibits this real as the least upper bound when the left side is a supremum.",
                        "The two sides have the same normal form.",
                    ),
                ),
            )
        return (_note(f"{title} is not a theorem. {_real_gap(left_form, right_form)}"),)
    return (_note(f"{title} is not a theorem. A set and a real are different objects."),)


class _OpenOrder(Exception):
    pass


def canonical(forms: tuple[RealForm, ...]) -> tuple[RealForm, ...]:
    unique: list[RealForm] = []
    for form in forms:
        if form not in unique:
            unique.append(form)
    try:
        return tuple(sorted(unique, key=cmp_to_key(_math_cmp)))
    except _OpenOrder:
        return tuple(sorted(unique, key=_syn_key))


def maximum(members: tuple[RealForm, ...]) -> RealForm | None:
    if not members:
        return None
    for candidate in members:
        directions = [compare_reals(item, candidate) for item in members]
        if "open" in directions:
            continue
        if all(direction in {"eq", "lt"} for direction in directions):
            return candidate
    return None


def _math_cmp(left: RealForm, right: RealForm) -> int:
    direction = compare_reals(left, right)
    if direction == "lt":
        return -1
    if direction == "gt":
        return 1
    if direction == "eq":
        return 0
    raise _OpenOrder()


def _enumerate(args: tuple[Term, ...]) -> SetTheorem:
    current = set_empty()
    for arg in args:
        current = set_insert(current, _as_element(arg))
    return current


def _as_set(term: Term) -> SetTheorem:
    if isinstance(term, App) and term.op == "sup":
        raise NotExact("union and intersection take sets")
    value = eval_set(term) if contains_set(term) else None
    from pgi.math.collect import CollectForm

    if isinstance(value, CollectForm):
        raise NotExact("this comprehension is not a finite enumeration")
    if not isinstance(value, SetTheorem):
        raise NotExact("union and intersection take sets")
    return value


def _as_element(term: Term) -> RealTheorem | SupTheorem:
    if isinstance(term, App) and term.op == "sup":
        return set_sup(_as_set(term.args[0]))
    if contains_set(term):
        raise NotExact("a set element must be a real expression")
    try:
        return eval_real(term)
    except NotExact:
        raise
    except KernelError as exc:
        if "free variable" in str(exc):
            raise NotExact("a free variable is not a set element") from exc
        raise


def _element_parts(element: RealTheorem | SupTheorem) -> tuple[RealForm, RealTheorem | None, SupTheorem | None]:
    if isinstance(element, SupTheorem):
        return element.form, None, element
    return element.form, element, None


def _element_trace(element: RealTheorem | SupTheorem, embedded: SupTheorem | None) -> tuple[str, ...]:
    if isinstance(element, RealTheorem):
        return real_trace(element)
    if embedded is not None:
        return sup_trace(embedded)
    return sup_trace(element)


def _sup_detail(members: tuple[RealForm, ...], found: RealForm) -> tuple[str, ...]:
    lines = [
        "Isabelle complete_real: a nonempty set of reals that is bounded above has a least upper bound.",
        "Finite_Set.finite.emptyI and finite.insertI: this enumeration is finite.",
        "Isabelle Max_in: the maximum of a finite nonempty set is a member.",
        "Isabelle Max_ge: every member is less than or equal to that maximum.",
        "Isabelle bdd_aboveI: that maximum is an upper bound of the set.",
        "Isabelle cSup_eq_maximum: a member that bounds the set above is the supremum.",
        "Isabelle cSup_eq_Max: the supremum of a finite nonempty set is its maximum.",
        "The general statement quantifies over an arbitrary set. An arbitrary set is outside this rule.",
    ]
    if len(members) == 1:
        lines.append("Isabelle cSup_singleton: the supremum of a singleton is its element.")
    for item in members:
        direction = compare_reals(item, found)
        if direction == "eq":
            place = "the same real"
        elif direction == "lt":
            place = "strictly below it"
        else:
            place = "not settled against it"
        lines.append(f"{show_form(item)} is {place}.")
    return tuple(lines)


def _member_detail(element: RealForm, members: tuple[RealForm, ...], holds: bool) -> tuple[str, ...]:
    lines = [
        "Isabelle empty_iff: the empty set has no members.",
        "Isabelle insert_iff: membership in an insertion is equality with the new element or membership in the rest.",
    ]
    if len(members) == 1:
        lines.append("Isabelle singleton_iff: membership in a singleton is equality with its element.")
    if holds:
        lines.append(f"{show_form(element)} has the same normal form as a member.")
    else:
        lines.append(f"{show_form(element)} equals none of the members.")
    return tuple(lines)


def _subset_detail(left: tuple[RealForm, ...], right: tuple[RealForm, ...], holds: bool) -> tuple[str, ...]:
    lines = ["Isabelle subset_eq: a set is contained when every member of it is a member of the other."]
    if not left:
        lines.append("Isabelle empty_subsetI: the empty set is contained in every set.")
    if holds:
        lines.append("Every member of the left set is a member of the right set.")
        return tuple(lines)
    missing = next(item for item in left if item not in right)
    lines.append(f"{show_form(missing)} is a member of the left set and is outside the right set.")
    return tuple(lines)


def _eq_witness(left: tuple[RealForm, ...], right: tuple[RealForm, ...]) -> str:
    for item in left:
        if item not in right:
            return f"{show_form(item)} is a member of the left set and is outside the right set."
    for item in right:
        if item not in left:
            return f"{show_form(item)} is a member of the right set and is outside the left set."
    return "The two enumerations differ."


def _real_gap(left: RealForm, right: RealForm) -> str:
    direction = compare_reals(left, right)
    if direction == "lt":
        return "The left side is strictly below the right side."
    if direction == "gt":
        return "The left side is strictly above the right side."
    if direction == "open":
        return "The two Cauchy classes were not separated in this slice."
    return "The two sides differ."


def _quantity(origin: Term, form: RealForm, lines: tuple[str, ...]) -> Rule:
    title_left = pretty(origin)
    shown = show_form(form)
    if not form.terms and not form.towers and not form.nests and not form.pairs and not form.deeps and not form.highs and not form.peaks and not form.crests and not form.summits and not form.apexes and not form.shells and not form.folds and not form.quads and not form.algebras:
        number = form.constant
        if number.den == 1:
            return Rule(
                id=f"math.value.{number.num}",
                layer="base",
                stage="quantity",
                title=f"{title_left} = {number.num}",
                produces=f"value({number.num})",
                detail_lines=lines,
            )
        return Rule(
            id=f"math.ratio.{number.num}.{number.den}",
            layer="base",
            stage="quantity",
            title=f"{title_left} = {number.num}/{number.den}",
            produces=f"ratio({number.num},{number.den})",
            detail_lines=(*lines, "The least upper bound is a constant rational."),
        )
    return Rule(
        id=_sup_id(form),
        layer="base",
        stage="quantity",
        title=f"{title_left} = {shown}",
        produces=f"cauchy({shown})",
        detail_lines=lines,
    )


def _kind(value: SetTheorem | SupTheorem | RealTheorem) -> str:
    if isinstance(value, SetTheorem):
        return "set"
    return "real"


def _real_form(value: SupTheorem | RealTheorem | SetTheorem) -> RealForm:
    if isinstance(value, SetTheorem):
        raise KernelError("a set has no real form")
    return value.form


def _value_trace(value: SetTheorem | SupTheorem | RealTheorem) -> tuple[str, ...]:
    if isinstance(value, SetTheorem):
        return set_trace(value)
    if isinstance(value, SupTheorem):
        return sup_trace(value)
    from pgi.math.arbitrary import BisectTheorem, IntervalSupTheorem, RaySupTheorem

    if isinstance(value, RaySupTheorem | BisectTheorem | IntervalSupTheorem):
        return value.detail
    return real_trace(value)


def _syn_key(form: RealForm) -> tuple:
    return (
        form.constant.num,
        form.constant.den,
        tuple((rad, coeff.num, coeff.den) for coeff, rad in form.terms),
        tuple((base, log_den, numer, coeff.num, coeff.den) for coeff, base, numer, log_den in form.towers),
        tuple(
            (rad, constant.num, constant.den, sqrt_coeff.num, sqrt_coeff.den, coeff.num, coeff.den)
            for coeff, constant, sqrt_coeff, rad in form.nests
        ),
        tuple(
            (left_r, right_r, left_c, right_c, coeff.num, coeff.den)
            for coeff, left_c, left_r, right_c, right_r in form.pairs
        ),
        tuple(
            (rad, constant, sqrt_coeff, mult, coeff.num, coeff.den)
            for coeff, mult, constant, sqrt_coeff, rad in form.deeps
        ),
        tuple(
            (left_r, right_r, left_c, right_c, mult, coeff.num, coeff.den)
            for coeff, mult, left_c, left_r, right_c, right_r in form.highs
        ),
        tuple(
            (left_r, right_r, left_c, right_c, hmult, pmult, coeff.num, coeff.den)
            for coeff, pmult, hmult, left_c, left_r, right_c, right_r in form.peaks
        ),
        tuple(
            (left_r, right_r, left_c, right_c, hmult, pmult, qmult, coeff.num, coeff.den)
            for coeff, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.crests
        ),
        tuple(
            (
                left_r,
                right_r,
                left_c,
                right_c,
                hmult,
                pmult,
                qmult,
                smult,
                coeff.num,
                coeff.den,
            )
            for coeff, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.summits
        ),
        tuple(
            (
                left_r,
                right_r,
                left_c,
                right_c,
                hmult,
                pmult,
                qmult,
                smult,
                amult,
                coeff.num,
                coeff.den,
            )
            for coeff, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.apexes
        ),
        tuple(
            (
                left_r,
                right_r,
                left_c,
                right_c,
                hmult,
                pmult,
                qmult,
                smult,
                amult,
                extra,
                coeff.num,
                coeff.den,
            )
            for coeff, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.shells
        ),
        tuple(
            (rad, constant, sqrt_coeff, mult, extra, coeff.num, coeff.den)
            for coeff, extra, mult, constant, sqrt_coeff, rad in form.folds
        ),
        tuple(
            (
                first,
                second,
                constant.num,
                constant.den,
                first_coeff.num,
                first_coeff.den,
                second_coeff.num,
                second_coeff.den,
                product_coeff.num,
                product_coeff.den,
                coeff.num,
                coeff.den,
            )
            for coeff, constant, first_coeff, first, second_coeff, second, product_coeff in form.quads
        ),
    )


def _set_id(members: tuple[RealForm, ...]) -> str:
    if not members:
        return "math.set.empty"
    return "math.set." + ".".join(_form_token(member) for member in members)


def _sup_id(form: RealForm) -> str:
    return "math.sup." + _form_token(form)


def _form_token(form: RealForm) -> str:
    parts = [f"{form.constant.num}.{form.constant.den}".replace("-", "m")]
    for coeff, rad in form.terms:
        parts.append(f"{coeff.num}.{coeff.den}.{rad}".replace("-", "m"))
    for coeff, base, numer, log_den in form.towers:
        parts.append(f"{coeff.num}.{coeff.den}.{base}.{numer}.{log_den}".replace("-", "m"))
    for coeff, constant, sqrt_coeff, rad in form.nests:
        parts.append(
            f"{coeff.num}.{coeff.den}.{constant.num}.{constant.den}.{sqrt_coeff.num}.{sqrt_coeff.den}.{rad}".replace(
                "-", "m"
            )
        )
    for coeff, left_c, left_r, right_c, right_r in form.pairs:
        parts.append(
            f"{coeff.num}.{coeff.den}.{left_c}.{left_r}.{right_c}.{right_r}".replace("-", "m")
        )
    for coeff, mult, constant, sqrt_coeff, rad in form.deeps:
        parts.append(
            f"{coeff.num}.{coeff.den}.{mult}.{constant}.{sqrt_coeff}.{rad}".replace("-", "m")
        )
    for coeff, mult, left_c, left_r, right_c, right_r in form.highs:
        parts.append(
            f"{coeff.num}.{coeff.den}.{mult}.{left_c}.{left_r}.{right_c}.{right_r}".replace("-", "m")
        )
    for coeff, pmult, hmult, left_c, left_r, right_c, right_r in form.peaks:
        parts.append(
            f"{coeff.num}.{coeff.den}.{pmult}.{hmult}.{left_c}.{left_r}.{right_c}.{right_r}".replace("-", "m")
        )
    for coeff, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.crests:
        parts.append(
            f"{coeff.num}.{coeff.den}.{qmult}.{pmult}.{hmult}.{left_c}.{left_r}.{right_c}.{right_r}".replace(
                "-", "m"
            )
        )
    for coeff, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.summits:
        parts.append(
            f"{coeff.num}.{coeff.den}.{smult}.{qmult}.{pmult}.{hmult}.{left_c}.{left_r}.{right_c}.{right_r}".replace(
                "-", "m"
            )
        )
    for coeff, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.apexes:
        parts.append(
            f"{coeff.num}.{coeff.den}.{amult}.{smult}.{qmult}.{pmult}.{hmult}.{left_c}.{left_r}.{right_c}.{right_r}".replace(
                "-", "m"
            )
        )
    for coeff, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.shells:
        mults = ".".join(str(mult) for mult in extra)
        parts.append(
            f"{coeff.num}.{coeff.den}.{mults}.{amult}.{smult}.{qmult}.{pmult}.{hmult}.{left_c}.{left_r}.{right_c}.{right_r}".replace(
                "-", "m"
            )
        )
    for coeff, extra, mult, constant, sqrt_coeff, rad in form.folds:
        mults = ".".join(str(item) for item in extra)
        parts.append(
            f"{coeff.num}.{coeff.den}.{mults}.{mult}.{constant}.{sqrt_coeff}.{rad}".replace("-", "m")
        )
    for coeff, constant, first_coeff, first, second_coeff, second, product_coeff in form.quads:
        parts.append(
            f"{coeff.num}.{coeff.den}.{constant.num}.{constant.den}.{first_coeff.num}.{first_coeff.den}.{first}.{second_coeff.num}.{second_coeff.den}.{second}.{product_coeff.num}.{product_coeff.den}".replace(
                "-", "m"
            )
        )
    for coeff, coeffs, index in form.algebras:
        poly = ".".join(str(value).replace("-", "m") for value in coeffs)
        parts.append(f"{coeff.num}.{coeff.den}.{poly}.{index}".replace("-", "m"))
    return "e" + "_".join(parts)


def _note(text: str) -> Rule:
    return Rule(
        id="math.open",
        layer="base",
        stage="check",
        title=text,
        produces=f"open({text})",
        detail_lines=(text,),
    )


def _all_canonical(forms: tuple[RealForm, ...]) -> bool:
    return all(_canonical(form) for form in forms)


def _justified_set(theorem: SetTheorem) -> bool:
    from pgi.math.quant import _FreeVariable, _OpenPredicate

    try:
        if not _all_canonical(theorem.members) or theorem.members != canonical(theorem.members):
            return False
        rule = theorem.rule
        premises = theorem.premises
        if rule == "Set.empty":
            return theorem.members == () and not premises and theorem.element is None and theorem.embedded is None
        if rule == "Set.insert":
            form = theorem.element.form if theorem.element is not None else None
            if form is None and theorem.embedded is not None:
                form = theorem.embedded.form
            if form is None or len(premises) != 1:
                return False
            if theorem.element is not None and theorem.embedded is not None:
                return False
            return theorem.members == canonical((*premises[0].members, form))
        if rule == "Set.union":
            if len(premises) != 2 or theorem.element is not None or theorem.embedded is not None:
                return False
            return theorem.members == canonical((*premises[0].members, *premises[1].members))
        if rule == "Set.inter":
            if len(premises) != 2 or theorem.element is not None or theorem.embedded is not None:
                return False
            shared = tuple(item for item in premises[0].members if item in premises[1].members)
            return theorem.members == canonical(shared)
        if rule == "Set.collect":
            if len(premises) != 1 or theorem.element is not None or theorem.embedded is not None:
                return False
            if theorem.relation not in {"le", "eq"} or not theorem.binder or theorem.left is None or theorem.right is None:
                return False
            from pgi.math.collect import selected_members

            kept = selected_members(premises[0].members, theorem.binder, theorem.relation, theorem.left, theorem.right)
            return theorem.members == kept
        if rule == "Set.singleton":
            if premises or theorem.element is None or theorem.embedded is not None:
                return False
            if theorem.relation != "eq" or not theorem.binder or theorem.left is None or theorem.right is None:
                return False
            from pgi.math.collect import singleton_form

            form = singleton_form(theorem.binder, theorem.relation, theorem.left, theorem.right)
            return theorem.members == (form,) and theorem.element.form == form
    except (NotExact, KernelError, _FreeVariable, _OpenPredicate):
        return False
    return False


def _justified_sup(theorem: SupTheorem) -> bool:
    try:
        if theorem.rule != "Set.sup":
            return False
        if theorem.source.members != theorem.members or not _all_canonical(theorem.members):
            return False
        if not _canonical(theorem.form):
            return False
        return maximum(theorem.members) == theorem.form
    except (NotExact, KernelError):
        return False


def _justified_member(theorem: MemberTheorem) -> bool:
    if not _canonical(theorem.element) or not _all_canonical(theorem.members):
        return False
    if theorem.members != canonical(theorem.members):
        return False
    holds = theorem.element in theorem.members
    if theorem.rule == "Set.member":
        return holds
    if theorem.rule == "Set.not_member":
        return not holds
    return False


def _justified_subset(theorem: SubsetTheorem) -> bool:
    if not _all_canonical(theorem.left) or not _all_canonical(theorem.right):
        return False
    if theorem.left != canonical(theorem.left) or theorem.right != canonical(theorem.right):
        return False
    holds = all(item in theorem.right for item in theorem.left)
    if theorem.rule == "Set.subset":
        return holds
    if theorem.rule == "Set.not_subset":
        return not holds
    return False
