"""Exact complex numbers in Q(i) and in a radical tower of height at most 3.

An element is an exact point of Q(i), of Q(√d, i) for a square-free d, of
the biquadratic field Q(√d, √e, i), or of the tri-quadratic tower
Q(√d, √e, √f, i), for pairwise coprime square-free integers 1 < d < e < f.
The real basis is the eight products of 1, √d, √e, and √f, and the same
with a factor of i. Arithmetic is the field laws. An inverse is kept
only when both products are 1. The identity i * i = -1 is a standing
check. A square root is kept for a nonnegative rational, written
k √m / q after splitting off square factors, or for a nonnegative field
element that denests in a tower of this kind (including a square already
in the field). Four or more independent square-free radicands, or a
compositum that is not a pairwise-coprime radical tower, stay open.

These are the scalars for finite-dimensional inner product spaces.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import gcd
from typing import Iterable

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
    """A number in Q(i), Q(√d, i), Q(√d, √e, i), or Q(√d, √e, √f, i).

    The quadratic case is (re0 + re1 √d) + (im0 + im1 √d) i.
    When e > 1, the biquadratic basis is 1, √d, √e, √(de), with
    coefficients re2, re3 and im2, im3. When f > 1, the remaining
    four real basis elements are √f, √(d f), √(e f), √(d e f), with
    coefficients re4..re7 and im4..im7.
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
    f: int = 0
    re4: Ratio = _ZERO
    re5: Ratio = _ZERO
    re6: Ratio = _ZERO
    re7: Ratio = _ZERO
    im4: Ratio = _ZERO
    im5: Ratio = _ZERO
    im6: Ratio = _ZERO
    im7: Ratio = _ZERO

    def __post_init__(self) -> None:
        if not _cnum_ok(self):
            raise KernelError("this complex number is not in normal form")


def _square_free_ok(value: int) -> bool:
    if value <= 1:
        return value == 0
    k, m = split_square(value)
    return k == 1 and m == value


def _pairwise_coprime(*values: int) -> bool:
    present = [value for value in values if value > 1]
    for i, left in enumerate(present):
        for right in present[i + 1 :]:
            if gcd(left, right) != 1:
                return False
    return True


def _cnum_ok(value: CNum) -> bool:
    if value.d < 0 or value.e < 0 or value.f < 0:
        return False
    if value.d > 1 and not _square_free_ok(value.d):
        return False
    if value.e > 1 and not _square_free_ok(value.e):
        return False
    if value.f > 1 and not _square_free_ok(value.f):
        return False
    if value.e > 1 and (value.d <= 1 or value.e == value.d or value.d >= value.e):
        return False
    if value.f > 1 and (value.e <= 1 or value.f <= value.e):
        return False
    if not _pairwise_coprime(value.d, value.e, value.f):
        return False
    coeffs = (
        value.re0, value.re1, value.im0, value.im1,
        value.re2, value.re3, value.im2, value.im3,
        value.re4, value.re5, value.re6, value.re7,
        value.im4, value.im5, value.im6, value.im7,
    )
    for coeff in coeffs:
        if coeff.den <= 0 or gcd(abs(coeff.num), coeff.den) != 1:
            return False
    if value.d == 0 and (not _qeq(value.re1, _ZERO) or not _qeq(value.im1, _ZERO)):
        return False
    if value.e == 0 and (not _qeq(value.re2, _ZERO) or not _qeq(value.re3, _ZERO) or not _qeq(value.im2, _ZERO) or not _qeq(value.im3, _ZERO)):
        return False
    if value.f == 0 and (
        not _qeq(value.re4, _ZERO) or not _qeq(value.re5, _ZERO) or not _qeq(value.re6, _ZERO) or not _qeq(value.re7, _ZERO)
        or not _qeq(value.im4, _ZERO) or not _qeq(value.im5, _ZERO) or not _qeq(value.im6, _ZERO) or not _qeq(value.im7, _ZERO)
    ):
        return False
    if value.d == 1 or value.e == 1 or value.f == 1:
        return False
    return True


def _slot_active(d: int, e: int, f: int, slot: int) -> bool:
    if (slot & 1) and d <= 1:
        return False
    if (slot & 2) and e <= 1:
        return False
    if (slot & 4) and f <= 1:
        return False
    return True


def _basis_product(d: int, e: int, f: int, slot: int) -> int:
    if not _slot_active(d, e, f, slot):
        return 0
    acc = 1
    if slot & 1:
        acc *= d
    if slot & 2:
        acc *= e
    if slot & 4:
        acc *= f
    return acc


def _slot_map(d: int, e: int, f: int) -> dict[int, int]:
    mapping: dict[int, int] = {}
    for slot in range(8):
        if not _slot_active(d, e, f, slot):
            continue
        product = _basis_product(d, e, f, slot)
        if product in mapping:
            raise KernelError("a radical basis assigned one product twice")
        mapping[product] = slot
    return mapping


def _swap_slot_bits(slot: int, bit_a: int, bit_b: int) -> int:
    left = (slot >> bit_a) & 1
    right = (slot >> bit_b) & 1
    if left == right:
        return slot
    return slot ^ ((1 << bit_a) | (1 << bit_b))


def _swap_axis(re: list[Ratio], im: list[Ratio], bit_a: int, bit_b: int) -> tuple[list[Ratio], list[Ratio]]:
    new_re = [_ZERO] * 8
    new_im = [_ZERO] * 8
    for slot in range(8):
        dest = _swap_slot_bits(slot, bit_a, bit_b)
        new_re[dest] = re[slot]
        new_im[dest] = im[slot]
    return new_re, new_im


def _split_axis(re: list[Ratio], im: list[Ratio], bit: int, value: int) -> tuple[list[Ratio], list[Ratio], int]:
    """Write value = k^2 * m and fold the square factor into the coefficients."""
    if value <= 1:
        return re, im, 0 if value == 1 else value
    k, m = split_square(value)
    if k != 1:
        re = list(re)
        im = list(im)
        scale = _q(k)
        for slot in range(8):
            if slot & (1 << bit):
                re[slot] = _qmul(re[slot], scale)
                im[slot] = _qmul(im[slot], scale)
        value = m
    if value == 1:
        new_re = [_ZERO] * 8
        new_im = [_ZERO] * 8
        for slot in range(8):
            dest = slot & ~(1 << bit)
            new_re[dest] = _qadd(new_re[dest], re[slot])
            new_im[dest] = _qadd(new_im[dest], im[slot])
        return new_re, new_im, 0
    return re, im, value


def _sort_axes(d: int, e: int, f: int, re: list[Ratio], im: list[Ratio]) -> tuple[int, int, int, list[Ratio], list[Ratio]]:
    def key(value: int) -> int:
        return value if value > 1 else 10 ** 18

    if key(d) > key(e):
        d, e = e, d
        re, im = _swap_axis(re, im, 0, 1)
    if key(e) > key(f):
        e, f = f, e
        re, im = _swap_axis(re, im, 1, 2)
    if key(d) > key(e):
        d, e = e, d
        re, im = _swap_axis(re, im, 0, 1)
    return d, e, f, re, im


def _primes_of(n: int) -> frozenset[int]:
    if n <= 1:
        return frozenset()
    factors: list[int] = []
    remaining = n
    prime = 2
    while prime * prime <= remaining:
        if remaining % prime == 0:
            factors.append(prime)
            remaining //= prime
            if remaining % prime == 0:
                raise NotExact("a radicand was not square-free")
        prime = prime + 1 if prime == 2 else prime + 2
    if remaining > 1:
        factors.append(remaining)
    return frozenset(factors)


def _product_of(primes: Iterable[int]) -> int:
    acc = 1
    for prime in primes:
        acc *= prime
    return acc


def _radical_basis(rads: set[int]) -> tuple[int, ...]:
    """F2-span basis of square-free radicands, of rank at most 3."""
    present = {rad for rad in rads if rad > 1}
    if not present:
        return ()
    vecs = [_primes_of(rad) for rad in sorted(present)]
    all_primes = sorted(set().union(*vecs))
    mat = [set(vec) for vec in vecs]
    used: set[int] = set()
    reduced: list[set[int]] = []
    for prime in all_primes:
        pivot = None
        for i, row in enumerate(mat):
            if i in used:
                continue
            if prime in row:
                pivot = i
                break
        if pivot is None:
            continue
        used.add(pivot)
        for j, row in enumerate(mat):
            if j != pivot and prime in row:
                mat[j] = mat[j] ^ mat[pivot]
        reduced.append(set(mat[pivot]))
    if len(reduced) > 3:
        raise NotExact("four independent square-free radicands stay open")
    basis = tuple(sorted(_product_of(row) for row in reduced if row))
    if len(basis) >= 2 and not _pairwise_coprime(*basis):
        # The even subfield Q(√6, √10, √15) is not a coprime biquadratic, but
        # it sits inside the coprime tower on the primes that appear.
        primes = sorted(set().union(*(_primes_of(rad) for rad in present)))
        if len(primes) > 3:
            raise NotExact("four independent square-free radicands stay open")
        return tuple(primes)
    return basis


def _pad_basis(basis: tuple[int, ...]) -> tuple[int, int, int]:
    padded = list(basis) + [0, 0, 0]
    return padded[0], padded[1], padded[2]


def _from_slots(d: int, e: int, f: int, re: list[Ratio], im: list[Ratio], keep: bool) -> CNum:
    if d < 0 or e < 0 or f < 0:
        raise NotExact("a negative radicand stays open")
    re = list(re)
    im = list(im)
    re, im, d = _split_axis(re, im, 0, d)
    re, im, e = _split_axis(re, im, 1, e)
    re, im, f = _split_axis(re, im, 2, f)
    d, e, f, re, im = _sort_axes(d, e, f, re, im)
    if not keep:
        terms: dict[int, tuple[Ratio, Ratio]] = {}
        for slot in range(8):
            if _qeq(re[slot], _ZERO) and _qeq(im[slot], _ZERO):
                continue
            if not _slot_active(d, e, f, slot):
                raise KernelError("a coefficient sat on an inactive radical slot")
            product = _basis_product(d, e, f, slot)
            if product > 1:
                k, m = split_square(product)
                if k != 1:
                    re[slot] = _qmul(re[slot], _q(k))
                    im[slot] = _qmul(im[slot], _q(k))
                    product = m
            prev = terms.get(product, (_ZERO, _ZERO))
            terms[product] = (_qadd(prev[0], re[slot]), _qadd(prev[1], im[slot]))
        used = {prod for prod, coeff in terms.items() if not _qeq(coeff[0], _ZERO) or not _qeq(coeff[1], _ZERO)}
        nd, ne, nf = _pad_basis(_radical_basis(used))
        slot_of = _slot_map(nd, ne, nf)
        new_re = [_ZERO] * 8
        new_im = [_ZERO] * 8
        for product, (re_c, im_c) in terms.items():
            if _qeq(re_c, _ZERO) and _qeq(im_c, _ZERO):
                continue
            if product not in slot_of:
                raise KernelError("a reduced term was not on the compositum basis")
            slot = slot_of[product]
            new_re[slot] = re_c
            new_im[slot] = im_c
        d, e, f, re, im = nd, ne, nf, new_re, new_im
    elif not _pairwise_coprime(d, e, f) or (e > 1 and d <= 1) or (f > 1 and e <= 1) or (e > 1 and d >= e) or (f > 1 and e >= f):
        raise NotExact("these numbers lie in different quadratic fields")
    value = CNum(
        d, re[0], re[1], im[0], im[1],
        e, re[2], re[3], im[2], im[3],
        f, re[4], re[5], re[6], re[7],
        im[4], im[5], im[6], im[7],
    )
    if not _cnum_ok(value):
        raise KernelError("a complex number left the allowed tower")
    return value


def _reduce_cnum(
    d: int,
    re0: Ratio,
    re1: Ratio,
    im0: Ratio,
    im1: Ratio,
    e: int = 0,
    re2: Ratio = _ZERO,
    re3: Ratio = _ZERO,
    im2: Ratio = _ZERO,
    im3: Ratio = _ZERO,
    f: int = 0,
    re4: Ratio = _ZERO,
    re5: Ratio = _ZERO,
    re6: Ratio = _ZERO,
    re7: Ratio = _ZERO,
    im4: Ratio = _ZERO,
    im5: Ratio = _ZERO,
    im6: Ratio = _ZERO,
    im7: Ratio = _ZERO,
    keep: bool = False,
) -> CNum:
    re = [re0, re1, re2, re3, re4, re5, re6, re7]
    im = [im0, im1, im2, im3, im4, im5, im6, im7]
    return _from_slots(d, e, f, re, im, keep)


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
        and _qeq(a.re4, b.re4)
        and _qeq(a.re5, b.re5)
        and _qeq(a.re6, b.re6)
        and _qeq(a.re7, b.re7)
        and _qeq(a.im4, b.im4)
        and _qeq(a.im5, b.im5)
        and _qeq(a.im6, b.im6)
        and _qeq(a.im7, b.im7)
        and a.d == b.d
        and a.e == b.e
        and a.f == b.f
    )


def c_is_zero(value: CNum) -> bool:
    return c_eq(value, c_zero())


def c_is_one(value: CNum) -> bool:
    return c_eq(value, c_one())


def c_is_real(value: CNum) -> bool:
    return (
        _qeq(value.im0, _ZERO) and _qeq(value.im1, _ZERO) and _qeq(value.im2, _ZERO) and _qeq(value.im3, _ZERO)
        and _qeq(value.im4, _ZERO) and _qeq(value.im5, _ZERO) and _qeq(value.im6, _ZERO) and _qeq(value.im7, _ZERO)
    )


def c_is_rational(value: CNum) -> bool:
    return value.d == 0 and value.e == 0 and value.f == 0 and c_is_real(value)


def c_as_ratio(value: CNum) -> Ratio | None:
    if c_is_rational(value):
        return value.re0
    return None


def _radicands(value: CNum) -> tuple[int, ...]:
    found: list[int] = []
    if value.d > 1:
        found.append(value.d)
    if value.e > 1:
        found.append(value.e)
    if value.f > 1:
        found.append(value.f)
    return tuple(found)


def _compositum(rads: set[int]) -> tuple[int, int, int]:
    """A pairwise-coprime triple (d, e, f) generating the same radical tower."""
    return _pad_basis(_radical_basis(rads))


def _in_field(rad: int, d: int, e: int, f: int) -> bool:
    if rad <= 1:
        return True
    products = {_basis_product(d, e, f, slot) for slot in range(8)}
    return rad in products


def _lift_to(value: CNum, d: int, e: int, f: int = 0) -> CNum:
    for rad in _radicands(value):
        if not _in_field(rad, d, e, f):
            raise NotExact("these numbers lie in different quadratic fields")
    if value.d == d and value.e == e and value.f == f:
        return value
    re = [_ZERO] * 8
    im = [_ZERO] * 8
    slot_of = _slot_map(d, e, f)
    src = (
        (value.re0, value.re1, value.re2, value.re3, value.re4, value.re5, value.re6, value.re7),
        (value.im0, value.im1, value.im2, value.im3, value.im4, value.im5, value.im6, value.im7),
    )
    for slot in range(8):
        product = _basis_product(value.d, value.e, value.f, slot)
        re_c, im_c = src[0][slot], src[1][slot]
        if _qeq(re_c, _ZERO) and _qeq(im_c, _ZERO):
            continue
        if product not in slot_of:
            raise NotExact("these numbers lie in different quadratic fields")
        dest = slot_of[product]
        re[dest] = re_c
        im[dest] = im_c
    return _from_slots(d, e, f, re, im, keep=True)


def c_align(left: CNum, right: CNum) -> tuple[CNum, CNum]:
    if left.d == right.d and left.e == right.e and left.f == right.f:
        return left, right
    d, e, f = _compositum(set(_radicands(left)) | set(_radicands(right)))
    if d == 0:
        return left, right
    return _lift_to(left, d, e, f), _lift_to(right, d, e, f)


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
        a.f,
        _qadd(a.re4, b.re4),
        _qadd(a.re5, b.re5),
        _qadd(a.re6, b.re6),
        _qadd(a.re7, b.re7),
        _qadd(a.im4, b.im4),
        _qadd(a.im5, b.im5),
        _qadd(a.im6, b.im6),
        _qadd(a.im7, b.im7),
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
        value.f,
        _qneg(value.re4),
        _qneg(value.re5),
        _qneg(value.re6),
        _qneg(value.re7),
        _qneg(value.im4),
        _qneg(value.im5),
        _qneg(value.im6),
        _qneg(value.im7),
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


def _lo(value: CNum) -> CNum:
    return _reduce_cnum(
        value.d, value.re0, value.re1, value.im0, value.im1,
        value.e, value.re2, value.re3, value.im2, value.im3,
    )


def _hi(value: CNum) -> CNum:
    return _reduce_cnum(
        value.d, value.re4, value.re5, value.im4, value.im5,
        value.e, value.re6, value.re7, value.im6, value.im7,
    )


def _join_tower(lo: CNum, hi: CNum, f: int) -> CNum:
    if f <= 1 or c_is_zero(hi):
        return lo
    a, b = c_align(lo, hi)
    if a.f != 0 or b.f != 0:
        raise KernelError("a tower factor left the biquadratic base")
    return _reduce_cnum(
        a.d, a.re0, a.re1, a.im0, a.im1,
        a.e, a.re2, a.re3, a.im2, a.im3,
        f, b.re0, b.re1, b.re2, b.re3, b.im0, b.im1, b.im2, b.im3,
    )


def c_mul(left: CNum, right: CNum) -> CNum:
    a, b = c_align(left, right)
    if a.f > 1:
        # (p + q √f)(r + s √f) = pr + qs f + (ps + qr) √f, in the base field.
        p, q = _lo(a), _hi(a)
        r, s = _lo(b), _hi(b)
        lo = c_add(c_mul(p, r), c_mul(c_mul(q, s), c_from_int(a.f)))
        hi = c_add(c_mul(p, s), c_mul(q, r))
        return _join_tower(lo, hi, a.f)
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
        value.f,
        value.re4,
        value.re5,
        value.re6,
        value.re7,
        _qneg(value.im4),
        _qneg(value.im5),
        _qneg(value.im6),
        _qneg(value.im7),
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
    if value.f > 1:
        # 1/(p + q √f) = (p - q √f) / (p^2 - q^2 f), then check both products.
        p, q = _lo(value), _hi(value)
        den = c_sub(c_mul(p, p), c_mul(c_mul(q, q), c_from_int(value.f)))
        scale = c_inv(den)
        result = _join_tower(c_mul(p, scale), c_neg(c_mul(q, scale)), value.f)
        if not c_eq(c_mul(value, result), c_one()) or not c_eq(c_mul(result, value), c_one()):
            raise KernelError("this inverse did not multiply back to 1")
        return result
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


def _split_largest(value: CNum) -> tuple[CNum, CNum, int]:
    """Write a real number as a + b √r with r the largest radicand and a, b in the base."""
    if value.f > 1:
        return _lo(value), _hi(value), value.f
    if value.e > 1:
        a = _reduce_cnum(value.d, value.re0, value.re1, value.im0, value.im1)
        b = _reduce_cnum(value.d, value.re2, value.re3, value.im2, value.im3)
        return a, b, value.e
    if value.d > 1:
        a = _reduce_cnum(0, value.re0, _ZERO, value.im0, _ZERO)
        b = _reduce_cnum(0, value.re1, _ZERO, value.im1, _ZERO)
        return a, b, value.d
    return value, c_zero(), 0


def c_is_nonneg(value: CNum) -> bool:
    """Whether a real number is nonnegative under the standard embedding √r > 0."""
    if not c_is_real(value):
        return False
    if c_is_zero(value):
        return True
    if c_is_rational(value):
        return value.re0.num >= 0
    a, b, rad = _split_largest(value)
    a_pos = c_is_nonneg(a)
    b_pos = c_is_nonneg(b)
    if a_pos and b_pos:
        return True
    a_nonpos = c_is_nonneg(c_neg(a))
    b_nonpos = c_is_nonneg(c_neg(b))
    if a_nonpos and b_nonpos:
        return False
    # Mixed signs: a + b √r >= 0 iff the squared comparison has the matching sign.
    disc = c_sub(c_mul(a, a), c_mul(c_mul(b, b), c_from_int(rad)))
    if a_pos and b_nonpos:
        return c_is_nonneg(disc)
    return not c_is_nonneg(disc) or c_is_zero(disc)


def c_is_pos(value: CNum) -> bool:
    return c_is_nonneg(value) and not c_is_zero(value)


def c_sqrt(value: CNum) -> CNum:
    """The nonnegative square root, kept only when it denests in the allowed tower."""
    if not c_is_real(value):
        raise NotExact("a square root of a non-real stays open")
    if not c_is_nonneg(value):
        raise NotExact("a negative radicand stays open")
    if c_is_zero(value):
        return c_zero()
    if c_is_rational(value):
        return c_sqrt_ratio(value.re0)
    a, b, rad = _split_largest(value)
    if c_is_zero(b):
        return c_sqrt(a)
    disc = c_sub(c_mul(a, a), c_mul(c_mul(b, b), c_from_int(rad)))
    if not c_is_nonneg(disc):
        raise NotExact("this square root does not denest in the allowed tower")
    last_error: Exception | None = None
    for sign in (c_one(), c_from_int(-1)):
        try:
            s = c_mul(sign, c_sqrt(disc))
        except NotExact as exc:
            last_error = exc
            continue
        half = c_div(c_add(a, s), c_from_int(2))
        if not c_is_nonneg(half):
            continue
        try:
            x = c_sqrt(half)
        except NotExact as exc:
            last_error = exc
            continue
        if c_is_zero(x):
            continue
        y = c_div(b, c_mul(c_from_int(2), x))
        candidate = c_add(x, c_mul(y, c_sqrt_ratio(_q(rad))))
        if c_is_pos(candidate) and c_eq(c_mul(candidate, candidate), value):
            return candidate
        flipped = c_neg(candidate)
        if c_is_pos(flipped) and c_eq(c_mul(flipped, flipped), value):
            return flipped
    if last_error is not None:
        raise NotExact("this square root does not denest in the allowed tower") from last_error
    raise NotExact("this square root does not denest in the allowed tower")


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
        coeffs = (value.im0, value.im1, value.im2, value.im3, value.im4, value.im5, value.im6, value.im7)
    else:
        coeffs = (value.re0, value.re1, value.re2, value.re3, value.re4, value.re5, value.re6, value.re7)
    d, e, f = value.d, value.e, value.f
    rads = [
        "",
        f"sqrt({d})" if d > 1 else "",
        f"sqrt({e})" if e > 1 else "",
        f"sqrt({d * e})" if d > 1 and e > 1 else "",
        f"sqrt({f})" if f > 1 else "",
        f"sqrt({d * f})" if d > 1 and f > 1 else "",
        f"sqrt({e * f})" if e > 1 and f > 1 else "",
        f"sqrt({d * e * f})" if d > 1 and e > 1 and f > 1 else "",
    ]
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


# Standing check at import: i^2 = -1, a sample inverse, a 3-radicand
# inverse, and a denesting square root.
_I_CHECK = c_i()
_TOWER = c_add(c_add(c_sqrt_ratio(_q(2)), c_sqrt_ratio(_q(3))), c_sqrt_ratio(_q(5)))
if not c_eq(c_mul(_TOWER, c_inv(_TOWER)), c_one()):
    raise KernelError("a 3-radicand inverse did not multiply back to 1")
_DENEST = c_add(c_from_int(4), c_mul(c_from_int(2), c_sqrt_ratio(_q(3))))
if not c_eq(c_sqrt(_DENEST), c_add(c_one(), c_sqrt_ratio(_q(3)))):
    raise KernelError("sqrt(4 + 2 sqrt(3)) did not denest to 1 + sqrt(3)")
