"""Arithmetic in a finite square-root tower over Q.

An element of Q(√d1)(√d2)...(√dn) is a vector of 2^n rationals, the
coordinates on the standard basis of products of subsets of {√d1, ..., √dn}.
Bit k of a basis index is the factor √(layer k). Each layer radicand is a
vector in the previous field.

Multiplication follows (a + b√d)(c + e√d) = (ac + bed) + (ae + bc)√d.
A zero, a unit, or a rational factor is scaled in one step, and a product
of the same vectors in the same tower is reused. The inverse is the
conjugate a − b√d over the norm a² − b²d, computed recursively down the
tower, and is kept only when it multiplies back to 1.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import gcd

from pgi.math.kernel import NotExact
from pgi.math.rational import Ratio

TOWER_DEGREE_LIMIT = 2048

_ZERO = Ratio(0, 1)
_ONE = Ratio(1, 1)


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


def _zeros(width: int) -> tuple[Ratio, ...]:
    return (_ZERO,) * width


def _one_coords(width: int) -> tuple[Ratio, ...]:
    if width < 1:
        raise NotExact("this quotient stays outside")
    return (_ONE,) + _zeros(width - 1)


def _add_coords(left: tuple[Ratio, ...], right: tuple[Ratio, ...]) -> tuple[Ratio, ...]:
    return tuple(_qadd(a, b) for a, b in zip(left, right))


def _sub_coords(left: tuple[Ratio, ...], right: tuple[Ratio, ...]) -> tuple[Ratio, ...]:
    return tuple(_qsub(a, b) for a, b in zip(left, right))


def _neg_coords(coords: tuple[Ratio, ...]) -> tuple[Ratio, ...]:
    return tuple(_qneg(value) for value in coords)


def _is_zero_coords(coords: tuple[Ratio, ...]) -> bool:
    return all(value.num == 0 for value in coords)


def _is_one_coords(coords: tuple[Ratio, ...]) -> bool:
    return coords[0] == _ONE and all(value.num == 0 for value in coords[1:])


def _scale_coords(coords: tuple[Ratio, ...], factor: Ratio) -> tuple[Ratio, ...]:
    if factor.num == 0:
        return _zeros(len(coords))
    if factor == _ONE:
        return coords
    return tuple(_qmul(value, factor) for value in coords)


# Products of the same coordinate vectors in the same tower are reused.
# The check that a constructed inverse multiplies back to 1 is unchanged.
_MUL_CACHE: dict[
    tuple[tuple[Ratio, ...], tuple[Ratio, ...], tuple[tuple[Ratio, ...], ...]],
    tuple[Ratio, ...],
] = {}


def _rational_scale(coords: tuple[Ratio, ...]) -> Ratio | None:
    if all(value.num == 0 for value in coords[1:]):
        return coords[0]
    return None


def _mul_coords(
    left: tuple[Ratio, ...],
    right: tuple[Ratio, ...],
    layers: tuple[tuple[Ratio, ...], ...],
) -> tuple[Ratio, ...]:
    width = len(left)
    if width == 1:
        return (_qmul(left[0], right[0]),)
    if _is_zero_coords(left) or _is_zero_coords(right):
        return _zeros(width)
    if _is_one_coords(left):
        return right
    if _is_one_coords(right):
        return left
    left_scale = _rational_scale(left)
    if left_scale is not None:
        return _scale_coords(right, left_scale)
    right_scale = _rational_scale(right)
    if right_scale is not None:
        return _scale_coords(left, right_scale)
    key = (left, right, layers)
    cached = _MUL_CACHE.get(key)
    if cached is not None:
        return cached
    swapped = (right, left, layers)
    cached = _MUL_CACHE.get(swapped)
    if cached is not None:
        return cached
    half = width // 2
    previous = layers[:-1]
    radicand = layers[-1]
    lower_left, upper_left = left[:half], left[half:]
    lower_right, upper_right = right[:half], right[half:]
    ac = _mul_coords(lower_left, lower_right, previous)
    be = _mul_coords(upper_left, upper_right, previous)
    bed = _mul_coords(be, radicand, previous)
    ae = _mul_coords(lower_left, upper_right, previous)
    bc = _mul_coords(upper_left, lower_right, previous)
    result = _add_coords(ac, bed) + _add_coords(ae, bc)
    _MUL_CACHE[key] = result
    return result


def _inv_coords(
    coords: tuple[Ratio, ...],
    layers: tuple[tuple[Ratio, ...], ...],
) -> tuple[Ratio, ...]:
    if _is_zero_coords(coords):
        raise NotExact("division by zero")
    if len(coords) == 1:
        return (_qinv(coords[0]),)
    half = len(coords) // 2
    previous = layers[:-1]
    radicand = layers[-1]
    lower, upper = coords[:half], coords[half:]
    square_lower = _mul_coords(lower, lower, previous)
    square_upper = _mul_coords(upper, upper, previous)
    norm = _sub_coords(square_lower, _mul_coords(square_upper, radicand, previous))
    if _is_zero_coords(norm):
        raise NotExact("this quotient stays outside")
    inverse_norm = _inv_coords(norm, previous)
    lower_out = _mul_coords(lower, inverse_norm, previous)
    upper_out = _mul_coords(_neg_coords(upper), inverse_norm, previous)
    return lower_out + upper_out


@dataclass(frozen=True)
class SqrtTower:
    """A tower Q(√d1)...(√dn). layers[i] is di as a vector of length 2^i."""

    layers: tuple[tuple[Ratio, ...], ...]

    def __post_init__(self) -> None:
        for index, radicand in enumerate(self.layers):
            if len(radicand) != 1 << index:
                raise NotExact("this quotient stays outside")
        if self.degree > TOWER_DEGREE_LIMIT:
            raise NotExact("this quotient stays outside")

    @property
    def degree(self) -> int:
        return 1 << len(self.layers)

    @property
    def integer_prefix(self) -> int:
        """How many leading layers have a rational radicand."""

        count = 0
        for radicand in self.layers:
            if any(value.num != 0 for value in radicand[1:]):
                break
            if radicand[0].num <= 0 or radicand[0].den != 1:
                break
            count += 1
        return count

    @property
    def complexity(self) -> int:
        total = 0
        for radicand in self.layers:
            for value in radicand:
                total += abs(value.num) + value.den
        return total


@dataclass(frozen=True)
class TowerElem:
    tower: SqrtTower
    coords: tuple[Ratio, ...]

    def __post_init__(self) -> None:
        if len(self.coords) != self.tower.degree:
            raise NotExact("this quotient stays outside")


def integer_tower(primes: tuple[int, ...]) -> SqrtTower:
    layers: list[tuple[Ratio, ...]] = []
    for index, prime in enumerate(primes):
        radicand = [_ZERO] * (1 << index)
        radicand[0] = _q(prime, 1)
        layers.append(tuple(radicand))
    return SqrtTower(tuple(layers))


def unit_last(layers_so_far: int) -> tuple[Ratio, ...]:
    """The previous-field vector for adjoining the latest generator."""

    if layers_so_far < 1:
        raise NotExact("this quotient stays outside")
    width = 1 << layers_so_far
    coords = [_ZERO] * width
    coords[1 << (layers_so_far - 1)] = _ONE
    return tuple(coords)


def lift(elem: TowerElem, target: SqrtTower) -> TowerElem:
    if elem.tower.layers == target.layers:
        return elem
    prefix = len(elem.tower.layers)
    if target.layers[:prefix] != elem.tower.layers:
        raise NotExact("this quotient stays outside")
    return TowerElem(target, elem.coords + _zeros(target.degree - len(elem.coords)))


def is_prefix(short: SqrtTower, long: SqrtTower) -> bool:
    return long.layers[: len(short.layers)] == short.layers


def add(left: TowerElem, right: TowerElem) -> TowerElem:
    if left.tower != right.tower:
        raise NotExact("this quotient stays outside")
    return TowerElem(left.tower, _add_coords(left.coords, right.coords))


def sub(left: TowerElem, right: TowerElem) -> TowerElem:
    if left.tower != right.tower:
        raise NotExact("this quotient stays outside")
    return TowerElem(left.tower, _sub_coords(left.coords, right.coords))


def neg(elem: TowerElem) -> TowerElem:
    return TowerElem(elem.tower, _neg_coords(elem.coords))


def scale(elem: TowerElem, factor: Ratio) -> TowerElem:
    return TowerElem(elem.tower, _scale_coords(elem.coords, factor))


def mul(left: TowerElem, right: TowerElem) -> TowerElem:
    if left.tower != right.tower:
        raise NotExact("this quotient stays outside")
    return TowerElem(
        left.tower,
        _mul_coords(left.coords, right.coords, left.tower.layers),
    )


def inv(elem: TowerElem) -> TowerElem:
    result = TowerElem(elem.tower, _inv_coords(elem.coords, elem.tower.layers))
    if not _is_one_coords(_mul_coords(result.coords, elem.coords, elem.tower.layers)):
        raise NotExact("constructed inverse did not multiply back to 1")
    return result


def one(tower: SqrtTower) -> TowerElem:
    return TowerElem(tower, _one_coords(tower.degree))


def zero(tower: SqrtTower) -> TowerElem:
    return TowerElem(tower, _zeros(tower.degree))


def is_one(elem: TowerElem) -> bool:
    return _is_one_coords(elem.coords)


def is_zero(elem: TowerElem) -> bool:
    return _is_zero_coords(elem.coords)


def from_rational(tower: SqrtTower, value: Ratio) -> TowerElem:
    return TowerElem(tower, _scale_coords(_one_coords(tower.degree), value))


def mask_coords(tower: SqrtTower, mask: int) -> tuple[Ratio, ...]:
    if mask < 0 or mask >= tower.degree:
        raise NotExact("this quotient stays outside")
    coords = [_ZERO] * tower.degree
    coords[mask] = _ONE
    return tuple(coords)
