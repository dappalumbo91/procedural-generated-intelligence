"""Exact complex numbers in Q(i) and in Q(√d, i).

An element is (re0 + re1 √d) + (im0 + im1 √d) i, with reduced rational
coefficients and a square-free radicand d. When d is 0, the number
lies in Q(i). A second coprime square-free radicand e may be adjoined,
so the number lies in Q(√d, √e, i) with basis 1, √d, √e, √(de).
Arithmetic is the field laws. An inverse is kept only when it
multiplies back to 1. The identity i * i = -1 is a standing check.
A square root of a positive rational is adjoined by extracting square
factors and, if needed, changing the radicand. Mixing three or more independent
square-free radicands, or two that do not lie in one coprime
biquadratic field Q(√d, √e), stays open. √d, √e, and √(de) are
the same field.

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
    """A number in Q(i), Q(√d, i), or Q(√d, √e, i).

    The quadratic case is (re0 + re1 √d) + (im0 + im1 √d) i.
    When e > 1, the basis is 1, √d, √e, √(de), with coefficients
    re2, re3 and im2, im3.
    """

    d: int
    re0: Ratio
    re1: Ratio
    im0: Ratio
    im1: Ratio
    e: int = 0
    re2: Ratio = _ZERO
    re3: Ratio = _ZERO
    im2: Ratio = _ZERO
    im3: Ratio = _ZERO

    def __post_init__(self) -> None:
        if not _cnum_ok(self):
            raise KernelError("this complex number is not in normal form")


def _cnum_ok(value: CNum) -> bool:
    if value.d < 0 or value.e < 0:
        return False
    if value.d > 1:
        k, m = split_square(value.d)
        if k != 1 or m != value.d:
            return False
    if value.e > 1:
        k, m = split_square(value.e)
        if k != 1 or m != value.e:
            return False
        if value.d <= 1 or value.e == value.d or value.d >= value.e:
            return False
        if gcd(value.d, value.e) != 1:
            return False
    coeffs = (value.re0, value.re1, value.im0, value.im1, value.re2, value.re3, value.im2, value.im3)
    for coeff in coeffs:
        if coeff.den <= 0 or gcd(abs(coeff.num), coeff.den) != 1:
            return False
    if value.d == 0 and (not _qeq(value.re1, _ZERO) or not _qeq(value.im1, _ZERO)):
        return False
    if value.e == 0 and (not _qeq(value.re2, _ZERO) or not _qeq(value.re3, _ZERO) or not _qeq(value.im2, _ZERO) or not _qeq(value.im3, _ZERO)):
        return False
    if value.d == 1 or value.e == 1:
        return False
    return True


def _reduce_cnum(d: int, re0: Ratio, re1: Ratio, im0: Ratio, im1: Ratio, e: int = 0, re2: Ratio = _ZERO, re3: Ratio = _ZERO, im2: Ratio = _ZERO, im3: Ratio = _ZERO, keep: bool = False) -> CNum:
    if d < 0 or e < 0:
        raise NotExact("a negative radicand stays open")
    if d == 1:
        re0, re1 = _qadd(re0, re1), _ZERO
        im0, im1 = _qadd(im0, im1), _ZERO
        # √1 * √e = √e, so re3, im3 fold into re2, im2.
        re2, re3 = _qadd(re2, re3), _ZERO
        im2, im3 = _qadd(im2, im3), _ZERO
        d = 0
    if e == 1:
        re0, re2 = _qadd(re0, re2), _ZERO
        im0, im2 = _qadd(im0, im2), _ZERO
        re1, re3 = _qadd(re1, re3), _ZERO
        im1, im3 = _qadd(im1, im3), _ZERO
        e = 0
    if d > 1:
        k, m = split_square(d)
        if k != 1:
            re1 = _qmul(re1, _q(k))
            im1 = _qmul(im1, _q(k))
            re3 = _qmul(re3, _q(k))
            im3 = _qmul(im3, _q(k))
            d = m
        if d == 1:
            return _reduce_cnum(0, _qadd(re0, re1), _ZERO, _qadd(im0, im1), _ZERO, e, _qadd(re2, re3), _ZERO, _qadd(im2, im3), _ZERO)
    if e > 1:
        k, m = split_square(e)
        if k != 1:
            re2 = _qmul(re2, _q(k))
            im2 = _qmul(im2, _q(k))
            re3 = _qmul(re3, _q(k))
            im3 = _qmul(im3, _q(k))
            e = m
        if e == 1:
            return _reduce_cnum(d, _qadd(re0, re2), re1, _qadd(im0, im2), im1, 0, _ZERO, _ZERO, _ZERO, _ZERO)
    # Canonical order d < e when both present.
    if d > 1 and e > 1 and d > e:
        d, e = e, d
        re1, re2 = re2, re1
        im1, im2 = im2, im1
    if e > 1 and (d <= 1 or d == e or gcd(d, e) != 1):
        raise NotExact("these numbers lie in different quadratic fields")
    if not keep:
        if e > 1 and _qeq(re2, _ZERO) and _qeq(re3, _ZERO) and _qeq(im2, _ZERO) and _qeq(im3, _ZERO):
            e = 0
        if d > 1 and e == 0 and _qeq(re1, _ZERO) and _qeq(im1, _ZERO):
            d = 0
        if d > 1 and e > 1 and _qeq(re1, _ZERO) and _qeq(re3, _ZERO) and _qeq(im1, _ZERO) and _qeq(im3, _ZERO):
            # Only √e remains: drop d and move e into d.
            return _reduce_cnum(e, re0, re2, im0, im2)
        if d > 1 and e > 1 and _qeq(re1, _ZERO) and _qeq(re2, _ZERO) and _qeq(im1, _ZERO) and _qeq(im2, _ZERO):
            # Only 1 and √(de) remain: drop to Q(√(de)).
            return _reduce_cnum(d * e, re0, re3, im0, im3)
        if d == 0 and e > 1:
            return _reduce_cnum(e, re0, re2, im0, im2)
        if e == 0:
            re2 = im2 = re3 = im3 = _ZERO
    return CNum(d, re0, re1, im0, im1, e, re2, re3, im2, im3)


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
        and _qeq(a.re2, b.re2)
        and _qeq(a.re3, b.re3)
        and _qeq(a.im2, b.im2)
        and _qeq(a.im3, b.im3)
        and a.d == b.d
        and a.e == b.e
    )


def c_is_zero(value: CNum) -> bool:
    return c_eq(value, c_zero())


def c_is_one(value: CNum) -> bool:
    return c_eq(value, c_one())


def c_is_real(value: CNum) -> bool:
    return _qeq(value.im0, _ZERO) and _qeq(value.im1, _ZERO) and _qeq(value.im2, _ZERO) and _qeq(value.im3, _ZERO)


def c_is_rational(value: CNum) -> bool:
    return value.d == 0 and value.e == 0 and c_is_real(value)


def c_as_ratio(value: CNum) -> Ratio | None:
    if c_is_rational(value):
        return value.re0
    return None


def _radicands(value: CNum) -> tuple[int, ...]:
    if value.e > 1:
        return (value.d, value.e)
    if value.d > 1:
        return (value.d,)
    return ()


def _compositum(rads: set[int]) -> tuple[int, int]:
    """A coprime pair (d, e) generating the same field, or (d, 0).

    √d, √e, and √(de) with gcd(d, e) = 1 are one biquadratic field.
    Two radicands where one is the other times a coprime square-free
    k are Q(√a, √k). Anything else stays open.
    """
    rads = {rad for rad in rads if rad > 1}
    if not rads:
        return 0, 0
    if len(rads) == 1:
        return next(iter(rads)), 0

    def pair_from(a: int, b: int) -> tuple[int, int] | None:
        if a > b:
            a, b = b, a
        if gcd(a, b) == 1:
            return a, b
        if b % a == 0:
            k = b // a
            if k > 1 and gcd(a, k) == 1:
                return (a, k) if a < k else (k, a)
        return None

    if len(rads) == 2:
        a, b = tuple(rads)
        got = pair_from(a, b)
        if got is None:
            raise NotExact("these numbers lie in different quadratic fields")
        return got
    if len(rads) == 3:
        items = tuple(rads)
        for i in range(3):
            for j in range(i + 1, 3):
                a, b = items[i], items[j]
                c = next(iter(rads - {a, b}))
                if gcd(a, b) == 1 and a * b == c:
                    return (a, b) if a < b else (b, a)
        raise NotExact("these numbers lie in different quadratic fields")
    raise NotExact("these numbers lie in different quadratic fields")


def _in_field(rad: int, d: int, e: int) -> bool:
    if rad <= 1:
        return True
    if rad == d:
        return True
    return e > 1 and (rad == e or rad == d * e)


def _lift_to(value: CNum, d: int, e: int) -> CNum:
    for rad in _radicands(value):
        if not _in_field(rad, d, e):
            raise NotExact("these numbers lie in different quadratic fields")
    if value.e > 1:
        if value.d == d and value.e == e:
            return value
        raise NotExact("these numbers lie in different quadratic fields")
    if value.d == 0:
        return _reduce_cnum(d, value.re0, _ZERO, value.im0, _ZERO, e, keep=True)
    re0, re1, re2, re3 = value.re0, _ZERO, _ZERO, _ZERO
    im0, im1, im2, im3 = value.im0, _ZERO, _ZERO, _ZERO
    if value.d == d:
        re1, im1 = value.re1, value.im1
    elif e > 1 and value.d == e:
        re2, im2 = value.re1, value.im1
    elif e > 1 and value.d == d * e:
        re3, im3 = value.re1, value.im1
    else:
        raise NotExact("these numbers lie in different quadratic fields")
    return _reduce_cnum(d, re0, re1, im0, im1, e, re2, re3, im2, im3, keep=True)


def c_align(left: CNum, right: CNum) -> tuple[CNum, CNum]:
    if left.d == right.d and left.e == right.e:
        return left, right
    d, e = _compositum(set(_radicands(left)) | set(_radicands(right)))
    if d == 0:
        return left, right
    return _lift_to(left, d, e), _lift_to(right, d, e)


def c_add(left: CNum, right: CNum) -> CNum:
    a, b = c_align(left, right)
    return _reduce_cnum(
        a.d,
        _qadd(a.re0, b.re0),
        _qadd(a.re1, b.re1),
        _qadd(a.im0, b.im0),
        _qadd(a.im1, b.im1),
        a.e,
        _qadd(a.re2, b.re2),
        _qadd(a.re3, b.re3),
        _qadd(a.im2, b.im2),
        _qadd(a.im3, b.im3),
    )


def c_neg(value: CNum) -> CNum:
    return _reduce_cnum(
        value.d,
        _qneg(value.re0),
        _qneg(value.re1),
        _qneg(value.im0),
        _qneg(value.im1),
        value.e,
        _qneg(value.re2),
        _qneg(value.re3),
        _qneg(value.im2),
        _qneg(value.im3),
    )


def c_sub(left: CNum, right: CNum) -> CNum:
    return c_add(left, c_neg(right))


def _rmul4(left: tuple[Ratio, Ratio, Ratio, Ratio], right: tuple[Ratio, Ratio, Ratio, Ratio], d: int, e: int) -> tuple[Ratio, Ratio, Ratio, Ratio]:
    """Product in Q(√d, √e) with basis 1, √d, √e, √(de)."""
    # √d * √d = d, √e * √e = e, √d * √e = √(de), √d * √(de) = d √e, √e * √(de) = e √d, √(de)*√(de) = d e
    a0, a1, a2, a3 = left
    b0, b1, b2, b3 = right
    qd = _q(d) if d else _ZERO
    qe = _q(e) if e else _ZERO
    qde = _qmul(qd, qe)

    def acc(parts):
        total = _ZERO
        for part in parts:
            total = _qadd(total, part)
        return total

    c0 = acc((_qmul(a0, b0), _qmul(_qmul(a1, b1), qd), _qmul(_qmul(a2, b2), qe), _qmul(_qmul(a3, b3), qde)))
    c1 = acc((_qmul(a0, b1), _qmul(a1, b0), _qmul(_qmul(a2, b3), qe), _qmul(_qmul(a3, b2), qe)))
    c2 = acc((_qmul(a0, b2), _qmul(a2, b0), _qmul(_qmul(a1, b3), qd), _qmul(_qmul(a3, b1), qd)))
    c3 = acc((_qmul(a0, b3), _qmul(a3, b0), _qmul(a1, b2), _qmul(a2, b1)))
    return c0, c1, c2, c3


def c_mul(left: CNum, right: CNum) -> CNum:
    a, b = c_align(left, right)
    # (x + y i)(u + v i) = (xu - yv) + (xv + yu) i, each of x,y,u,v in Q(√d, √e)
    xu = _rmul4((a.re0, a.re1, a.re2, a.re3), (b.re0, b.re1, b.re2, b.re3), a.d, a.e)
    yv = _rmul4((a.im0, a.im1, a.im2, a.im3), (b.im0, b.im1, b.im2, b.im3), a.d, a.e)
    xv = _rmul4((a.re0, a.re1, a.re2, a.re3), (b.im0, b.im1, b.im2, b.im3), a.d, a.e)
    yu = _rmul4((a.im0, a.im1, a.im2, a.im3), (b.re0, b.re1, b.re2, b.re3), a.d, a.e)
    return _reduce_cnum(
        a.d,
        _qsub(xu[0], yv[0]),
        _qsub(xu[1], yv[1]),
        _qadd(xv[0], yu[0]),
        _qadd(xv[1], yu[1]),
        a.e,
        _qsub(xu[2], yv[2]),
        _qsub(xu[3], yv[3]),
        _qadd(xv[2], yu[2]),
        _qadd(xv[3], yu[3]),
    )


def c_conj(value: CNum) -> CNum:
    return _reduce_cnum(
        value.d,
        value.re0,
        value.re1,
        _qneg(value.im0),
        _qneg(value.im1),
        value.e,
        value.re2,
        value.re3,
        _qneg(value.im2),
        _qneg(value.im3),
    )


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


def _flip_d(value: CNum) -> CNum:
    return _reduce_cnum(
        value.d,
        value.re0,
        _qneg(value.re1),
        value.im0,
        _qneg(value.im1),
        value.e,
        value.re2,
        _qneg(value.re3),
        value.im2,
        _qneg(value.im3),
    )


def _flip_e(value: CNum) -> CNum:
    return _reduce_cnum(
        value.d,
        value.re0,
        value.re1,
        value.im0,
        value.im1,
        value.e,
        _qneg(value.re2),
        _qneg(value.re3),
        _qneg(value.im2),
        _qneg(value.im3),
    )


def c_inv(value: CNum) -> CNum:
    if c_is_zero(value):
        raise NotExact("division by zero")
    # 1/z = conj(z) / |z|^2.
    conj = c_conj(value)
    norm = c_norm2(value)
    if norm.e == 0:
        i0, i1 = _quad_inv(norm.d, norm.re0, norm.re1)
        scale = _reduce_cnum(norm.d, i0, i1, _ZERO, _ZERO)
    else:
        # Invert the real biquadratic norm by the Galois product of conjugates.
        galois = c_mul(c_mul(_flip_d(norm), _flip_e(norm)), _flip_e(_flip_d(norm)))
        total = c_mul(norm, galois)
        if not c_is_rational(total) or total.re0.num == 0:
            raise KernelError("the biquadratic norm was not a nonzero rational")
        scale = c_mul(galois, c_from_ratio(_qinv(total.re0)))
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


def _show_term(coeff: Ratio, rad: str) -> str:
    if _qeq(coeff, _ZERO):
        return ""
    if rad == "":
        return show_ratio(coeff)
    if _qeq(coeff, _ONE):
        return rad
    if _qeq(coeff, _NEG_ONE):
        return "-" + rad
    return show_ratio(coeff) + " * " + rad


def _join_terms(parts: list[str]) -> str:
    parts = [part for part in parts if part]
    if not parts:
        return "0"
    out = parts[0]
    for part in parts[1:]:
        if part.startswith("-"):
            out += " - " + part[1:]
        else:
            out += " + " + part
    return out


def _show_real(value: CNum, imag: bool) -> str:
    if imag:
        coeffs = (value.im0, value.im1, value.im2, value.im3)
    else:
        coeffs = (value.re0, value.re1, value.re2, value.re3)
    rads = ["", f"sqrt({value.d})" if value.d > 1 else "", f"sqrt({value.e})" if value.e > 1 else "", f"sqrt({value.d * value.e})" if value.d > 1 and value.e > 1 else ""]
    return _join_terms([_show_term(coeff, rad) for coeff, rad in zip(coeffs, rads)])


def show_cnum(value: CNum) -> str:
    if c_is_zero(value):
        return "0"
    re = _show_real(value, False)
    im = _show_real(value, True)
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
