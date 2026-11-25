"""Resultants, number-field arithmetic, and polynomials with algebraic coefficients.

A polynomial whose coefficients lie in a real algebraic field is reduced to a
rational polynomial by a resultant (the norm, or an eliminant that is a
multiple of the norm). Sturm isolation lists the candidate real roots. A
candidate is kept only when an exact check shows it vanishes in the original
polynomial. Isolating intervals are refined until every sign in the chart is
certain.

This module does not import Lean, Isabelle, or Octave.
"""

from __future__ import annotations

from math import comb, gcd, isqrt
from typing import Iterable

from pgi.math.algebraic import (
    AlgebraicReal,
    Poly,
    RatPoly,
    _divmod_rat,
    _mul_int,
    _q,
    _qadd,
    _qcmp,
    _qdiv,
    _qmul,
    _qneg,
    _qsub,
    _refine,
    _sign_of,
    _to_rat,
    _trim_int,
    cauchy_bound,
    degree,
    eval_int,
    extract_rational_roots,
    factor_square_free,
    from_ratio_coeffs,
    integer_poly,
    isolate_all,
    isolate_interval,
    leading,
    linear_factor,
    primitive,
    real_root_count,
    show_algebraic,
    show_poly,
    square_free_factors,
    sturm_count,
)
from pgi.math.kernel import KernelError, NotExact
from pgi.math.rational import Ratio

_ZERO = Ratio(0, 1)
_ONE = Ratio(1, 1)

# Resultants and norms may be of higher degree than a single minpoly.
ALGEBRA_DEGREE_LIMIT = 64

Alg = Ratio | AlgebraicReal


def _trim_rat(poly: RatPoly) -> RatPoly:
    items = list(poly)
    while len(items) > 1 and items[-1].num == 0:
        items.pop()
    if not items:
        return (_ZERO,)
    return tuple(items)


def _deg_rat(poly: RatPoly) -> int:
    poly = _trim_rat(poly)
    if poly == (_ZERO,):
        return -1
    return len(poly) - 1


def _add_int(left: Poly, right: Poly) -> Poly:
    size = max(len(left), len(right))
    return _trim_int(
        (left[i] if i < len(left) else 0) + (right[i] if i < len(right) else 0) for i in range(size)
    )


def _scale_int(poly: Poly, factor: int) -> Poly:
    if factor == 0 or poly == (0,):
        return (0,)
    return _trim_int(coeff * factor for coeff in poly)


def _shift_x(poly: Poly, power: int) -> Poly:
    if poly == (0,) or power == 0:
        return poly
    return _trim_int((0,) * power + tuple(poly))


def _add_rat(left: RatPoly, right: RatPoly) -> RatPoly:
    size = max(len(left), len(right))
    return _trim_rat(
        tuple(
            _qadd(left[i] if i < len(left) else _ZERO, right[i] if i < len(right) else _ZERO)
            for i in range(size)
        )
    )


def _sub_rat(left: RatPoly, right: RatPoly) -> RatPoly:
    return _add_rat(left, tuple(_qneg(coeff) for coeff in right))


def _neg_rat(poly: RatPoly) -> RatPoly:
    return tuple(_qneg(coeff) for coeff in poly)


def _mul_rat(left: RatPoly, right: RatPoly) -> RatPoly:
    if left == (_ZERO,) or right == (_ZERO,):
        return (_ZERO,)
    acc = [_ZERO] * (len(left) + len(right) - 1)
    for i, a in enumerate(left):
        if a.num == 0:
            continue
        for j, b in enumerate(right):
            acc[i + j] = _qadd(acc[i + j], _qmul(a, b))
    return _trim_rat(tuple(acc))


def _pow_int(poly: Poly, exponent: int) -> Poly:
    if exponent < 0:
        raise KernelError("a negative polynomial power stays outside")
    if exponent == 0:
        return (1,)
    acc = (1,)
    base = poly
    while exponent:
        if exponent & 1:
            acc = _mul_int(acc, base)
        exponent >>= 1
        if exponent:
            base = _mul_int(base, base)
    return acc


# --- Univariate resultant over Q ---


def resultant(f: Poly, g: Poly) -> int:
    """Resultant of two integer polynomials."""

    value = _resultant_rat(_to_rat(f), _to_rat(g))
    if value.den != 1:
        # Clear by returning the integer resultant of a primitive pair, scaled.
        raise KernelError("a resultant over the integers was not integral")
    return value.num


def _resultant_rat(f: RatPoly, g: RatPoly) -> Ratio:
    f = _trim_rat(f)
    g = _trim_rat(g)
    if f == (_ZERO,) or g == (_ZERO,):
        return _ZERO
    sign = 1
    acc = _ONE
    while True:
        dg = _deg_rat(g)
        df = _deg_rat(f)
        if dg < 0:
            return _ZERO
        if dg == 0:
            power = _ONE
            for _ in range(df):
                power = _qmul(power, g[0])
            return _qmul(acc, _qmul(_q(sign, 1), power))
        if df < dg:
            if (df * dg) % 2:
                sign = -sign
            f, g = g, f
            continue
        _, rem = _divmod_rat(f, g)
        rem = _trim_rat(rem)
        if rem == (_ZERO,):
            return _ZERO
        dr = _deg_rat(rem)
        if (df * dg) % 2:
            sign = -sign
        factor = _ONE
        lead = g[-1]
        for _ in range(df - dr):
            factor = _qmul(factor, lead)
        acc = _qmul(acc, factor)
        f, g = g, rem


# --- Polynomials in y with coefficients in Z[x] ---

ByX = tuple[Poly, ...]


def _trim_byx(poly: ByX) -> ByX:
    items = list(poly)
    while len(items) > 1 and items[-1] == (0,):
        items.pop()
    if not items:
        return ((0,),)
    return tuple(items)


def _shift_minus_y(poly: Poly) -> ByX:
    """m(x - y) as a polynomial in y, with coefficients in Z[x]."""

    acc: list[Poly] = [(0,)]
    for power, coeff in enumerate(poly):
        if coeff == 0:
            continue
        for index in range(power + 1):
            term = _scale_int(_shift_x((1,), power - index), coeff * comb(power, index) * ((-1) ** index))
            while len(acc) <= index:
                acc.append((0,))
            acc[index] = _add_int(acc[index], term)
    return tuple(acc)


def _const_in_x(poly: Poly) -> ByX:
    return tuple((coeff,) for coeff in poly)


def _linear_resultant(f: ByX, g: ByX) -> RatPoly:
    """g = d + c y. Res_y(f, g) = sum_j f_j (-d)^j c^{deg f - j}."""

    intercept, slope = g[0], g[1]
    top = len(f) - 1
    total: RatPoly = (_ZERO,)
    minus_d = _scale_int(intercept, -1)
    power_d = (1,)
    # c^{top-j} computed downward
    powers_c = [(1,)]
    for _ in range(top):
        powers_c.append(_mul_int(powers_c[-1], slope))
    for index, coeff in enumerate(f):
        term = _mul_int(_mul_int(coeff, power_d), powers_c[top - index])
        total = _add_rat(total, _to_rat(term))
        power_d = _mul_int(power_d, minus_d)
    return _trim_rat(total)


def _sylvester_resultant(f: ByX, g: ByX) -> RatPoly:
    """Bareiss determinant of the Sylvester matrix over Q[x]."""

    df = len(f) - 1
    dg = len(g) - 1
    size = df + dg
    if size == 0:
        return (_ONE,)
    zero = (_ZERO,)
    f_r = tuple(_to_rat(coeff) for coeff in f)
    g_r = tuple(_to_rat(coeff) for coeff in g)
    matrix = [[zero for _ in range(size)] for _ in range(size)]
    for row in range(dg):
        for col, coeff in enumerate(f_r):
            if row + col < size:
                matrix[row][row + col] = coeff
    for row in range(df):
        for col, coeff in enumerate(g_r):
            if row + col < size:
                matrix[dg + row][row + col] = coeff
    sign = 1
    denom = (_ONE,)
    for pivot_index in range(size):
        pivot_row = None
        for row in range(pivot_index, size):
            if matrix[row][pivot_index] != (_ZERO,):
                pivot_row = row
                break
        if pivot_row is None:
            return (_ZERO,)
        if pivot_row != pivot_index:
            matrix[pivot_index], matrix[pivot_row] = matrix[pivot_row], matrix[pivot_index]
            sign = -sign
        pivot = matrix[pivot_index][pivot_index]
        for row in range(pivot_index + 1, size):
            for col in range(pivot_index + 1, size):
                numerator = _sub_rat(
                    _mul_rat(pivot, matrix[row][col]),
                    _mul_rat(matrix[row][pivot_index], matrix[pivot_index][col]),
                )
                if pivot_index == 0:
                    matrix[row][col] = numerator
                else:
                    quot, rem = _divmod_rat(numerator, denom)
                    if rem != (_ZERO,):
                        raise KernelError("Bareiss division was not exact")
                    matrix[row][col] = quot
            matrix[row][pivot_index] = (_ZERO,)
        denom = pivot
    det = matrix[size - 1][size - 1]
    if sign < 0:
        det = _neg_rat(det)
    return _trim_rat(det)


def resultant_in_y(f: ByX, g: ByX) -> RatPoly:
    f = _trim_byx(f)
    g = _trim_byx(g)
    if f == ((0,),) or g == ((0,),):
        return (_ZERO,)
    if len(f) == 2 and len(g) != 2:
        f, g = g, f
    if len(g) == 2:
        return _linear_resultant(f, g)
    return _sylvester_resultant(f, g)


def vanishing_poly_sum(left: Poly, right: Poly) -> Poly:
    """A polynomial that vanishes at α + β when left(α) = right(β) = 0."""

    if degree(left) * degree(right) > ALGEBRA_DEGREE_LIMIT:
        raise NotExact("this algebraic number stays outside")
    result = resultant_in_y(_shift_minus_y(left), _const_in_x(right))
    if result == (_ZERO,):
        raise NotExact("this algebraic sum stays outside")
    poly = from_ratio_coeffs(result)
    if degree(poly) > ALGEBRA_DEGREE_LIMIT:
        raise NotExact("this algebraic number stays outside")
    return poly


def vanishing_poly_product(left: Poly, right: Poly) -> Poly:
    """A polynomial that vanishes at α β: Res_y(y^{deg right} right(x/y), left(y))."""

    # Build right_rev(y) = y^n right(x/y) as a polynomial in y with Z[x] coeffs.
    # right = sum b_k y^k, y^n right(x/y) = sum b_k x^k y^{n-k}.
    n = degree(right)
    if n < 0:
        return (0,)
    if degree(left) * n > ALGEBRA_DEGREE_LIMIT:
        raise NotExact("this algebraic number stays outside")
    acc: list[Poly] = [(0,)] * (n + 1)
    for index, coeff in enumerate(right):
        # term b_k x^k y^{n-k}
        power = n - index
        acc[power] = _add_int(acc[power], _scale_int(_shift_x((1,), index), coeff))
    result = resultant_in_y(_const_in_x(left), tuple(acc))
    if result == (_ZERO,):
        raise NotExact("this algebraic product stays outside")
    poly = from_ratio_coeffs(result)
    if degree(poly) > ALGEBRA_DEGREE_LIMIT:
        raise NotExact("this algebraic number stays outside")
    return poly


def vanishing_poly_power(poly: Poly, exponent: int) -> Poly:
    """A polynomial that vanishes at α^k: Res_y(poly(y), x - y^k)."""

    if exponent < 1:
        raise NotExact("this algebraic power stays outside")
    if exponent == 1:
        return primitive(poly)
    if exponent == 2 and all(poly[index] == 0 for index in range(1, len(poly), 2)):
        # p(y) = s(y^2), so p(α)=0 implies s(α^2)=0.
        return primitive(tuple(poly[::2]))
    # x - y^k as a polynomial in y: coeff of y^0 is (x,), of y^k is (-1,)
    in_y: list[Poly] = [(0,)] * (exponent + 1)
    in_y[0] = (0, 1)  # x
    in_y[exponent] = (-1,)
    result = resultant_in_y(_const_in_x(poly), tuple(in_y))
    if result == (_ZERO,):
        raise NotExact("this algebraic power stays outside")
    out = from_ratio_coeffs(result)
    if degree(out) > ALGEBRA_DEGREE_LIMIT:
        raise NotExact("this algebraic number stays outside")
    return out


def vanishing_poly_root(poly: Poly, exponent: int) -> Poly:
    """A polynomial that vanishes at a k-th root of α: Res_y(poly(y), x^k - y) = poly(x^k)."""

    if exponent < 1:
        raise NotExact("this algebraic root stays outside")
    if exponent == 1:
        return primitive(poly)
    # x^k - y: coeff of y^0 is x^k, of y^1 is -1. Linear in y.
    in_y = (_shift_x((1,), exponent), (-1,))
    result = resultant_in_y(_const_in_x(poly), in_y)
    if result == (_ZERO,):
        raise NotExact("this algebraic root stays outside")
    out = from_ratio_coeffs(result)
    if degree(out) > ALGEBRA_DEGREE_LIMIT:
        raise NotExact("this algebraic number stays outside")
    return out


def vanishing_poly_scale(poly: Poly, scale: Ratio) -> Poly:
    """A polynomial that vanishes at r α: r^{deg} poly(x/r)."""

    if scale.num == 0:
        return (0, 1)  # x, the minpoly of 0 is not used this way
    top = degree(poly)
    acc: list[Ratio] = []
    # coeff of x^k in r^{top} p(x/r) is p_k * r^{top-k}
    for index, coeff in enumerate(poly):
        power = top - index
        factor = _q(scale.num ** power, scale.den ** power)
        acc.append(_qmul(_q(coeff, 1), factor))
    return from_ratio_coeffs(acc)


def vanishing_poly_shift(poly: Poly, shift: Ratio) -> Poly:
    """A polynomial that vanishes at α + r: poly(x - r)."""

    # poly(x-r) = sum p_k (x-r)^k
    acc: RatPoly = (_ZERO,)
    for power, coeff in enumerate(poly):
        if coeff == 0:
            continue
        # (x-r)^k = sum_i comb(k,i) x^i (-r)^{k-i}
        term = [_ZERO] * (power + 1)
        for index in range(power + 1):
            factor = _q(comb(power, index), 1)
            # (-r)^{power-index}
            exp = power - index
            if exp == 0:
                scale = _ONE
            else:
                scale = _q(((-shift.num) ** exp), (shift.den ** exp))
            term[index] = _qmul(_qmul(_q(coeff, 1), factor), scale)
        acc = _add_rat(acc, tuple(term))
    return from_ratio_coeffs(acc)


# --- Isolation helpers ---


def refine_interval(poly: Poly, low: Ratio, high: Ratio, steps: int = 32, width: Ratio | None = None) -> tuple[Ratio, Ratio]:
    current_low, current_high = low, high
    limit = width if width is not None else _q(1, 16)
    for _ in range(max(0, steps)):
        if _qcmp(_qsub(current_high, current_low), limit) <= 0:
            break
        next_low, next_high = _refine(poly, current_low, current_high)
        if next_low == current_low and next_high == current_high:
            break
        current_low, current_high = next_low, next_high
    return current_low, current_high


def interval_of(number: Alg, steps: int = 24) -> tuple[Ratio, Ratio]:
    if isinstance(number, Ratio):
        return number, number
    low, high = number.interval
    return refine_interval(number.coeffs, low, high, steps)


def _interval_add(left: tuple[Ratio, Ratio], right: tuple[Ratio, Ratio]) -> tuple[Ratio, Ratio]:
    return _qadd(left[0], right[0]), _qadd(left[1], right[1])


def _interval_neg(bounds: tuple[Ratio, Ratio]) -> tuple[Ratio, Ratio]:
    return _qneg(bounds[1]), _qneg(bounds[0])


def _interval_mul(left: tuple[Ratio, Ratio], right: tuple[Ratio, Ratio]) -> tuple[Ratio, Ratio]:
    corners = (
        _qmul(left[0], right[0]),
        _qmul(left[0], right[1]),
        _qmul(left[1], right[0]),
        _qmul(left[1], right[1]),
    )
    low = corners[0]
    high = corners[0]
    for value in corners[1:]:
        if _qcmp(value, low) < 0:
            low = value
        if _qcmp(value, high) > 0:
            high = value
    return low, high


def _interval_overlap(left: tuple[Ratio, Ratio], right: tuple[Ratio, Ratio]) -> bool:
    return _qcmp(left[1], right[0]) > 0 and _qcmp(right[1], left[0]) > 0


# --- Factoring over Q ---


def _l2_bound(poly: Poly) -> int:
    total = 0
    for coeff in poly:
        total += coeff * coeff
    return isqrt(total) + 1


def _factor_coeff_bound(poly: Poly, factor_deg: int) -> int:
    # A generous Mignotte-style bound on factor coefficients.
    n = degree(poly)
    if factor_deg < 1 or factor_deg >= n:
        factor_deg = max(1, n // 2)
    return (isqrt(factor_deg + 1) + 1) * (1 << factor_deg) * _l2_bound(poly) * abs(leading(poly)) + 2


def _mod_trim(poly: list[int] | tuple[int, ...], prime: int) -> list[int]:
    items = [coeff % prime for coeff in poly]
    while len(items) > 1 and items[-1] == 0:
        items.pop()
    if not items:
        return [0]
    return items


def _mod_deg(poly: list[int], prime: int) -> int:
    items = _mod_trim(poly, prime)
    if items == [0]:
        return -1
    return len(items) - 1


def _mod_add(left: list[int], right: list[int], prime: int) -> list[int]:
    size = max(len(left), len(right))
    return _mod_trim(
        [
            (left[i] if i < len(left) else 0) + (right[i] if i < len(right) else 0)
            for i in range(size)
        ],
        prime,
    )


def _mod_sub(left: list[int], right: list[int], prime: int) -> list[int]:
    size = max(len(left), len(right))
    return _mod_trim(
        [
            (left[i] if i < len(left) else 0) - (right[i] if i < len(right) else 0)
            for i in range(size)
        ],
        prime,
    )


def _mod_mul(left: list[int], right: list[int], prime: int) -> list[int]:
    if _mod_deg(left, prime) < 0 or _mod_deg(right, prime) < 0:
        return [0]
    acc = [0] * (len(left) + len(right) - 1)
    for i, a in enumerate(left):
        if a % prime == 0:
            continue
        for j, b in enumerate(right):
            acc[i + j] = (acc[i + j] + a * b) % prime
    return _mod_trim(acc, prime)


def _mod_inv(value: int, prime: int) -> int:
    return pow(value % prime, prime - 2, prime)


def _mod_divmod(left: list[int], right: list[int], prime: int) -> tuple[list[int], list[int]]:
    right = _mod_trim(right, prime)
    if _mod_deg(right, prime) < 0:
        raise ZeroDivisionError
    rem = _mod_trim(left, prime)
    inv_lead = _mod_inv(right[-1], prime)
    quot = [0]
    while _mod_deg(rem, prime) >= _mod_deg(right, prime):
        shift = _mod_deg(rem, prime) - _mod_deg(right, prime)
        coeff = (rem[-1] * inv_lead) % prime
        if shift >= len(quot):
            quot.extend([0] * (shift - len(quot) + 1))
        quot[shift] = (quot[shift] + coeff) % prime
        if len(rem) < shift + len(right):
            rem.extend([0] * (shift + len(right) - len(rem)))
        for i, value in enumerate(right):
            rem[i + shift] = (rem[i + shift] - value * coeff) % prime
        rem = _mod_trim(rem, prime)
    return _mod_trim(quot, prime), rem


def _mod_gcd(left: list[int], right: list[int], prime: int) -> list[int]:
    a, b = _mod_trim(left, prime), _mod_trim(right, prime)
    while _mod_deg(b, prime) >= 0:
        _, rem = _mod_divmod(a, b, prime)
        a, b = b, rem
    if _mod_deg(a, prime) < 0:
        return [0]
    inv_lead = _mod_inv(a[-1], prime)
    return _mod_trim([coeff * inv_lead for coeff in a], prime)


def _mod_monic(poly: list[int], prime: int) -> list[int]:
    poly = _mod_trim(poly, prime)
    if _mod_deg(poly, prime) < 0:
        return poly
    inv_lead = _mod_inv(poly[-1], prime)
    return _mod_trim([coeff * inv_lead for coeff in poly], prime)


def _mod_pow(base: list[int], exponent: int, modulus: list[int], prime: int) -> list[int]:
    result = [1]
    current = _mod_trim(base, prime)
    power = exponent
    while power > 0:
        if power & 1:
            result = _mod_divmod(_mod_mul(result, current, prime), modulus, prime)[1]
        power >>= 1
        if power:
            current = _mod_divmod(_mod_mul(current, current, prime), modulus, prime)[1]
    return result


def _mod_deriv(poly: list[int], prime: int) -> list[int]:
    if len(poly) <= 1:
        return [0]
    return _mod_trim([index * coeff for index, coeff in enumerate(poly)][1:], prime)


def _lcg(seed: int):
    state = seed % 2147483647 or 1
    while True:
        state = (1103515245 * state + 12345) % 2147483648
        yield state


def _mod_random_poly(max_deg: int, prime: int, rng) -> list[int]:
    degree_here = 0 if max_deg < 1 else (next(rng) % max_deg)
    items = [next(rng) % prime for _ in range(degree_here + 1)]
    if items[-1] == 0:
        items[-1] = 1
    return _mod_trim(items, prime)


def _equal_degree_split(poly: list[int], factor_deg: int, prime: int, rng) -> list[list[int]]:
    """Cantor–Zassenhaus split of a product of equal-degree irreducibles, p odd."""

    poly = _mod_monic(poly, prime)
    top = _mod_deg(poly, prime)
    if top == factor_deg:
        return [poly]
    if top < factor_deg or top % factor_deg != 0:
        raise NotExact("this polynomial stays outside this rule")
    remaining = [poly]
    factors: list[list[int]] = []
    attempts = 0
    exponent = (pow(prime, factor_deg) - 1) // 2
    while remaining:
        current = remaining.pop()
        if _mod_deg(current, prime) == factor_deg:
            factors.append(_mod_monic(current, prime))
            continue
        split = None
        for _ in range(48):
            attempts += 1
            trial = _mod_random_poly(_mod_deg(current, prime) - 1, prime, rng)
            power = _mod_pow(trial, exponent, current, prime)
            gcd = _mod_gcd(_mod_sub(power, [1], prime), current, prime)
            gd = _mod_deg(gcd, prime)
            if 0 < gd < _mod_deg(current, prime):
                quot, rem = _mod_divmod(current, gcd, prime)
                if rem != [0]:
                    continue
                remaining.append(_mod_monic(gcd, prime))
                remaining.append(_mod_monic(quot, prime))
                split = True
                break
        if not split:
            raise NotExact("this polynomial stays outside this rule")
    return factors


def _ddf_and_split(poly: Poly, prime: int) -> list[list[int]] | None:
    """Complete irreducible factorization of a monic square-free poly over F_p, p odd.

    Returns None when p divides the leading coefficient or the reduction is not square-free.
    """

    if prime <= 2 or leading(poly) % prime == 0:
        return None
    reduced = _mod_monic(_mod_trim(poly, prime), prime)
    if _mod_deg(reduced, prime) < 1:
        return None
    if _mod_deg(_mod_gcd(reduced, _mod_deriv(reduced, prime), prime), prime) > 0:
        return None
    seed = prime + sum((index + 1) * abs(coeff) for index, coeff in enumerate(poly))
    rng = _lcg(seed)
    remaining = reduced
    x = [0, 1]
    frobenius = x[:]
    factors: list[list[int]] = []
    step = 0
    while _mod_deg(remaining, prime) >= 2 * (step + 1):
        step += 1
        frobenius = _mod_pow(frobenius, prime, remaining, prime)
        block = _mod_gcd(remaining, _mod_sub(frobenius, x, prime), prime)
        if _mod_deg(block, prime) > 0:
            factors.extend(_equal_degree_split(block, step, prime, rng))
            quot, rem = _mod_divmod(remaining, block, prime)
            if rem != [0]:
                raise KernelError("a modular distinct-degree quotient had a remainder")
            remaining = _mod_monic(quot, prime)
            frobenius = _mod_divmod(frobenius, remaining, prime)[1]
    if _mod_deg(remaining, prime) > 0:
        factors.append(_mod_monic(remaining, prime))
    return factors




def _center(value: int, modulus: int) -> int:
    residue = value % modulus
    if residue * 2 > modulus:
        residue -= modulus
    return residue


def _reduce_mod(poly: list[int] | Poly, modulus: int) -> list[int]:
    items = [_center(int(coeff), modulus) for coeff in poly]
    while len(items) > 1 and items[-1] == 0:
        items.pop()
    return items or [0]


def _poly_mul_int(left: list[int], right: list[int]) -> list[int]:
    if left == [0] or right == [0]:
        return [0]
    acc = [0] * (len(left) + len(right) - 1)
    for i, a in enumerate(left):
        if a == 0:
            continue
        for j, b in enumerate(right):
            acc[i + j] += a * b
    while len(acc) > 1 and acc[-1] == 0:
        acc.pop()
    return acc


def _poly_add_int(left: list[int], right: list[int]) -> list[int]:
    size = max(len(left), len(right))
    acc = [(left[i] if i < len(left) else 0) + (right[i] if i < len(right) else 0) for i in range(size)]
    while len(acc) > 1 and acc[-1] == 0:
        acc.pop()
    return acc or [0]


def _poly_sub_int(left: list[int], right: list[int]) -> list[int]:
    return _poly_add_int(left, [-coeff for coeff in right])


def _poly_scale_list(poly: list[int], factor: int) -> list[int]:
    if factor == 0:
        return [0]
    acc = [coeff * factor for coeff in poly]
    while len(acc) > 1 and acc[-1] == 0:
        acc.pop()
    return acc or [0]


def _product_lists(factors: list[list[int]]) -> list[int]:
    acc = [1]
    for factor in factors:
        acc = _poly_mul_int(acc, factor)
    return acc


def _hensel_lift_pair(
    poly: Poly,
    left: list[int],
    right: list[int],
    prime: int,
    target_power: int,
) -> tuple[list[int], list[int]]:
    """Linear Hensel lift of a coprime monic factorization from mod prime to prime^target_power."""

    g = _reduce_mod(left, prime)
    h = _reduce_mod(right, prime)
    # a*g + b*h = 1 over F_p
    _, a, b = _mod_egcd_pair(g, h, prime)
    power = 1
    while power < target_power:
        scale = prime ** power
        modulus = prime ** (power + 1)
        product = _poly_mul_int(g, h)
        error = _poly_sub_int(list(poly), product)
        divided: list[int] = []
        for coeff in error:
            if coeff % scale != 0:
                raise NotExact("this polynomial stays outside this rule")
            divided.append(coeff // scale)
        # s = (b * e) rem g, t = (a * e) rem h over F_p
        s = _mod_divmod(_mod_mul(_mod_trim(b, prime), _mod_trim(divided, prime), prime), _mod_trim(g, prime), prime)[1]
        t = _mod_divmod(_mod_mul(_mod_trim(a, prime), _mod_trim(divided, prime), prime), _mod_trim(h, prime), prime)[1]
        g = _reduce_mod(_poly_add_int(g, _poly_scale_list(s, scale)), modulus)
        h = _reduce_mod(_poly_add_int(h, _poly_scale_list(t, scale)), modulus)
        power += 1
    return g, h


def _mod_egcd_pair(left: list[int], right: list[int], prime: int) -> tuple[list[int], list[int], list[int]]:
    r0, r1 = _mod_trim(left, prime), _mod_trim(right, prime)
    s0, s1 = [1], [0]
    t0, t1 = [0], [1]
    while _mod_deg(r1, prime) >= 0:
        quot, rem = _mod_divmod(r0, r1, prime)
        r0, r1 = r1, rem
        s0, s1 = s1, _mod_sub(s0, _mod_mul(quot, s1, prime), prime)
        t0, t1 = t1, _mod_sub(t0, _mod_mul(quot, t1, prime), prime)
    if _mod_deg(r0, prime) < 0:
        raise NotExact("this polynomial stays outside this rule")
    inv_lead = _mod_inv(r0[-1], prime)
    gcd = _mod_trim([coeff * inv_lead for coeff in r0], prime)
    if gcd != [1]:
        raise NotExact("this polynomial stays outside this rule")
    return gcd, _mod_mul(s0, [inv_lead], prime), _mod_mul(t0, [inv_lead], prime)


def _lift_factors(poly: Poly, factors: list[list[int]], prime: int, target_power: int) -> list[list[int]]:
    if not factors:
        return []
    if len(factors) == 1:
        return [_reduce_mod(list(poly), prime ** target_power)]
    if len(factors) == 2:
        left, right = _hensel_lift_pair(poly, factors[0], factors[1], prime, target_power)
        return [left, right]
    rest = _product_lists(factors[1:])
    left, right = _hensel_lift_pair(poly, factors[0], rest, prime, target_power)
    return [left, *_lift_factors(_trim_int(right), factors[1:], prime, target_power)]


def _to_integer_factor(items: list[int], lc_hint: int) -> Poly:
    poly = primitive(_trim_int(items))
    if leading(poly) < 0:
        poly = _scale_int(poly, -1)
    return poly


def _recombine(poly: Poly, lifted: list[list[int]], modulus: int) -> tuple[Poly, ...]:
    """Find proper integer factors, or prove the polynomial is irreducible over Q."""

    poly = primitive(poly)
    n = degree(poly)
    if n < 2:
        return (poly,)
    # Center coefficients and try subset products of degree at most n//2.
    centered = [_reduce_mod(factor, modulus) for factor in lifted]
    count = len(centered)
    if count == 1:
        return (poly,)
    from itertools import combinations

    found: list[Poly] = []
    remaining = poly
    used = [False] * count
    max_subset = min(count // 1, count)
    for size in range(1, (count // 2) + 1):
        indices = [i for i in range(count) if not used[i]]
        if not indices:
            break
        for choice in combinations(indices, size):
            if any(used[i] for i in choice):
                continue
            product = [1]
            for index in choice:
                product = _poly_mul_int(product, centered[index])
            if len(product) - 1 > degree(remaining) // 2 or len(product) - 1 < 1:
                continue
            # Match the leading coefficient of remaining as nearly as possible.
            candidate = primitive(_trim_int(product))
            if leading(candidate) < 0:
                candidate = _scale_int(candidate, -1)
            # Try lc(remaining) * monic(product) variants: also try product as-is.
            trials = [candidate]
            lead = leading(remaining)
            if candidate[-1] != 0 and lead % candidate[-1] == 0:
                trials.append(primitive(_scale_int(candidate, lead // candidate[-1])))
            for trial in trials:
                if degree(trial) < 1 or degree(trial) >= degree(remaining):
                    continue
                if _divides(trial, remaining):
                    found.append(primitive(trial))
                    remaining = _exact_quo(remaining, primitive(trial))
                    for index in choice:
                        used[index] = True
                    break
            if degree(remaining) <= 1:
                break
        if degree(remaining) <= 1:
            break
    remaining = primitive(remaining)
    if found:
        if degree(remaining) >= 1:
            found.append(remaining)
        return tuple(found)
    # No proper factor: irreducible.
    return (poly,)


def _divides(factor: Poly, poly: Poly) -> bool:
    from pgi.math.algebraic import _divides_int

    return _divides_int(factor, poly)


def _exact_quo(poly: Poly, factor: Poly) -> Poly:
    from pgi.math.algebraic import _quo_int

    return _quo_int(poly, factor)


_SMALL_ODD_PRIMES = (
    3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97,
    101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151, 157, 163, 167, 173, 179, 181, 191, 193,
)


def _make_monic_integer(poly: Poly) -> tuple[Poly, int]:
    """Return a monic integer polynomial similar to f, and the original leading coefficient."""

    poly = primitive(poly)
    lead = leading(poly)
    if lead == 1:
        return poly, 1
    if lead == -1:
        return _scale_int(poly, -1), -1
    top = degree(poly)
    acc: list[int] = []
    for index, coeff in enumerate(poly):
        # a_k * lead^{n-1-k} for k < n, and 1 at k = n, as in a^{n-1} f(x/a) adjusted.
        if index == top:
            acc.append(1)
        else:
            acc.append(coeff * (lead ** (top - 1 - index)))
    return primitive(_trim_int(acc)), lead


def factor_primitive_square_free(poly: Poly) -> tuple[Poly, ...]:
    """Irreducible factors of a primitive square-free integer polynomial."""

    poly = primitive(poly)
    n = degree(poly)
    if n <= 0:
        return ()
    if n == 1:
        return (poly if leading(poly) > 0 else _scale_int(poly, -1),)
    # Strip nothing: caller already removed rational roots when desired.
    # Try a cheap modular irreducibility / factorization.
    monic, _lead = _make_monic_integer(poly)
    bound = _factor_coeff_bound(monic, n // 2)
    last_error = None
    for prime in _SMALL_ODD_PRIMES:
        try:
            factors = _ddf_and_split(monic, prime)
        except NotExact as exc:
            last_error = exc
            continue
        if factors is None:
            continue
        # Power to exceed twice the coefficient bound.
        target = 1
        modulus = prime
        while modulus <= 2 * bound:
            target += 1
            modulus *= prime
            if target > 64:
                break
        try:
            lifted = _lift_factors(monic, factors, prime, target)
            pieces = _recombine(monic, lifted, modulus)
        except (NotExact, KernelError) as exc:
            last_error = exc
            continue
        if len(pieces) == 1 and degree(pieces[0]) == degree(monic):
            # Irreducible. Return the original primitive (same roots, unit).
            out = primitive(poly)
            return (out if leading(out) > 0 else _scale_int(out, -1),)
        # Map monic factors back: they divide monic, and we want factors of poly.
        # For monic original they're the same up to sign.
        if leading(poly) in {1, -1} and monic == (poly if leading(poly) > 0 else _scale_int(poly, -1)):
            return tuple(primitive(piece) if leading(piece) > 0 else _scale_int(primitive(piece), -1) for piece in pieces)
        # General leading coefficient: factor by testing division of the original.
        recovered: list[Poly] = []
        remaining = primitive(poly)
        for piece in pieces:
            # piece is monic (approximately) of monic(f). Try to find a corresponding factor of f.
            trial = primitive(piece)
            if leading(trial) < 0:
                trial = _scale_int(trial, -1)
            if _divides(trial, remaining):
                recovered.append(trial)
                remaining = _exact_quo(remaining, trial)
                continue
            # Try content-adjusted trial: lc(remaining) * monic piece, primitive.
            adjusted = primitive(_scale_int(trial, leading(remaining)))
            if leading(adjusted) < 0:
                adjusted = _scale_int(adjusted, -1)
            if degree(adjusted) >= 1 and _divides(adjusted, remaining):
                recovered.append(adjusted)
                remaining = _exact_quo(remaining, adjusted)
        if degree(remaining) >= 1:
            recovered.append(primitive(remaining))
        recovered = [item if leading(item) > 0 else _scale_int(item, -1) for item in recovered if degree(item) >= 1]
        if recovered and sum(degree(item) for item in recovered) == n:
            return tuple(recovered)
    if last_error is not None:
        raise last_error
    raise NotExact("this polynomial stays outside this rule")


def irreducible_factors(poly: Poly) -> tuple[tuple[Poly, int], ...]:
    """Irreducible factors of an integer polynomial, with multiplicity."""

    poly = primitive(poly)
    if degree(poly) <= 0:
        return ()
    found: list[tuple[Poly, int]] = []
    for factor, multiplicity in square_free_factors(poly):
        # Extract rational roots first; the remainder is rational-root-free.
        rationals, rest = extract_rational_roots(factor)
        for root, _count in rationals:
            found.append((linear_factor(root), multiplicity))
        if degree(rest) <= 0:
            continue
        if degree(rest) <= 3:
            # Degree 2 or 3 with no rational root is irreducible. Degree 1 too.
            piece = rest if leading(rest) > 0 else _scale_int(rest, -1)
            found.append((piece, multiplicity))
            continue
        for piece in factor_primitive_square_free(rest):
            found.append((piece, multiplicity))
    return tuple(found)


def pick_algebraic(poly: Poly, low: Ratio, high: Ratio) -> Alg:
    """The unique real root of poly in (low, high), as a checked algebraic or rational."""

    if _qcmp(low, high) >= 0:
        raise KernelError("an isolating interval was empty")
    poly = primitive(poly)
    if degree(poly) <= 0:
        raise NotExact("this algebraic number stays outside")
    # A linear factor is a rational.
    if degree(poly) == 1:
        # lead x + c = 0 => x = -c/lead
        root = _q(-poly[0], poly[1])
        if _qcmp(low, root) < 0 and _qcmp(root, high) < 0:
            return root
        raise NotExact("this algebraic number stays outside")
    # Square-free part first: a multiple root is rational or handled by Yun.
    sf = square_free_factors(poly)
    matching: list[Alg] = []
    for factor, _mult in sf:
        rationals, rest = extract_rational_roots(factor)
        for root, _count in rationals:
            if _qcmp(low, root) < 0 and _qcmp(root, high) < 0:
                matching.append(root)
        if degree(rest) <= 0:
            continue
        pieces = (rest,) if degree(rest) <= 3 or _cheap_irreducible(rest) else factor_primitive_square_free(rest)
        for piece in pieces:
            piece = piece if leading(piece) > 0 else _scale_int(piece, -1)
            try:
                intervals = isolate_all(piece)
            except (NotExact, KernelError):
                continue
            for index, (left, right) in enumerate(intervals, start=1):
                if _qcmp(right, low) <= 0 or _qcmp(left, high) >= 0:
                    continue
                # Overlap: this is the root, provided uniqueness of the overlap.
                if degree(piece) == 1:
                    matching.append(_q(-piece[0], piece[1]))
                else:
                    matching.append(AlgebraicReal(piece, index))
    if len(matching) != 1:
        # Refine? If several overlaps, shrink (low, high) is the enclosure; try tighter match.
        if not matching:
            raise NotExact("this algebraic number stays outside")
        # Prefer a root whose refined interval is contained in a tightening of (low, high).
        tight: list[Alg] = []
        mid_low = low
        mid_high = high
        for item in matching:
            bounds = interval_of(item, 32)
            if _qcmp(bounds[1], mid_low) <= 0 or _qcmp(bounds[0], mid_high) >= 0:
                continue
            tight.append(item)
        if len(tight) == 1:
            return tight[0]
        raise NotExact("this algebraic number stays outside")
    return matching[0]


def _cheap_irreducible(poly: Poly) -> bool:
    from pgi.math.algebraic import _irreducible, _possible_rational_roots

    n = degree(poly)
    if n <= 1:
        return n == 1
    for root in _possible_rational_roots(poly):
        if eval_int(poly, root).num == 0:
            return False
    if n <= 3:
        return True
    # Use the local modular factorer when the current kernel limit would refuse.
    return False


def algebraic_neg(number: Alg) -> Alg:
    if isinstance(number, Ratio):
        return _qneg(number)
    # Roots of m(-x) in reversed order: if m has r real roots, -root_i is root_{r+1-i} of m(-x).
    flipped = _trim_int((coeff if index % 2 == 0 else -coeff) for index, coeff in enumerate(number.coeffs))
    flipped = primitive(flipped)
    if leading(flipped) < 0:
        flipped = _scale_int(flipped, -1)
    count = real_root_count(flipped)
    return AlgebraicReal(flipped, count + 1 - number.index)


def algebraic_scale(number: Alg, scale: Ratio) -> Alg:
    if scale.num == 0:
        return _ZERO
    if scale == _ONE:
        return number
    if isinstance(number, Ratio):
        return _qmul(number, scale)
    if scale == _q(-1, 1):
        return algebraic_neg(number)
    poly = vanishing_poly_scale(number.coeffs, scale)
    low, high = interval_of(number, 32)
    # r * interval: swap if r < 0
    if scale.num < 0:
        left, right = _qmul(high, scale), _qmul(low, scale)
    else:
        left, right = _qmul(low, scale), _qmul(high, scale)
    return pick_algebraic(poly, _widen(left), _widen(right))


def _widen(value: Ratio) -> Ratio:
    # A tiny outward nudge is not used; pick_algebraic uses open overlap.
    return value


def algebraic_add(left: Alg, right: Alg) -> Alg:
    if isinstance(left, Ratio) and isinstance(right, Ratio):
        return _qadd(left, right)
    if isinstance(left, Ratio):
        if left.num == 0:
            return right
        poly = vanishing_poly_shift(right.coeffs if isinstance(right, AlgebraicReal) else (1,), left)
        low, high = _interval_add((left, left), interval_of(right, 32))
        return pick_algebraic(poly, low, high)
    if isinstance(right, Ratio):
        return algebraic_add(right, left)
    if left == right:
        return algebraic_scale(left, _q(2, 1))
    if algebraic_equal(left, algebraic_neg(right)):
        return _ZERO
    poly = vanishing_poly_sum(left.coeffs, right.coeffs)
    low, high = _interval_add(interval_of(left, 32), interval_of(right, 32))
    # If the enclosure contains only 0 as a possible rational root and has width that
    # can be refined to exclude everything else, pick_algebraic will return 0 if it's 0.
    # Shrink the enclosure when it is wide.
    for steps in (32, 48, 64):
        low, high = _interval_add(interval_of(left, steps), interval_of(right, steps))
        try:
            return pick_algebraic(poly, low, high)
        except (NotExact, KernelError):
            continue
    return pick_algebraic(poly, low, high)


def algebraic_mul(left: Alg, right: Alg) -> Alg:
    if isinstance(left, Ratio) and isinstance(right, Ratio):
        return _qmul(left, right)
    if isinstance(left, Ratio):
        return algebraic_scale(right, left)
    if isinstance(right, Ratio):
        return algebraic_scale(left, right)
    if left == right:
        return algebraic_pow(left, 2)
    poly = vanishing_poly_product(left.coeffs, right.coeffs)
    low, high = _interval_mul(interval_of(left, 32), interval_of(right, 32))
    # If the product interval is degenerate at 0.
    if _qcmp(low, _ZERO) == 0 and _qcmp(high, _ZERO) == 0:
        return _ZERO
    for steps in (32, 48, 64):
        low, high = _interval_mul(interval_of(left, steps), interval_of(right, steps))
        try:
            return pick_algebraic(poly, low, high)
        except (NotExact, KernelError):
            continue
    return pick_algebraic(poly, low, high)


def algebraic_pow(number: Alg, exponent: int) -> Alg:
    if exponent == 0:
        return _ONE
    if exponent == 1:
        return number
    if exponent < 0:
        raise NotExact("this algebraic power stays outside")
    if isinstance(number, Ratio):
        return _q(number.num ** exponent, number.den ** exponent)
    poly = vanishing_poly_power(number.coeffs, exponent)
    bounds = interval_of(number, 32)
    # bounds^exponent via repeated interval mul
    acc = (_ONE, _ONE)
    base = bounds
    exp = exponent
    while exp:
        if exp & 1:
            acc = _interval_mul(acc, base)
        exp >>= 1
        if exp:
            base = _interval_mul(base, base)
    return pick_algebraic(poly, acc[0], acc[1])


def algebraic_sqrt(number: Alg, nonnegative: bool = True) -> Alg:
    """The real square root of a nonnegative algebraic number."""

    if isinstance(number, Ratio):
        if number.num < 0:
            raise NotExact("square root of a negative stays open")
        if number.num == 0:
            return _ZERO
        # x^2 - p/q = 0 => q x^2 - p
        poly = from_ratio_coeffs((_qneg(number), _ZERO, _ONE))
        # Isolate the positive (or negative) root.
        if nonnegative:
            return pick_algebraic(poly, _ZERO, _qadd(_q(1, 1), _q(max(number.num, number.den), 1)))
        return algebraic_neg(algebraic_sqrt(number, True))
    # Must be >= 0
    low, high = interval_of(number, 24)
    if _qcmp(high, _ZERO) < 0:
        raise NotExact("square root of a negative stays open")
    poly = vanishing_poly_root(number.coeffs, 2)
    # Enclosure of the sqrt: [0, or sqrt of high bound]
    # A crude rational upper bound for sqrt(high) is 1 + high.
    upper = _qadd(_ONE, high if _qcmp(high, _ZERO) > 0 else _ONE)
    lower = _ZERO if nonnegative else _qneg(upper)
    if nonnegative:
        return pick_algebraic(poly, _ZERO, upper)
    return pick_algebraic(poly, lower, _ZERO)



def algebraic_nth_root(number: Alg, exponent: int, nonnegative: bool = True) -> Alg:
    """A real exponent-th root of an algebraic number."""

    if exponent < 1:
        raise NotExact("this algebraic root stays outside")
    if exponent == 1:
        return number
    if exponent == 2:
        return algebraic_sqrt(number, nonnegative)
    if isinstance(number, Ratio):
        if number.num == 0:
            return _ZERO
        if number.num < 0 and exponent % 2 == 0:
            raise NotExact("square root of a negative stays open")
        poly = from_ratio_coeffs((_qneg(number),) + (_ZERO,) * (exponent - 1) + (_ONE,))
    else:
        low, high = interval_of(number, 24)
        if _qcmp(high, _ZERO) < 0 and exponent % 2 == 0:
            raise NotExact("square root of a negative stays open")
        poly = vanishing_poly_root(number.coeffs, exponent)
    # Crude rational bound: 1 + |number|.
    if isinstance(number, Ratio):
        peak = _q(abs(number.num) + abs(number.den), 1)
    else:
        low, high = interval_of(number, 16)
        peak = high if _qcmp(high, _qneg(low)) >= 0 else _qneg(low)
        if _qcmp(peak, _ZERO) < 0:
            peak = _qneg(peak)
    upper = _qadd(_ONE, peak)
    if nonnegative and exponent % 2 == 0:
        return pick_algebraic(poly, _ZERO, upper)
    if nonnegative:
        # The real odd root has the sign of the radicand; pick the unique real root
        # in a large interval, preferring the one whose sign matches.
        return pick_algebraic(poly, _qneg(upper), upper)
    return pick_algebraic(poly, _qneg(upper), _ZERO)


def algebraic_equal(left: Alg, right: Alg) -> bool:
    if left == right:
        return True
    if isinstance(left, Ratio) and isinstance(right, Ratio):
        return left == right
    if isinstance(left, AlgebraicReal) and isinstance(right, AlgebraicReal):
        if left.coeffs == right.coeffs:
            return left.index == right.index
    # Refine isolating intervals. Disjoint intervals prove inequality.
    # If both remain nested around the same point and one minpoly divides
    # the other, the numbers are equal when the enclosed root matches.
    for steps in (16, 32, 48, 64):
        left_low, left_high = interval_of(left, steps)
        right_low, right_high = interval_of(right, steps)
        if _qcmp(left_high, right_low) <= 0 or _qcmp(right_high, left_low) <= 0:
            return False
    if isinstance(left, AlgebraicReal) and isinstance(right, AlgebraicReal):
        from pgi.math.algebraic import _divides_int

        if _divides_int(left.coeffs, right.coeffs) or _divides_int(right.coeffs, left.coeffs):
            # Same number if the isolating intervals still overlap after refinement.
            return True
    if isinstance(left, Ratio) or isinstance(right, Ratio):
        return False
    # Last resort, only when the difference resultant is admitted.
    try:
        difference = algebraic_add(left, algebraic_neg(right))
    except (NotExact, KernelError):
        return False
    return isinstance(difference, Ratio) and difference.num == 0


def algebraic_sign(number: Alg) -> int:
    if isinstance(number, Ratio):
        return _sign_of(number)
    low, high = interval_of(number, 0)
    if _qcmp(high, _ZERO) < 0:
        return -1
    if _qcmp(low, _ZERO) > 0:
        return 1
    for steps in (4, 8, 16, 24, 32):
        low, high = interval_of(number, steps)
        if _qcmp(high, _ZERO) < 0:
            return -1
        if _qcmp(low, _ZERO) > 0:
            return 1
    raise NotExact("a sign in this chart could not be certified")


# --- Norm of a polynomial with algebraic coefficients ---


def _as_alg(value: Alg) -> Alg:
    return value


def norm_polynomial(coeffs: tuple[Alg, ...]) -> Poly:
    """An integer polynomial vanishing at every complex root of sum a_i x^i.

    Coefficients may be rational or real algebraic. The result is a multiple
    of the field norm, primitive, of degree at most ALGEBRA_DEGREE_LIMIT.
    """

    if not coeffs:
        raise NotExact("this polynomial stays outside this rule")
    # Identify unique algebraic coefficients; rationals stay in Q[x].
    # Represent P in Z[x][y1,...,yr] and eliminate yi one at a time.
    rationals: list[Ratio] = []
    algebraics: list[tuple[int, AlgebraicReal]] = []
    for index, coeff in enumerate(coeffs):
        if isinstance(coeff, Ratio):
            rationals.append(coeff)
        else:
            rationals.append(_ZERO)
            algebraics.append((index, coeff))
    # Start with the rational part as a polynomial in x, and add y_j x^{k_j}.
    # Eliminate each algebraic by a resultant in that variable.
    # Encode the current eliminant as a sparse multivariate polynomial:
    # after processing some algebraics, we still have others plus x.
    # We always keep a polynomial in (x, y) where y is the next algebraic,
    # with earlier algebraics already eliminated.
    return _eliminate_all(tuple(rationals), tuple(algebraics))


def _eliminate_all(rationals: tuple[Ratio, ...], algebraics: tuple[tuple[int, AlgebraicReal], ...]) -> Poly:
    if not algebraics:
        return integer_poly(rationals) if any(c.num != 0 for c in rationals) else (0,)
    # Group identical (minpoly, index) so shared coefficients share a variable.
    groups: dict[tuple[Poly, int], list[int]] = {}
    order: list[tuple[Poly, int]] = []
    for index, number in algebraics:
        key = (number.coeffs, number.index)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(index)
    # If only one algebraic symbol y, P = Q(x) + y R(x), linear in y.
    if len(order) == 1:
        key = order[0]
        minpoly, _index = key
        q_coeffs = list(rationals)
        r_acc: list[Ratio] = [_ZERO] * len(rationals)
        for index in groups[key]:
            while len(r_acc) <= index:
                r_acc.append(_ZERO)
            r_acc[index] = _qadd(r_acc[index], _ONE)
        # Res_y(m(y), Q(x) + y R(x)) = R^{deg m} m(-Q/R)
        return _linear_coeff_norm(minpoly, tuple(q_coeffs), tuple(r_acc))
    # Several independent symbols: eliminate the last, recursively.
    # Build P as a polynomial in the last y, with coefficients that are
    # themselves polynomials in x and the earlier y's... For two or more,
    # eliminate one at a time by treating the current P as ByX-like in y,
    # but the "x" ring also contains the remaining symbols.
    # Encode remaining algebraics via a Kronecker substitution later if needed.
    # For the two-symbol case we build a trivariate then resultant.
    return _tensor_norm(rationals, algebraics, order)


def _poly_x_from_ratios(coeffs: tuple[Ratio, ...]) -> RatPoly:
    return _trim_rat(coeffs) if coeffs else (_ZERO,)


def _linear_coeff_norm(minpoly: Poly, constant: tuple[Ratio, ...], slope: tuple[Ratio, ...]) -> Poly:
    """Res_y(m(y), Q(x) + y R(x)) = R^{deg m} m(-Q/R) as an integer polynomial."""

    top = degree(minpoly)
    if top < 1:
        raise NotExact("this polynomial stays outside this rule")
    q = _poly_x_from_ratios(constant)
    r = _poly_x_from_ratios(slope)
    # term_j = m_j * (-Q)^j * R^{top-j}
    total: RatPoly = (_ZERO,)
    minus_q = _neg_rat(q)
    power_q = (_ONE,)
    # powers of R
    powers_r = [(_ONE,)]
    for _ in range(top):
        powers_r.append(_mul_rat(powers_r[-1], r))
    for index, coeff in enumerate(minpoly):
        if coeff == 0:
            power_q = _mul_rat(power_q, minus_q)
            continue
        term = _mul_rat(_mul_rat(_scale_rat(power_q, _q(coeff, 1)), powers_r[top - index]), (_ONE,))
        total = _add_rat(total, term)
        power_q = _mul_rat(power_q, minus_q)
    if total == (_ZERO,):
        raise NotExact("this polynomial stays outside this rule")
    poly = from_ratio_coeffs(total)
    if degree(poly) > ALGEBRA_DEGREE_LIMIT:
        raise NotExact("this polynomial stays outside this rule")
    return primitive(poly)


def _scale_rat(poly: RatPoly, factor: Ratio) -> RatPoly:
    if factor.num == 0 or poly == (_ZERO,):
        return (_ZERO,)
    return _trim_rat(tuple(_qmul(coeff, factor) for coeff in poly))


def _eliminate_successive(
    rationals: tuple[Ratio, ...],
    algebraics: tuple[tuple[int, AlgebraicReal], ...],
) -> Poly:
    """Eliminate several algebraic coefficients by successive linear resultants.

    Each coefficient is treated as an independent algebraic number. The
    eliminant is then a multiple of the true norm, which is enough after
    the exact vanishing filter.
    """

    # Current rational-in-x polynomial after eliminating no variables:
    # We maintain a polynomial in x whose coefficients still involve remaining
    # algebraics... easier: after eliminating y_r, the result is a polynomial
    # in x with coefficients in Q(y1,...,y_{r-1}), which we represent by
    # expanding as a polynomial in the next y.
    #
    # Implementation for a small number of symbols: represent the current
    # value as a list of (Alg-free integer polynomial in x? no)
    #
    # Use a sparse encoding: a dict mapping an exponent-of-last-y to a
    # polynomial that itself will be an eliminand.
    #
    # Successive case using only one algebraic at a time by substituting
    # a standalone symbol and composing norms:
    # If P = P0 + y_r P1 with P0, P1 in Q(y1,...,y_{r-1})[x], then
    # N_r(P) = P1^{deg m_r} m_r(-P0/P1) is a polynomial in the earlier
    # coefficients. When P0, P1 themselves have algebraic coeffs, we get
    # a new polynomial whose coefficients are polynomials in the earlier
    # y's... this can be done if we expand m_r(-P0/P1) * P1^{d} with
    # P0, P1 having algebraic (not yet eliminated) coefficients, producing
    # a new list of algebraic coefficients.
    #
    # That's messy if P0 has algebraic coeffs. For independent symbols,
    # P0 is the rational part plus earlier y_i x^{k_i}, P1 is a 0-1 poly in x.
    #
    # We'll implement a loop: the "current polynomial" is a list of Alg
    # coefficients in x. Start with the original. While some coeff is
    # algebraic, pick one algebraic number α appearing, write P = Q + α R
    # where Q, R have coefficients that do not use this particular α
    # (they may use other algebraics), replace P by R^d m(-Q/R) computed
    # in the ring of Alg-coefficient polynomials (using algebraic_add/mul
    # for coefficient arithmetic).
    current: list[Alg] = list(rationals)
    # Pad
    used: set[tuple[Poly, int]] = set()
    remaining = list(algebraics)
    # Rebuild current from rationals + algebraics (original coeffs).
    current = []
    max_index = len(rationals) - 1
    for index, _number in algebraics:
        if index > max_index:
            max_index = index
    for index in range(max_index + 1):
        current.append(rationals[index] if index < len(rationals) else _ZERO)
    for index, number in algebraics:
        current[index] = algebraic_add(current[index], number)
    safety = 0
    while True:
        safety += 1
        if safety > 16:
            raise NotExact("this polynomial stays outside this rule")
        # Find a coefficient that is algebraic.
        target: AlgebraicReal | None = None
        for coeff in current:
            if isinstance(coeff, AlgebraicReal):
                target = coeff
                break
        if target is None:
            ratios = tuple(coeff if isinstance(coeff, Ratio) else _ZERO for coeff in current)
            poly = integer_poly(ratios)
            if degree(poly) > ALGEBRA_DEGREE_LIMIT:
                raise NotExact("this polynomial stays outside this rule")
            return primitive(poly)
        key = (target.coeffs, target.index)
        if key in used:
            # Same minpoly and index already scheduled — shouldn't loop.
            raise NotExact("this polynomial stays outside this rule")
        used.add(key)
        # Write current = Q + α R, where a coeff is in Q if it is not a
        # rational-linear expression in this particular α. We only split
        # when the coefficient is *exactly* this α, a rational, or
        # rational + this α. If a coefficient is a different algebraic,
        # it goes into Q.
        q: list[Alg] = []
        r: list[Alg] = []
        for coeff in current:
            q.append(_ZERO)
            r.append(_ZERO)
            if isinstance(coeff, Ratio):
                q[-1] = coeff
                continue
            if isinstance(coeff, AlgebraicReal) and (coeff.coeffs, coeff.index) == key:
                r[-1] = _ONE
                continue
            # coeff might be s + t α, but we store them as combined AlgebraicReals
            # of a different minpoly. Treat as part of Q (independent).
            q[-1] = coeff
        # Compute R^{deg m} m(-Q/R) with algebraic coefficient arithmetic.
        current = _apply_minpoly_linear(target.coeffs, q, r)
        # Trim
        while len(current) > 1 and _is_zero_alg(current[-1]):
            current.pop()


def _is_zero_alg(value: Alg) -> bool:
    return isinstance(value, Ratio) and value.num == 0


def _apply_minpoly_linear(minpoly: Poly, constant: list[Alg], slope: list[Alg]) -> list[Alg]:
    """R^{deg m} m(-Q/R) as an Alg-coefficient polynomial in x."""

    top = degree(minpoly)
    # polys Q, R as lists of Alg
    q, r = list(constant), list(slope)
    minus_q = _poly_alg_neg(q)
    power_q: list[Alg] = [_ONE]  # (-Q)^0
    powers_r: list[list[Alg]] = [[_ONE]]
    for _ in range(top):
        powers_r.append(_poly_alg_mul(powers_r[-1], r))
    total: list[Alg] = [_ZERO]
    current_q_pow = [_ONE]
    for index, coeff in enumerate(minpoly):
        if coeff != 0:
            # m_j * (-Q)^j * R^{top-j}
            term = _poly_alg_scale(current_q_pow, _q(coeff, 1))
            term = _poly_alg_mul(term, powers_r[top - index])
            total = _poly_alg_add(total, term)
        current_q_pow = _poly_alg_mul(current_q_pow, minus_q)
    return total


def _poly_alg_neg(poly: list[Alg]) -> list[Alg]:
    return [algebraic_neg(coeff) for coeff in poly]


def _poly_alg_scale(poly: list[Alg], factor: Ratio) -> list[Alg]:
    if factor.num == 0:
        return [_ZERO]
    return [algebraic_scale(coeff, factor) for coeff in poly]


def _poly_alg_add(left: list[Alg], right: list[Alg]) -> list[Alg]:
    size = max(len(left), len(right))
    return [
        algebraic_add(left[i] if i < len(left) else _ZERO, right[i] if i < len(right) else _ZERO)
        for i in range(size)
    ]


def _poly_alg_mul(left: list[Alg], right: list[Alg]) -> list[Alg]:
    if not left or not right:
        return [_ZERO]
    acc: list[Alg] = [_ZERO] * (len(left) + len(right) - 1)
    for i, a in enumerate(left):
        if _is_zero_alg(a):
            continue
        for j, b in enumerate(right):
            if _is_zero_alg(b):
                continue
            acc[i + j] = algebraic_add(acc[i + j], algebraic_mul(a, b))
    return acc


def enclose_poly_alg(coeffs: tuple[Alg, ...] | list[Alg], value: Alg, steps: int = 32) -> tuple[Ratio, Ratio]:
    """A rational isolating interval for p(value), by interval arithmetic."""

    if isinstance(value, Ratio):
        val_iv = (value, value)
    else:
        val_iv = interval_of(value, steps)
    total = (_ZERO, _ZERO)
    power = (_ONE, _ONE)
    last = len(list(coeffs)) - 1
    for index, coeff in enumerate(coeffs):
        coeff_iv = (coeff, coeff) if isinstance(coeff, Ratio) else interval_of(coeff, steps)
        total = _interval_add(total, _interval_mul(coeff_iv, power))
        if index < last:
            power = _interval_mul(power, val_iv)
    return total


def is_root_of_poly(coeffs: tuple[Alg, ...] | list[Alg], value: Alg) -> bool:
    """True only when p(value) is certified to be exactly 0."""

    for steps in (16, 32, 48, 64, 80):
        low, high = enclose_poly_alg(coeffs, value, steps)
        if _qcmp(high, _ZERO) < 0 or _qcmp(low, _ZERO) > 0:
            return False
    # The enclosure still contains 0. Prove vanishing exactly.
    total = eval_poly_alg(coeffs, value)
    return algebraic_equal(total, _ZERO)


def eval_poly_alg(coeffs: tuple[Alg, ...] | list[Alg], value: Alg) -> Alg:
    total: Alg = _ZERO
    power: Alg = _ONE
    last = len(list(coeffs)) - 1
    for index, coeff in enumerate(coeffs):
        total = algebraic_add(total, algebraic_mul(coeff, power))
        if index < last:
            power = algebraic_mul(power, value)
    return total


def roots_of_algebraic_polynomial(coeffs: tuple[Alg, ...]) -> tuple[tuple[Alg, int], ...]:
    """Distinct real roots of a polynomial with rational or algebraic coefficients.

    Multiplicity is recorded as 1 for an odd-sign-change root and 2 for an
    even-sign-change isolated root after the sign chart of the original is
    inspected by the caller; here every isolated vanishing root is returned
    with multiplicity 1, and the caller infers parity from signs.
    """

    if not coeffs:
        return ()
    # All rational? Use the existing rational path.
    if all(isinstance(coeff, Ratio) for coeff in coeffs):
        from pgi.math.algebraic import roots_of_rational_polynomial

        found = roots_of_rational_polynomial(integer_poly(coeffs))
        converted: list[tuple[Alg, int]] = []
        for root, multiplicity in found:
            converted.append((root, multiplicity))
        return tuple(converted)
    norm = norm_polynomial(coeffs)
    if degree(norm) <= 0:
        return ()
    # Isolate real roots of the square-free part of the norm.
    candidates: list[Alg] = []
    for factor, _mult in square_free_factors(norm):
        rationals, rest = extract_rational_roots(factor)
        for root, _count in rationals:
            candidates.append(root)
        if degree(rest) <= 0:
            continue
        try:
            pieces = (rest,) if degree(rest) <= 3 else factor_primitive_square_free(rest)
        except NotExact:
            # Still isolate the (possibly reducible) square-free remainder,
            # then pick an irreducible minpoly for each real root if possible.
            pieces = (rest,)
        for piece in pieces:
            piece = piece if leading(piece) > 0 else _scale_int(piece, -1)
            intervals = isolate_all(piece)
            if _cheap_irreducible(piece) or (degree(piece) <= 3) or _is_proved_irreducible(piece):
                for index, _interval in enumerate(intervals, start=1):
                    if degree(piece) == 1:
                        candidates.append(_q(-piece[0], piece[1]))
                    else:
                        candidates.append(AlgebraicReal(piece, index))
            else:
                # Factor, or pick per interval.
                try:
                    factors = factor_primitive_square_free(piece)
                except NotExact:
                    # Last resort: treat each isolated root of this piece.
                    for index, (low, high) in enumerate(intervals, start=1):
                        candidates.append(pick_algebraic(piece, low, high))
                else:
                    for factor in factors:
                        factor = factor if leading(factor) > 0 else _scale_int(factor, -1)
                        for index, _interval in enumerate(isolate_all(factor), start=1):
                            if degree(factor) == 1:
                                candidates.append(_q(-factor[0], factor[1]))
                            else:
                                candidates.append(AlgebraicReal(factor, index))
    # Keep only roots of the original, exactly.
    kept: list[Alg] = []
    for candidate in candidates:
        if is_root_of_poly(coeffs, candidate):
            kept.append(candidate)
    # Sort by isolating interval
    def sort_key(number: Alg) -> tuple[int, int, int, int]:
        low, high = interval_of(number, 16)
        # Compare midpoints by cross multiplication after a common view
        mid = _qadd(low, high)
        # (num/den) — store as (sign, abs num, den) with mid/2
        return (mid.num, mid.den, low.num, low.den)

    kept.sort(key=lambda number: _sort_pair(interval_of(number, 16)))
    # Deduplicate
    unique: list[Alg] = []
    for item in kept:
        if unique and algebraic_equal(unique[-1], item):
            continue
        unique.append(item)
    return tuple((item, 1) for item in unique)


def _sort_pair(bounds: tuple[Ratio, Ratio]) -> tuple[int, int]:
    mid = _qadd(bounds[0], bounds[1])
    # Sort by mid/2: compare mid.num/mid.den
    return (mid.num, mid.den)


def _is_proved_irreducible(poly: Poly) -> bool:
    try:
        factors = factor_primitive_square_free(poly)
    except (NotExact, KernelError):
        return False
    return len(factors) == 1 and degree(factors[0]) == degree(poly)


def sign_at_algebraic(coeffs: tuple[Alg, ...] | list[Alg], value: Ratio) -> int:
    """Sign of a polynomial with algebraic coefficients at a rational point."""

    for steps in (0, 4, 8, 16, 24, 32):
        low, high = enclose_poly_alg(coeffs, value, steps)
        if _qcmp(high, _ZERO) < 0:
            return -1
        if _qcmp(low, _ZERO) > 0:
            return 1
        if _qcmp(low, _ZERO) == 0 and _qcmp(high, _ZERO) == 0:
            return 0
    total = eval_poly_alg(coeffs, value)
    if algebraic_equal(total, _ZERO) or _is_zero_alg(total):
        return 0
    return algebraic_sign(total)


def _tensor_norm(
    rationals: tuple[Ratio, ...],
    algebraics: tuple[tuple[int, AlgebraicReal], ...],
    order: list[tuple[Poly, int]],
) -> Poly:
    """det of multiplication by p(x) on Q[y_1]/(m_1) (x) ... (x) Q[y_r]/(m_r).

    Each distinct algebraic coefficient is a symbol y_j with minimal polynomial
    m_j. The determinant is the product of p(x) over every tuple of
    conjugates, so it vanishes at every root of p and is a multiple of the
    field norm. It is a rational polynomial in x of degree n * prod(deg m_j),
    found exactly by evaluating the determinant at that many plus one integer
    points and interpolating.
    """

    from fractions import Fraction

    dims = [degree(key[0]) for key in order]
    size = 1
    for dim in dims:
        size *= dim
    top = max(len(rationals) - 1, max(index for index, _ in algebraics))
    if size * top > ALGEBRA_DEGREE_LIMIT:
        raise NotExact("this polynomial stays outside this rule")

    def companion(poly: Poly) -> list[list[Fraction]]:
        d = degree(poly)
        lead = Fraction(poly[d])
        mat = [[Fraction(0)] * d for _ in range(d)]
        for row in range(1, d):
            mat[row][row - 1] = Fraction(1)
        for row in range(d):
            mat[row][d - 1] = -Fraction(poly[row]) / lead
        return mat

    def kron(left: list[list[Fraction]], right: list[list[Fraction]]) -> list[list[Fraction]]:
        a, b = len(left), len(right)
        out = [[Fraction(0)] * (a * b) for _ in range(a * b)]
        for i in range(a):
            for j in range(a):
                v = left[i][j]
                if v == 0:
                    continue
                for k in range(b):
                    for l in range(b):
                        w = right[k][l]
                        if w:
                            out[i * b + k][j * b + l] = v * w
        return out

    def identity(n: int) -> list[list[Fraction]]:
        return [[Fraction(int(i == j)) for j in range(n)] for i in range(n)]

    symbol_mats: dict[tuple[Poly, int], list[list[Fraction]]] = {}
    for position, key in enumerate(order):
        mat = [[Fraction(1)]]
        for other, dim in enumerate(dims):
            mat = kron(mat, companion(key[0]) if other == position else identity(dim))
        symbol_mats[key] = mat
    coeff_mats: list[list[list[Fraction]]] = []
    for index in range(top + 1):
        mat = [[Fraction(0)] * size for _ in range(size)]
        if index < len(rationals) and rationals[index].num:
            r = Fraction(rationals[index].num, rationals[index].den)
            for i in range(size):
                mat[i][i] += r
        coeff_mats.append(mat)
    for index, number in algebraics:
        sym = symbol_mats[(number.coeffs, number.index)]
        target = coeff_mats[index]
        for i in range(size):
            for j in range(size):
                if sym[i][j]:
                    target[i][j] += sym[i][j]

    def det(mat: list[list[Fraction]]) -> Fraction:
        m = [row[:] for row in mat]
        n = len(m)
        result = Fraction(1)
        for col in range(n):
            pivot = next((r for r in range(col, n) if m[r][col] != 0), None)
            if pivot is None:
                return Fraction(0)
            if pivot != col:
                m[col], m[pivot] = m[pivot], m[col]
                result = -result
            pv = m[col][col]
            result *= pv
            for r in range(col + 1, n):
                f = m[r][col]
                if f:
                    f /= pv
                    row_r, row_c = m[r], m[col]
                    for c in range(col, n):
                        row_r[c] -= f * row_c[c]
        return result

    total_degree = size * top
    xs = list(range(-(total_degree // 2), total_degree - total_degree // 2 + 1))
    ys: list[Fraction] = []
    for x in xs:
        mat = [[Fraction(0)] * size for _ in range(size)]
        power = Fraction(1)
        for cm in coeff_mats:
            for i in range(size):
                row, src = mat[i], cm[i]
                for j in range(size):
                    if src[j]:
                        row[j] += power * src[j]
            power *= x
        ys.append(det(mat))
    # Newton interpolation, then expand to monomial coefficients.
    count = len(xs)
    diffs = ys[:]
    for level in range(1, count):
        for i in range(count - 1, level - 1, -1):
            diffs[i] = (diffs[i] - diffs[i - 1]) / (xs[i] - xs[i - level])
    poly = [Fraction(0)] * count
    basis = [Fraction(1)]
    for i in range(count):
        for k, b in enumerate(basis):
            poly[k] += diffs[i] * b
        nxt = [Fraction(0)] * (len(basis) + 1)
        for k, b in enumerate(basis):
            nxt[k + 1] += b
            nxt[k] -= xs[i] * b
        basis = nxt
    ratios = tuple(_q(c.numerator, c.denominator) for c in poly)
    if all(c.num == 0 for c in ratios):
        raise NotExact("this polynomial stays outside this rule")
    result = primitive(integer_poly(ratios))
    if degree(result) > ALGEBRA_DEGREE_LIMIT:
        raise NotExact("this polynomial stays outside this rule")
    return result
