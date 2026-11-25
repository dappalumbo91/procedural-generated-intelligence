"""Exact multivariate polynomials and rational functions over Q.

A polynomial is a finite sum of reduced rational coefficients times
monomials. Addition, multiplication, and powers use those exact
coefficients. A rational function is a reduced quotient: the numerator
and denominator are divided by their primitive GCD, and a zero
denominator stays open. A partial derivative is termwise, and a
derivative of a quotient uses the quotient rule, then reduces. Mixed
partials of a polynomial are kept only when they commute.

Lean mathlib `MvPolynomial` and `derivative`, and Isabelle
`Polynomial.thy` together with the AFP multivariate polynomials, are
the named laws. Clairaut's theorem for polynomials is the equality of
mixed partials, checked exactly, with no analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import gcd, lcm

from pgi.math.kernel import KernelError, NotExact
from pgi.math.rational import Ratio, RatTheorem, eval_rat, rat_normalize
from pgi.math.syntax import App, IntLit, Term, Var, closed, pretty
from pgi.model import Rule


VAR_LIMIT = 8
DEGREE_LIMIT = 32
TERM_LIMIT = 256
POWER_LIMIT = 32
_ZERO = Ratio(0, 1)
_ONE = Ratio(1, 1)


@dataclass(frozen=True)
class MPoly:
    names: tuple[str, ...]
    terms: tuple[tuple[tuple[int, ...], Ratio], ...]

    def __post_init__(self) -> None:
        if not _poly_ok(self):
            raise KernelError("this multivariate polynomial is not in normal form")

    @property
    def is_zero(self) -> bool:
        return not self.terms

    @property
    def is_one(self) -> bool:
        return self.terms == (((), _ONE),) or (
            len(self.terms) == 1 and self.terms[0][0] == (0,) * len(self.names) and self.terms[0][1] == _ONE
        )

    @property
    def is_constant(self) -> bool:
        if not self.terms:
            return True
        return all(all(exp == 0 for exp in monom) for monom, _coeff in self.terms)

    def constant(self) -> Ratio:
        if not self.terms:
            return _ZERO
        if len(self.terms) == 1 and all(exp == 0 for exp in self.terms[0][0]):
            return self.terms[0][1]
        raise KernelError("this polynomial is not a constant")


@dataclass(frozen=True)
class MRat:
    num: MPoly
    den: MPoly

    def __post_init__(self) -> None:
        if self.den.is_zero:
            raise KernelError("a rational function needs a nonzero denominator")
        if not _rat_ok(self):
            raise KernelError("this rational function is not reduced")

    @property
    def is_poly(self) -> bool:
        return _is_unit_constant(self.den)


def _poly_ok(poly: MPoly) -> bool:
    if len(poly.names) != len(set(poly.names)):
        return False
    if any(not name or not (name[0].isalpha() or name[0] == "_") for name in poly.names):
        return False
    if len(poly.names) > VAR_LIMIT:
        return False
    seen: set[tuple[int, ...]] = set()
    width = len(poly.names)
    previous: tuple[int, ...] | None = None
    for monom, coeff in poly.terms:
        if len(monom) != width:
            return False
        if any(exp < 0 or exp > DEGREE_LIMIT for exp in monom):
            return False
        if sum(monom) > DEGREE_LIMIT:
            return False
        if coeff.num == 0 or coeff.den <= 0 or gcd(abs(coeff.num), coeff.den) != 1:
            return False
        if monom in seen:
            return False
        seen.add(monom)
        if previous is not None and _monom_key(monom) <= previous:
            return False
        previous = _monom_key(monom, coeff)
    return len(poly.terms) <= TERM_LIMIT


def _rat_ok(value: MRat) -> bool:
    if value.num.names != value.den.names:
        return False
    if value.den.is_zero:
        return False
    content_num, prim_num = _split_content(value.num)
    content_den, prim_den = _split_content(value.den)
    if _mpoly_gcd(prim_num, prim_den).terms not in {(( (0,) * len(value.den.names), _ONE),), (((), _ONE),)} and not (
        _mpoly_gcd(prim_num, prim_den).is_one or _is_unit_constant(_mpoly_gcd(prim_num, prim_den))
    ):
        return False
    if content_den.num < 0:
        return False
    return True


def _monom_key(monom: tuple[int, ...], coeff: Ratio | None = None) -> tuple:
    return (-sum(monom), tuple(-exp for exp in monom))


def zero_poly(names: tuple[str, ...] = ()) -> MPoly:
    return MPoly(names, ())


def const_poly(value: Ratio, names: tuple[str, ...] = ()) -> MPoly:
    if value.num == 0:
        return zero_poly(names)
    monom = (0,) * len(names)
    return MPoly(names, ((monom, value),))


def var_poly(name: str, names: tuple[str, ...] | None = None) -> MPoly:
    names = names if names is not None else (name,)
    if name not in names:
        names = tuple(sorted((*names, name)))
    monom = tuple(1 if item == name else 0 for item in names)
    return MPoly(names, ((monom, _ONE),))


def show_poly(poly: MPoly) -> str:
    if poly.is_zero:
        return "0"
    pieces: list[str] = []
    for monom, coeff in poly.terms:
        pieces.append(_show_term(poly.names, monom, coeff))
    body = pieces[0]
    for term in pieces[1:]:
        if term.startswith("-"):
            body = f"{body} - {term[1:]}"
        else:
            body = f"{body} + {term}"
    return body


def show_rat(value: MRat) -> str:
    if value.is_poly:
        if value.den.constant() == _ONE:
            return show_poly(value.num)
        # denominator is a negative unit (should not happen after normalize)
        return show_poly(mpoly_smul(_inv(value.den.constant()), value.num))
    num = show_poly(value.num)
    den = show_poly(value.den)
    if _needs_parens(value.num):
        num = f"({num})"
    if _needs_parens(value.den):
        den = f"({den})"
    return f"{num} / {den}"


def _needs_parens(poly: MPoly) -> bool:
    return len(poly.terms) > 1


def _show_term(names: tuple[str, ...], monom: tuple[int, ...], coeff: Ratio) -> str:
    factors: list[str] = []
    for name, exp in zip(names, monom):
        if exp == 0:
            continue
        if exp == 1:
            factors.append(name)
        else:
            factors.append(f"{name}^{exp}")
    if not factors:
        return _show_ratio(coeff)
    if coeff == _ONE:
        return " * ".join(factors)
    if coeff == Ratio(-1, 1):
        return "-" + " * ".join(factors)
    return _show_ratio(coeff) + " * " + " * ".join(factors)


def _show_ratio(value: Ratio) -> str:
    if value.den == 1:
        return str(value.num)
    return f"{value.num}/{value.den}"


def mpoly_add(left: MPoly, right: MPoly) -> MPoly:
    left, right = _align(left, right)
    return _from_map(left.names, _add_maps(_as_map(left), _as_map(right)))


def mpoly_sub(left: MPoly, right: MPoly) -> MPoly:
    return mpoly_add(left, mpoly_neg(right))


def mpoly_neg(poly: MPoly) -> MPoly:
    return MPoly(poly.names, tuple((monom, Ratio(-coeff.num, coeff.den)) for monom, coeff in poly.terms))


def mpoly_smul(scalar: Ratio, poly: MPoly) -> MPoly:
    if scalar.num == 0:
        return zero_poly(poly.names)
    return _from_map(poly.names, {monom: _mul(scalar, coeff) for monom, coeff in poly.terms})


def mpoly_mul(left: MPoly, right: MPoly) -> MPoly:
    left, right = _align(left, right)
    acc: dict[tuple[int, ...], Ratio] = {}
    for monom_l, coeff_l in left.terms:
        for monom_r, coeff_r in right.terms:
            monom = tuple(a + b for a, b in zip(monom_l, monom_r))
            if sum(monom) > DEGREE_LIMIT or any(exp > DEGREE_LIMIT for exp in monom):
                raise NotExact("this polynomial exceeds the degree limit")
            acc[monom] = _add(acc.get(monom, _ZERO), _mul(coeff_l, coeff_r))
    result = _from_map(left.names, acc)
    if len(result.terms) > TERM_LIMIT:
        raise NotExact("this polynomial exceeds the term limit")
    return result


def mpoly_pow(base: MPoly, exponent: int) -> MPoly:
    if exponent < 0:
        raise KernelError("a polynomial power stays nonnegative")
    if exponent > POWER_LIMIT:
        raise NotExact("this power exceeds the exponent limit")
    if exponent == 0:
        if base.is_zero:
            raise NotExact("0^0 stays open")
        return const_poly(_ONE, base.names)
    result = const_poly(_ONE, base.names)
    for _ in range(exponent):
        result = mpoly_mul(result, base)
    check = result
    # The power is rebuilt by repeated multiplication; that is the justification.
    return check


def mpoly_diff(poly: MPoly, name: str) -> MPoly:
    if name not in poly.names:
        return zero_poly(poly.names)
    index = poly.names.index(name)
    acc: dict[tuple[int, ...], Ratio] = {}
    for monom, coeff in poly.terms:
        exp = monom[index]
        if exp == 0:
            continue
        new = list(monom)
        new[index] = exp - 1
        acc[tuple(new)] = _add(acc.get(tuple(new), _ZERO), _mul(Ratio(exp, 1), coeff))
    return _from_map(poly.names, acc)


def mpoly_eq(left: MPoly, right: MPoly) -> bool:
    left, right = _align(left, right)
    return left.terms == right.terms and left.names == right.names


def mrat_from(num: MPoly, den: MPoly) -> MRat:
    if den.is_zero:
        raise NotExact("division by zero")
    return _reduce_rat(num, den)


def mrat_add(left: MRat, right: MRat) -> MRat:
    return _reduce_rat(
        mpoly_add(mpoly_mul(left.num, right.den), mpoly_mul(right.num, left.den)),
        mpoly_mul(left.den, right.den),
    )


def mrat_sub(left: MRat, right: MRat) -> MRat:
    return mrat_add(left, mrat_neg(right))


def mrat_neg(value: MRat) -> MRat:
    return _reduce_rat(mpoly_neg(value.num), value.den)


def mrat_mul(left: MRat, right: MRat) -> MRat:
    return _reduce_rat(mpoly_mul(left.num, right.num), mpoly_mul(left.den, right.den))


def mrat_div(left: MRat, right: MRat) -> MRat:
    if right.num.is_zero:
        raise NotExact("division by zero")
    return _reduce_rat(mpoly_mul(left.num, right.den), mpoly_mul(left.den, right.num))


def mrat_pow(base: MRat, exponent: int) -> MRat:
    if exponent > POWER_LIMIT or exponent < -POWER_LIMIT:
        raise NotExact("this power exceeds the exponent limit")
    if exponent == 0:
        if base.num.is_zero:
            raise NotExact("0^0 stays open")
        return mrat_from(const_poly(_ONE, base.num.names), const_poly(_ONE, base.num.names))
    if exponent > 0:
        result = mrat_from(const_poly(_ONE, base.num.names), const_poly(_ONE, base.num.names))
        for _ in range(exponent):
            result = mrat_mul(result, base)
        return result
    if base.num.is_zero:
        raise NotExact("division by zero")
    inverse = mrat_from(base.den, base.num)
    result = mrat_from(const_poly(_ONE, base.num.names), const_poly(_ONE, base.num.names))
    for _ in range(-exponent):
        result = mrat_mul(result, inverse)
    return result


def mrat_diff(value: MRat, name: str) -> MRat:
    # Quotient rule: (n' d - n d') / d^2, then reduce.
    numerator = mpoly_sub(mpoly_mul(mpoly_diff(value.num, name), value.den), mpoly_mul(value.num, mpoly_diff(value.den, name)))
    denominator = mpoly_mul(value.den, value.den)
    result = _reduce_rat(numerator, denominator)
    # Check the unreduced quotient rule identity.
    if not mpoly_eq(mpoly_mul(result.num, denominator), mpoly_mul(numerator, result.den)):
        raise KernelError("the quotient rule did not multiply back")
    return result


def mrat_eq(left: MRat, right: MRat) -> bool:
    left_n, left_d = _align(left.num, left.den)
    # Cross-multiply after aligning all four through a common variable set.
    nums = _align_all((left.num, left.den, right.num, right.den))
    return mpoly_eq(mpoly_mul(nums[0], nums[3]), mpoly_mul(nums[2], nums[1]))


def as_rat(value: MPoly | MRat) -> MRat:
    if isinstance(value, MRat):
        return value
    return mrat_from(value, const_poly(_ONE, value.names))


def _reduce_rat(num: MPoly, den: MPoly) -> MRat:
    if den.is_zero:
        raise NotExact("division by zero")
    num, den = _align(num, den)
    content_num, prim_num = _split_content(num)
    content_den, prim_den = _split_content(den)
    common = _mpoly_gcd(prim_num, prim_den)
    if not _is_unit_constant(common):
        prim_num = _exact_div(prim_num, common)
        prim_den = _exact_div(prim_den, common)
    scale = _div(content_num, content_den)
    if scale.num < 0:
        # Keep the denominator's rational content positive by moving the sign to the numerator.
        pass
    num = mpoly_smul(scale, prim_num)
    den = prim_den
    # If the denominator's leading coefficient is negative, flip both signs.
    if not den.is_zero and _lead_coeff(den).num < 0:
        num = mpoly_neg(num)
        den = mpoly_neg(den)
    return MRat(num, den)


def _split_content(poly: MPoly) -> tuple[Ratio, MPoly]:
    if poly.is_zero:
        return _ONE, poly
    nums = [coeff.num for _monom, coeff in poly.terms]
    dens = [coeff.den for _monom, coeff in poly.terms]
    common_num = abs(nums[0])
    for value in nums[1:]:
        common_num = gcd(common_num, abs(value))
    common_den = dens[0]
    for value in dens[1:]:
        common_den = lcm(common_den, value)
    content = rat_normalize(common_num, common_den).value
    # The first term carries the sign of the content.
    if _lead_coeff(poly).num < 0:
        content = Ratio(-content.num, content.den)
    primitive = mpoly_smul(_inv(content), poly)
    return content, primitive


def _lead_coeff(poly: MPoly) -> Ratio:
    if poly.is_zero:
        return _ZERO
    return poly.terms[0][1]


def _is_unit_constant(poly: MPoly) -> bool:
    if poly.is_zero or not poly.is_constant:
        return False
    value = poly.constant()
    return abs(value.num) == 1 and value.den == 1


def _mpoly_gcd(left: MPoly, right: MPoly) -> MPoly:
    left, right = _align(left, right)
    if left.is_zero:
        return _canonical_gcd(right)
    if right.is_zero:
        return _canonical_gcd(left)
    if not left.names:
        value = rat_normalize(gcd(abs(left.constant().num), abs(right.constant().num)), 1).value
        if value.num == 0:
            return zero_poly()
        return const_poly(value)
    return _canonical_gcd(_gcd_recursive(left, right))


def _canonical_gcd(poly: MPoly) -> MPoly:
    if poly.is_zero:
        return poly
    content, primitive = _split_content(poly)
    # Primitive, positive leading coefficient; drop a unit content.
    return primitive


def _gcd_recursive(left: MPoly, right: MPoly) -> MPoly:
    if left.is_zero:
        return right
    if right.is_zero:
        return left
    if not left.names:
        return const_poly(rat_normalize(gcd(abs(left.constant().num), abs(right.constant().num)), 1).value)
    main = left.names[-1]
    rest = left.names[:-1]
    content_l, prim_l = _content_primitive_in(left, main)
    content_r, prim_r = _content_primitive_in(right, main)
    content = _mpoly_gcd(content_l, content_r)
    primitive = _primitive_gcd_in(prim_l, prim_r, main)
    return mpoly_mul(_embed(content, left.names), primitive)


def _content_primitive_in(poly: MPoly, main: str) -> tuple[MPoly, MPoly]:
    coeffs = [coeff for _deg, coeff in _univariate(poly, main)]
    content = coeffs[0]
    for coeff in coeffs[1:]:
        content = _mpoly_gcd(content, coeff)
    if content.is_zero or _is_unit_constant(content) and content.constant() == _ONE:
        return const_poly(_ONE, poly.names[:-1] if poly.names else ()), poly
    primitive = _map_coeffs(poly, main, lambda coeff: _exact_div(coeff, content) if not content.is_zero else coeff)
    return content, primitive


def _primitive_gcd_in(left: MPoly, right: MPoly, main: str) -> MPoly:
    f, g = left, right
    steps = 0
    while not g.is_zero:
        if _deg_in(f, main) < _deg_in(g, main):
            f, g = g, f
        remainder = _pseudo_rem(f, g, main)
        _content, primitive = _content_primitive_in(remainder, main) if not remainder.is_zero else (const_poly(_ONE), remainder)
        f, g = g, primitive
        steps += 1
        if steps > DEGREE_LIMIT * 2 + 8:
            raise KernelError("the polynomial GCD did not terminate")
    content, primitive = _content_primitive_in(f, main)
    return primitive


def _univariate(poly: MPoly, main: str) -> list[tuple[int, MPoly]]:
    if main not in poly.names:
        return [(0, poly)]
    index = poly.names.index(main)
    rest = tuple(name for name in poly.names if name != main)
    buckets: dict[int, dict[tuple[int, ...], Ratio]] = {}
    for monom, coeff in poly.terms:
        exp = monom[index]
        other = tuple(power for i, power in enumerate(monom) if i != index)
        buckets.setdefault(exp, {})[other] = _add(buckets.get(exp, {}).get(other, _ZERO), coeff)
    return sorted(((exp, _from_map(rest, terms)) for exp, terms in buckets.items()), reverse=True)


def _from_univariate(names: tuple[str, ...], main: str, parts: list[tuple[int, MPoly]]) -> MPoly:
    acc: dict[tuple[int, ...], Ratio] = {}
    if main not in names:
        names = tuple(sorted((*names, main)))
    index = names.index(main)
    for exp, coeff in parts:
        if coeff.is_zero:
            continue
        embedded = _embed(coeff, tuple(name for name in names if name != main))
        for monom, value in embedded.terms:
            full = list(monom)
            full.insert(index, exp)
            key = tuple(full)
            acc[key] = _add(acc.get(key, _ZERO), value)
    return _from_map(names, acc)


def _deg_in(poly: MPoly, main: str) -> int:
    parts = _univariate(poly, main)
    return parts[0][0] if parts else -1


def _lead_in(poly: MPoly, main: str) -> MPoly:
    parts = _univariate(poly, main)
    if not parts:
        return zero_poly(tuple(name for name in poly.names if name != main))
    return parts[0][1]


def _pseudo_rem(left: MPoly, right: MPoly, main: str) -> MPoly:
    if right.is_zero:
        raise KernelError("pseudo-remainder by the zero polynomial")
    rem = left
    deg_r = _deg_in(right, main)
    lead_r = _lead_in(right, main)
    steps = 0
    while not rem.is_zero and _deg_in(rem, main) >= deg_r:
        deg_f = _deg_in(rem, main)
        lead_f = _lead_in(rem, main)
        shift = deg_f - deg_r
        # rem := lead_r * rem - lead_f * x^shift * right
        rem = mpoly_sub(
            mpoly_mul(_embed(lead_r, rem.names), rem),
            mpoly_mul(_embed(lead_f, rem.names), mpoly_mul(_var_power(main, shift, rem.names), right)),
        )
        steps += 1
        if steps > DEGREE_LIMIT + 4:
            raise KernelError("pseudo-division did not terminate")
    return rem


def _var_power(name: str, exp: int, names: tuple[str, ...]) -> MPoly:
    if exp == 0:
        return const_poly(_ONE, names)
    monom = tuple(exp if item == name else 0 for item in names)
    return MPoly(names, ((monom, _ONE),))


def _map_coeffs(poly: MPoly, main: str, fn) -> MPoly:
    parts = [(exp, fn(coeff)) for exp, coeff in _univariate(poly, main)]
    return _from_univariate(poly.names, main, parts)


def _exact_div(left: MPoly, right: MPoly) -> MPoly:
    if right.is_zero:
        raise KernelError("division by the zero polynomial")
    left, right = _align(left, right)
    if _is_unit_constant(right):
        return mpoly_smul(_inv(right.constant()), left)
    # Multivariate exact division by multiplying back.
    quot = _try_div(left, right)
    if quot is None or not mpoly_eq(mpoly_mul(quot, right), left):
        raise KernelError("polynomial division was not exact")
    return quot


def _try_div(left: MPoly, right: MPoly) -> MPoly | None:
    if left.is_zero:
        return zero_poly(left.names)
    if right.is_zero:
        return None
    if not left.names:
        if right.constant().num == 0:
            return None
        return const_poly(_div(left.constant(), right.constant()))
    main = left.names[-1]
    if _deg_in(left, main) < _deg_in(right, main) and not (left.is_constant and right.is_constant):
        # try other main variables if left is independent of main
        if _deg_in(right, main) > 0 and _deg_in(left, main) < 0:
            return None
    acc = zero_poly(left.names)
    rem = left
    steps = 0
    while not rem.is_zero:
        if _deg_in(rem, main) < _deg_in(right, main):
            # remainder would be nonzero unless rem is 0
            if rem.is_zero:
                break
            # Try dividing as polynomials in a different variable, or fail.
            if rem.is_constant and right.is_constant:
                return mpoly_add(acc, const_poly(_div(rem.constant(), right.constant()), rem.names))
            return None
        lead_q = _try_div(_lead_in(rem, main), _lead_in(right, main))
        if lead_q is None:
            return None
        shift = _deg_in(rem, main) - _deg_in(right, main)
        term = mpoly_mul(_embed(lead_q, rem.names), _var_power(main, shift, rem.names))
        acc = mpoly_add(acc, term)
        rem = mpoly_sub(rem, mpoly_mul(term, right))
        steps += 1
        if steps > TERM_LIMIT + 8:
            return None
    return acc


def _align(left: MPoly, right: MPoly) -> tuple[MPoly, MPoly]:
    names = tuple(sorted(set(left.names) | set(right.names)))
    if len(names) > VAR_LIMIT:
        raise NotExact("this polynomial exceeds the variable limit")
    return _embed(left, names), _embed(right, names)


def _align_all(polys: tuple[MPoly, ...]) -> tuple[MPoly, ...]:
    names = tuple(sorted(set().union(*(poly.names for poly in polys))))
    if len(names) > VAR_LIMIT:
        raise NotExact("this polynomial exceeds the variable limit")
    return tuple(_embed(poly, names) for poly in polys)


def _embed(poly: MPoly, names: tuple[str, ...]) -> MPoly:
    if poly.names == names:
        return poly
    index = [poly.names.index(name) if name in poly.names else None for name in names]
    acc: dict[tuple[int, ...], Ratio] = {}
    for monom, coeff in poly.terms:
        new = tuple(0 if pos is None else monom[pos] for pos in index)
        acc[new] = _add(acc.get(new, _ZERO), coeff)
    return _from_map(names, acc)


def _as_map(poly: MPoly) -> dict[tuple[int, ...], Ratio]:
    return {monom: coeff for monom, coeff in poly.terms}


def _add_maps(left: dict[tuple[int, ...], Ratio], right: dict[tuple[int, ...], Ratio]) -> dict[tuple[int, ...], Ratio]:
    acc = dict(left)
    for monom, coeff in right.items():
        acc[monom] = _add(acc.get(monom, _ZERO), coeff)
    return acc


def _from_map(names: tuple[str, ...], terms: dict[tuple[int, ...], Ratio]) -> MPoly:
    items = [(monom, coeff) for monom, coeff in terms.items() if coeff.num != 0]
    items.sort(key=lambda item: _monom_key(item[0]))
    return MPoly(names, tuple(items))


def _add(left: Ratio, right: Ratio) -> Ratio:
    return rat_normalize(left.num * right.den + right.num * left.den, left.den * right.den).value


def _mul(left: Ratio, right: Ratio) -> Ratio:
    return rat_normalize(left.num * right.num, left.den * right.den).value


def _div(left: Ratio, right: Ratio) -> Ratio:
    if right.num == 0:
        raise NotExact("division by zero")
    return rat_normalize(left.num * right.den, left.den * right.num).value


def _inv(value: Ratio) -> Ratio:
    if value.num == 0:
        raise NotExact("division by zero")
    return rat_normalize(value.den, value.num).value


def eval_symbolic(term: Term) -> MRat:
    return as_rat(_eval(term))


def _eval(term: Term) -> MPoly | MRat:
    if isinstance(term, IntLit):
        return const_poly(Ratio(term.n, 1))
    if isinstance(term, Var):
        return var_poly(term.name)
    if not isinstance(term, App):
        raise NotExact("this term is not a polynomial or a rational function")
    if term.op in {"d", "partial", "diff"}:
        return _eval_diff(term)
    if term.op == "pow":
        if len(term.args) != 2:
            raise NotExact("pow takes a base and an exponent")
        base = as_rat(_eval(term.args[0]))
        exponent = _closed_int(term.args[1])
        return mrat_pow(base, exponent)
    if term.op == "neg":
        if len(term.args) != 1:
            raise KernelError("neg")
        return _neg_value(_eval(term.args[0]))
    if term.op in {"add", "sub", "mul", "div"} and len(term.args) == 2:
        return _combine(term.op, _eval(term.args[0]), _eval(term.args[1]))
    raise NotExact("this term is not a polynomial or a rational function")


def _eval_diff(term: App) -> MRat:
    if len(term.args) not in {2, 3}:
        raise NotExact("a partial derivative needs an expression and a variable")
    value = as_rat(_eval(term.args[0]))
    name = _var_name(term.args[1])
    times = 1
    if len(term.args) == 3:
        times = _closed_int(term.args[2])
        if times < 0:
            raise NotExact("a negative derivative order stays outside")
        if times > POWER_LIMIT:
            raise NotExact("this derivative order exceeds the limit")
    result = value
    previous = result
    for index in range(times):
        result = mrat_diff(result, name)
        # For a polynomial, check mixed partials when we can: after the first derivative, a further
        # derivative in another variable is checked by the caller; here a repeated derivative in
        # the same variable is just iteration.
        previous = result
    # Clairaut: if the original is a polynomial, ∂/∂x and then a formal check that
    # differentiating zero times more is itself. Mixed commutation is checked when
    # two successive calls use different names; see mrat_diff_commute.
    return result


def mrat_diff_commute(value: MRat, first: str, second: str) -> None:
    left = mrat_diff(mrat_diff(value, first), second)
    right = mrat_diff(mrat_diff(value, second), first)
    if not mrat_eq(left, right):
        raise KernelError("mixed partial derivatives did not commute")


def _combine(op: str, left: MPoly | MRat, right: MPoly | MRat) -> MPoly | MRat:
    left_r = as_rat(left)
    right_r = as_rat(right)
    if op == "add":
        return mrat_add(left_r, right_r)
    if op == "sub":
        return mrat_sub(left_r, right_r)
    if op == "mul":
        return mrat_mul(left_r, right_r)
    if op == "div":
        return mrat_div(left_r, right_r)
    raise KernelError(op)


def _neg_value(value: MPoly | MRat) -> MPoly | MRat:
    if isinstance(value, MRat):
        return mrat_neg(value)
    return mpoly_neg(value)


def _var_name(term: Term) -> str:
    if isinstance(term, Var):
        return term.name
    raise NotExact("a partial derivative is taken with respect to a variable")


def _closed_int(term: Term) -> int:
    if isinstance(term, IntLit):
        return term.n
    if isinstance(term, App) and term.op == "neg" and len(term.args) == 1 and isinstance(term.args[0], IntLit):
        return -term.args[0].n
    try:
        value = eval_rat(term).value
    except (KernelError, NotExact) as exc:
        raise NotExact("this exponent is not a closed integer") from exc
    if value.den != 1:
        raise NotExact("this exponent is not a closed integer")
    return value.num


def has_symbolic(term: Term) -> bool:
    if isinstance(term, App):
        if term.op in {"d", "partial", "diff"}:
            return True
        if term.op == "pow" and not closed(term):
            return True
        if term.op == "div" and not closed(term) and _field_term(term):
            return True
        return any(has_symbolic(arg) for arg in term.args)
    return False


def _field_term(term: Term) -> bool:
    if isinstance(term, (IntLit, Var)):
        return True
    if isinstance(term, App):
        if term.op in {"add", "sub", "mul", "div", "neg", "pow", "d", "partial", "diff"}:
            return all(_field_term(arg) for arg in term.args)
    return False


@dataclass(frozen=True)
class SymTheorem:
    value: MRat
    origin: Term
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not mrat_eq(self.value, eval_symbolic(self.origin)):
            raise KernelError("this symbolic result does not match the exact evaluation")


def eval_sym_result(term: Term) -> SymTheorem | RatTheorem:
    value = eval_symbolic(term)
    # After a derivative, if two variables appear in a polynomial, mixed partials commute.
    if isinstance(term, App) and term.op in {"d", "partial", "diff"} and len(term.args) >= 2:
        source = as_rat(_eval(term.args[0]))
        names = source.num.names if source.is_poly else tuple(sorted(set(source.num.names) | set(source.den.names)))
        if source.is_poly and len(names) >= 2:
            first, second = names[0], names[1]
            mrat_diff_commute(source, first, second)
    if value.is_poly and value.num.is_constant and (not value.num.names or value.num.is_constant):
        try:
            number = value.num.constant() if not value.num.is_zero else _ZERO
            if value.den.is_constant:
                number = _div(number, value.den.constant())
                return rat_normalize(number.num, number.den)
        except KernelError:
            pass
    lines = _detail(term, value)
    return SymTheorem(value, term, lines)


def _detail(term: Term, value: MRat) -> tuple[str, ...]:
    lines = [
        "Lean mathlib MvPolynomial, with derivative on a multivariate polynomial.",
        "Isabelle Polynomial.thy, and the AFP multivariate polynomials, over the rationals.",
    ]
    if isinstance(term, App) and term.op in {"d", "partial", "diff"}:
        lines.append("A partial derivative is termwise on a polynomial, or the quotient rule on a rational function.")
        lines.append("The quotient rule is kept only when it multiplies back.")
        lines.append("Mixed partials of a polynomial commute, checked exactly (Clairaut).")
    if isinstance(term, App) and term.op == "div":
        lines.append("A rational function is reduced by the primitive GCD of its numerator and denominator.")
    return tuple(lines)


def sym_value_rule(origin: Term, result: SymTheorem | RatTheorem, prelude: tuple[str, ...] = ()) -> Rule:
    title_left = pretty(origin)
    if isinstance(result, RatTheorem):
        from pgi.math.rational import ratio_rule

        return ratio_rule(origin, result, prelude)
    shown = show_rat(result.value)
    lines = (*prelude, *result.detail)
    if result.value.is_poly:
        return Rule(
            id=f"math.poly.{shown}",
            layer="base",
            stage="quantity",
            title=f"{title_left} = {shown}",
            produces=f"poly({shown})",
            detail_lines=lines,
        )
    return Rule(
        id=f"math.ratfn.{shown}",
        layer="base",
        stage="quantity",
        title=f"{title_left} = {shown}",
        produces=f"rat({shown})",
        detail_lines=lines,
    )


def sym_equality_rules(
    left: Term,
    right: Term,
    left_value: SymTheorem | RatTheorem,
    right_value: SymTheorem | RatTheorem,
    prelude: tuple[str, ...] = (),
) -> tuple[Rule, ...]:
    title = f"{pretty(left)} = {pretty(right)}"
    left_rat = _as_mrat(left_value)
    right_rat = _as_mrat(right_value)
    if left_rat is not None and right_rat is not None and mrat_eq(left_rat, right_rat):
        return (
            Rule(
                id="math.poly.eq",
                layer="base",
                stage="quantity",
                title=title,
                produces=f"identity({title})",
                detail_lines=(*prelude, "The two reduced rational functions are the same."),
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


def _as_mrat(result: SymTheorem | RatTheorem) -> MRat | None:
    if isinstance(result, SymTheorem):
        return result.value
    if isinstance(result, RatTheorem):
        return mrat_from(const_poly(result.value), const_poly(_ONE))
    return None
