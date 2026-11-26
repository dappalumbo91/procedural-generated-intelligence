"""Canonical commutators, angular momentum, and oscillator ladder operators.

Position and momentum act on polynomials in the coordinates, with ħ = 1:
X_i is multiplication by the coordinate, and P_i = −i ∂_i. Their
commutator is [X_i, P_j] = i δ_ij, checked as an identity of operators
in normal form (coefficients on the left, derivatives on the right).
An inverse, here a coefficient, is kept only when the operator product
rebuilds the original.

Angular momentum is L_i = ε_ijk X_j P_k. The so(3) algebra
[L_i, L_j] = i ε_ijk L_k is checked on those polynomial operators.

The harmonic-oscillator ladder operators, with ħ = ω = m = 1, are
a = (X + i P)/√2 = (X + ∂)/√2 and a† = (X − i P)/√2 = (X − ∂)/√2.
Their commutator is [a, a†] = 1, checked identically.

Certificates are operator identities, checked exactly, with no approximation.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import comb

from pgi.math.cnum import (
    CNum,
    c_add,
    c_eq,
    c_from_int,
    c_from_ratio,
    c_i,
    c_is_zero,
    c_mul,
    c_neg,
    c_one,
    c_sqrt_ratio,
    c_sub,
    c_zero,
    show_cnum,
)
from pgi.math.kernel import KernelError, NotExact
from pgi.math.rational import Ratio, RatTheorem, rat_normalize
from pgi.math.syntax import App, IntLit, Term, Var, pretty
from pgi.model import Rule


_ZERO = Ratio(0, 1)
_ONE = Ratio(1, 1)
_I = c_i()


def _names_ok(names: tuple[str, ...]) -> bool:
    return bool(names) and len(set(names)) == len(names)


def _align_names(*groups: tuple[str, ...]) -> tuple[str, ...]:
    seen: list[str] = []
    for group in groups:
        for name in group:
            if name not in seen:
                seen.append(name)
    return tuple(seen)


def _shift(exponents: tuple[int, ...], names: tuple[str, ...], target: tuple[str, ...]) -> tuple[int, ...]:
    index = {name: exp for name, exp in zip(names, exponents)}
    return tuple(index.get(name, 0) for name in target)


@dataclass(frozen=True)
class CPoly:
    """A polynomial with exact complex coefficients."""

    names: tuple[str, ...]
    terms: tuple[tuple[tuple[int, ...], CNum], ...]

    def __post_init__(self) -> None:
        if not _names_ok(self.names):
            raise KernelError("this operator polynomial is not in normal form")
        seen: set[tuple[int, ...]] = set()
        for exponents, coeff in self.terms:
            if len(exponents) != len(self.names) or any(exp < 0 for exp in exponents):
                raise KernelError("this operator polynomial is not in normal form")
            if exponents in seen or c_is_zero(coeff):
                raise KernelError("this operator polynomial is not in normal form")
            seen.add(exponents)


def _make_poly(names: tuple[str, ...], raw: list[tuple[tuple[int, ...], CNum]]) -> CPoly:
    merged: dict[tuple[int, ...], CNum] = {}
    for exponents, coeff in raw:
        if c_is_zero(coeff):
            continue
        merged[exponents] = c_add(merged[exponents], coeff) if exponents in merged else coeff
    terms = tuple((exponents, coeff) for exponents, coeff in sorted(merged.items()) if not c_is_zero(coeff))
    return CPoly(names, terms)


def _embed_poly(value: CPoly, names: tuple[str, ...]) -> CPoly:
    if value.names == names:
        return value
    return _make_poly(names, [(_shift(exponents, value.names, names), coeff) for exponents, coeff in value.terms])


def _const_poly(coeff: CNum, names: tuple[str, ...]) -> CPoly:
    if c_is_zero(coeff):
        return _make_poly(names, [])
    return _make_poly(names, [((0,) * len(names), coeff)])


def _var_poly(index: int, names: tuple[str, ...]) -> CPoly:
    exponents = tuple(1 if i == index else 0 for i in range(len(names)))
    return _make_poly(names, [(exponents, c_one())])


def _poly_add(left: CPoly, right: CPoly) -> CPoly:
    names = _align_names(left.names, right.names)
    a, b = _embed_poly(left, names), _embed_poly(right, names)
    return _make_poly(names, list(a.terms) + list(b.terms))


def _poly_neg(value: CPoly) -> CPoly:
    return _make_poly(value.names, [(exponents, c_neg(coeff)) for exponents, coeff in value.terms])


def _poly_sub(left: CPoly, right: CPoly) -> CPoly:
    return _poly_add(left, _poly_neg(right))


def _poly_scale(value: CPoly, coeff: CNum) -> CPoly:
    if c_is_zero(coeff):
        return _make_poly(value.names, [])
    return _make_poly(value.names, [(exponents, c_mul(coeff, term)) for exponents, term in value.terms])


def _poly_mul(left: CPoly, right: CPoly) -> CPoly:
    names = _align_names(left.names, right.names)
    a, b = _embed_poly(left, names), _embed_poly(right, names)
    raw = []
    for left_exp, left_c in a.terms:
        for right_exp, right_c in b.terms:
            raw.append((tuple(x + y for x, y in zip(left_exp, right_exp)), c_mul(left_c, right_c)))
    return _make_poly(names, raw)


def _poly_eq(left: CPoly, right: CPoly) -> bool:
    names = _align_names(left.names, right.names)
    a, b = _embed_poly(left, names), _embed_poly(right, names)
    if len(a.terms) != len(b.terms):
        return False
    right_map = {exponents: coeff for exponents, coeff in b.terms}
    return all(exponents in right_map and c_eq(coeff, right_map[exponents]) for exponents, coeff in a.terms)


def _poly_diff(value: CPoly, index: int) -> CPoly:
    raw = []
    for exponents, coeff in value.terms:
        power = exponents[index]
        if power == 0:
            continue
        new_exp = list(exponents)
        new_exp[index] = power - 1
        raw.append((tuple(new_exp), c_mul(c_from_int(power), coeff)))
    return _make_poly(value.names, raw)


def _poly_is_zero(value: CPoly) -> bool:
    return not value.terms


def _poly_as_constant(value: CPoly) -> CNum | None:
    if not value.terms:
        return c_zero()
    if len(value.terms) == 1 and all(exp == 0 for exp in value.terms[0][0]):
        return value.terms[0][1]
    return None


@dataclass(frozen=True)
class DiffOp:
    """A linear differential operator in normal form: coefficients on the left."""

    names: tuple[str, ...]
    terms: tuple[tuple[tuple[int, ...], CPoly], ...]

    def __post_init__(self) -> None:
        if not _names_ok(self.names):
            raise KernelError("this differential operator is not in normal form")
        seen: set[tuple[int, ...]] = set()
        for orders, coeff in self.terms:
            if len(orders) != len(self.names) or any(order < 0 for order in orders):
                raise KernelError("this differential operator is not in normal form")
            if orders in seen or _poly_is_zero(coeff) or coeff.names != self.names:
                raise KernelError("this differential operator is not in normal form")
            seen.add(orders)


def _make_op(names: tuple[str, ...], raw: list[tuple[tuple[int, ...], CPoly]]) -> DiffOp:
    merged: dict[tuple[int, ...], CPoly] = {}
    for orders, coeff in raw:
        coeff = _embed_poly(coeff, names)
        if _poly_is_zero(coeff):
            continue
        merged[orders] = _poly_add(merged[orders], coeff) if orders in merged else coeff
    terms = tuple((orders, coeff) for orders, coeff in sorted(merged.items()) if not _poly_is_zero(coeff))
    return DiffOp(names, terms)


def _embed_op(value: DiffOp, names: tuple[str, ...]) -> DiffOp:
    if value.names == names:
        return value
    raw = [(_shift(orders, value.names, names), _embed_poly(coeff, names)) for orders, coeff in value.terms]
    return _make_op(names, raw)


def op_zero(names: tuple[str, ...]) -> DiffOp:
    return _make_op(names, [])


def op_identity(names: tuple[str, ...]) -> DiffOp:
    return _make_op(names, [((0,) * len(names), _const_poly(c_one(), names))])


def op_add(left: DiffOp, right: DiffOp) -> DiffOp:
    names = _align_names(left.names, right.names)
    a, b = _embed_op(left, names), _embed_op(right, names)
    return _make_op(names, list(a.terms) + list(b.terms))


def op_neg(value: DiffOp) -> DiffOp:
    return _make_op(value.names, [(orders, _poly_neg(coeff)) for orders, coeff in value.terms])


def op_sub(left: DiffOp, right: DiffOp) -> DiffOp:
    return op_add(left, op_neg(right))


def op_scale(value: DiffOp, coeff: CNum) -> DiffOp:
    return _make_op(value.names, [(orders, _poly_scale(term, coeff)) for orders, term in value.terms])


def _multi_binom(left: tuple[int, ...], k: tuple[int, ...]) -> int:
    total = 1
    for a, b in zip(left, k):
        if b > a:
            return 0
        total *= comb(a, b)
    return total


def _multi_range(orders: tuple[int, ...]):
    # all multi-indices k with 0 <= k_i <= orders_i
    size = 1
    for order in orders:
        size *= order + 1
    for flat in range(size):
        k = []
        n = flat
        for order in orders:
            k.append(n % (order + 1))
            n //= order + 1
        yield tuple(k)


def _poly_partials(value: CPoly, k: tuple[int, ...]) -> CPoly:
    result = value
    for index, times in enumerate(k):
        for _ in range(times):
            result = _poly_diff(result, index)
    return result


def op_mul(left: DiffOp, right: DiffOp) -> DiffOp:
    names = _align_names(left.names, right.names)
    a, b = _embed_op(left, names), _embed_op(right, names)
    raw: list[tuple[tuple[int, ...], CPoly]] = []
    # (f D^α) (g D^β) = f * sum_k C(α,k) (D^k g) D^{α-k+β}
    for left_orders, left_coeff in a.terms:
        for right_orders, right_coeff in b.terms:
            for k in _multi_range(left_orders):
                binom = _multi_binom(left_orders, k)
                if binom == 0:
                    continue
                derived = _poly_partials(right_coeff, k)
                if _poly_is_zero(derived):
                    continue
                new_orders = tuple(lo - ki + ro for lo, ki, ro in zip(left_orders, k, right_orders))
                raw.append((new_orders, _poly_scale(_poly_mul(left_coeff, derived), c_from_int(binom))))
    return _make_op(names, raw)


def op_eq(left: DiffOp, right: DiffOp) -> bool:
    names = _align_names(left.names, right.names)
    a, b = _embed_op(left, names), _embed_op(right, names)
    if len(a.terms) != len(b.terms):
        return False
    right_map = {orders: coeff for orders, coeff in b.terms}
    return all(orders in right_map and _poly_eq(coeff, right_map[orders]) for orders, coeff in a.terms)


def commutator(left: DiffOp, right: DiffOp) -> DiffOp:
    return op_sub(op_mul(left, right), op_mul(right, left))


def position(name: str, names: tuple[str, ...] | None = None) -> DiffOp:
    names = names or (name,)
    if name not in names:
        raise NotExact("this coordinate is not in the operator chart")
    index = names.index(name)
    return _make_op(names, [((0,) * len(names), _var_poly(index, names))])


def momentum(name: str, names: tuple[str, ...] | None = None) -> DiffOp:
    names = names or (name,)
    if name not in names:
        raise NotExact("this coordinate is not in the operator chart")
    index = names.index(name)
    orders = tuple(1 if i == index else 0 for i in range(len(names)))
    # P = -i ∂
    return _make_op(names, [(orders, _const_poly(c_neg(_I), names))])


def derivative(name: str, names: tuple[str, ...]) -> DiffOp:
    index = names.index(name)
    orders = tuple(1 if i == index else 0 for i in range(len(names)))
    return _make_op(names, [(orders, _const_poly(c_one(), names))])


def angmom(axis: str) -> DiffOp:
    names = ("x", "y", "z")
    # L_i = ε_ijk X_j P_k
    if axis == "x":
        return op_sub(op_mul(position("y", names), momentum("z", names)), op_mul(position("z", names), momentum("y", names)))
    if axis == "y":
        return op_sub(op_mul(position("z", names), momentum("x", names)), op_mul(position("x", names), momentum("z", names)))
    if axis == "z":
        return op_sub(op_mul(position("x", names), momentum("y", names)), op_mul(position("y", names), momentum("x", names)))
    raise NotExact("angular momentum is Lx, Ly, or Lz")


def ladder(kind: str) -> DiffOp:
    names = ("x",)
    # a = (X + iP)/√2 = (X + ∂)/√2, a† = (X - iP)/√2 = (X - ∂)/√2
    scale = c_inv_sqrt2()
    x = position("x", names)
    ddx = derivative("x", names)
    if kind in {"a", "lower"}:
        return op_scale(op_add(x, ddx), scale)
    if kind in {"adagger", "raise", "dagger"}:
        return op_scale(op_sub(x, ddx), scale)
    raise NotExact("a ladder operator is lower or raise")


def c_inv_sqrt2() -> CNum:
    # 1/√2, checked by (1/√2)^2 = 1/2
    value = c_sqrt_ratio(Ratio(1, 2))
    half = c_from_ratio(Ratio(1, 2))
    if not c_eq(c_mul(value, value), half):
        raise KernelError("1/√2 did not square to 1/2")
    return value


def _epsilon(i: str, j: str, k: str) -> int:
    order = ("x", "y", "z")
    if {i, j, k} != set(order) or i == j or j == k or i == k:
        return 0
    perm = (i, j, k)
    sign = 1
    items = list(perm)
    for a in range(3):
        for b in range(2, a, -1):
            if items[b] == items[b - 1]:
                return 0
            if order.index(items[b]) < order.index(items[b - 1]):
                items[b], items[b - 1] = items[b - 1], items[b]
                sign = -sign
    return sign


def _standing() -> None:
    global _STANDING
    if _STANDING:
        return
    names = ("x", "y", "z")
    # [X_i, P_j] = i δ_ij
    for i, left_name in enumerate(names):
        for j, right_name in enumerate(names):
            value = commutator(position(left_name, names), momentum(right_name, names))
            expected = op_scale(op_identity(names), _I) if i == j else op_zero(names)
            if not op_eq(value, expected):
                raise KernelError("the canonical commutator [X, P] failed")
    # [L_i, L_j] = i ε_ijk L_k
    axes = ("x", "y", "z")
    for i in axes:
        for j in axes:
            value = commutator(angmom(i), angmom(j))
            expected = op_zero(names)
            for k in axes:
                sign = _epsilon(i, j, k)
                if sign:
                    expected = op_add(expected, op_scale(angmom(k), c_mul(c_from_int(sign), _I)))
            if not op_eq(value, expected):
                raise KernelError("the angular-momentum algebra [L_i, L_j] = i ε L_k failed")
    # [a, a†] = 1
    if not op_eq(commutator(ladder("lower"), ladder("raise")), op_identity(("x",))):
        raise KernelError("the oscillator ladder commutator [a, a†] did not equal 1")
    # a and a† also match (X ± iP)/√2
    scale = c_inv_sqrt2()
    xp = position("x")
    pp = momentum("x")
    if not op_eq(ladder("lower"), op_scale(op_add(xp, op_scale(pp, _I)), scale)):
        raise KernelError("a did not equal (X + iP)/√2")
    if not op_eq(ladder("raise"), op_scale(op_sub(xp, op_scale(pp, _I)), scale)):
        raise KernelError("a† did not equal (X − iP)/√2")
    _STANDING = True


_STANDING = False


OPERATOR_OPS = frozenset({"position", "momentum", "angmom", "ladder"})


def _contains_op(term: Term, names: frozenset[str]) -> bool:
    if isinstance(term, App):
        if term.op in names:
            return True
        return any(_contains_op(arg, names) for arg in term.args)
    return False


def has_operators(term: Term) -> bool:
    return _contains_op(term, OPERATOR_OPS)


def _name(term: Term) -> str:
    if isinstance(term, Var):
        return term.name
    raise NotExact("a coordinate or axis is a name")


def _axis(term: Term) -> str:
    name = _name(term)
    mapping = {"x": "x", "y": "y", "z": "z", "1": "x", "2": "y", "3": "z"}
    if name not in mapping:
        raise NotExact("an axis is x, y, or z")
    return mapping[name]


def _eval_op(term: Term) -> DiffOp:
    _standing()
    if isinstance(term, Var) and term.name == "i":
        return op_scale(op_identity(("x", "y", "z")), _I)
    if isinstance(term, IntLit):
        return op_scale(op_identity(("x", "y", "z")), c_from_int(term.n))
    if isinstance(term, App):
        if term.op == "position":
            if len(term.args) != 1:
                raise NotExact("position takes a coordinate")
            name = _name(term.args[0])
            names = ("x", "y", "z") if name in {"x", "y", "z"} else (name,)
            return position(name, names)
        if term.op == "momentum":
            if len(term.args) != 1:
                raise NotExact("momentum takes a coordinate")
            name = _name(term.args[0])
            names = ("x", "y", "z") if name in {"x", "y", "z"} else (name,)
            return momentum(name, names)
        if term.op == "angmom":
            if len(term.args) != 1:
                raise NotExact("angmom takes an axis")
            return angmom(_axis(term.args[0]))
        if term.op == "ladder":
            if len(term.args) != 1:
                raise NotExact("ladder takes lower or raise")
            return ladder(_name(term.args[0]))
        if term.op in {"commutator", "comm"} and len(term.args) == 2:
            return commutator(_eval_op(term.args[0]), _eval_op(term.args[1]))
        if term.op == "add" and len(term.args) == 2:
            return op_add(_eval_any_op(term.args[0]), _eval_any_op(term.args[1]))
        if term.op == "sub" and len(term.args) == 2:
            return op_sub(_eval_any_op(term.args[0]), _eval_any_op(term.args[1]))
        if term.op == "neg" and len(term.args) == 1:
            return op_neg(_eval_op(term.args[0]))
        if term.op == "mul" and len(term.args) == 2:
            try:
                return op_scale(_eval_op(term.args[1]), _eval_scalar(term.args[0]))
            except NotExact:
                try:
                    return op_scale(_eval_op(term.args[0]), _eval_scalar(term.args[1]))
                except NotExact:
                    return op_mul(_eval_op(term.args[0]), _eval_op(term.args[1]))
    raise NotExact("this term is not a differential operator")


def _eval_any_op(term: Term) -> DiffOp:
    try:
        return _eval_op(term)
    except NotExact:
        return op_scale(op_identity(("x", "y", "z")), _eval_scalar(term))


def _eval_scalar(term: Term) -> CNum:
    if isinstance(term, IntLit):
        return c_from_int(term.n)
    if isinstance(term, Var) and term.name == "i":
        return _I
    if isinstance(term, App):
        if term.op == "neg" and len(term.args) == 1:
            return c_neg(_eval_scalar(term.args[0]))
        if term.op == "mul" and len(term.args) == 2:
            return c_mul(_eval_scalar(term.args[0]), _eval_scalar(term.args[1]))
    raise NotExact("this scalar is not an exact complex coefficient")


def show_op(value: DiffOp) -> str:
    constant = _as_scalar_op(value)
    if constant is not None:
        return show_cnum(constant)
    # Keep named forms when they match.
    for axis in ("x", "y", "z"):
        if op_eq(value, angmom(axis)):
            return f"angmom({axis})"
        scaled = op_scale(angmom(axis), _I)
        if op_eq(value, scaled):
            return f"i * angmom({axis})"
        if op_eq(value, op_neg(scaled)):
            return f"-i * angmom({axis})"
    if op_eq(value, ladder("lower")):
        return "ladder(lower)"
    if op_eq(value, ladder("raise")):
        return "ladder(raise)"
    if op_eq(value, op_identity(value.names)):
        return "1"
    return "operator(" + _show_raw(value) + ")"


def _as_scalar_op(value: DiffOp) -> CNum | None:
    if len(value.terms) == 0:
        return c_zero()
    if len(value.terms) == 1 and all(order == 0 for order in value.terms[0][0]):
        return _poly_as_constant(value.terms[0][1])
    return None


def _show_raw(value: DiffOp) -> str:
    parts = []
    for orders, coeff in value.terms:
        shown = _show_poly(coeff)
        derivs = [f"d({name})" for name, order in zip(value.names, orders) for _ in range(order)]
        if derivs:
            body = "*".join(derivs)
            parts.append(shown + " * " + body if shown != "1" else body)
        else:
            parts.append(shown)
    return " + ".join(parts).replace(" + -", " - ") if parts else "0"


def _show_poly(value: CPoly) -> str:
    const = _poly_as_constant(value)
    if const is not None:
        return show_cnum(const)
    parts = []
    for exponents, coeff in value.terms:
        mons = []
        for name, exp in zip(value.names, exponents):
            if exp == 1:
                mons.append(name)
            elif exp > 1:
                mons.append(f"{name}^{exp}")
        mon = "*".join(mons) if mons else "1"
        shown = show_cnum(coeff)
        if shown == "1":
            parts.append(mon)
        elif shown == "-1":
            parts.append("-" + mon)
        else:
            parts.append(f"{shown} * {mon}" if mon != "1" else shown)
    return " + ".join(parts).replace(" + -", " - ")


@dataclass(frozen=True)
class OperatorTheorem:
    value: DiffOp
    origin: Term
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not op_eq(self.value, _eval_op(self.origin)):
            raise KernelError("this operator does not match the exact evaluation")


def eval_operators_result(term: Term):
    _standing()
    return OperatorTheorem(_eval_op(term), term, _detail())


def _detail() -> tuple[str, ...]:
    return (
        "Position and momentum are polynomial operators, with ħ = 1 and P = −i ∂.",
        "A commutator is kept only as an identity of operators in normal form.",
        "Angular momentum satisfies [L_i, L_j] = i ε_ijk L_k. The oscillator ladders satisfy [a, a†] = 1.",
    )


def operators_value_rule(origin: Term, result: object, prelude: tuple[str, ...] = ()) -> Rule:
    if not isinstance(result, OperatorTheorem):
        raise KernelError("this operator result has no claim")
    shown = show_op(result.value)
    return Rule(
        id=f"math.operators.{shown}",
        layer="base",
        stage="quantity",
        title=f"{pretty(origin)} = {shown}",
        produces=shown,
        detail_lines=(*prelude, *result.detail),
    )


def operators_equality_rules(
    left: Term,
    right: Term,
    left_value: object,
    right_value: object,
    prelude: tuple[str, ...] = (),
) -> tuple[Rule, ...]:
    title = f"{pretty(left)} = {pretty(right)}"
    if _operators_eq(left_value, right_value):
        return (
            Rule(
                id="math.operators.eq",
                layer="base",
                stage="quantity",
                title=title,
                produces=f"identity({title})",
                detail_lines=(*prelude, "The two sides are the same exact differential operator."),
            ),
        )
    return (
        Rule(
            id="math.open",
            layer="base",
            stage="check",
            title=f"{title} is not a theorem",
            produces=f"open({title} is not a theorem)",
            detail_lines=(f"{title} is not a theorem",),
        ),
    )


def _as_op(value: object) -> DiffOp | None:
    if isinstance(value, OperatorTheorem):
        return value.value
    if isinstance(value, DiffOp):
        return value
    return None


def _operators_eq(left: object, right: object) -> bool:
    a, b = _as_op(left), _as_op(right)
    if a is not None and b is not None:
        return op_eq(a, b)
    return False


def side_as_operators(term: Term) -> object:
    try:
        return eval_operators_result(term)
    except NotExact:
        if isinstance(term, Var) and term.name == "i":
            return OperatorTheorem(op_scale(op_identity(("x",)), _I), term, _detail())
        if isinstance(term, IntLit):
            names = ("x",)
            return OperatorTheorem(op_scale(op_identity(names), c_from_int(term.n)), term, _detail())
        raise
