"""Exact checks that a candidate solves a linear ordinary differential equation.

The one-dimensional harmonic oscillator, with ħ = ω = m = 1, has
eigenfunctions ψ_n(x) built from a polynomial times exp(-x² / 2), and
energies E_n = n + 1/2. The residual ψ'' − (x² − 2n − 1) ψ is kept
only when it is identically zero. The admitted states are n = 0, 1, and 2:
ψ_0 = exp(-x² / 2), ψ_1 = x exp(-x² / 2), and ψ_2 = (2x² − 1) exp(-x² / 2).

The hydrogen radial function is the reduced wave u_{n,ℓ}(r) = r R_{nℓ}(r)
in atomic units with Z = 1. It must satisfy
u'' − ℓ(ℓ+1)/r² u + 2/r u − u/n² = 0, the radial equation at
E = −1/(2n²). The admitted states are (n, ℓ) = (1, 0), (2, 0), and (2, 1),
with u_10 = r exp(-r), u_20 = r (1 − r/2) exp(-r/2), and
u_21 = r² exp(-r/2).

A named check `ode(...)` is 0 only when the residual vanishes identically.
The identities are checked exactly, with no approximation.
"""

from __future__ import annotations

from pgi.math.kernel import KernelError, NotExact
from pgi.math.rational import RatTheorem, eval_rat, rat_normalize
from pgi.math.syntax import App, IntLit, Term, parse_term, pretty
from pgi.math.trans import (
    TransTheorem,
    eval_trans,
    eval_trans_result,
    fexpr_add,
    fexpr_diff,
    fexpr_eq,
    fexpr_mul,
    fexpr_sub,
    show_fexpr,
    side_as_trans,
    trans_equality_rules,
    trans_value_rule,
)
from pgi.model import Rule


def _fexpr(text: str):
    return eval_trans(parse_term(text))


def _zero():
    return _fexpr("0")


def harmonic_wave(level: int):
    if level == 0:
        return _fexpr("exp(-x^2 / 2)")
    if level == 1:
        return _fexpr("x * exp(-x^2 / 2)")
    if level == 2:
        return _fexpr("(2 * x^2 - 1) * exp(-x^2 / 2)")
    raise NotExact("a harmonic-oscillator check is admitted here only for n = 0, 1, or 2")


def harmonic_residual(level: int):
    psi = harmonic_wave(level)
    psi_xx = fexpr_diff(fexpr_diff(psi, "x"), "x")
    weight = _fexpr(f"x^2 - {2 * level + 1}")
    return fexpr_sub(psi_xx, fexpr_mul(weight, psi))


def hydrogen_radial(level: int, ell: int):
    if level == 1 and ell == 0:
        return _fexpr("r * exp(-r)")
    if level == 2 and ell == 0:
        return _fexpr("r * (1 - r / 2) * exp(-r / 2)")
    if level == 2 and ell == 1:
        return _fexpr("r^2 * exp(-r / 2)")
    raise NotExact("a hydrogen radial check is admitted here only for (n, l) = (1, 0), (2, 0), or (2, 1)")


def hydrogen_residual(level: int, ell: int):
    radial = hydrogen_radial(level, ell)
    u_rr = fexpr_diff(fexpr_diff(radial, "r"), "r")
    centrifugal = _fexpr(f"{ell * (ell + 1)} / r^2")
    coulomb = _fexpr("2 / r")
    energy = _fexpr(f"1 / {level * level}")
    # u'' − ℓ(ℓ+1)/r² u + 2/r u − u/n²
    return fexpr_sub(
        fexpr_add(fexpr_sub(u_rr, fexpr_mul(centrifugal, radial)), fexpr_mul(coulomb, radial)),
        fexpr_mul(energy, radial),
    )


def _check_residual(value) -> None:
    if not fexpr_eq(value, _zero()):
        raise KernelError("this candidate does not satisfy the differential equation identically")


_STANDING = False


def _standing() -> None:
    global _STANDING
    if _STANDING:
        return
    for level in (0, 1, 2):
        _check_residual(harmonic_residual(level))
    for level, ell in ((1, 0), (2, 0), (2, 1)):
        _check_residual(hydrogen_residual(level, ell))
    _STANDING = True


def _index(term: Term) -> int:
    if isinstance(term, IntLit):
        if term.n < 0:
            raise NotExact("a quantum number is a nonnegative integer")
        return term.n
    raise NotExact("a quantum number must be an integer")


ODE_OPS = frozenset({"ode", "harmonic", "hydrogen"})


def _contains_op(term: Term, names: frozenset[str]) -> bool:
    if isinstance(term, App):
        if term.op in names:
            return True
        return any(_contains_op(arg, names) for arg in term.args)
    return False


def has_ode(term: Term) -> bool:
    return _contains_op(term, ODE_OPS)


def _eval_wave(term: Term):
    if isinstance(term, App) and term.op == "harmonic" and len(term.args) == 1:
        return harmonic_wave(_index(term.args[0]))
    if isinstance(term, App) and term.op == "hydrogen" and len(term.args) == 2:
        return hydrogen_radial(_index(term.args[0]), _index(term.args[1]))
    raise NotExact("ode takes harmonic(n) or hydrogen(n, l)")


def _eval(term: Term):
    _standing()
    if isinstance(term, App):
        if term.op in {"harmonic", "hydrogen"}:
            return _eval_wave(term)
        if term.op == "ode":
            if len(term.args) != 1:
                raise NotExact("ode takes a harmonic or hydrogen candidate")
            candidate = term.args[0]
            if isinstance(candidate, App) and candidate.op == "harmonic":
                if len(candidate.args) != 1:
                    raise NotExact("harmonic takes a level n")
                residual = harmonic_residual(_index(candidate.args[0]))
            elif isinstance(candidate, App) and candidate.op == "hydrogen":
                if len(candidate.args) != 2:
                    raise NotExact("hydrogen takes n and l")
                residual = hydrogen_residual(_index(candidate.args[0]), _index(candidate.args[1]))
            else:
                raise NotExact("ode takes harmonic(n) or hydrogen(n, l)")
            _check_residual(residual)
            return rat_normalize(0, 1)
    raise NotExact("this term is not an exact ODE check")


def eval_ode_result(term: Term):
    _standing()
    value = _eval(term)
    if isinstance(value, RatTheorem):
        return value
    # A named wavefunction is the corresponding elementary expression.
    shown = parse_term(show_fexpr(value))
    return TransTheorem(value, shown, _ode_detail())


def _ode_detail() -> tuple[str, ...]:
    return (
        "A candidate solution is kept only when its residual in the linear ODE vanishes identically.",
        "The harmonic oscillator uses ħ = ω = m = 1, with ψ'' − (x² − 2n − 1) ψ = 0 for n = 0, 1, 2.",
        "The hydrogen radial equation is u'' − ℓ(ℓ+1)/r² u + 2/r u − u/n² = 0 in atomic units, for (n, ℓ) = (1, 0), (2, 0), and (2, 1).",
    )


def ode_value_rule(origin: Term, result: object, prelude: tuple[str, ...] = ()) -> Rule:
    if isinstance(result, RatTheorem):
        from pgi.math.rational import ratio_rule

        rule = ratio_rule(origin, result, prelude)
        return Rule(
            id=rule.id,
            layer=rule.layer,
            stage=rule.stage,
            title=rule.title,
            produces=rule.produces,
            detail_lines=(*prelude, *_ode_detail()) if not prelude else (*prelude, *_ode_detail()),
        )
    return trans_value_rule(origin, result, (*prelude, *_ode_detail()) if prelude else _ode_detail())


def ode_equality_rules(left, right, left_value, right_value, prelude=()):
    return trans_equality_rules(left, right, left_value, right_value, prelude or _ode_detail())


def side_as_ode(term: Term) -> object:
    try:
        return eval_ode_result(term)
    except NotExact:
        try:
            return side_as_trans(term)
        except NotExact:
            return eval_rat(term)
