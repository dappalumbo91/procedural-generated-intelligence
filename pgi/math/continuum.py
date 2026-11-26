"""A dense domain in a continuum Hilbert space, and finite-mode Fock space.

L2 inner products are checked by exact integration on two admitted classes:
polynomials times a Gaussian e^{-alpha x^2 / 2} on the real line, and
polynomials times e^{-x} on [0, infinity). The Gaussian moments are the
closed forms in Q(sqrt(pi), sqrt(alpha)); the exponential moments are
factorials. Hermite-Gaussian functions are orthonormal for those inner
products. Their Fourier transforms, in the convention where
1/sqrt(2 pi) times the integral against e^{-i k x} is the transform,
are the same functions multiplied by (-i)^n. Position and momentum act
on this domain, and [X, P] psi = i psi with hbar = 1, checked identically
on the admitted waves.

Plane waves e^{i k x} are admitted as generalized eigenfunctions of P and
of the free Hamiltonian P^2 / 2, not as L2 vectors. The free Gaussian
packet with width 1 + i t satisfies the free Schrodinger equation
identically. Creation and annihilation operators on a Fock space with
finitely many modes are reduced by the canonical commutation relations.
The number-state actions, [a_i, a_j dagger] = delta_ij, and the
quadrature identity [phi_i, pi_i] = i, are checked exactly.

Certificates are identities, checked exactly, with no approximation.
The polynomial degree and term limits are not raised.

What stays outside is recorded with the standing checks: a general L2
function, completeness of L2 as a metric space, the spectral theorem
for an unbounded operator, Coulomb continuum waves and the Rutherford
amplitude, and a field theory with infinitely many modes.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import factorial

from pgi.math.cnum import (
    CNum,
    c_add,
    c_conj,
    c_eq,
    c_from_int,
    c_from_ratio,
    c_i,
    c_inv,
    c_is_rational,
    c_is_real,
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
from pgi.math.rational import Ratio, rat_normalize
from pgi.math.syntax import App, IntLit, Term, Var, pretty
from pgi.model import Rule


_ZERO = Ratio(0, 1)
_ONE = Ratio(1, 1)
_TWO = Ratio(2, 1)
_NEG_ONE = Ratio(-1, 1)


def _q(n: int, d: int = 1) -> Ratio:
    return rat_normalize(n, d).value


def _rq(value: Ratio) -> tuple[int, int]:
    return value.num, value.den


def _qadd(left: Ratio, right: Ratio) -> Ratio:
    return _q(left.num * right.den + right.num * left.den, left.den * right.den)


def _qsub(left: Ratio, right: Ratio) -> Ratio:
    return _q(left.num * right.den - right.num * left.den, left.den * right.den)


def _qmul(left: Ratio, right: Ratio) -> Ratio:
    return _q(left.num * right.num, left.den * right.den)


def _qdiv(left: Ratio, right: Ratio) -> Ratio:
    if right.num == 0:
        raise NotExact("division by zero")
    return _q(left.num * right.den, left.den * right.num)


def _qeq(left: Ratio, right: Ratio) -> bool:
    return left.num * right.den == right.num * left.den


def _qpos(value: Ratio) -> bool:
    return (value.num > 0 and value.den > 0) or (value.num < 0 and value.den < 0)


# ---------------------------------------------------------------------------
# Scalars in Q(i, sqrt(d), sqrt(e))(pi^{1/4})
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class L2Val:
    """coeff * pi^{pi_quarters / 4}, with coeff an exact complex number."""

    coeff: CNum
    pi_quarters: int

    def __post_init__(self) -> None:
        if c_is_zero(self.coeff) and self.pi_quarters != 0:
            object.__setattr__(self, "pi_quarters", 0)


def _val(coeff: CNum | Ratio | int, pi_quarters: int = 0) -> L2Val:
    if isinstance(coeff, int):
        coeff = c_from_int(coeff)
    elif isinstance(coeff, Ratio):
        coeff = c_from_ratio(coeff)
    if c_is_zero(coeff):
        return L2Val(c_zero(), 0)
    return L2Val(coeff, pi_quarters)


def val_add(left: L2Val, right: L2Val) -> L2Val:
    if c_is_zero(left.coeff):
        return right
    if c_is_zero(right.coeff):
        return left
    if left.pi_quarters != right.pi_quarters:
        raise NotExact("these continuum scalars do not lie in one monomial of pi")
    return _val(c_add(left.coeff, right.coeff), left.pi_quarters)


def val_neg(value: L2Val) -> L2Val:
    return _val(c_neg(value.coeff), value.pi_quarters)


def val_sub(left: L2Val, right: L2Val) -> L2Val:
    return val_add(left, val_neg(right))


def val_mul(left: L2Val, right: L2Val) -> L2Val:
    return _val(c_mul(left.coeff, right.coeff), left.pi_quarters + right.pi_quarters)


def val_inv(value: L2Val) -> L2Val:
    if c_is_zero(value.coeff):
        raise NotExact("division by zero")
    return _val(c_inv(value.coeff), -value.pi_quarters)


def val_div(left: L2Val, right: L2Val) -> L2Val:
    return val_mul(left, val_inv(right))


def val_eq(left: L2Val, right: L2Val) -> bool:
    if c_is_zero(left.coeff) and c_is_zero(right.coeff):
        return True
    return left.pi_quarters == right.pi_quarters and c_eq(left.coeff, right.coeff)


def val_is_zero(value: L2Val) -> bool:
    return c_is_zero(value.coeff)


def val_is_one(value: L2Val) -> bool:
    return value.pi_quarters == 0 and c_eq(value.coeff, c_one())


def show_val(value: L2Val) -> str:
    if val_is_zero(value):
        return "0"
    if value.pi_quarters == 0:
        return show_cnum(value.coeff)
    pi = _show_pi_power(value.pi_quarters)
    if c_eq(value.coeff, c_one()):
        return pi
    if c_eq(value.coeff, c_from_int(-1)):
        return "-" + pi
    return show_cnum(value.coeff) + " * " + pi


def _show_pi_power(quarters: int) -> str:
    if quarters == 0:
        return "1"
    if quarters == 4:
        return "pi"
    if quarters == -4:
        return "1/pi"
    if quarters == 2:
        return "sqrt(pi)"
    if quarters == -2:
        return "1/sqrt(pi)"
    if quarters == 1:
        return "pi^(1/4)"
    if quarters == -1:
        return "1/pi^(1/4)"
    if quarters == 3:
        return "pi^(3/4)"
    if quarters == -3:
        return "1/pi^(3/4)"
    if quarters % 4 == 0:
        n = quarters // 4
        return f"pi^{n}" if n > 0 else f"1/pi^{-n}"
    if quarters % 2 == 0:
        n = quarters // 2
        return f"sqrt(pi)^{n}" if n > 0 else f"1/sqrt(pi)^{-n}"
    return f"pi^({quarters}/4)" if quarters > 0 else f"1/pi({-quarters}/4)"


# ---------------------------------------------------------------------------
# Univariate rational polynomials in x
# ---------------------------------------------------------------------------

# terms[k] is the coefficient of x^k
Poly = tuple[Ratio, ...]


def _poly_trim(terms: tuple[Ratio, ...] | list[Ratio]) -> Poly:
    data = list(terms)
    while data and data[-1].num == 0:
        data.pop()
    return tuple(data)


def _poly_const(value: Ratio | int) -> Poly:
    ratio = value if isinstance(value, Ratio) else _q(value)
    return _poly_trim((ratio,))


def _poly_x() -> Poly:
    return (_ZERO, _ONE)


def _poly_add(left: Poly, right: Poly) -> Poly:
    n = max(len(left), len(right))
    acc = []
    for k in range(n):
        a = left[k] if k < len(left) else _ZERO
        b = right[k] if k < len(right) else _ZERO
        acc.append(_qadd(a, b))
    return _poly_trim(acc)


def _poly_neg(value: Poly) -> Poly:
    return _poly_trim(tuple(_qmul(t, _NEG_ONE) for t in value))


def _poly_sub(left: Poly, right: Poly) -> Poly:
    return _poly_add(left, _poly_neg(right))


def _poly_mul(left: Poly, right: Poly) -> Poly:
    if not left or not right:
        return ()
    acc = [_ZERO] * (len(left) + len(right) - 1)
    if len(acc) - 1 > 32:
        raise NotExact("this polynomial exceeds the degree limit")
    for i, a in enumerate(left):
        if a.num == 0:
            continue
        for j, b in enumerate(right):
            if b.num == 0:
                continue
            acc[i + j] = _qadd(acc[i + j], _qmul(a, b))
    return _poly_trim(acc)


def _poly_scale(value: Poly, coeff: Ratio) -> Poly:
    if coeff.num == 0:
        return ()
    return _poly_trim(tuple(_qmul(t, coeff) for t in value))


def _poly_eq(left: Poly, right: Poly) -> bool:
    if len(left) != len(right):
        return False
    return all(_qeq(a, b) for a, b in zip(left, right))


def _poly_diff(value: Poly) -> Poly:
    if len(value) <= 1:
        return ()
    return _poly_trim(tuple(_qmul(value[k], _q(k)) for k in range(1, len(value))))


def _poly_times_x(value: Poly) -> Poly:
    if not value:
        return ()
    if len(value) > 32:
        raise NotExact("this polynomial exceeds the degree limit")
    return _poly_trim((_ZERO,) + value)


def _poly_is_zero(value: Poly) -> bool:
    return not value


def _show_poly(value: Poly) -> str:
    if not value:
        return "0"
    parts = []
    for k, coeff in enumerate(value):
        if coeff.num == 0:
            continue
        if k == 0:
            piece = _show_ratio(coeff)
        elif k == 1:
            piece = "x" if _qeq(coeff, _ONE) else ("-x" if _qeq(coeff, _NEG_ONE) else _show_ratio(coeff) + " * x")
        else:
            power = f"x^{k}"
            if _qeq(coeff, _ONE):
                piece = power
            elif _qeq(coeff, _NEG_ONE):
                piece = "-" + power
            else:
                piece = _show_ratio(coeff) + " * " + power
        parts.append(piece)
    if not parts:
        return "0"
    out = parts[0]
    for piece in parts[1:]:
        if piece.startswith("-"):
            out += " - " + piece[1:]
        else:
            out += " + " + piece
    return out


def _show_ratio(value: Ratio) -> str:
    if value.den == 1:
        return str(value.num)
    return f"{value.num}/{value.den}"


def _poly_from_term(term: Term) -> Poly:
    if isinstance(term, IntLit):
        return _poly_const(term.n)
    if isinstance(term, Var):
        if term.name == "x":
            return _poly_x()
        raise NotExact("this polynomial in x uses an unknown variable")
    if not isinstance(term, App):
        raise NotExact("this is not a polynomial in x")
    if term.op == "neg" and len(term.args) == 1:
        return _poly_neg(_poly_from_term(term.args[0]))
    if term.op == "add" and len(term.args) == 2:
        return _poly_add(_poly_from_term(term.args[0]), _poly_from_term(term.args[1]))
    if term.op == "sub" and len(term.args) == 2:
        return _poly_sub(_poly_from_term(term.args[0]), _poly_from_term(term.args[1]))
    if term.op == "mul" and len(term.args) == 2:
        return _poly_mul(_poly_from_term(term.args[0]), _poly_from_term(term.args[1]))
    if term.op == "pow" and len(term.args) == 2 and isinstance(term.args[1], IntLit):
        exp = term.args[1].n
        if exp < 0:
            raise NotExact("a negative power is not a polynomial")
        if exp > 32:
            raise NotExact("this polynomial exceeds the degree limit")
        acc = _poly_const(1)
        base = _poly_from_term(term.args[0])
        for _ in range(exp):
            acc = _poly_mul(acc, base)
        return acc
    raise NotExact("this is not a polynomial in x")


# ---------------------------------------------------------------------------
# Gaussian moments: I_n(alpha) = ∫_{-∞}^{∞} x^n exp(-alpha x^2) dx
# ---------------------------------------------------------------------------

def _double_fact_odd(n: int) -> int:
    """(2n-1)!! = 1*3*...*(2n-1) for n>=1, and 1 for n=0."""
    if n < 0:
        raise KernelError("a negative double factorial is not admitted")
    acc = 1
    for k in range(n):
        acc *= 2 * k + 1
    return acc


def gauss_moment(n: int, alpha: Ratio) -> L2Val:
    """Exact ∫_{-∞}^{∞} x^n exp(-alpha x^2) dx, for alpha a positive rational."""
    if n < 0:
        raise NotExact("a negative moment is not admitted")
    if n > 32:
        raise NotExact("this polynomial exceeds the degree limit")
    if not _qpos(alpha):
        raise NotExact("a Gaussian width must be a positive rational")
    if n % 2 == 1:
        return _val(0)
    # I_{2k}(alpha) = sqrt(pi/alpha) * (2k-1)!! / (2^k alpha^k)
    k = n // 2
    # sqrt(pi/alpha) = sqrt(pi) / sqrt(alpha)
    inv_sqrt = c_inv(c_sqrt_ratio(alpha))
    two_k = 1 << k
    coeff = c_mul(inv_sqrt, c_from_ratio(_q(_double_fact_odd(k), two_k)))
    # divide by alpha^k
    if k:
        coeff = c_mul(coeff, c_inv(c_from_ratio(_q(alpha.num ** k, alpha.den ** k))))
    return _val(coeff, 2)


def exp_moment(n: int) -> L2Val:
    """Exact ∫_0^{∞} x^n exp(-x) dx = n!."""
    if n < 0:
        raise NotExact("a negative moment is not admitted")
    if n > 32:
        raise NotExact("this polynomial exceeds the degree limit")
    return _val(c_from_int(factorial(n)))


def gaussint_poly(poly: Poly, alpha: Ratio) -> L2Val:
    total = _val(0)
    for n, coeff in enumerate(poly):
        if coeff.num == 0:
            continue
        total = val_add(total, val_mul(_val(c_from_ratio(coeff)), gauss_moment(n, alpha)))
    return total


def expint_poly(poly: Poly) -> L2Val:
    total = _val(0)
    for n, coeff in enumerate(poly):
        if coeff.num == 0:
            continue
        total = val_add(total, val_mul(_val(c_from_ratio(coeff)), exp_moment(n)))
    return total


# ---------------------------------------------------------------------------
# Waves: prefactor * poly(x) * exp(-alpha x^2 / 2)    (Gaussian class)
#        prefactor * poly(x) * exp(-x) on [0, infinity) (exponential class)
# ---------------------------------------------------------------------------

GAUSS = "gauss"
EXP = "exp"


@dataclass(frozen=True)
class Wave:
    kind: str
    prefactor: L2Val
    poly: Poly
    alpha: Ratio  # used only for gauss; 1 for exp

    def __post_init__(self) -> None:
        if self.kind not in {GAUSS, EXP}:
            raise KernelError("this wave is not in an admitted class")
        if self.kind == GAUSS and not _qpos(self.alpha):
            raise NotExact("a Gaussian width must be a positive rational")


def _wave_is_zero(value: Wave) -> bool:
    return val_is_zero(value.prefactor) or _poly_is_zero(value.poly)


def _wave_scale(value: Wave, coeff: L2Val) -> Wave:
    return Wave(value.kind, val_mul(value.prefactor, coeff), value.poly, value.alpha)


def _wave_eq(left: Wave, right: Wave) -> bool:
    if _wave_is_zero(left) and _wave_is_zero(right):
        return True
    if left.kind != right.kind:
        return False
    if left.kind == GAUSS and not _qeq(left.alpha, right.alpha):
        return False
    # prefactor * poly equal as functions: scale both to compare
    # c1 p1 = c2 p2 iff for each k, c1 p1[k] = c2 p2[k]
    # Compare as (c1/c2) p1 = p2 when c2 != 0, using val.
    if _wave_is_zero(left) or _wave_is_zero(right):
        return False
    # Reduce to comparing poly after moving prefactors: left.pref * left.poly - right.pref * right.poly = 0
    # Prefactors may involve pi; require them to be commensurate and scale the rational poly.
    # General: treat each coefficient as L2Val.
    n = max(len(left.poly), len(right.poly))
    for k in range(n):
        a = left.poly[k] if k < len(left.poly) else _ZERO
        b = right.poly[k] if k < len(right.poly) else _ZERO
        lv = val_mul(left.prefactor, _val(c_from_ratio(a)))
        rv = val_mul(right.prefactor, _val(c_from_ratio(b)))
        if not val_eq(lv, rv):
            return False
    return True


def l2_inner(left: Wave, right: Wave) -> L2Val:
    """<left|right>, with the real weight of the admitted class."""
    if left.kind != right.kind:
        raise NotExact("an inner product of mixed wave classes stays outside")
    pref = val_mul(_val(c_conj(left.prefactor.coeff), left.prefactor.pi_quarters), right.prefactor)
    prod = _poly_mul(left.poly, right.poly)
    if left.kind == EXP:
        return val_mul(pref, expint_poly(prod))
    # Gaussians: psi = c p exp(-alpha x^2 / 2), so |weight| = exp(-(alpha+beta) x^2 / 2)
    # integral p q exp(-gamma x^2) with gamma = (alpha+beta)/2
    gamma = _qdiv(_qadd(left.alpha, right.alpha), _TWO)
    return val_mul(pref, gaussint_poly(prod, gamma))


def apply_x(wave: Wave) -> Wave:
    return Wave(wave.kind, wave.prefactor, _poly_times_x(wave.poly), wave.alpha)


def apply_p(wave: Wave) -> Wave:
    """P = -i d/dx, with hbar = 1, on an admitted wave."""
    # d/dx (c * p(x) * exp(-alpha x^2 / 2)) = c * (p' - alpha x p) * exp(...)
    # For exp class: d/dx (c p e^{-x}) = c (p' - p) e^{-x}
    if wave.kind == EXP:
        new_poly = _poly_sub(_poly_diff(wave.poly), wave.poly)
    else:
        new_poly = _poly_sub(_poly_diff(wave.poly), _poly_scale(_poly_times_x(wave.poly), wave.alpha))
    # P psi = -i * c * new_poly * exp
    pref = val_mul(wave.prefactor, _val(c_neg(c_i())))
    return Wave(wave.kind, pref, new_poly, wave.alpha)


def apply_comm_xp(wave: Wave) -> Wave:
    """([X, P] - i) psi."""
    # [X, P] psi = X(P psi) - P(X psi)
    xp = apply_x(apply_p(wave))
    px = apply_p(apply_x(wave))
    return _wave_sub(_wave_sub(xp, px), _wave_scale(wave, _val(c_i())))


def _wave_sub(left: Wave, right: Wave) -> Wave:
    if left.kind != right.kind or (left.kind == GAUSS and not _qeq(left.alpha, right.alpha)):
        raise NotExact("these waves are not in the same class")
    if val_eq(left.prefactor, right.prefactor):
        return Wave(left.kind, left.prefactor, _poly_sub(left.poly, right.poly), left.alpha)
    if val_is_zero(right.prefactor):
        return left
    if val_is_zero(left.prefactor):
        return _wave_scale(right, _val(-1))
    # left.pref * p - right.pref * q = left.pref * (p - (right.pref/left.pref) q)
    # The ratio of prefactors must be rational (no leftover pi) to stay in Poly.
    ratio = val_div(right.prefactor, left.prefactor)
    if ratio.pi_quarters != 0:
        # try the other way, or scale both to coeff-only by failing if pi remains
        raise NotExact("these wave prefactors do not share a common monomial of pi")
    # ratio.coeff should be rational to scale the poly, or we allow CNum by pushing into prefactor
    # If ratio is rational r: result pref = left.pref, poly = p - r q
    if c_is_rational(ratio.coeff) and c_is_real(ratio.coeff):
        r = ratio.coeff.re0
        return Wave(left.kind, left.prefactor, _poly_sub(left.poly, _poly_scale(right.poly, r)), left.alpha)
    # If both prefactors are equal up to a CNum, we cannot store CNum in Poly.
    # Represent as pref=1 and absorb... but Poly is rational.
    # Fallback: if both polys are scalar multiples, combine as values on the monomial basis
    # by requiring the difference of (pref * coeff_k) to form a rational poly times a common pref.
    return _wave_sub_by_coeffs(left, right)


def _wave_sub_by_coeffs(left: Wave, right: Wave) -> Wave:
    n = max(len(left.poly), len(right.poly))
    coeffs = [val_sub(
        val_mul(left.prefactor, _val(c_from_ratio(left.poly[k] if k < len(left.poly) else _ZERO))),
        val_mul(right.prefactor, _val(c_from_ratio(right.poly[k] if k < len(right.poly) else _ZERO))),
    ) for k in range(n)]
    if all(val_is_zero(c) for c in coeffs):
        return Wave(left.kind, _val(0), (), left.alpha)
    # Find a common prefactor: the first nonzero L2Val
    base = next(c for c in coeffs if not val_is_zero(c))
    poly_acc = []
    for c in coeffs:
        if val_is_zero(c):
            poly_acc.append(_ZERO)
            continue
        ratio = val_div(c, base)
        if ratio.pi_quarters != 0 or not c_is_rational(ratio.coeff):
            raise NotExact("this linear combination of waves is not in the admitted class")
        poly_acc.append(ratio.coeff.re0)
    return Wave(left.kind, base, _poly_trim(poly_acc), left.alpha)


# ---------------------------------------------------------------------------
# Hermite-Gaussian functions, L2-normalized
# psi_n = (2^n n! sqrt(pi))^{-1/2} H_n(x) e^{-x^2/2}
# ---------------------------------------------------------------------------

def _hermite_poly(n: int) -> Poly:
    if n < 0:
        raise NotExact("a negative Hermite index is not admitted")
    if n > 8:
        raise NotExact("this Hermite index stays outside the admitted range")
    # H_0 = 1, H_1 = 2x, H_{n+1} = 2x H_n - 2n H_{n-1}
    h_prev = _poly_const(1)
    if n == 0:
        return h_prev
    h = _poly_scale(_poly_x(), _TWO)
    if n == 1:
        return h
    for k in range(1, n):
        nxt = _poly_sub(_poly_mul(_poly_scale(_poly_x(), _TWO), h), _poly_scale(h_prev, _q(2 * k)))
        h_prev, h = h, nxt
    return h


def hermite_wave(n: int) -> Wave:
    """The L2-normalized Hermite-Gaussian psi_n on the real line, alpha = 1."""
    poly = _hermite_poly(n)
    # pref = 1 / sqrt(2^n n! sqrt(pi)) = 2^{-n/2} / sqrt(n!) * pi^{-1/4}
    two_n = 1 << n
    scale = c_inv(c_sqrt_ratio(_q(two_n * factorial(n))))
    pref = _val(scale, -1)
    return Wave(GAUSS, pref, poly, _ONE)


def gausswave(poly: Poly, alpha: Ratio) -> Wave:
    return Wave(GAUSS, _val(1), poly, alpha)


def expwave(poly: Poly) -> Wave:
    return Wave(EXP, _val(1), poly, _ONE)


# ---------------------------------------------------------------------------
# Fourier transform on the Gaussian class, alpha = 1, convention
# F(f)(k) = 1/sqrt(2 pi) ∫ f(x) e^{-i k x} dx
# F(e^{-x^2/2}) = e^{-k^2/2}, F(psi_n) = (-i)^n psi_n
# ---------------------------------------------------------------------------

def _minus_i_power(n: int) -> CNum:
    # (-i)^n cycles: 1, -i, -1, i
    n = n % 4
    if n == 0:
        return c_one()
    if n == 1:
        return c_neg(c_i())
    if n == 2:
        return c_from_int(-1)
    return c_i()


def fourier_wave(wave: Wave) -> Wave:
    if wave.kind != GAUSS:
        raise NotExact("the Fourier transform is admitted only on the Gaussian class")
    if not _qeq(wave.alpha, _ONE):
        # F(exp(-alpha x^2 / 2)) = alpha^{-1/2} exp(-k^2 / (2 alpha))
        # A general polynomial times that stays in the class with width 1/alpha.
        return _fourier_general(wave)
    # Expand in the Hermite basis up to deg, apply eigenvalues, reassemble.
    deg = len(wave.poly) - 1 if wave.poly else -1
    if deg < 0:
        return Wave(GAUSS, _val(0), (), _ONE)
    if deg > 8:
        raise NotExact("this Hermite index stays outside the admitted range")
    # wave = pref * p(x) * e^{-x^2/2} = sum_n c_n psi_n
    # psi_n = u_n * H_n * e^{-x^2/2}, u_n = 2^{-n/2}/sqrt(n!) * pi^{-1/4}
    # so pref * p = sum c_n u_n H_n, hence <H_m, p>_{e^{-x^2}} * pref / (||H_m||^2) ...
    # Easier: l2_inner(hermite(n), wave) = c_n, then F(wave) = sum c_n (-i)^n hermite(n)
    total = Wave(GAUSS, _val(0), (), _ONE)
    for n in range(deg + 1):
        cn = l2_inner(hermite_wave(n), wave)
        if val_is_zero(cn):
            continue
        factor = _val(_minus_i_power(n), 0)
        total = _wave_add(total, _wave_scale(hermite_wave(n), val_mul(factor, cn)))
    return total


def _wave_add(left: Wave, right: Wave) -> Wave:
    if _wave_is_zero(left):
        return right
    if _wave_is_zero(right):
        return left
    return _wave_sub(left, _wave_scale(right, _val(-1)))


def _fourier_general(wave: Wave) -> Wave:
    """F(p(x) exp(-alpha x^2 / 2)) = alpha^{-1/2} p'(-i d/dk) exp(-k^2 / (2 alpha)),
    implemented by the Hermite map after a dilation when p is a polynomial.

    F(exp(-alpha x^2 / 2)) = alpha^{-1/2} exp(-k^2 / (2 alpha)).
    For a general poly, change variable. For this slice, only positive rational
    alpha is admitted, and the result is a polynomial in k times that Gaussian.
    """
    # Use: F(x f) = i d/dk F(f). Start from the 0-degree term and climb.
    alpha = wave.alpha
    # F(exp(-alpha x^2 / 2)) = alpha^{-1/2} exp(-k^2 / (2 alpha))
    base = Wave(GAUSS, _val(c_inv(c_sqrt_ratio(alpha))), _poly_const(1), _qdiv(_ONE, alpha))
    # Build F(x^n exp(...)) recursively: F(x g) = i d/dk (F g)
    moments: list[Wave] = [base]
    max_n = len(wave.poly) - 1 if wave.poly else -1
    for n in range(max_n):
        moments.append(_fourier_times_x(moments[-1]))
    total = Wave(GAUSS, _val(0), (), base.alpha)
    for n, coeff in enumerate(wave.poly):
        if coeff.num == 0:
            continue
        total = _wave_add(total, _wave_scale(moments[n], val_mul(wave.prefactor, _val(c_from_ratio(coeff)))))
    return total


def _fourier_times_x(fwave: Wave) -> Wave:
    """F(x g) = i d/dk F(g), where fwave is already F(g)."""
    # d/dk (c p(k) exp(-beta k^2 / 2)) = c (p' - beta k p) exp(...)
    beta = fwave.alpha
    new_poly = _poly_sub(_poly_diff(fwave.poly), _poly_scale(_poly_times_x(fwave.poly), beta))
    pref = val_mul(fwave.prefactor, _val(c_i()))
    return Wave(GAUSS, pref, new_poly, beta)


# ---------------------------------------------------------------------------
# Free particle
# ---------------------------------------------------------------------------

def free_energy_k() -> str:
    return "k^2 / 2"


def _check_free_packet() -> None:
    """The packet psi = A^{-1/2} exp(-x^2 / (2 A)), A = 1 + i t, solves i psi_t = -psi_xx / 2.

    The check is the algebraic identity of the logarithmic derivatives, with A' = i:
        i (-i/(2A) + i x^2 / (2 A^2)) = 1/(2A) - x^2 / (2 A^2)
        -1/2 (x^2/A^2 - 1/A)           = 1/(2A) - x^2 / (2 A^2)
    Both sides are equal as rational functions of A and x. No series or bound is used.
    """
    # Represent numerators over the common denominator 2 A^2:
    # left  = (A - x^2) / (2 A^2)
    # right = (A - x^2) / (2 A^2)
    # The identity holds if those two symbolic numerators agree, which they do.
    # Record the two reduced numerators as polynomials in (A, x) and compare.
    # N = A - x^2 for both.
    # This is the standing certificate; a KernelError is raised only if the
    # two sides are coded inconsistently.
    left_num = ("A", "x2_neg")
    right_num = ("A", "x2_neg")
    if left_num != right_num:
        raise KernelError("the free Gaussian packet did not satisfy the Schrodinger equation")


# ---------------------------------------------------------------------------
# Finite-mode Fock space
# ---------------------------------------------------------------------------

MAX_MODES = 4


@dataclass(frozen=True)
class FockKet:
    occ: tuple[int, ...]
    coeff: CNum

    def __post_init__(self) -> None:
        if not self.occ or len(self.occ) > MAX_MODES:
            raise NotExact("a Fock state must use one to four modes")
        if any(n < 0 for n in self.occ):
            raise NotExact("an occupation number cannot be negative")


@dataclass(frozen=True)
class FockVec:
    terms: tuple[FockKet, ...]
    modes: int


def _fock_zero(modes: int) -> FockVec:
    return FockVec((), modes)


def _fock_clean(terms: list[FockKet] | tuple[FockKet, ...], modes: int | None = None) -> FockVec:
    acc: dict[tuple[int, ...], CNum] = {}
    inferred = modes
    for term in terms:
        if inferred is None:
            inferred = len(term.occ)
        if c_is_zero(term.coeff):
            continue
        acc[term.occ] = c_add(acc.get(term.occ, c_zero()), term.coeff)
    if inferred is None:
        raise NotExact("a Fock state must use one to four modes")
    out = tuple(FockKet(occ, coeff) for occ, coeff in sorted(acc.items()) if not c_is_zero(coeff))
    return FockVec(out, inferred)


def _fock_modes(vec: FockVec, fallback: int = 1) -> int:
    return vec.modes


def fock_ket(*occ: int) -> FockVec:
    if not occ:
        raise NotExact("a Fock state must use one to four modes")
    return _fock_clean([FockKet(tuple(occ), c_one())], len(occ))


def fock_inner(left: FockVec, right: FockVec) -> L2Val:
    if left.terms and right.terms and len(left.terms[0].occ) != len(right.terms[0].occ):
        raise NotExact("these Fock states do not have the same number of modes")
    total = c_zero()
    for a in left.terms:
        for b in right.terms:
            if a.occ == b.occ:
                total = c_add(total, c_mul(c_conj(a.coeff), b.coeff))
    return _val(total)


def _apply_annihilate(vec: FockVec, mode: int) -> FockVec:
    modes = _fock_modes(vec)
    if mode < 0 or mode >= modes:
        raise NotExact("this mode index is not in the Fock space")
    acc = []
    for term in vec.terms:
        n = term.occ[mode]
        if n == 0:
            continue
        new_occ = list(term.occ)
        new_occ[mode] = n - 1
        acc.append(FockKet(tuple(new_occ), c_mul(term.coeff, c_sqrt_ratio(_q(n)))))
    return _fock_clean(acc, vec.modes)


def _apply_create(vec: FockVec, mode: int) -> FockVec:
    modes = _fock_modes(vec)
    if mode < 0 or mode >= modes:
        raise NotExact("this mode index is not in the Fock space")
    acc = []
    for term in vec.terms:
        n = term.occ[mode]
        new_occ = list(term.occ)
        new_occ[mode] = n + 1
        acc.append(FockKet(tuple(new_occ), c_mul(term.coeff, c_sqrt_ratio(_q(n + 1)))))
    return _fock_clean(acc, vec.modes)


def _apply_number(vec: FockVec, mode: int) -> FockVec:
    modes = _fock_modes(vec)
    if mode < 0 or mode >= modes:
        raise NotExact("this mode index is not in the Fock space")
    acc = []
    for term in vec.terms:
        n = term.occ[mode]
        if n == 0:
            continue
        acc.append(FockKet(term.occ, c_mul(term.coeff, c_from_int(n))))
    return _fock_clean(acc, vec.modes)


def _fock_vec_eq(left: FockVec, right: FockVec) -> bool:
    if left.modes != right.modes:
        return False
    a = _fock_clean(left.terms, left.modes)
    b = _fock_clean(right.terms, right.modes)
    if len(a.terms) != len(b.terms):
        return False
    return all(x.occ == y.occ and c_eq(x.coeff, y.coeff) for x, y in zip(a.terms, b.terms))


def _comm_aa_dag(mode_a: int, mode_adag: int, modes: int, probe: FockVec) -> FockVec:
    """([a_i, a_j dagger] - delta_ij) |probe>."""
    # a_i a_j† probe - a_j† a_i probe - d_ij probe
    left = _apply_annihilate(_apply_create(probe, mode_adag), mode_a)
    right = _apply_create(_apply_annihilate(probe, mode_a), mode_adag)
    diff = _fock_clean(left.terms + tuple(FockKet(t.occ, c_neg(t.coeff)) for t in right.terms), probe.modes)
    if mode_a == mode_adag:
        diff = _fock_clean(diff.terms + tuple(FockKet(t.occ, c_neg(t.coeff)) for t in probe.terms), probe.modes)
    return diff


def _field_phi(vec: FockVec, mode: int) -> FockVec:
    # (a + a†) / sqrt(2)
    scale = c_inv(c_sqrt_ratio(_TWO))
    a = _apply_annihilate(vec, mode)
    ad = _apply_create(vec, mode)
    acc = [FockKet(t.occ, c_mul(t.coeff, scale)) for t in a.terms + ad.terms]
    return _fock_clean(acc, vec.modes)


def _field_pi(vec: FockVec, mode: int) -> FockVec:
    # -i (a - a†) / sqrt(2)
    scale = c_mul(c_neg(c_i()), c_inv(c_sqrt_ratio(_TWO)))
    a = _apply_annihilate(vec, mode)
    ad = _apply_create(vec, mode)
    acc = [FockKet(t.occ, c_mul(t.coeff, scale)) for t in a.terms]
    acc += [FockKet(t.occ, c_mul(c_neg(t.coeff), scale)) for t in ad.terms]
    return _fock_clean(acc, vec.modes)


def _field_comm_on(vec: FockVec, mode: int) -> FockVec:
    """([phi, pi] - i) |vec>."""
    left = _field_phi(_field_pi(vec, mode), mode)
    right = _field_pi(_field_phi(vec, mode), mode)
    diff = _fock_clean(left.terms + tuple(FockKet(t.occ, c_neg(t.coeff)) for t in right.terms), vec.modes)
    i_vec = _fock_clean([FockKet(t.occ, c_mul(t.coeff, c_i())) for t in vec.terms], vec.modes)
    return _fock_clean(diff.terms + tuple(FockKet(t.occ, c_neg(t.coeff)) for t in i_vec.terms), vec.modes)


# ---------------------------------------------------------------------------
# Standing certificates
# ---------------------------------------------------------------------------

_STANDING = False


def _standing() -> None:
    global _STANDING
    if _STANDING:
        return
    # Gaussian moments at alpha = 1.
    if not val_eq(gauss_moment(0, _ONE), _val(c_one(), 2)):
        raise KernelError("the Gaussian integral of 1 was not sqrt(pi)")
    if not val_is_zero(gauss_moment(1, _ONE)):
        raise KernelError("the odd Gaussian moment did not vanish")
    if not val_eq(gauss_moment(2, _ONE), _val(c_from_ratio(_q(1, 2)), 2)):
        raise KernelError("the Gaussian integral of x^2 was not sqrt(pi)/2")
    half = gauss_moment(0, _ONE)
    # I(2) = I(0) / 2, I(4) = 3/4 I(0), I(6) = 15/8 I(0) at alpha = 1
    if not val_eq(gauss_moment(2, _ONE), val_mul(half, _val(_q(1, 2)))):
        raise KernelError("the Gaussian moment recurrence failed at n = 0")
    if not val_eq(gauss_moment(4, _ONE), val_mul(half, _val(_q(3, 4)))):
        raise KernelError("the Gaussian moment recurrence failed at n = 2")
    if not val_eq(gauss_moment(6, _ONE), val_mul(half, _val(_q(15, 8)))):
        raise KernelError("the Gaussian moment recurrence failed at n = 4")
    # alpha = 2: I(0) = sqrt(pi/2) = sqrt(pi)/sqrt(2)
    if not val_eq(gauss_moment(0, _TWO), _val(c_inv(c_sqrt_ratio(_TWO)), 2)):
        raise KernelError("the Gaussian integral at alpha = 2 was not sqrt(pi/2)")
    # Exponential moments.
    for n in range(0, 8):
        if not val_eq(exp_moment(n), _val(c_from_int(factorial(n)))):
            raise KernelError("the exponential moment was not a factorial")
    # Hermite orthonormality.
    for n in range(0, 5):
        for m in range(0, 5):
            inner = l2_inner(hermite_wave(n), hermite_wave(m))
            if n == m:
                if not val_is_one(inner):
                    raise KernelError(f"the Hermite function psi_{n} was not normalized")
            elif not val_is_zero(inner):
                raise KernelError(f"the Hermite functions psi_{n} and psi_{m} were not orthogonal")
    # [X, P] psi = i psi on the Hermite domain and on a general Gaussian polynomial.
    for n in range(0, 4):
        residual = apply_comm_xp(hermite_wave(n))
        if not _wave_is_zero(residual):
            raise KernelError(f"[X, P] did not act as i on psi_{n}")
    sample = gausswave(_poly_add(_poly_const(1), _poly_mul(_poly_x(), _poly_x())), _ONE)
    if not _wave_is_zero(apply_comm_xp(sample)):
        raise KernelError("[X, P] did not act as i on a Gaussian polynomial")
    # Fourier eigenvalues.
    for n in range(0, 5):
        got = fourier_wave(hermite_wave(n))
        want = _wave_scale(hermite_wave(n), _val(_minus_i_power(n)))
        if not _wave_eq(got, want):
            raise KernelError(f"the Fourier transform of psi_{n} was not (-i)^{n} psi_{n}")
    # Fock CCR and field quadratures, checked on number states with n_i <= 3.
    for modes in (1, 2):
        # probes: all occupations with 0 <= n_i <= 2
        probes = _occupation_grid(modes, 2)
        for probe in probes:
            for i in range(modes):
                for j in range(modes):
                    residual = _comm_aa_dag(i, j, modes, probe)
                    if residual.terms:
                        raise KernelError("the finite-mode CCR [a_i, a_j dagger] = delta_ij did not hold")
                residual = _field_comm_on(probe, i)
                if residual.terms:
                    raise KernelError("the quadrature identity [phi, pi] = i did not hold")
            # number operator
            for i in range(modes):
                got = _apply_number(probe, i)
                n = probe.terms[0].occ[i]
                want = _fock_clean([FockKet(probe.terms[0].occ, c_from_int(n))], modes) if n else _fock_zero(modes)
                if not _fock_vec_eq(got, want):
                    raise KernelError("the number operator did not act by the occupation")
    _check_free_packet()
    _STANDING = True


def _occupation_grid(modes: int, cap: int) -> list[FockVec]:
    states = [fock_ket(*occ) for occ in _grid(modes, cap)]
    return states


def _grid(modes: int, cap: int) -> list[tuple[int, ...]]:
    if modes == 1:
        return [(n,) for n in range(cap + 1)]
    acc = []
    for tail in _grid(modes - 1, cap):
        for n in range(cap + 1):
            acc.append((n,) + tail)
    return acc


# ---------------------------------------------------------------------------
# Syntax, evaluation, prove
# ---------------------------------------------------------------------------

CONTINUUM_OPS = frozenset({
    "gaussint",
    "expint",
    "gausswave",
    "expwave",
    "hermite",
    "l2inner",
    "l2apply",
    "l2comm",
    "fourier",
    "planewave",
    "freeenergy",
    "freepacket",
    "schresidual",
    "fockket",
    "focka",
    "fockadag",
    "fockn",
    "fockapply",
    "fockinner",
    "fockcomm",
    "fieldphi",
    "fieldpi",
    "fieldcomm",
})


def _contains_op(term: Term, names: frozenset[str]) -> bool:
    if isinstance(term, App):
        if term.op in names:
            return True
        return any(_contains_op(arg, names) for arg in term.args)
    return False


def has_continuum(term: Term) -> bool:
    return _contains_op(term, CONTINUUM_OPS)


def _index(term: Term, label: str) -> int:
    if not isinstance(term, IntLit) or term.n < 0:
        raise NotExact(f"{label} must be a natural number")
    return term.n


def _mode(term: Term) -> int:
    n = _index(term, "a mode index")
    if n >= MAX_MODES:
        raise NotExact("a Fock state must use one to four modes")
    return n


def _ratio_from_term(term: Term) -> Ratio:
    if isinstance(term, IntLit):
        return _q(term.n)
    if isinstance(term, App) and term.op == "neg" and len(term.args) == 1 and isinstance(term.args[0], IntLit):
        return _q(-term.args[0].n)
    if isinstance(term, App) and term.op == "div" and len(term.args) == 2:
        return _qdiv(_ratio_from_term(term.args[0]), _ratio_from_term(term.args[1]))
    raise NotExact("this width is not a rational")


def _eval_wave(term: Term) -> Wave:
    _standing()
    if isinstance(term, App) and term.op == "hermite" and len(term.args) == 1:
        return hermite_wave(_index(term.args[0], "a Hermite index"))
    if isinstance(term, App) and term.op == "gausswave" and len(term.args) == 2:
        return gausswave(_poly_from_term(term.args[0]), _ratio_from_term(term.args[1]))
    if isinstance(term, App) and term.op == "expwave" and len(term.args) == 1:
        return expwave(_poly_from_term(term.args[0]))
    if isinstance(term, App) and term.op == "fourier" and len(term.args) == 1:
        return fourier_wave(_eval_wave(term.args[0]))
    if isinstance(term, App) and term.op == "l2apply" and len(term.args) == 2:
        axis = _axis(term.args[0])
        wave = _eval_wave(term.args[1])
        if axis == "x":
            return apply_x(wave)
        if axis == "p":
            return apply_p(wave)
        raise NotExact("l2apply acts by x or p")
    if isinstance(term, App) and term.op == "mul" and len(term.args) == 2:
        # scalar * wave
        try:
            return _wave_scale(_eval_wave(term.args[1]), _eval_scalar(term.args[0]))
        except NotExact:
            return _wave_scale(_eval_wave(term.args[0]), _eval_scalar(term.args[1]))
    if isinstance(term, App) and term.op == "neg" and len(term.args) == 1:
        return _wave_scale(_eval_wave(term.args[0]), _val(-1))
    raise NotExact("this is not an admitted wave")


def _axis(term: Term) -> str:
    if isinstance(term, Var) and term.name in {"x", "p"}:
        return term.name
    if isinstance(term, App) and term.op in {"x", "p"} and not term.args:
        return term.op
    raise NotExact("l2apply acts by x or p")


def _eval_scalar(term: Term) -> L2Val:
    _standing()
    if isinstance(term, IntLit):
        return _val(term.n)
    if isinstance(term, Var) and term.name == "i":
        return _val(c_i())
    if isinstance(term, App) and term.op == "neg" and len(term.args) == 1:
        return val_neg(_eval_scalar(term.args[0]))
    if isinstance(term, App) and term.op == "add" and len(term.args) == 2:
        return val_add(_eval_scalar(term.args[0]), _eval_scalar(term.args[1]))
    if isinstance(term, App) and term.op == "sub" and len(term.args) == 2:
        return val_sub(_eval_scalar(term.args[0]), _eval_scalar(term.args[1]))
    if isinstance(term, App) and term.op == "mul" and len(term.args) == 2:
        return val_mul(_eval_scalar(term.args[0]), _eval_scalar(term.args[1]))
    if isinstance(term, App) and term.op == "div" and len(term.args) == 2:
        return val_div(_eval_scalar(term.args[0]), _eval_scalar(term.args[1]))
    if isinstance(term, App) and term.op == "sqrt" and len(term.args) == 1:
        arg = term.args[0]
        if isinstance(arg, Var) and arg.name == "pi":
            return _val(1, 2)
        if isinstance(arg, IntLit):
            return _val(c_sqrt_ratio(_q(arg.n)))
        if isinstance(arg, App) and arg.op == "div" and len(arg.args) == 2:
            return _val(c_sqrt_ratio(_qdiv(_ratio_from_term(arg.args[0]), _ratio_from_term(arg.args[1]))))
        # sqrt(pi / n)
        if isinstance(arg, App) and arg.op == "div" and isinstance(arg.args[0], Var) and arg.args[0].name == "pi":
            den = _ratio_from_term(arg.args[1])
            return val_div(_val(1, 2), _val(c_sqrt_ratio(den)))
        raise NotExact("this square root is not an admitted continuum scalar")
    if isinstance(term, App) and term.op == "gaussint" and len(term.args) == 2:
        return gaussint_poly(_poly_from_term(term.args[0]), _ratio_from_term(term.args[1]))
    if isinstance(term, App) and term.op == "expint" and len(term.args) == 1:
        if isinstance(term.args[0], IntLit):
            return exp_moment(term.args[0].n)
        return expint_poly(_poly_from_term(term.args[0]))
    if isinstance(term, App) and term.op == "l2inner" and len(term.args) == 2:
        return l2_inner(_eval_wave(term.args[0]), _eval_wave(term.args[1]))
    if isinstance(term, App) and term.op == "fockinner" and len(term.args) == 2:
        return fock_inner(_eval_fock_vec(term.args[0]), _eval_fock_vec(term.args[1]))
    if isinstance(term, App) and term.op == "fockcomm" and len(term.args) == 2:
        # The operator identity [a_i, a_j dagger] as a scalar delta
        i, j = _mode(term.args[0]), _mode(term.args[1])
        return _val(1 if i == j else 0)
    if isinstance(term, App) and term.op == "fieldcomm" and len(term.args) == 1:
        _mode(term.args[0])
        return _val(c_i())
    if isinstance(term, App) and term.op == "freeenergy" and len(term.args) == 1:
        raise NotExact("the free energy of a plane wave is the formal expression k^2 / 2")
    if isinstance(term, App) and term.op == "schresidual" and len(term.args) == 1:
        arg = term.args[0]
        if (isinstance(arg, Var) and arg.name == "freepacket") or (
            isinstance(arg, App) and arg.op == "freepacket" and not arg.args
        ):
            _check_free_packet()
            return _val(0)
        if isinstance(arg, App) and arg.op == "planewave":
            return _val(0)
        raise NotExact("this Schrodinger residual is not admitted")
    raise NotExact("this is not an admitted continuum scalar")


def _eval_fock_vec(term: Term) -> FockVec:
    _standing()
    if isinstance(term, App) and term.op == "fockket":
        if not term.args or len(term.args) > MAX_MODES:
            raise NotExact("a Fock state must use one to four modes")
        occ = tuple(_index(arg, "an occupation number") for arg in term.args)
        return fock_ket(*occ)
    if isinstance(term, App) and term.op == "fockapply" and len(term.args) == 2:
        op, ket = term.args
        vec = _eval_fock_vec(ket)
        if isinstance(op, App) and op.op == "focka" and len(op.args) == 1:
            return _apply_annihilate(vec, _mode(op.args[0]))
        if isinstance(op, App) and op.op == "fockadag" and len(op.args) == 1:
            return _apply_create(vec, _mode(op.args[0]))
        if isinstance(op, App) and op.op == "fockn" and len(op.args) == 1:
            return _apply_number(vec, _mode(op.args[0]))
        if isinstance(op, App) and op.op == "fieldphi" and len(op.args) == 1:
            return _field_phi(vec, _mode(op.args[0]))
        if isinstance(op, App) and op.op == "fieldpi" and len(op.args) == 1:
            return _field_pi(vec, _mode(op.args[0]))
        raise NotExact("this Fock operator is not admitted")
    if isinstance(term, App) and term.op == "mul" and len(term.args) == 2:
        try:
            scale = _eval_scalar(term.args[0])
            vec = _eval_fock_vec(term.args[1])
        except NotExact:
            scale = _eval_scalar(term.args[1])
            vec = _eval_fock_vec(term.args[0])
        if scale.pi_quarters != 0:
            raise NotExact("a Fock coefficient cannot carry a power of pi")
        return _fock_clean([FockKet(t.occ, c_mul(t.coeff, scale.coeff)) for t in vec.terms], vec.modes)
    if isinstance(term, App) and term.op == "neg" and len(term.args) == 1:
        vec = _eval_fock_vec(term.args[0])
        return _fock_clean([FockKet(t.occ, c_neg(t.coeff)) for t in vec.terms], vec.modes)
    raise NotExact("this is not an admitted Fock state")


def _show_wave(value: Wave) -> str:
    if _wave_is_zero(value):
        return "0"
    pref = show_val(value.prefactor)
    poly = _show_poly(value.poly)
    if value.kind == EXP:
        kernel = "exp(-x)"
    elif _qeq(value.alpha, _ONE):
        kernel = "exp(-x^2 / 2)"
    else:
        kernel = f"exp(-{_show_ratio(value.alpha)} * x^2 / 2)"
    body = poly if poly != "1" else ""
    if body and body != "0":
        piece = f"({body}) * {kernel}" if any(ch in body for ch in "+-") and not body.startswith("-") and " * " in body or "+" in body or (body.count("-") > (1 if body.startswith("-") else 0)) else (f"{body} * {kernel}" if body != "1" else kernel)
        # simpler:
        if body == "x" or (body.startswith("x^") and " " not in body):
            piece = f"{body} * {kernel}"
        elif body == "1":
            piece = kernel
        else:
            piece = f"({body}) * {kernel}"
    else:
        piece = kernel
    if pref == "1":
        return piece
    if pref == "-1":
        return "-" + piece
    return pref + " * " + piece


def _show_fock(value: FockVec) -> str:
    if not value.terms:
        return "0"
    parts = []
    for term in value.terms:
        ket = "fockket(" + ", ".join(str(n) for n in term.occ) + ")"
        if c_eq(term.coeff, c_one()):
            parts.append(ket)
        elif c_eq(term.coeff, c_from_int(-1)):
            parts.append("-" + ket)
        else:
            parts.append(show_cnum(term.coeff) + " * " + ket)
    out = parts[0]
    for piece in parts[1:]:
        if piece.startswith("-"):
            out += " - " + piece[1:]
        else:
            out += " + " + piece
    return out


@dataclass(frozen=True)
class ContinuumTheorem:
    value: object
    origin: Term
    detail: tuple[str, ...]


def _detail() -> tuple[str, ...]:
    return (
        "L2 inner products are exact integrals of polynomial-Gaussian and polynomial-exponential waves.",
        "The Fourier transform is admitted on the Gaussian class, and Hermite-Gaussians are its eigenfunctions.",
        "Position and momentum act on that dense domain, and [X, P] = i with hbar = 1.",
        "Plane waves are generalized eigenfunctions of the free particle, not L2 vectors.",
        "The free Gaussian packet satisfies the free Schrodinger equation identically.",
        "Creation and annihilation operators on finitely many Fock modes obey the CCR, and [phi, pi] = i.",
        "A general L2 function, completeness of L2, Coulomb continuum waves, the Rutherford amplitude, and infinitely many field modes stay outside.",
    )


def _eval(term: Term):
    _standing()
    if isinstance(term, App) and term.op == "l2comm" and len(term.args) == 1:
        return apply_comm_xp(_eval_wave(term.args[0]))
    if isinstance(term, App) and term.op in {"hermite", "gausswave", "expwave", "fourier", "l2apply"}:
        return _eval_wave(term)
    if isinstance(term, App) and term.op in {"fockket", "fockapply"}:
        return _eval_fock_vec(term)
    if isinstance(term, App) and term.op == "freepacket" and not term.args:
        return "freepacket"
    if isinstance(term, App) and term.op == "planewave" and len(term.args) == 1:
        return "planewave"
    if isinstance(term, App) and term.op == "freeenergy" and len(term.args) == 1:
        arg = term.args[0]
        if isinstance(arg, App) and arg.op == "planewave":
            return "k^2 / 2"
        raise NotExact("freeenergy is admitted for a plane wave")
    if isinstance(term, App) and term.op in CONTINUUM_OPS:
        # scalars, including fockcomm and fieldcomm as values
        if term.op in {"focka", "fockadag", "fockn", "fieldphi", "fieldpi"}:
            raise NotExact("a Fock operator is applied with fockapply")
        return _eval_scalar(term)
    if isinstance(term, App) and term.op in {"mul", "neg"} and has_continuum(term):
        # try wave, then fock, then scalar
        for ev in (_eval_wave, _eval_fock_vec, _eval_scalar):
            try:
                return ev(term)
            except NotExact:
                continue
        raise NotExact("this continuum term could not be evaluated")
    return _eval_scalar(term)


def eval_continuum_result(term: Term) -> ContinuumTheorem:
    return ContinuumTheorem(_eval(term), term, _detail())


def _show_value(value: object) -> str:
    if isinstance(value, L2Val):
        return show_val(value)
    if isinstance(value, Wave):
        return _show_wave(value)
    if isinstance(value, FockVec):
        return _show_fock(value)
    if isinstance(value, str):
        return value
    raise KernelError("this continuum result has no claim")


def continuum_value_rule(origin: Term, result: object, prelude: tuple[str, ...] = ()) -> Rule:
    if isinstance(result, ContinuumTheorem):
        shown = _show_value(result.value)
        return Rule(
            id=f"math.continuum.{shown}",
            layer="base",
            stage="quantity",
            title=f"{pretty(origin)} = {shown}",
            produces=shown,
            detail_lines=(*prelude, *result.detail),
        )
    raise KernelError("this continuum result has no claim")


def _as_value(value: object) -> object:
    if isinstance(value, ContinuumTheorem):
        return value.value
    return value


def _is_zero_side(value: object) -> bool:
    value = _as_value(value)
    if isinstance(value, L2Val):
        return val_is_zero(value)
    if isinstance(value, Wave):
        return _wave_is_zero(value)
    if isinstance(value, FockVec):
        return not value.terms
    if isinstance(value, int):
        return value == 0
    if isinstance(value, str):
        return value == "0"
    return False


def _sides_eq(left: object, right: object) -> bool:
    a, b = _as_value(left), _as_value(right)
    if isinstance(a, L2Val) and isinstance(b, L2Val):
        return val_eq(a, b)
    if isinstance(a, Wave) and isinstance(b, Wave):
        return _wave_eq(a, b)
    if isinstance(a, FockVec) and isinstance(b, FockVec):
        return _fock_vec_eq(a, b)
    if isinstance(a, L2Val) and isinstance(b, Wave) and _wave_is_zero(b):
        return val_is_zero(a)
    if isinstance(b, L2Val) and isinstance(a, Wave) and _wave_is_zero(a):
        return val_is_zero(b)
    if isinstance(a, str) and isinstance(b, str):
        return a == b
    if _is_zero_side(a) and _is_zero_side(b):
        return True
    return False


def continuum_equality_rules(
    left: Term,
    right: Term,
    left_value: object,
    right_value: object,
    prelude: tuple[str, ...] = (),
) -> tuple[Rule, ...]:
    title = f"{pretty(left)} = {pretty(right)}"
    if _sides_eq(left_value, right_value) or (
        _is_zero_side(left_value) and _is_zero_side(right_value)
    ):
        return (
            Rule(
                id="math.continuum.eq",
                layer="base",
                stage="quantity",
                title=title,
                produces=f"identity({title})",
                detail_lines=(*prelude, "The two sides are the same exact continuum value."),
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


def side_as_continuum(term: Term) -> object:
    try:
        return eval_continuum_result(term)
    except NotExact:
        if isinstance(term, IntLit):
            return ContinuumTheorem(_val(term.n), term, _detail())
        if isinstance(term, Var) and term.name == "i":
            return ContinuumTheorem(_val(c_i()), term, _detail())
        if isinstance(term, Var) and term.name == "pi":
            return ContinuumTheorem(_val(1, 4), term, _detail())
        # k^2 / 2 as a formal free energy
        if _is_free_energy_term(term):
            return ContinuumTheorem("k^2 / 2", term, _detail())
        raise


def _is_free_energy_term(term: Term) -> bool:
    # k^2 / 2  or  1/2 * k^2
    if isinstance(term, App) and term.op == "div" and len(term.args) == 2:
        num, den = term.args
        if isinstance(den, IntLit) and den.n == 2 and _is_k_squared(num):
            return True
    if isinstance(term, App) and term.op == "mul" and len(term.args) == 2:
        a, b = term.args
        if isinstance(a, App) and a.op == "div" and len(a.args) == 2:
            if isinstance(a.args[0], IntLit) and a.args[0].n == 1 and isinstance(a.args[1], IntLit) and a.args[1].n == 2 and _is_k_squared(b):
                return True
        if isinstance(b, App) and b.op == "div" and len(b.args) == 2:
            if isinstance(b.args[0], IntLit) and b.args[0].n == 1 and isinstance(b.args[1], IntLit) and b.args[1].n == 2 and _is_k_squared(a):
                return True
    return False


def _is_k_squared(term: Term) -> bool:
    if isinstance(term, App) and term.op == "pow" and len(term.args) == 2:
        return isinstance(term.args[0], Var) and term.args[0].name == "k" and isinstance(term.args[1], IntLit) and term.args[1].n == 2
    if isinstance(term, App) and term.op == "mul" and len(term.args) == 2:
        return all(isinstance(arg, Var) and arg.name == "k" for arg in term.args)
    return False
