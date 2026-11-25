"""Separation over a finite enumeration, and the singleton equality comprehension.

Isabelle Set.thy axiomatizes `Collect`. `mem_Collect_eq` says membership in
`Collect P` is the predicate at that element. The separation `{p ∈ A. P}` is
`Collect` of membership in `A` and `P`. `Collect_subset` says that separation
is contained in `A`. `Finite_Set.finite_subset` says a subset of a finite set
is finite.

`singleton_conv` and `singleton_conv2` identify `{x. x = a}` and `{x. a = x}`
with the singleton `{a}`. An unbounded predicate that is not that equality
stays outside this rule. The proof of `complete_real` for an arbitrary set
stays outside this rule.

Core Lean 4.36.0 does not resolve `Collect`, `Set.sep`, or `setOf`. This
module does not import Lean or Isabelle, and it does not use Octave.
"""

from __future__ import annotations

from dataclasses import dataclass

from pgi.math.kernel import KernelError, NotExact
from pgi.math.quant import Pred, _FreeVariable, _OpenPredicate, _holds
from pgi.math.rational import Ratio
from pgi.math.real import RealForm, _canonical, eval_real, show_form
from pgi.math.set import (
    SetTheorem,
    canonical,
    contains_set,
    eval_element,
    eval_set,
    member_rule,
    subset_rule,
)
from pgi.math.set import _element_parts, _element_trace
from pgi.math.syntax import App, IntLit, Term, Var, pretty
from pgi.model import Rule

_BOUND = "_bound"


@dataclass(frozen=True)
class CollectForm:
    binder: str
    relation: str
    left: Term
    right: Term


@dataclass(frozen=True)
class CollectMemberTheorem:
    element: RealForm
    binder: str
    relation: str
    left: Term
    right: Term
    rule: str
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _justified_member(self):
            raise KernelError(f"{self.rule} does not justify membership")


@dataclass(frozen=True)
class CollectSubsetTheorem:
    members: tuple[RealForm, ...]
    binder: str
    relation: str
    left: Term
    right: Term
    witness: RealForm | None
    rule: str
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _justified_subset(self):
            raise KernelError(f"{self.rule} does not justify inclusion")


@dataclass(frozen=True)
class CollectCongTheorem:
    left_binder: str
    left_relation: str
    left_left: Term
    left_right: Term
    right_binder: str
    right_relation: str
    right_left: Term
    right_right: Term
    rule: str
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.rule != "Collect.cong" or not _safe_agree(self):
            raise KernelError("Collect.cong does not justify this equality")


def eval_collect(term: Term) -> SetTheorem | CollectForm:
    if not isinstance(term, App) or term.op != "collect" or len(term.args) != 3:
        raise NotExact("this comprehension is not settled")
    binder_term, domain, predicate = term.args
    if not isinstance(binder_term, Var) or not isinstance(predicate, App) or predicate.op not in {"le", "eq", "lt"}:
        raise NotExact("this comprehension is not settled")
    if len(predicate.args) != 2:
        raise NotExact("this comprehension is not settled")
    binder = binder_term.name
    left, right = predicate.args
    _reject_set_operand(left, right)
    if predicate.op == "lt" and not (isinstance(domain, App) and domain.op == "type"):
        raise NotExact("a strict comparison on a finite enumeration stays outside this rule")
    if isinstance(domain, App) and domain.op == "type":
        return _unbounded(binder, predicate.op, left, right)
    domain_value = eval_set(domain)
    if isinstance(domain_value, CollectForm):
        raise NotExact("this comprehension is not a finite enumeration")
    if not isinstance(domain_value, SetTheorem):
        raise NotExact("this expression is not a finite set")
    try:
        kept = selected_members(domain_value.members, binder, predicate.op, left, right)
    except _OpenPredicate as exc:
        raise NotExact("this comprehension is not settled") from exc
    return SetTheorem(
        kept,
        "Set.collect",
        (domain_value,),
        None,
        None,
        _collect_detail(domain_value.members, kept),
        binder=binder,
        relation=predicate.op,
        left=left,
        right=right,
    )


def selected_members(
    members: tuple[RealForm, ...],
    binder: str,
    relation: str,
    left: Term,
    right: Term,
) -> tuple[RealForm, ...]:
    _reject_set_operand(left, right)
    if not members:
        return ()
    kept: list[RealForm] = []
    try:
        for member in members:
            if _holds(Pred(relation, left, right), binder, member):
                kept.append(member)
    except _FreeVariable as exc:
        raise NotExact("a free variable stays open") from exc
    except NotExact as exc:
        raise NotExact(_remap(str(exc))) from exc
    return canonical(tuple(kept))


def singleton_form(binder: str, relation: str, left: Term | None, right: Term | None) -> RealForm:
    side = _singleton_term(binder, relation, left, right)
    if side is None:
        raise KernelError("Set.singleton does not justify this comprehension")
    if contains_set(side):
        raise NotExact("a set does not enter this comprehension")
    return eval_real(side).form


def collect_relation_rules(
    kind: str,
    left: Term,
    right: Term,
    left_body: Term,
    right_body: Term,
    prelude: tuple[str, ...],
) -> tuple[Rule, ...]:
    if kind == "in":
        return _relate_member(left, right, left_body, right_body, prelude)
    return _relate_subset(left, right, left_body, right_body, prelude)


def collect_equality_rules(
    left: Term,
    right: Term,
    left_value: object,
    right_value: object,
    prelude: tuple[str, ...] = (),
) -> tuple[Rule, ...]:
    title = f"{pretty(left)} = {pretty(right)}"
    if isinstance(left_value, CollectForm) and isinstance(right_value, CollectForm):
        return _cong_rules(title, left_value, right_value, prelude)
    finite = left_value if isinstance(left_value, SetTheorem) else right_value if isinstance(right_value, SetTheorem) else None
    form = left_value if isinstance(left_value, CollectForm) else right_value if isinstance(right_value, CollectForm) else None
    if not isinstance(finite, SetTheorem) or not isinstance(form, CollectForm):
        return (_note("this comprehension is not a finite enumeration"),)
    try:
        witness = _failing_member(finite.members, form)
    except NotExact as exc:
        return (_note(str(exc)),)
    if witness is not None:
        shown = show_form(witness)
        return (_note(f"{title} is not a theorem. {shown} is a member of the finite set and fails the predicate."),)
    from pgi.math.arbitrary import ray_equality_rules

    return ray_equality_rules(title, left_value, right_value, prelude)


def _unbounded(binder: str, relation: str, left: Term, right: Term) -> SetTheorem | CollectForm:
    found = _singleton_parts(binder, relation, left, right)
    if found is None:
        return CollectForm(binder, relation, left, right)
    side, lemma = found
    if contains_set(side):
        raise NotExact("a set does not enter this comprehension")
    try:
        element = eval_real(side)
    except KernelError as exc:
        if "free variable" in str(exc):
            raise NotExact("a free variable stays open") from exc
        raise
    return SetTheorem(
        (element.form,),
        "Set.singleton",
        (),
        element,
        None,
        _singleton_detail(lemma, element.form),
        binder=binder,
        relation="eq",
        left=left,
        right=right,
    )


def _relate_member(left: Term, right: Term, left_body: Term, right_body: Term, prelude: tuple[str, ...]) -> tuple[Rule, ...]:
    if not contains_set(right_body):
        raise NotExact("this expression is not a finite set")
    from pgi.math.arbitrary import interpret

    right_value, extra = interpret(right_body)
    prelude = (*prelude, *extra)
    if isinstance(right_value, SetTheorem):
        element = eval_element(left_body)
        return (member_rule(left, right, element, right_value, prelude),)
    if not isinstance(right_value, CollectForm):
        raise NotExact("this expression is not a finite set")
    if contains_set(left_body):
        raise NotExact("a set does not enter this comprehension")
    element = eval_element(left_body)
    return (collect_member_rule(left, right, element, right_value, prelude),)


def _relate_subset(left: Term, right: Term, left_body: Term, right_body: Term, prelude: tuple[str, ...]) -> tuple[Rule, ...]:
    from pgi.math.arbitrary import interpret, ray_subset_rule

    left_value, left_extra = interpret(left_body) if contains_set(left_body) else (None, ())
    right_value, right_extra = interpret(right_body) if contains_set(right_body) else (None, ())
    prelude = (*prelude, *left_extra, *right_extra)
    if isinstance(left_value, SetTheorem) and isinstance(right_value, CollectForm):
        return (collect_subset_rule(left, right, left_value, right_value, prelude),)
    if isinstance(left_value, CollectForm):
        return (ray_subset_rule(left, right, left_value, right_value, prelude),)
    if isinstance(left_value, SetTheorem) and isinstance(right_value, SetTheorem):
        return (subset_rule(left, right, left_value, right_value, prelude),)
    raise NotExact("this expression is not a finite set")


def collect_member_rule(left: Term, right: Term, element, form: CollectForm, prelude: tuple[str, ...]) -> Rule:
    real_form, _real, embedded = _element_parts(element)
    try:
        holds = _holds(Pred(form.relation, form.left, form.right), form.binder, real_form)
    except _OpenPredicate as exc:
        raise NotExact("this comprehension is not settled") from exc
    except _FreeVariable as exc:
        raise NotExact("a free variable stays open") from exc
    except NotExact as exc:
        raise NotExact(_remap(str(exc))) from exc
    rule = "Collect.member" if holds else "Collect.not_member"
    theorem = CollectMemberTheorem(
        real_form,
        form.binder,
        form.relation,
        form.left,
        form.right,
        rule,
        _member_detail(holds, real_form),
    )
    atom_left = pretty(left)
    atom_right = pretty(right)
    lines = (*prelude, *_element_trace(element, embedded), *theorem.detail)
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


def collect_subset_rule(
    left: Term,
    right: Term,
    base: SetTheorem,
    form: CollectForm,
    prelude: tuple[str, ...],
) -> Rule:
    if not base.members:
        theorem = CollectSubsetTheorem(
            (),
            form.binder,
            form.relation,
            form.left,
            form.right,
            None,
            "Collect.subset",
            _empty_subset_detail(),
        )
        return _subset_rule(left, right, True, prelude, theorem.detail, ())
    try:
        witness = _failing_member(base.members, form)
    except _OpenPredicate as exc:
        raise NotExact("this comprehension is not settled") from exc
    holds = witness is None
    rule = "Collect.subset" if holds else "Collect.not_subset"
    detail = _subset_holds_detail(base.members) if holds else _subset_fails_detail(witness)
    theorem = CollectSubsetTheorem(
        base.members,
        form.binder,
        form.relation,
        form.left,
        form.right,
        None if holds else witness,
        rule,
        detail,
    )
    from pgi.math.set import set_trace

    return _subset_rule(left, right, holds, (*prelude, *set_trace(base)), theorem.detail, ())


def _cong_rules(title: str, left: CollectForm, right: CollectForm, prelude: tuple[str, ...]) -> tuple[Rule, ...]:
    try:
        agreed = _predicates_agree(
            left.binder,
            left.relation,
            left.left,
            left.right,
            right.binder,
            right.relation,
            right.left,
            right.right,
        )
    except NotExact as exc:
        return (_note(_remap(str(exc))),)
    if not agreed:
        from pgi.math.arbitrary import ray_equality_rules

        return ray_equality_rules(title, left, right, prelude)
    theorem = CollectCongTheorem(
        left.binder,
        left.relation,
        left.left,
        left.right,
        right.binder,
        right.relation,
        right.left,
        right.right,
        "Collect.cong",
        _cong_detail(),
    )
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


def _failing_member(members: tuple[RealForm, ...], form: CollectForm) -> RealForm | None:
    if not members:
        return None
    _reject_set_operand(form.left, form.right)
    saw_open = False
    try:
        for member in members:
            try:
                holds = _holds(Pred(form.relation, form.left, form.right), form.binder, member)
            except _OpenPredicate:
                saw_open = True
                continue
            if not holds:
                return member
    except _FreeVariable as exc:
        raise NotExact("a free variable stays open") from exc
    except NotExact as exc:
        raise NotExact(_remap(str(exc))) from exc
    if saw_open:
        raise NotExact("this comprehension is not settled")
    return None


def _subset_rule(
    left: Term,
    right: Term,
    holds: bool,
    prelude: tuple[str, ...],
    detail: tuple[str, ...],
    extra: tuple[str, ...],
) -> Rule:
    atom_left = pretty(left)
    atom_right = pretty(right)
    lines = (*prelude, *extra, *detail)
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


def _collect_detail(domain: tuple[RealForm, ...], kept: tuple[RealForm, ...]) -> tuple[str, ...]:
    lines = [
        "Isabelle Collect builds the set of values that satisfy a predicate.",
        "Isabelle mem_Collect_eq: membership in Collect P is the predicate at that element.",
        "Isabelle CollectI: a value that satisfies the predicate is a member.",
        "Isabelle CollectD: a member satisfies the predicate.",
        "Isabelle Collect_subset: {x ∈ A. P x} is a subset of A.",
        "Finite_Set.finite_subset: a subset of a finite set is finite.",
    ]
    if not domain:
        lines.append("The domain is empty, so the separation is empty. The body is not evaluated.")
        return tuple(lines)
    for member in domain:
        if member in kept:
            lines.append(f"{show_form(member)} satisfies the predicate.")
        else:
            lines.append(f"{show_form(member)} does not satisfy the predicate.")
    if not kept:
        lines.append("No member satisfies the predicate.")
    return tuple(lines)


def _singleton_detail(lemma: str, form: RealForm) -> tuple[str, ...]:
    if lemma == "singleton_conv":
        named = "Isabelle singleton_conv: {x. x = a} = {a}."
    else:
        named = "Isabelle singleton_conv2: {x. a = x} = {a}."
    return (
        named,
        "Isabelle mem_Collect_eq: membership in Collect P is the predicate at that element.",
        "Isabelle singleton_iff: membership in a singleton is equality with its element.",
        f"The member is {show_form(form)}.",
    )


def _member_detail(holds: bool, form: RealForm) -> tuple[str, ...]:
    if holds:
        return (
            "Isabelle mem_Collect_eq: membership in Collect P is the predicate at that element.",
            "Isabelle CollectI: a value that satisfies the predicate is a member.",
            f"{show_form(form)} satisfies the predicate.",
        )
    return (
        "Isabelle mem_Collect_eq: membership in Collect P is the predicate at that element.",
        "Isabelle CollectD: a member of the comprehension satisfies the predicate.",
        f"{show_form(form)} does not satisfy the predicate.",
    )


def _empty_subset_detail() -> tuple[str, ...]:
    return (
        "Isabelle empty_subsetI: the empty set is contained in every set.",
        "The body is not evaluated.",
        "Isabelle mem_Collect_eq: membership in Collect P is the predicate at that element.",
    )


def _subset_holds_detail(members: tuple[RealForm, ...]) -> tuple[str, ...]:
    lines = [
        "Isabelle subset_eq: a set is contained when every member of it is a member of the other.",
        "Isabelle mem_Collect_eq: membership in Collect P is the predicate at that element.",
        "Isabelle CollectI: a value that satisfies the predicate is a member.",
    ]
    for member in members:
        lines.append(f"{show_form(member)} satisfies the predicate.")
    return tuple(lines)


def _subset_fails_detail(witness: RealForm | None) -> tuple[str, ...]:
    shown = show_form(witness) if witness is not None else ""
    return (
        "Isabelle subset_eq: a set is contained when every member of it is a member of the other.",
        "Isabelle mem_Collect_eq: membership in Collect P is the predicate at that element.",
        "Isabelle CollectD: a member of the comprehension satisfies the predicate.",
        f"{shown} is a member of the finite set and fails the predicate.",
    )


def _cong_detail() -> tuple[str, ...]:
    return (
        "Isabelle Collect_cong: two comprehensions are the same set when their predicates agree at every value.",
        "Isabelle mem_Collect_eq: membership in Collect P is the predicate at that element.",
        "The predicates agree after the closed parts are reduced.",
    )


def _singleton_parts(binder: str, relation: str, left: Term, right: Term) -> tuple[Term, str] | None:
    side = _singleton_term(binder, relation, left, right)
    if side is None:
        return None
    if isinstance(left, Var) and left.name == binder:
        return side, "singleton_conv"
    return side, "singleton_conv2"


def _singleton_term(binder: str, relation: str, left: Term | None, right: Term | None) -> Term | None:
    if relation != "eq" or left is None or right is None or not binder:
        return None
    if isinstance(left, Var) and left.name == binder and binder not in _frees(right):
        return right
    if isinstance(right, Var) and right.name == binder and binder not in _frees(left):
        return left
    return None


def _reject_set_operand(left: Term, right: Term) -> None:
    if contains_set(left) or contains_set(right):
        raise NotExact("a set does not enter this comprehension")


def _predicates_agree(
    left_binder: str,
    left_relation: str,
    left_left: Term,
    left_right: Term,
    right_binder: str,
    right_relation: str,
    right_left: Term,
    right_right: Term,
) -> bool:
    if left_relation != right_relation or left_relation not in {"le", "eq"}:
        return False
    left_pair = (_canon_side(left_left, left_binder), _canon_side(left_right, left_binder))
    right_pair = (_canon_side(right_left, right_binder), _canon_side(right_right, right_binder))
    return left_pair == right_pair


def _safe_agree(theorem: CollectCongTheorem) -> bool:
    try:
        return _predicates_agree(
            theorem.left_binder,
            theorem.left_relation,
            theorem.left_left,
            theorem.left_right,
            theorem.right_binder,
            theorem.right_relation,
            theorem.right_left,
            theorem.right_right,
        )
    except (NotExact, KernelError, _FreeVariable, _OpenPredicate):
        return False


def _canon_side(term: Term, binder: str) -> Term:
    return _rename(_freeze(term, binder), binder)


def _freeze(term: Term, binder: str) -> Term:
    if isinstance(term, Var):
        if term.name == binder:
            return term
        raise NotExact("a free variable stays open")
    if isinstance(term, IntLit):
        return term
    if not isinstance(term, App):
        raise NotExact("a free variable stays open")
    if term.op == "collect" or contains_set(term):
        raise NotExact("a set does not enter this comprehension")
    if not _mentions(term, binder):
        return _term_of_form(eval_real(term).form)
    return App(term.op, tuple(_freeze(arg, binder) for arg in term.args))


def _mentions(term: Term, binder: str) -> bool:
    if isinstance(term, Var):
        return term.name == binder
    if isinstance(term, App):
        return any(_mentions(arg, binder) for arg in term.args)
    return False


def _rename(term: Term, binder: str) -> Term:
    if isinstance(term, Var):
        if term.name == binder:
            return Var(_BOUND)
        return term
    if isinstance(term, App):
        return App(term.op, tuple(_rename(arg, binder) for arg in term.args))
    return term


def _term_of_form(form: RealForm) -> Term:
    node: Term | None = None
    if form.constant.num != 0 or not (
        form.terms
        or form.towers
        or form.nests
        or form.pairs
        or form.deeps
        or form.highs
        or form.peaks
        or form.crests or form.summits or form.apexes or form.shells or form.folds or form.quads
    ):
        node = _term_of_ratio(form.constant)
    for coeff, rad in form.terms:
        node = _add_piece(node, _term_of_radical(coeff, rad))
    for coeff, base, numer, log_den in form.towers:
        node = _add_piece(node, _term_of_tower(coeff, base, numer, log_den))
    for coeff, constant, sqrt_coeff, rad in form.nests:
        node = _add_piece(node, _term_of_nest(coeff, constant, sqrt_coeff, rad))
    for coeff, left_c, left_r, right_c, right_r in form.pairs:
        node = _add_piece(node, _term_of_pair(coeff, left_c, left_r, right_c, right_r))
    for coeff, mult, constant, sqrt_coeff, rad in form.deeps:
        node = _add_piece(node, _term_of_deep(coeff, mult, constant, sqrt_coeff, rad))
    for coeff, mult, left_c, left_r, right_c, right_r in form.highs:
        node = _add_piece(node, _term_of_high(coeff, mult, left_c, left_r, right_c, right_r))
    for coeff, pmult, hmult, left_c, left_r, right_c, right_r in form.peaks:
        node = _add_piece(node, _term_of_peak(coeff, pmult, hmult, left_c, left_r, right_c, right_r))
    for coeff, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.crests:
        node = _add_piece(
            node,
            _term_of_crest(coeff, qmult, pmult, hmult, left_c, left_r, right_c, right_r),
        )
    for coeff, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.summits:
        node = _add_piece(
            node,
            _term_of_summit(
                coeff, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
            ),
        )
    for coeff, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.apexes:
        node = _add_piece(
            node,
            _term_of_apex(
                coeff, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
            ),
        )
    for coeff, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.shells:
        node = _add_piece(
            node,
            _term_of_shell(
                coeff, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
            ),
        )
    for coeff, extra, mult, constant, sqrt_coeff, rad in form.folds:
        node = _add_piece(node, _term_of_fold(coeff, extra, mult, constant, sqrt_coeff, rad))
    for coeff, constant, first_coeff, first, second_coeff, second, product_coeff in form.quads:
        node = _add_piece(
            node,
            _term_of_quad(coeff, constant, first_coeff, first, second_coeff, second, product_coeff),
        )
    return node if node is not None else IntLit(0)


def _add_piece(node: Term | None, piece: Term) -> Term:
    if node is None or (isinstance(node, IntLit) and node.n == 0):
        return piece
    return App("add", (node, piece))


def _term_of_ratio(value: Ratio) -> Term:
    if value.den == 1:
        return IntLit(value.num)
    return App("div", (IntLit(value.num), IntLit(value.den)))


def _term_of_radical(coeff: Ratio, rad: int) -> Term:
    return _scale_term(App("sqrt", (IntLit(rad),)), coeff)


def _term_of_nest(coeff: Ratio, constant: Ratio, sqrt_coeff: Ratio, rad: int) -> Term:
    inside = _add_piece(_term_of_ratio(constant), _term_of_radical(sqrt_coeff, rad))
    return _scale_term(App("sqrt", (inside,)), coeff)


def _term_of_deep(coeff: Ratio, mult: int, constant: int, sqrt_coeff: int, rad: int) -> Term:
    inside = _term_of_nest(Ratio(1, 1), Ratio(constant, 1), Ratio(sqrt_coeff, 1), rad)
    if mult != 1:
        inside = App("mul", (IntLit(mult), inside))
    return _scale_term(App("sqrt", (inside,)), coeff)


def _term_of_fold(
    coeff: Ratio,
    extra: tuple[int, ...],
    mult: int,
    constant: int,
    sqrt_coeff: int,
    rad: int,
) -> Term:
    inside = _term_of_deep(Ratio(1, 1), mult, constant, sqrt_coeff, rad)
    for item in reversed(extra):
        if item != 1:
            inside = App("mul", (IntLit(item), inside))
        inside = App("sqrt", (inside,))
    return _scale_term(inside, coeff)



def _term_of_quad(
    coeff: Ratio,
    constant: Ratio,
    first_coeff: Ratio,
    first: int,
    second_coeff: Ratio,
    second: int,
    product_coeff: Ratio,
) -> Term:
    inside: Term | None = None
    if constant.num != 0:
        inside = _term_of_ratio(constant)
    if first_coeff.num != 0:
        inside = _add_piece(inside, _term_of_radical(first_coeff, first))
    if second_coeff.num != 0:
        inside = _add_piece(inside, _term_of_radical(second_coeff, second))
    if product_coeff.num != 0:
        inside = _add_piece(inside, _term_of_radical(product_coeff, first * second))
    if inside is None:
        raise KernelError("biquadratic term was empty")
    return _scale_term(App("sqrt", (inside,)), coeff)


def _term_of_shell(
    coeff: Ratio,
    extra: tuple[int, ...],
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> Term:
    inside = _term_of_apex(
        Ratio(1, 1), amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    )
    for mult in reversed(extra):
        if mult != 1:
            inside = App("mul", (IntLit(mult), inside))
        inside = App("sqrt", (inside,))
    return _scale_term(inside, coeff)


def _term_of_apex(
    coeff: Ratio,
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> Term:
    inside = _term_of_summit(
        Ratio(1, 1), smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    )
    if amult != 1:
        inside = App("mul", (IntLit(amult), inside))
    return _scale_term(App("sqrt", (inside,)), coeff)


def _term_of_summit(
    coeff: Ratio,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> Term:
    inside = _term_of_crest(Ratio(1, 1), qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    if smult != 1:
        inside = App("mul", (IntLit(smult), inside))
    return _scale_term(App("sqrt", (inside,)), coeff)


def _term_of_crest(
    coeff: Ratio,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> Term:
    inside = _term_of_peak(Ratio(1, 1), pmult, hmult, left_c, left_r, right_c, right_r)
    if qmult != 1:
        inside = App("mul", (IntLit(qmult), inside))
    return _scale_term(App("sqrt", (inside,)), coeff)


def _term_of_peak(
    coeff: Ratio,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> Term:
    inside = _term_of_high(Ratio(1, 1), hmult, left_c, left_r, right_c, right_r)
    if pmult != 1:
        inside = App("mul", (IntLit(pmult), inside))
    return _scale_term(App("sqrt", (inside,)), coeff)


def _term_of_high(
    coeff: Ratio,
    mult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> Term:
    inside = _term_of_pair(Ratio(1, 1), left_c, left_r, right_c, right_r)
    if mult != 1:
        inside = App("mul", (IntLit(mult), inside))
    return _scale_term(App("sqrt", (inside,)), coeff)


def _term_of_pair(coeff: Ratio, left_c: int, left_r: int, right_c: int, right_r: int) -> Term:
    inside = _add_piece(
        _term_of_radical(Ratio(left_c, 1), left_r),
        _term_of_radical(Ratio(right_c, 1), right_r),
    )
    return _scale_term(App("sqrt", (inside,)), coeff)


def _term_of_tower(coeff: Ratio, base: int, numer: int, log_den: int) -> Term:
    shown = base if numer == 1 else base**numer
    node: Term = IntLit(shown)
    for _ in range(log_den):
        node = App("sqrt", (node,))
    return _scale_term(node, coeff)


def _scale_term(radical: Term, coeff: Ratio) -> Term:
    if coeff == Ratio(1, 1):
        return radical
    if coeff == Ratio(-1, 1):
        return App("neg", (radical,))
    return App("mul", (_term_of_ratio(coeff), radical))


def _frees(term: Term) -> set[str]:
    if isinstance(term, Var):
        return {term.name}
    if isinstance(term, App):
        found: set[str] = set()
        for arg in term.args:
            found |= _frees(arg)
        return found
    return set()


def _justified_member(theorem: CollectMemberTheorem) -> bool:
    if not _canonical(theorem.element) or theorem.relation not in {"le", "eq"} or not theorem.binder:
        return False
    try:
        _reject_set_operand(theorem.left, theorem.right)
        holds = _holds(Pred(theorem.relation, theorem.left, theorem.right), theorem.binder, theorem.element)
    except (NotExact, _OpenPredicate, _FreeVariable, KernelError):
        return False
    if theorem.rule == "Collect.member":
        return holds
    if theorem.rule == "Collect.not_member":
        return not holds
    return False


def _justified_subset(theorem: CollectSubsetTheorem) -> bool:
    if theorem.relation not in {"le", "eq"} or not theorem.binder:
        return False
    if not all(_canonical(member) for member in theorem.members) or theorem.members != canonical(theorem.members):
        return False
    try:
        _reject_set_operand(theorem.left, theorem.right)
    except NotExact:
        return False
    if theorem.rule == "Collect.subset":
        if theorem.witness is not None:
            return False
        if not theorem.members:
            return True
        try:
            return _failing_member(theorem.members, CollectForm(theorem.binder, theorem.relation, theorem.left, theorem.right)) is None
        except (NotExact, _OpenPredicate, _FreeVariable, KernelError):
            return False
    if theorem.rule == "Collect.not_subset":
        if theorem.witness is None or theorem.witness not in theorem.members:
            return False
        try:
            failed = _failing_member(theorem.members, CollectForm(theorem.binder, theorem.relation, theorem.left, theorem.right))
        except (NotExact, _OpenPredicate, _FreeVariable, KernelError):
            return False
        return failed == theorem.witness
    return False


def _remap(text: str) -> str:
    if text == "a set does not enter this quantifier":
        return "a set does not enter this comprehension"
    return text


def _note(text: str) -> Rule:
    return Rule(
        id="math.open",
        layer="base",
        stage="check",
        title=text,
        produces=f"open({text})",
        detail_lines=(text,),
    )
