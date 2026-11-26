"""Solid spherical harmonics and L², Lz eigen-identities.

The solid harmonics r^ℓ Y_ℓ^m are homogeneous harmonic polynomials in
x, y, z. With ħ = 1 they are eigenfunctions of L² = Lx² + Ly² + Lz²
with eigenvalue ℓ(ℓ+1), and of Lz with eigenvalue m, checked by
applying the angular-momentum operators already admitted. An inverse,
here a coefficient in a derivative, is kept only when it multiplies back.

The admitted degrees are ℓ = 0, 1, and 2, with every m from −ℓ to ℓ.
Certificates are identities, checked exactly, with no approximation.
"""

from __future__ import annotations

from dataclasses import dataclass

from pgi.math.cnum import (
    CNum,
    c_from_int,
    c_i,
    c_is_zero,
    c_mul,
    c_neg,
    c_zero,
    show_cnum,
)
from pgi.math.kernel import KernelError, NotExact
from pgi.math.operators import (
    CPoly,
    _align_names,
    _const_poly,
    _embed_op,
    _embed_poly,
    _make_poly,
    _poly_add,
    _poly_eq,
    _poly_is_zero,
    _poly_mul,
    _poly_partials,
    _poly_scale,
    _var_poly,
    angmom,
    op_add,
    op_mul,
)
from pgi.math.rational import Ratio, RatTheorem, rat_normalize
from pgi.math.syntax import App, IntLit, Term, Var, pretty
from pgi.model import Rule


_NAMES = ("x", "y", "z")
_I = c_i()


def _zero_poly() -> CPoly:
    return _make_poly(_NAMES, [])


def _one_poly() -> CPoly:
    return _const_poly(c_from_int(1), _NAMES)


def _coord(name: str) -> CPoly:
    return _var_poly(_NAMES.index(name), _NAMES)


def _plus_i_y() -> CPoly:
    # x + i y
    return _make_poly(_NAMES, [
        ((1, 0, 0), c_from_int(1)),
        ((0, 1, 0), _I),
    ])


def _minus_i_y() -> CPoly:
    # x - i y
    return _make_poly(_NAMES, [
        ((1, 0, 0), c_from_int(1)),
        ((0, 1, 0), c_neg(_I)),
    ])


def op_apply(op, fn: CPoly) -> CPoly:
    names = _align_names(op.names, fn.names)
    op = _embed_op(op, names)
    fn = _embed_poly(fn, names)
    raw: list = []
    for orders, coeff in op.terms:
        derived = _poly_partials(fn, orders)
        if _poly_is_zero(derived):
            continue
        raw.extend(_poly_mul(coeff, derived).terms)
    return _make_poly(names, [(exponents, coeff) for exponents, coeff in raw])


def l2_op():
    lx, ly, lz = angmom("x"), angmom("y"), angmom("z")
    return op_add(op_mul(lx, lx), op_add(op_mul(ly, ly), op_mul(lz, lz)))


def lz_op():
    return angmom("z")


def solid_harmonic(ell: int, m: int) -> CPoly:
    if ell not in {0, 1, 2} or abs(m) > ell:
        raise NotExact("a spherical harmonic is admitted here only for l = 0, 1, or 2, with |m| <= l")
    if ell == 0:
        return _one_poly()
    if ell == 1:
        if m == 0:
            return _coord("z")
        if m == 1:
            return _plus_i_y()
        return _minus_i_y()
    # ell == 2
    z = _coord("z")
    x = _coord("x")
    y = _coord("y")
    if m == 0:
        # 2z² − x² − y²
        return _make_poly(_NAMES, [
            ((0, 0, 2), c_from_int(2)),
            ((2, 0, 0), c_from_int(-1)),
            ((0, 2, 0), c_from_int(-1)),
        ])
    if m == 1:
        return _poly_mul(_plus_i_y(), z)
    if m == -1:
        return _poly_mul(_minus_i_y(), z)
    if m == 2:
        return _poly_mul(_plus_i_y(), _plus_i_y())
    return _poly_mul(_minus_i_y(), _minus_i_y())


def l2_on(ell: int, m: int) -> CPoly:
    return op_apply(l2_op(), solid_harmonic(ell, m))


def lz_on(ell: int, m: int) -> CPoly:
    return op_apply(lz_op(), solid_harmonic(ell, m))


def _scale_harmonic(ell: int, m: int, coeff: int) -> CPoly:
    return _poly_scale(solid_harmonic(ell, m), c_from_int(coeff))


def _check_standing() -> None:
    for ell in (0, 1, 2):
        for m in range(-ell, ell + 1):
            expected_l2 = _scale_harmonic(ell, m, ell * (ell + 1))
            if not _poly_eq(l2_on(ell, m), expected_l2):
                raise KernelError("L^2 of this solid harmonic was not l(l+1) times the harmonic")
            expected_lz = _scale_harmonic(ell, m, m)
            if not _poly_eq(lz_on(ell, m), expected_lz):
                raise KernelError("Lz of this solid harmonic was not m times the harmonic")


_STANDING = False


def _standing() -> None:
    global _STANDING
    if _STANDING:
        return
    _check_standing()
    _STANDING = True


def show_cpoly(value: CPoly) -> str:
    if _poly_is_zero(value):
        return "0"
    parts: list[str] = []
    # terms are already sorted by _make_poly
    for exponents, coeff in value.terms:
        monom = _show_monom(value.names, exponents)
        shown = show_cnum(coeff)
        if monom == "1":
            part = shown
        elif shown == "1":
            part = monom
        elif shown == "-1":
            part = f"-{monom}"
        else:
            if any(ch in shown[1:] for ch in "+-"):
                part = f"({shown}) * {monom}"
            else:
                part = f"{shown} * {monom}"
        parts.append(part)
    body = parts[0]
    for part in parts[1:]:
        if part.startswith("-"):
            body = f"{body} - {part[1:]}"
        else:
            body = f"{body} + {part}"
    return body


def _show_monom(names: tuple[str, ...], exponents: tuple[int, ...]) -> str:
    bits = []
    for name, exp in zip(names, exponents):
        if exp == 1:
            bits.append(name)
        elif exp > 1:
            bits.append(f"{name}^{exp}")
    return " * ".join(bits) if bits else "1"


YLM_OPS = frozenset({"ylm", "l2", "lz"})


def _contains_op(term: Term, names: frozenset[str]) -> bool:
    if isinstance(term, App):
        if term.op in names:
            return True
        return any(_contains_op(arg, names) for arg in term.args)
    return False


def has_ylm(term: Term) -> bool:
    return _contains_op(term, YLM_OPS)


def _index(term: Term, signed: bool = False) -> int:
    if isinstance(term, IntLit):
        if (not signed) and term.n < 0:
            raise NotExact("a degree is a nonnegative integer")
        return term.n
    if isinstance(term, App) and term.op == "neg" and len(term.args) == 1 and isinstance(term.args[0], IntLit):
        return -term.args[0].n
    raise NotExact("a spherical-harmonic index must be an integer")


def _pair(term: Term) -> tuple[int, int]:
    if not isinstance(term, App) or term.op != "ylm" or len(term.args) != 2:
        raise NotExact("ylm takes l and m")
    return _index(term.args[0]), _index(term.args[1], signed=True)


def _eval_ylm_expr(term: Term) -> CPoly:
    _standing()
    if isinstance(term, App):
        if term.op == "ylm":
            ell, m = _pair(term)
            return solid_harmonic(ell, m)
        if term.op == "l2":
            if len(term.args) != 1:
                raise NotExact("l2 takes a solid harmonic")
            ell, m = _pair(term.args[0])
            return l2_on(ell, m)
        if term.op == "lz":
            if len(term.args) != 1:
                raise NotExact("lz takes a solid harmonic")
            ell, m = _pair(term.args[0])
            return lz_on(ell, m)
        if term.op == "mul" and len(term.args) == 2:
            # n * ylm(...) or n * l2(...)
            if isinstance(term.args[0], IntLit) or (isinstance(term.args[0], App) and term.args[0].op == "neg"):
                scale = _index(term.args[0], signed=True)
                return _poly_scale(_eval_ylm_expr(term.args[1]), c_from_int(scale))
            if isinstance(term.args[1], IntLit):
                scale = _index(term.args[1], signed=True)
                return _poly_scale(_eval_ylm_expr(term.args[0]), c_from_int(scale))
        if term.op in {"add", "sub"} and len(term.args) == 2:
            left, right = _eval_ylm_expr(term.args[0]), _eval_ylm_expr(term.args[1])
            return _poly_add(left, right) if term.op == "add" else _poly_add(left, _poly_scale(right, c_from_int(-1)))
        if term.op == "neg" and len(term.args) == 1:
            return _poly_scale(_eval_ylm_expr(term.args[0]), c_from_int(-1))
    raise NotExact("this term is not a spherical-harmonic expression")


@dataclass(frozen=True)
class YlmTheorem:
    value: CPoly
    origin: Term
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        expected = _eval_ylm_expr(self.origin)
        if not _poly_eq(self.value, expected):
            raise KernelError("this spherical-harmonic result does not match the exact evaluation")


def eval_ylm_result(term: Term):
    _standing()
    return YlmTheorem(_eval_ylm_expr(term), term, _detail())


def _detail() -> tuple[str, ...]:
    return (
        "The solid harmonics r^l Y_l^m are homogeneous polynomials in x, y, z.",
        "L^2 = Lx^2 + Ly^2 + Lz^2 has eigenvalue l(l+1), and Lz has eigenvalue m, checked by applying the angular-momentum operators.",
    )


def ylm_value_rule(origin: Term, result: object, prelude: tuple[str, ...] = ()) -> Rule:
    if not isinstance(result, YlmTheorem):
        raise KernelError("this spherical-harmonic result has no claim")
    shown = show_cpoly(result.value)
    return Rule(
        id=f"math.ylm.{shown}",
        layer="base",
        stage="quantity",
        title=f"{pretty(origin)} = {shown}",
        produces=shown,
        detail_lines=(*prelude, *result.detail),
    )


def ylm_equality_rules(left: Term, right: Term, left_value: object, right_value: object, prelude: tuple[str, ...] = ()):
    title = f"{pretty(left)} = {pretty(right)}"
    if _ylm_eq(left_value, right_value):
        return (
            Rule(
                id="math.ylm.eq",
                layer="base",
                stage="quantity",
                title=title,
                produces=f"identity({title})",
                detail_lines=(*prelude, "The two sides are the same exact polynomial."),
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


def _as_poly(value: object) -> CPoly | None:
    if isinstance(value, YlmTheorem):
        return value.value
    if isinstance(value, CPoly):
        return value
    return None


def _is_zero_side(value: object) -> bool:
    poly = _as_poly(value)
    if poly is not None:
        return _poly_is_zero(poly)
    if isinstance(value, RatTheorem):
        return value.value.num == 0
    if isinstance(value, Ratio):
        return value.num == 0
    return False


def _ylm_eq(left: object, right: object) -> bool:
    a, b = _as_poly(left), _as_poly(right)
    if a is not None and b is not None:
        return _poly_eq(a, b)
    if a is not None and _is_zero_side(right):
        return _poly_is_zero(a)
    if b is not None and _is_zero_side(left):
        return _poly_is_zero(b)
    return False


def side_as_ylm(term: Term) -> object:
    try:
        return eval_ylm_result(term)
    except NotExact:
        if isinstance(term, IntLit) and term.n == 0:
            return rat_normalize(0, 1)
        raise
