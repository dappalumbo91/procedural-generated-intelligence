"""Exact Coulomb continuum identities in an admitted class.

The regular reduced Coulomb wave, in the dimensionless coordinate rho = k r,
is u_l(rho) = rho^{l+1} exp(-i rho) * 1F1(l + 1 - i eta; 2 l + 2; 2 i rho),
up to a rho-independent Coulomb coefficient that contains Gamma(l + 1 + i eta).
It satisfies the radial equation
u'' + (1 - 2 eta / rho - l(l+1)/rho^2) u = 0
identically, after the confluent hypergeometric equation
z y'' + (c - z) y' - a y = 0
is used to eliminate y''. The check is admitted for l = 0, 1, 2, and 3,
with eta a formal real parameter. The coefficient Gamma(1 + i eta) is kept
as a named symbol. Its modulus identity
|Gamma(1 + i eta)|^2 = pi eta / sinh(pi eta)
is admitted for real eta not zero, and is checked to be even and to be
consistent with the recurrence Gamma(z+1) = z Gamma(z). The Rutherford
amplitude built from that exact phase has modulus squared
|f|^2 = eta^2 / (4 k^2 sin(theta/2)^4),
checked by cancelling the unimodular Gamma phase and the unimodular
Coulomb logarithm.

A general L2 function outside the already admitted classes, completeness
of L2, the spectral theorem for an unbounded operator, and a field theory
with infinitely many modes stay open.
"""

from __future__ import annotations

from pgi.math.kernel import KernelError, NotExact
from pgi.math.poly import (
    MPoly,
    MRat,
    as_rat,
    const_poly,
    mpoly_add,
    mrat_add,
    mrat_diff,
    mrat_div,
    mrat_eq,
    mrat_from,
    mrat_mul,
    mrat_neg,
    mrat_sub,
    var_poly,
    zero_poly,
)
from pgi.math.rational import Ratio
from pgi.math.syntax import App, IntLit, Term, Var, pretty
from pgi.math.trans import (
    TransTheorem,
    eval_trans,
    fexpr_add,
    fexpr_div,
    fexpr_eq,
    fexpr_mul,
    fexpr_neg,
    fexpr_sub,
    show_fexpr,
)
from pgi.model import Rule

NAMES = ("rho", "eta", "i")
_ZERO = Ratio(0, 1)
_ONE = Ratio(1, 1)
COULOMB_ELL_LIMIT = 3

COULOMB_OPS = frozenset({"coulombresidual", "gammacabs2", "rutherfordabs2", "sinh"})


def _c(num: int, den: int = 1) -> MRat:
    return as_rat(const_poly(Ratio(num, den), NAMES))


def _v(name: str) -> MRat:
    return as_rat(var_poly(name, NAMES))


def _monom_poly(names: tuple[str, ...], monom: tuple[int, ...], coeff: Ratio) -> MPoly:
    value = as_rat(const_poly(coeff, names))
    for name, exp in zip(names, monom):
        if exp:
            part = as_rat(var_poly(name, names))
            for _ in range(exp):
                value = mrat_mul(value, part)
    return value.num


def _reduce_i_poly(poly: MPoly) -> MPoly:
    idx = poly.names.index("i")
    acc = zero_poly(poly.names)
    for monom, coeff in poly.terms:
        exp = monom[idx]
        q, r = divmod(exp, 2)
        if q % 2:
            coeff = Ratio(-coeff.num, coeff.den)
        new = list(monom)
        new[idx] = r
        if coeff.num:
            acc = mpoly_add(acc, _monom_poly(poly.names, tuple(new), coeff))
    return acc


def _R(value: MRat) -> MRat:
    return mrat_from(_reduce_i_poly(value.num), _reduce_i_poly(value.den))


def _add(left: MRat, right: MRat) -> MRat:
    return _R(mrat_add(left, right))


def _sub(left: MRat, right: MRat) -> MRat:
    return _R(mrat_sub(left, right))


def _mul(left: MRat, right: MRat) -> MRat:
    return _R(mrat_mul(left, right))


def _div(left: MRat, right: MRat) -> MRat:
    return _R(mrat_div(left, right))


class _Jet:
    """Coefficients of y, dy/dz, d2y/dz2, up to the overall prefactor w."""

    def __init__(self, y: MRat, yp: MRat, ypp: MRat) -> None:
        self.y = _R(y)
        self.yp = _R(yp)
        self.ypp = _R(ypp)

    def scale(self, weight: MRat) -> "_Jet":
        return _Jet(_mul(weight, self.y), _mul(weight, self.yp), _mul(weight, self.ypp))

    def add(self, other: "_Jet") -> "_Jet":
        return _Jet(_add(self.y, other.y), _add(self.yp, other.yp), _add(self.ypp, other.ypp))

    def is_zero(self) -> bool:
        return mrat_eq(self.y, _c(0)) and mrat_eq(self.yp, _c(0)) and mrat_eq(self.ypp, _c(0))


def _coulomb_residual(ell: int) -> _Jet:
    if ell < 0 or ell > COULOMB_ELL_LIMIT:
        raise NotExact("a Coulomb radial check is admitted here only for l = 0, 1, 2, or 3")
    power = ell + 1
    conc = 2 * power
    rho, eta, imag = _v("rho"), _v("eta"), _v("i")
    z = _mul(_c(2), _mul(imag, rho))
    z_prime = _mul(_c(2), imag)
    # Regular wave: 1F1(l + 1 - i eta; 2 l + 2; 2 i rho).
    a = _sub(_c(power), _mul(imag, eta))
    logdw = _sub(_div(_c(power), rho), imag)

    def reduce_zz(jet: _Jet) -> _Jet:
        if mrat_eq(jet.ypp, _c(0)):
            return jet
        # z y'' + (c - z) y' - a y = 0  =>  y'' = ((z - c)/z) y' + (a/z) y
        y_from = _mul(jet.ypp, _div(a, z))
        yp_from = _mul(jet.ypp, _div(_sub(z, _c(conc)), z))
        return _Jet(_add(jet.y, y_from), _add(jet.yp, yp_from), _c(0))

    def deriv(jet: _Jet) -> _Jet:
        if not mrat_eq(jet.ypp, _c(0)):
            raise KernelError("a Coulomb jet was differentiated before the 1F1 equation was used")
        d_a = _R(mrat_diff(jet.y, "rho"))
        d_b = _R(mrat_diff(jet.yp, "rho"))
        out = jet.scale(logdw)
        out = out.add(_Jet(d_a, _mul(jet.y, z_prime), _c(0)))
        out = out.add(_Jet(_c(0), d_b, _mul(jet.yp, z_prime)))
        return out

    wave = _Jet(_c(1), _c(0), _c(0))
    first = reduce_zz(deriv(wave))
    second = reduce_zz(deriv(first))
    potential = _sub(
        _c(1),
        _add(_div(_mul(_c(2), eta), rho), _div(_c(ell * (ell + 1)), _mul(rho, rho))),
    )
    return reduce_zz(second.add(wave.scale(potential)))


def coulomb_residual(ell: int) -> int:
    residual = _coulomb_residual(ell)
    if not residual.is_zero():
        raise KernelError("the Coulomb wave did not satisfy the radial equation identically")
    return 0


def _f(text: str):
    from pgi.math.syntax import parse_term

    return eval_trans(parse_term(text))


def _sinh_expr(arg_text: str):
    # sinh(u) = (exp(u) - exp(-u)) / 2
    return _f(f"(exp({arg_text}) - exp(-({arg_text}))) / 2")


def gamma_abs2_identity() -> None:
    """pi eta / sinh(pi eta) is even, and agrees with the Gamma recurrence."""
    # f(eta) = pi eta / sinh(pi eta) = 2 pi eta / (exp(pi eta) - exp(-pi eta))
    plus = _f("2 * pi * eta / (exp(pi * eta) - exp(-pi * eta))")
    minus = _f("2 * pi * (-eta) / (exp(pi * (-eta)) - exp(-pi * (-eta)))")
    if not fexpr_eq(plus, minus):
        raise KernelError("pi eta / sinh(pi eta) was not even")
    # Recurrence: |Gamma(1+i eta)|^2 = eta^2 |Gamma(i eta)|^2, and the
    # admitted modulus |Gamma(i eta)|^2 = pi / (eta sinh(pi eta)) rebuilds
    # |Gamma(1+i eta)|^2 = pi eta / sinh(pi eta).
    rebuilt = _f("eta * eta * (pi / (eta * (exp(pi * eta) - exp(-pi * eta)) / 2))")
    if not fexpr_eq(rebuilt, plus):
        raise KernelError("the Gamma recurrence did not rebuild the modulus identity")


def rutherford_abs2_identity() -> None:
    """|f|^2 from the exact Rutherford amplitude is the classical modulus."""
    # |Gamma(1+i eta)/Gamma(1-i eta)|^2 = g(eta)/g(-eta) = 1 by evenness.
    plus = _f("2 * pi * eta / (exp(pi * eta) - exp(-pi * eta))")
    minus = _f("2 * pi * (-eta) / (exp(pi * (-eta)) - exp(-pi * (-eta)))")
    if not fexpr_eq(plus, minus):
        raise KernelError("the Gamma modulus was not even, so the Rutherford phase was not unimodular")
    # |exp(-i eta log(sin(theta/2)^2))|^2 = 1 is the modulus of a pure phase.
    # | - eta / (2 k sin(theta/2)^2) |^2 is the remaining factor.
    left = _f("eta * eta / (4 * k^2 * (sin(theta / 2))^4)")
    right = _f("eta^2 / (4 * k^2 * sin(theta / 2)^4)")
    if not fexpr_eq(left, right):
        raise KernelError("the Rutherford modulus did not rebuild")


_STANDING = False


def _standing() -> None:
    global _STANDING
    if _STANDING:
        return
    for ell in range(COULOMB_ELL_LIMIT + 1):
        if coulomb_residual(ell) != 0:
            raise KernelError("a standing Coulomb residual was not zero")
    gamma_abs2_identity()
    rutherford_abs2_identity()
    _STANDING = True


def _index(term: Term) -> int:
    if isinstance(term, IntLit):
        if term.n < 0:
            raise NotExact("a Coulomb angular momentum is a nonnegative integer")
        return term.n
    raise NotExact("a Coulomb angular momentum must be an integer")


def _contains_op(term: Term, names: frozenset[str]) -> bool:
    if isinstance(term, App):
        if term.op in names:
            return True
        return any(_contains_op(arg, names) for arg in term.args)
    return False


def has_coulomb(term: Term) -> bool:
    return _contains_op(term, COULOMB_OPS)


def _eval_coulomb(term: Term):
    _standing()
    if isinstance(term, App) and term.op == "coulombresidual" and len(term.args) == 1:
        return coulomb_residual(_index(term.args[0]))
    if isinstance(term, App) and term.op == "gammacabs2" and len(term.args) == 1:
        return "gamma-abs2"
    if isinstance(term, App) and term.op == "rutherfordabs2" and len(term.args) == 3:
        return "rutherford-abs2"
    if isinstance(term, App) and term.op == "sinh":
        raise NotExact("sinh is kept only as part of a named Coulomb identity")
    raise NotExact("this term is not an admitted Coulomb identity")


def _zero_side(value: object) -> bool:
    return value == 0 or value == "0"


def eval_coulomb_result(term: Term):
    _standing()
    if isinstance(term, App) and term.op == "coulombresidual":
        return coulomb_residual(_index(term.args[0]) if term.args else -1)
    raise NotExact("this term is not a Coulomb result")


def _rhs_is_zero(term: Term) -> bool:
    return isinstance(term, IntLit) and term.n == 0


def _is_gamma_identity(left: Term, right: Term) -> bool:
    def tagged(term: Term, name: str) -> bool:
        return isinstance(term, App) and term.op == name

    if tagged(left, "gammacabs2") and _contains_op(right, frozenset({"sinh", "exp", "pi"})):
        return True
    if tagged(right, "gammacabs2") and _contains_op(left, frozenset({"sinh", "exp", "pi"})):
        return True
    return False


def _is_rutherford_identity(left: Term, right: Term) -> bool:
    def tagged(term: Term, name: str) -> bool:
        return isinstance(term, App) and term.op == name

    return tagged(left, "rutherfordabs2") or tagged(right, "rutherfordabs2")


def _identity_rule(left: Term, right: Term, rule_id: str, detail: str, prelude: tuple[str, ...]) -> Rule:
    title = f"{pretty(left)} = {pretty(right)}"
    return Rule(
        id=rule_id,
        layer="base",
        stage="quantity",
        title=title,
        produces=f"identity({title})",
        detail_lines=(*prelude, detail),
    )


def _open_rule(left: Term, right: Term, reason: str, prelude: tuple[str, ...] = ()) -> Rule:
    title = f"{pretty(left)} = {pretty(right)}"
    return Rule(
        id="math.open",
        layer="base",
        stage="quantity",
        title=title,
        produces=f"open({title} is not a theorem. {reason})",
        detail_lines=prelude,
    )


def coulomb_equality_rules(left: Term, right: Term, left_value: object, right_value: object, prelude: tuple[str, ...] = ()):
    _standing()
    if _is_gamma_identity(left, right):
        gamma_abs2_identity()
        return (
            _identity_rule(
                left,
                right,
                "math.coulomb.gamma",
                "The identity |Gamma(1 + i eta)|^2 = pi eta / sinh(pi eta) is a named symbol law for real eta, checked to be even and to agree with Gamma(z+1) = z Gamma(z).",
                prelude,
            ),
        )
    if _is_rutherford_identity(left, right):
        rutherford_abs2_identity()
        return (
            _identity_rule(
                left,
                right,
                "math.coulomb.rutherford",
                "The Rutherford amplitude is the exact Coulomb phase times -eta / (2 k sin(theta/2)^2). Its modulus squared is eta^2 / (4 k^2 sin(theta/2)^4), after the unimodular Gamma phase and the unimodular Coulomb logarithm cancel.",
                prelude,
            ),
        )
    if left_value == 0 and (right_value == 0 or _rhs_is_zero(right) or _rhs_is_zero(left)):
        return (
            _identity_rule(
                left,
                right,
                "math.coulomb.radial",
                "The regular Coulomb wave rho^{l+1} exp(-i rho) 1F1(l + 1 - i eta; 2 l + 2; 2 i rho) satisfies u'' + (1 - 2 eta / rho - l(l+1)/rho^2) u = 0 identically for l = 0, 1, 2, and 3, after the confluent equation is used to eliminate the second z-derivative.",
                prelude,
            ),
        )
    return (
        _open_rule(left, right, "This Coulomb claim is not an admitted exact identity."),
    )


def coulomb_value_rule(origin: Term, result: object, prelude: tuple[str, ...] = ()) -> Rule:
    _standing()
    shown = pretty(origin) if result != 0 else "0"
    return Rule(
        id="math.coulomb.value",
        layer="base",
        stage="quantity",
        title=f"{pretty(origin)} = {shown}" if result == 0 else pretty(origin),
        produces=f"value({shown})" if result != 0 else f"value({shown})",
        detail_lines=(*prelude, "A Coulomb continuum identity is kept only when it is checked exactly."),
    )


def side_as_coulomb(term: Term) -> object:
    try:
        return _eval_coulomb(term)
    except NotExact:
        if isinstance(term, IntLit) and term.n == 0:
            return 0
        return None
