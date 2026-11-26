"""Ricci = 0 for the Kerr metric, checked exactly in rational coordinates.

The Boyer–Lindquist chart is rewritten with x = cos(theta), so the metric
is a rational function of (r, x, m, a). The denominators

    Sigma = r^2 + a^2 x^2,
    Delta = r^2 - 2 m r + a^2,
    Xi    = 1 - x^2

are kept as named factors and reduced by exact polynomial division against
those definitions. Christoffel symbols, the Riemann tensor, and the Ricci
tensor are computed in this ring. An inverse is kept only when both products
are the identity. The Ricci tensor vanishes identically, so the Einstein
tensor vanishes as well.

Certificates are identities, checked exactly, with no approximation. The
generic Levi-Civita path is not used, and the polynomial degree and term
limits are not raised.
"""

from __future__ import annotations

from dataclasses import dataclass

from pgi.math.kernel import KernelError, NotExact
from pgi.math.poly import (
    MPoly,
    _align,
    _embed,
    _try_div,
    const_poly,
    mpoly_add,
    mpoly_diff,
    mpoly_eq,
    mpoly_mul,
    mpoly_neg,
    mpoly_pow,
    mpoly_smul,
    mpoly_sub,
    var_poly,
    zero_poly,
)
from pgi.math.rational import Ratio, rat_normalize


_ZERO = Ratio(0, 1)
_ONE = Ratio(1, 1)
_TWO = Ratio(2, 1)
_HALF = Ratio(1, 2)
_NAMES = ("r", "x", "m", "a")
# Coordinate order for the x-chart: t, r, x, phi.
_T, _R, _X, _PHI = 0, 1, 2, 3


def _q(n: int, d: int = 1) -> Ratio:
    return rat_normalize(n, d).value


def _c(value: int | Ratio) -> MPoly:
    ratio = value if isinstance(value, Ratio) else Ratio(value, 1)
    return const_poly(ratio, _NAMES)


def _v(name: str) -> MPoly:
    return var_poly(name, _NAMES)


def _sigma_poly() -> MPoly:
    # r^2 + a^2 x^2
    r, a, x = _v("r"), _v("a"), _v("x")
    return mpoly_add(mpoly_pow(r, 2), mpoly_mul(mpoly_pow(a, 2), mpoly_pow(x, 2)))


def _delta_poly() -> MPoly:
    # r^2 - 2 m r + a^2
    r, m, a = _v("r"), _v("m"), _v("a")
    return mpoly_add(mpoly_sub(mpoly_pow(r, 2), mpoly_mul(_c(2), mpoly_mul(m, r))), mpoly_pow(a, 2))


def _xi_poly() -> MPoly:
    # 1 - x^2
    return mpoly_sub(_c(1), mpoly_pow(_v("x"), 2))


_SIGMA = _sigma_poly()
_DELTA = _delta_poly()
_XI = _xi_poly()


def _try_div_any(left: MPoly, right: MPoly) -> MPoly | None:
    """Exact division, trying each variable as the main one if needed."""
    left, right = _align(left, right)
    if left.is_zero:
        return zero_poly(left.names)
    direct = _try_div(left, right)
    if direct is not None and mpoly_eq(mpoly_mul(direct, right), left):
        return direct
    names = left.names
    for i, _name in enumerate(names):
        rotated = names[i + 1 :] + names[: i + 1]
        a = _embed(left, rotated)
        b = _embed(right, rotated)
        quot = _try_div(a, b)
        if quot is None:
            continue
        quot = _embed(quot, names)
        if mpoly_eq(mpoly_mul(quot, right), left):
            return quot
    return None


@dataclass(frozen=True)
class KerrRat:
    """A rational function num / (Sigma^sig * Delta^delta * Xi^xi)."""

    num: MPoly
    sig: int
    delta: int
    xi: int

    def __post_init__(self) -> None:
        if self.num.names != _NAMES and not self.num.is_zero:
            object.__setattr__(self, "num", _embed(self.num, _NAMES))


def _kr(num: MPoly | int | Ratio, sig: int = 0, delta: int = 0, xi: int = 0) -> KerrRat:
    if isinstance(num, int):
        num = _c(num)
    elif isinstance(num, Ratio):
        num = _c(num)
    return _reduce(KerrRat(num, sig, delta, xi))


def _reduce(value: KerrRat) -> KerrRat:
    num, sig, delta, xi = value.num, value.sig, value.delta, value.xi
    if num.is_zero:
        return KerrRat(zero_poly(_NAMES), 0, 0, 0)
    changed = True
    guard = 0
    while changed and guard < 64:
        changed = False
        guard += 1
        quot = _try_div_any(num, _SIGMA)
        if quot is not None:
            num, sig, changed = quot, sig - 1, True
            continue
        quot = _try_div_any(num, _DELTA)
        if quot is not None:
            num, delta, changed = quot, delta - 1, True
            continue
        quot = _try_div_any(num, _XI)
        if quot is not None:
            num, xi, changed = quot, xi - 1, True
            continue
    return KerrRat(num, sig, delta, xi)


def _mul_named(num: MPoly, sig: int, delta: int, xi: int) -> MPoly:
    """Multiply num by Sigma^sig Delta^delta Xi^xi, with nonnegative exponents."""
    if sig < 0 or delta < 0 or xi < 0:
        raise KernelError("named-denominator expansion needs nonnegative exponents")
    if sig:
        num = mpoly_mul(num, mpoly_pow(_SIGMA, sig))
    if delta:
        num = mpoly_mul(num, mpoly_pow(_DELTA, delta))
    if xi:
        num = mpoly_mul(num, mpoly_pow(_XI, xi))
    return num


def kr_add(left: KerrRat, right: KerrRat) -> KerrRat:
    sig = max(left.sig, right.sig)
    delta = max(left.delta, right.delta)
    xi = max(left.xi, right.xi)
    ln = _mul_named(left.num, sig - left.sig, delta - left.delta, xi - left.xi)
    rn = _mul_named(right.num, sig - right.sig, delta - right.delta, xi - right.xi)
    return _reduce(KerrRat(mpoly_add(ln, rn), sig, delta, xi))


def kr_sub(left: KerrRat, right: KerrRat) -> KerrRat:
    return kr_add(left, kr_neg(right))


def kr_neg(value: KerrRat) -> KerrRat:
    return KerrRat(mpoly_neg(value.num), value.sig, value.delta, value.xi)


def kr_mul(left: KerrRat, right: KerrRat) -> KerrRat:
    return _reduce(KerrRat(mpoly_mul(left.num, right.num), left.sig + right.sig, left.delta + right.delta, left.xi + right.xi))


def kr_smul(value: KerrRat, scalar: Ratio) -> KerrRat:
    return _reduce(KerrRat(mpoly_smul(scalar, value.num), value.sig, value.delta, value.xi))


def kr_div(left: KerrRat, right: KerrRat) -> KerrRat:
    if kr_is_zero(right):
        raise NotExact("division by zero")
    # left/right = (nL / denL) * (denR / nR) = nL * denR_named / (nR * denL_named)
    # Move right.num into the denominator by exact division if possible later;
    # represent as num = nL, and increment exponents by right's, then divide num by right.num.
    quot = _try_div_any(left.num, right.num)
    if quot is not None:
        return _reduce(KerrRat(quot, left.sig - right.sig, left.delta - right.delta, left.xi - right.xi))
    # Otherwise invert the right numerator by keeping it as a polynomial in the
    # denominator: not representable unless we add a fourth named factor.
    # For Kerr, every denominator that arises is a product of Sigma, Delta, Xi
    # and a polynomial that divides the numerator after clearing.
    raise NotExact("this Kerr rational is not in the Sigma-Delta-Xi ring")


def kr_is_zero(value: KerrRat) -> bool:
    return _reduce(value).num.is_zero


def kr_eq(left: KerrRat, right: KerrRat) -> bool:
    return kr_is_zero(kr_sub(left, right))


def kr_diff(value: KerrRat, name: str) -> KerrRat:
    if name not in {"r", "x"}:
        return _kr(0)
    n_d = mpoly_diff(value.num, name)
    total = KerrRat(n_d, value.sig, value.delta, value.xi)
    if name == "r":
        dsigma = _kr(mpoly_smul(_TWO, _v("r")))  # 2r
        ddelta = _kr(mpoly_smul(_TWO, mpoly_sub(_v("r"), _v("m"))))  # 2(r-m)
        dxi = _kr(0)
    else:
        dsigma = _kr(mpoly_mul(_c(2), mpoly_mul(mpoly_pow(_v("a"), 2), _v("x"))))  # 2 a^2 x
        ddelta = _kr(0)
        dxi = _kr(mpoly_smul(Ratio(-2, 1), _v("x")))  # -2x
    if value.sig:
        # -s N (dSigma) / (Sigma^{s+1} ...)
        term = kr_mul(_kr(mpoly_smul(_q(-value.sig), value.num), value.sig + 1, value.delta, value.xi), dsigma)
        total = kr_add(total, term)
    if value.delta:
        term = kr_mul(_kr(mpoly_smul(_q(-value.delta), value.num), value.sig, value.delta + 1, value.xi), ddelta)
        total = kr_add(total, term)
    if value.xi:
        term = kr_mul(_kr(mpoly_smul(_q(-value.xi), value.num), value.sig, value.delta, value.xi + 1), dxi)
        total = kr_add(total, term)
    return _reduce(total)


def _show_kr(value: KerrRat) -> str:
    value = _reduce(value)
    if value.num.is_zero:
        return "0"
    from pgi.math.poly import show_poly

    num = show_poly(value.num)
    dens = []
    nums = []
    for name, exp in (("Sigma", value.sig), ("Delta", value.delta), ("Xi", value.xi)):
        if exp > 0:
            dens.append(name if exp == 1 else f"{name}^{exp}")
        elif exp < 0:
            e = -exp
            nums.append(name if e == 1 else f"{name}^{e}")
    if nums:
        num = "(" + num + ")*" + "*".join(nums) if num != "1" else "*".join(nums)
    if dens:
        return "(" + num + ")/(" + "*".join(dens) + ")"
    return num


# ---- metric and inverse ---------------------------------------------------

def _metric() -> list[list[KerrRat]]:
    """Kerr metric in (t, r, x, phi), x = cos(theta)."""
    z = _kr(0)
    r = _v("r")
    m = _v("m")
    a = _v("a")
    two_m_r = mpoly_mul(_c(2), mpoly_mul(m, r))
    # g_tt = -(Sigma - 2 m r) / Sigma
    g_tt = _kr(mpoly_neg(mpoly_sub(_SIGMA, two_m_r)), 1, 0, 0)
    # g_tphi = -2 m r a Xi / Sigma
    g_tp = _kr(mpoly_neg(mpoly_mul(mpoly_mul(two_m_r, a), _XI)), 1, 0, 0)
    # g_rr = Sigma / Delta
    g_rr = _kr(_SIGMA, 0, 1, 0)
    # g_xx = Sigma / Xi
    g_xx = _kr(_SIGMA, 0, 0, 1)
    # A = (r^2+a^2)^2 - Delta a^2 Xi
    r2 = mpoly_pow(r, 2)
    a2 = mpoly_pow(a, 2)
    r2_a2 = mpoly_add(r2, a2)
    big_a = mpoly_sub(mpoly_pow(r2_a2, 2), mpoly_mul(mpoly_mul(_DELTA, a2), _XI))
    # g_phiphi = A * Xi / Sigma
    g_pp = _kr(mpoly_mul(big_a, _XI), 1, 0, 0)
    g = [
        [g_tt, z, z, g_tp],
        [z, g_rr, z, z],
        [z, z, g_xx, z],
        [g_tp, z, z, g_pp],
    ]
    return g


def _inverse() -> list[list[KerrRat]]:
    z = _kr(0)
    r = _v("r")
    m = _v("m")
    a = _v("a")
    two_m_r = mpoly_mul(_c(2), mpoly_mul(m, r))
    r2 = mpoly_pow(r, 2)
    a2 = mpoly_pow(a, 2)
    r2_a2 = mpoly_add(r2, a2)
    big_a = mpoly_sub(mpoly_pow(r2_a2, 2), mpoly_mul(mpoly_mul(_DELTA, a2), _XI))
    # g^{tt} = -A / (Sigma Delta)
    gi_tt = _kr(mpoly_neg(big_a), 1, 1, 0)
    # g^{tphi} = -2 m r a / (Sigma Delta)
    gi_tp = _kr(mpoly_neg(mpoly_mul(two_m_r, a)), 1, 1, 0)
    # g^{rr} = Delta / Sigma
    gi_rr = _kr(_DELTA, 1, 0, 0)
    # g^{xx} = Xi / Sigma
    gi_xx = _kr(_XI, 1, 0, 0)
    # g^{phiphi} = (Delta - a^2 Xi) / (Sigma Delta Xi)
    gi_pp = _kr(mpoly_sub(_DELTA, mpoly_mul(a2, _XI)), 1, 1, 1)
    return [
        [gi_tt, z, z, gi_tp],
        [z, gi_rr, z, z],
        [z, z, gi_xx, z],
        [gi_tp, z, z, gi_pp],
    ]


def _matmul(left, right) -> list[list[KerrRat]]:
    n = 4
    z = _kr(0)
    out = [[z for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(n):
            total = z
            for k in range(n):
                if kr_is_zero(left[i][k]) or kr_is_zero(right[k][j]):
                    continue
                total = kr_add(total, kr_mul(left[i][k], right[k][j]))
            out[i][j] = total
    return out


def _is_identity(mat) -> bool:
    for i in range(4):
        for j in range(4):
            if i == j:
                if not kr_eq(mat[i][j], _kr(1)):
                    return False
            else:
                if not kr_is_zero(mat[i][j]):
                    return False
    return True


def _check_inverse(g, gi) -> None:
    if not _is_identity(_matmul(g, gi)) or not _is_identity(_matmul(gi, g)):
        raise KernelError("the Kerr inverse in x = cos(theta) did not multiply back to the identity")


def _christoffel(g, gi) -> list[list[list[KerrRat]]]:
    """Gamma^lam_{mu nu}."""
    z = _kr(0)
    coord = {0: "t", 1: "r", 2: "x", 3: "phi"}
    # derivatives of g
    dg = [[[z for _ in range(4)] for _ in range(4)] for _ in range(4)]
    for mu in range(4):
        name = coord[mu]
        for i in range(4):
            for j in range(4):
                if kr_is_zero(g[i][j]):
                    continue
                dg[mu][i][j] = kr_diff(g[i][j], name)
    gamma = [[[z for _ in range(4)] for _ in range(4)] for _ in range(4)]
    for lam in range(4):
        for mu in range(4):
            for nu in range(mu, 4):
                total = z
                for sig in range(4):
                    if kr_is_zero(gi[lam][sig]):
                        continue
                    # d_mu g_nu sig + d_nu g_mu sig - d_sig g_mu nu
                    piece = kr_sub(kr_add(dg[mu][nu][sig], dg[nu][mu][sig]), dg[sig][mu][nu])
                    if kr_is_zero(piece):
                        continue
                    total = kr_add(total, kr_mul(gi[lam][sig], piece))
                total = kr_smul(total, _HALF)
                gamma[lam][mu][nu] = total
                gamma[lam][nu][mu] = total
    return gamma


def _ricci_from(gamma) -> list[list[KerrRat]]:
    z = _kr(0)
    coord = {0: "t", 1: "r", 2: "x", 3: "phi"}
    # d_mu Gamma^rho_{nu sig}
    dgamma = [[[[z for _ in range(4)] for _ in range(4)] for _ in range(4)] for _ in range(4)]
    for mu in range(4):
        name = coord[mu]
        for rho in range(4):
            for nu in range(4):
                for sig in range(4):
                    if kr_is_zero(gamma[rho][nu][sig]):
                        continue
                    dgamma[mu][rho][nu][sig] = kr_diff(gamma[rho][nu][sig], name)
    ric = [[z for _ in range(4)] for _ in range(4)]
    for sig in range(4):
        for nu in range(sig, 4):  # Ricci is symmetric; compute upper triangle
            total = z
            for rho in range(4):
                # R^rho_{sig rho nu} = d_rho Gamma^rho_{nu sig} - d_nu Gamma^rho_{rho sig}
                #                   + Gamma^rho_{rho lam} Gamma^lam_{nu sig}
                #                   - Gamma^rho_{nu lam} Gamma^lam_{rho sig}
                term = kr_sub(dgamma[rho][rho][nu][sig], dgamma[nu][rho][rho][sig])
                for lam in range(4):
                    if not kr_is_zero(gamma[rho][rho][lam]) and not kr_is_zero(gamma[lam][nu][sig]):
                        term = kr_add(term, kr_mul(gamma[rho][rho][lam], gamma[lam][nu][sig]))
                    if not kr_is_zero(gamma[rho][nu][lam]) and not kr_is_zero(gamma[lam][rho][sig]):
                        term = kr_sub(term, kr_mul(gamma[rho][nu][lam], gamma[lam][rho][sig]))
                total = kr_add(total, term)
            ric[sig][nu] = total
            ric[nu][sig] = total
    return ric


_KERR_RICCI_OK = False
_KERR_INVERSE_X_OK = False


def _check_kerr_ricci_vanishes() -> None:
    global _KERR_RICCI_OK, _KERR_INVERSE_X_OK
    if _KERR_RICCI_OK:
        return
    g = _metric()
    gi = _inverse()
    _check_inverse(g, gi)
    _KERR_INVERSE_X_OK = True
    ric = _ricci_from(_christoffel(g, gi))
    for i in range(4):
        for j in range(4):
            if not kr_is_zero(ric[i][j]):
                raise KernelError(
                    f"the Ricci tensor of Kerr in x = cos(theta) did not vanish at ({i}, {j}): {_show_kr(ric[i][j])}"
                )
    _KERR_RICCI_OK = True


def kerr_ricci_zero_metric(names: tuple[str, ...]):
    """A zero (0,2) tensor on the given chart, after Ricci = 0 is checked."""
    from pgi.math.metric import Metric, _field_embed
    from pgi.math.rational import Ratio
    from pgi.math.trans import const_fexpr

    _check_kerr_ricci_vanishes()
    zero = const_fexpr(Ratio(0, 1), ())
    rows = tuple(tuple(_field_embed(zero, names) for _ in names) for _ in names)
    return Metric(names, rows)
