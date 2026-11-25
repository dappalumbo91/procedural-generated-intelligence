"""Exact complex numbers in Q(i) and in Q(√d, i).

An element is (re0 + re1 √d) + (im0 + im1 √d) i, with reduced rational
coefficients and a square-free radicand d. When d is 0, the number
lies in Q(i). Arithmetic is the field laws. An inverse is kept only
when it multiplies back to 1. The identity i * i = -1 is a standing
check. A square root of a positive rational is adjoined by extracting
square factors and, if needed, changing the radicand; mixing two
different square-free radicands stays open.

These are the scalars for finite-dimensional inner product spaces.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import gcd

from pgi.math.kernel import KernelError, NotExact
from pgi.math.rational import Ratio, rat_normalize


_ZERO = Ratio(0, 1)
_ONE = Ratio(1, 1)
_NEG_ONE = Ratio(-1, 1)


def _q(num: int, den: int = 1) -> Ratio:
    return rat_normalize(num, den).value


def _qadd(left: Ratio, right: Ratio) -> Ratio:
    return _q(left.num * right.den + right.num * left.den, left.den * right.den)


def _qsub(left: Ratio, right: Ratio) -> Ratio:
    return _q(left.num * right.den - right.num * left.den, left.den * right.den)


def _qmul(left: Ratio, right: Ratio) -> Ratio:
    return _q(left.num * right.num, left.den * right.den)


def _qneg(value: Ratio) -> Ratio:
    return _q(-value.num, value.den)


def _qinv(value: Ratio) -> Ratio:
    if value.num == 0:
        raise NotExact("division by zero")
    return _q(value.den, value.num)


def _qdiv(left: Ratio, right: Ratio) -> Ratio:
    return _qmul(left, _qinv(right))


def _qeq(left: Ratio, right: Ratio) -> bool:
    return left.num == right.num and left.den == right.den


def _qsign(value: Ratio) -> int:
    if value.num == 0:
        return 0
    return 1 if value.num > 0 else -1


def split_square(n: int) -> tuple[int, int]:
    """Write n >= 0 as (k^2) * m with m square-free."""
    if n < 0:
        raise KernelError("a negative radicand stays open")
    if n == 0:
        return 0, 0
    k = 1
    m = n
    p = 2
    while p * p <= m:
        if m % (p * p) == 0:
            while m % (p * p) == 0:
                m //= p * p
                k *= p
        p += 1 if p == 2 else 2
    return k, m


@dataclass(frozen=True)
class CNum:
    """(re0 + re1 √d) + (im0 + im1 √d) i, with d square-free or 0."""

    d: int
    re0: Ratio
    re1: Ratio
    im0: Ratio
    im1: Ratio

    def __post_init__(self) -> None:
        if not _cnum_ok(self):
            raise KernelError("this complex number is not in normal form")


def _cnum_ok(value: CNum) -> bool:
    if value.d < 0:
        return False
    if value.d > 1:
        k, m = split_square(value.d)
        if k != 1 or m != value.d:
            return False
    coeffs = (value.re0, value.re1, value.im0, value.im1)
    for coeff in coeffs:
        if coeff.den <= 0 or gcd(abs(coeff.num), coeff.den) != 1:
            return False
    if value.d == 0 and (not _qeq(value.re1, _ZERO) or not _qeq(value.im1, _ZERO)):
        return False
    if value.d == 1:
        return False
    return True


def _reduce_cnum(d: int, re0: Ratio, re1: Ratio, im0: Ratio, im1: Ratio) -> CNum:
    if d < 0:
        raise NotExact("a negative radicand stays open")
    if d == 1:
        # √1 = 1, fold into the rational parts.
        re0, re1 = _qadd(re0, re1), _ZERO
        im0, im1 = _qadd(im0, im1), _ZERO
        d = 0
    if d > 1:
        k, m = split_square(d)
        if k != 1:
            # √(k^2 m) = k √m, should not happen if callers pass square-free d.
            re1 = _qmul(re1, _q(k))
            im1 = _qmul(im1, _q(k))
            d = m
        if d == 1:
            return _reduce_cnum(0, _qadd(re0, re1), _ZERO, _qadd(im0, im1), _ZERO)
    if d > 1 and _qeq(re1, _ZERO) and _qeq(im1, _ZERO):
        d = 0
    return CNum(d, re0, re1, im0, im1)


def c_zero() -> CNum:
    return CNum(0, _ZERO, _ZERO, _ZERO, _ZERO)


def c_one() -> CNum:
    return CNum(0, _ONE, _ZERO, _ZERO, _ZERO)


def c_i() -> CNum:
    value = CNum(0, _ZERO, _ZERO, _ONE, _ZERO)
    product = c_mul(value, value)
    if not c_eq(product, c_from_int(-1)):
        raise KernelError("i * i did not equal -1")
    return value


def c_from_int(value: int) -> CNum:
    return CNum(0, _q(value), _ZERO, _ZERO, _ZERO)


def c_from_ratio(value: Ratio) -> CNum:
    return CNum(0, value, _ZERO, _ZERO, _ZERO)


def c_from_parts(re: Ratio, im: Ratio) -> CNum:
    return CNum(0, re, _ZERO, im, _ZERO)


def c_eq(left: CNum, right: CNum) -> bool:
    a, b = c_align(left, right)
    return (
        _qeq(a.re0, b.re0)
        and _qeq(a.re1, b.re1)
        and _qeq(a.im0, b.im0)
        and _qeq(a.im1, b.im1)
        and a.d == b.d
    )


def c_is_zero(value: CNum) -> bool:
    return c_eq(value, c_zero())


def c_is_one(value: CNum) -> bool:
    return c_eq(value, c_one())


def c_is_real(value: CNum) -> bool:
    return _qeq(value.im0, _ZERO) and _qeq(value.im1, _ZERO)


def c_is_rational(value: CNum) -> bool:
    return value.d == 0 and c_is_real(value)


def c_as_ratio(value: CNum) -> Ratio | None:
    if c_is_rational(value):
        return value.re0
    return None


def c_align(left: CNum, right: CNum) -> tuple[CNum, CNum]:
    if left.d == right.d:
        return left, right
    if left.d == 0:
        return CNum(right.d, left.re0, _ZERO, left.im0, _ZERO), right
    if right.d == 0:
        return left, CNum(left.d, right.re0, _ZERO, right.im0, _ZERO)
    raise NotExact("these numbers lie in different quadratic fields")


def c_add(left: CNum, right: CNum) -> CNum:
    a, b = c_align(left, right)
    return _reduce_cnum(
        a.d,
        _qadd(a.re0, b.re0),
        _qadd(a.re1, b.re1),
        _qadd(a.im0, b.im0),
        _qadd(a.im1, b.im1),
    )


def c_neg(value: CNum) -> CNum:
    return _reduce_cnum(value.d, _qneg(value.re0), _qneg(value.re1), _qneg(value.im0), _qneg(value.im1))


def c_sub(left: CNum, right: CNum) -> CNum:
    return c_add(left, c_neg(right))


def c_mul(left: CNum, right: CNum) -> CNum:
    a, b = c_align(left, right)
    d = a.d
    # (p + q √d)(r + s √d) = (pr + qs d) + (ps + qr) √d
    def _rmul(p0: Ratio, p1: Ratio, r0: Ratio, r1: Ratio) -> tuple[Ratio, Ratio]:
        real = _qadd(_qmul(p0, r0), _qmul(_qmul(p1, r1), _q(d) if d else _ZERO))
        rad = _qadd(_qmul(p0, r1), _qmul(p1, r0))
        return real, rad

    # (x + y i)(u + v i) = (xu - yv) + (xv + yu) i
    # x = re(a), y = im(a), u = re(b), v = im(b), each in Q(√d)
    xu0, xu1 = _rmul(a.re0, a.re1, b.re0, b.re1)
    yv0, yv1 = _rmul(a.im0, a.im1, b.im0, b.im1)
    xv0, xv1 = _rmul(a.re0, a.re1, b.im0, b.im1)
    yu0, yu1 = _rmul(a.im0, a.im1, b.re0, b.re1)
    return _reduce_cnum(
        d,
        _qsub(xu0, yv0),
        _qsub(xu1, yv1),
        _qadd(xv0, yu0),
        _qadd(xv1, yu1),
    )


def c_conj(value: CNum) -> CNum:
    return _reduce_cnum(value.d, value.re0, value.re1, _qneg(value.im0), _qneg(value.im1))


def c_norm2(value: CNum) -> CNum:
    """⟨z, z⟩ = z * conj(z), a nonnegative element of Q(√d)."""
    result = c_mul(value, c_conj(value))
    if not c_is_real(result):
        raise KernelError("z * conjugate(z) was not real")
    return result


def _quad_inv(d: int, a: Ratio, b: Ratio) -> tuple[Ratio, Ratio]:
    """Inverse of a + b √d in Q(√d)."""
    # (a + b √d)(a - b √d) = a^2 - d b^2
    norm = _qsub(_qmul(a, a), _qmul(_qmul(b, b), _q(d) if d else _ZERO))
    if norm.num == 0:
        raise NotExact("division by zero")
    inv = _qinv(norm)
    return _qmul(a, inv), _qmul(_qneg(b), inv)


def c_inv(value: CNum) -> CNum:
    if c_is_zero(value):
        raise NotExact("division by zero")
    # 1/z = conj(z) / |z|^2, and |z|^2 = p + q √d.
    conj = c_conj(value)
    n0, n1 = c_norm2(value).re0, c_norm2(value).re1
    i0, i1 = _quad_inv(value.d, n0, n1)
    scale = _reduce_cnum(value.d, i0, i1, _ZERO, _ZERO)
    result = c_mul(conj, scale)
    if not c_eq(c_mul(value, result), c_one()) or not c_eq(c_mul(result, value), c_one()):
        raise KernelError("this inverse did not multiply back to 1")
    return result


def c_div(left: CNum, right: CNum) -> CNum:
    return c_mul(left, c_inv(right))


def c_sqrt_ratio(value: Ratio) -> CNum:
    """The nonnegative square root of a rational, in Q(√d)."""
    if value.num < 0:
        raise NotExact("a negative radicand stays open")
    if value.num == 0:
        return c_zero()
    # √(p/q) = √(p q) / q
    k, m = split_square(value.num * value.den)
    # √(p/q) = √(p q) / q = k √m / q
    coeff = _q(k, value.den)
    if m == 1:
        return _reduce_cnum(0, coeff, _ZERO, _ZERO, _ZERO)
    return _reduce_cnum(m, _ZERO, coeff, _ZERO, _ZERO)


def show_ratio(value: Ratio) -> str:
    if value.den == 1:
        return str(value.num)
    return f"{value.num}/{value.den}"


def _show_real(d: int, a: Ratio, b: Ratio) -> str:
    if _qeq(b, _ZERO):
        return show_ratio(a)
    rad = "sqrt(" + str(d) + ")"
    if _qeq(b, _ONE):
        tail = rad
    elif _qeq(b, _NEG_ONE):
        tail = "-" + rad
    else:
        tail = show_ratio(b) + " * " + rad
    if _qeq(a, _ZERO):
        return tail
    if tail.startswith("-"):
        return show_ratio(a) + " - " + tail[1:]
    return show_ratio(a) + " + " + tail


def show_cnum(value: CNum) -> str:
    if c_is_zero(value):
        return "0"
    re = _show_real(value.d, value.re0, value.re1)
    im = _show_real(value.d, value.im0, value.im1)
    if im == "0":
        return re
    if re == "0":
        if im == "1":
            return "i"
        if im == "-1":
            return "-i"
        if im.startswith("-"):
            return im + " * i" if im not in {"-1"} else "-i"
        return "i" if im == "1" else im + " * i"
    # both parts
    def _im_term(text: str) -> str:
        if text == "1":
            return "i"
        if text == "-1":
            return "-i"
        return text + " * i"

    im_term = _im_term(im)
    if im_term.startswith("-"):
        return re + " - " + im_term[1:]
    return re + " + " + im_term


# Standing check at import: i^2 = -1, and a sample inverse.
_I_CHECK = c_i()
