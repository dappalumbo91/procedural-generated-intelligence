"""Checked real algebraic numbers.

A real algebraic number is a primitive irreducible integer polynomial
together with the index of one of its real roots, ordered increasingly.
Sturm's theorem isolates that root in a rational interval that contains
exactly one real root, and the number is kept only when that count, the
irreducibility of the polynomial, and the index all check.

Square-free factorization (Yun) plus isolation of each irreducible factor
give the distinct real roots of a rational polynomial, with multiplicity.
The sign chart built from those roots is kept only when it is checked at
rational test points and at every constructed root.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import gcd, isqrt
from typing import Iterable

from pgi.math.kernel import KernelError, NotExact
from pgi.math.rational import Ratio

POLY_DEGREE_LIMIT = 12

_ZERO = Ratio(0, 1)
_ONE = Ratio(1, 1)

# Integer coefficients, constant term first.
Poly = tuple[int, ...]
RatPoly = tuple[Ratio, ...]


def _q(numerator: int, denominator: int = 1) -> Ratio:
    if denominator == 0:
        raise NotExact("division by zero")
    if denominator < 0:
        numerator = -numerator
        denominator = -denominator
    if numerator == 0:
        return _ZERO
    div = gcd(abs(numerator), denominator)
    return Ratio(numerator // div, denominator // div)


def _qadd(left: Ratio, right: Ratio) -> Ratio:
    return _q(left.num * right.den + right.num * left.den, left.den * right.den)


def _qsub(left: Ratio, right: Ratio) -> Ratio:
    return _q(left.num * right.den - right.num * left.den, left.den * right.den)


def _qmul(left: Ratio, right: Ratio) -> Ratio:
    return _q(left.num * right.num, left.den * right.den)


def _qneg(value: Ratio) -> Ratio:
    if value.num == 0:
        return _ZERO
    return Ratio(-value.num, value.den)


def _qinv(value: Ratio) -> Ratio:
    if value.num == 0:
        raise NotExact("division by zero")
    return _q(value.den, value.num)


def _qdiv(left: Ratio, right: Ratio) -> Ratio:
    return _qmul(left, _qinv(right))


def _qcmp(left: Ratio, right: Ratio) -> int:
    value = left.num * right.den - right.num * left.den
    if value < 0:
        return -1
    if value > 0:
        return 1
    return 0


def _trim_int(coeffs: Iterable[int]) -> Poly:
    items = list(coeffs)
    while len(items) > 1 and items[-1] == 0:
        items.pop()
    if not items:
        return (0,)
    return tuple(items)


def _trim_rat(coeffs: Iterable[Ratio]) -> RatPoly:
    items = list(coeffs)
    while len(items) > 1 and items[-1].num == 0:
        items.pop()
    if not items:
        return (_ZERO,)
    return tuple(items)


def degree(poly: Poly) -> int:
    if poly == (0,):
        return -1
    return len(poly) - 1


def leading(poly: Poly) -> int:
    return poly[-1]


def primitive(poly: Poly) -> Poly:
    poly = _trim_int(poly)
    if poly == (0,):
        return poly
    content = 0
    for coeff in poly:
        content = gcd(content, abs(coeff))
    if content in {0, 1} and leading(poly) > 0:
        return poly
    if content == 0:
        return poly
    if leading(poly) < 0:
        content = -content
    return tuple(coeff // content for coeff in poly)


def from_ratio_coeffs(coeffs: Iterable[Ratio]) -> Poly:
    items = _trim_rat(coeffs)
    den = 1
    for coeff in items:
        den = den * coeff.den // gcd(den, coeff.den)
    integers = [coeff.num * (den // coeff.den) for coeff in items]
    return primitive(_trim_int(integers))


def integer_poly(coeffs: Iterable[Ratio]) -> Poly:
    """Clear denominators and a positive content, keeping the leading sign."""

    items = _trim_rat(coeffs)
    den = 1
    for coeff in items:
        den = den * coeff.den // gcd(den, coeff.den)
    integers = [coeff.num * (den // coeff.den) for coeff in items]
    poly = _trim_int(integers)
    if poly == (0,):
        return poly
    content = 0
    for coeff in poly:
        content = gcd(content, abs(coeff))
    if content in {0, 1}:
        return poly
    return tuple(coeff // content for coeff in poly)


def _to_rat(poly: Poly) -> RatPoly:
    return tuple(_q(coeff, 1) for coeff in poly)


def _add_rat(left: RatPoly, right: RatPoly) -> RatPoly:
    size = max(len(left), len(right))
    return _trim_rat(
        _qadd(left[i] if i < len(left) else _ZERO, right[i] if i < len(right) else _ZERO)
        for i in range(size)
    )


def _sub_rat(left: RatPoly, right: RatPoly) -> RatPoly:
    return _add_rat(left, tuple(_qneg(coeff) for coeff in right))


def _mul_int(left: Poly, right: Poly) -> Poly:
    acc = [0] * (len(left) + len(right) - 1)
    for i, a in enumerate(left):
        if a == 0:
            continue
        for j, b in enumerate(right):
            acc[i + j] += a * b
    return _trim_int(acc)


def _divmod_rat(left: RatPoly, right: RatPoly) -> tuple[RatPoly, RatPoly]:
    right = _trim_rat(right)
    if right == (_ZERO,):
        raise NotExact("division by zero")
    remainder = list(_trim_rat(left))
    divisor_deg = len(right) - 1
    divisor_lc = right[-1]
    quot = [_ZERO]
    while True:
        rem = _trim_rat(remainder)
        if rem == (_ZERO,) or len(rem) - 1 < divisor_deg:
            break
        shift = (len(rem) - 1) - divisor_deg
        coeff = _qdiv(rem[-1], divisor_lc)
        if shift >= len(quot):
            quot.extend([_ZERO] * (shift - len(quot) + 1))
        quot[shift] = _qadd(quot[shift], coeff)
        remainder = list(rem)
        for i, value in enumerate(right):
            index = i + shift
            if index >= len(remainder):
                remainder.extend([_ZERO] * (index - len(remainder) + 1))
            remainder[index] = _qsub(remainder[index], _qmul(value, coeff))
    return _trim_rat(quot), rem if rem == (_ZERO,) else _trim_rat(remainder)


def _derivative_rat(poly: RatPoly) -> RatPoly:
    if len(poly) <= 1:
        return (_ZERO,)
    return _trim_rat(_qmul(poly[i], _q(i, 1)) for i in range(1, len(poly)))


def eval_int(poly: Poly, value: Ratio) -> Ratio:
    total = _ZERO
    power = _ONE
    for coeff in poly:
        total = _qadd(total, _qmul(_q(coeff, 1), power))
        power = _qmul(power, value)
    return total


def _gcd_rat(left: RatPoly, right: RatPoly) -> RatPoly:
    a, b = _trim_rat(left), _trim_rat(right)
    while b != (_ZERO,):
        _, rem = _divmod_rat(a, b)
        a, b = b, rem
    if a == (_ZERO,):
        return (_ZERO,)
    return tuple(_qdiv(coeff, a[-1]) for coeff in a)


def _quo_int(poly: Poly, factor: Poly) -> Poly:
    quot, rem = _divmod_rat(_to_rat(poly), _to_rat(factor))
    if rem != (_ZERO,):
        raise KernelError("an expected exact polynomial quotient had a remainder")
    return from_ratio_coeffs(quot)


def _divides_int(factor: Poly, poly: Poly) -> bool:
    if factor == (0,):
        return False
    _, rem = _divmod_rat(_to_rat(poly), _to_rat(factor))
    return rem == (_ZERO,)


def square_free_factors(poly: Poly) -> tuple[tuple[Poly, int], ...]:
    """Yun's algorithm. Each factor is primitive and square-free, with its multiplicity."""

    poly = primitive(poly)
    if poly == (0,):
        raise NotExact("the zero polynomial has no square-free factorization")
    if degree(poly) <= 0:
        return ()
    f = _to_rat(poly)
    g = _gcd_rat(f, _derivative_rat(f))
    a, _ = _divmod_rat(f, g)
    b, _ = _divmod_rat(_derivative_rat(f), g)
    factors: list[tuple[Poly, int]] = []
    k = 1
    while degree(from_ratio_coeffs(a)) > 0:
        c = _sub_rat(b, _derivative_rat(a))
        d = _gcd_rat(a, c)
        if degree(from_ratio_coeffs(d)) > 0:
            factors.append((from_ratio_coeffs(d), k))
        a, _ = _divmod_rat(a, d)
        b, _ = _divmod_rat(c, d)
        a = _trim_rat(a)
        b = _trim_rat(b)
        k += 1
        if k > POLY_DEGREE_LIMIT + 2:
            raise NotExact("this polynomial stays outside this rule")
    return tuple(factors)


def _divisors(number: int) -> tuple[int, ...]:
    number = abs(number)
    if number == 0:
        return (0,)
    found: list[int] = []
    limit = isqrt(number)
    for candidate in range(1, limit + 1):
        if number % candidate == 0:
            found.append(candidate)
            other = number // candidate
            if other != candidate:
                found.append(other)
    return tuple(found)


def _possible_rational_roots(poly: Poly) -> tuple[Ratio, ...]:
    poly = primitive(poly)
    if degree(poly) < 1:
        return ()
    constant = abs(poly[0])
    lead = abs(leading(poly))
    candidates: list[Ratio] = []
    seen: set[tuple[int, int]] = set()
    if constant == 0:
        candidates.append(_ZERO)
        seen.add((0, 1))
    for p in _divisors(constant if constant else 1):
        for q in _divisors(lead):
            for sign in (1, -1):
                value = _q(sign * p, q)
                key = (value.num, value.den)
                if key not in seen:
                    seen.add(key)
                    candidates.append(value)
    return tuple(candidates)


def linear_factor(root: Ratio) -> Poly:
    return primitive((-root.num, root.den))


def _ratio_key(value: Ratio) -> tuple[int, int]:
    return (value.num * 1 - 0, value.den) if False else (value.num * 10**0, value.den)


def _ratio_order(value: Ratio) -> tuple[int, int]:
    # Compare by cross-multiplying against 0, then by |num|/den via (abs(num), den) is wrong.
    # Use (sign, abs_num * scale). For sorting only: (num, den) with same sign comparison
    # is not total by value. Store (num, den) and sort with _qcmp.
    return (value.num, value.den)


def extract_rational_roots(poly: Poly) -> tuple[tuple[tuple[Ratio, int], ...], Poly]:
    """Strip every rational root, with multiplicity. The remainder has none."""

    remaining = primitive(poly)
    found: dict[tuple[int, int], tuple[Ratio, int]] = {}
    progressed = True
    while progressed and degree(remaining) >= 1:
        progressed = False
        for root in _possible_rational_roots(remaining):
            if eval_int(remaining, root).num == 0:
                remaining = _quo_int(remaining, linear_factor(root))
                key = (root.num, root.den)
                previous = found.get(key)
                found[key] = (root, 1 if previous is None else previous[1] + 1)
                progressed = True
                break
    ordered = tuple(sorted(found.values(), key=lambda item: _qcmp(item[0], _ZERO) or 0))
    # sorted by actual rational value
    values = list(found.values())
    values.sort(key=lambda item: (item[0].num * 1, item[0].den))
    values.sort(key=lambda a: 0)  # dummy to be replaced — use cmp_to_key
    from functools import cmp_to_key

    values = list(found.values())
    values.sort(key=cmp_to_key(lambda a, b: _qcmp(a[0], b[0])))
    return tuple(values), remaining


def _interpolate(xs: tuple[int, ...], ys: tuple[int, ...]) -> Poly | None:
    """Lagrange interpolation of a rational polynomial through integer points, if it is integral."""

    if len(xs) != len(ys) or not xs:
        return None
    total = (_ZERO,)
    for i, yi in enumerate(ys):
        numer = (_q(yi, 1),)
        for j, xj in enumerate(xs):
            if i == j:
                continue
            # (x - xj) / (xi - xj)
            numer = _mul_int_rat(numer, (_q(-xj, 1), _ONE))
            denom = xs[i] - xj
            if denom == 0:
                return None
            numer = tuple(_qdiv(coeff, _q(denom, 1)) for coeff in numer)
        total = _add_rat(total, numer)
    # require integer coefficients
    integers: list[int] = []
    for coeff in _trim_rat(total):
        if coeff.den != 1:
            return None
        integers.append(coeff.num)
    return _trim_int(integers)


def _mul_int_rat(left: RatPoly, right: RatPoly) -> RatPoly:
    acc = [_ZERO] * (len(left) + len(right) - 1)
    for i, a in enumerate(left):
        if a.num == 0:
            continue
        for j, b in enumerate(right):
            acc[i + j] = _qadd(acc[i + j], _qmul(a, b))
    return _trim_rat(acc)


def _integer_divisors_of_value(value: int) -> tuple[int, ...]:
    if value == 0:
        return (0,)
    positives = _divisors(abs(value))
    return tuple(item for pos in positives for item in (pos, -pos))


def _kronecker_factors(poly: Poly, max_deg: int) -> tuple[Poly, ...]:
    poly = primitive(poly)
    n = degree(poly)
    if n < 2 or max_deg < 1:
        return ()
    max_deg = min(max_deg, n // 2)
    # Evaluate at 0, 1, -1, 2, -2, ... until we have max_deg + 1 nonzero values.
    points: list[int] = []
    values: list[int] = []
    trial = 0
    step = 0
    while len(points) < max_deg + 1:
        if step == 0:
            trial = 0
        elif step % 2 == 1:
            trial = (step + 1) // 2
        else:
            trial = -step // 2
        step += 1
        if step > 40:
            break
        value = eval_int(poly, _q(trial, 1))
        if value.den != 1:
            continue
        if value.num == 0:
            # A rational integer root should already have been extracted.
            continue
        points.append(trial)
        values.append(value.num)
    if len(points) < 2:
        return ()
    # Search for a factor of degree 1..max_deg by choosing divisor tuples.
    # Bound the search: skip if any |f(t)| has too many divisors.
    from itertools import product

    found: list[Poly] = []
    seen: set[Poly] = set()
    for deg in range(1, max_deg + 1):
        xs = tuple(points[: deg + 1])
        ys_choices = [_integer_divisors_of_value(values[i]) for i in range(deg + 1)]
        if any(len(choices) > 24 for choices in ys_choices):
            continue
        if _product_len(ys_choices) > 8000:
            continue
        for ys in product(*ys_choices):
            candidate = _interpolate(xs, ys)
            if candidate is None:
                continue
            candidate = primitive(candidate)
            if degree(candidate) < 1 or degree(candidate) > deg:
                continue
            if candidate in seen or candidate == (1,) or candidate == (-1,):
                continue
            if leading(candidate) < 0:
                continue
            if _divides_int(candidate, poly) and degree(candidate) < n:
                seen.add(candidate)
                found.append(candidate)
    return tuple(found)


def _product_len(choices: list[tuple[int, ...]]) -> int:
    total = 1
    for item in choices:
        total *= max(1, len(item))
    return total


def _irreducible(poly: Poly) -> bool:
    poly = primitive(poly)
    n = degree(poly)
    if n <= 0:
        return False
    if n == 1:
        return True
    # A rational root means a linear factor.
    for root in _possible_rational_roots(poly):
        if eval_int(poly, root).num == 0:
            return False
    if n <= 3:
        return True
    if n > POLY_DEGREE_LIMIT:
        from pgi.math.algfield import _is_proved_irreducible

        return _is_proved_irreducible(poly)
    return not _kronecker_factors(poly, n // 2)


def factor_square_free(poly: Poly) -> tuple[Poly, ...]:
    """Irreducible factors of a square-free primitive polynomial, up to units."""

    poly = primitive(poly)
    if degree(poly) <= 0:
        return ()
    if _irreducible(poly):
        return (poly,)
    factors = _kronecker_factors(poly, degree(poly) // 2)
    if not factors:
        # Could not split, even though a rational-root-free cubic is irreducible.
        if degree(poly) <= 3:
            return (poly,)
        from pgi.math.algfield import factor_primitive_square_free

        return factor_primitive_square_free(poly)
    factor = factors[0]
    rest = _quo_int(poly, factor)
    return tuple((*factor_square_free(factor), *factor_square_free(rest)))


# --- Sturm isolation ---


def _sturm_chain(poly: Poly) -> tuple[RatPoly, ...]:
    p0 = _to_rat(primitive(poly))
    p1 = _derivative_rat(p0)
    chain = [p0, p1]
    while chain[-1] != (_ZERO,) and len(chain[-1]) > 1:
        _, rem = _divmod_rat(chain[-2], chain[-1])
        if rem == (_ZERO,):
            break
        chain.append(tuple(_qneg(coeff) for coeff in rem))
        if len(chain) > max(POLY_DEGREE_LIMIT + 4, degree(poly) + 4):
            raise NotExact("this polynomial stays outside this rule")
    # drop a trailing zero if present
    if chain[-1] == (_ZERO,):
        chain.pop()
    return tuple(chain)


def _sign_of(value: Ratio) -> int:
    if value.num < 0:
        return -1
    if value.num > 0:
        return 1
    return 0


def _eval_sign(poly: RatPoly, value: Ratio | None, plus_inf: bool) -> int:
    if value is None:
        # Sign at ±∞ from the leading coefficient and the degree.
        lead = poly[-1]
        deg = len(poly) - 1 if poly != (_ZERO,) else -1
        sign = _sign_of(lead)
        if plus_inf or deg < 0:
            return sign
        return sign if deg % 2 == 0 else -sign
    return _sign_of(eval_rat_poly(poly, value))


def eval_rat_poly(poly: RatPoly, value: Ratio) -> Ratio:
    total = _ZERO
    power = _ONE
    for coeff in poly:
        total = _qadd(total, _qmul(coeff, power))
        power = _qmul(power, value)
    return total


def _variations(chain: tuple[RatPoly, ...], value: Ratio | None, plus_inf: bool) -> int:
    signs: list[int] = []
    for poly in chain:
        sign = _eval_sign(poly, value, plus_inf)
        if sign == 0:
            continue
        signs.append(sign)
    count = 0
    for left, right in zip(signs, signs[1:]):
        if left != right:
            count += 1
    return count


def sturm_count(poly: Poly, low: Ratio | None, high: Ratio | None) -> int:
    """Number of distinct real roots in (low, high). None means ±∞."""

    poly = primitive(poly)
    if degree(poly) <= 0:
        return 0
    chain = _sturm_chain(poly)
    if low is not None and high is not None and _qcmp(low, high) >= 0:
        return 0
    if low is not None and eval_int(poly, low).num == 0:
        raise NotExact("a Sturm endpoint must not be a root")
    if high is not None and eval_int(poly, high).num == 0:
        raise NotExact("a Sturm endpoint must not be a root")
    left = _variations(chain, low, plus_inf=False)
    right = _variations(chain, high, plus_inf=True if high is None else False)
    return left - right


def cauchy_bound(poly: Poly) -> Ratio:
    poly = primitive(poly)
    if degree(poly) <= 0:
        return _ONE
    lead = abs(leading(poly))
    peak = 0
    for coeff in poly[:-1]:
        peak = max(peak, abs(coeff))
    # 1 + max |a_i / a_n|
    return _qadd(_ONE, _q(peak, lead))


def _mid(low: Ratio, high: Ratio) -> Ratio:
    return _qdiv(_qadd(low, high), _q(2, 1))


def isolate_interval(poly: Poly, index: int) -> tuple[Ratio, Ratio]:
    """Return a rational isolating interval for the index-th real root (1-based)."""

    intervals = list(isolate_all(poly))
    if index < 1 or index > len(intervals):
        raise KernelError("this algebraic index is not a real root of the polynomial")
    return intervals[index - 1]


def isolate_all(poly: Poly) -> tuple[tuple[Ratio, Ratio], ...]:
    """Disjoint open rational intervals, one for each distinct real root, in order."""

    poly = primitive(poly)
    if degree(poly) <= 0:
        return ()
    bound = cauchy_bound(poly)
    low = _qneg(_qadd(bound, _ONE))
    high = _qadd(bound, _ONE)
    # Nudge endpoints off any roots at the bound (rationals already extracted usually).
    while eval_int(poly, low).num == 0:
        low = _qsub(low, _ONE)
    while eval_int(poly, high).num == 0:
        high = _qadd(high, _ONE)
    found: list[tuple[Ratio, Ratio]] = []
    _collect_intervals(poly, low, high, found)
    found.sort(key=lambda item: (_qcmp(item[0], _ZERO), item[0].num, item[0].den))
    from functools import cmp_to_key

    found.sort(key=cmp_to_key(lambda a, b: _qcmp(a[0], b[0]) or _qcmp(a[1], b[1])))
    return tuple(found)


def _collect_intervals(poly: Poly, low: Ratio, high: Ratio, found: list[tuple[Ratio, Ratio]]) -> None:
    count = sturm_count(poly, low, high)
    if count == 0:
        return
    if count == 1:
        # Tighten until the width is below 1, so neighbouring roots get disjoint intervals.
        width_limit = _q(1, 2)
        steps = 0
        while _qcmp(_qsub(high, low), width_limit) > 0 and steps < 64:
            mid = _mid(low, high)
            steps += 1
            if _qcmp(mid, low) <= 0 or _qcmp(mid, high) >= 0:
                break
            if eval_int(poly, mid).num == 0:
                break
            if sturm_count(poly, low, mid) == 1:
                high = mid
            else:
                low = mid
        found.append((low, high))
        return
    mid = _mid(low, high)
    if _qcmp(mid, low) <= 0 or _qcmp(mid, high) >= 0:
        if count == 1:
            found.append((low, high))
        return
    if eval_int(poly, mid).num == 0:
        # A rational root inside the interval: isolate it as a degenerate split.
        left_high = _mid(low, mid) if _qcmp(low, mid) < 0 else low
        # Shrink away from the root.
        left_end = _qdiv(_qadd(low, mid), _q(2, 1))
        # Use mid - eps and mid + eps with a small rational step.
        step = _q(1, mid.den * low.den * 2 or 2)
        left_end = _qsub(mid, step)
        right_start = _qadd(mid, step)
        if _qcmp(left_end, low) > 0:
            _collect_intervals(poly, low, left_end, found)
        if _qcmp(right_start, high) < 0:
            _collect_intervals(poly, right_start, high, found)
        return
    _collect_intervals(poly, low, mid, found)
    _collect_intervals(poly, mid, high, found)


def real_root_count(poly: Poly) -> int:
    return sturm_count(poly, None, None)


def show_poly(poly: Poly) -> str:
    poly = _trim_int(poly)
    if poly == (0,):
        return "0"
    pieces: list[str] = []
    for index, coeff in enumerate(poly):
        if coeff == 0:
            continue
        if index == 0:
            term = str(coeff)
        elif index == 1:
            if coeff == 1:
                term = "x"
            elif coeff == -1:
                term = "-x"
            else:
                term = f"{coeff} * x"
        else:
            if coeff == 1:
                term = f"x^{index}"
            elif coeff == -1:
                term = f"-x^{index}"
            else:
                term = f"{coeff} * x^{index}"
        pieces.append(term)
    if not pieces:
        return "0"
    body = pieces[-1]
    for term in reversed(pieces[:-1]):
        if term.startswith("-"):
            body = f"{body} - {term[1:]}"
        else:
            body = f"{body} + {term}"
    return body


@dataclass(frozen=True)
class AlgebraicReal:
    """The index-th real root of a primitive irreducible integer polynomial."""

    coeffs: Poly
    index: int

    def __post_init__(self) -> None:
        if not _algebraic_ok(self):
            raise KernelError("this algebraic number is not isolated by its minimal polynomial")

    @property
    def interval(self) -> tuple[Ratio, Ratio]:
        return isolate_interval(self.coeffs, self.index)


def _algebraic_ok(number: AlgebraicReal) -> bool:
    poly = primitive(number.coeffs)
    if poly != number.coeffs:
        return False
    if degree(poly) < 2:
        return False
    if degree(poly) > 64:
        return False
    if not _irreducible(poly):
        return False
    try:
        count = real_root_count(poly)
        if number.index < 1 or number.index > count:
            return False
        low, high = isolate_interval(poly, number.index)
    except (NotExact, KernelError):
        return False
    if _qcmp(low, high) >= 0:
        return False
    if eval_int(poly, low).num == 0 or eval_int(poly, high).num == 0:
        return False
    if sturm_count(poly, low, high) != 1:
        return False
    # A simple real root of an irreducible polynomial crosses zero.
    if _sign_of(eval_int(poly, low)) * _sign_of(eval_int(poly, high)) >= 0:
        return False
    return True


def show_algebraic(number: AlgebraicReal) -> str:
    return f"root({show_poly(number.coeffs)}, {number.index})"


def compare_algebraic(left: AlgebraicReal, right: AlgebraicReal) -> str:
    if left == right:
        return "eq"
    if left.coeffs == right.coeffs:
        if left.index < right.index:
            return "lt"
        if left.index > right.index:
            return "gt"
        return "eq"
    # Distinct monic/primitive irreducibles are coprime, so the roots differ.
    # Refine isolating intervals until they are disjoint.
    left_low, left_high = left.interval
    right_low, right_high = right.interval
    for _ in range(64):
        if _qcmp(left_high, right_low) <= 0:
            return "lt"
        if _qcmp(right_high, left_low) <= 0:
            return "gt"
        left_low, left_high = _refine(left.coeffs, left_low, left_high)
        right_low, right_high = _refine(right.coeffs, right_low, right_high)
    raise NotExact("these algebraic numbers could not be compared")


def compare_algebraic_to_ratio(number: AlgebraicReal, value: Ratio) -> str:
    # An irreducible of degree >= 2 has no rational root.
    low, high = number.interval
    if _qcmp(high, value) <= 0:
        return "lt"
    if _qcmp(value, low) <= 0:
        return "gt"
    for _ in range(64):
        low, high = _refine(number.coeffs, low, high)
        if _qcmp(high, value) <= 0:
            return "lt"
        if _qcmp(value, low) <= 0:
            return "gt"
    raise NotExact("this algebraic number could not be compared")


def _refine(poly: Poly, low: Ratio, high: Ratio) -> tuple[Ratio, Ratio]:
    mid = _mid(low, high)
    if _qcmp(mid, low) <= 0 or _qcmp(mid, high) >= 0:
        return low, high
    if eval_int(poly, mid).num == 0:
        return low, high
    if sturm_count(poly, low, mid) == 1:
        return low, mid
    return mid, high


def roots_of_rational_polynomial(poly: Poly) -> tuple[tuple[object, int], ...]:
    """Distinct real roots of a rational polynomial, with multiplicity.

    A rational root is a Ratio. An irrational root is an AlgebraicReal.
    Multiplicity comes from Yun factorization.
    """

    poly = primitive(poly)
    if degree(poly) <= 0:
        return ()
    if degree(poly) > POLY_DEGREE_LIMIT:
        raise NotExact("this polynomial stays outside this rule")
    found: list[tuple[object, int]] = []
    for factor, multiplicity in square_free_factors(poly):
        rationals, rest = extract_rational_roots(factor)
        for root, inner in rationals:
            if inner != 1:
                raise KernelError("a square-free factor had a repeated rational root")
            found.append((root, multiplicity))
        if degree(rest) <= 0:
            continue
        for irreducible in factor_square_free(rest):
            intervals = isolate_all(irreducible)
            if len(intervals) != real_root_count(irreducible):
                raise KernelError("Sturm isolation missed a real root")
            for index in range(1, len(intervals) + 1):
                found.append((AlgebraicReal(irreducible, index), multiplicity))
    from functools import cmp_to_key

    def _cmp(left: tuple[object, int], right: tuple[object, int]) -> int:
        return _cmp_root(left[0], right[0])

    found.sort(key=cmp_to_key(_cmp))
    return tuple(found)


def _cmp_root(left: object, right: object) -> int:
    if isinstance(left, Ratio) and isinstance(right, Ratio):
        return _qcmp(left, right)
    if isinstance(left, AlgebraicReal) and isinstance(right, AlgebraicReal):
        direction = compare_algebraic(left, right)
    elif isinstance(left, AlgebraicReal) and isinstance(right, Ratio):
        direction = compare_algebraic_to_ratio(left, right)
    elif isinstance(left, Ratio) and isinstance(right, AlgebraicReal):
        flipped = compare_algebraic_to_ratio(right, left)
        direction = {"lt": "gt", "gt": "lt", "eq": "eq"}[flipped]
    else:
        raise KernelError("an unexpected root kind")
    return {"lt": -1, "eq": 0, "gt": 1}[direction]


def leading_sign(poly: Poly) -> int:
    return 1 if leading(primitive(poly)) > 0 else -1


def sign_at(poly: Poly, value: Ratio) -> int:
    return _sign_of(eval_int(poly, value))
