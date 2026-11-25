"""Cauchy reals built from the rationals.

Isabelle2025-2 `Real.thy` defines a real as an equivalence class of Cauchy
sequences of rationals. `cauchy X` means that for every positive rational r
there is a k such that m, n ≥ k implies |X m - X n| < r. `realrel X Y` means
both sequences are Cauchy and their difference vanishes. `of_rat x` is the
constant sequence. Core Lean 4.36 has no `Real`.

This slice admits those constant sequences and the positive square-root
sequences, then closes them under addition, subtraction, multiplication, and
division. A square root is the bisection sequence that keeps a positive
rational interval whose squares bracket the radicand. The width halves at
every step, which is the Cauchy modulus. The squared sequence differs from
the radicand by a vanishing sequence, so the class is a square root. Square
factors move into the rational coefficient.

Isabelle sets `inverse (0::real) = 0`. Division by zero stays open here.
`complete_real` is a least upper bound for a nonempty set of reals that is
bounded above. This module does not build sets. A finite enumeration discharges
that statement by its maximum in the set module. The open down-ray
`{x. x < a}` is settled in the arbitrary-set module by running the
Archimedean bisection from `Real.thy`. A nested radical of one square-free
integer is a tower `base^(odd/2^k)`. A product of radicals at different levels
is one integer to the power `1/2^k`. Denesting `a + b*sqrt(n)` uses
`real_sqrt_unique`. When `a^2 - n*b^2` is a rational square, the root is a
sum of rational square roots. Otherwise the nonnegative root is the nested
radical `sqrt(a + b*sqrt(n))`, and its square is that radicand. A sum of two
different square roots stays that sum. When the difference of their squares
is a rational square, `real_sqrt_unique` writes the square root of that sum
as a sum of two binomial roots. `sqrt(sqrt(2) + sqrt(3))` is
`1/2 * sqrt(-2 + 2*sqrt(3)) + 1/2 * sqrt(2 + 2*sqrt(3))`. When that difference
is not a rational square, the nonnegative root is the nested radical itself.
`sqrt(sqrt(2) + sqrt(5))` is `sqrt(sqrt(2) + sqrt(5))`, and its square is
`sqrt(2) + sqrt(5)`. A square root of one positive binomial nest is the
nested radical `sqrt(sqrt(a + b*sqrt(n)))` when that nest does not denest.
`sqrt(sqrt(2 + sqrt(2)))` is that root, and its square is `sqrt(2 + sqrt(2))`.
A square root of one positive pair is the nested radical
`sqrt(sqrt(A*sqrt(m) + B*sqrt(n)))` when that pair does not denest.
`sqrt(sqrt(sqrt(2) + sqrt(5)))` is that root, and its square is
`sqrt(sqrt(2) + sqrt(5))`. A square root of one positive high is the nested
radical `sqrt(sqrt(sqrt(A*sqrt(m) + B*sqrt(n))))` when that high does not
denest. `sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))` is that root, and its square is
`sqrt(sqrt(sqrt(2) + sqrt(5)))`. A square root of one positive peak is the
nested radical `sqrt(sqrt(sqrt(sqrt(A*sqrt(m) + B*sqrt(n)))))` when that peak
does not denest. `sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))` is that root, and
its square is `sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))`. A square root of one
positive crest is the nested radical
`sqrt(sqrt(sqrt(sqrt(sqrt(A*sqrt(m) + B*sqrt(n))))))` when that crest does
not denest. `sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))` is that root,
and its square is `sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))`. A square root of one
positive summit is the nested radical
`sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(A*sqrt(m) + B*sqrt(n)))))))` when that summit does
not denest. `sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))` is that root,
and its square is `sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))`. Every further
finite square root of this radical is the same nested radical, one square root
deeper, by `real_sqrt_unique`. Every further finite square root of one positive
binomial nest is the same nested radical, one square root deeper, by the same
rule. A sum of the two conjugate binomial nests from a denested two-radical
square root has the difference of those nests as its inverse.
A further finite square root of one positive binomial nest, a fold, has
the inverse given by that fold times the inverse of its square.
`1 / sqrt(sqrt(sqrt(2 + sqrt(2))))` is
`sqrt(sqrt(2 * sqrt(676 + 478 * sqrt(2)))) - 1/2 * sqrt(2 * sqrt(2 * sqrt(676 + 478 * sqrt(2))))`.
A two-prime biquadratic `a + b*sqrt(p) + c*sqrt(q) + d*sqrt(p*q)` that is
not a square in `Q(sqrt(p), sqrt(q))` is itself under one square root, by
`real_sqrt_unique`. The field norm not being a rational square is the
obstruction. `sqrt(1 + sqrt(2) + sqrt(5))` is that root, and its square is
`1 + sqrt(2) + sqrt(5)`. When the field norm is a rational square and the
relative denesting succeeds, the root is written in the field. The inverse
of such a root is the root times the inverse of its square, which already
lies in that field.
A nest times a pair is the square root of the product of those insides,
by `real_sqrt_mult`. When that product is a two-prime biquadratic that is
not a square in the field, the product is that nested radical itself.
`sqrt(2 + sqrt(2)) * sqrt(sqrt(2) + sqrt(5))` is
`sqrt(2 + 2 * sqrt(2) + 2 * sqrt(5) + sqrt(10))`. A field norm that is a
rational square is not enough to denest: both relative norms must be
squares in the intermediate field. When they are not, and that fact is
decided, the root stays the biquadratic radical.
A radicand the kernel cannot see as nonnegative stays open.
Arithmetic in a finite square-root tower over Q is one checked rule: an element
is a vector on the basis of products of the adjoined square roots, multiplication
follows (a + b√d)(c + e√d) = (ac + bed) + (ae + bc)√d, and the inverse is the
conjugate over the norm, taken down the tower and kept only when it multiplies
back to 1. Named ladder levels and any further finite depth use that one rule.
Division multiplies by the inverse.
That inverse lies in the same span, and its product with the divisor is the
constant sequence 1. A divisor the kernel cannot see as nonzero stays open.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from math import isqrt
import sys

if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)

from pgi.math.kernel import KernelError, NotExact
from pgi.math.rational import Ratio, rat_add, rat_div, rat_mul, rat_neg, rat_normalize, rat_sub
from pgi.math import tower as sqrt_tower
from pgi.math.syntax import App, IntLit, Term, pretty
from pgi.model import Rule

_CERT_DEPTH = 4
_TOWER_GUARD = 0


@contextmanager
def _tower_guard():
    global _TOWER_GUARD
    _TOWER_GUARD += 1
    try:
        yield
    finally:
        _TOWER_GUARD -= 1

_DEPTHS = (0, 1, 2, 4, 8, 16, 32, 48, 64)


@dataclass(frozen=True)
class RealForm:
    constant: Ratio
    terms: tuple[tuple[Ratio, int], ...]
    towers: tuple[tuple[Ratio, int, int, int], ...] = ()
    # coeff * sqrt(constant + sqrt_coeff * sqrt(rad)), after the rational-square denest fails.
    nests: tuple[tuple[Ratio, Ratio, Ratio, int], ...] = ()
    # coeff * sqrt(left_coeff * sqrt(left_rad) + right_coeff * sqrt(right_rad)),
    # left_rad < right_rad, after the rational-square denest of the two squares fails.
    pairs: tuple[tuple[Ratio, int, int, int, int], ...] = ()
    # coeff * sqrt(mult * sqrt(constant + sqrt_coeff * sqrt(rad))).
    # mult is positive and square-free. The binomial nest does not denest.
    deeps: tuple[tuple[Ratio, int, int, int, int], ...] = ()
    # coeff * sqrt(mult * sqrt(left_c * sqrt(left_r) + right_c * sqrt(right_r))).
    # mult is positive and square-free. The pair does not denest.
    highs: tuple[tuple[Ratio, int, int, int, int, int], ...] = ()
    # coeff * sqrt(pmult * sqrt(hmult * sqrt(left_c * sqrt(left_r) + right_c * sqrt(right_r)))).
    # pmult and hmult are positive and square-free. The pair does not denest.
    peaks: tuple[tuple[Ratio, int, int, int, int, int, int], ...] = ()
    # coeff * sqrt(qmult * sqrt(pmult * sqrt(hmult * sqrt(left + right)))).
    # qmult, pmult, and hmult are positive and square-free. The pair does not denest.
    crests: tuple[tuple[Ratio, int, int, int, int, int, int, int], ...] = ()
    # coeff * sqrt(smult * sqrt(qmult * sqrt(pmult * sqrt(hmult * sqrt(left + right))))).
    # smult, qmult, pmult, and hmult are positive and square-free. The pair does not denest.
    summits: tuple[tuple[Ratio, int, int, int, int, int, int, int, int], ...] = ()
    # coeff * sqrt(amult * sqrt(smult * sqrt(qmult * sqrt(pmult * sqrt(hmult * sqrt(left + right)))))).
    # amult, smult, qmult, pmult, and hmult are positive and square-free. The pair does not denest.
    apexes: tuple[tuple[Ratio, int, int, int, int, int, int, int, int, int], ...] = ()
    # coeff * sqrt(e1 * sqrt(e2 * ... * sqrt(ek * apex)...)).
    # extra is nonempty and outermost first. Each multiplier is positive and square-free.
    shells: tuple[
        tuple[Ratio, tuple[int, ...], int, int, int, int, int, int, int, int, int], ...
    ] = ()
    # coeff * sqrt(e1 * sqrt(e2 * ... * sqrt(ek * deep)...)).
    # extra is nonempty and outermost first. Each multiplier is positive and square-free.
    folds: tuple[tuple[Ratio, tuple[int, ...], int, int, int, int], ...] = ()
    quads: tuple[tuple[Ratio, Ratio, Ratio, int, Ratio, int, Ratio], ...] = ()
    # coeff * the index-th real root of a primitive irreducible integer polynomial.
    algebras: tuple[tuple[Ratio, tuple[int, ...], int], ...] = ()


@dataclass(frozen=True)
class RealTheorem:
    form: RealForm
    rule: str
    premises: tuple[RealTheorem, ...] = ()
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _justified(self):
            raise KernelError(f"{self.rule} does not justify {show_form(self.form)}")


def eval_real(term: Term) -> RealTheorem:
    if isinstance(term, IntLit):
        return real_of_rat(_ratio(term.n, 1))
    if not isinstance(term, App):
        raise KernelError("a free variable is not a real numeral")
    if term.op == "sqrt":
        return real_sqrt(eval_real(term.args[0]))
    if term.op == "root":
        return real_of_algebraic(term)
    if term.op == "neg":
        return real_neg(eval_real(term.args[0]))
    left = eval_real(term.args[0])
    right = eval_real(term.args[1])
    if term.op == "add":
        return real_add(left, right)
    if term.op == "sub":
        return real_sub(left, right)
    if term.op == "mul":
        return real_mul(left, right)
    if term.op == "div":
        return real_div(left, right)
    raise KernelError(term.op)


def real_of_rat(value: Ratio) -> RealTheorem:
    form = RealForm(_ratio(value.num, value.den), ())
    return RealTheorem(
        form,
        "Real.of_rat",
        (),
        (
            "Isabelle of_rat_Real: of_rat x = Real (λn. x).",
            "Isabelle cauchy_const: a constant sequence of rationals is Cauchy.",
        ),
    )


def real_sqrt(operand: RealTheorem) -> RealTheorem:
    form = _sqrt_of_form(operand.form)
    return RealTheorem(form, "Real.sqrt", (operand,), _sqrt_lines(operand.form, form))


def real_add(left: RealTheorem, right: RealTheorem) -> RealTheorem:
    return RealTheorem(
        _add_forms(left.form, right.form),
        "Real.add",
        (left, right),
        (
            "Isabelle plus_real and add_Real: addition is pointwise on Cauchy sequences.",
            "Isabelle cauchy_add.",
        ),
    )


def real_neg(premise: RealTheorem) -> RealTheorem:
    return RealTheorem(
        _neg_form(premise.form),
        "Real.neg",
        (premise,),
        (
            "Isabelle uminus_real and minus_Real: negation is pointwise.",
            "Isabelle cauchy_minus.",
        ),
    )


def real_sub(left: RealTheorem, right: RealTheorem) -> RealTheorem:
    return RealTheorem(
        _sub_forms(left.form, right.form),
        "Real.sub",
        (left, right),
        (
            "Isabelle diff_Real: Real X - Real Y = Real (λn. X n - Y n).",
            "Isabelle cauchy_diff.",
        ),
    )


def real_mul(left: RealTheorem, right: RealTheorem) -> RealTheorem:
    return RealTheorem(
        _mul_forms(left.form, right.form),
        "Real.mul",
        (left, right),
        (
            "Isabelle times_real and mult_Real: multiplication is pointwise.",
            "A product of square roots is rewritten by sqrt(a) * sqrt(b) = sqrt(a*b), then square factors are extracted.",
            "Isabelle real_sqrt_mult: for nonnegative factors, sqrt(x*y) = sqrt x * sqrt y.",
            "Isabelle real_root_mult: root n (x * y) = root n x * root n y.",
            "Isabelle real_root_power: 0 < n implies root n (x ^ k) = root n x ^ k.",
            "Isabelle real_root_mult_exp: root (m * n) x = root m (root n x). A square root and a fourth root are one integer to the power 1/2^k.",
            "Same-base powers add their exponents. Equal exponents of two square-free integers multiply the integers and reduce. Unequal prime exponents stay one packed radical.",
            "A result with no radical is a constant sequence. Its difference from that rational vanishes.",
        ),
    )


def real_div(left: RealTheorem, right: RealTheorem) -> RealTheorem:
    if _is_zero(right.form):
        raise NotExact("division by zero")
    return RealTheorem(
        _div_form(left.form, right.form),
        "Real.div",
        (left, right),
        _div_lines(right.form),
    )


def real_trace(theorem: RealTheorem) -> tuple[str, ...]:
    lines: list[str] = []
    for premise in theorem.premises:
        lines.extend(real_trace(premise))
    lines.append(f"{theorem.rule}: {show_form(theorem.form)}")
    lines.extend(theorem.detail)
    return tuple(lines)


def real_value_rule(origin: Term, theorem: RealTheorem, prelude: tuple[str, ...] = ()) -> Rule:
    shown = show_form(theorem.form)
    lines = (*prelude, *real_trace(theorem))
    title_left = pretty(origin)
    if _is_rational(theorem.form):
        number = theorem.form.constant
        if number.den == 1:
            return Rule(
                id=f"math.value.{number.num}",
                layer="base",
                stage="quantity",
                title=f"{title_left} = {number.num}",
                produces=f"value({number.num})",
                detail_lines=lines,
            )
        return Rule(
            id=f"math.ratio.{number.num}.{number.den}",
            layer="base",
            stage="quantity",
            title=f"{title_left} = {number.num}/{number.den}",
            produces=f"ratio({number.num},{number.den})",
            detail_lines=(*lines, "The Cauchy class is a constant rational."),
        )
    return Rule(
        id=_form_id(theorem.form),
        layer="base",
        stage="quantity",
        title=f"{title_left} = {shown}",
        produces=f"cauchy({shown})",
        detail_lines=lines,
    )


def real_equality_rules(
    left: Term,
    right: Term,
    left_real: RealTheorem,
    right_real: RealTheorem,
    prelude: tuple[str, ...] = (),
) -> tuple[Rule, ...]:
    title = f"{pretty(left)} = {pretty(right)}"
    lines = (
        *prelude,
        *real_trace(left_real),
        *real_trace(right_real),
        "Isabelle eq_Real: Cauchy sequences are the same real when their difference vanishes.",
        "The same normal form is the same class. realrel is reflexive on a Cauchy sequence.",
    )
    if left_real.form == right_real.form:
        return (
            Rule(
                id="math.real.eq",
                layer="base",
                stage="quantity",
                title=title,
                produces=f"identity({title})",
                detail_lines=lines,
            ),
        )
    direction = _classify(_sub_forms(left_real.form, right_real.form))
    reason = _direction_sentence(direction)
    return (_note(f"{title} is not a theorem. {reason}".rstrip()),)


def real_order_rule(
    left: Term,
    right: Term,
    left_real: RealTheorem,
    right_real: RealTheorem,
    prelude: tuple[str, ...] = (),
) -> Rule:
    diff = _sub_forms(left_real.form, right_real.form)
    direction = _classify(diff)
    title_body = f"{pretty(left)} <= {pretty(right)}"
    base = (
        *prelude,
        *real_trace(left_real),
        *real_trace(right_real),
        "Isabelle defines x < y as positive(y - x), and x <= y as x < y or x = y.",
        "positive (Real X) means some positive rational stays strictly below the tail.",
        *_separation_lines(diff, direction),
    )
    if direction == "eq":
        return Rule(
            id="math.real.le",
            layer="base",
            stage="quantity",
            title=title_body,
            produces=f"le({pretty(left)},{pretty(right)})",
            detail_lines=(*base, "The two sides have the same normal form, so realrel_refl gives equality and therefore <=."),
        )
    if direction == "lt":
        return Rule(
            id="math.real.le",
            layer="base",
            stage="quantity",
            title=title_body,
            produces=f"le({pretty(left)},{pretty(right)})",
            detail_lines=base,
        )
    if direction == "gt":
        return Rule(
            id="math.real.not_le",
            layer="base",
            stage="quantity",
            title=f"not ({title_body})",
            produces=f"not_le({pretty(left)},{pretty(right)})",
            detail_lines=base,
        )
    return _note(f"{title_body} is not settled in this slice")


def show_form(form: RealForm) -> str:
    pieces: list[tuple[str, bool]] = []
    if form.constant.num != 0 or not (
        form.terms
        or form.towers
        or form.nests
        or form.pairs
        or form.deeps
        or form.highs
        or form.peaks
        or form.crests or form.summits or form.apexes or form.shells or form.folds or form.quads or form.algebras
    ):
        pieces.append(_ratio_piece(form.constant))
    for coeff, rad in form.terms:
        pieces.append(_term_piece(coeff, rad))
    for coeff, base, numer, log_den in form.towers:
        pieces.append(_tower_piece(coeff, base, numer, log_den))
    for coeff, constant, sqrt_coeff, rad in form.nests:
        pieces.append(_nest_piece(coeff, constant, sqrt_coeff, rad))
    for coeff, left_coeff, left_rad, right_coeff, right_rad in form.pairs:
        pieces.append(_pair_piece(coeff, left_coeff, left_rad, right_coeff, right_rad))
    for coeff, mult, constant, sqrt_coeff, rad in form.deeps:
        pieces.append(_deep_piece(coeff, mult, constant, sqrt_coeff, rad))
    for coeff, mult, left_c, left_r, right_c, right_r in form.highs:
        pieces.append(_high_piece(coeff, mult, left_c, left_r, right_c, right_r))
    for coeff, pmult, hmult, left_c, left_r, right_c, right_r in form.peaks:
        pieces.append(_peak_piece(coeff, pmult, hmult, left_c, left_r, right_c, right_r))
    for coeff, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.crests:
        pieces.append(_crest_piece(coeff, qmult, pmult, hmult, left_c, left_r, right_c, right_r))
    for coeff, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.summits:
        pieces.append(
            _summit_piece(coeff, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r)
        )
    for coeff, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.apexes:
        pieces.append(
            _apex_piece(
                coeff, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
            )
        )
    for coeff, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.shells:
        pieces.append(
            _shell_piece(
                coeff, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
            )
        )
    for coeff, extra, mult, constant, sqrt_coeff, rad in form.folds:
        pieces.append(_fold_piece(coeff, extra, mult, constant, sqrt_coeff, rad))
    for coeff, constant, first_coeff, first, second_coeff, second, product_coeff in form.quads:
        pieces.append(
            _quad_piece(coeff, constant, first_coeff, first, second_coeff, second, product_coeff)
        )
    for coeff, coeffs, index in form.algebras:
        pieces.append(_algebra_piece(coeff, coeffs, index))
    parts: list[str] = []
    for index, (text, negative) in enumerate(pieces):
        if index == 0:
            parts.append(f"-{text}" if negative else text)
        elif negative:
            parts.append(f" - {text}")
        else:
            parts.append(f" + {text}")
    return "".join(parts)


def _sqrt_form(radicand: Ratio) -> RealForm:
    if radicand.num < 0:
        raise NotExact("square root of a negative stays open")
    if radicand.num == 0:
        return RealForm(_ratio(0, 1), ())
    product = radicand.num * radicand.den
    root, free = _square_part(product)
    coeff = _ratio(root, radicand.den)
    if free == 1:
        return RealForm(coeff, ())
    return RealForm(_ratio(0, 1), ((coeff, free),))


def _add_forms(left: RealForm, right: RealForm) -> RealForm:
    if left.algebras or right.algebras:
        raise NotExact("this algebraic sum stays outside")
    coeffs: dict[int, Ratio] = {}
    for coeff, rad in (*left.terms, *right.terms):
        current = coeffs.get(rad, _ratio(0, 1))
        coeffs[rad] = _qadd(current, coeff)
    terms = tuple((coeff, rad) for rad, coeff in sorted(coeffs.items()) if coeff.num != 0)
    towers: dict[tuple[int, int, int], Ratio] = {}
    for coeff, base, numer, log_den in (*left.towers, *right.towers):
        key = (base, log_den, numer)
        towers[key] = _qadd(towers.get(key, _ratio(0, 1)), coeff)
    tower_terms = tuple(
        (coeff, base, numer, log_den)
        for (base, log_den, numer), coeff in sorted(towers.items())
        if coeff.num != 0
    )
    nests: dict[tuple[int, int, int, int, int], tuple[Ratio, Ratio, int]] = {}
    nest_coeffs: dict[tuple[int, int, int, int, int], Ratio] = {}
    for coeff, constant, sqrt_coeff, rad in (*left.nests, *right.nests):
        key = _nest_key(constant, sqrt_coeff, rad)
        nest_coeffs[key] = _qadd(nest_coeffs.get(key, _ratio(0, 1)), coeff)
        nests[key] = (constant, sqrt_coeff, rad)
    nest_terms = tuple(
        (coeff, nests[key][0], nests[key][1], nests[key][2])
        for key, coeff in sorted(nest_coeffs.items())
        if coeff.num != 0
    )
    pairs: dict[tuple[int, int, int, int], Ratio] = {}
    for coeff, left_coeff, left_rad, right_coeff, right_rad in (*left.pairs, *right.pairs):
        key = (left_rad, right_rad, left_coeff, right_coeff)
        pairs[key] = _qadd(pairs.get(key, _ratio(0, 1)), coeff)
    pair_terms = tuple(
        (coeff, key[2], key[0], key[3], key[1])
        for key, coeff in sorted(pairs.items())
        if coeff.num != 0
    )
    deeps: dict[tuple[int, int, int, int], Ratio] = {}
    for coeff, mult, constant, sqrt_coeff, rad in (*left.deeps, *right.deeps):
        key = (rad, constant, sqrt_coeff, mult)
        deeps[key] = _qadd(deeps.get(key, _ratio(0, 1)), coeff)
    deep_terms = tuple(
        (coeff, key[3], key[1], key[2], key[0])
        for key, coeff in sorted(deeps.items())
        if coeff.num != 0
    )
    highs: dict[tuple[int, int, int, int, int], Ratio] = {}
    for coeff, mult, left_c, left_r, right_c, right_r in (*left.highs, *right.highs):
        key = (left_r, right_r, left_c, right_c, mult)
        highs[key] = _qadd(highs.get(key, _ratio(0, 1)), coeff)
    high_terms = tuple(
        (coeff, key[4], key[2], key[0], key[3], key[1])
        for key, coeff in sorted(highs.items())
        if coeff.num != 0
    )
    peaks: dict[tuple[int, int, int, int, int, int], Ratio] = {}
    for coeff, pmult, hmult, left_c, left_r, right_c, right_r in (*left.peaks, *right.peaks):
        key = (left_r, right_r, left_c, right_c, hmult, pmult)
        peaks[key] = _qadd(peaks.get(key, _ratio(0, 1)), coeff)
    peak_terms = tuple(
        (coeff, key[5], key[4], key[2], key[0], key[3], key[1])
        for key, coeff in sorted(peaks.items())
        if coeff.num != 0
    )
    crests: dict[tuple[int, int, int, int, int, int, int], Ratio] = {}
    for coeff, qmult, pmult, hmult, left_c, left_r, right_c, right_r in (*left.crests, *right.crests):
        key = (left_r, right_r, left_c, right_c, hmult, pmult, qmult)
        crests[key] = _qadd(crests.get(key, _ratio(0, 1)), coeff)
    crest_terms = tuple(
        (coeff, key[6], key[5], key[4], key[2], key[0], key[3], key[1])
        for key, coeff in sorted(crests.items())
        if coeff.num != 0
    )
    summits: dict[tuple[int, int, int, int, int, int, int, int], Ratio] = {}
    for coeff, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in (
        *left.summits,
        *right.summits,
    ):
        key = (left_r, right_r, left_c, right_c, hmult, pmult, qmult, smult)
        summits[key] = _qadd(summits.get(key, _ratio(0, 1)), coeff)
    summit_terms = tuple(
        (coeff, key[7], key[6], key[5], key[4], key[2], key[0], key[3], key[1])
        for key, coeff in sorted(summits.items())
        if coeff.num != 0
    )
    apexes: dict[tuple[int, int, int, int, int, int, int, int, int], Ratio] = {}
    for coeff, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in (
        *left.apexes,
        *right.apexes,
    ):
        key = (left_r, right_r, left_c, right_c, hmult, pmult, qmult, smult, amult)
        apexes[key] = _qadd(apexes.get(key, _ratio(0, 1)), coeff)
    apex_terms = tuple(
        (coeff, key[8], key[7], key[6], key[5], key[4], key[2], key[0], key[3], key[1])
        for key, coeff in sorted(apexes.items())
        if coeff.num != 0
    )
    shells: dict[tuple[int, int, int, int, int, int, int, int, int, tuple[int, ...]], Ratio] = {}
    for coeff, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in (
        *left.shells,
        *right.shells,
    ):
        key = (left_r, right_r, left_c, right_c, hmult, pmult, qmult, smult, amult, extra)
        shells[key] = _qadd(shells.get(key, _ratio(0, 1)), coeff)
    shell_terms = tuple(
        (coeff, key[9], key[8], key[7], key[6], key[5], key[4], key[2], key[0], key[3], key[1])
        for key, coeff in sorted(shells.items())
        if coeff.num != 0
    )
    folds: dict[tuple[int, int, int, int, tuple[int, ...]], Ratio] = {}
    for coeff, extra, mult, constant, sqrt_coeff, rad in (*left.folds, *right.folds):
        key = (rad, constant, sqrt_coeff, mult, extra)
        folds[key] = _qadd(folds.get(key, _ratio(0, 1)), coeff)
    fold_terms = tuple(
        (coeff, key[4], key[3], key[1], key[2], key[0])
        for key, coeff in sorted(folds.items())
        if coeff.num != 0
    )
    quads: dict[tuple[int, int, int, int, int, int, int, int, int, int], Ratio] = {}
    for coeff, constant, first_coeff, first, second_coeff, second, product_coeff in (
        *left.quads,
        *right.quads,
    ):
        key = (
            first,
            second,
            constant.num,
            constant.den,
            first_coeff.num,
            first_coeff.den,
            second_coeff.num,
            second_coeff.den,
            product_coeff.num,
            product_coeff.den,
        )
        quads[key] = _qadd(quads.get(key, _ratio(0, 1)), coeff)
    quad_terms = tuple(
        (
            coeff,
            _ratio(key[2], key[3]),
            _ratio(key[4], key[5]),
            key[0],
            _ratio(key[6], key[7]),
            key[1],
            _ratio(key[8], key[9]),
        )
        for key, coeff in sorted(quads.items())
        if coeff.num != 0
    )
    return RealForm(
        _qadd(left.constant, right.constant),
        terms,
        tower_terms,
        nest_terms,
        pair_terms,
        deep_terms,
        high_terms,
        peak_terms,
        crest_terms,
        summit_terms,
        apex_terms,
        shell_terms,
        fold_terms,
        quad_terms,
    )


def _neg_form(form: RealForm) -> RealForm:
    return RealForm(
        _qneg(form.constant),
        tuple((_qneg(coeff), rad) for coeff, rad in form.terms),
        tuple((_qneg(coeff), base, numer, log_den) for coeff, base, numer, log_den in form.towers),
        tuple(
            (_qneg(coeff), constant, sqrt_coeff, rad)
            for coeff, constant, sqrt_coeff, rad in form.nests
        ),
        tuple(
            (_qneg(coeff), left_coeff, left_rad, right_coeff, right_rad)
            for coeff, left_coeff, left_rad, right_coeff, right_rad in form.pairs
        ),
        tuple(
            (_qneg(coeff), mult, constant, sqrt_coeff, rad)
            for coeff, mult, constant, sqrt_coeff, rad in form.deeps
        ),
        tuple(
            (_qneg(coeff), mult, left_c, left_r, right_c, right_r)
            for coeff, mult, left_c, left_r, right_c, right_r in form.highs
        ),
        tuple(
            (_qneg(coeff), pmult, hmult, left_c, left_r, right_c, right_r)
            for coeff, pmult, hmult, left_c, left_r, right_c, right_r in form.peaks
        ),
        tuple(
            (_qneg(coeff), qmult, pmult, hmult, left_c, left_r, right_c, right_r)
            for coeff, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.crests
        ),
        tuple(
            (
                _qneg(coeff),
                smult,
                qmult,
                pmult,
                hmult,
                left_c,
                left_r,
                right_c,
                right_r,
            )
            for coeff, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.summits
        ),
        tuple(
            (
                _qneg(coeff),
                amult,
                smult,
                qmult,
                pmult,
                hmult,
                left_c,
                left_r,
                right_c,
                right_r,
            )
            for coeff, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.apexes
        ),
        tuple(
            (
                _qneg(coeff),
                extra,
                amult,
                smult,
                qmult,
                pmult,
                hmult,
                left_c,
                left_r,
                right_c,
                right_r,
            )
            for coeff, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.shells
        ),
        tuple(
            (_qneg(coeff), extra, mult, constant, sqrt_coeff, rad)
            for coeff, extra, mult, constant, sqrt_coeff, rad in form.folds
        ),
        tuple(
            (_qneg(coeff), constant, first_coeff, first, second_coeff, second, product_coeff)
            for coeff, constant, first_coeff, first, second_coeff, second, product_coeff in form.quads
        ),
        tuple((_qneg(coeff), coeffs, index) for coeff, coeffs, index in form.algebras),
    )


def _sub_forms(left: RealForm, right: RealForm) -> RealForm:
    return _add_forms(left, _neg_form(right))


def _uses_nested_radicals(form: RealForm) -> bool:
    return bool(
        form.nests
        or form.pairs
        or form.deeps
        or form.highs
        or form.peaks
        or form.crests
        or form.summits
        or form.apexes
        or form.shells
        or form.folds
        or form.quads
    )


def _mul_forms(left: RealForm, right: RealForm) -> RealForm:
    if _TOWER_GUARD == 0 and (_uses_nested_radicals(left) or _uses_nested_radicals(right)):
        with _tower_guard():
            towered = _mul_forms_tower(left, right)
        if towered is not None:
            return towered
    return _mul_forms_parts(left, right)


def _mul_forms_parts(left: RealForm, right: RealForm) -> RealForm:
    product = _scale(right, left.constant)
    for coeff, rad in left.terms:
        product = _add_forms(product, _mul_sqrt(coeff, rad, right))
    for coeff, base, numer, log_den in left.towers:
        product = _add_forms(product, _mul_tower(coeff, base, numer, log_den, right))
    for coeff, constant, sqrt_coeff, rad in left.nests:
        product = _add_forms(product, _mul_nest(coeff, constant, sqrt_coeff, rad, right))
    for coeff, left_coeff, left_rad, right_coeff, right_rad in left.pairs:
        product = _add_forms(
            product,
            _mul_pair(coeff, left_coeff, left_rad, right_coeff, right_rad, right),
        )
    for coeff, mult, constant, sqrt_coeff, rad in left.deeps:
        product = _add_forms(
            product,
            _mul_one_deep(coeff, mult, constant, sqrt_coeff, rad, right),
        )
    for coeff, mult, left_c, left_r, right_c, right_r in left.highs:
        product = _add_forms(
            product,
            _mul_one_high(coeff, mult, left_c, left_r, right_c, right_r, right),
        )
    for coeff, pmult, hmult, left_c, left_r, right_c, right_r in left.peaks:
        product = _add_forms(
            product,
            _mul_one_peak(coeff, pmult, hmult, left_c, left_r, right_c, right_r, right),
        )
    for coeff, qmult, pmult, hmult, left_c, left_r, right_c, right_r in left.crests:
        product = _add_forms(
            product,
            _mul_one_crest(coeff, qmult, pmult, hmult, left_c, left_r, right_c, right_r, right),
        )
    for coeff, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in left.summits:
        product = _add_forms(
            product,
            _mul_one_summit(
                coeff,
                smult,
                qmult,
                pmult,
                hmult,
                left_c,
                left_r,
                right_c,
                right_r,
                right,
            ),
        )
    for coeff, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in left.apexes:
        product = _add_forms(
            product,
            _mul_one_apex(
                coeff,
                amult,
                smult,
                qmult,
                pmult,
                hmult,
                left_c,
                left_r,
                right_c,
                right_r,
                right,
            ),
        )
    for coeff, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in left.shells:
        product = _add_forms(
            product,
            _mul_one_shell(
                coeff,
                extra,
                amult,
                smult,
                qmult,
                pmult,
                hmult,
                left_c,
                left_r,
                right_c,
                right_r,
                right,
            ),
        )
    for coeff, extra, mult, constant, sqrt_coeff, rad in left.folds:
        product = _add_forms(
            product,
            _mul_one_fold(coeff, extra, mult, constant, sqrt_coeff, rad, right),
        )
    for coeff, constant, first_coeff, first, second_coeff, second, product_coeff in left.quads:
        product = _add_forms(
            product,
            _mul_one_quad(
                coeff, constant, first_coeff, first, second_coeff, second, product_coeff, right
            ),
        )
    return product


def _mul_sqrt(coeff: Ratio, rad: int, other: RealForm) -> RealForm:
    product = RealForm(_ratio(0, 1), ())
    if other.constant.num != 0:
        product = _add_forms(product, _term_form(_qmul(coeff, other.constant), rad))
    for other_coeff, other_rad in other.terms:
        factor = _qmul(coeff, other_coeff)
        product = _add_forms(product, _scale(_sqrt_form(_ratio(rad * other_rad, 1)), factor))
    for tower_coeff, base, numer, log_den in other.towers:
        factor = _qmul(coeff, tower_coeff)
        product = _add_forms(product, _mul_powers(factor, (rad, 1, 1), (base, numer, log_den)))
    for nest_coeff, constant, sqrt_coeff, nest_rad in other.nests:
        factor = _qmul(coeff, nest_coeff)
        piece = _binomial_sqrt(
            _qmul(_ratio(rad, 1), constant),
            _qmul(_ratio(rad, 1), sqrt_coeff),
            nest_rad,
        )
        product = _add_forms(product, _scale(piece, factor))
    for pair_coeff, left_coeff, left_rad, right_coeff, right_rad in other.pairs:
        piece = _pair_sqrt(
            _qmul(_ratio(left_coeff * rad, 1), _ratio(1, 1)),
            left_rad,
            _qmul(_ratio(right_coeff * rad, 1), _ratio(1, 1)),
            right_rad,
        )
        product = _add_forms(product, _scale(piece, _qmul(coeff, pair_coeff)))
    for deep_coeff, deep_mult, deep_const, deep_sqrt, deep_rad in other.deeps:
        piece = _deep_times_term(deep_mult, deep_const, deep_sqrt, deep_rad, rad)
        product = _add_forms(product, _scale(piece, _qmul(coeff, deep_coeff)))
    for high_coeff, high_mult, left_c, left_r, right_c, right_r in other.highs:
        piece = _high_times_term(high_mult, left_c, left_r, right_c, right_r, rad)
        product = _add_forms(product, _scale(piece, _qmul(coeff, high_coeff)))
    for peak_coeff, pmult, hmult, left_c, left_r, right_c, right_r in other.peaks:
        piece = _peak_times_term(pmult, hmult, left_c, left_r, right_c, right_r, rad)
        product = _add_forms(product, _scale(piece, _qmul(coeff, peak_coeff)))
    for crest_coeff, qmult, pmult, hmult, left_c, left_r, right_c, right_r in other.crests:
        piece = _crest_times_term(qmult, pmult, hmult, left_c, left_r, right_c, right_r, rad)
        product = _add_forms(product, _scale(piece, _qmul(coeff, crest_coeff)))
    for summit_coeff, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in other.summits:
        piece = _summit_times_term(
            smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r, rad
        )
        product = _add_forms(product, _scale(piece, _qmul(coeff, summit_coeff)))
    for apex_coeff, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in other.apexes:
        piece = _apex_times_term(
            amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r, rad
        )
        product = _add_forms(product, _scale(piece, _qmul(coeff, apex_coeff)))
    for shell_coeff, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in other.shells:
        piece = _shell_times_term(
            extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r, rad
        )
        product = _add_forms(product, _scale(piece, _qmul(coeff, shell_coeff)))
    for fold_coeff, extra, mult, constant, sqrt_coeff, fold_rad in other.folds:
        piece = _fold_times_term(extra, mult, constant, sqrt_coeff, fold_rad, rad)
        product = _add_forms(product, _scale(piece, _qmul(coeff, fold_coeff)))
    for (
        quad_coeff,
        constant,
        first_coeff,
        first,
        second_coeff,
        second,
        product_coeff,
    ) in other.quads:
        piece = _quad_times_term(
            constant, first_coeff, first, second_coeff, second, product_coeff, rad
        )
        product = _add_forms(product, _scale(piece, _qmul(coeff, quad_coeff)))
    return product


def _mul_tower(coeff: Ratio, base: int, numer: int, log_den: int, other: RealForm) -> RealForm:
    product = RealForm(_ratio(0, 1), ())
    if other.constant.num != 0:
        product = _add_forms(product, _power_form(_qmul(coeff, other.constant), base, numer, log_den))
    for other_coeff, other_rad in other.terms:
        factor = _qmul(coeff, other_coeff)
        product = _add_forms(product, _mul_powers(factor, (base, numer, log_den), (other_rad, 1, 1)))
    for tower_coeff, other_base, other_numer, other_log in other.towers:
        factor = _qmul(coeff, tower_coeff)
        product = _add_forms(
            product,
            _mul_powers(factor, (base, numer, log_den), (other_base, other_numer, other_log)),
        )
    for nest_coeff, constant, sqrt_coeff, nest_rad in other.nests:
        product = _add_forms(
            product,
            _mul_tower_and_nest(
                coeff, base, numer, log_den, nest_coeff, constant, sqrt_coeff, nest_rad
            ),
        )
    if other.pairs or other.deeps or other.highs or other.peaks or other.crests or other.summits or other.apexes or other.shells or other.folds or other.quads:
        raise NotExact("this nested radical stays outside")
    return product


def _scale(form: RealForm, factor: Ratio) -> RealForm:
    if factor.num == 0:
        return RealForm(_ratio(0, 1), ())
    return RealForm(
        _qmul(form.constant, factor),
        tuple((_qmul(coeff, factor), rad) for coeff, rad in form.terms),
        tuple((_qmul(coeff, factor), base, numer, log_den) for coeff, base, numer, log_den in form.towers),
        tuple(
            (_qmul(coeff, factor), constant, sqrt_coeff, rad)
            for coeff, constant, sqrt_coeff, rad in form.nests
        ),
        tuple(
            (_qmul(coeff, factor), left_coeff, left_rad, right_coeff, right_rad)
            for coeff, left_coeff, left_rad, right_coeff, right_rad in form.pairs
        ),
        tuple(
            (_qmul(coeff, factor), mult, constant, sqrt_coeff, rad)
            for coeff, mult, constant, sqrt_coeff, rad in form.deeps
        ),
        tuple(
            (_qmul(coeff, factor), mult, left_c, left_r, right_c, right_r)
            for coeff, mult, left_c, left_r, right_c, right_r in form.highs
        ),
        tuple(
            (_qmul(coeff, factor), pmult, hmult, left_c, left_r, right_c, right_r)
            for coeff, pmult, hmult, left_c, left_r, right_c, right_r in form.peaks
        ),
        tuple(
            (_qmul(coeff, factor), qmult, pmult, hmult, left_c, left_r, right_c, right_r)
            for coeff, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.crests
        ),
        tuple(
            (
                _qmul(coeff, factor),
                smult,
                qmult,
                pmult,
                hmult,
                left_c,
                left_r,
                right_c,
                right_r,
            )
            for coeff, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.summits
        ),
        tuple(
            (
                _qmul(coeff, factor),
                amult,
                smult,
                qmult,
                pmult,
                hmult,
                left_c,
                left_r,
                right_c,
                right_r,
            )
            for coeff, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.apexes
        ),
        tuple(
            (
                _qmul(coeff, factor),
                extra,
                amult,
                smult,
                qmult,
                pmult,
                hmult,
                left_c,
                left_r,
                right_c,
                right_r,
            )
            for coeff, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.shells
        ),
        tuple(
            (_qmul(coeff, factor), extra, mult, constant, sqrt_coeff, rad)
            for coeff, extra, mult, constant, sqrt_coeff, rad in form.folds
        ),
        tuple(
            (_qmul(coeff, factor), constant, first_coeff, first, second_coeff, second, product_coeff)
            for coeff, constant, first_coeff, first, second_coeff, second, product_coeff in form.quads
        ),
        tuple((_qmul(coeff, factor), coeffs, index) for coeff, coeffs, index in form.algebras if _qmul(coeff, factor).num != 0),
    )


def _term_form(coeff: Ratio, rad: int) -> RealForm:
    if coeff.num == 0:
        return RealForm(_ratio(0, 1), ())
    return RealForm(_ratio(0, 1), ((coeff, rad),))


def _sqrt_of_form(form: RealForm) -> RealForm:
    if form.algebras:
        raise NotExact("a radicand the kernel cannot see as nonnegative stays open")
    if _is_rational(form):
        if form.constant.num < 0:
            raise NotExact("square root of a negative stays open")
        return _sqrt_form(form.constant)
    if _classify(form) == "lt":
        raise NotExact("square root of a negative stays open")
    if _classify(form) != "gt":
        raise NotExact("a radicand the kernel cannot see as nonnegative stays open")
    monomial = _as_monomial(form)
    if monomial is not None:
        return _sqrt_monomial(*monomial)
    denested = _denest(form)
    if denested is not None:
        return denested
    if (
        not form.towers
        and not form.nests
        and not form.pairs
        and not form.deeps
        and not form.highs
        and not form.peaks
        and not form.crests and not form.summits and not form.apexes and not form.shells and not form.folds and not form.quads and not form.algebras
        and len(form.terms) == 1
        and form.constant.num != 0
    ):
        coeff, rad = form.terms[0]
        return _binomial_sqrt(form.constant, coeff, rad)
    paired = _denest_two_radicals(form)
    if paired is not None:
        return paired
    if (
        not form.towers
        and not form.nests
        and not form.pairs
        and not form.deeps
        and not form.highs
        and not form.peaks
        and not form.crests and not form.summits and not form.apexes and not form.shells and not form.folds and not form.quads and not form.algebras
        and form.constant.num == 0
        and len(form.terms) == 2
    ):
        (first_coeff, first_rad), (second_coeff, second_rad) = form.terms
        return _pair_sqrt(first_coeff, first_rad, second_coeff, second_rad)
    if (
        not form.towers
        and not form.terms
        and not form.pairs
        and not form.deeps
        and not form.highs
        and not form.peaks
        and not form.crests and not form.summits and not form.apexes and not form.shells and not form.folds and not form.quads and not form.algebras
        and form.constant.num == 0
        and len(form.nests) == 1
    ):
        coeff, constant, sqrt_coeff, rad = form.nests[0]
        return _deep_sqrt(coeff, constant, sqrt_coeff, rad)
    if (
        not form.towers
        and not form.terms
        and not form.nests
        and not form.deeps
        and not form.highs
        and not form.peaks
        and not form.crests and not form.summits and not form.apexes and not form.shells and not form.folds and not form.quads and not form.algebras
        and form.constant.num == 0
        and len(form.pairs) == 1
    ):
        coeff, left_c, left_r, right_c, right_r = form.pairs[0]
        return _high_sqrt(coeff, left_c, left_r, right_c, right_r)
    if (
        not form.towers
        and not form.terms
        and not form.nests
        and not form.pairs
        and not form.deeps
        and not form.peaks
        and not form.crests and not form.summits and not form.apexes and not form.shells and not form.folds and not form.quads and not form.algebras
        and form.constant.num == 0
        and len(form.highs) == 1
    ):
        coeff, hmult, left_c, left_r, right_c, right_r = form.highs[0]
        return _peak_sqrt(coeff, hmult, left_c, left_r, right_c, right_r)
    if (
        not form.towers
        and not form.terms
        and not form.nests
        and not form.pairs
        and not form.deeps
        and not form.highs
        and not form.crests and not form.summits and not form.apexes and not form.shells and not form.folds and not form.quads and not form.algebras
        and form.constant.num == 0
        and len(form.peaks) == 1
    ):
        coeff, pmult, hmult, left_c, left_r, right_c, right_r = form.peaks[0]
        return _crest_sqrt(coeff, pmult, hmult, left_c, left_r, right_c, right_r)
    if (
        not form.towers
        and not form.terms
        and not form.nests
        and not form.pairs
        and not form.deeps
        and not form.highs
        and not form.peaks
        and not form.summits and not form.apexes and not form.shells and not form.folds and not form.quads and not form.algebras
        and form.constant.num == 0
        and len(form.crests) == 1
    ):
        coeff, qmult, pmult, hmult, left_c, left_r, right_c, right_r = form.crests[0]
        return _summit_sqrt(coeff, qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    if (
        not form.towers
        and not form.terms
        and not form.nests
        and not form.pairs
        and not form.deeps
        and not form.highs
        and not form.peaks
        and not form.crests
        and not form.apexes and not form.shells and not form.folds and not form.quads and not form.algebras
        and form.constant.num == 0
        and len(form.summits) == 1
    ):
        coeff, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r = form.summits[0]
        return _apex_sqrt(coeff, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    if (
        not form.towers
        and not form.terms
        and not form.nests
        and not form.pairs
        and not form.deeps
        and not form.highs
        and not form.peaks
        and not form.crests
        and not form.summits
        and not form.shells and not form.folds and not form.quads and not form.algebras
        and form.constant.num == 0
        and len(form.apexes) == 1
    ):
        coeff, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r = form.apexes[0]
        return _shell_from_apex(
            coeff, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
        )
    if (
        not form.towers
        and not form.terms
        and not form.nests
        and not form.pairs
        and not form.deeps
        and not form.highs
        and not form.peaks
        and not form.crests
        and not form.summits
        and not form.apexes
        and form.constant.num == 0
        and len(form.shells) == 1
    ):
        (
            coeff,
            extra,
            amult,
            smult,
            qmult,
            pmult,
            hmult,
            left_c,
            left_r,
            right_c,
            right_r,
        ) = form.shells[0]
        return _shell_from_shell(
            coeff, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
        )
    if (
        not form.towers
        and not form.terms
        and not form.nests
        and not form.pairs
        and not form.highs
        and not form.peaks
        and not form.crests
        and not form.summits
        and not form.apexes
        and not form.shells
        and not form.folds and not form.quads and not form.algebras
        and form.constant.num == 0
        and len(form.deeps) == 1
    ):
        coeff, mult, constant, sqrt_coeff, rad = form.deeps[0]
        return _fold_from_deep(coeff, mult, constant, sqrt_coeff, rad)
    if (
        not form.towers
        and not form.terms
        and not form.nests
        and not form.pairs
        and not form.deeps
        and not form.highs
        and not form.peaks
        and not form.crests
        and not form.summits
        and not form.apexes
        and not form.shells
        and form.constant.num == 0
        and len(form.folds) == 1
    ):
        coeff, extra, mult, constant, sqrt_coeff, rad = form.folds[0]
        return _fold_from_fold(coeff, extra, mult, constant, sqrt_coeff, rad)
    if (
        not form.towers
        and not form.nests
        and not form.pairs
        and not form.deeps
        and not form.highs
        and not form.peaks
        and not form.crests
        and not form.summits
        and not form.apexes
        and not form.shells
        and not form.folds
        and not form.quads
        and _as_biquadratic(form) is not None
    ):
        return _quad_sqrt(form)
    raise NotExact("this nested radical stays outside")


def _sqrt_lines(operand: RealForm, result: RealForm) -> tuple[str, ...]:
    if _is_rational(operand):
        lines = [
            "Square factors are extracted. sqrt(a/b) = sqrt(a*b) / b, and the square part of a*b moves into the coefficient.",
        ]
        if result.terms:
            lines.extend(_certificate_lines(result.terms[0][1]))
        else:
            lines.append("The radicand is a perfect square, so the sequence is constant.")
            lines.append("Isabelle cauchy_const. Isabelle of_rat_Real embeds that rational.")
        return tuple(lines)
    lines: list[str] = []
    if _as_monomial(operand) is None:
        lines.append("Isabelle real_sqrt_unique: y^2 = x and 0 <= y implies sqrt x = y.")
        lines.append("The ansatz squares back to the radicand, and the result is nonnegative.")
    else:
        lines.append("Isabelle real_sqrt_mult: for nonnegative factors, sqrt(x * y) = sqrt x * sqrt y.")
        lines.append("Isabelle real_sqrt_pow2: 0 <= x implies (sqrt x)^2 = x. Iterating gives the nested root.")
        lines.append("Isabelle real_sqrt_ge_zero: the root is nonnegative.")
        lines.append("Isabelle real_sqrt_unique: a nonnegative y whose power is the radicand is the root.")
    if any(
        base > 1 and _square_part(base) != (1, base)
        for _coeff, base, _numer, _log_den in result.towers
    ):
        lines.append("Isabelle real_root_mult: root n (x * y) = root n x * root n y.")
        lines.append("Isabelle real_root_power: 0 < n implies root n (x ^ k) = root n x ^ k.")
        lines.append("Isabelle real_root_mult_exp: root (m * n) x = root m (root n x).")
    for _coeff, rad in result.terms:
        lines.extend(_certificate_lines(rad))
    for _coeff, base, numer, log_den in result.towers:
        lines.extend(_tower_certificate_lines(base, numer, log_den))
    for _coeff, constant, sqrt_coeff, rad in result.nests:
        lines.extend(_nest_certificate_lines(constant.num, sqrt_coeff.num, rad))
    for _coeff, left_coeff, left_rad, right_coeff, right_rad in result.pairs:
        lines.extend(_pair_certificate_lines(left_coeff, left_rad, right_coeff, right_rad))
    for _coeff, mult, constant, sqrt_coeff, rad in result.deeps:
        lines.extend(_deep_certificate_lines(mult, constant, sqrt_coeff, rad))
    for _coeff, mult, left_c, left_r, right_c, right_r in result.highs:
        lines.extend(_high_certificate_lines(mult, left_c, left_r, right_c, right_r))
    for _coeff, pmult, hmult, left_c, left_r, right_c, right_r in result.peaks:
        lines.extend(_peak_certificate_lines(pmult, hmult, left_c, left_r, right_c, right_r))
    for _coeff, qmult, pmult, hmult, left_c, left_r, right_c, right_r in result.crests:
        lines.extend(_crest_certificate_lines(qmult, pmult, hmult, left_c, left_r, right_c, right_r))
    for _coeff, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in result.summits:
        lines.extend(
            _summit_certificate_lines(smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r)
        )
    for (
        _coeff,
        amult,
        smult,
        qmult,
        pmult,
        hmult,
        left_c,
        left_r,
        right_c,
        right_r,
    ) in result.apexes:
        lines.extend(
            _apex_certificate_lines(
                amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
            )
        )
    for (
        _coeff,
        extra,
        amult,
        smult,
        qmult,
        pmult,
        hmult,
        left_c,
        left_r,
        right_c,
        right_r,
    ) in result.shells:
        lines.extend(
            _shell_certificate_lines(
                extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
            )
        )
    for _coeff, extra, mult, constant, sqrt_coeff, rad in result.folds:
        lines.extend(_fold_certificate_lines(extra, mult, constant, sqrt_coeff, rad))
    for (
        _coeff,
        constant,
        first_coeff,
        first,
        second_coeff,
        second,
        product_coeff,
    ) in result.quads:
        lines.extend(
            _quad_certificate_lines(constant, first_coeff, first, second_coeff, second, product_coeff)
        )
    if _is_rational(result):
        lines.append("The power reduced to a constant sequence.")
        lines.append("Isabelle cauchy_const. Isabelle of_rat_Real embeds that rational.")
    return tuple(lines)


def _as_monomial(form: RealForm) -> tuple[Ratio, int, int, int] | None:
    if form.nests or form.pairs or form.deeps or form.highs or form.peaks or form.crests or form.summits or form.apexes or form.shells or form.folds or form.quads or form.algebras or form.constant.num != 0 or (form.terms and form.towers):
        return None
    if len(form.terms) == 1 and not form.towers:
        coeff, rad = form.terms[0]
        if coeff.num <= 0:
            return None
        return coeff, rad, 1, 1
    if len(form.towers) == 1 and not form.terms:
        coeff, base, numer, log_den = form.towers[0]
        if coeff.num <= 0:
            return None
        return coeff, base, numer, log_den
    return None


def _sqrt_monomial(coeff: Ratio, base: int, numer: int, log_den: int) -> RealForm:
    if coeff.num < 0:
        raise NotExact("square root of a negative stays open")
    if coeff.num == 0:
        return RealForm(_ratio(0, 1), ())
    root = _sqrt_form(coeff)
    raised = _power_form(_ratio(1, 1), base, numer, log_den + 1)
    return _mul_forms(root, raised)


def _denest(form: RealForm) -> RealForm | None:
    if form.towers or form.nests or form.pairs or form.deeps or form.highs or form.peaks or form.crests or form.summits or form.apexes or form.shells or form.folds or form.quads or form.algebras or len(form.terms) != 1 or form.constant.num == 0:
        return None
    coeff, rad = form.terms[0]
    if coeff.num == 0:
        return None
    discriminant = _qsub(_qmul(form.constant, form.constant), _qmul(_ratio(rad, 1), _qmul(coeff, coeff)))
    root = _rational_square_root(discriminant)
    if root is None:
        return None
    half = _ratio(1, 2)
    larger = _qmul(_qadd(form.constant, root), half)
    smaller = _qmul(_qsub(form.constant, root), half)
    if larger.num < 0 or smaller.num < 0:
        return None
    left = _sqrt_form(larger)
    right = _sqrt_form(smaller)
    result = _add_forms(left, right) if coeff.num > 0 else _sub_forms(left, right)
    if _mul_forms(result, result) != form:
        return None
    if _classify(result) not in {"gt", "eq"}:
        return None
    return result


def _nest_key(constant: Ratio, sqrt_coeff: Ratio, rad: int) -> tuple[int, int, int, int, int]:
    return (rad, constant.num, constant.den, sqrt_coeff.num, sqrt_coeff.den)


def _nest_form(coeff: Ratio, constant: Ratio, sqrt_coeff: Ratio, rad: int) -> RealForm:
    if coeff.num == 0:
        return RealForm(_ratio(0, 1), ())
    return RealForm(_ratio(0, 1), (), (), ((coeff, constant, sqrt_coeff, rad),))


def _nest_times_pair(
    constant: Ratio,
    sqrt_coeff: Ratio,
    rad: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> RealForm:
    nest_inside = RealForm(constant, ((sqrt_coeff, rad),) if sqrt_coeff.num != 0 else ())
    pair_inside = _pair_inside(left_c, left_r, right_c, right_r)
    return _sqrt_of_form(_mul_forms(nest_inside, pair_inside))


def _mul_nest(coeff: Ratio, constant: Ratio, sqrt_coeff: Ratio, rad: int, other: RealForm) -> RealForm:
    piece = _nest_form(coeff, constant, sqrt_coeff, rad)
    product = _scale(piece, other.constant) if other.constant.num != 0 else RealForm(_ratio(0, 1), ())
    for other_coeff, other_rad in other.terms:
        scaled = _binomial_sqrt(
            _qmul(_ratio(other_rad, 1), constant),
            _qmul(_ratio(other_rad, 1), sqrt_coeff),
            rad,
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, other_coeff)))
    for tower_coeff, base, numer, log_den in other.towers:
        product = _add_forms(
            product,
            _mul_tower_and_nest(
                tower_coeff, base, numer, log_den, coeff, constant, sqrt_coeff, rad
            ),
        )
    for other_coeff, other_const, other_sqrt, other_rad in other.nests:
        if other_rad != rad:
            raise NotExact("this nested radical stays outside")
        mixed_const = _qadd(
            _qmul(constant, other_const),
            _qmul(_qmul(sqrt_coeff, other_sqrt), _ratio(rad, 1)),
        )
        mixed_sqrt = _qadd(_qmul(constant, other_sqrt), _qmul(sqrt_coeff, other_const))
        scaled = _binomial_sqrt(mixed_const, mixed_sqrt, rad)
        product = _add_forms(product, _scale(scaled, _qmul(coeff, other_coeff)))
    for deep_coeff, deep_mult, deep_const, deep_sqrt, deep_rad in other.deeps:
        if (
            deep_rad != rad
            or constant.den != 1
            or sqrt_coeff.den != 1
            or deep_const == 0
        ):
            raise NotExact("this nested radical stays outside")
        piece = _deep_times_nest(
            deep_mult,
            deep_const,
            deep_sqrt,
            constant.num,
            sqrt_coeff.num,
            rad,
        )
        product = _add_forms(product, _scale(piece, _qmul(coeff, deep_coeff)))
    for pair_coeff, left_c, left_r, right_c, right_r in other.pairs:
        piece = _nest_times_pair(constant, sqrt_coeff, rad, left_c, left_r, right_c, right_r)
        product = _add_forms(product, _scale(piece, _qmul(coeff, pair_coeff)))
    for fold_coeff, extra, fold_mult, fold_const, fold_sqrt, fold_rad in other.folds:
        scaled = _fold_times_nest(
            extra, fold_mult, fold_const, fold_sqrt, fold_rad, constant, sqrt_coeff, rad
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, fold_coeff)))
    if other.highs or other.peaks or other.crests or other.summits or other.apexes or other.shells or other.quads:
        raise NotExact("this nested radical stays outside")
    return product


def _mul_tower_and_nest(
    tower_coeff: Ratio,
    base: int,
    numer: int,
    log_den: int,
    nest_coeff: Ratio,
    constant: Ratio,
    sqrt_coeff: Ratio,
    rad: int,
) -> RealForm:
    unit = _power_form(_ratio(1, 1), base, numer, log_den)
    squared = _mul_forms(unit, unit)
    if squared.towers or squared.nests or squared.pairs or squared.deeps or squared.highs or squared.peaks or squared.crests or squared.summits or squared.apexes or squared.shells or squared.folds or len(squared.terms) > 1:
        raise NotExact("this nested radical stays outside")
    if squared.terms and squared.terms[0][1] != rad:
        raise NotExact("this nested radical stays outside")
    radical = squared.terms[0][0] if squared.terms else _ratio(0, 1)
    mixed_const = _qadd(
        _qmul(squared.constant, constant),
        _qmul(_qmul(radical, sqrt_coeff), _ratio(rad, 1)),
    )
    mixed_sqrt = _qadd(_qmul(squared.constant, sqrt_coeff), _qmul(radical, constant))
    piece = _binomial_sqrt(mixed_const, mixed_sqrt, rad)
    return _scale(piece, _qmul(tower_coeff, nest_coeff))


def _binomial_positive(constant: int, sqrt_coeff: int, rad: int) -> bool:
    if sqrt_coeff == 0:
        return constant > 0
    if constant >= 0 and sqrt_coeff > 0:
        return True
    if constant <= 0 and sqrt_coeff < 0:
        return False
    gap = constant * constant - rad * sqrt_coeff * sqrt_coeff
    if sqrt_coeff < 0:
        return gap > 0
    return gap < 0


def _binomial_sqrt(constant: Ratio, sqrt_coeff: Ratio, rad: int) -> RealForm:
    if sqrt_coeff.num == 0:
        if constant.num < 0:
            raise NotExact("square root of a negative stays open")
        return _sqrt_form(constant)
    if rad <= 1 or _square_part(rad) != (1, rad):
        raise KernelError("binomial radicand was not square-free")
    denominator = constant.den * sqrt_coeff.den
    base_const = constant.num * sqrt_coeff.den
    base_sqrt = sqrt_coeff.num * constant.den
    integer_const = base_const * denominator
    integer_sqrt = base_sqrt * denominator
    if integer_const == 0 and integer_sqrt == 0:
        return RealForm(_ratio(0, 1), ())
    content = _gcd(abs(integer_const), abs(integer_sqrt))
    root, _free = _square_part(content)
    square = root * root
    reduced_const = integer_const // square
    reduced_sqrt = integer_sqrt // square
    scale = _qdiv(_ratio(root, 1), _ratio(denominator, 1))
    if reduced_const == 0:
        if reduced_sqrt < 0:
            raise NotExact("square root of a negative stays open")
        return _scale(_sqrt_monomial(_ratio(reduced_sqrt, 1), rad, 1, 1), scale)
    if not _binomial_positive(reduced_const, reduced_sqrt, rad):
        raise NotExact("square root of a negative stays open")
    operand = RealForm(_ratio(reduced_const, 1), ((_ratio(reduced_sqrt, 1), rad),))
    discriminant = _qsub(
        _qmul(operand.constant, operand.constant),
        _qmul(_ratio(rad, 1), _qmul(operand.terms[0][0], operand.terms[0][0])),
    )
    expected = _scale(operand, _qmul(scale, scale))
    if _rational_square_root(discriminant) is not None:
        denested = _denest(operand)
        if denested is None:
            raise KernelError("binomial square root did not denest")
        result = _scale(denested, scale)
        squared = _mul_forms(result, result)
    else:
        result = _nest_form(scale, operand.constant, operand.terms[0][0], rad)
        squared = _square_nest(result)
    if squared != expected:
        raise KernelError("binomial square disagreed")
    if _classify(result) not in {"gt", "eq"}:
        raise KernelError("binomial root was not nonnegative")
    return result


def _square_nest(form: RealForm) -> RealForm:
    if (
        form.constant.num != 0
        or form.terms
        or form.towers
        or form.pairs
        or form.deeps
        or form.highs or form.peaks or form.crests or form.summits or form.apexes or form.shells or form.folds or form.quads or form.algebras
        or len(form.nests) != 1
    ):
        raise KernelError("binomial square left the nest")
    coeff, constant, sqrt_coeff, rad = form.nests[0]
    inside = RealForm(constant, ((sqrt_coeff, rad),))
    return _scale(inside, _qmul(coeff, coeff))


def _denest_two_radicals(form: RealForm) -> RealForm | None:
    """sqrt(A*sqrt(m) + B*sqrt(n)) when A^2*m - B^2*n is a rational square.

    The larger square is the shared radicand. Each half is a binomial whose
    own discriminant is the negative of the other square, so it stays a nest.
    The sign of the smaller term chooses the sum or the difference.
    """

    if (
        form.constant.num != 0
        or form.towers
        or form.nests
        or form.pairs
        or form.deeps
        or form.highs or form.peaks or form.crests or form.summits or form.apexes or form.shells or form.folds or form.quads or form.algebras
        or len(form.terms) != 2
    ):
        return None
    (first_coeff, first_rad), (second_coeff, second_rad) = form.terms
    first_square = _qmul(_qmul(first_coeff, first_coeff), _ratio(first_rad, 1))
    second_square = _qmul(_qmul(second_coeff, second_coeff), _ratio(second_rad, 1))
    if _qcmp(first_square, second_square) > 0:
        major_coeff, major_rad = first_coeff, first_rad
        minor_coeff = second_coeff
        gap = _qsub(first_square, second_square)
    else:
        major_coeff, major_rad = second_coeff, second_rad
        minor_coeff = first_coeff
        gap = _qsub(second_square, first_square)
    if gap.num <= 0:
        return None
    if major_coeff.num <= 0:
        raise KernelError("two-radical major term was not positive")
    root = _rational_square_root(gap)
    if root is None:
        return None
    half = _ratio(1, 2)
    shared = _qmul(major_coeff, half)
    left = _binomial_sqrt(_qmul(root, half), shared, major_rad)
    right = _binomial_sqrt(_qmul(_qneg(root), half), shared, major_rad)
    result = _add_forms(left, right) if minor_coeff.num > 0 else _sub_forms(left, right)
    if _mul_forms(result, result) != form:
        raise KernelError("two-radical square disagreed")
    if _classify(result) not in {"gt", "eq"}:
        raise KernelError("two-radical root was not nonnegative")
    return result


def _pair_inside(left_c: int, left_r: int, right_c: int, right_r: int) -> RealForm:
    return _add_forms(
        _term_form(_ratio(left_c, 1), left_r),
        _term_form(_ratio(right_c, 1), right_r),
    )


def _pair_form(coeff: Ratio, left_c: int, left_r: int, right_c: int, right_r: int) -> RealForm:
    if coeff.num == 0:
        return RealForm(_ratio(0, 1), ())
    return RealForm(_ratio(0, 1), (), (), (), ((coeff, left_c, left_r, right_c, right_r),))


def _pair_sqrt(left_coeff: Ratio, left_rad: int, right_coeff: Ratio, right_rad: int) -> RealForm:
    """sqrt(A*sqrt(m) + B*sqrt(n)) when A^2*m - B^2*n is not a rational square.

    The nonnegative root is the nested radical. A gap that is a rational square
    returns the older denesting instead of storing a pair. The square check
    multiplies the two insides, so it does not call `_pair_sqrt` again.
    """

    if left_rad == right_rad:
        return _sqrt_monomial(_qadd(left_coeff, right_coeff), left_rad, 1, 1)
    if left_rad > right_rad:
        left_coeff, left_rad, right_coeff, right_rad = right_coeff, right_rad, left_coeff, left_rad
    if (
        left_rad <= 1
        or right_rad <= 1
        or _square_part(left_rad) != (1, left_rad)
        or _square_part(right_rad) != (1, right_rad)
    ):
        raise KernelError("pair radicand was not square-free")
    denominator = left_coeff.den * right_coeff.den
    if denominator < 1:
        raise KernelError("pair coefficient was not a rational")
    integer_left = left_coeff.num * right_coeff.den
    integer_right = right_coeff.num * left_coeff.den
    root, free = _square_part(denominator)
    integer_left *= free
    integer_right *= free
    if integer_left == 0 and integer_right == 0:
        return RealForm(_ratio(0, 1), ())
    if integer_left == 0:
        monomial = _sqrt_monomial(_ratio(integer_right, 1), right_rad, 1, 1)
        return _scale(monomial, _ratio(1, root * free))
    if integer_right == 0:
        monomial = _sqrt_monomial(_ratio(integer_left, 1), left_rad, 1, 1)
        return _scale(monomial, _ratio(1, root * free))
    content = _gcd(abs(integer_left), abs(integer_right))
    square_root, _square_free = _square_part(content)
    square = square_root * square_root
    integer_left //= square
    integer_right //= square
    outer = _ratio(square_root, root * free)
    if integer_left * integer_left * left_rad == integer_right * integer_right * right_rad:
        raise KernelError("pair squares were equal")
    if not _pair_inside_positive(integer_left, left_rad, integer_right, right_rad):
        raise NotExact("square root of a negative stays open")
    inside = _pair_inside(integer_left, left_rad, integer_right, right_rad)
    expected = _scale(inside, _qmul(outer, outer))
    denested = _denest_two_radicals(inside)
    if denested is not None:
        result = _scale(denested, outer)
    else:
        result = _pair_form(outer, integer_left, left_rad, integer_right, right_rad)
    try:
        squared = _mul_forms(result, result)
    except NotExact as exc:
        raise KernelError("pair square disagreed") from exc
    if squared != expected:
        raise KernelError("pair square disagreed")
    if _classify(result) not in {"gt", "eq"}:
        raise KernelError("pair root was not nonnegative")
    return result


def _mul_pair(
    coeff: Ratio,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    other: RealForm,
) -> RealForm:
    piece = _pair_form(coeff, left_c, left_r, right_c, right_r)
    product = _scale(piece, other.constant) if other.constant.num != 0 else RealForm(_ratio(0, 1), ())
    for other_coeff, other_rad in other.terms:
        scaled = _pair_sqrt(
            _ratio(left_c * other_rad, 1),
            left_r,
            _ratio(right_c * other_rad, 1),
            right_r,
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, other_coeff)))
    for nest_coeff, nest_const, nest_sqrt, nest_rad in other.nests:
        piece = _nest_times_pair(nest_const, nest_sqrt, nest_rad, left_c, left_r, right_c, right_r)
        product = _add_forms(product, _scale(piece, _qmul(coeff, nest_coeff)))
    if other.towers or other.deeps:
        raise NotExact("this nested radical stays outside")
    for other_coeff, other_left, other_left_rad, other_right, other_right_rad in other.pairs:
        if other_left_rad != left_r or other_right_rad != right_r:
            raise NotExact("this nested radical stays outside")
        if left_c == other_left and right_c == other_right:
            # sqrt((A*sqrt(m) + B*sqrt(n))^2) is the positive inside.
            combined = _pair_inside(left_c, left_r, right_c, right_r)
        elif left_c == -other_left and right_c == -other_right:
            combined = _pair_inside(-left_c, left_r, -right_c, right_r)
        else:
            rational = left_c * other_left * left_r + right_c * other_right * right_r
            cross = left_c * other_right + right_c * other_left
            # Same two radicals: the product of the insides is one binomial, not another pair.
            combined = _sqrt_of_crossed(rational, cross, left_r * right_r)
        product = _add_forms(product, _scale(combined, _qmul(coeff, other_coeff)))
    for high_coeff, high_mult, high_left, high_left_rad, high_right, high_right_rad in other.highs:
        if high_left_rad != left_r or high_right_rad != right_r:
            raise NotExact("this nested radical stays outside")
        scaled = _high_times_pair(
            high_mult, high_left, left_r, high_right, right_r, left_c, right_c
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, high_coeff)))
    for peak_coeff, pmult, hmult, peak_left, peak_left_rad, peak_right, peak_right_rad in other.peaks:
        if peak_left_rad != left_r or peak_right_rad != right_r:
            raise NotExact("this nested radical stays outside")
        scaled = _peak_times_pair(
            pmult, hmult, peak_left, left_r, peak_right, right_r, left_c, right_c
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, peak_coeff)))
    for crest_coeff, qmult, pmult, hmult, crest_left, crest_left_rad, crest_right, crest_right_rad in other.crests:
        if crest_left_rad != left_r or crest_right_rad != right_r:
            raise NotExact("this nested radical stays outside")
        scaled = _crest_times_pair(
            qmult, pmult, hmult, crest_left, left_r, crest_right, right_r, left_c, right_c
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, crest_coeff)))
    if other.summits or other.apexes or other.shells or other.folds or other.quads:
        raise NotExact("this nested radical stays outside")
    return product


def _sqrt_of_crossed(rational: int, cross: int, rad: int) -> RealForm:
    if rad < 1:
        raise KernelError("pair product radicand was not positive")
    if cross == 0:
        if rational < 0:
            raise NotExact("square root of a negative stays open")
        return _sqrt_form(_ratio(rational, 1))
    root, free = _square_part(rad)
    radical_coeff = cross * root
    if free == 1:
        total = rational + radical_coeff
        if total < 0:
            raise NotExact("square root of a negative stays open")
        return _sqrt_form(_ratio(total, 1))
    return _binomial_sqrt(_ratio(rational, 1), _ratio(radical_coeff, 1), free)


def _deep_form(coeff: Ratio, mult: int, constant: int, sqrt_coeff: int, rad: int) -> RealForm:
    if coeff.num == 0:
        return RealForm(_ratio(0, 1), ())
    return RealForm(_ratio(0, 1), (), (), (), (), ((coeff, mult, constant, sqrt_coeff, rad),))


def _deep_sqrt(coeff: Ratio, constant: Ratio, sqrt_coeff: Ratio, rad: int) -> RealForm:
    """sqrt of one binomial nest whose own discriminant is not a rational square.

    The nonnegative root is the nested radical. The square check scales the nest
    by the squared outer coefficient and does not call `_deep_sqrt` again.
    """

    if coeff.num < 0:
        raise NotExact("square root of a negative stays open")
    if coeff.num == 0:
        return RealForm(_ratio(0, 1), ())
    if coeff.den < 1:
        raise KernelError("deep coefficient was not a rational")
    if constant.den != 1 or sqrt_coeff.den != 1 or constant.num == 0 or sqrt_coeff.num == 0:
        raise KernelError("deep binomial was not reduced")
    if rad <= 1 or _square_part(rad) != (1, rad):
        raise KernelError("deep radicand was not square-free")
    content = _gcd(abs(constant.num), abs(sqrt_coeff.num))
    if _square_part(content)[0] != 1:
        raise KernelError("deep binomial was not reduced")
    if not _binomial_positive(constant.num, sqrt_coeff.num, rad):
        raise NotExact("square root of a negative stays open")
    if _denest(RealForm(constant, ((sqrt_coeff, rad),))) is not None:
        raise KernelError("deep binomial denested")
    root, free = _square_part(coeff.num * coeff.den)
    outer = _ratio(root, coeff.den)
    result = _deep_form(outer, free, constant.num, sqrt_coeff.num, rad)
    expected = _nest_form(coeff, constant, sqrt_coeff, rad)
    squared = _square_deep(result)
    if squared != expected:
        raise KernelError("deep square disagreed")
    if _classify(result) not in {"gt", "eq"}:
        raise KernelError("deep root was not nonnegative")
    return result


def _square_deep(form: RealForm) -> RealForm:
    if (
        form.constant.num != 0
        or form.terms
        or form.towers
        or form.nests
        or form.pairs
        or form.highs or form.peaks or form.crests or form.summits or form.apexes or form.shells or form.folds or form.quads or form.algebras
        or len(form.deeps) != 1
    ):
        raise KernelError("deep square left the radical")
    outer, mult, constant, sqrt_coeff, rad = form.deeps[0]
    nest = _nest_form(_ratio(1, 1), _ratio(constant, 1), _ratio(sqrt_coeff, 1), rad)
    return _scale(nest, _qmul(_qmul(outer, outer), _ratio(mult, 1)))


def _fourth_root_binomial(constant: int, sqrt_coeff: int, rad: int) -> RealForm:
    if constant == 0 and sqrt_coeff == 0:
        return RealForm(_ratio(0, 1), ())
    if sqrt_coeff == 0:
        if constant < 0:
            raise NotExact("square root of a negative stays open")
        return _sqrt_of_form(_sqrt_form(_ratio(constant, 1)))
    once = _binomial_sqrt(_ratio(constant, 1), _ratio(sqrt_coeff, 1), rad)
    return _sqrt_of_form(once)


def _deep_times_term(mult: int, constant: int, sqrt_coeff: int, rad: int, other_rad: int) -> RealForm:
    scale = (mult * other_rad) * (mult * other_rad)
    return _fourth_root_binomial(scale * constant, scale * sqrt_coeff, rad)


def _deep_times_nest(
    mult: int,
    deep_const: int,
    deep_sqrt: int,
    nest_const: int,
    nest_sqrt: int,
    rad: int,
) -> RealForm:
    square_const = nest_const * nest_const + nest_sqrt * nest_sqrt * rad
    square_sqrt = 2 * nest_const * nest_sqrt
    prod_const = deep_const * square_const + deep_sqrt * square_sqrt * rad
    prod_sqrt = deep_const * square_sqrt + deep_sqrt * square_const
    scale = mult * mult
    return _fourth_root_binomial(scale * prod_const, scale * prod_sqrt, rad)


def _deep_times_deep(
    left_mult: int,
    left_const: int,
    left_sqrt: int,
    right_mult: int,
    right_const: int,
    right_sqrt: int,
    rad: int,
) -> RealForm:
    prod_const = left_const * right_const + left_sqrt * right_sqrt * rad
    prod_sqrt = left_const * right_sqrt + left_sqrt * right_const
    scale = (left_mult * right_mult) * (left_mult * right_mult)
    return _fourth_root_binomial(scale * prod_const, scale * prod_sqrt, rad)


def _mul_one_deep(
    coeff: Ratio,
    mult: int,
    constant: int,
    sqrt_coeff: int,
    rad: int,
    other: RealForm,
) -> RealForm:
    piece = _deep_form(coeff, mult, constant, sqrt_coeff, rad)
    product = _scale(piece, other.constant) if other.constant.num != 0 else RealForm(_ratio(0, 1), ())
    for other_coeff, other_rad in other.terms:
        scaled = _deep_times_term(mult, constant, sqrt_coeff, rad, other_rad)
        product = _add_forms(product, _scale(scaled, _qmul(coeff, other_coeff)))
    if other.towers:
        raise NotExact("this nested radical stays outside")
    for nest_coeff, nest_const, nest_sqrt, nest_rad in other.nests:
        if nest_rad != rad or nest_const.den != 1 or nest_sqrt.den != 1:
            raise NotExact("this nested radical stays outside")
        scaled = _deep_times_nest(
            mult,
            constant,
            sqrt_coeff,
            nest_const.num,
            nest_sqrt.num,
            rad,
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, nest_coeff)))
    if other.pairs:
        raise NotExact("this nested radical stays outside")
    for deep_coeff, deep_mult, deep_const, deep_sqrt, deep_rad in other.deeps:
        if deep_rad != rad:
            raise NotExact("this nested radical stays outside")
        scaled = _deep_times_deep(
            mult,
            constant,
            sqrt_coeff,
            deep_mult,
            deep_const,
            deep_sqrt,
            rad,
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, deep_coeff)))
    for fold_coeff, extra, fold_mult, fold_const, fold_sqrt, fold_rad in other.folds:
        scaled = _fold_times_deep(
            extra,
            fold_mult,
            fold_const,
            fold_sqrt,
            fold_rad,
            mult,
            constant,
            sqrt_coeff,
            rad,
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, fold_coeff)))
    if other.highs or other.peaks or other.crests or other.summits or other.apexes or other.shells or other.quads:
        raise NotExact("this nested radical stays outside")
    return product


def _high_form(
    coeff: Ratio,
    mult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> RealForm:
    if coeff.num == 0:
        return RealForm(_ratio(0, 1), ())
    return RealForm(
        _ratio(0, 1),
        (),
        (),
        (),
        (),
        (),
        ((coeff, mult, left_c, left_r, right_c, right_r),),
    )


def _high_sqrt(coeff: Ratio, left_c: int, left_r: int, right_c: int, right_r: int) -> RealForm:
    """sqrt of one positive pair whose squares differ by a non-square.

    The nonnegative root is the nested radical. The square check scales the pair
    by the squared outer coefficient and does not call `_high_sqrt` again.
    """

    if coeff.num < 0:
        raise NotExact("square root of a negative stays open")
    if coeff.num == 0:
        return RealForm(_ratio(0, 1), ())
    if coeff.den < 1:
        raise KernelError("high coefficient was not a rational")
    if left_c == 0 or right_c == 0 or left_r <= 1 or right_r <= left_r:
        raise KernelError("high pair was not reduced")
    if _square_part(left_r) != (1, left_r) or _square_part(right_r) != (1, right_r):
        raise KernelError("high radicand was not square-free")
    content = _gcd(abs(left_c), abs(right_c))
    if _square_part(content)[0] != 1:
        raise KernelError("high pair was not reduced")
    if left_c * left_c * left_r == right_c * right_c * right_r:
        raise KernelError("high pair squares were equal")
    if not _pair_inside_positive(left_c, left_r, right_c, right_r):
        raise NotExact("square root of a negative stays open")
    if _denest_two_radicals(_pair_inside(left_c, left_r, right_c, right_r)) is not None:
        raise KernelError("high pair denested")
    root, free = _square_part(coeff.num * coeff.den)
    outer = _ratio(root, coeff.den)
    result = _high_form(outer, free, left_c, left_r, right_c, right_r)
    expected = _pair_form(coeff, left_c, left_r, right_c, right_r)
    squared = _square_high(result)
    if squared != expected:
        raise KernelError("high square disagreed")
    if _classify(result) not in {"gt", "eq"}:
        raise KernelError("high root was not nonnegative")
    return result


def _square_high(form: RealForm) -> RealForm:
    if (
        form.constant.num != 0
        or form.terms
        or form.towers
        or form.nests
        or form.pairs
        or form.deeps
        or form.peaks
        or form.crests or form.summits or form.apexes or form.shells or form.folds or form.quads or form.algebras
        or len(form.highs) != 1
    ):
        raise KernelError("high square left the radical")
    outer, mult, left_c, left_r, right_c, right_r = form.highs[0]
    pair = _pair_form(_ratio(1, 1), left_c, left_r, right_c, right_r)
    return _scale(pair, _qmul(_qmul(outer, outer), _ratio(mult, 1)))


def _fourth_root_pair(left_c: int, left_r: int, right_c: int, right_r: int) -> RealForm:
    if left_c == 0 and right_c == 0:
        return RealForm(_ratio(0, 1), ())
    once = _sqrt_of_form(_pair_inside(left_c, left_r, right_c, right_r))
    return _sqrt_of_form(once)


def _high_times_term(
    mult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    other_rad: int,
) -> RealForm:
    scale = (mult * other_rad) * (mult * other_rad)
    return _fourth_root_pair(scale * left_c, left_r, scale * right_c, right_r)


def _high_times_pair(
    mult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    pair_left: int,
    pair_right: int,
) -> RealForm:
    rational = pair_left * pair_left * left_r + pair_right * pair_right * right_r
    cross = 2 * pair_left * pair_right
    new_left = left_c * rational + right_c * cross * right_r
    new_right = right_c * rational + left_c * cross * left_r
    scale = mult * mult
    return _fourth_root_pair(scale * new_left, left_r, scale * new_right, right_r)


def _high_times_high(
    left_mult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    right_mult: int,
    other_left: int,
    other_right: int,
) -> RealForm:
    rational = left_c * other_left * left_r + right_c * other_right * right_r
    cross = left_c * other_right + right_c * other_left
    scale = left_mult * right_mult
    squared = scale * scale
    root, free = _square_part(left_r * right_r)
    if free == 1:
        return _fourth_root_binomial(squared * (rational + cross * root), 0, 2)
    return _fourth_root_binomial(squared * rational, squared * cross * root, free)


def _mul_one_high(
    coeff: Ratio,
    mult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    other: RealForm,
) -> RealForm:
    piece = _high_form(coeff, mult, left_c, left_r, right_c, right_r)
    product = _scale(piece, other.constant) if other.constant.num != 0 else RealForm(_ratio(0, 1), ())
    for other_coeff, other_rad in other.terms:
        scaled = _high_times_term(mult, left_c, left_r, right_c, right_r, other_rad)
        product = _add_forms(product, _scale(scaled, _qmul(coeff, other_coeff)))
    if other.towers or other.nests or other.deeps:
        raise NotExact("this nested radical stays outside")
    for pair_coeff, pair_left, pair_left_rad, pair_right, pair_right_rad in other.pairs:
        if pair_left_rad != left_r or pair_right_rad != right_r:
            raise NotExact("this nested radical stays outside")
        scaled = _high_times_pair(mult, left_c, left_r, right_c, right_r, pair_left, pair_right)
        product = _add_forms(product, _scale(scaled, _qmul(coeff, pair_coeff)))
    for high_coeff, high_mult, high_left, high_left_rad, high_right, high_right_rad in other.highs:
        if high_left_rad != left_r or high_right_rad != right_r:
            raise NotExact("this nested radical stays outside")
        scaled = _high_times_high(
            mult,
            left_c,
            left_r,
            right_c,
            right_r,
            high_mult,
            high_left,
            high_right,
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, high_coeff)))
    for peak_coeff, pmult, hmult, peak_left, peak_left_rad, peak_right, peak_right_rad in other.peaks:
        if peak_left_rad != left_r or peak_right_rad != right_r:
            raise NotExact("this nested radical stays outside")
        scaled = _peak_times_high(
            pmult, hmult, peak_left, left_r, peak_right, right_r, mult, left_c, right_c
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, peak_coeff)))
    for crest_coeff, qmult, pmult, hmult, crest_left, crest_left_rad, crest_right, crest_right_rad in other.crests:
        if crest_left_rad != left_r or crest_right_rad != right_r:
            raise NotExact("this nested radical stays outside")
        scaled = _crest_times_high(
            qmult, pmult, hmult, crest_left, left_r, crest_right, right_r, mult, left_c, right_c
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, crest_coeff)))
    if other.summits or other.apexes or other.shells or other.folds or other.quads:
        raise NotExact("this nested radical stays outside")
    return product


def _peak_form(
    coeff: Ratio,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> RealForm:
    if coeff.num == 0:
        return RealForm(_ratio(0, 1), ())
    return RealForm(
        _ratio(0, 1),
        (),
        (),
        (),
        (),
        (),
        (),
        ((coeff, pmult, hmult, left_c, left_r, right_c, right_r),),
    )


def _peak_sqrt(coeff: Ratio, hmult: int, left_c: int, left_r: int, right_c: int, right_r: int) -> RealForm:
    """sqrt of one positive high whose pair does not denest.

    The nonnegative root is the nested radical. The square check scales the high
    by the squared outer coefficient and does not call `_peak_sqrt` again.
    """

    if coeff.num < 0:
        raise NotExact("square root of a negative stays open")
    if coeff.num == 0:
        return RealForm(_ratio(0, 1), ())
    if coeff.den < 1:
        raise KernelError("peak coefficient was not a rational")
    if hmult < 1:
        raise KernelError("peak multiplier was not positive")
    if _square_part(hmult) != (1, hmult):
        raise KernelError("peak radicand was not square-free")
    if left_c == 0 or right_c == 0 or left_r <= 1 or right_r <= left_r:
        raise KernelError("peak pair was not reduced")
    if _square_part(left_r) != (1, left_r) or _square_part(right_r) != (1, right_r):
        raise KernelError("peak radicand was not square-free")
    content = _gcd(abs(left_c), abs(right_c))
    if _square_part(content)[0] != 1:
        raise KernelError("peak pair was not reduced")
    if left_c * left_c * left_r == right_c * right_c * right_r:
        raise KernelError("peak pair squares were equal")
    if not _pair_inside_positive(left_c, left_r, right_c, right_r):
        raise NotExact("square root of a negative stays open")
    if _denest_two_radicals(_pair_inside(left_c, left_r, right_c, right_r)) is not None:
        raise KernelError("peak pair denested")
    root, free = _square_part(coeff.num * coeff.den)
    outer = _ratio(root, coeff.den)
    result = _peak_form(outer, free, hmult, left_c, left_r, right_c, right_r)
    expected = _high_form(coeff, hmult, left_c, left_r, right_c, right_r)
    squared = _square_peak(result)
    if squared != expected:
        raise KernelError("peak square disagreed")
    if _classify(result) not in {"gt", "eq"}:
        raise KernelError("peak root was not nonnegative")
    return result


def _square_peak(form: RealForm) -> RealForm:
    if (
        form.constant.num != 0
        or form.terms
        or form.towers
        or form.nests
        or form.pairs
        or form.deeps
        or form.highs
        or form.crests or form.summits or form.apexes or form.shells or form.folds or form.quads or form.algebras
        or len(form.peaks) != 1
    ):
        raise KernelError("peak square left the radical")
    outer, pmult, hmult, left_c, left_r, right_c, right_r = form.peaks[0]
    high = _high_form(_ratio(1, 1), hmult, left_c, left_r, right_c, right_r)
    return _scale(high, _qmul(_qmul(outer, outer), _ratio(pmult, 1)))


def _peak_times_term(
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    other_rad: int,
) -> RealForm:
    return _peak_sqrt(_ratio(other_rad * pmult, 1), hmult, left_c, left_r, right_c, right_r)


def _peak_times_peak(
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    other_pmult: int,
    other_hmult: int,
    other_left: int,
    other_right: int,
) -> RealForm:
    high_product = _high_times_high(
        hmult,
        left_c,
        left_r,
        right_c,
        right_r,
        other_hmult,
        other_left,
        other_right,
    )
    return _sqrt_of_form(_scale(high_product, _ratio(pmult * other_pmult, 1)))


def _peak_times_pair(
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    pair_left: int,
    pair_right: int,
) -> RealForm:
    core = _high_form(_ratio(1, 1), hmult, left_c, left_r, right_c, right_r)
    pair = _pair_form(_ratio(1, 1), pair_left, left_r, pair_right, right_r)
    # P * pair = sqrt(P^2 * pair^2) = sqrt((core * pair) * pair). Associate
    # through the already closed high-times-pair product, not through core
    # times the field element pair^2, which splits into a sum whose square
    # root stays outside.
    mixed = _mul_forms(_mul_forms(core, pair), pair)
    return _sqrt_of_form(_scale(mixed, _ratio(pmult, 1)))


def _peak_times_high(
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    high_mult: int,
    high_left: int,
    high_right: int,
) -> RealForm:
    core = _high_form(_ratio(1, 1), hmult, left_c, left_r, right_c, right_r)
    other = _high_form(_ratio(1, 1), high_mult, high_left, left_r, high_right, right_r)
    squared = _square_high(other)
    return _sqrt_of_form(_scale(_mul_forms(core, squared), _ratio(pmult, 1)))


def _mul_one_peak(
    coeff: Ratio,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    other: RealForm,
) -> RealForm:
    piece = _peak_form(coeff, pmult, hmult, left_c, left_r, right_c, right_r)
    product = _scale(piece, other.constant) if other.constant.num != 0 else RealForm(_ratio(0, 1), ())
    for other_coeff, other_rad in other.terms:
        scaled = _peak_times_term(pmult, hmult, left_c, left_r, right_c, right_r, other_rad)
        product = _add_forms(product, _scale(scaled, _qmul(coeff, other_coeff)))
    for pair_coeff, pair_left, pair_left_rad, pair_right, pair_right_rad in other.pairs:
        if pair_left_rad != left_r or pair_right_rad != right_r:
            raise NotExact("this nested radical stays outside")
        scaled = _peak_times_pair(
            pmult, hmult, left_c, left_r, right_c, right_r, pair_left, pair_right
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, pair_coeff)))
    for high_coeff, high_mult, high_left, high_left_rad, high_right, high_right_rad in other.highs:
        if high_left_rad != left_r or high_right_rad != right_r:
            raise NotExact("this nested radical stays outside")
        scaled = _peak_times_high(
            pmult, hmult, left_c, left_r, right_c, right_r, high_mult, high_left, high_right
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, high_coeff)))
    for crest_coeff, qmult, crest_pmult, crest_hmult, crest_left, crest_left_rad, crest_right, crest_right_rad in other.crests:
        if crest_left_rad != left_r or crest_right_rad != right_r:
            raise NotExact("this nested radical stays outside")
        scaled = _crest_times_peak(
            qmult,
            crest_pmult,
            crest_hmult,
            crest_left,
            left_r,
            crest_right,
            right_r,
            pmult,
            hmult,
            left_c,
            right_c,
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, crest_coeff)))
    if other.towers or other.nests or other.deeps or other.summits or other.apexes or other.shells or other.folds or other.quads:
        raise NotExact("this nested radical stays outside")
    for (
        peak_coeff,
        other_pmult,
        other_hmult,
        other_left,
        other_left_rad,
        other_right,
        other_right_rad,
    ) in other.peaks:
        if other_left_rad != left_r or other_right_rad != right_r:
            raise NotExact("this nested radical stays outside")
        scaled = _peak_times_peak(
            pmult,
            hmult,
            left_c,
            left_r,
            right_c,
            right_r,
            other_pmult,
            other_hmult,
            other_left,
            other_right,
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, peak_coeff)))
    return product


def _crest_form(
    coeff: Ratio,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> RealForm:
    if coeff.num == 0:
        return RealForm(_ratio(0, 1), ())
    return RealForm(
        _ratio(0, 1),
        (),
        (),
        (),
        (),
        (),
        (),
        (),
        ((coeff, qmult, pmult, hmult, left_c, left_r, right_c, right_r),),
    )


def _crest_sqrt(
    coeff: Ratio,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> RealForm:
    """sqrt of one positive peak whose pair does not denest.

    The nonnegative root is the nested radical. The square check scales the peak
    by the squared outer coefficient and does not call `_crest_sqrt` again.
    """

    if coeff.num < 0:
        raise NotExact("square root of a negative stays open")
    if coeff.num == 0:
        return RealForm(_ratio(0, 1), ())
    if coeff.den < 1:
        raise KernelError("crest coefficient was not a rational")
    if pmult < 1 or hmult < 1:
        raise KernelError("crest multiplier was not positive")
    if _square_part(pmult) != (1, pmult) or _square_part(hmult) != (1, hmult):
        raise KernelError("crest radicand was not square-free")
    if left_c == 0 or right_c == 0 or left_r <= 1 or right_r <= left_r:
        raise KernelError("crest pair was not reduced")
    if _square_part(left_r) != (1, left_r) or _square_part(right_r) != (1, right_r):
        raise KernelError("crest radicand was not square-free")
    content = _gcd(abs(left_c), abs(right_c))
    if _square_part(content)[0] != 1:
        raise KernelError("crest pair was not reduced")
    if left_c * left_c * left_r == right_c * right_c * right_r:
        raise KernelError("crest pair squares were equal")
    if not _pair_inside_positive(left_c, left_r, right_c, right_r):
        raise NotExact("square root of a negative stays open")
    if _denest_two_radicals(_pair_inside(left_c, left_r, right_c, right_r)) is not None:
        raise KernelError("crest pair denested")
    root, free = _square_part(coeff.num * coeff.den)
    outer = _ratio(root, coeff.den)
    result = _crest_form(outer, free, pmult, hmult, left_c, left_r, right_c, right_r)
    expected = _peak_form(coeff, pmult, hmult, left_c, left_r, right_c, right_r)
    squared = _square_crest(result)
    if squared != expected:
        raise KernelError("crest square disagreed")
    if _classify(result) not in {"gt", "eq"}:
        raise KernelError("crest root was not nonnegative")
    return result


def _square_crest(form: RealForm) -> RealForm:
    if (
        form.constant.num != 0
        or form.terms
        or form.towers
        or form.nests
        or form.pairs
        or form.deeps
        or form.highs
        or form.peaks
        or form.summits or form.apexes or form.shells or form.folds or form.quads or form.algebras
        or len(form.crests) != 1
    ):
        raise KernelError("crest square left the radical")
    outer, qmult, pmult, hmult, left_c, left_r, right_c, right_r = form.crests[0]
    peak = _peak_form(_ratio(1, 1), pmult, hmult, left_c, left_r, right_c, right_r)
    return _scale(peak, _qmul(_qmul(outer, outer), _ratio(qmult, 1)))


def _crest_times_term(
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    other_rad: int,
) -> RealForm:
    return _crest_sqrt(_ratio(other_rad * qmult, 1), pmult, hmult, left_c, left_r, right_c, right_r)


def _crest_times_crest(
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    other_qmult: int,
    other_pmult: int,
    other_hmult: int,
    other_left: int,
    other_right: int,
) -> RealForm:
    peak_product = _peak_times_peak(
        pmult,
        hmult,
        left_c,
        left_r,
        right_c,
        right_r,
        other_pmult,
        other_hmult,
        other_left,
        other_right,
    )
    return _sqrt_of_form(_scale(peak_product, _ratio(qmult * other_qmult, 1)))


def _crest_times_pair(
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    pair_left: int,
    pair_right: int,
) -> RealForm:
    core = _peak_form(_ratio(1, 1), pmult, hmult, left_c, left_r, right_c, right_r)
    pair = _pair_form(_ratio(1, 1), pair_left, left_r, pair_right, right_r)
    # C * pair = sqrt((core * pair) * pair). Associate through the already
    # closed peak-times-pair product.
    mixed = _mul_forms(_mul_forms(core, pair), pair)
    return _sqrt_of_form(_scale(mixed, _ratio(qmult, 1)))


def _crest_times_high(
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    high_mult: int,
    high_left: int,
    high_right: int,
) -> RealForm:
    core = _peak_form(_ratio(1, 1), pmult, hmult, left_c, left_r, right_c, right_r)
    other = _high_form(_ratio(1, 1), high_mult, high_left, left_r, high_right, right_r)
    squared = _square_high(other)
    return _sqrt_of_form(_scale(_mul_forms(core, squared), _ratio(qmult, 1)))


def _crest_times_peak(
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    peak_pmult: int,
    peak_hmult: int,
    peak_left: int,
    peak_right: int,
) -> RealForm:
    core = _peak_form(_ratio(1, 1), pmult, hmult, left_c, left_r, right_c, right_r)
    other = _peak_form(_ratio(1, 1), peak_pmult, peak_hmult, peak_left, left_r, peak_right, right_r)
    squared = _square_peak(other)
    return _sqrt_of_form(_scale(_mul_forms(core, squared), _ratio(qmult, 1)))


def _mul_one_crest(
    coeff: Ratio,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    other: RealForm,
) -> RealForm:
    piece = _crest_form(coeff, qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    product = _scale(piece, other.constant) if other.constant.num != 0 else RealForm(_ratio(0, 1), ())
    for other_coeff, other_rad in other.terms:
        scaled = _crest_times_term(qmult, pmult, hmult, left_c, left_r, right_c, right_r, other_rad)
        product = _add_forms(product, _scale(scaled, _qmul(coeff, other_coeff)))
    for pair_coeff, pair_left, pair_left_rad, pair_right, pair_right_rad in other.pairs:
        if pair_left_rad != left_r or pair_right_rad != right_r:
            raise NotExact("this nested radical stays outside")
        scaled = _crest_times_pair(
            qmult, pmult, hmult, left_c, left_r, right_c, right_r, pair_left, pair_right
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, pair_coeff)))
    for high_coeff, high_mult, high_left, high_left_rad, high_right, high_right_rad in other.highs:
        if high_left_rad != left_r or high_right_rad != right_r:
            raise NotExact("this nested radical stays outside")
        scaled = _crest_times_high(
            qmult, pmult, hmult, left_c, left_r, right_c, right_r, high_mult, high_left, high_right
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, high_coeff)))
    for (
        peak_coeff,
        peak_pmult,
        peak_hmult,
        peak_left,
        peak_left_rad,
        peak_right,
        peak_right_rad,
    ) in other.peaks:
        if peak_left_rad != left_r or peak_right_rad != right_r:
            raise NotExact("this nested radical stays outside")
        scaled = _crest_times_peak(
            qmult,
            pmult,
            hmult,
            left_c,
            left_r,
            right_c,
            right_r,
            peak_pmult,
            peak_hmult,
            peak_left,
            peak_right,
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, peak_coeff)))
    if (
        other.towers
        or other.nests
        or other.deeps
        or other.summits or other.apexes or other.shells or other.folds or other.quads
    ):
        raise NotExact("this nested radical stays outside")
    for (
        crest_coeff,
        other_qmult,
        other_pmult,
        other_hmult,
        other_left,
        other_left_rad,
        other_right,
        other_right_rad,
    ) in other.crests:
        if other_left_rad != left_r or other_right_rad != right_r:
            raise NotExact("this nested radical stays outside")
        scaled = _crest_times_crest(
            qmult,
            pmult,
            hmult,
            left_c,
            left_r,
            right_c,
            right_r,
            other_qmult,
            other_pmult,
            other_hmult,
            other_left,
            other_right,
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, crest_coeff)))
    return product



def _summit_form(
    coeff: Ratio,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> RealForm:
    if coeff.num == 0:
        return RealForm(_ratio(0, 1), ())
    return RealForm(
        _ratio(0, 1),
        (),
        (),
        (),
        (),
        (),
        (),
        (),
        (),
        ((coeff, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r),),
    )


def _summit_sqrt(
    coeff: Ratio,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> RealForm:
    """sqrt of one positive crest whose pair does not denest.

    The nonnegative root is the nested radical. The square check scales the crest
    by the squared outer coefficient and does not call `_summit_sqrt` again.
    """

    if coeff.num < 0:
        raise NotExact("square root of a negative stays open")
    if coeff.num == 0:
        return RealForm(_ratio(0, 1), ())
    if coeff.den < 1:
        raise KernelError("summit coefficient was not a rational")
    if qmult < 1 or pmult < 1 or hmult < 1:
        raise KernelError("summit multiplier was not positive")
    if (
        _square_part(qmult) != (1, qmult)
        or _square_part(pmult) != (1, pmult)
        or _square_part(hmult) != (1, hmult)
    ):
        raise KernelError("summit radicand was not square-free")
    if left_c == 0 or right_c == 0 or left_r <= 1 or right_r <= left_r:
        raise KernelError("summit pair was not reduced")
    if _square_part(left_r) != (1, left_r) or _square_part(right_r) != (1, right_r):
        raise KernelError("summit radicand was not square-free")
    content = _gcd(abs(left_c), abs(right_c))
    if _square_part(content)[0] != 1:
        raise KernelError("summit pair was not reduced")
    if left_c * left_c * left_r == right_c * right_c * right_r:
        raise KernelError("summit pair squares were equal")
    if not _pair_inside_positive(left_c, left_r, right_c, right_r):
        raise NotExact("square root of a negative stays open")
    if _denest_two_radicals(_pair_inside(left_c, left_r, right_c, right_r)) is not None:
        raise KernelError("summit pair denested")
    root, free = _square_part(coeff.num * coeff.den)
    outer = _ratio(root, coeff.den)
    result = _summit_form(outer, free, qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    expected = _crest_form(coeff, qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    squared = _square_summit(result)
    if squared != expected:
        raise KernelError("summit square disagreed")
    if _classify(result) not in {"gt", "eq"}:
        raise KernelError("summit root was not nonnegative")
    return result


def _square_summit(form: RealForm) -> RealForm:
    if (
        form.constant.num != 0
        or form.terms
        or form.towers
        or form.nests
        or form.pairs
        or form.deeps
        or form.highs
        or form.peaks
        or form.crests
        or form.apexes or form.shells or form.folds or form.quads or form.algebras
        or len(form.summits) != 1
    ):
        raise KernelError("summit square left the radical")
    outer, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r = form.summits[0]
    crest = _crest_form(_ratio(1, 1), qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    return _scale(crest, _qmul(_qmul(outer, outer), _ratio(smult, 1)))


def _summit_times_term(
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    other_rad: int,
) -> RealForm:
    return _summit_sqrt(_ratio(other_rad * smult, 1), qmult, pmult, hmult, left_c, left_r, right_c, right_r)


def _summit_times_summit(
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    other_smult: int,
    other_qmult: int,
    other_pmult: int,
    other_hmult: int,
    other_left: int,
    other_right: int,
) -> RealForm:
    crest_product = _crest_times_crest(
        qmult,
        pmult,
        hmult,
        left_c,
        left_r,
        right_c,
        right_r,
        other_qmult,
        other_pmult,
        other_hmult,
        other_left,
        other_right,
    )
    return _sqrt_of_form(_scale(crest_product, _ratio(smult * other_smult, 1)))


def _mul_one_summit(
    coeff: Ratio,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    other: RealForm,
) -> RealForm:
    piece = _summit_form(coeff, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    product = _scale(piece, other.constant) if other.constant.num != 0 else RealForm(_ratio(0, 1), ())
    for other_coeff, other_rad in other.terms:
        scaled = _summit_times_term(
            smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r, other_rad
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, other_coeff)))
    if (
        other.towers
        or other.nests
        or other.pairs
        or other.deeps
        or other.highs
        or other.peaks
        or other.crests
        or other.apexes or other.shells or other.folds or other.quads
    ):
        raise NotExact("this nested radical stays outside")
    for (
        summit_coeff,
        other_smult,
        other_qmult,
        other_pmult,
        other_hmult,
        other_left,
        other_left_rad,
        other_right,
        other_right_rad,
    ) in other.summits:
        if other_left_rad != left_r or other_right_rad != right_r:
            raise NotExact("this nested radical stays outside")
        scaled = _summit_times_summit(
            smult,
            qmult,
            pmult,
            hmult,
            left_c,
            left_r,
            right_c,
            right_r,
            other_smult,
            other_qmult,
            other_pmult,
            other_hmult,
            other_left,
            other_right,
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, summit_coeff)))
    return product



def _apex_form(
    coeff: Ratio,
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> RealForm:
    if coeff.num == 0:
        return RealForm(_ratio(0, 1), ())
    return RealForm(
        _ratio(0, 1),
        (),
        (),
        (),
        (),
        (),
        (),
        (),
        (),
        (),
        ((coeff, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r),),
    )


def _apex_sqrt(
    coeff: Ratio,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> RealForm:
    """sqrt of one positive summit whose pair does not denest.

    The nonnegative root is the nested radical. The square check scales the summit
    by the squared outer coefficient and does not call `_apex_sqrt` again.
    """

    if coeff.num < 0:
        raise NotExact("square root of a negative stays open")
    if coeff.num == 0:
        return RealForm(_ratio(0, 1), ())
    if coeff.den < 1:
        raise KernelError("apex coefficient was not a rational")
    if smult < 1 or qmult < 1 or pmult < 1 or hmult < 1:
        raise KernelError("apex multiplier was not positive")
    if (
        _square_part(smult) != (1, smult)
        or _square_part(qmult) != (1, qmult)
        or _square_part(pmult) != (1, pmult)
        or _square_part(hmult) != (1, hmult)
    ):
        raise KernelError("apex radicand was not square-free")
    if left_c == 0 or right_c == 0 or left_r <= 1 or right_r <= left_r:
        raise KernelError("apex pair was not reduced")
    if _square_part(left_r) != (1, left_r) or _square_part(right_r) != (1, right_r):
        raise KernelError("apex radicand was not square-free")
    content = _gcd(abs(left_c), abs(right_c))
    if _square_part(content)[0] != 1:
        raise KernelError("apex pair was not reduced")
    if left_c * left_c * left_r == right_c * right_c * right_r:
        raise KernelError("apex pair squares were equal")
    if not _pair_inside_positive(left_c, left_r, right_c, right_r):
        raise NotExact("square root of a negative stays open")
    if _denest_two_radicals(_pair_inside(left_c, left_r, right_c, right_r)) is not None:
        raise KernelError("apex pair denested")
    root, free = _square_part(coeff.num * coeff.den)
    outer = _ratio(root, coeff.den)
    result = _apex_form(
        outer, free, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    )
    expected = _summit_form(coeff, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    squared = _square_apex(result)
    if squared != expected:
        raise KernelError("apex square disagreed")
    if _classify(result) not in {"gt", "eq"}:
        raise KernelError("apex root was not nonnegative")
    return result


def _square_apex(form: RealForm) -> RealForm:
    if (
        form.constant.num != 0
        or form.terms
        or form.towers
        or form.nests
        or form.pairs
        or form.deeps
        or form.highs
        or form.peaks
        or form.crests
        or form.summits
        or form.shells or form.folds or form.quads or form.algebras
        or len(form.apexes) != 1
    ):
        raise KernelError("apex square left the radical")
    outer, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r = form.apexes[0]
    summit = _summit_form(_ratio(1, 1), smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    return _scale(summit, _qmul(_qmul(outer, outer), _ratio(amult, 1)))


def _apex_times_term(
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    other_rad: int,
) -> RealForm:
    return _apex_sqrt(
        _ratio(other_rad * amult, 1), smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    )


def _apex_times_apex(
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    other_amult: int,
    other_smult: int,
    other_qmult: int,
    other_pmult: int,
    other_hmult: int,
    other_left: int,
    other_right: int,
) -> RealForm:
    summit_product = _summit_times_summit(
        smult,
        qmult,
        pmult,
        hmult,
        left_c,
        left_r,
        right_c,
        right_r,
        other_smult,
        other_qmult,
        other_pmult,
        other_hmult,
        other_left,
        other_right,
    )
    return _sqrt_of_form(_scale(summit_product, _ratio(amult * other_amult, 1)))


def _mul_one_apex(
    coeff: Ratio,
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    other: RealForm,
) -> RealForm:
    piece = _apex_form(
        coeff, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    )
    product = _scale(piece, other.constant) if other.constant.num != 0 else RealForm(_ratio(0, 1), ())
    for other_coeff, other_rad in other.terms:
        scaled = _apex_times_term(
            amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r, other_rad
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, other_coeff)))
    if (
        other.towers
        or other.nests
        or other.pairs
        or other.deeps
        or other.highs
        or other.peaks
        or other.crests
        or other.summits
        or other.shells or other.folds or other.quads
    ):
        raise NotExact("this nested radical stays outside")
    for (
        apex_coeff,
        other_amult,
        other_smult,
        other_qmult,
        other_pmult,
        other_hmult,
        other_left,
        other_left_rad,
        other_right,
        other_right_rad,
    ) in other.apexes:
        if other_left_rad != left_r or other_right_rad != right_r:
            raise NotExact("this nested radical stays outside")
        scaled = _apex_times_apex(
            amult,
            smult,
            qmult,
            pmult,
            hmult,
            left_c,
            left_r,
            right_c,
            right_r,
            other_amult,
            other_smult,
            other_qmult,
            other_pmult,
            other_hmult,
            other_left,
            other_right,
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, apex_coeff)))
    return product


def _shell_form(
    coeff: Ratio,
    extra: tuple[int, ...],
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> RealForm:
    if coeff.num == 0:
        return RealForm(_ratio(0, 1), ())
    return RealForm(
        _ratio(0, 1),
        (),
        shells=(
            (coeff, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r),
        ),
    )


def _shell_core(
    extra: tuple[int, ...],
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> RealForm:
    """Radicand of the outermost square root, with coefficient 1."""

    if len(extra) == 1:
        return _apex_form(
            _ratio(1, 1), amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
        )
    return _shell_form(
        _ratio(1, 1),
        extra[1:],
        amult,
        smult,
        qmult,
        pmult,
        hmult,
        left_c,
        left_r,
        right_c,
        right_r,
    )


def _square_shell(form: RealForm) -> RealForm:
    if (
        form.constant.num != 0
        or form.terms
        or form.towers
        or form.nests
        or form.pairs
        or form.deeps
        or form.highs
        or form.peaks
        or form.crests
        or form.summits
        or form.apexes
        or form.folds or form.quads or form.algebras
        or len(form.shells) != 1
    ):
        raise KernelError("shell square left the radical")
    outer, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r = form.shells[0]
    core = _shell_core(extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    return _scale(core, _qmul(_qmul(outer, outer), _ratio(extra[0], 1)))


def _check_shell_base(
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> None:
    base = _apex_form(
        _ratio(1, 1), amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    )
    if not _canonical(base):
        raise KernelError("shell apex was not canonical")
    if _classify(base) != "gt":
        raise NotExact("square root of a negative stays open")


def _check_extra(extra: tuple[int, ...]) -> None:
    if not extra:
        raise KernelError("shell depth was empty")
    for mult in extra:
        if mult < 1 or _square_part(mult) != (1, mult):
            raise KernelError("shell multiplier was not square-free")


def _shell_from_apex(
    coeff: Ratio,
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> RealForm:
    """Nonnegative square root of one positive apex.

    Every further finite nesting is this same radical with one more square root.
    The square check scales the apex and does not call `_shell_from_apex` again.
    """

    if coeff.num < 0:
        raise NotExact("square root of a negative stays open")
    if coeff.num == 0:
        return RealForm(_ratio(0, 1), ())
    if coeff.den < 1:
        raise KernelError("shell coefficient was not a rational")
    _check_shell_base(amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    root, free = _square_part(coeff.num * coeff.den)
    outer = _ratio(root, coeff.den)
    result = _shell_form(
        outer, (free,), amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    )
    expected = _apex_form(
        coeff, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    )
    if _square_shell(result) != expected:
        raise KernelError("shell square disagreed")
    if _classify(result) not in {"gt", "eq"}:
        raise KernelError("shell root was not nonnegative")
    return result


def _shell_from_shell(
    coeff: Ratio,
    extra: tuple[int, ...],
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> RealForm:
    """One more square root of a shell. The depth tuple grows by one."""

    if coeff.num < 0:
        raise NotExact("square root of a negative stays open")
    if coeff.num == 0:
        return RealForm(_ratio(0, 1), ())
    if coeff.den < 1:
        raise KernelError("shell coefficient was not a rational")
    _check_extra(extra)
    _check_shell_base(amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    root, free = _square_part(coeff.num * coeff.den)
    outer = _ratio(root, coeff.den)
    result = _shell_form(
        outer,
        (free,) + extra,
        amult,
        smult,
        qmult,
        pmult,
        hmult,
        left_c,
        left_r,
        right_c,
        right_r,
    )
    expected = _shell_form(
        coeff, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    )
    if _square_shell(result) != expected:
        raise KernelError("shell square disagreed")
    if _classify(result) not in {"gt", "eq"}:
        raise KernelError("shell root was not nonnegative")
    return result


def _shell_times_term(
    extra: tuple[int, ...],
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    other_rad: int,
) -> RealForm:
    core = _shell_core(extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    return _sqrt_of_form(_scale(core, _ratio(extra[0] * other_rad, 1)))


def _shell_times_shell(
    extra: tuple[int, ...],
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    other_extra: tuple[int, ...],
    other_amult: int,
    other_smult: int,
    other_qmult: int,
    other_pmult: int,
    other_hmult: int,
    other_left: int,
    other_left_rad: int,
    other_right: int,
    other_right_rad: int,
) -> RealForm:
    left = _shell_core(extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    right = _shell_core(
        other_extra,
        other_amult,
        other_smult,
        other_qmult,
        other_pmult,
        other_hmult,
        other_left,
        other_left_rad,
        other_right,
        other_right_rad,
    )
    product = _mul_forms(left, right)
    return _sqrt_of_form(_scale(product, _ratio(extra[0] * other_extra[0], 1)))


def _mul_one_shell(
    coeff: Ratio,
    extra: tuple[int, ...],
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    other: RealForm,
) -> RealForm:
    piece = _shell_form(
        coeff, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    )
    product = _scale(piece, other.constant) if other.constant.num != 0 else RealForm(_ratio(0, 1), ())
    for other_coeff, other_rad in other.terms:
        scaled = _shell_times_term(
            extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r, other_rad
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, other_coeff)))
    if (
        other.towers
        or other.nests
        or other.pairs
        or other.deeps
        or other.highs
        or other.peaks
        or other.crests
        or other.summits
        or other.apexes
        or other.folds or other.quads
    ):
        raise NotExact("this nested radical stays outside")
    for (
        shell_coeff,
        other_extra,
        other_amult,
        other_smult,
        other_qmult,
        other_pmult,
        other_hmult,
        other_left,
        other_left_rad,
        other_right,
        other_right_rad,
    ) in other.shells:
        scaled = _shell_times_shell(
            extra,
            amult,
            smult,
            qmult,
            pmult,
            hmult,
            left_c,
            left_r,
            right_c,
            right_r,
            other_extra,
            other_amult,
            other_smult,
            other_qmult,
            other_pmult,
            other_hmult,
            other_left,
            other_left_rad,
            other_right,
            other_right_rad,
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, shell_coeff)))
    return product


def _invert_shell(form: RealForm) -> RealForm:
    if (
        form.constant.num != 0
        or form.terms
        or form.towers
        or form.nests
        or form.pairs
        or form.deeps
        or form.highs
        or form.peaks
        or form.crests
        or form.summits
        or form.apexes
        or form.folds or form.quads or form.algebras
        or len(form.shells) != 1
    ):
        raise NotExact("this quotient stays outside")
    return _sqrt_of_form(_inverse_form(_square_shell(form)))


def _fold_form(
    coeff: Ratio,
    extra: tuple[int, ...],
    mult: int,
    constant: int,
    sqrt_coeff: int,
    rad: int,
) -> RealForm:
    if coeff.num == 0:
        return RealForm(_ratio(0, 1), ())
    return RealForm(
        _ratio(0, 1),
        (),
        folds=((coeff, extra, mult, constant, sqrt_coeff, rad),),
    )


def _fold_core(
    extra: tuple[int, ...],
    mult: int,
    constant: int,
    sqrt_coeff: int,
    rad: int,
) -> RealForm:
    """Radicand of the outermost square root, with coefficient 1."""

    if len(extra) == 1:
        return _deep_form(_ratio(1, 1), mult, constant, sqrt_coeff, rad)
    return _fold_form(_ratio(1, 1), extra[1:], mult, constant, sqrt_coeff, rad)


def _square_fold(form: RealForm) -> RealForm:
    if (
        form.constant.num != 0
        or form.terms
        or form.towers
        or form.nests
        or form.pairs
        or form.deeps
        or form.highs
        or form.peaks
        or form.crests
        or form.summits
        or form.apexes
        or form.shells
        or len(form.folds) != 1
    ):
        raise KernelError("fold square left the radical")
    outer, extra, mult, constant, sqrt_coeff, rad = form.folds[0]
    core = _fold_core(extra, mult, constant, sqrt_coeff, rad)
    return _scale(core, _qmul(_qmul(outer, outer), _ratio(extra[0], 1)))


def _check_fold_base(mult: int, constant: int, sqrt_coeff: int, rad: int) -> None:
    base = _deep_form(_ratio(1, 1), mult, constant, sqrt_coeff, rad)
    if not _canonical(base):
        raise KernelError("fold deep was not canonical")
    if _classify(base) != "gt":
        raise NotExact("square root of a negative stays open")


def _check_fold_extra(extra: tuple[int, ...]) -> None:
    if not extra:
        raise KernelError("fold depth was empty")
    for mult in extra:
        if mult < 1 or _square_part(mult) != (1, mult):
            raise KernelError("fold multiplier was not square-free")


def _fold_from_deep(coeff: Ratio, mult: int, constant: int, sqrt_coeff: int, rad: int) -> RealForm:
    """Nonnegative square root of one positive deep.

    Every further finite nesting is this same radical with one more square root.
    The square check scales the deep and does not call `_fold_from_deep` again.
    """

    if coeff.num < 0:
        raise NotExact("square root of a negative stays open")
    if coeff.num == 0:
        return RealForm(_ratio(0, 1), ())
    if coeff.den < 1:
        raise KernelError("fold coefficient was not a rational")
    if constant == 0 or sqrt_coeff == 0:
        raise KernelError("fold binomial was not reduced")
    _check_fold_base(mult, constant, sqrt_coeff, rad)
    root, free = _square_part(coeff.num * coeff.den)
    outer = _ratio(root, coeff.den)
    result = _fold_form(outer, (free,), mult, constant, sqrt_coeff, rad)
    expected = _deep_form(coeff, mult, constant, sqrt_coeff, rad)
    if _square_fold(result) != expected:
        raise KernelError("fold square disagreed")
    if _classify(result) not in {"gt", "eq"}:
        raise KernelError("fold root was not nonnegative")
    return result


def _fold_from_fold(
    coeff: Ratio,
    extra: tuple[int, ...],
    mult: int,
    constant: int,
    sqrt_coeff: int,
    rad: int,
) -> RealForm:
    """One more square root of a fold. The depth tuple grows by one."""

    if coeff.num < 0:
        raise NotExact("square root of a negative stays open")
    if coeff.num == 0:
        return RealForm(_ratio(0, 1), ())
    if coeff.den < 1:
        raise KernelError("fold coefficient was not a rational")
    _check_fold_extra(extra)
    _check_fold_base(mult, constant, sqrt_coeff, rad)
    root, free = _square_part(coeff.num * coeff.den)
    outer = _ratio(root, coeff.den)
    result = _fold_form(outer, (free,) + extra, mult, constant, sqrt_coeff, rad)
    expected = _fold_form(coeff, extra, mult, constant, sqrt_coeff, rad)
    if _square_fold(result) != expected:
        raise KernelError("fold square disagreed")
    if _classify(result) not in {"gt", "eq"}:
        raise KernelError("fold root was not nonnegative")
    return result


def _fold_times_term(
    extra: tuple[int, ...],
    mult: int,
    constant: int,
    sqrt_coeff: int,
    rad: int,
    other_rad: int,
) -> RealForm:
    core = _fold_core(extra, mult, constant, sqrt_coeff, rad)
    return _sqrt_of_form(_scale(core, _ratio(extra[0] * other_rad, 1)))


def _fold_times_nest(
    extra: tuple[int, ...],
    mult: int,
    constant: int,
    sqrt_coeff: int,
    rad: int,
    nest_const: Ratio,
    nest_sqrt: Ratio,
    nest_rad: int,
) -> RealForm:
    if nest_rad != rad:
        raise NotExact("this nested radical stays outside")
    core = _fold_core(extra, mult, constant, sqrt_coeff, rad)
    nest = _nest_form(_ratio(1, 1), nest_const, nest_sqrt, nest_rad)
    # F * N = sqrt(F^2 * N^2) = sqrt((core * N) * N). Associate through
    # the already closed deep-times-nest product, not through core * N^2,
    # which splits into a sum whose square root stays outside.
    mixed = _mul_forms(_mul_forms(core, nest), nest)
    return _sqrt_of_form(_scale(mixed, _ratio(extra[0], 1)))


def _fold_times_deep(
    extra: tuple[int, ...],
    mult: int,
    constant: int,
    sqrt_coeff: int,
    rad: int,
    deep_mult: int,
    deep_const: int,
    deep_sqrt: int,
    deep_rad: int,
) -> RealForm:
    if deep_rad != rad:
        raise NotExact("this nested radical stays outside")
    core = _fold_core(extra, mult, constant, sqrt_coeff, rad)
    other = _deep_form(_ratio(1, 1), deep_mult, deep_const, deep_sqrt, deep_rad)
    squared = _square_deep(other)
    return _sqrt_of_form(_scale(_mul_forms(core, squared), _ratio(extra[0], 1)))


def _fold_times_fold(
    extra: tuple[int, ...],
    mult: int,
    constant: int,
    sqrt_coeff: int,
    rad: int,
    other_extra: tuple[int, ...],
    other_mult: int,
    other_constant: int,
    other_sqrt: int,
    other_rad: int,
) -> RealForm:
    left = _fold_core(extra, mult, constant, sqrt_coeff, rad)
    right = _fold_core(other_extra, other_mult, other_constant, other_sqrt, other_rad)
    product = _mul_forms(left, right)
    return _sqrt_of_form(_scale(product, _ratio(extra[0] * other_extra[0], 1)))


def _mul_one_fold(
    coeff: Ratio,
    extra: tuple[int, ...],
    mult: int,
    constant: int,
    sqrt_coeff: int,
    rad: int,
    other: RealForm,
) -> RealForm:
    piece = _fold_form(coeff, extra, mult, constant, sqrt_coeff, rad)
    product = _scale(piece, other.constant) if other.constant.num != 0 else RealForm(_ratio(0, 1), ())
    for other_coeff, other_rad in other.terms:
        scaled = _fold_times_term(extra, mult, constant, sqrt_coeff, rad, other_rad)
        product = _add_forms(product, _scale(scaled, _qmul(coeff, other_coeff)))
    for nest_coeff, nest_const, nest_sqrt, nest_rad in other.nests:
        scaled = _fold_times_nest(
            extra, mult, constant, sqrt_coeff, rad, nest_const, nest_sqrt, nest_rad
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, nest_coeff)))
    if (
        other.towers
        or other.pairs
        or other.highs
        or other.peaks
        or other.crests
        or other.summits
        or other.apexes
        or other.shells
    ):
        raise NotExact("this nested radical stays outside")
    for deep_coeff, deep_mult, deep_const, deep_sqrt, deep_rad in other.deeps:
        scaled = _fold_times_deep(
            extra,
            mult,
            constant,
            sqrt_coeff,
            rad,
            deep_mult,
            deep_const,
            deep_sqrt,
            deep_rad,
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, deep_coeff)))
    for (
        fold_coeff,
        other_extra,
        other_mult,
        other_constant,
        other_sqrt,
        other_rad,
    ) in other.folds:
        scaled = _fold_times_fold(
            extra,
            mult,
            constant,
            sqrt_coeff,
            rad,
            other_extra,
            other_mult,
            other_constant,
            other_sqrt,
            other_rad,
        )
        product = _add_forms(product, _scale(scaled, _qmul(coeff, fold_coeff)))
    return product


def _invert_fold(form: RealForm) -> RealForm:
    if (
        form.constant.num != 0
        or form.terms
        or form.towers
        or form.nests
        or form.pairs
        or form.deeps
        or form.highs
        or form.peaks
        or form.crests
        or form.summits
        or form.apexes
        or form.shells
        or len(form.folds) != 1
    ):
        raise NotExact("this quotient stays outside")
    try:
        return _mul_forms(form, _inverse_form(_square_fold(form)))
    except NotExact as exc:
        raise NotExact("this quotient stays outside") from exc


def _as_biquadratic(
    form: RealForm,
) -> tuple[Ratio, Ratio, int, Ratio, int, Ratio] | None:
    if (
        form.towers
        or form.nests
        or form.pairs
        or form.deeps
        or form.highs
        or form.peaks
        or form.crests
        or form.summits
        or form.apexes
        or form.shells
        or form.folds
        or form.quads
    ):
        return None
    primes: set[int] = set()
    for _coeff, rad in form.terms:
        if rad <= 1 or _square_part(rad) != (1, rad):
            return None
        for prime, exponent in _prime_exponents(rad):
            if exponent != 1:
                return None
            primes.add(prime)
    if len(primes) != 2:
        return None
    first, second = sorted(primes)
    constant = form.constant
    first_coeff = _ratio(0, 1)
    second_coeff = _ratio(0, 1)
    product_coeff = _ratio(0, 1)
    for coeff, rad in form.terms:
        if rad == first:
            first_coeff = _qadd(first_coeff, coeff)
        elif rad == second:
            second_coeff = _qadd(second_coeff, coeff)
        elif rad == first * second:
            product_coeff = _qadd(product_coeff, coeff)
        else:
            return None
    if first_coeff.num == 0 and second_coeff.num == 0 and product_coeff.num == 0:
        return None
    return constant, first_coeff, first, second_coeff, second, product_coeff


def _quad_inside(constant: Ratio, first_coeff: Ratio, first: int, second_coeff: Ratio, second: int, product_coeff: Ratio) -> RealForm:
    return RealForm(
        constant,
        tuple(
            (coeff, rad)
            for coeff, rad in (
                (first_coeff, first),
                (second_coeff, second),
                (product_coeff, first * second),
            )
            if coeff.num != 0
        ),
    )


def _biquadratic_norm(
    constant: Ratio,
    first_coeff: Ratio,
    first: int,
    second_coeff: Ratio,
    second: int,
    product_coeff: Ratio,
) -> Ratio:
    first_r = _ratio(first, 1)
    second_r = _ratio(second, 1)
    left = _qsub(
        _qadd(_qmul(constant, constant), _qmul(first_r, _qmul(first_coeff, first_coeff))),
        _qadd(
            _qmul(second_r, _qmul(second_coeff, second_coeff)),
            _qmul(_qmul(second_r, first_r), _qmul(product_coeff, product_coeff)),
        ),
    )
    right = _qsub(
        _qmul(_ratio(2, 1), _qmul(constant, first_coeff)),
        _qmul(_ratio(2, 1), _qmul(second_r, _qmul(second_coeff, product_coeff))),
    )
    return _qsub(_qmul(left, left), _qmul(first_r, _qmul(right, right)))


def _in_quadratic(form: RealForm, rad: int) -> bool:
    if (
        form.towers
        or form.nests
        or form.pairs
        or form.deeps
        or form.highs
        or form.peaks
        or form.crests
        or form.summits
        or form.apexes
        or form.shells
        or form.folds
        or form.quads
    ):
        return False
    return all(term_rad == rad for _coeff, term_rad in form.terms)


def _sqrt_in_quadratic(form: RealForm, rad: int) -> RealForm | None:
    if not _in_quadratic(form, rad):
        return None
    if _is_zero(form):
        return RealForm(_ratio(0, 1), ())
    direction = _classify(form)
    if direction == "lt":
        return None
    if direction != "gt":
        return None
    if _is_rational(form):
        root = _rational_square_root(form.constant)
        if root is not None:
            return RealForm(root, ())
        try:
            extracted = _sqrt_form(form.constant)
        except NotExact:
            return None
        if _in_quadratic(extracted, rad):
            return extracted
        return None
    denested = _denest(form)
    if denested is None or not _in_quadratic(denested, rad):
        return None
    if _classify(denested) not in {"gt", "eq"}:
        return None
    return denested


def _try_denest_over(
    x: RealForm,
    y: RealForm,
    base: int,
    other: int,
    inside: RealForm,
) -> RealForm | None:
    delta = _sub_forms(_mul_forms(x, x), _scale(_mul_forms(y, y), _ratio(other, 1)))
    root = _sqrt_in_quadratic(delta, base)
    if root is None:
        return None
    half = _ratio(1, 2)
    for signed in (root, _neg_form(root)):
        half_sum = _scale(_add_forms(x, signed), half)
        first = _sqrt_in_quadratic(half_sum, base)
        if first is None or _is_zero(first):
            continue
        try:
            second = _div_form(y, _scale(first, _ratio(2, 1)))
        except NotExact:
            continue
        if not _in_quadratic(second, base):
            continue
        result = _add_forms(first, _mul_forms(second, _term_form(_ratio(1, 1), other)))
        if _mul_forms(result, result) != inside:
            continue
        if _classify(result) not in {"gt", "eq"}:
            result = _neg_form(result)
            if _mul_forms(result, result) != inside or _classify(result) not in {"gt", "eq"}:
                continue
        return result
    return None


def _try_denest_biquadratic(
    constant: Ratio,
    first_coeff: Ratio,
    first: int,
    second_coeff: Ratio,
    second: int,
    product_coeff: Ratio,
) -> RealForm | None:
    inside = _quad_inside(constant, first_coeff, first, second_coeff, second, product_coeff)
    left = _quad_inside(constant, first_coeff, first, _ratio(0, 1), second, _ratio(0, 1))
    right = _quad_inside(second_coeff, product_coeff, first, _ratio(0, 1), second, _ratio(0, 1))
    over_second = _try_denest_over(left, right, first, second, inside)
    if over_second is not None:
        return over_second
    swapped_left = _quad_inside(constant, second_coeff, second, _ratio(0, 1), first, _ratio(0, 1))
    swapped_right = _quad_inside(first_coeff, product_coeff, second, _ratio(0, 1), first, _ratio(0, 1))
    return _try_denest_over(swapped_left, swapped_right, second, first, inside)



def _biquadratic_groupings(
    constant: Ratio,
    first_coeff: Ratio,
    first: int,
    second_coeff: Ratio,
    second: int,
    product_coeff: Ratio,
) -> tuple[
    tuple[RealForm, RealForm, int, int],
    tuple[RealForm, RealForm, int, int],
]:
    left = _quad_inside(constant, first_coeff, first, _ratio(0, 1), second, _ratio(0, 1))
    right = _quad_inside(second_coeff, product_coeff, first, _ratio(0, 1), second, _ratio(0, 1))
    swapped_left = _quad_inside(constant, second_coeff, second, _ratio(0, 1), first, _ratio(0, 1))
    swapped_right = _quad_inside(first_coeff, product_coeff, second, _ratio(0, 1), first, _ratio(0, 1))
    return (
        (left, right, first, second),
        (swapped_left, swapped_right, second, first),
    )


def _biquadratic_denest_decided(
    constant: Ratio,
    first_coeff: Ratio,
    first: int,
    second_coeff: Ratio,
    second: int,
    product_coeff: Ratio,
) -> bool:
    for left, right, base, other in _biquadratic_groupings(
        constant, first_coeff, first, second_coeff, second, product_coeff
    ):
        delta = _sub_forms(_mul_forms(left, left), _scale(_mul_forms(right, right), _ratio(other, 1)))
        if not _in_quadratic(delta, base):
            return False
        if _classify(delta) == "open":
            return False
    return True


def _biquadratic_not_a_field_square(
    constant: Ratio,
    first_coeff: Ratio,
    first: int,
    second_coeff: Ratio,
    second: int,
    product_coeff: Ratio,
) -> bool:
    if _try_denest_biquadratic(constant, first_coeff, first, second_coeff, second, product_coeff) is not None:
        return False
    if _rational_square_root(
        _biquadratic_norm(constant, first_coeff, first, second_coeff, second, product_coeff)
    ) is None:
        return True
    return _biquadratic_denest_decided(constant, first_coeff, first, second_coeff, second, product_coeff)



def _lcm(left: int, right: int) -> int:
    if left == 0 or right == 0:
        return 0
    return abs(left * right) // _gcd(left, right)


def _reduce_quad_radicand(
    constant: Ratio,
    first_coeff: Ratio,
    first: int,
    second_coeff: Ratio,
    second: int,
    product_coeff: Ratio,
) -> tuple[Ratio, Ratio, Ratio, int, Ratio, int, Ratio]:
    common = 1
    for value in (constant, first_coeff, second_coeff, product_coeff):
        common = _lcm(common, value.den)
    whole = (
        constant.num * (common // constant.den),
        first_coeff.num * (common // first_coeff.den),
        second_coeff.num * (common // second_coeff.den),
        product_coeff.num * (common // product_coeff.den),
    )
    content = 0
    for value in whole:
        content = _gcd(content, abs(value))
    if content == 0:
        return _ratio(0, 1), _ratio(0, 1), _ratio(0, 1), first, _ratio(0, 1), second, _ratio(0, 1)
    root, free = _square_part(content)
    reduced = (
        _ratio(whole[0] // content, 1),
        _ratio(whole[1] // content, 1),
        _ratio(whole[2] // content, 1),
        _ratio(whole[3] // content, 1),
    )
    numerator = root * root * free
    shared = _gcd(numerator, common)
    numerator //= shared
    denominator = common // shared
    num_root, num_free = _square_part(numerator)
    den_root, den_free = _square_part(denominator)
    coeff = _ratio(num_root, den_root * den_free)
    scale = num_free * den_free
    return (
        coeff,
        _ratio(reduced[0].num * scale, 1),
        _ratio(reduced[1].num * scale, 1),
        first,
        _ratio(reduced[2].num * scale, 1),
        second,
        _ratio(reduced[3].num * scale, 1),
    )


def _quad_form(
    coeff: Ratio,
    constant: Ratio,
    first_coeff: Ratio,
    first: int,
    second_coeff: Ratio,
    second: int,
    product_coeff: Ratio,
) -> RealForm:
    if coeff.num == 0:
        return RealForm(_ratio(0, 1), ())
    if first >= second or first <= 1 or second <= 1:
        raise KernelError("biquadratic primes were not ordered")
    if _square_part(first) != (1, first) or _square_part(second) != (1, second):
        raise KernelError("biquadratic radicand was not square-free")
    if first_coeff.num == 0 and second_coeff.num == 0 and product_coeff.num == 0:
        raise KernelError("biquadratic had no irrational terms")
    return RealForm(
        _ratio(0, 1),
        (),
        quads=((coeff, constant, first_coeff, first, second_coeff, second, product_coeff),),
    )


def _quad_sqrt(form: RealForm) -> RealForm:
    span = _as_biquadratic(form)
    if span is None:
        raise NotExact("this nested radical stays outside")
    constant, first_coeff, first, second_coeff, second, product_coeff = span
    outer, reduced_const, reduced_first, first, reduced_second, second, reduced_product = (
        _reduce_quad_radicand(constant, first_coeff, first, second_coeff, second, product_coeff)
    )
    if outer.num == 0:
        return RealForm(_ratio(0, 1), ())
    reduced = _quad_inside(
        reduced_const, reduced_first, first, reduced_second, second, reduced_product
    )
    if _is_rational(reduced) or (not reduced.terms):
        return _scale(_sqrt_form(reduced.constant) if _is_rational(reduced) else reduced, outer)
    if _as_biquadratic(reduced) is None:
        return _scale(_sqrt_of_form(reduced), outer)
    denested = _try_denest_biquadratic(
        reduced_const, reduced_first, first, reduced_second, second, reduced_product
    )
    if denested is not None:
        return _scale(denested, outer)
    if not _biquadratic_not_a_field_square(
        reduced_const, reduced_first, first, reduced_second, second, reduced_product
    ):
        raise NotExact("this nested radical stays outside")
    result = _quad_form(
        outer, reduced_const, reduced_first, first, reduced_second, second, reduced_product
    )
    squared = _square_quad(result)
    if squared != form:
        raise KernelError("biquadratic square disagreed")
    if _classify(result) not in {"gt", "eq"}:
        raise KernelError("biquadratic root was not nonnegative")
    return result


def _square_quad(form: RealForm) -> RealForm:
    if (
        form.constant.num != 0
        or form.terms
        or form.towers
        or form.nests
        or form.pairs
        or form.deeps
        or form.highs
        or form.peaks
        or form.crests
        or form.summits
        or form.apexes
        or form.shells
        or form.folds
        or len(form.quads) != 1
    ):
        raise KernelError("biquadratic square left the radical")
    coeff, constant, first_coeff, first, second_coeff, second, product_coeff = form.quads[0]
    return _scale(
        _quad_inside(constant, first_coeff, first, second_coeff, second, product_coeff),
        _qmul(coeff, coeff),
    )


def _quad_times_term(
    constant: Ratio,
    first_coeff: Ratio,
    first: int,
    second_coeff: Ratio,
    second: int,
    product_coeff: Ratio,
    other_rad: int,
) -> RealForm:
    return _sqrt_of_form(
        _scale(
            _quad_inside(constant, first_coeff, first, second_coeff, second, product_coeff),
            _ratio(other_rad, 1),
        )
    )


def _quad_times_quad(
    constant: Ratio,
    first_coeff: Ratio,
    first: int,
    second_coeff: Ratio,
    second: int,
    product_coeff: Ratio,
    other_const: Ratio,
    other_first: Ratio,
    other_p: int,
    other_second: Ratio,
    other_q: int,
    other_product: Ratio,
) -> RealForm:
    left = _quad_inside(constant, first_coeff, first, second_coeff, second, product_coeff)
    right = _quad_inside(other_const, other_first, other_p, other_second, other_q, other_product)
    if left == right:
        return left
    return _sqrt_of_form(_mul_forms(left, right))


def _mul_one_quad(
    coeff: Ratio,
    constant: Ratio,
    first_coeff: Ratio,
    first: int,
    second_coeff: Ratio,
    second: int,
    product_coeff: Ratio,
    other: RealForm,
) -> RealForm:
    product = RealForm(_ratio(0, 1), ())
    piece = _quad_form(_ratio(1, 1), constant, first_coeff, first, second_coeff, second, product_coeff)
    if other.constant.num != 0:
        product = _add_forms(product, _scale(piece, _qmul(coeff, other.constant)))
    for other_coeff, other_rad in other.terms:
        product = _add_forms(
            product,
            _scale(
                _quad_times_term(
                    constant, first_coeff, first, second_coeff, second, product_coeff, other_rad
                ),
                _qmul(coeff, other_coeff),
            ),
        )
    for (
        other_coeff,
        other_const,
        other_first,
        other_p,
        other_second,
        other_q,
        other_product,
    ) in other.quads:
        product = _add_forms(
            product,
            _scale(
                _quad_times_quad(
                    constant,
                    first_coeff,
                    first,
                    second_coeff,
                    second,
                    product_coeff,
                    other_const,
                    other_first,
                    other_p,
                    other_second,
                    other_q,
                    other_product,
                ),
                _qmul(coeff, other_coeff),
            ),
        )
    if (
        other.towers
        or other.nests
        or other.pairs
        or other.deeps
        or other.highs
        or other.peaks
        or other.crests
        or other.summits
        or other.apexes
        or other.shells
        or other.folds
    ):
        raise NotExact("this nested radical stays outside")
    return product


def _invert_quad(form: RealForm) -> RealForm:
    if (
        form.constant.num != 0
        or form.terms
        or form.towers
        or form.nests
        or form.pairs
        or form.deeps
        or form.highs
        or form.peaks
        or form.crests
        or form.summits
        or form.apexes
        or form.shells
        or form.folds
        or len(form.quads) != 1
    ):
        raise NotExact("this quotient stays outside")
    try:
        return _mul_forms(form, _inverse_form(_square_quad(form)))
    except NotExact as exc:
        raise NotExact("this quotient stays outside") from exc


def _quad_piece(
    coeff: Ratio,
    constant: Ratio,
    first_coeff: Ratio,
    first: int,
    second_coeff: Ratio,
    second: int,
    product_coeff: Ratio,
) -> tuple[str, bool]:
    return _scaled_piece(
        f"sqrt({show_form(_quad_inside(constant, first_coeff, first, second_coeff, second, product_coeff))})",
        coeff,
    )


def _quad_cmp(
    value: Ratio,
    constant: Ratio,
    first_coeff: Ratio,
    first: int,
    second_coeff: Ratio,
    second: int,
    product_coeff: Ratio,
) -> int:
    inside = _quad_inside(constant, first_coeff, first, second_coeff, second, product_coeff)
    direction = _classify(_sub_forms(RealForm(_qmul(value, value), ()), inside))
    if direction == "eq":
        return 0
    if direction == "lt":
        return -1
    if direction == "gt":
        return 1
    raise KernelError("biquadratic comparison stayed open")


def _quad_start(
    constant: Ratio,
    first_coeff: Ratio,
    first: int,
    second_coeff: Ratio,
    second: int,
    product_coeff: Ratio,
) -> tuple[Ratio, Ratio]:
    inside = _quad_inside(constant, first_coeff, first, second_coeff, second, product_coeff)
    lower_inside = _ratio(0, 1)
    upper_inside = _ratio(0, 1)
    found = False
    for depth in _DEPTHS:
        lower_inside, upper_inside = _enclose(inside, depth)
        if lower_inside.num > 0:
            found = True
            break
    if not found:
        raise KernelError("biquadratic lower bound was not positive")
    lower = _qdiv(lower_inside, _qadd(lower_inside, _ratio(1, 1)))
    ceiling = (abs(upper_inside.num) + upper_inside.den - 1) // upper_inside.den
    if ceiling < 1:
        ceiling = 1
    upper = _ratio(_isqrt_ceil(ceiling), 1)
    if lower.num <= 0 or _qcmp(lower, upper) >= 0:
        raise KernelError("biquadratic bounds left the positive interval")
    return lower, upper


def _quad_bisect(
    lower: Ratio,
    upper: Ratio,
    constant: Ratio,
    first_coeff: Ratio,
    first: int,
    second_coeff: Ratio,
    second: int,
    product_coeff: Ratio,
) -> tuple[Ratio, Ratio]:
    midpoint = _qdiv(_qadd(lower, upper), _ratio(2, 1))
    compared = _quad_cmp(midpoint, constant, first_coeff, first, second_coeff, second, product_coeff)
    if compared == 0:
        raise KernelError("biquadratic bisection hit a rational root")
    if compared < 0:
        return midpoint, upper
    return lower, midpoint


def _quad_bracket(
    lower: Ratio,
    upper: Ratio,
    constant: Ratio,
    first_coeff: Ratio,
    first: int,
    second_coeff: Ratio,
    second: int,
    product_coeff: Ratio,
) -> None:
    if lower.num <= 0 or _qcmp(lower, upper) >= 0:
        raise KernelError("biquadratic bounds left the positive interval")
    if (
        _quad_cmp(lower, constant, first_coeff, first, second_coeff, second, product_coeff) > 0
        or _quad_cmp(upper, constant, first_coeff, first, second_coeff, second, product_coeff) < 0
    ):
        raise KernelError("biquadratic bounds stopped bracketing the radicand")


def _quad_gap_within(
    lower: Ratio,
    constant: Ratio,
    first_coeff: Ratio,
    first: int,
    second_coeff: Ratio,
    second: int,
    product_coeff: Ratio,
    width: Ratio,
    upper: Ratio,
) -> bool:
    if _quad_cmp(lower, constant, first_coeff, first, second_coeff, second, product_coeff) >= 0:
        return False
    limit = _qmul(width, _qmul(_ratio(2, 1), upper))
    ceiling = _qadd(_qmul(lower, lower), limit)
    direction = _classify(
        _sub_forms(
            RealForm(ceiling, ()),
            _quad_inside(constant, first_coeff, first, second_coeff, second, product_coeff),
        )
    )
    return direction in {"gt", "eq"}


def _quad_bounds(
    constant: Ratio,
    first_coeff: Ratio,
    first: int,
    second_coeff: Ratio,
    second: int,
    product_coeff: Ratio,
    depth: int,
) -> tuple[Ratio, Ratio, Ratio]:
    lower, upper = _quad_start(constant, first_coeff, first, second_coeff, second, product_coeff)
    initial_width = _qsub(upper, lower)
    _quad_bracket(lower, upper, constant, first_coeff, first, second_coeff, second, product_coeff)
    for _ in range(depth):
        lower, upper = _quad_bisect(
            lower, upper, constant, first_coeff, first, second_coeff, second, product_coeff
        )
        _quad_bracket(lower, upper, constant, first_coeff, first, second_coeff, second, product_coeff)
    width = _qsub(upper, lower)
    expected = _qdiv(initial_width, _ratio(2**depth, 1))
    if width != expected:
        raise KernelError("bisection width disagreed with the modulus")
    return lower, upper, initial_width


def _quad_bounds_from(
    lower: Ratio,
    upper: Ratio,
    constant: Ratio,
    first_coeff: Ratio,
    first: int,
    second_coeff: Ratio,
    second: int,
    product_coeff: Ratio,
    depth: int,
) -> tuple[Ratio, Ratio, Ratio]:
    initial_width = _qsub(upper, lower)
    for _ in range(depth):
        lower, upper = _quad_bisect(
            lower, upper, constant, first_coeff, first, second_coeff, second, product_coeff
        )
        _quad_bracket(lower, upper, constant, first_coeff, first, second_coeff, second, product_coeff)
    width = _qsub(upper, lower)
    expected = _qdiv(initial_width, _ratio(2**depth, 1))
    if width != expected:
        raise KernelError("bisection width disagreed with the modulus")
    return lower, upper, width


def _quad_certificate_lines(
    constant: Ratio,
    first_coeff: Ratio,
    first: int,
    second_coeff: Ratio,
    second: int,
    product_coeff: Ratio,
) -> tuple[str, ...]:
    lower, upper = _quad_start(constant, first_coeff, first, second_coeff, second, product_coeff)
    _quad_bracket(lower, upper, constant, first_coeff, first, second_coeff, second, product_coeff)
    width = _qsub(upper, lower)
    for _ in range(64):
        end_lower, _end_upper, width = _quad_bounds_from(
            lower,
            upper,
            constant,
            first_coeff,
            first,
            second_coeff,
            second,
            product_coeff,
            _CERT_DEPTH,
        )
        if _quad_gap_within(
            end_lower,
            constant,
            first_coeff,
            first,
            second_coeff,
            second,
            product_coeff,
            width,
            upper,
        ):
            break
        lower, upper = _quad_bisect(
            lower, upper, constant, first_coeff, first, second_coeff, second, product_coeff
        )
        _quad_bracket(lower, upper, constant, first_coeff, first, second_coeff, second, product_coeff)
    else:
        raise KernelError("biquadratic gap bound failed")
    shown = show_form(_quad_inside(constant, first_coeff, first, second_coeff, second, product_coeff))
    return (
        f"sqrt({shown}) is the positive bisection sequence. The depth 0 interval is [{show_ratio(lower)}, {show_ratio(upper)}].",
        "Each step takes the midpoint and keeps the half whose square still brackets the radicand.",
        "The comparison is exact: a rational square sits below the biquadratic when their difference has an order decided by enclosure.",
        "The lower endpoint stays positive, so the class is the nonnegative root.",
        "Isabelle real_sqrt_ge_zero.",
        "Isabelle real_le_lsqrt: 0 <= y and x <= y^2 imply sqrt x <= y.",
        "Isabelle real_sqrt_pow2: 0 <= x implies (sqrt x)^2 = x.",
        "Isabelle real_sqrt_unique: a nonnegative y whose square is the radicand is the root.",
        "Isabelle cauchy: for every positive rational r there is a k such that m, n >= k implies the absolute difference is below r.",
        f"At depth {_CERT_DEPTH} the width is {show_ratio(width)}, the initial width {show_ratio(_qsub(upper, lower))} divided by {2 ** _CERT_DEPTH}.",
        "Both later terms lie in that interval, so the sequence is Cauchy.",
        f"The square gap at depth {_CERT_DEPTH} is bounded by the width times twice the upper endpoint.",
        "The gap shrinks to zero, so the squared sequence differs from the radicand by a vanishing sequence.",
        "Isabelle eq_Real: Cauchy sequences are the same real when their difference vanishes.",
    )


def _invert_two_nests(form: RealForm) -> RealForm:
    """Inverse of c1*N1 + c2*N2 when the squares differ by a nonzero rational.

    (c2*N2 - c1*N1) * (c1*N1 + c2*N2) = c2^2*N2^2 - c1^2*N1^2.
    The quotient is that difference divided by the rational gap.
    """

    if (
        form.constant.num != 0
        or form.terms
        or form.towers
        or form.pairs
        or form.deeps
        or form.highs
        or form.peaks
        or form.crests
        or form.summits
        or form.apexes
        or form.shells
        or form.folds or form.quads or form.algebras
        or len(form.nests) != 2
    ):
        raise NotExact("this quotient stays outside")
    (first_coeff, first_const, first_sqrt, first_rad), (
        second_coeff,
        second_const,
        second_sqrt,
        second_rad,
    ) = form.nests
    if (
        first_rad != second_rad
        or first_const.den != 1
        or first_sqrt.den != 1
        or second_const.den != 1
        or second_sqrt.den != 1
    ):
        raise NotExact("this quotient stays outside")
    first_square = _scale(
        _square_nest(_nest_form(_ratio(1, 1), first_const, first_sqrt, first_rad)),
        _qmul(first_coeff, first_coeff),
    )
    second_square = _scale(
        _square_nest(_nest_form(_ratio(1, 1), second_const, second_sqrt, second_rad)),
        _qmul(second_coeff, second_coeff),
    )
    gap = _sub_forms(second_square, first_square)
    if not _is_rational(gap) or gap.constant.num == 0:
        raise NotExact("this quotient stays outside")
    conjugate = _add_forms(
        _nest_form(_qneg(first_coeff), first_const, first_sqrt, first_rad),
        _nest_form(second_coeff, second_const, second_sqrt, second_rad),
    )
    return _scale(conjugate, _inverse(gap.constant))
def _rational_square_root(value: Ratio) -> Ratio | None:
    if value.num < 0:
        return None
    if value.num == 0:
        return _ratio(0, 1)
    num_root, num_free = _square_part(value.num)
    den_root, den_free = _square_part(value.den)
    if num_free != 1 or den_free != 1:
        return None
    return _ratio(num_root, den_root)


def _power_form(coeff: Ratio, number: int, numer: int, log_den: int) -> RealForm:
    if coeff.num == 0:
        return RealForm(_ratio(0, 1), ())
    if numer < 0 or log_den < 0 or number < 0:
        raise KernelError("a power was not a nonnegative dyadic")
    if numer == 0 or number == 1:
        return RealForm(coeff, ())
    if number == 0:
        return RealForm(_ratio(0, 1), ())
    if log_den == 0:
        return RealForm(_qmul(coeff, _ratio(number**numer, 1)), ())
    exponent = 1 << log_den
    whole, remain = divmod(numer, exponent)
    if whole:
        coeff = _qmul(coeff, _ratio(number**whole, 1))
    if remain == 0:
        return RealForm(coeff, ())
    exponents: dict[int, int] = {}
    rational_extra = 1
    for prime, multiplicity in _prime_exponents(number):
        carry, leftover = divmod(multiplicity * remain, exponent)
        if carry:
            rational_extra *= prime**carry
        if leftover:
            exponents[prime] = leftover
    if rational_extra != 1:
        coeff = _qmul(coeff, _ratio(rational_extra, 1))
    return _radical_from_exponents(coeff, exponents, log_den)


def _mul_powers(coeff: Ratio, left: tuple[int, int, int], right: tuple[int, int, int]) -> RealForm:
    if coeff.num == 0:
        return RealForm(_ratio(0, 1), ())
    base_left, numer_left, log_left = left
    base_right, numer_right, log_right = right
    numer_left, log_left = _reduce_dyadic(numer_left, log_left)
    numer_right, log_right = _reduce_dyadic(numer_right, log_right)
    level = max(log_left, log_right)
    if level == 0:
        return RealForm(_qmul(coeff, _ratio((base_left**numer_left) * (base_right**numer_right), 1)), ())
    modulus = 1 << level
    exponents: dict[int, int] = {}
    rational_extra = 1
    for base, numer, log_den in ((base_left, numer_left, log_left), (base_right, numer_right, log_right)):
        if numer == 0 or base == 1:
            continue
        if base < 1 or log_den < 0:
            raise KernelError("a power was not a nonnegative dyadic")
        if log_den == 0:
            rational_extra *= base**numer
            continue
        scaled = numer << (level - log_den)
        for prime, multiplicity in _prime_exponents(base):
            total = exponents.get(prime, 0) + multiplicity * scaled
            carry, leftover = divmod(total, modulus)
            if carry:
                rational_extra *= prime**carry
            if leftover:
                exponents[prime] = leftover
            else:
                exponents.pop(prime, None)
    if rational_extra != 1:
        coeff = _qmul(coeff, _ratio(rational_extra, 1))
    return _radical_from_exponents(coeff, exponents, level)


def _reduce_dyadic(numer: int, log_den: int) -> tuple[int, int]:
    if numer < 0 or log_den < 0:
        raise KernelError("a dyadic exponent was negative")
    while log_den > 0 and numer % 2 == 0:
        numer //= 2
        log_den -= 1
    return numer, log_den


def _make_tower(coeff: Ratio, base: int, numer: int, log_den: int) -> RealForm:
    if coeff.num == 0:
        return RealForm(_ratio(0, 1), ())
    if log_den < 2 or numer <= 0 or numer % 2 == 0 or numer >= (1 << log_den):
        raise KernelError("tower shape was not reduced")
    if base <= 1 or _square_part(base) != (1, base):
        raise KernelError("tower base was not square-free")
    return RealForm(_ratio(0, 1), (), ((coeff, base, numer, log_den),))


def _prime_exponents(number: int) -> tuple[tuple[int, int], ...]:
    if number < 1:
        raise KernelError("factorization needs a positive integer")
    factors: list[tuple[int, int]] = []
    rest = number
    prime = 2
    while prime * prime <= rest:
        exponent = 0
        while rest % prime == 0:
            rest //= prime
            exponent += 1
        if exponent:
            factors.append((prime, exponent))
        prime = 3 if prime == 2 else prime + 2
    if rest > 1:
        factors.append((rest, 1))
    return tuple(factors)


def _packed_base(base: int, log_den: int) -> bool:
    # Equal exponents stay on the square-free tower. 2^(3/4) remains (2, 3, 2),
    # because the one-base reader matches that generator base.
    if base <= 1 or log_den < 2:
        return False
    limit = 1 << log_den
    exponents: list[int] = []
    for _prime, exponent in _prime_exponents(base):
        if exponent <= 0 or exponent >= limit:
            return False
        exponents.append(exponent)
    if len(exponents) < 2:
        return False
    if all(exponent % 2 == 0 for exponent in exponents):
        return False
    return len(set(exponents)) > 1


def _make_packed(coeff: Ratio, base: int, log_den: int) -> RealForm:
    if coeff.num == 0:
        return RealForm(_ratio(0, 1), ())
    if not _packed_base(base, log_den):
        raise KernelError("packed tower shape was not reduced")
    return RealForm(_ratio(0, 1), (), ((coeff, base, 1, log_den),))


def _radical_from_exponents(coeff: Ratio, exponents: dict[int, int], level: int) -> RealForm:
    if coeff.num == 0:
        return RealForm(_ratio(0, 1), ())
    if level < 0:
        raise KernelError("a dyadic exponent was negative")
    remainders = {prime: exponent for prime, exponent in exponents.items() if exponent}
    while level > 0 and remainders and all(exponent % 2 == 0 for exponent in remainders.values()):
        remainders = {prime: exponent // 2 for prime, exponent in remainders.items()}
        level -= 1
    if level == 0 or not remainders:
        extra = 1
        for prime, exponent in remainders.items():
            extra *= prime**exponent
        if extra != 1:
            coeff = _qmul(coeff, _ratio(extra, 1))
        return RealForm(coeff, ())
    limit = 1 << level
    for exponent in remainders.values():
        if exponent <= 0 or exponent >= limit:
            raise KernelError("a dyadic exponent was not reduced")
    if level == 1:
        free = 1
        for prime, exponent in sorted(remainders.items()):
            if exponent != 1:
                raise KernelError("a square root numerator was not 1")
            free *= prime
        return _scale(_sqrt_form(_ratio(free, 1)), coeff)
    if len(set(remainders.values())) == 1:
        numer = next(iter(remainders.values()))
        base = 1
        for prime in sorted(remainders):
            base *= prime
        return _make_tower(coeff, base, numer, level)
    base = 1
    for prime, exponent in sorted(remainders.items()):
        base *= prime**exponent
    return _make_packed(coeff, base, level)


def _certificate_lines(rad: int) -> tuple[str, ...]:
    lower, upper, initial_width = _bounds(rad, _CERT_DEPTH)
    radicand = _ratio(rad, 1)
    gap = _qsub(radicand, _qmul(lower, lower))
    width = _qsub(upper, lower)
    limit = _qmul(width, _qmul(_ratio(2, 1), _ratio(rad, 1)))
    if gap.num <= 0 or _qcmp(gap, limit) > 0:
        raise KernelError("square gap bound failed")
    return (
        f"sqrt({rad}) is the positive bisection sequence. The depth 0 interval is [1, {rad}].",
        "Each step takes the midpoint and keeps the half whose square still brackets the radicand.",
        "The lower endpoint stays positive, so the class is the nonnegative root.",
        "Isabelle cauchy: for every positive rational r there is a k such that m, n >= k implies the absolute difference is below r.",
        f"At depth {_CERT_DEPTH} the width is {show_ratio(width)}, the initial width {show_ratio(initial_width)} divided by {2 ** _CERT_DEPTH}.",
        "Both later terms lie in that interval, so the sequence is Cauchy.",
        f"The square gap at depth {_CERT_DEPTH} is {show_ratio(gap)}, at most the width times twice the initial upper bound.",
        "The gap shrinks to zero, so the squared sequence differs from the radicand by a vanishing sequence.",
        "Isabelle eq_Real: Cauchy sequences are the same real when their difference vanishes.",
    )


def _bounds(rad: int, depth: int) -> tuple[Ratio, Ratio, Ratio]:
    radicand = _ratio(rad, 1)
    lower = _ratio(1, 1)
    upper = _ratio(rad, 1)
    initial_width = _qsub(upper, lower)
    _bracket(lower, upper, radicand)
    for _ in range(depth):
        lower, upper = _bisect(lower, upper, radicand)
        _bracket(lower, upper, radicand)
    width = _qsub(upper, lower)
    expected = _qdiv(initial_width, _ratio(2**depth, 1))
    if width != expected:
        raise KernelError("bisection width disagreed with the modulus")
    return lower, upper, initial_width


def _bisect(lower: Ratio, upper: Ratio, radicand: Ratio) -> tuple[Ratio, Ratio]:
    midpoint = _qdiv(_qadd(lower, upper), _ratio(2, 1))
    if _qcmp(_qmul(midpoint, midpoint), radicand) <= 0:
        return midpoint, upper
    return lower, midpoint


def _bracket(lower: Ratio, upper: Ratio, radicand: Ratio) -> None:
    if lower.num <= 0 or _qcmp(lower, upper) > 0:
        raise KernelError("sqrt bounds left the positive interval")
    if _qcmp(_qmul(lower, lower), radicand) > 0 or _qcmp(radicand, _qmul(upper, upper)) > 0:
        raise KernelError("sqrt bounds stopped bracketing the radicand")


def _tower_certificate_lines(base: int, numer: int, log_den: int) -> tuple[str, ...]:
    lower, upper, initial_width = _tower_bounds(base, numer, log_den, _CERT_DEPTH)
    width = _qsub(upper, lower)
    if not _power_gap_within(lower, base, numer, log_den, width):
        raise KernelError("tower gap bound failed")
    exponent = 1 << log_den
    return (
        f"The positive root of x^{exponent} = {base}^{numer} is the bisection sequence on [1, {base}].",
        "Each step takes the midpoint and keeps the half whose power still brackets the integer.",
        "The comparison is integer: (a/b)^{2^k} <= base^numer exactly when a^{2^k} <= base^numer * b^{2^k}.",
        "The lower endpoint stays positive, so the class is the nonnegative root.",
        "Isabelle real_sqrt_ge_zero.",
        "Isabelle real_le_lsqrt: 0 <= y and x <= y^2 imply sqrt x <= y. The nested root iterates that comparison.",
        "Isabelle real_sqrt_pow2: 0 <= x implies (sqrt x)^2 = x. Iterating recovers the radicand.",
        "Isabelle real_sqrt_unique: a nonnegative y whose power is the radicand is the root.",
        "Isabelle cauchy: for every positive rational r there is a k such that m, n >= k implies the absolute difference is below r.",
        f"At depth {_CERT_DEPTH} the width is {show_ratio(width)}, the initial width {show_ratio(initial_width)} divided by {2 ** _CERT_DEPTH}.",
        "Both later terms lie in that interval, so the sequence is Cauchy.",
        "The power gap at that depth is bounded by the width times the derivative scale, and it shrinks to zero.",
        "Isabelle eq_Real: Cauchy sequences are the same real when their difference vanishes.",
    )


def _tower_bounds(base: int, numer: int, log_den: int, depth: int) -> tuple[Ratio, Ratio, Ratio]:
    lower = _ratio(1, 1)
    upper = _ratio(base, 1)
    initial_width = _qsub(upper, lower)
    _tower_bracket(lower, upper, base, numer, log_den)
    for _ in range(depth):
        lower, upper = _tower_bisect(lower, upper, base, numer, log_den)
        _tower_bracket(lower, upper, base, numer, log_den)
    width = _qsub(upper, lower)
    expected = _qdiv(initial_width, _ratio(2**depth, 1))
    if width != expected:
        raise KernelError("bisection width disagreed with the modulus")
    return lower, upper, initial_width


def _tower_bisect(
    lower: Ratio,
    upper: Ratio,
    base: int,
    numer: int,
    log_den: int,
) -> tuple[Ratio, Ratio]:
    midpoint = _qdiv(_qadd(lower, upper), _ratio(2, 1))
    compared = _power_cmp(midpoint, base, numer, log_den)
    if compared == 0:
        raise KernelError("tower bisection hit a rational root")
    if compared < 0:
        return midpoint, upper
    return lower, midpoint


def _tower_bracket(lower: Ratio, upper: Ratio, base: int, numer: int, log_den: int) -> None:
    if lower.num <= 0 or _qcmp(lower, upper) >= 0:
        raise KernelError("tower bounds left the positive interval")
    if _power_cmp(lower, base, numer, log_den) >= 0 or _power_cmp(upper, base, numer, log_den) <= 0:
        raise KernelError("tower bounds stopped bracketing the power")


def _power_cmp(value: Ratio, base: int, numer: int, log_den: int) -> int:
    if value.num < 0:
        return -1
    exponent = 1 << log_den
    left = value.num**exponent
    right = (base**numer) * (value.den**exponent)
    return (left > right) - (left < right)


def _power_gap_within(lower: Ratio, base: int, numer: int, log_den: int, width: Ratio) -> bool:
    exponent = 1 << log_den
    target = base**numer
    left_pow = lower.num**exponent
    right_pow = target * (lower.den**exponent)
    if right_pow <= left_pow:
        return False
    gap_num = right_pow - left_pow
    scale = exponent * (base ** (exponent - 1))
    return gap_num * width.den <= width.num * scale * (lower.den**exponent)


def _compare_rational_binomial(value: Ratio, constant: int, sqrt_coeff: int, rad: int) -> int:
    """Compare a rational with `constant + sqrt_coeff * sqrt(rad)`."""

    diff = _qsub(value, _ratio(constant, 1))
    if sqrt_coeff == 0:
        return _qcmp(diff, _ratio(0, 1))
    if sqrt_coeff > 0:
        if diff.num <= 0:
            return -1
        return _qcmp(_qmul(diff, diff), _ratio(sqrt_coeff * sqrt_coeff * rad, 1))
    if diff.num >= 0:
        return 1
    return -_qcmp(_qmul(diff, diff), _ratio(sqrt_coeff * sqrt_coeff * rad, 1))


def _nest_cmp(value: Ratio, constant: int, sqrt_coeff: int, rad: int) -> int:
    if value.num < 0:
        return -1
    return _compare_rational_binomial(_qmul(value, value), constant, sqrt_coeff, rad)


def _nest_start(constant: int, sqrt_coeff: int, rad: int) -> tuple[Ratio, Ratio]:
    if constant > 0 and sqrt_coeff > 0:
        lower_inside = _ratio(constant, 1)
    elif sqrt_coeff < 0:
        numerator = constant * constant - rad * sqrt_coeff * sqrt_coeff
        denominator = constant + (-sqrt_coeff) * rad
        lower_inside = _ratio(numerator, denominator)
    else:
        numerator = rad * sqrt_coeff * sqrt_coeff - constant * constant
        denominator = sqrt_coeff * rad + (-constant)
        lower_inside = _ratio(numerator, denominator)
    if lower_inside.num <= 0:
        raise KernelError("binomial lower bound was not positive")
    lower = _qdiv(lower_inside, _qadd(lower_inside, _ratio(1, 1)))
    ceiling = abs(constant) + abs(sqrt_coeff) * rad
    upper = _ratio(_isqrt_ceil(ceiling), 1)
    if _qcmp(lower, upper) >= 0:
        raise KernelError("nest bounds left the positive interval")
    return lower, upper


def _isqrt_ceil(number: int) -> int:
    if number < 1:
        return 1
    low = 1
    high = number
    while low < high:
        mid = (low + high) // 2
        if mid * mid >= number:
            high = mid
        else:
            low = mid + 1
    return low


def _nest_bisect(
    lower: Ratio,
    upper: Ratio,
    constant: int,
    sqrt_coeff: int,
    rad: int,
) -> tuple[Ratio, Ratio]:
    midpoint = _qdiv(_qadd(lower, upper), _ratio(2, 1))
    compared = _nest_cmp(midpoint, constant, sqrt_coeff, rad)
    if compared == 0:
        raise KernelError("nest bisection hit a rational root")
    if compared < 0:
        return midpoint, upper
    return lower, midpoint


def _nest_bracket(lower: Ratio, upper: Ratio, constant: int, sqrt_coeff: int, rad: int) -> None:
    if lower.num <= 0 or _qcmp(lower, upper) >= 0:
        raise KernelError("nest bounds left the positive interval")
    if _nest_cmp(lower, constant, sqrt_coeff, rad) > 0 or _nest_cmp(upper, constant, sqrt_coeff, rad) < 0:
        raise KernelError("nest bounds stopped bracketing the radicand")


def _nest_gap_within(
    lower: Ratio,
    constant: int,
    sqrt_coeff: int,
    rad: int,
    width: Ratio,
    upper: Ratio,
) -> bool:
    if _nest_cmp(lower, constant, sqrt_coeff, rad) >= 0:
        return False
    limit = _qmul(width, _qmul(_ratio(2, 1), upper))
    ceiling = _qadd(_qmul(lower, lower), limit)
    return _compare_rational_binomial(ceiling, constant, sqrt_coeff, rad) >= 0


def _nest_bounds(constant: int, sqrt_coeff: int, rad: int, depth: int) -> tuple[Ratio, Ratio, Ratio]:
    lower, upper = _nest_start(constant, sqrt_coeff, rad)
    initial_width = _qsub(upper, lower)
    _nest_bracket(lower, upper, constant, sqrt_coeff, rad)
    for _ in range(depth):
        lower, upper = _nest_bisect(lower, upper, constant, sqrt_coeff, rad)
        _nest_bracket(lower, upper, constant, sqrt_coeff, rad)
    width = _qsub(upper, lower)
    expected = _qdiv(initial_width, _ratio(2**depth, 1))
    if width != expected:
        raise KernelError("bisection width disagreed with the modulus")
    return lower, upper, initial_width


def _nest_certificate_lines(constant: int, sqrt_coeff: int, rad: int) -> tuple[str, ...]:
    lower, upper = _nest_start(constant, sqrt_coeff, rad)
    _nest_bracket(lower, upper, constant, sqrt_coeff, rad)
    end_lower = lower
    width = _qsub(upper, lower)
    for _ in range(64):
        end_lower, _end_upper, width = _nest_bounds_from(lower, upper, constant, sqrt_coeff, rad, _CERT_DEPTH)
        if _nest_gap_within(end_lower, constant, sqrt_coeff, rad, width, upper):
            break
        lower, upper = _nest_bisect(lower, upper, constant, sqrt_coeff, rad)
        _nest_bracket(lower, upper, constant, sqrt_coeff, rad)
    else:
        raise KernelError("nest gap bound failed")
    shown = show_form(RealForm(_ratio(constant, 1), ((_ratio(sqrt_coeff, 1), rad),)))
    return (
        f"sqrt({shown}) is the positive bisection sequence. The depth 0 interval is [{show_ratio(lower)}, {show_ratio(upper)}].",
        "Each step takes the midpoint and keeps the half whose square still brackets the radicand.",
        "The comparison is exact: a rational square sits below the binomial when their difference has an order decided by squaring.",
        "The lower endpoint stays positive, so the class is the nonnegative root.",
        "Isabelle real_sqrt_ge_zero.",
        "Isabelle real_le_lsqrt: 0 <= y and x <= y^2 imply sqrt x <= y.",
        "Isabelle real_sqrt_pow2: 0 <= x implies (sqrt x)^2 = x.",
        "Isabelle real_sqrt_unique: a nonnegative y whose square is the radicand is the root.",
        "Isabelle cauchy: for every positive rational r there is a k such that m, n >= k implies the absolute difference is below r.",
        f"At depth {_CERT_DEPTH} the width is {show_ratio(width)}, the initial width {show_ratio(_qsub(upper, lower))} divided by {2 ** _CERT_DEPTH}.",
        "Both later terms lie in that interval, so the sequence is Cauchy.",
        f"The square gap at depth {_CERT_DEPTH} is bounded by the width times twice the upper endpoint.",
        "The gap shrinks to zero, so the squared sequence differs from the radicand by a vanishing sequence.",
        "Isabelle eq_Real: Cauchy sequences are the same real when their difference vanishes.",
    )


def _sign_int(value: int) -> int:
    return (value > 0) - (value < 0)


def _compare_positive_pair(target: int, left_c: int, left_r: int, right_c: int, right_r: int) -> int:
    """target ? left_c*sqrt(left_r) + right_c*sqrt(right_r), both coefficients nonnegative."""

    if left_c == 0 and right_c == 0:
        return _sign_int(target)
    if target <= 0:
        return -1
    left = target * target - left_c * left_c * left_r - right_c * right_c * right_r
    cross = 2 * left_c * right_c
    if cross == 0:
        return _sign_int(left)
    if left <= 0:
        return -1
    gap = left * left - cross * cross * left_r * right_r
    return _sign_int(gap)


def _compare_shifted(target: int, neg_c: int, neg_r: int, pos_c: int, pos_r: int) -> int:
    """Sign of target + neg_c*sqrt(neg_r) - pos_c*sqrt(pos_r), with target nonnegative."""

    if target < 0:
        raise KernelError("pair comparison shifted a negative rational")
    other = pos_c * pos_c * pos_r - target * target - neg_c * neg_c * neg_r
    cross = 2 * target * neg_c
    if cross == 0:
        return _sign_int(target * target + neg_c * neg_c * neg_r - pos_c * pos_c * pos_r)
    if other <= 0:
        return 1
    gap = cross * cross * neg_r - other * other
    return _sign_int(gap)


def _compare_int_pair(target: int, left_c: int, left_r: int, right_c: int, right_r: int) -> int:
    if target < 0:
        return -1
    if left_c < 0 and right_c < 0:
        return 1
    if left_c >= 0 and right_c >= 0:
        return _compare_positive_pair(target, left_c, left_r, right_c, right_r)
    if left_c < 0:
        return _compare_shifted(target, -left_c, left_r, right_c, right_r)
    return _compare_shifted(target, -right_c, right_r, left_c, left_r)


def _compare_rational_pair(target: Ratio, left_c: int, left_r: int, right_c: int, right_r: int) -> int:
    if target.num < 0:
        return -1
    return _compare_int_pair(target.num, left_c * target.den, left_r, right_c * target.den, right_r)


def _pair_inside_positive(left_c: int, left_r: int, right_c: int, right_r: int) -> bool:
    return _compare_int_pair(0, left_c, left_r, right_c, right_r) < 0


def _pair_cmp(value: Ratio, left_c: int, left_r: int, right_c: int, right_r: int) -> int:
    if value.num < 0:
        return -1
    return _compare_rational_pair(_qmul(value, value), left_c, left_r, right_c, right_r)


def _pair_start(left_c: int, left_r: int, right_c: int, right_r: int) -> tuple[Ratio, Ratio]:
    gap = abs(left_c * left_c * left_r - right_c * right_c * right_r)
    if gap == 0:
        raise KernelError("pair bounds met equal squares")
    denom = abs(left_c) * left_r + abs(right_c) * right_r
    lower = _ratio(gap, denom + gap)
    upper = _ratio(_isqrt_ceil(denom), 1)
    if lower.num <= 0 or _qcmp(lower, upper) >= 0:
        raise KernelError("pair bounds left the positive interval")
    return lower, upper


def _pair_bisect(
    lower: Ratio,
    upper: Ratio,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> tuple[Ratio, Ratio]:
    midpoint = _qdiv(_qadd(lower, upper), _ratio(2, 1))
    compared = _pair_cmp(midpoint, left_c, left_r, right_c, right_r)
    if compared == 0:
        raise KernelError("pair bisection hit a rational root")
    if compared < 0:
        return midpoint, upper
    return lower, midpoint


def _pair_bracket(
    lower: Ratio,
    upper: Ratio,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> None:
    if lower.num <= 0 or _qcmp(lower, upper) >= 0:
        raise KernelError("pair bounds left the positive interval")
    if _pair_cmp(lower, left_c, left_r, right_c, right_r) > 0 or _pair_cmp(
        upper, left_c, left_r, right_c, right_r
    ) < 0:
        raise KernelError("pair bounds stopped bracketing the radicand")


def _pair_gap_within(
    lower: Ratio,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    width: Ratio,
    upper: Ratio,
) -> bool:
    if _pair_cmp(lower, left_c, left_r, right_c, right_r) >= 0:
        return False
    limit = _qmul(width, _qmul(_ratio(2, 1), upper))
    ceiling = _qadd(_qmul(lower, lower), limit)
    return _compare_rational_pair(ceiling, left_c, left_r, right_c, right_r) >= 0


def _pair_bounds(
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    depth: int,
) -> tuple[Ratio, Ratio, Ratio]:
    lower, upper = _pair_start(left_c, left_r, right_c, right_r)
    initial_width = _qsub(upper, lower)
    _pair_bracket(lower, upper, left_c, left_r, right_c, right_r)
    for _ in range(depth):
        lower, upper = _pair_bisect(lower, upper, left_c, left_r, right_c, right_r)
        _pair_bracket(lower, upper, left_c, left_r, right_c, right_r)
    width = _qsub(upper, lower)
    expected = _qdiv(initial_width, _ratio(2**depth, 1))
    if width != expected:
        raise KernelError("bisection width disagreed with the modulus")
    return lower, upper, initial_width


def _pair_bounds_from(
    lower: Ratio,
    upper: Ratio,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    depth: int,
) -> tuple[Ratio, Ratio, Ratio]:
    initial_width = _qsub(upper, lower)
    for _ in range(depth):
        lower, upper = _pair_bisect(lower, upper, left_c, left_r, right_c, right_r)
        _pair_bracket(lower, upper, left_c, left_r, right_c, right_r)
    width = _qsub(upper, lower)
    expected = _qdiv(initial_width, _ratio(2**depth, 1))
    if width != expected:
        raise KernelError("bisection width disagreed with the modulus")
    return lower, upper, width


def _pair_certificate_lines(left_c: int, left_r: int, right_c: int, right_r: int) -> tuple[str, ...]:
    lower, upper = _pair_start(left_c, left_r, right_c, right_r)
    _pair_bracket(lower, upper, left_c, left_r, right_c, right_r)
    width = _qsub(upper, lower)
    for _ in range(64):
        end_lower, _end_upper, width = _pair_bounds_from(
            lower, upper, left_c, left_r, right_c, right_r, _CERT_DEPTH
        )
        if _pair_gap_within(end_lower, left_c, left_r, right_c, right_r, width, upper):
            break
        lower, upper = _pair_bisect(lower, upper, left_c, left_r, right_c, right_r)
        _pair_bracket(lower, upper, left_c, left_r, right_c, right_r)
    else:
        raise KernelError("pair gap bound failed")
    shown = show_form(_pair_inside(left_c, left_r, right_c, right_r))
    return (
        f"sqrt({shown}) is the positive bisection sequence. The depth 0 interval is [{show_ratio(lower)}, {show_ratio(upper)}].",
        "Each step takes the midpoint and keeps the half whose square still brackets the radicand.",
        "The comparison is exact: a rational sits below a sum of two square roots when isolating one radical and squaring twice decides the order.",
        "The lower endpoint stays positive, so the class is the nonnegative root.",
        "Isabelle real_sqrt_ge_zero.",
        "Isabelle real_le_lsqrt: 0 <= y and x <= y^2 imply sqrt x <= y.",
        "Isabelle real_sqrt_pow2: 0 <= x implies (sqrt x)^2 = x.",
        "Isabelle real_sqrt_unique: a nonnegative y whose square is the radicand is the root.",
        "Isabelle cauchy: for every positive rational r there is a k such that m, n >= k implies the absolute difference is below r.",
        f"At depth {_CERT_DEPTH} the width is {show_ratio(width)}, the initial width {show_ratio(_qsub(upper, lower))} divided by {2 ** _CERT_DEPTH}.",
        "Both later terms lie in that interval, so the sequence is Cauchy.",
        f"The square gap at depth {_CERT_DEPTH} is bounded by the width times twice the upper endpoint.",
        "The gap shrinks to zero, so the squared sequence differs from the radicand by a vanishing sequence.",
        "Isabelle eq_Real: Cauchy sequences are the same real when their difference vanishes.",
    )


def _deep_cmp(value: Ratio, mult: int, constant: int, sqrt_coeff: int, rad: int) -> int:
    if value.num < 0:
        return -1
    squared = _qmul(value, value)
    fourth = _qmul(squared, squared)
    scaled = mult * mult
    return _compare_rational_binomial(fourth, scaled * constant, scaled * sqrt_coeff, rad)


def _deep_start(mult: int, constant: int, sqrt_coeff: int, rad: int) -> tuple[Ratio, Ratio]:
    if mult < 1:
        raise KernelError("deep multiplier was not positive")
    scaled = mult * mult
    lower, upper = _nest_start(scaled * constant, scaled * sqrt_coeff, rad)
    _deep_bracket(lower, upper, mult, constant, sqrt_coeff, rad)
    return lower, upper


def _deep_bisect(
    lower: Ratio,
    upper: Ratio,
    mult: int,
    constant: int,
    sqrt_coeff: int,
    rad: int,
) -> tuple[Ratio, Ratio]:
    midpoint = _qdiv(_qadd(lower, upper), _ratio(2, 1))
    compared = _deep_cmp(midpoint, mult, constant, sqrt_coeff, rad)
    if compared == 0:
        raise KernelError("deep bisection hit a rational root")
    if compared < 0:
        return midpoint, upper
    return lower, midpoint


def _deep_bracket(
    lower: Ratio,
    upper: Ratio,
    mult: int,
    constant: int,
    sqrt_coeff: int,
    rad: int,
) -> None:
    if lower.num <= 0 or _qcmp(lower, upper) >= 0:
        raise KernelError("deep bounds left the positive interval")
    if _deep_cmp(lower, mult, constant, sqrt_coeff, rad) > 0 or _deep_cmp(
        upper, mult, constant, sqrt_coeff, rad
    ) < 0:
        raise KernelError("deep bounds stopped bracketing the radicand")


def _deep_gap_within(
    lower: Ratio,
    mult: int,
    constant: int,
    sqrt_coeff: int,
    rad: int,
    width: Ratio,
    upper: Ratio,
) -> bool:
    if _deep_cmp(lower, mult, constant, sqrt_coeff, rad) >= 0:
        return False
    limit = _qmul(width, _qmul(_ratio(2, 1), upper))
    lifted = _qadd(_qmul(lower, lower), limit)
    ceiling = _qmul(lifted, lifted)
    scaled = mult * mult
    return _compare_rational_binomial(ceiling, scaled * constant, scaled * sqrt_coeff, rad) >= 0


def _deep_bounds(
    mult: int,
    constant: int,
    sqrt_coeff: int,
    rad: int,
    depth: int,
) -> tuple[Ratio, Ratio, Ratio]:
    lower, upper = _deep_start(mult, constant, sqrt_coeff, rad)
    initial_width = _qsub(upper, lower)
    for _ in range(depth):
        lower, upper = _deep_bisect(lower, upper, mult, constant, sqrt_coeff, rad)
        _deep_bracket(lower, upper, mult, constant, sqrt_coeff, rad)
    width = _qsub(upper, lower)
    expected = _qdiv(initial_width, _ratio(2**depth, 1))
    if width != expected:
        raise KernelError("bisection width disagreed with the modulus")
    return lower, upper, initial_width


def _deep_bounds_from(
    lower: Ratio,
    upper: Ratio,
    mult: int,
    constant: int,
    sqrt_coeff: int,
    rad: int,
    depth: int,
) -> tuple[Ratio, Ratio, Ratio]:
    initial_width = _qsub(upper, lower)
    for _ in range(depth):
        lower, upper = _deep_bisect(lower, upper, mult, constant, sqrt_coeff, rad)
        _deep_bracket(lower, upper, mult, constant, sqrt_coeff, rad)
    width = _qsub(upper, lower)
    expected = _qdiv(initial_width, _ratio(2**depth, 1))
    if width != expected:
        raise KernelError("bisection width disagreed with the modulus")
    return lower, upper, width


def _deep_certificate_lines(mult: int, constant: int, sqrt_coeff: int, rad: int) -> tuple[str, ...]:
    lower, upper = _deep_start(mult, constant, sqrt_coeff, rad)
    width = _qsub(upper, lower)
    for _ in range(64):
        end_lower, _end_upper, width = _deep_bounds_from(
            lower, upper, mult, constant, sqrt_coeff, rad, _CERT_DEPTH
        )
        if _deep_gap_within(end_lower, mult, constant, sqrt_coeff, rad, width, upper):
            break
        lower, upper = _deep_bisect(lower, upper, mult, constant, sqrt_coeff, rad)
        _deep_bracket(lower, upper, mult, constant, sqrt_coeff, rad)
    else:
        raise KernelError("deep gap bound failed")
    inside = show_form(RealForm(_ratio(constant, 1), ((_ratio(sqrt_coeff, 1), rad),)))
    nested = f"sqrt({inside})"
    shown = nested if mult == 1 else f"{mult} * {nested}"
    return (
        f"sqrt({shown}) is the positive bisection sequence. The depth 0 interval is [{show_ratio(lower)}, {show_ratio(upper)}].",
        "Each step takes the midpoint and keeps the half whose fourth power still brackets the binomial.",
        "The comparison is exact: a rational sits below a square root of a binomial when isolating one radical and squaring twice decides the order.",
        "The lower endpoint stays positive, so the class is the nonnegative root.",
        "Isabelle real_sqrt_ge_zero.",
        "Isabelle real_le_lsqrt: 0 <= y and x <= y^2 imply sqrt x <= y. The nested root iterates that comparison.",
        "Isabelle real_sqrt_pow2: 0 <= x implies (sqrt x)^2 = x. Iterating recovers the radicand.",
        "Isabelle real_sqrt_unique: a nonnegative y whose power is the radicand is the root.",
        "Isabelle cauchy: for every positive rational r there is a k such that m, n >= k implies the absolute difference is below r.",
        f"At depth {_CERT_DEPTH} the width is {show_ratio(width)}, the initial width {show_ratio(_qsub(upper, lower))} divided by {2 ** _CERT_DEPTH}.",
        "Both later terms lie in that interval, so the sequence is Cauchy.",
        f"The fourth-power gap at depth {_CERT_DEPTH} is bounded by the width times twice the upper endpoint, after one more squaring.",
        "The gap shrinks to zero, so the squared sequence differs from the radicand by a vanishing sequence.",
        "Isabelle eq_Real: Cauchy sequences are the same real when their difference vanishes.",
    )


def _high_cmp(
    value: Ratio,
    mult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> int:
    if value.num < 0:
        return -1
    squared = _qmul(value, value)
    fourth = _qmul(squared, squared)
    scaled = mult * mult
    return _compare_rational_pair(fourth, scaled * left_c, left_r, scaled * right_c, right_r)


def _high_start(
    mult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> tuple[Ratio, Ratio]:
    if mult < 1:
        raise KernelError("high multiplier was not positive")
    scaled = mult * mult
    lower, upper = _pair_start(scaled * left_c, left_r, scaled * right_c, right_r)
    _high_bracket(lower, upper, mult, left_c, left_r, right_c, right_r)
    return lower, upper


def _high_bisect(
    lower: Ratio,
    upper: Ratio,
    mult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> tuple[Ratio, Ratio]:
    midpoint = _qdiv(_qadd(lower, upper), _ratio(2, 1))
    compared = _high_cmp(midpoint, mult, left_c, left_r, right_c, right_r)
    if compared == 0:
        raise KernelError("high bisection hit a rational root")
    if compared < 0:
        return midpoint, upper
    return lower, midpoint


def _high_bracket(
    lower: Ratio,
    upper: Ratio,
    mult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> None:
    if lower.num <= 0 or _qcmp(lower, upper) >= 0:
        raise KernelError("high bounds left the positive interval")
    if _high_cmp(lower, mult, left_c, left_r, right_c, right_r) > 0 or _high_cmp(
        upper, mult, left_c, left_r, right_c, right_r
    ) < 0:
        raise KernelError("high bounds stopped bracketing the radicand")


def _high_gap_within(
    lower: Ratio,
    mult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    width: Ratio,
    upper: Ratio,
) -> bool:
    if _high_cmp(lower, mult, left_c, left_r, right_c, right_r) >= 0:
        return False
    limit = _qmul(width, _qmul(_ratio(2, 1), upper))
    lifted = _qadd(_qmul(lower, lower), limit)
    ceiling = _qmul(lifted, lifted)
    scaled = mult * mult
    return _compare_rational_pair(ceiling, scaled * left_c, left_r, scaled * right_c, right_r) >= 0


def _high_bounds(
    mult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    depth: int,
) -> tuple[Ratio, Ratio, Ratio]:
    lower, upper = _high_start(mult, left_c, left_r, right_c, right_r)
    initial_width = _qsub(upper, lower)
    for _ in range(depth):
        lower, upper = _high_bisect(lower, upper, mult, left_c, left_r, right_c, right_r)
        _high_bracket(lower, upper, mult, left_c, left_r, right_c, right_r)
    width = _qsub(upper, lower)
    expected = _qdiv(initial_width, _ratio(2**depth, 1))
    if width != expected:
        raise KernelError("bisection width disagreed with the modulus")
    return lower, upper, initial_width


def _high_bounds_from(
    lower: Ratio,
    upper: Ratio,
    mult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    depth: int,
) -> tuple[Ratio, Ratio, Ratio]:
    initial_width = _qsub(upper, lower)
    for _ in range(depth):
        lower, upper = _high_bisect(lower, upper, mult, left_c, left_r, right_c, right_r)
        _high_bracket(lower, upper, mult, left_c, left_r, right_c, right_r)
    width = _qsub(upper, lower)
    expected = _qdiv(initial_width, _ratio(2**depth, 1))
    if width != expected:
        raise KernelError("bisection width disagreed with the modulus")
    return lower, upper, width


def _high_certificate_lines(
    mult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> tuple[str, ...]:
    lower, upper = _high_start(mult, left_c, left_r, right_c, right_r)
    width = _qsub(upper, lower)
    for _ in range(64):
        end_lower, _end_upper, width = _high_bounds_from(
            lower, upper, mult, left_c, left_r, right_c, right_r, _CERT_DEPTH
        )
        if _high_gap_within(end_lower, mult, left_c, left_r, right_c, right_r, width, upper):
            break
        lower, upper = _high_bisect(lower, upper, mult, left_c, left_r, right_c, right_r)
        _high_bracket(lower, upper, mult, left_c, left_r, right_c, right_r)
    else:
        raise KernelError("high gap bound failed")
    inside = show_form(_pair_inside(left_c, left_r, right_c, right_r))
    nested = f"sqrt({inside})"
    shown = nested if mult == 1 else f"{mult} * {nested}"
    return (
        f"sqrt({shown}) is the positive bisection sequence. The depth 0 interval is [{show_ratio(lower)}, {show_ratio(upper)}].",
        "Each step takes the midpoint and keeps the half whose fourth power still brackets the sum of two square roots.",
        "The comparison is exact: a rational sits below a square root of a sum of two square roots when isolating the two radicals and squaring twice decides the order.",
        "The lower endpoint stays positive, so the class is the nonnegative root.",
        "Isabelle real_sqrt_ge_zero.",
        "Isabelle real_le_lsqrt: 0 <= y and x <= y^2 imply sqrt x <= y. The nested root iterates that comparison.",
        "Isabelle real_sqrt_pow2: 0 <= x implies (sqrt x)^2 = x. Iterating recovers the radicand.",
        "Isabelle real_sqrt_unique: a nonnegative y whose power is the radicand is the root.",
        "Isabelle cauchy: for every positive rational r there is a k such that m, n >= k implies the absolute difference is below r.",
        f"At depth {_CERT_DEPTH} the width is {show_ratio(width)}, the initial width {show_ratio(_qsub(upper, lower))} divided by {2 ** _CERT_DEPTH}.",
        "Both later terms lie in that interval, so the sequence is Cauchy.",
        f"The fourth-power gap at depth {_CERT_DEPTH} is bounded by the width times twice the upper endpoint, after one more squaring.",
        "The gap shrinks to zero, so the squared sequence differs from the radicand by a vanishing sequence.",
        "Isabelle eq_Real: Cauchy sequences are the same real when their difference vanishes.",
    )


def _peak_cmp(
    value: Ratio,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> int:
    if value.num < 0:
        return -1
    reduced = _qdiv(_qmul(value, value), _ratio(pmult, 1))
    return _high_cmp(reduced, hmult, left_c, left_r, right_c, right_r)


def _peak_start(
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> tuple[Ratio, Ratio]:
    if pmult < 1:
        raise KernelError("peak multiplier was not positive")
    high_lower, high_upper = _high_start(hmult, left_c, left_r, right_c, right_r)
    upper = high_upper if pmult == 1 else _qmul(_ratio(pmult, 1), high_upper)
    _peak_bracket(high_lower, upper, pmult, hmult, left_c, left_r, right_c, right_r)
    return high_lower, upper


def _peak_bisect(
    lower: Ratio,
    upper: Ratio,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> tuple[Ratio, Ratio]:
    midpoint = _qdiv(_qadd(lower, upper), _ratio(2, 1))
    compared = _peak_cmp(midpoint, pmult, hmult, left_c, left_r, right_c, right_r)
    if compared == 0:
        raise KernelError("peak bisection hit a rational root")
    if compared < 0:
        return midpoint, upper
    return lower, midpoint


def _peak_bracket(
    lower: Ratio,
    upper: Ratio,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> None:
    if lower.num <= 0 or _qcmp(lower, upper) >= 0:
        raise KernelError("peak bounds left the positive interval")
    if _peak_cmp(lower, pmult, hmult, left_c, left_r, right_c, right_r) > 0 or _peak_cmp(
        upper, pmult, hmult, left_c, left_r, right_c, right_r
    ) < 0:
        raise KernelError("peak bounds stopped bracketing the radicand")


def _peak_gap_within(
    lower: Ratio,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    width: Ratio,
    upper: Ratio,
) -> bool:
    if _peak_cmp(lower, pmult, hmult, left_c, left_r, right_c, right_r) >= 0:
        return False
    limit = _qmul(width, _qmul(_ratio(2, 1), upper))
    lifted = _qadd(_qmul(lower, lower), limit)
    fourth = _qmul(lifted, lifted)
    eighth = _qmul(fourth, fourth)
    scale = (pmult * pmult) * (pmult * pmult) * (hmult * hmult)
    return _compare_rational_pair(eighth, scale * left_c, left_r, scale * right_c, right_r) >= 0


def _peak_bounds(
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    depth: int,
) -> tuple[Ratio, Ratio, Ratio]:
    lower, upper = _peak_start(pmult, hmult, left_c, left_r, right_c, right_r)
    initial_width = _qsub(upper, lower)
    for _ in range(depth):
        lower, upper = _peak_bisect(lower, upper, pmult, hmult, left_c, left_r, right_c, right_r)
        _peak_bracket(lower, upper, pmult, hmult, left_c, left_r, right_c, right_r)
    width = _qsub(upper, lower)
    expected = _qdiv(initial_width, _ratio(2**depth, 1))
    if width != expected:
        raise KernelError("bisection width disagreed with the modulus")
    return lower, upper, initial_width


def _peak_bounds_from(
    lower: Ratio,
    upper: Ratio,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    depth: int,
) -> tuple[Ratio, Ratio, Ratio]:
    initial_width = _qsub(upper, lower)
    for _ in range(depth):
        lower, upper = _peak_bisect(lower, upper, pmult, hmult, left_c, left_r, right_c, right_r)
        _peak_bracket(lower, upper, pmult, hmult, left_c, left_r, right_c, right_r)
    width = _qsub(upper, lower)
    expected = _qdiv(initial_width, _ratio(2**depth, 1))
    if width != expected:
        raise KernelError("bisection width disagreed with the modulus")
    return lower, upper, width


def _peak_certificate_lines(
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> tuple[str, ...]:
    lower, upper = _peak_start(pmult, hmult, left_c, left_r, right_c, right_r)
    width = _qsub(upper, lower)
    for _ in range(64):
        end_lower, _end_upper, width = _peak_bounds_from(
            lower, upper, pmult, hmult, left_c, left_r, right_c, right_r, _CERT_DEPTH
        )
        if _peak_gap_within(end_lower, pmult, hmult, left_c, left_r, right_c, right_r, width, upper):
            break
        lower, upper = _peak_bisect(lower, upper, pmult, hmult, left_c, left_r, right_c, right_r)
        _peak_bracket(lower, upper, pmult, hmult, left_c, left_r, right_c, right_r)
    else:
        raise KernelError("peak gap bound failed")
    shown = _peak_body(pmult, hmult, left_c, left_r, right_c, right_r)
    return (
        f"sqrt({shown}) is the positive bisection sequence. The depth 0 interval is [{show_ratio(lower)}, {show_ratio(upper)}].",
        "Each step takes the midpoint and keeps the half whose eighth power still brackets the sum of two square roots.",
        "The comparison is exact: a rational sits below a square root of a high when isolating the two radicals and squaring enough times decides the order.",
        "The lower endpoint stays positive, so the class is the nonnegative root.",
        "Isabelle real_sqrt_ge_zero.",
        "Isabelle real_le_lsqrt: 0 <= y and x <= y^2 imply sqrt x <= y. The nested root iterates that comparison.",
        "Isabelle real_sqrt_pow2: 0 <= x implies (sqrt x)^2 = x. Iterating recovers the radicand.",
        "Isabelle real_sqrt_unique: a nonnegative y whose power is the radicand is the root.",
        "Isabelle cauchy: for every positive rational r there is a k such that m, n >= k implies the absolute difference is below r.",
        f"At depth {_CERT_DEPTH} the width is {show_ratio(width)}, the initial width {show_ratio(_qsub(upper, lower))} divided by {2 ** _CERT_DEPTH}.",
        "Both later terms lie in that interval, so the sequence is Cauchy.",
        f"The eighth-power gap at depth {_CERT_DEPTH} is bounded by the width times twice the upper endpoint, after two more squarings.",
        "The gap shrinks to zero, so the squared sequence differs from the radicand by a vanishing sequence.",
        "Isabelle eq_Real: Cauchy sequences are the same real when their difference vanishes.",
    )


def _crest_cmp(
    value: Ratio,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> int:
    if value.num < 0:
        return -1
    reduced = _qdiv(_qmul(value, value), _ratio(qmult, 1))
    return _peak_cmp(reduced, pmult, hmult, left_c, left_r, right_c, right_r)


def _crest_start(
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> tuple[Ratio, Ratio]:
    if qmult < 1:
        raise KernelError("crest multiplier was not positive")
    peak_lower, peak_upper = _peak_start(pmult, hmult, left_c, left_r, right_c, right_r)
    upper = peak_upper if qmult == 1 else _qmul(_ratio(qmult, 1), peak_upper)
    _crest_bracket(peak_lower, upper, qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    return peak_lower, upper


def _crest_bisect(
    lower: Ratio,
    upper: Ratio,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> tuple[Ratio, Ratio]:
    midpoint = _qdiv(_qadd(lower, upper), _ratio(2, 1))
    compared = _crest_cmp(midpoint, qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    if compared == 0:
        raise KernelError("crest bisection hit a rational root")
    if compared < 0:
        return midpoint, upper
    return lower, midpoint


def _crest_bracket(
    lower: Ratio,
    upper: Ratio,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> None:
    if lower.num <= 0 or _qcmp(lower, upper) >= 0:
        raise KernelError("crest bounds left the positive interval")
    if _crest_cmp(lower, qmult, pmult, hmult, left_c, left_r, right_c, right_r) > 0 or _crest_cmp(
        upper, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    ) < 0:
        raise KernelError("crest bounds stopped bracketing the radicand")


def _crest_gap_within(
    lower: Ratio,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    width: Ratio,
    upper: Ratio,
) -> bool:
    if _crest_cmp(lower, qmult, pmult, hmult, left_c, left_r, right_c, right_r) >= 0:
        return False
    limit = _qmul(width, _qmul(_ratio(2, 1), upper))
    lifted = _qadd(_qmul(lower, lower), limit)
    fourth = _qmul(lifted, lifted)
    eighth = _qmul(fourth, fourth)
    sixteenth = _qmul(eighth, eighth)
    scale = (qmult * qmult) * (qmult * qmult) * (qmult * qmult) * (qmult * qmult)
    scale *= (pmult * pmult) * (pmult * pmult) * (hmult * hmult)
    return _compare_rational_pair(sixteenth, scale * left_c, left_r, scale * right_c, right_r) >= 0


def _crest_bounds(
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    depth: int,
) -> tuple[Ratio, Ratio, Ratio]:
    lower, upper = _crest_start(qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    initial_width = _qsub(upper, lower)
    for _ in range(depth):
        lower, upper = _crest_bisect(
            lower, upper, qmult, pmult, hmult, left_c, left_r, right_c, right_r
        )
        _crest_bracket(lower, upper, qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    width = _qsub(upper, lower)
    expected = _qdiv(initial_width, _ratio(2**depth, 1))
    if width != expected:
        raise KernelError("bisection width disagreed with the modulus")
    return lower, upper, initial_width


def _crest_bounds_from(
    lower: Ratio,
    upper: Ratio,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    depth: int,
) -> tuple[Ratio, Ratio, Ratio]:
    initial_width = _qsub(upper, lower)
    for _ in range(depth):
        lower, upper = _crest_bisect(
            lower, upper, qmult, pmult, hmult, left_c, left_r, right_c, right_r
        )
        _crest_bracket(lower, upper, qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    width = _qsub(upper, lower)
    expected = _qdiv(initial_width, _ratio(2**depth, 1))
    if width != expected:
        raise KernelError("bisection width disagreed with the modulus")
    return lower, upper, width


def _crest_certificate_lines(
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> tuple[str, ...]:
    lower, upper = _crest_start(qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    width = _qsub(upper, lower)
    for _ in range(64):
        end_lower, _end_upper, width = _crest_bounds_from(
            lower, upper, qmult, pmult, hmult, left_c, left_r, right_c, right_r, _CERT_DEPTH
        )
        if _crest_gap_within(
            end_lower, qmult, pmult, hmult, left_c, left_r, right_c, right_r, width, upper
        ):
            break
        lower, upper = _crest_bisect(
            lower, upper, qmult, pmult, hmult, left_c, left_r, right_c, right_r
        )
        _crest_bracket(lower, upper, qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    else:
        raise KernelError("crest gap bound failed")
    shown = _crest_body(qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    return (
        f"sqrt({shown}) is the positive bisection sequence. The depth 0 interval is [{show_ratio(lower)}, {show_ratio(upper)}].",
        "Each step takes the midpoint and keeps the half whose sixteenth power still brackets the sum of two square roots.",
        "The comparison is exact: a rational sits below a square root of a peak when isolating the two radicals and squaring enough times decides the order.",
        "The lower endpoint stays positive, so the class is the nonnegative root.",
        "Isabelle real_sqrt_ge_zero.",
        "Isabelle real_le_lsqrt: 0 <= y and x <= y^2 imply sqrt x <= y. The nested root iterates that comparison.",
        "Isabelle real_sqrt_pow2: 0 <= x implies (sqrt x)^2 = x. Iterating recovers the radicand.",
        "Isabelle real_sqrt_unique: a nonnegative y whose power is the radicand is the root.",
        "Isabelle cauchy: for every positive rational r there is a k such that m, n >= k implies the absolute difference is below r.",
        f"At depth {_CERT_DEPTH} the width is {show_ratio(width)}, the initial width {show_ratio(_qsub(upper, lower))} divided by {2 ** _CERT_DEPTH}.",
        "Both later terms lie in that interval, so the sequence is Cauchy.",
        f"The sixteenth-power gap at depth {_CERT_DEPTH} is bounded by the width times twice the upper endpoint, after three more squarings.",
        "The gap shrinks to zero, so the squared sequence differs from the radicand by a vanishing sequence.",
        "Isabelle eq_Real: Cauchy sequences are the same real when their difference vanishes.",
    )



def _summit_cmp(
    value: Ratio,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> int:
    if value.num < 0:
        return -1
    reduced = _qdiv(_qmul(value, value), _ratio(smult, 1))
    return _crest_cmp(reduced, qmult, pmult, hmult, left_c, left_r, right_c, right_r)


def _summit_start(
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> tuple[Ratio, Ratio]:
    if smult < 1:
        raise KernelError("summit multiplier was not positive")
    crest_lower, crest_upper = _crest_start(qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    upper = crest_upper if smult == 1 else _qmul(_ratio(smult, 1), crest_upper)
    _summit_bracket(
        crest_lower, upper, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    )
    return crest_lower, upper


def _summit_bisect(
    lower: Ratio,
    upper: Ratio,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> tuple[Ratio, Ratio]:
    midpoint = _qdiv(_qadd(lower, upper), _ratio(2, 1))
    compared = _summit_cmp(
        midpoint, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    )
    if compared == 0:
        raise KernelError("summit bisection hit a rational root")
    if compared < 0:
        return midpoint, upper
    return lower, midpoint


def _summit_bracket(
    lower: Ratio,
    upper: Ratio,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> None:
    if lower.num <= 0 or _qcmp(lower, upper) >= 0:
        raise KernelError("summit bounds left the positive interval")
    if _summit_cmp(
        lower, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    ) > 0 or _summit_cmp(
        upper, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    ) < 0:
        raise KernelError("summit bounds stopped bracketing the radicand")


def _summit_gap_within(
    lower: Ratio,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    width: Ratio,
    upper: Ratio,
) -> bool:
    if _summit_cmp(lower, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r) >= 0:
        return False
    limit = _qmul(width, _qmul(_ratio(2, 1), upper))
    lifted = _qadd(_qmul(lower, lower), limit)
    fourth = _qmul(lifted, lifted)
    eighth = _qmul(fourth, fourth)
    sixteenth = _qmul(eighth, eighth)
    thirty_second = _qmul(sixteenth, sixteenth)
    scale = (smult * smult) * (smult * smult) * (smult * smult) * (smult * smult)
    scale *= (smult * smult) * (smult * smult) * (smult * smult) * (smult * smult)
    scale *= (qmult * qmult) * (qmult * qmult) * (qmult * qmult) * (qmult * qmult)
    scale *= (pmult * pmult) * (pmult * pmult) * (hmult * hmult)
    return _compare_rational_pair(thirty_second, scale * left_c, left_r, scale * right_c, right_r) >= 0


def _summit_bounds(
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    depth: int,
) -> tuple[Ratio, Ratio, Ratio]:
    lower, upper = _summit_start(smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    initial_width = _qsub(upper, lower)
    for _ in range(depth):
        lower, upper = _summit_bisect(
            lower, upper, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
        )
        _summit_bracket(
            lower, upper, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
        )
    width = _qsub(upper, lower)
    expected = _qdiv(initial_width, _ratio(2**depth, 1))
    if width != expected:
        raise KernelError("bisection width disagreed with the modulus")
    return lower, upper, initial_width


def _summit_bounds_from(
    lower: Ratio,
    upper: Ratio,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    depth: int,
) -> tuple[Ratio, Ratio, Ratio]:
    initial_width = _qsub(upper, lower)
    for _ in range(depth):
        lower, upper = _summit_bisect(
            lower, upper, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
        )
        _summit_bracket(
            lower, upper, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
        )
    width = _qsub(upper, lower)
    expected = _qdiv(initial_width, _ratio(2**depth, 1))
    if width != expected:
        raise KernelError("bisection width disagreed with the modulus")
    return lower, upper, width


def _summit_certificate_lines(
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> tuple[str, ...]:
    lower, upper = _summit_start(smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    width = _qsub(upper, lower)
    for _ in range(64):
        end_lower, _end_upper, width = _summit_bounds_from(
            lower,
            upper,
            smult,
            qmult,
            pmult,
            hmult,
            left_c,
            left_r,
            right_c,
            right_r,
            _CERT_DEPTH,
        )
        if _summit_gap_within(
            end_lower,
            smult,
            qmult,
            pmult,
            hmult,
            left_c,
            left_r,
            right_c,
            right_r,
            width,
            upper,
        ):
            break
        lower, upper = _summit_bisect(
            lower, upper, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
        )
        _summit_bracket(
            lower, upper, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
        )
    else:
        raise KernelError("summit gap bound failed")
    shown = _summit_body(smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    return (
        f"sqrt({shown}) is the positive bisection sequence. The depth 0 interval is [{show_ratio(lower)}, {show_ratio(upper)}].",
        "Each step takes the midpoint and keeps the half whose thirty-second power still brackets the sum of two square roots.",
        "The comparison is exact: a rational sits below a square root of a crest when isolating the two radicals and squaring enough times decides the order.",
        "The lower endpoint stays positive, so the class is the nonnegative root.",
        "Isabelle real_sqrt_ge_zero.",
        "Isabelle real_le_lsqrt: 0 <= y and x <= y^2 imply sqrt x <= y. The nested root iterates that comparison.",
        "Isabelle real_sqrt_pow2: 0 <= x implies (sqrt x)^2 = x. Iterating recovers the radicand.",
        "Isabelle real_sqrt_unique: a nonnegative y whose power is the radicand is the root.",
        "Isabelle cauchy: for every positive rational r there is a k such that m, n >= k implies the absolute difference is below r.",
        f"At depth {_CERT_DEPTH} the width is {show_ratio(width)}, the initial width {show_ratio(_qsub(upper, lower))} divided by {2 ** _CERT_DEPTH}.",
        "Both later terms lie in that interval, so the sequence is Cauchy.",
        f"The thirty-second-power gap at depth {_CERT_DEPTH} is bounded by the width times twice the upper endpoint, after four more squarings.",
        "The gap shrinks to zero, so the squared sequence differs from the radicand by a vanishing sequence.",
        "Isabelle eq_Real: Cauchy sequences are the same real when their difference vanishes.",
    )



def _apex_cmp(
    value: Ratio,
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> int:
    if value.num < 0:
        return -1
    reduced = _qdiv(_qmul(value, value), _ratio(amult, 1))
    return _summit_cmp(reduced, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r)


def _apex_start(
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> tuple[Ratio, Ratio]:
    if amult < 1:
        raise KernelError("apex multiplier was not positive")
    summit_lower, summit_upper = _summit_start(
        smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    )
    upper = summit_upper if amult == 1 else _qmul(_ratio(amult, 1), summit_upper)
    _apex_bracket(
        summit_lower,
        upper,
        amult,
        smult,
        qmult,
        pmult,
        hmult,
        left_c,
        left_r,
        right_c,
        right_r,
    )
    return summit_lower, upper


def _apex_bisect(
    lower: Ratio,
    upper: Ratio,
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> tuple[Ratio, Ratio]:
    midpoint = _qdiv(_qadd(lower, upper), _ratio(2, 1))
    compared = _apex_cmp(
        midpoint, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    )
    if compared == 0:
        raise KernelError("apex bisection hit a rational root")
    if compared < 0:
        return midpoint, upper
    return lower, midpoint


def _apex_bracket(
    lower: Ratio,
    upper: Ratio,
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> None:
    if lower.num <= 0 or _qcmp(lower, upper) >= 0:
        raise KernelError("apex bounds left the positive interval")
    if _apex_cmp(
        lower, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    ) > 0 or _apex_cmp(
        upper, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    ) < 0:
        raise KernelError("apex bounds stopped bracketing the radicand")


def _apex_gap_within(
    lower: Ratio,
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    width: Ratio,
    upper: Ratio,
) -> bool:
    if _apex_cmp(lower, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r) >= 0:
        return False
    limit = _qmul(width, _qmul(_ratio(2, 1), upper))
    lifted = _qadd(_qmul(lower, lower), limit)
    fourth = _qmul(lifted, lifted)
    eighth = _qmul(fourth, fourth)
    sixteenth = _qmul(eighth, eighth)
    thirty_second = _qmul(sixteenth, sixteenth)
    sixty_fourth = _qmul(thirty_second, thirty_second)
    scale = (amult * amult) * (amult * amult) * (amult * amult) * (amult * amult)
    scale *= (amult * amult) * (amult * amult) * (amult * amult) * (amult * amult)
    scale *= (amult * amult) * (amult * amult) * (amult * amult) * (amult * amult)
    scale *= (amult * amult) * (amult * amult) * (amult * amult) * (amult * amult)
    scale *= (smult * smult) * (smult * smult) * (smult * smult) * (smult * smult)
    scale *= (smult * smult) * (smult * smult) * (smult * smult) * (smult * smult)
    scale *= (qmult * qmult) * (qmult * qmult) * (qmult * qmult) * (qmult * qmult)
    scale *= (pmult * pmult) * (pmult * pmult) * (hmult * hmult)
    return _compare_rational_pair(
        sixty_fourth, scale * left_c, left_r, scale * right_c, right_r
    ) >= 0


def _apex_bounds(
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    depth: int,
) -> tuple[Ratio, Ratio, Ratio]:
    lower, upper = _apex_start(
        amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    )
    initial_width = _qsub(upper, lower)
    for _ in range(depth):
        lower, upper = _apex_bisect(
            lower, upper, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
        )
        _apex_bracket(
            lower, upper, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
        )
    width = _qsub(upper, lower)
    expected = _qdiv(initial_width, _ratio(2**depth, 1))
    if width != expected:
        raise KernelError("bisection width disagreed with the modulus")
    return lower, upper, initial_width


def _apex_bounds_from(
    lower: Ratio,
    upper: Ratio,
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    depth: int,
) -> tuple[Ratio, Ratio, Ratio]:
    initial_width = _qsub(upper, lower)
    for _ in range(depth):
        lower, upper = _apex_bisect(
            lower, upper, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
        )
        _apex_bracket(
            lower, upper, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
        )
    width = _qsub(upper, lower)
    expected = _qdiv(initial_width, _ratio(2**depth, 1))
    if width != expected:
        raise KernelError("bisection width disagreed with the modulus")
    return lower, upper, width


def _apex_certificate_lines(
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> tuple[str, ...]:
    lower, upper = _apex_start(
        amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    )
    width = _qsub(upper, lower)
    for _ in range(64):
        end_lower, _end_upper, width = _apex_bounds_from(
            lower,
            upper,
            amult,
            smult,
            qmult,
            pmult,
            hmult,
            left_c,
            left_r,
            right_c,
            right_r,
            _CERT_DEPTH,
        )
        if _apex_gap_within(
            end_lower,
            amult,
            smult,
            qmult,
            pmult,
            hmult,
            left_c,
            left_r,
            right_c,
            right_r,
            width,
            upper,
        ):
            break
        lower, upper = _apex_bisect(
            lower, upper, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
        )
        _apex_bracket(
            lower, upper, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
        )
    else:
        raise KernelError("apex gap bound failed")
    shown = _apex_body(amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    return (
        f"sqrt({shown}) is the positive bisection sequence. The depth 0 interval is [{show_ratio(lower)}, {show_ratio(upper)}].",
        "Each step takes the midpoint and keeps the half whose sixty-fourth power still brackets the sum of two square roots.",
        "The comparison is exact: a rational sits below a square root of a summit when isolating the two radicals and squaring enough times decides the order.",
        "The lower endpoint stays positive, so the class is the nonnegative root.",
        "Isabelle real_sqrt_ge_zero.",
        "Isabelle real_le_lsqrt: 0 <= y and x <= y^2 imply sqrt x <= y. The nested root iterates that comparison.",
        "Isabelle real_sqrt_pow2: 0 <= x implies (sqrt x)^2 = x. Iterating recovers the radicand.",
        "Isabelle real_sqrt_unique: a nonnegative y whose power is the radicand is the root.",
        "Isabelle cauchy: for every positive rational r there is a k such that m, n >= k implies the absolute difference is below r.",
        f"At depth {_CERT_DEPTH} the width is {show_ratio(width)}, the initial width {show_ratio(_qsub(upper, lower))} divided by {2 ** _CERT_DEPTH}.",
        "Both later terms lie in that interval, so the sequence is Cauchy.",
        f"The sixty-fourth-power gap at depth {_CERT_DEPTH} is bounded by the width times twice the upper endpoint, after five more squarings.",
        "The gap shrinks to zero, so the squared sequence differs from the radicand by a vanishing sequence.",
        "Isabelle eq_Real: Cauchy sequences are the same real when their difference vanishes.",
    )



def _shell_cmp(
    value: Ratio,
    extra: tuple[int, ...],
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> int:
    if value.num < 0:
        return -1
    reduced = _qdiv(_qmul(value, value), _ratio(extra[0], 1))
    if len(extra) == 1:
        return _apex_cmp(reduced, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    return _shell_cmp(
        reduced, extra[1:], amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    )


def _shell_start(
    extra: tuple[int, ...],
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> tuple[Ratio, Ratio]:
    lower, upper = _apex_start(amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    for mult in extra:
        if mult != 1:
            upper = _qmul(_ratio(mult, 1), upper)
    _shell_bracket(
        lower, upper, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    )
    return lower, upper


def _shell_bisect(
    lower: Ratio,
    upper: Ratio,
    extra: tuple[int, ...],
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> tuple[Ratio, Ratio]:
    midpoint = _qdiv(_qadd(lower, upper), _ratio(2, 1))
    compared = _shell_cmp(
        midpoint, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    )
    if compared == 0:
        raise KernelError("shell bisection hit a rational root")
    if compared < 0:
        return midpoint, upper
    return lower, midpoint


def _shell_bracket(
    lower: Ratio,
    upper: Ratio,
    extra: tuple[int, ...],
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> None:
    if lower.num <= 0 or _qcmp(lower, upper) >= 0:
        raise KernelError("shell bounds left the positive interval")
    if _shell_cmp(
        lower, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    ) > 0 or _shell_cmp(
        upper, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    ) < 0:
        raise KernelError("shell bounds stopped bracketing the radicand")


def _shell_gap_within(
    lower: Ratio,
    extra: tuple[int, ...],
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    width: Ratio,
    upper: Ratio,
) -> bool:
    if _shell_cmp(
        lower, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    ) >= 0:
        return False
    limit = _qmul(width, _qmul(_ratio(2, 1), upper))
    ceiling = _qadd(_qmul(lower, lower), limit)
    reduced = _qdiv(ceiling, _ratio(extra[0], 1))
    if len(extra) == 1:
        return _apex_cmp(
            reduced, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
        ) >= 0
    return _shell_cmp(
        reduced, extra[1:], amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    ) >= 0


def _shell_bounds(
    extra: tuple[int, ...],
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    depth: int,
) -> tuple[Ratio, Ratio, Ratio]:
    lower, upper = _shell_start(
        extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    )
    initial_width = _qsub(upper, lower)
    for _ in range(depth):
        lower, upper = _shell_bisect(
            lower, upper, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
        )
        _shell_bracket(
            lower, upper, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
        )
    width = _qsub(upper, lower)
    expected = _qdiv(initial_width, _ratio(2**depth, 1))
    if width != expected:
        raise KernelError("bisection width disagreed with the modulus")
    return lower, upper, initial_width


def _shell_bounds_from(
    lower: Ratio,
    upper: Ratio,
    extra: tuple[int, ...],
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
    depth: int,
) -> tuple[Ratio, Ratio, Ratio]:
    initial_width = _qsub(upper, lower)
    for _ in range(depth):
        lower, upper = _shell_bisect(
            lower, upper, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
        )
        _shell_bracket(
            lower, upper, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
        )
    width = _qsub(upper, lower)
    expected = _qdiv(initial_width, _ratio(2**depth, 1))
    if width != expected:
        raise KernelError("bisection width disagreed with the modulus")
    return lower, upper, width


def _shell_certificate_lines(
    extra: tuple[int, ...],
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> tuple[str, ...]:
    lower, upper = _shell_start(
        extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
    )
    width = _qsub(upper, lower)
    for _ in range(64):
        end_lower, _end_upper, width = _shell_bounds_from(
            lower,
            upper,
            extra,
            amult,
            smult,
            qmult,
            pmult,
            hmult,
            left_c,
            left_r,
            right_c,
            right_r,
            _CERT_DEPTH,
        )
        if _shell_gap_within(
            end_lower,
            extra,
            amult,
            smult,
            qmult,
            pmult,
            hmult,
            left_c,
            left_r,
            right_c,
            right_r,
            width,
            upper,
        ):
            break
        lower, upper = _shell_bisect(
            lower, upper, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
        )
        _shell_bracket(
            lower, upper, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
        )
    else:
        raise KernelError("shell gap bound failed")
    shown = _shell_body(extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r)
    lines = [
        f"{shown} is the positive bisection sequence. The depth 0 interval is [{show_ratio(lower)}, {show_ratio(upper)}].",
        "Each step takes the midpoint and keeps the half whose square still brackets the radicand.",
        "The radicand is one positive apex. Squaring once recovers that apex.",
        "The lower endpoint stays positive, so the class is the nonnegative root.",
        "Isabelle real_sqrt_ge_zero.",
        "Isabelle real_le_lsqrt: 0 <= y and x <= y^2 imply sqrt x <= y. One more square root iterates that comparison.",
        "Isabelle real_sqrt_pow2: 0 <= x implies (sqrt x)^2 = x.",
        "Isabelle real_sqrt_unique: a nonnegative y whose square is the radicand is the root.",
        "Isabelle cauchy: for every positive rational r there is a k such that m, n >= k implies the absolute difference is below r.",
        f"At depth {_CERT_DEPTH} the width is {show_ratio(width)}, the initial width {show_ratio(_qsub(upper, lower))} divided by {2 ** _CERT_DEPTH}.",
        "Both later terms lie in that interval, so the sequence is Cauchy.",
        f"The square gap at depth {_CERT_DEPTH} is bounded by the width times twice the upper endpoint.",
        "The gap shrinks to zero, so the squared sequence differs from the radicand by a vanishing sequence.",
        "Isabelle eq_Real: Cauchy sequences are the same real when their difference vanishes.",
    ]
    if len(extra) == 1:
        lines.extend(
            _apex_certificate_lines(amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r)
        )
    else:
        lines.extend(
            _shell_certificate_lines(
                extra[1:], amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
            )
        )
    return tuple(lines)


def _shell_body(
    extra: tuple[int, ...],
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> str:
    inner = f"sqrt({_apex_body(amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r)})"
    for mult in reversed(extra):
        factor = inner if mult == 1 else f"{mult} * {inner}"
        inner = f"sqrt({factor})"
    return inner


def _shell_piece(
    coeff: Ratio,
    extra: tuple[int, ...],
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> tuple[str, bool]:
    return _scaled_piece(
        _shell_body(extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r),
        coeff,
    )



def _fold_cmp(
    value: Ratio,
    extra: tuple[int, ...],
    mult: int,
    constant: int,
    sqrt_coeff: int,
    rad: int,
) -> int:
    if value.num < 0:
        return -1
    reduced = _qdiv(_qmul(value, value), _ratio(extra[0], 1))
    if len(extra) == 1:
        return _deep_cmp(reduced, mult, constant, sqrt_coeff, rad)
    return _fold_cmp(reduced, extra[1:], mult, constant, sqrt_coeff, rad)


def _fold_start(
    extra: tuple[int, ...],
    mult: int,
    constant: int,
    sqrt_coeff: int,
    rad: int,
) -> tuple[Ratio, Ratio]:
    lower, upper = _deep_start(mult, constant, sqrt_coeff, rad)
    for item in extra:
        if item != 1:
            upper = _qmul(_ratio(item, 1), upper)
    _fold_bracket(lower, upper, extra, mult, constant, sqrt_coeff, rad)
    return lower, upper


def _fold_bisect(
    lower: Ratio,
    upper: Ratio,
    extra: tuple[int, ...],
    mult: int,
    constant: int,
    sqrt_coeff: int,
    rad: int,
) -> tuple[Ratio, Ratio]:
    midpoint = _qdiv(_qadd(lower, upper), _ratio(2, 1))
    compared = _fold_cmp(midpoint, extra, mult, constant, sqrt_coeff, rad)
    if compared == 0:
        raise KernelError("fold bisection hit a rational root")
    if compared < 0:
        return midpoint, upper
    return lower, midpoint


def _fold_bracket(
    lower: Ratio,
    upper: Ratio,
    extra: tuple[int, ...],
    mult: int,
    constant: int,
    sqrt_coeff: int,
    rad: int,
) -> None:
    if lower.num <= 0 or _qcmp(lower, upper) >= 0:
        raise KernelError("fold bounds left the positive interval")
    if _fold_cmp(lower, extra, mult, constant, sqrt_coeff, rad) > 0 or _fold_cmp(
        upper, extra, mult, constant, sqrt_coeff, rad
    ) < 0:
        raise KernelError("fold bounds stopped bracketing the radicand")


def _fold_gap_within(
    lower: Ratio,
    extra: tuple[int, ...],
    mult: int,
    constant: int,
    sqrt_coeff: int,
    rad: int,
    width: Ratio,
    upper: Ratio,
) -> bool:
    if _fold_cmp(lower, extra, mult, constant, sqrt_coeff, rad) >= 0:
        return False
    limit = _qmul(width, _qmul(_ratio(2, 1), upper))
    ceiling = _qadd(_qmul(lower, lower), limit)
    reduced = _qdiv(ceiling, _ratio(extra[0], 1))
    if len(extra) == 1:
        return _deep_cmp(reduced, mult, constant, sqrt_coeff, rad) >= 0
    return _fold_cmp(reduced, extra[1:], mult, constant, sqrt_coeff, rad) >= 0


def _fold_bounds(
    extra: tuple[int, ...],
    mult: int,
    constant: int,
    sqrt_coeff: int,
    rad: int,
    depth: int,
) -> tuple[Ratio, Ratio, Ratio]:
    lower, upper = _fold_start(extra, mult, constant, sqrt_coeff, rad)
    initial_width = _qsub(upper, lower)
    for _ in range(depth):
        lower, upper = _fold_bisect(lower, upper, extra, mult, constant, sqrt_coeff, rad)
        _fold_bracket(lower, upper, extra, mult, constant, sqrt_coeff, rad)
    width = _qsub(upper, lower)
    expected = _qdiv(initial_width, _ratio(2**depth, 1))
    if width != expected:
        raise KernelError("bisection width disagreed with the modulus")
    return lower, upper, initial_width


def _fold_bounds_from(
    lower: Ratio,
    upper: Ratio,
    extra: tuple[int, ...],
    mult: int,
    constant: int,
    sqrt_coeff: int,
    rad: int,
    depth: int,
) -> tuple[Ratio, Ratio, Ratio]:
    initial_width = _qsub(upper, lower)
    for _ in range(depth):
        lower, upper = _fold_bisect(lower, upper, extra, mult, constant, sqrt_coeff, rad)
        _fold_bracket(lower, upper, extra, mult, constant, sqrt_coeff, rad)
    width = _qsub(upper, lower)
    expected = _qdiv(initial_width, _ratio(2**depth, 1))
    if width != expected:
        raise KernelError("bisection width disagreed with the modulus")
    return lower, upper, width


def _fold_certificate_lines(
    extra: tuple[int, ...],
    mult: int,
    constant: int,
    sqrt_coeff: int,
    rad: int,
) -> tuple[str, ...]:
    lower, upper = _fold_start(extra, mult, constant, sqrt_coeff, rad)
    width = _qsub(upper, lower)
    for _ in range(64):
        end_lower, _end_upper, width = _fold_bounds_from(
            lower, upper, extra, mult, constant, sqrt_coeff, rad, _CERT_DEPTH
        )
        if _fold_gap_within(end_lower, extra, mult, constant, sqrt_coeff, rad, width, upper):
            break
        lower, upper = _fold_bisect(lower, upper, extra, mult, constant, sqrt_coeff, rad)
        _fold_bracket(lower, upper, extra, mult, constant, sqrt_coeff, rad)
    else:
        raise KernelError("fold gap bound failed")
    shown = _fold_body(extra, mult, constant, sqrt_coeff, rad)
    lines = [
        f"{shown} is the positive bisection sequence. The depth 0 interval is [{show_ratio(lower)}, {show_ratio(upper)}].",
        "Each step takes the midpoint and keeps the half whose square still brackets the radicand.",
        "The radicand is one positive square root of a nested binomial. Squaring once recovers that radical.",
        "The lower endpoint stays positive, so the class is the nonnegative root.",
        "Isabelle real_sqrt_ge_zero.",
        "Isabelle real_le_lsqrt: 0 <= y and x <= y^2 imply sqrt x <= y. One more square root iterates that comparison.",
        "Isabelle real_sqrt_pow2: 0 <= x implies (sqrt x)^2 = x.",
        "Isabelle real_sqrt_unique: a nonnegative y whose square is the radicand is the root.",
        "Isabelle cauchy: for every positive rational r there is a k such that m, n >= k implies the absolute difference is below r.",
        f"At depth {_CERT_DEPTH} the width is {show_ratio(width)}, the initial width {show_ratio(_qsub(upper, lower))} divided by {2 ** _CERT_DEPTH}.",
        "Both later terms lie in that interval, so the sequence is Cauchy.",
        f"The square gap at depth {_CERT_DEPTH} is bounded by the width times twice the upper endpoint.",
        "The gap shrinks to zero, so the squared sequence differs from the radicand by a vanishing sequence.",
        "Isabelle eq_Real: Cauchy sequences are the same real when their difference vanishes.",
    ]
    if len(extra) == 1:
        lines.extend(_deep_certificate_lines(mult, constant, sqrt_coeff, rad))
    else:
        lines.extend(_fold_certificate_lines(extra[1:], mult, constant, sqrt_coeff, rad))
    return tuple(lines)


def _fold_body(
    extra: tuple[int, ...],
    mult: int,
    constant: int,
    sqrt_coeff: int,
    rad: int,
) -> str:
    inner = show_form(_deep_form(_ratio(1, 1), mult, constant, sqrt_coeff, rad))
    for item in reversed(extra):
        factor = inner if item == 1 else f"{item} * {inner}"
        inner = f"sqrt({factor})"
    return inner


def _fold_piece(
    coeff: Ratio,
    extra: tuple[int, ...],
    mult: int,
    constant: int,
    sqrt_coeff: int,
    rad: int,
) -> tuple[str, bool]:
    return _scaled_piece(_fold_body(extra, mult, constant, sqrt_coeff, rad), coeff)


def _nest_bounds_from(
    lower: Ratio,
    upper: Ratio,
    constant: int,
    sqrt_coeff: int,
    rad: int,
    depth: int,
) -> tuple[Ratio, Ratio, Ratio]:
    initial_width = _qsub(upper, lower)
    for _ in range(depth):
        lower, upper = _nest_bisect(lower, upper, constant, sqrt_coeff, rad)
        _nest_bracket(lower, upper, constant, sqrt_coeff, rad)
    width = _qsub(upper, lower)
    expected = _qdiv(initial_width, _ratio(2**depth, 1))
    if width != expected:
        raise KernelError("bisection width disagreed with the modulus")
    return lower, upper, width


def _enclose(form: RealForm, depth: int) -> tuple[Ratio, Ratio]:
    lower = form.constant
    upper = form.constant
    for coeff, rad in form.terms:
        left, right, _width = _bounds(rad, depth)
        lower, upper = _absorb(lower, upper, coeff, left, right)
    for coeff, base, numer, log_den in form.towers:
        left, right, _width = _tower_bounds(base, numer, log_den, depth)
        lower, upper = _absorb(lower, upper, coeff, left, right)
    for coeff, constant, sqrt_coeff, rad in form.nests:
        if constant.den != 1 or sqrt_coeff.den != 1:
            raise KernelError("a binomial nest was not an integer")
        left, right, _width = _nest_bounds(constant.num, sqrt_coeff.num, rad, depth)
        lower, upper = _absorb(lower, upper, coeff, left, right)
    for coeff, left_c, left_r, right_c, right_r in form.pairs:
        left, right, _width = _pair_bounds(left_c, left_r, right_c, right_r, depth)
        lower, upper = _absorb(lower, upper, coeff, left, right)
    for coeff, mult, constant, sqrt_coeff, rad in form.deeps:
        left, right, _width = _deep_bounds(mult, constant, sqrt_coeff, rad, depth)
        lower, upper = _absorb(lower, upper, coeff, left, right)
    for coeff, mult, left_c, left_r, right_c, right_r in form.highs:
        left, right, _width = _high_bounds(mult, left_c, left_r, right_c, right_r, depth)
        lower, upper = _absorb(lower, upper, coeff, left, right)
    for coeff, pmult, hmult, left_c, left_r, right_c, right_r in form.peaks:
        left, right, _width = _peak_bounds(pmult, hmult, left_c, left_r, right_c, right_r, depth)
        lower, upper = _absorb(lower, upper, coeff, left, right)
    for coeff, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.crests:
        left, right, _width = _crest_bounds(qmult, pmult, hmult, left_c, left_r, right_c, right_r, depth)
        lower, upper = _absorb(lower, upper, coeff, left, right)
    for coeff, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.summits:
        left, right, _width = _summit_bounds(
            smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r, depth
        )
        lower, upper = _absorb(lower, upper, coeff, left, right)
    for coeff, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.apexes:
        left, right, _width = _apex_bounds(
            amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r, depth
        )
        lower, upper = _absorb(lower, upper, coeff, left, right)
    for coeff, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.shells:
        left, right, _width = _shell_bounds(
            extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r, depth
        )
        lower, upper = _absorb(lower, upper, coeff, left, right)
    for coeff, extra, mult, constant, sqrt_coeff, rad in form.folds:
        left, right, _width = _fold_bounds(extra, mult, constant, sqrt_coeff, rad, depth)
        lower, upper = _absorb(lower, upper, coeff, left, right)
    for coeff, constant, first_coeff, first, second_coeff, second, product_coeff in form.quads:
        left, right, _width = _quad_bounds(
            constant, first_coeff, first, second_coeff, second, product_coeff, depth
        )
        lower, upper = _absorb(lower, upper, coeff, left, right)
    for coeff, coeffs, index in form.algebras:
        left, right = _algebra_bounds(coeffs, index)
        lower, upper = _absorb(lower, upper, coeff, left, right)
    if _qcmp(lower, upper) > 0:
        raise KernelError("enclosure crossed itself")
    return lower, upper


def _absorb(
    lower: Ratio,
    upper: Ratio,
    coeff: Ratio,
    left: Ratio,
    right: Ratio,
) -> tuple[Ratio, Ratio]:
    images = (_qmul(coeff, left), _qmul(coeff, right))
    term_lower = images[0] if _qcmp(images[0], images[1]) <= 0 else images[1]
    term_upper = images[1] if term_lower == images[0] else images[0]
    return _qadd(lower, term_lower), _qadd(upper, term_upper)


def _classify(form: RealForm) -> str:
    if _is_rational(form):
        if form.constant.num < 0:
            return "lt"
        if form.constant.num > 0:
            return "gt"
        return "eq"
    for depth in _DEPTHS:
        lower, upper = _enclose(form, depth)
        if upper.num <= 0:
            return "lt"
        if lower.num >= 0:
            return "gt"
    return "open"


def compare_reals(left: RealForm, right: RealForm) -> str:
    """Compare two normal forms. `lt` means the first is strictly smaller."""

    if left == right:
        return "eq"
    if left.algebras or right.algebras:
        return _compare_algebras(left, right)
    direction = _classify(_sub_forms(left, right))
    if direction == "eq":
        raise KernelError("two normal forms were equal and distinct")
    return direction


def _separation_lines(form: RealForm, direction: str) -> tuple[str, ...]:
    if direction == "eq":
        return ("The difference is the constant sequence 0.",)
    if _is_rational(form):
        shown = show_form(form)
        if direction == "lt":
            return (f"The difference is the negative rational {shown}.",)
        if direction == "gt":
            return (f"The difference is the positive rational {shown}.",)
        return ("The rational difference did not decide the comparison.",)
    packed = any(
        base > 1 and _square_part(base) != (1, base) for _coeff, base, _numer, _log_den in form.towers
    )
    if form.quads:
        inside = "A square root of a two-prime biquadratic is not attained at a rational endpoint, so the value stays strictly inside the interval."
    elif form.folds:
        inside = "A further square root of a nested binomial is not attained at a rational endpoint, so the value stays strictly inside the interval."
    elif form.shells:
        inside = "A further square root of an apex is not attained at a rational endpoint, so the value stays strictly inside the interval."
    elif form.apexes:
        inside = "A square root of a summit is not attained at a rational endpoint, so the value stays strictly inside the interval."
    elif form.summits:
        inside = "A square root of a crest is not attained at a rational endpoint, so the value stays strictly inside the interval."
    elif form.crests:
        inside = "A square root of a peak is not attained at a rational endpoint, so the value stays strictly inside the interval."
    elif form.peaks:
        inside = "A square root of a high is not attained at a rational endpoint, so the value stays strictly inside the interval."
    elif form.highs:
        inside = "A square root of a two-radical pair is not attained at a rational endpoint, so the value stays strictly inside the interval."
    elif form.deeps:
        inside = "A square root of a nested binomial is not attained at a rational endpoint, so the value stays strictly inside the interval."
    elif form.pairs:
        inside = "A square root of a sum of two square roots is not attained at a rational endpoint, so the value stays strictly inside the interval."
    elif form.nests:
        inside = "A square root of a binomial is not attained at a rational endpoint, so the value stays strictly inside the interval."
    elif form.towers and form.terms:
        if packed:
            inside = "A square-free radical and a nested radical are not attained at a rational endpoint, so the value stays strictly inside the interval."
        else:
            inside = "A square-free radical and a nested radical of one square-free integer are not attained at a rational endpoint, so the value stays strictly inside the interval."
    elif form.towers:
        if packed:
            inside = "A nested radical is not attained at a rational endpoint, so the value stays strictly inside the interval."
        else:
            inside = "A nested radical of one square-free integer is not attained at a rational endpoint, so the value stays strictly inside the interval."
    else:
        inside = "A square-free radical is not attained at a rational endpoint, so the value stays strictly inside the interval."
    for depth in _DEPTHS:
        lower, upper = _enclose(form, depth)
        if upper.num <= 0 or lower.num >= 0:
            return (
                f"Enclosure at depth {depth}: ({show_ratio(lower)}, {show_ratio(upper)}).",
                inside,
                "An upper bound at most 0 puts the difference strictly below 0. A lower bound at least 0 puts it strictly above 0.",
            )
    return ("The enclosure did not separate the difference from zero.",)


def _apart(form: RealForm) -> bool:
    return _classify(form) in {"lt", "gt"}


def _direction_sentence(direction: str) -> str:
    if direction == "lt":
        return "The difference is strictly negative."
    if direction == "gt":
        return "The difference is strictly positive."
    if direction == "eq":
        return ""
    return "The two Cauchy classes were not separated in this slice."


def _is_zero(form: RealForm) -> bool:
    return _is_rational(form) and form.constant.num == 0


def _is_rational(form: RealForm) -> bool:
    return (
        not form.terms
        and not form.towers
        and not form.nests
        and not form.pairs
        and not form.deeps
        and not form.highs
        and not form.peaks
        and not form.crests and not form.summits and not form.apexes and not form.shells and not form.folds and not form.quads and not form.algebras
    )


def _form_id(form: RealForm) -> str:
    parts = [f"k{form.constant.num}.{form.constant.den}"]
    for coeff, rad in form.terms:
        parts.append(f"t{coeff.num}.{coeff.den}.s{rad}")
    for coeff, base, numer, log_den in form.towers:
        parts.append(f"w{coeff.num}.{coeff.den}.b{base}.n{numer}.d{log_den}")
    for coeff, constant, sqrt_coeff, rad in form.nests:
        parts.append(
            f"g{coeff.num}.{coeff.den}.c{constant.num}.{constant.den}.b{sqrt_coeff.num}.{sqrt_coeff.den}.r{rad}"
        )
    for coeff, left_c, left_r, right_c, right_r in form.pairs:
        parts.append(f"p{coeff.num}.{coeff.den}.a{left_c}.m{left_r}.b{right_c}.n{right_r}")
    for coeff, mult, constant, sqrt_coeff, rad in form.deeps:
        parts.append(
            f"h{coeff.num}.{coeff.den}.m{mult}.c{constant}.b{sqrt_coeff}.r{rad}"
        )
    for coeff, mult, left_c, left_r, right_c, right_r in form.highs:
        parts.append(
            f"q{coeff.num}.{coeff.den}.m{mult}.a{left_c}.u{left_r}.b{right_c}.v{right_r}"
        )
    for coeff, pmult, hmult, left_c, left_r, right_c, right_r in form.peaks:
        parts.append(
            f"y{coeff.num}.{coeff.den}.p{pmult}.h{hmult}.a{left_c}.u{left_r}.b{right_c}.v{right_r}"
        )
    for coeff, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.crests:
        parts.append(
            f"z{coeff.num}.{coeff.den}.q{qmult}.p{pmult}.h{hmult}.a{left_c}.u{left_r}.b{right_c}.v{right_r}"
        )
    for coeff, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.summits:
        parts.append(
            f"j{coeff.num}.{coeff.den}.s{smult}.q{qmult}.p{pmult}.h{hmult}.a{left_c}.u{left_r}.b{right_c}.v{right_r}"
        )
    for coeff, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.apexes:
        parts.append(
            f"x{coeff.num}.{coeff.den}.e{amult}.s{smult}.q{qmult}.p{pmult}.h{hmult}.a{left_c}.u{left_r}.b{right_c}.v{right_r}"
        )
    for coeff, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.shells:
        mults = ".".join(f"m{mult}" for mult in extra)
        parts.append(
            f"o{coeff.num}.{coeff.den}.{mults}.e{amult}.s{smult}.q{qmult}.p{pmult}.h{hmult}.a{left_c}.u{left_r}.b{right_c}.v{right_r}"
        )
    for coeff, extra, mult, constant, sqrt_coeff, rad in form.folds:
        mults = ".".join(f"m{item}" for item in extra)
        parts.append(
            f"f{coeff.num}.{coeff.den}.{mults}.d{mult}.c{constant}.b{sqrt_coeff}.r{rad}"
        )
    for coeff, constant, first_coeff, first, second_coeff, second, product_coeff in form.quads:
        parts.append(
            "u"
            f"{coeff.num}.{coeff.den}."
            f"c{constant.num}.{constant.den}."
            f"a{first_coeff.num}.{first_coeff.den}.p{first}."
            f"b{second_coeff.num}.{second_coeff.den}.q{second}."
            f"d{product_coeff.num}.{product_coeff.den}"
        )
    for coeff, coeffs, index in form.algebras:
        body = ".".join(str(value) for value in coeffs)
        parts.append(f"r{coeff.num}.{coeff.den}.p{body}.i{index}")
    return "math.cauchy." + ".".join(parts)


def _ratio_piece(value: Ratio) -> tuple[str, bool]:
    text = str(abs(value.num)) if value.den == 1 else f"{abs(value.num)}/{value.den}"
    return text, value.num < 0


def _term_piece(coeff: Ratio, rad: int) -> tuple[str, bool]:
    return _scaled_piece(f"sqrt({rad})", coeff)


def _tower_piece(coeff: Ratio, base: int, numer: int, log_den: int) -> tuple[str, bool]:
    shown = base if numer == 1 else base**numer
    body = str(shown)
    for _ in range(log_den):
        body = f"sqrt({body})"
    return _scaled_piece(body, coeff)


def _nest_piece(coeff: Ratio, constant: Ratio, sqrt_coeff: Ratio, rad: int) -> tuple[str, bool]:
    inside = show_form(RealForm(constant, ((sqrt_coeff, rad),)))
    return _scaled_piece(f"sqrt({inside})", coeff)


def _pair_piece(coeff: Ratio, left_c: int, left_r: int, right_c: int, right_r: int) -> tuple[str, bool]:
    inside = show_form(_pair_inside(left_c, left_r, right_c, right_r))
    return _scaled_piece(f"sqrt({inside})", coeff)


def _deep_piece(coeff: Ratio, mult: int, constant: int, sqrt_coeff: int, rad: int) -> tuple[str, bool]:
    inside = show_form(RealForm(_ratio(constant, 1), ((_ratio(sqrt_coeff, 1), rad),)))
    nested = f"sqrt({inside})"
    body = nested if mult == 1 else f"{mult} * {nested}"
    return _scaled_piece(f"sqrt({body})", coeff)


def _high_piece(
    coeff: Ratio,
    mult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> tuple[str, bool]:
    inside = show_form(_pair_inside(left_c, left_r, right_c, right_r))
    nested = f"sqrt({inside})"
    body = nested if mult == 1 else f"{mult} * {nested}"
    return _scaled_piece(f"sqrt({body})", coeff)


def _peak_body(pmult: int, hmult: int, left_c: int, left_r: int, right_c: int, right_r: int) -> str:
    inside = show_form(_pair_inside(left_c, left_r, right_c, right_r))
    nested = f"sqrt({inside})"
    high_body = nested if hmult == 1 else f"{hmult} * {nested}"
    high = f"sqrt({high_body})"
    return high if pmult == 1 else f"{pmult} * {high}"


def _peak_piece(
    coeff: Ratio,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> tuple[str, bool]:
    return _scaled_piece(f"sqrt({_peak_body(pmult, hmult, left_c, left_r, right_c, right_r)})", coeff)


def _crest_body(
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> str:
    nested = f"sqrt({_peak_body(pmult, hmult, left_c, left_r, right_c, right_r)})"
    return nested if qmult == 1 else f"{qmult} * {nested}"


def _crest_piece(
    coeff: Ratio,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> tuple[str, bool]:
    return _scaled_piece(
        f"sqrt({_crest_body(qmult, pmult, hmult, left_c, left_r, right_c, right_r)})",
        coeff,
    )


def _summit_body(
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> str:
    nested = f"sqrt({_crest_body(qmult, pmult, hmult, left_c, left_r, right_c, right_r)})"
    return nested if smult == 1 else f"{smult} * {nested}"


def _summit_piece(
    coeff: Ratio,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> tuple[str, bool]:
    return _scaled_piece(
        f"sqrt({_summit_body(smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r)})",
        coeff,
    )


def _apex_body(
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> str:
    nested = f"sqrt({_summit_body(smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r)})"
    return nested if amult == 1 else f"{amult} * {nested}"


def _apex_piece(
    coeff: Ratio,
    amult: int,
    smult: int,
    qmult: int,
    pmult: int,
    hmult: int,
    left_c: int,
    left_r: int,
    right_c: int,
    right_r: int,
) -> tuple[str, bool]:
    return _scaled_piece(
        f"sqrt({_apex_body(amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r)})",
        coeff,
    )



def _algebra_piece(coeff: Ratio, coeffs: tuple[int, ...], index: int) -> tuple[str, bool]:
    from pgi.math.algebraic import AlgebraicReal, show_algebraic

    return _scaled_piece(show_algebraic(AlgebraicReal(coeffs, index)), coeff)


def _algebra_bounds(coeffs: tuple[int, ...], index: int) -> tuple[Ratio, Ratio]:
    from pgi.math.algebraic import AlgebraicReal

    return AlgebraicReal(coeffs, index).interval


def _compare_algebras(left: RealForm, right: RealForm) -> str:
    from pgi.math.algebraic import (
        AlgebraicReal,
        compare_algebraic,
        compare_algebraic_to_ratio,
    )

    if left == right:
        return "eq"
    left_alg = _as_unit_algebra(left)
    right_alg = _as_unit_algebra(right)
    if left_alg is not None and right_alg is not None:
        return compare_algebraic(left_alg, right_alg)
    if left_alg is not None and _is_rational(right):
        return compare_algebraic_to_ratio(left_alg, right.constant)
    if right_alg is not None and _is_rational(left):
        flipped = compare_algebraic_to_ratio(right_alg, left.constant)
        return {"lt": "gt", "gt": "lt", "eq": "eq"}[flipped]
    # Enclose both and refine the algebraic side until the intervals separate,
    # or prove equality if a radical form satisfies the minimal polynomial and
    # lies in the isolating interval.
    if left_alg is not None and _algebra_holds(left_alg, right):
        return "eq"
    if right_alg is not None and _algebra_holds(right_alg, left):
        return "eq"
    left_low, left_high = _enclose(left, 8)
    right_low, right_high = _enclose(right, 8)
    if _qcmp(left_high, right_low) <= 0:
        return "lt"
    if _qcmp(right_high, left_low) <= 0:
        return "gt"
    for depth in range(9, 24):
        left_low, left_high = _enclose(left, depth)
        right_low, right_high = _enclose(right, depth)
        if _qcmp(left_high, right_low) <= 0:
            return "lt"
        if _qcmp(right_high, left_low) <= 0:
            return "gt"
    raise NotExact("these algebraic numbers could not be compared")


def _as_unit_algebra(form: RealForm) -> object | None:
    from pgi.math.algebraic import AlgebraicReal

    if not form.algebras or not _algebra_only(form):
        return None
    if len(form.algebras) != 1:
        return None
    coeff, coeffs, index = form.algebras[0]
    if coeff != _ratio(1, 1):
        return None
    return AlgebraicReal(coeffs, index)


def _algebra_only(form: RealForm) -> bool:
    return (
        form.constant.num == 0
        and not form.terms
        and not form.towers
        and not form.nests
        and not form.pairs
        and not form.deeps
        and not form.highs
        and not form.peaks
        and not form.crests
        and not form.summits
        and not form.apexes
        and not form.shells
        and not form.folds
        and not form.quads
        and form.algebras
    )


def _algebra_holds(number: object, form: RealForm) -> bool:
    from pgi.math.algebraic import AlgebraicReal, eval_int

    if not isinstance(number, AlgebraicReal):
        return False
    total = _algebra_poly_eval(number.coeffs, form)
    if not _is_rational(total) or total.constant.num != 0:
        return False
    low, high = number.interval
    enclosed_low, enclosed_high = _enclose(form, 12)
    return _qcmp(low, enclosed_high) < 0 and _qcmp(enclosed_low, high) < 0


def _algebra_poly_eval(coeffs: tuple[int, ...], value: RealForm) -> RealForm:
    total = RealForm(_ratio(0, 1), ())
    power = RealForm(_ratio(1, 1), ())
    for coeff in coeffs:
        total = _add_forms(total, _scale(power, _ratio(coeff, 1)))
        power = _mul_forms(power, value)
    return total


def real_of_algebraic(term: Term) -> RealTheorem:
    if not isinstance(term, App) or term.op != "root" or len(term.args) < 4:
        raise NotExact("this algebraic number stays outside")
    if not all(isinstance(arg, IntLit) for arg in term.args):
        raise NotExact("this algebraic number stays outside")
    values = tuple(arg.n for arg in term.args)
    coeff = _ratio(values[0], values[1])
    index = values[-1]
    coeffs = values[2:-1]
    form = form_of_algebraic(coeffs, index, coeff)
    return RealTheorem(
        form,
        "Real.algebraic",
        detail=(
            "This real is the indicated real root of a primitive irreducible integer polynomial.",
            "A Sturm sequence isolates that unique root in a rational interval, and the index is the place of the root among the real roots, ordered increasingly.",
        ),
    )


def form_of_algebraic(coeffs: tuple[int, ...], index: int, coeff: Ratio | None = None) -> RealForm:
    """A checked real algebraic number as a normal form."""

    from pgi.math.algebraic import AlgebraicReal

    AlgebraicReal(coeffs, index)
    scale = coeff if coeff is not None else _ratio(1, 1)
    if scale.num == 0:
        return RealForm(_ratio(0, 1), ())
    return RealForm(_ratio(0, 1), (), algebras=((scale, coeffs, index),))


def try_radical_form(coeffs: tuple[int, ...], index: int) -> RealForm | None:
    """Return an admitted radical form of this algebraic root, when there is one."""

    from pgi.math.algebraic import AlgebraicReal, degree, leading

    number = AlgebraicReal(coeffs, index)
    poly = number.coeffs
    n = degree(poly)
    # x^n - k for n a power of two and k a positive integer is a nested square root.
    if (
        n >= 2
        and n.bit_count() == 1
        and leading(poly) == 1
        and all(value == 0 for value in poly[1:-1])
        and poly[0] < 0
    ):
        form = _sqrt_form(_ratio(-poly[0], 1))
        steps = n.bit_length() - 2
        for _ in range(steps):
            form = _sqrt_of_form(form)
        if n % 2 == 0:
            if index == 1:
                form = _neg_form(form)
            elif index != 2:
                return None
        elif index != 1:
            return None
        if not _algebra_holds(number, form):
            raise KernelError("a constructed radical did not match this algebraic root")
        return form
    if n == 2:
        constant, linear, lead = (poly[0], poly[1], poly[2])
        # (-b ± sqrt(b^2 - 4ac)) / (2a)
        disc = linear * linear - 4 * lead * constant
        if disc <= 0:
            return None
        try:
            sqrt_disc = _sqrt_form(_ratio(disc, 1))
            two_a = _ratio(2 * lead, 1)
            minus_b = _ratio(-linear, 1)
            plus = _div_form(_add_forms(RealForm(minus_b, ()), sqrt_disc), RealForm(two_a, ()))
            minus = _div_form(_sub_forms(RealForm(minus_b, ()), sqrt_disc), RealForm(two_a, ()))
        except (NotExact, KernelError):
            return None
        # Choose the root that lies in the isolating interval.
        for candidate in (minus, plus):
            if _algebra_holds(number, candidate):
                return candidate
        return None
    return None

def _scaled_piece(body: str, coeff: Ratio) -> tuple[str, bool]:
    magnitude, _negative = _ratio_piece(_ratio(abs(coeff.num), coeff.den))
    text = body if magnitude == "1" else f"{magnitude} * {body}"
    return text, coeff.num < 0


def show_ratio(value: Ratio) -> str:
    text, negative = _ratio_piece(value)
    return f"-{text}" if negative else text


def _note(text: str) -> Rule:
    return Rule(
        id="math.open",
        layer="base",
        stage="check",
        title=text,
        produces=f"open({text})",
        detail_lines=(text,),
    )


def _justified(theorem: RealTheorem) -> bool:
    form = theorem.form
    if not _canonical(form):
        return False
    rule = theorem.rule
    premises = theorem.premises
    try:
        if rule == "Real.of_rat":
            return not premises and _is_rational(form)
        if rule == "Real.algebraic":
            return not premises and bool(form.algebras) and _canonical(form)
        if rule == "Real.sqrt":
            if len(premises) != 1:
                return False
            expected = _sqrt_of_form(premises[0].form)
            if form != expected:
                return False
            for _coeff, rad in form.terms:
                _bounds(rad, _CERT_DEPTH)
            for _coeff, base, numer, log_den in form.towers:
                _tower_certificate_lines(base, numer, log_den)
            for _coeff, constant, sqrt_coeff, rad in form.nests:
                if constant.den != 1 or sqrt_coeff.den != 1:
                    return False
                _nest_certificate_lines(constant.num, sqrt_coeff.num, rad)
            for _coeff, left_c, left_r, right_c, right_r in form.pairs:
                _pair_certificate_lines(left_c, left_r, right_c, right_r)
            for _coeff, mult, constant, sqrt_coeff, rad in form.deeps:
                _deep_certificate_lines(mult, constant, sqrt_coeff, rad)
            for _coeff, mult, left_c, left_r, right_c, right_r in form.highs:
                _high_certificate_lines(mult, left_c, left_r, right_c, right_r)
            for _coeff, pmult, hmult, left_c, left_r, right_c, right_r in form.peaks:
                _peak_certificate_lines(pmult, hmult, left_c, left_r, right_c, right_r)
            for _coeff, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.crests:
                _crest_certificate_lines(qmult, pmult, hmult, left_c, left_r, right_c, right_r)
            for _coeff, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.summits:
                _summit_certificate_lines(
                    smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
                )
            for (
                _coeff,
                amult,
                smult,
                qmult,
                pmult,
                hmult,
                left_c,
                left_r,
                right_c,
                right_r,
            ) in form.apexes:
                _apex_certificate_lines(
                    amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
                )
            for (
                _coeff,
                extra,
                amult,
                smult,
                qmult,
                pmult,
                hmult,
                left_c,
                left_r,
                right_c,
                right_r,
            ) in form.shells:
                _shell_certificate_lines(
                    extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
                )
            for _coeff, extra, mult, constant, sqrt_coeff, rad in form.folds:
                _fold_certificate_lines(extra, mult, constant, sqrt_coeff, rad)
            for (
                _coeff,
                constant,
                first_coeff,
                first,
                second_coeff,
                second,
                product_coeff,
            ) in form.quads:
                _quad_certificate_lines(
                    constant, first_coeff, first, second_coeff, second, product_coeff
                )
            return True
        if rule == "Real.neg":
            return len(premises) == 1 and form == _neg_form(premises[0].form)
        if rule == "Real.add":
            return len(premises) == 2 and form == _add_forms(premises[0].form, premises[1].form)
        if rule == "Real.sub":
            return len(premises) == 2 and form == _sub_forms(premises[0].form, premises[1].form)
        if rule == "Real.mul":
            return len(premises) == 2 and form == _mul_forms(premises[0].form, premises[1].form)
        if rule == "Real.div":
            if len(premises) != 2 or _is_zero(premises[1].form):
                return False
            if not _apart(premises[1].form):
                return False
            return _mul_forms(form, premises[1].form) == premises[0].form
    except NotExact:
        return False
    return False


_UNSEEN_DIVISOR = "a divisor the kernel cannot see as nonzero stays open"
_SPAN_LIMIT = 8
_DEGREE_LIMIT = 256


def _div_lines(divisor: RealForm) -> tuple[str, ...]:
    if _is_rational(divisor):
        return (
            "Isabelle divide_real_def: x div y = x * inverse y.",
            "The divisor is a nonzero constant sequence.",
            "Isabelle proves inverse (0::real) = 0. That convention is not a rule here.",
        )
    lines = [
        "Isabelle divide_real_def: x div y = x * inverse y.",
        "Isabelle divide_inverse: a / b = a * inverse b.",
        "The divisor is bounded away from zero.",
        "The constructed multiplier times the divisor is the constant sequence 1.",
        "Isabelle inverse_unique: a * b = 1 names the inverse.",
        "Multiplication rewrites nonnegative roots by Isabelle real_root_mult. A square root and a fourth root are one integer to the power 1/2^k.",
        "Isabelle proves inverse (0::real) = 0. That convention is not a rule here.",
    ]
    if (
        not divisor.towers
        and not divisor.nests
        and not divisor.pairs
        and not divisor.deeps
        and not divisor.highs
        and not divisor.peaks
        and not divisor.crests and not divisor.summits and not divisor.apexes and not divisor.shells and not divisor.folds
        and divisor.constant.num == 0
        and len(divisor.terms) == 1
        and divisor.terms[0][0] == _ratio(1, 1)
    ):
        lines.insert(
            2,
            "Isabelle real_div_sqrt: 0 <= x implies x / sqrt x = sqrt x. For a positive radicand the inverse of the root is that root over the radicand.",
        )
    return tuple(lines)


def _div_form(left: RealForm, right: RealForm) -> RealForm:
    if left.algebras or right.algebras:
        raise NotExact("this algebraic quotient stays outside")
    if _is_zero(right):
        raise NotExact("division by zero")
    if not _apart(right):
        raise NotExact(_UNSEEN_DIVISOR)
    if _TOWER_GUARD == 0:
        with _tower_guard():
            towered = _div_forms_tower(left, right)
        if towered is not None:
            return towered
    inverse = _inverse_form(right)
    if _mul_forms(inverse, right) != RealForm(_ratio(1, 1), ()):
        raise KernelError("constructed inverse did not multiply back to 1")
    return _mul_forms(left, inverse)


def _as_shifted_radical(form: RealForm) -> tuple[Ratio, RealForm] | None:
    if form.constant.num == 0 or form.terms or form.towers:
        return None
    families = [
        ("nests", form.nests),
        ("pairs", form.pairs),
        ("deeps", form.deeps),
        ("highs", form.highs),
        ("peaks", form.peaks),
        ("crests", form.crests),
        ("summits", form.summits),
        ("apexes", form.apexes),
        ("shells", form.shells),
        ("folds", form.folds),
        ("quads", form.quads),
    ]
    present = [(name, items) for name, items in families if items]
    if len(present) != 1 or len(present[0][1]) != 1:
        return None
    name, items = present[0]
    kwargs = {name: items}
    radical = RealForm(_ratio(0, 1), (), **kwargs)
    return form.constant, radical


def _invert_shifted_radical(form: RealForm) -> RealForm:
    parsed = _as_shifted_radical(form)
    if parsed is None:
        raise NotExact("this quotient stays outside")
    constant, radical = parsed
    power = radical
    step_const = constant
    cofactor = _sub_forms(RealForm(constant, ()), radical)
    try:
        for _ in range(16):
            square = _mul_forms(power, power)
            denom = _sub_forms(RealForm(_qmul(step_const, step_const), ()), square)
            try:
                inverse_denom = _inverse_form(denom)
            except NotExact:
                next_const = _qmul(step_const, step_const)
                cofactor = _mul_forms(cofactor, _add_forms(RealForm(next_const, ()), square))
                power = square
                step_const = next_const
                continue
            result = _mul_forms(cofactor, inverse_denom)
            if _mul_forms(result, form) != RealForm(_ratio(1, 1), ()):
                raise KernelError("shifted inverse did not multiply back to 1")
            return result
    except NotExact as exc:
        raise NotExact("this quotient stays outside") from exc
    raise NotExact("this quotient stays outside")


def _inverse_form(form: RealForm) -> RealForm:
    if _is_rational(form):
        return RealForm(_inverse(form.constant), ())
    if _TOWER_GUARD == 0:
        with _tower_guard():
            towered = _inverse_form_tower(form)
        if towered is not None:
            return towered
    if _as_shifted_radical(form) is not None:
        return _invert_shifted_radical(form)
    if form.quads:
        return _invert_quad(form)
    if form.folds:
        return _invert_fold(form)
    if form.shells:
        return _invert_shell(form)
    if form.apexes:
        return _invert_apex(form)
    if form.summits:
        return _invert_summit(form)
    if form.crests:
        return _invert_crest(form)
    if form.peaks:
        return _invert_peak(form)
    if form.highs:
        return _invert_high(form)
    if form.deeps:
        return _invert_deep(form)
    if form.pairs:
        return _invert_pair(form)
    if form.nests:
        if len(form.nests) == 2:
            return _invert_two_nests(form)
        return _invert_binomial_nest(form)
    monomial = _monomial_power(form)
    if monomial is not None:
        return _inverse_monomial(*monomial)
    if form.towers:
        located = _one_base(form)
        if located is not None and _square_part(located[0]) == (1, located[0]):
            base, level = located
            return _invert_on_basis(form, _dyadic_basis(base, level), _dyadic_reader(base, level))
        return _invert_prime_span(form)
    primes = _quadratic_primes(form)
    if len(primes) > _SPAN_LIMIT:
        raise NotExact("this quotient stays outside")
    return _invert_on_basis(form, _quadratic_basis(primes), _quadratic_reader(primes))


def _invert_high(form: RealForm) -> RealForm:
    if (
        form.constant.num != 0
        or form.terms
        or form.towers
        or form.nests
        or form.pairs
        or form.deeps
        or form.peaks
        or form.crests or form.summits or form.apexes or form.shells or form.folds or form.quads or form.algebras
        or len(form.highs) != 1
    ):
        raise NotExact("this quotient stays outside")
    squared = _square_high(form)
    if (
        not squared.pairs
        or squared.constant.num != 0
        or squared.terms
        or squared.towers
        or squared.nests
        or squared.deeps
        or squared.highs
        or squared.peaks
        or squared.crests or squared.summits or squared.apexes or squared.shells or squared.folds
    ):
        raise NotExact("this quotient stays outside")
    return _mul_forms(form, _inverse_form(squared))




def _invert_apex(form: RealForm) -> RealForm:
    if (
        form.constant.num != 0
        or form.terms
        or form.towers
        or form.nests
        or form.pairs
        or form.deeps
        or form.highs
        or form.peaks
        or form.crests
        or form.summits
        or form.shells or form.folds or form.quads or form.algebras
        or len(form.apexes) != 1
    ):
        raise NotExact("this quotient stays outside")
    squared = _square_apex(form)
    if (
        len(squared.summits) != 1
        or squared.constant.num != 0
        or squared.terms
        or squared.towers
        or squared.nests
        or squared.pairs
        or squared.deeps
        or squared.highs
        or squared.peaks
        or squared.crests
        or squared.apexes or squared.shells or squared.folds
    ):
        raise NotExact("this quotient stays outside")
    inverse = _inverse_form(squared)
    if (
        len(inverse.summits) != 1
        or inverse.constant.num != 0
        or inverse.terms
        or inverse.towers
        or inverse.nests
        or inverse.pairs
        or inverse.deeps
        or inverse.highs
        or inverse.peaks
        or inverse.crests
        or inverse.apexes or inverse.shells or inverse.folds
    ):
        raise NotExact("this quotient stays outside")
    coeff, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r = inverse.summits[0]
    return _apex_sqrt(coeff, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r)


def _invert_summit(form: RealForm) -> RealForm:
    if (
        form.constant.num != 0
        or form.terms
        or form.towers
        or form.nests
        or form.pairs
        or form.deeps
        or form.highs
        or form.peaks
        or form.crests
        or form.apexes or form.shells or form.folds or form.quads or form.algebras
        or len(form.summits) != 1
    ):
        raise NotExact("this quotient stays outside")
    squared = _square_summit(form)
    if (
        len(squared.crests) != 1
        or squared.constant.num != 0
        or squared.terms
        or squared.towers
        or squared.nests
        or squared.pairs
        or squared.deeps
        or squared.highs
        or squared.peaks
        or squared.summits or squared.apexes or squared.shells or squared.folds
    ):
        raise NotExact("this quotient stays outside")
    inverse = _inverse_form(squared)
    if (
        len(inverse.crests) != 1
        or inverse.constant.num != 0
        or inverse.terms
        or inverse.towers
        or inverse.nests
        or inverse.pairs
        or inverse.deeps
        or inverse.highs
        or inverse.peaks
        or inverse.summits or inverse.apexes or inverse.shells or inverse.folds
    ):
        raise NotExact("this quotient stays outside")
    coeff, qmult, pmult, hmult, left_c, left_r, right_c, right_r = inverse.crests[0]
    return _summit_sqrt(coeff, qmult, pmult, hmult, left_c, left_r, right_c, right_r)


def _invert_crest(form: RealForm) -> RealForm:
    if (
        form.constant.num != 0
        or form.terms
        or form.towers
        or form.nests
        or form.pairs
        or form.deeps
        or form.highs
        or form.peaks
        or form.summits or form.apexes or form.shells or form.folds or form.quads or form.algebras
        or len(form.crests) != 1
    ):
        raise NotExact("this quotient stays outside")
    squared = _square_crest(form)
    if (
        len(squared.peaks) != 1
        or squared.constant.num != 0
        or squared.terms
        or squared.towers
        or squared.nests
        or squared.pairs
        or squared.deeps
        or squared.highs
        or squared.crests or squared.summits or squared.apexes or squared.shells or squared.folds
    ):
        raise NotExact("this quotient stays outside")
    inverse = _inverse_form(squared)
    if (
        len(inverse.peaks) != 1
        or inverse.constant.num != 0
        or inverse.terms
        or inverse.towers
        or inverse.nests
        or inverse.pairs
        or inverse.deeps
        or inverse.highs
        or inverse.crests or inverse.summits or inverse.apexes or inverse.shells or inverse.folds
    ):
        raise NotExact("this quotient stays outside")
    coeff, pmult, hmult, left_c, left_r, right_c, right_r = inverse.peaks[0]
    return _crest_sqrt(coeff, pmult, hmult, left_c, left_r, right_c, right_r)


def _invert_peak(form: RealForm) -> RealForm:
    if (
        form.constant.num != 0
        or form.terms
        or form.towers
        or form.nests
        or form.pairs
        or form.deeps
        or form.highs
        or form.crests or form.summits or form.apexes or form.shells or form.folds or form.quads or form.algebras
        or len(form.peaks) != 1
    ):
        raise NotExact("this quotient stays outside")
    squared = _square_peak(form)
    if (
        len(squared.highs) != 1
        or squared.constant.num != 0
        or squared.terms
        or squared.towers
        or squared.nests
        or squared.pairs
        or squared.deeps
        or squared.peaks
        or squared.crests or squared.summits or squared.apexes or squared.shells or squared.folds
    ):
        raise NotExact("this quotient stays outside")
    inverse = _inverse_form(squared)
    if (
        len(inverse.highs) != 1
        or inverse.constant.num != 0
        or inverse.terms
        or inverse.towers
        or inverse.nests
        or inverse.pairs
        or inverse.deeps
        or inverse.peaks
        or inverse.crests or inverse.summits or inverse.apexes or inverse.shells or inverse.folds
    ):
        raise NotExact("this quotient stays outside")
    coeff, hmult, left_c, left_r, right_c, right_r = inverse.highs[0]
    return _peak_sqrt(coeff, hmult, left_c, left_r, right_c, right_r)


def _invert_deep(form: RealForm) -> RealForm:
    if (
        form.constant.num != 0
        or form.terms
        or form.towers
        or form.nests
        or form.pairs
        or form.highs or form.peaks or form.crests or form.summits or form.apexes or form.shells or form.folds or form.quads or form.algebras
        or len(form.deeps) != 1
    ):
        raise NotExact("this quotient stays outside")
    squared = _square_deep(form)
    if not squared.nests or squared.constant.num != 0 or squared.terms or squared.towers or squared.pairs or squared.deeps or squared.highs or squared.peaks or squared.crests or squared.summits or squared.apexes or squared.shells or squared.folds:
        raise NotExact("this quotient stays outside")
    return _mul_forms(form, _inverse_form(squared))


def _invert_pair(form: RealForm) -> RealForm:
    if form.constant.num != 0 or form.terms or form.towers or form.nests or form.deeps or form.highs or form.peaks or form.crests or form.summits or form.apexes or form.shells or form.folds or form.quads or form.algebras or len(form.pairs) != 1:
        raise NotExact("this quotient stays outside")
    outer, left_c, left_r, right_c, right_r = form.pairs[0]
    gap = left_c * left_c * left_r - right_c * right_c * right_r
    if gap < 0:
        conj_left, conj_right = -left_c, right_c
        magnitude = -gap
    elif gap > 0:
        conj_left, conj_right = left_c, -right_c
        magnitude = gap
    else:
        raise KernelError("pair inverse met equal squares")
    conjugate = _pair_sqrt(
        _ratio(magnitude * conj_left, 1),
        left_r,
        _ratio(magnitude * conj_right, 1),
        right_r,
    )
    return _scale(conjugate, _inverse(_qmul(outer, _ratio(magnitude, 1))))


def _monomial_power(form: RealForm) -> tuple[Ratio, int, int, int] | None:
    if (
        form.pairs
        or form.nests
        or form.deeps
        or form.highs or form.peaks or form.crests or form.summits or form.apexes or form.shells or form.folds or form.quads or form.algebras
        or form.constant.num != 0
        or len(form.terms) + len(form.towers) != 1
    ):
        return None
    if form.terms:
        coeff, rad = form.terms[0]
        return coeff, rad, 1, 1
    coeff, base, numer, log_den = form.towers[0]
    return coeff, base, numer, log_den


def _inverse_monomial(coeff: Ratio, base: int, numer: int, log_den: int) -> RealForm:
    if coeff.num == 0:
        raise NotExact("division by zero")
    complement = (1 << log_den) - numer
    powered = _power_form(_ratio(1, 1), base, complement, log_den)
    unit = _scale(powered, _inverse(_ratio(base, 1)))
    return _scale(unit, _inverse(coeff))


def _one_base(form: RealForm) -> tuple[int, int] | None:
    bases: set[int] = set()
    level = 0
    for _coeff, rad in form.terms:
        bases.add(rad)
        level = max(level, 1)
    for _coeff, base, _numer, log_den in form.towers:
        bases.add(base)
        level = max(level, log_den)
    if len(bases) != 1:
        return None
    return next(iter(bases)), level


def _dyadic_basis(base: int, level: int) -> tuple[RealForm, ...]:
    if level < 1 or level > _SPAN_LIMIT:
        raise NotExact("this quotient stays outside")
    return tuple(_power_form(_ratio(1, 1), base, index, level) for index in range(1 << level))


def _dyadic_reader(base: int, level: int):
    width = 1 << level
    half = 1 << (level - 1)

    def read(form: RealForm) -> list[Ratio]:
        if form.nests or form.pairs or form.deeps or form.highs or form.peaks or form.crests or form.summits or form.apexes or form.shells or form.folds or form.quads or form.algebras:
            raise KernelError("a power product left the one-base span")
        coords = [_ratio(0, 1) for _ in range(width)]
        coords[0] = form.constant
        for coeff, rad in form.terms:
            if rad != base:
                raise KernelError("a power product left the one-base span")
            coords[half] = _qadd(coords[half], coeff)
        for coeff, other, numer, log_den in form.towers:
            if other != base or log_den > level:
                raise KernelError("a power product left the one-base span")
            index = numer << (level - log_den)
            if index <= 0 or index >= width:
                raise KernelError("a power product left the one-base span")
            coords[index] = _qadd(coords[index], coeff)
        return coords

    return read


def _invert_prime_span(form: RealForm) -> RealForm:
    primes, level = _span_primes(form)
    width = 1 << level
    if width ** len(primes) > _DEGREE_LIMIT:
        raise NotExact("this quotient stays outside")
    return _invert_on_basis(form, _prime_basis(primes, level), _prime_reader(primes, level))


def _span_primes(form: RealForm) -> tuple[tuple[int, ...], int]:
    found: set[int] = set()
    level = 1
    for _coeff, rad in form.terms:
        for prime, exponent in _prime_exponents(rad):
            if exponent != 1:
                raise KernelError("a square-free radicand had a square factor")
            found.add(prime)
    for _coeff, base, _numer, log_den in form.towers:
        level = max(level, log_den)
        for prime, _exponent in _prime_exponents(base):
            found.add(prime)
    if not found or level < 1 or level > _SPAN_LIMIT or len(found) > _SPAN_LIMIT:
        raise NotExact("this quotient stays outside")
    return tuple(sorted(found)), level


def _prime_basis(primes: tuple[int, ...], level: int) -> tuple[RealForm, ...]:
    width = 1 << level
    forms: list[RealForm] = []
    for index in range(width ** len(primes)):
        exponents: dict[int, int] = {}
        cursor = index
        for prime in primes:
            exponent = cursor % width
            cursor //= width
            if exponent:
                exponents[prime] = exponent
        forms.append(_radical_from_exponents(_ratio(1, 1), exponents, level))
    return tuple(forms)


def _prime_reader(primes: tuple[int, ...], level: int):
    width = 1 << level
    degree = width ** len(primes)
    known = set(primes)

    def coordinate(exponents: dict[int, int]) -> int:
        index = 0
        stride = 1
        for prime in primes:
            exponent = exponents.get(prime, 0)
            if exponent < 0 or exponent >= width:
                raise KernelError("a radical left the span")
            index += exponent * stride
            stride *= width
        if index <= 0 or index >= degree:
            raise KernelError("a radical left the span")
        return index

    def exponents_of(base: int, numer: int, log_den: int) -> dict[int, int]:
        if log_den < 1 or log_den > level or numer <= 0:
            raise KernelError("a radical left the span")
        scaled = numer << (level - log_den)
        found: dict[int, int] = {}
        for prime, multiplicity in _prime_exponents(base):
            if prime not in known:
                raise KernelError("a radical left the span")
            exponent = multiplicity * scaled
            if exponent <= 0 or exponent >= width:
                raise KernelError("a radical left the span")
            found[prime] = exponent
        if not found:
            raise KernelError("a radical left the span")
        return found

    def read(form: RealForm) -> list[Ratio]:
        if form.nests or form.pairs or form.deeps or form.highs or form.peaks or form.crests or form.summits or form.apexes or form.shells or form.folds or form.quads or form.algebras:
            raise KernelError("a radical left the span")
        coords = [_ratio(0, 1) for _ in range(degree)]
        coords[0] = form.constant
        for coeff, rad in form.terms:
            slot = coordinate(exponents_of(rad, 1, 1))
            coords[slot] = _qadd(coords[slot], coeff)
        for coeff, base, numer, log_den in form.towers:
            slot = coordinate(exponents_of(base, numer, log_den))
            coords[slot] = _qadd(coords[slot], coeff)
        return coords

    return read


def _quadratic_primes(form: RealForm) -> tuple[int, ...]:
    found: set[int] = set()
    for _coeff, rad in form.terms:
        for prime, exponent in _prime_exponents(rad):
            if exponent != 1:
                raise KernelError("a square-free radicand had a square factor")
            found.add(prime)
    return tuple(sorted(found))


def _quadratic_basis(primes: tuple[int, ...]) -> tuple[RealForm, ...]:
    forms: list[RealForm] = []
    for mask in range(1 << len(primes)):
        if mask == 0:
            forms.append(RealForm(_ratio(1, 1), ()))
            continue
        rad = 1
        for index, prime in enumerate(primes):
            if mask & (1 << index):
                rad *= prime
        forms.append(_sqrt_form(_ratio(rad, 1)))
    return tuple(forms)


def _quadratic_reader(primes: tuple[int, ...]):
    width = 1 << len(primes)

    def read(form: RealForm) -> list[Ratio]:
        if form.towers or form.nests or form.pairs or form.deeps or form.highs or form.peaks or form.crests or form.summits or form.apexes or form.shells or form.folds or form.quads or form.algebras:
            raise KernelError("a square-root product left the basis")
        coords = [_ratio(0, 1) for _ in range(width)]
        coords[0] = form.constant
        for coeff, rad in form.terms:
            mask = _mask_of(rad, primes)
            coords[mask] = _qadd(coords[mask], coeff)
        return coords

    return read


def _mask_of(rad: int, primes: tuple[int, ...]) -> int:
    mask = 0
    rest = rad
    for index, prime in enumerate(primes):
        if rest % prime == 0:
            rest //= prime
            mask |= 1 << index
            if rest % prime == 0:
                raise KernelError("a square-free radicand had a square factor")
    if rest != 1 or mask == 0:
        raise KernelError("a square-root product left the basis")
    return mask


def _invert_binomial_nest(form: RealForm) -> RealForm:
    rads = {rad for _coeff, _constant, _sqrt_coeff, rad in form.nests}
    if len(rads) != 1 or form.towers:
        raise NotExact("this quotient stays outside")
    rad = next(iter(rads))
    for _coeff, term_rad in form.terms:
        if term_rad != rad:
            raise NotExact("this quotient stays outside")
    _coeff, constant, sqrt_coeff, _rad = form.nests[0]
    fund = _nest_form(_ratio(1, 1), constant, sqrt_coeff, rad)
    partner = _mul_forms(_sqrt_form(_ratio(rad, 1)), fund)
    if (
        partner.constant.num != 0
        or partner.terms
        or partner.towers
        or partner.pairs
        or partner.deeps
        or partner.highs or partner.peaks or partner.crests or partner.summits or partner.apexes or partner.shells or partner.folds
        or len(partner.nests) != 1
    ):
        raise NotExact("this quotient stays outside")
    unit, partner_const, partner_sqrt, partner_rad = partner.nests[0]
    if partner_rad != rad or unit.num == 0:
        raise NotExact("this quotient stays outside")
    fund_key = (constant, sqrt_coeff, rad)
    partner_key = (partner_const, partner_sqrt, partner_rad)
    if fund_key == partner_key:
        raise KernelError("binomial partner collided with the generator")
    basis = (
        RealForm(_ratio(1, 1), ()),
        _sqrt_form(_ratio(rad, 1)),
        fund,
        partner,
    )

    def read(value: RealForm) -> list[Ratio]:
        if value.towers or value.pairs or value.deeps or value.highs or value.peaks or value.crests or value.summits or value.apexes or value.shells or value.folds:
            raise NotExact("this quotient stays outside")
        coords = [_ratio(0, 1) for _ in range(4)]
        coords[0] = value.constant
        for coeff, term_rad in value.terms:
            if term_rad != rad:
                raise NotExact("this quotient stays outside")
            coords[1] = _qadd(coords[1], coeff)
        for coeff, nest_const, nest_sqrt, nest_rad in value.nests:
            key = (nest_const, nest_sqrt, nest_rad)
            if key == fund_key:
                coords[2] = _qadd(coords[2], coeff)
            elif key == partner_key:
                coords[3] = _qadd(coords[3], _qdiv(coeff, unit))
            else:
                raise NotExact("this quotient stays outside")
        return coords

    return _invert_on_basis(form, basis, read)


def _invert_on_basis(form: RealForm, basis: tuple[RealForm, ...], read) -> RealForm:
    columns = [read(_mul_forms(form, element)) for element in basis]
    coeffs = _solve_unit(columns)
    result = RealForm(_ratio(0, 1), ())
    for coeff, element in zip(coeffs, basis, strict=True):
        if coeff.num == 0:
            continue
        result = _add_forms(result, _scale(element, coeff))
    return result


def _solve_unit(columns: list[list[Ratio]]) -> list[Ratio]:
    width = len(columns)
    augmented: list[list[Ratio]] = []
    for row in range(width):
        line = [columns[column][row] for column in range(width)]
        line.append(_ratio(1 if row == 0 else 0, 1))
        augmented.append(line)
    for column in range(width):
        pivot = next((row for row in range(column, width) if augmented[row][column].num != 0), None)
        if pivot is None:
            raise KernelError("constructed inverse system was singular")
        if pivot != column:
            augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        scale = augmented[column][column]
        augmented[column] = [_qdiv(entry, scale) for entry in augmented[column]]
        for row in range(width):
            factor = augmented[row][column]
            if row == column or factor.num == 0:
                continue
            pivot_row = augmented[column]
            augmented[row] = [
                _qsub(entry, _qmul(factor, pivot_row[index])) for index, entry in enumerate(augmented[row])
            ]
    return [augmented[row][width] for row in range(width)]


def _canonical(form: RealForm) -> bool:
    if not _canonical_ratio(form.constant):
        return False
    previous = 1
    for coeff, rad in form.terms:
        if coeff.num == 0 or not _canonical_ratio(coeff):
            return False
        if rad <= previous or _square_part(rad) != (1, rad):
            return False
        previous = rad
    seen = (0, 0, 0)
    for coeff, base, numer, log_den in form.towers:
        if coeff.num == 0 or not _canonical_ratio(coeff):
            return False
        if log_den < 2 or numer <= 0 or numer >= (1 << log_den) or base <= 1:
            return False
        if _square_part(base) == (1, base):
            if numer % 2 == 0:
                return False
        elif numer != 1 or not _packed_base(base, log_den):
            return False
        key = (base, log_den, numer)
        if key <= seen:
            return False
        seen = key
    seen_nest: tuple[int, int, int, int, int] | None = None
    for coeff, constant, sqrt_coeff, rad in form.nests:
        if coeff.num == 0 or not _canonical_ratio(coeff):
            return False
        if constant.den != 1 or sqrt_coeff.den != 1 or sqrt_coeff.num == 0 or constant.num == 0:
            return False
        if rad <= 1 or _square_part(rad) != (1, rad):
            return False
        content = _gcd(abs(constant.num), abs(sqrt_coeff.num))
        if _square_part(content)[0] != 1:
            return False
        if not _binomial_positive(constant.num, sqrt_coeff.num, rad):
            return False
        if _denest(RealForm(constant, ((sqrt_coeff, rad),))) is not None:
            return False
        key = _nest_key(constant, sqrt_coeff, rad)
        if seen_nest is not None and key <= seen_nest:
            return False
        seen_nest = key
    seen_pair: tuple[int, int, int, int] | None = None
    for coeff, left_c, left_r, right_c, right_r in form.pairs:
        if coeff.num == 0 or not _canonical_ratio(coeff):
            return False
        if left_c == 0 or right_c == 0 or left_r <= 1 or right_r <= left_r:
            return False
        if _square_part(left_r) != (1, left_r) or _square_part(right_r) != (1, right_r):
            return False
        content = _gcd(abs(left_c), abs(right_c))
        if _square_part(content)[0] != 1:
            return False
        if left_c * left_c * left_r == right_c * right_c * right_r:
            return False
        if not _pair_inside_positive(left_c, left_r, right_c, right_r):
            return False
        if _denest_two_radicals(_pair_inside(left_c, left_r, right_c, right_r)) is not None:
            return False
        key = (left_r, right_r, left_c, right_c)
        if seen_pair is not None and key <= seen_pair:
            return False
        seen_pair = key
    seen_deep: tuple[int, int, int, int] | None = None
    for coeff, mult, constant, sqrt_coeff, rad in form.deeps:
        if coeff.num == 0 or not _canonical_ratio(coeff):
            return False
        if mult < 1 or _square_part(mult) != (1, mult):
            return False
        if constant == 0 or sqrt_coeff == 0 or rad <= 1 or _square_part(rad) != (1, rad):
            return False
        content = _gcd(abs(constant), abs(sqrt_coeff))
        if _square_part(content)[0] != 1:
            return False
        if not _binomial_positive(constant, sqrt_coeff, rad):
            return False
        if _denest(RealForm(_ratio(constant, 1), ((_ratio(sqrt_coeff, 1), rad),))) is not None:
            return False
        key = (rad, constant, sqrt_coeff, mult)
        if seen_deep is not None and key <= seen_deep:
            return False
        seen_deep = key
    seen_high: tuple[int, int, int, int, int] | None = None
    for coeff, mult, left_c, left_r, right_c, right_r in form.highs:
        if coeff.num == 0 or not _canonical_ratio(coeff):
            return False
        if mult < 1 or _square_part(mult) != (1, mult):
            return False
        if left_c == 0 or right_c == 0 or left_r <= 1 or right_r <= left_r:
            return False
        if _square_part(left_r) != (1, left_r) or _square_part(right_r) != (1, right_r):
            return False
        content = _gcd(abs(left_c), abs(right_c))
        if _square_part(content)[0] != 1:
            return False
        if left_c * left_c * left_r == right_c * right_c * right_r:
            return False
        if not _pair_inside_positive(left_c, left_r, right_c, right_r):
            return False
        if _denest_two_radicals(_pair_inside(left_c, left_r, right_c, right_r)) is not None:
            return False
        key = (left_r, right_r, left_c, right_c, mult)
        if seen_high is not None and key <= seen_high:
            return False
        seen_high = key
    seen_peak: tuple[int, int, int, int, int, int] | None = None
    for coeff, pmult, hmult, left_c, left_r, right_c, right_r in form.peaks:
        if coeff.num == 0 or not _canonical_ratio(coeff):
            return False
        if pmult < 1 or _square_part(pmult) != (1, pmult):
            return False
        if hmult < 1 or _square_part(hmult) != (1, hmult):
            return False
        if left_c == 0 or right_c == 0 or left_r <= 1 or right_r <= left_r:
            return False
        if _square_part(left_r) != (1, left_r) or _square_part(right_r) != (1, right_r):
            return False
        content = _gcd(abs(left_c), abs(right_c))
        if _square_part(content)[0] != 1:
            return False
        if left_c * left_c * left_r == right_c * right_c * right_r:
            return False
        if not _pair_inside_positive(left_c, left_r, right_c, right_r):
            return False
        if _denest_two_radicals(_pair_inside(left_c, left_r, right_c, right_r)) is not None:
            return False
        key = (left_r, right_r, left_c, right_c, hmult, pmult)
        if seen_peak is not None and key <= seen_peak:
            return False
        seen_peak = key
    seen_crest: tuple[int, int, int, int, int, int, int] | None = None
    for coeff, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.crests:
        if coeff.num == 0 or not _canonical_ratio(coeff):
            return False
        if qmult < 1 or _square_part(qmult) != (1, qmult):
            return False
        if pmult < 1 or _square_part(pmult) != (1, pmult):
            return False
        if hmult < 1 or _square_part(hmult) != (1, hmult):
            return False
        if left_c == 0 or right_c == 0 or left_r <= 1 or right_r <= left_r:
            return False
        if _square_part(left_r) != (1, left_r) or _square_part(right_r) != (1, right_r):
            return False
        content = _gcd(abs(left_c), abs(right_c))
        if _square_part(content)[0] != 1:
            return False
        if left_c * left_c * left_r == right_c * right_c * right_r:
            return False
        if not _pair_inside_positive(left_c, left_r, right_c, right_r):
            return False
        if _denest_two_radicals(_pair_inside(left_c, left_r, right_c, right_r)) is not None:
            return False
        key = (left_r, right_r, left_c, right_c, hmult, pmult, qmult)
        if seen_crest is not None and key <= seen_crest:
            return False
        seen_crest = key
    seen_summit: tuple[int, int, int, int, int, int, int, int] | None = None
    for coeff, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.summits:
        if coeff.num == 0 or not _canonical_ratio(coeff):
            return False
        if smult < 1 or _square_part(smult) != (1, smult):
            return False
        if qmult < 1 or _square_part(qmult) != (1, qmult):
            return False
        if pmult < 1 or _square_part(pmult) != (1, pmult):
            return False
        if hmult < 1 or _square_part(hmult) != (1, hmult):
            return False
        if left_c == 0 or right_c == 0 or left_r <= 1 or right_r <= left_r:
            return False
        if _square_part(left_r) != (1, left_r) or _square_part(right_r) != (1, right_r):
            return False
        content = _gcd(abs(left_c), abs(right_c))
        if _square_part(content)[0] != 1:
            return False
        if left_c * left_c * left_r == right_c * right_c * right_r:
            return False
        if not _pair_inside_positive(left_c, left_r, right_c, right_r):
            return False
        if _denest_two_radicals(_pair_inside(left_c, left_r, right_c, right_r)) is not None:
            return False
        key = (left_r, right_r, left_c, right_c, hmult, pmult, qmult, smult)
        if seen_summit is not None and key <= seen_summit:
            return False
        seen_summit = key

    seen_apex: tuple[int, int, int, int, int, int, int, int, int] | None = None
    for (
        coeff,
        amult,
        smult,
        qmult,
        pmult,
        hmult,
        left_c,
        left_r,
        right_c,
        right_r,
    ) in form.apexes:
        if coeff.num == 0 or not _canonical_ratio(coeff):
            return False
        if amult < 1 or _square_part(amult) != (1, amult):
            return False
        if smult < 1 or _square_part(smult) != (1, smult):
            return False
        if qmult < 1 or _square_part(qmult) != (1, qmult):
            return False
        if pmult < 1 or _square_part(pmult) != (1, pmult):
            return False
        if hmult < 1 or _square_part(hmult) != (1, hmult):
            return False
        if left_c == 0 or right_c == 0 or left_r <= 1 or right_r <= left_r:
            return False
        if _square_part(left_r) != (1, left_r) or _square_part(right_r) != (1, right_r):
            return False
        content = _gcd(abs(left_c), abs(right_c))
        if _square_part(content)[0] != 1:
            return False
        if left_c * left_c * left_r == right_c * right_c * right_r:
            return False
        if not _pair_inside_positive(left_c, left_r, right_c, right_r):
            return False
        if _denest_two_radicals(_pair_inside(left_c, left_r, right_c, right_r)) is not None:
            return False
        key = (left_r, right_r, left_c, right_c, hmult, pmult, qmult, smult, amult)
        if seen_apex is not None and key <= seen_apex:
            return False

        seen_apex = key
    seen_shell: tuple[int, int, int, int, int, int, int, int, int, tuple[int, ...]] | None = None
    for (
        coeff,
        extra,
        amult,
        smult,
        qmult,
        pmult,
        hmult,
        left_c,
        left_r,
        right_c,
        right_r,
    ) in form.shells:
        if coeff.num == 0 or not _canonical_ratio(coeff):
            return False
        if not extra:
            return False
        for mult in extra:
            if mult < 1 or _square_part(mult) != (1, mult):
                return False
        if amult < 1 or _square_part(amult) != (1, amult):
            return False
        if smult < 1 or _square_part(smult) != (1, smult):
            return False
        if qmult < 1 or _square_part(qmult) != (1, qmult):
            return False
        if pmult < 1 or _square_part(pmult) != (1, pmult):
            return False
        if hmult < 1 or _square_part(hmult) != (1, hmult):
            return False
        if left_c == 0 or right_c == 0 or left_r <= 1 or right_r <= left_r:
            return False
        if _square_part(left_r) != (1, left_r) or _square_part(right_r) != (1, right_r):
            return False
        content = _gcd(abs(left_c), abs(right_c))
        if _square_part(content)[0] != 1:
            return False
        if left_c * left_c * left_r == right_c * right_c * right_r:
            return False
        if not _pair_inside_positive(left_c, left_r, right_c, right_r):
            return False
        if _denest_two_radicals(_pair_inside(left_c, left_r, right_c, right_r)) is not None:
            return False
        key = (left_r, right_r, left_c, right_c, hmult, pmult, qmult, smult, amult, extra)
        if seen_shell is not None and key <= seen_shell:
            return False
        seen_shell = key
    seen_fold: tuple[int, int, int, int, tuple[int, ...]] | None = None
    for coeff, extra, mult, constant, sqrt_coeff, rad in form.folds:
        if coeff.num == 0 or not _canonical_ratio(coeff):
            return False
        if not extra:
            return False
        for item in extra:
            if item < 1 or _square_part(item) != (1, item):
                return False
        if mult < 1 or _square_part(mult) != (1, mult):
            return False
        if constant == 0 or sqrt_coeff == 0 or rad <= 1 or _square_part(rad) != (1, rad):
            return False
        content = _gcd(abs(constant), abs(sqrt_coeff))
        if _square_part(content)[0] != 1:
            return False
        if not _binomial_positive(constant, sqrt_coeff, rad):
            return False
        if _denest(RealForm(_ratio(constant, 1), ((_ratio(sqrt_coeff, 1), rad),))) is not None:
            return False
        key = (rad, constant, sqrt_coeff, mult, extra)
        if seen_fold is not None and key <= seen_fold:
            return False
        seen_fold = key
    seen_quad: tuple[int, int, int, int, int, int, int, int, int, int] | None = None
    for coeff, constant, first_coeff, first, second_coeff, second, product_coeff in form.quads:
        if coeff.num == 0 or not _canonical_ratio(coeff):
            return False
        if first >= second or first <= 1 or second <= 1:
            return False
        if _square_part(first) != (1, first) or _square_part(second) != (1, second):
            return False
        if not (
            _canonical_ratio(constant)
            and _canonical_ratio(first_coeff)
            and _canonical_ratio(second_coeff)
            and _canonical_ratio(product_coeff)
        ):
            return False
        if first_coeff.num == 0 and second_coeff.num == 0 and product_coeff.num == 0:
            return False
        inside = _quad_inside(constant, first_coeff, first, second_coeff, second, product_coeff)
        if _classify(inside) not in {"gt", "eq"}:
            return False
        if _try_denest_biquadratic(constant, first_coeff, first, second_coeff, second, product_coeff) is not None:
            return False
        if not _biquadratic_not_a_field_square(
            constant, first_coeff, first, second_coeff, second, product_coeff
        ):
            return False
        key = (
            first,
            second,
            constant.num,
            constant.den,
            first_coeff.num,
            first_coeff.den,
            second_coeff.num,
            second_coeff.den,
            product_coeff.num,
            product_coeff.den,
        )
        if seen_quad is not None and key <= seen_quad:
            return False
        seen_quad = key
    if form.algebras:
        if (
            form.constant.num != 0
            or form.terms
            or form.towers
            or form.nests
            or form.pairs
            or form.deeps
            or form.highs
            or form.peaks
            or form.crests
            or form.summits
            or form.apexes
            or form.shells
            or form.folds
            or form.quads
        ):
            return False
        if len(form.algebras) != 1:
            return False
        coeff, coeffs, index = form.algebras[0]
        if coeff.num == 0 or not _canonical_ratio(coeff):
            return False
        try:
            from pgi.math.algebraic import AlgebraicReal

            AlgebraicReal(coeffs, index)
        except (KernelError, NotExact, TypeError, ValueError):
            return False
    return True


def _canonical_ratio(value: Ratio) -> bool:
    return value.den > 0 and _gcd(abs(value.num), value.den) == 1


def _miller_rabin(number: int) -> bool:
    if number < 2:
        return False
    small = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31)
    for prime in small:
        if number == prime:
            return True
        if number % prime == 0:
            return False
    reduced = number - 1
    twos = 0
    while reduced % 2 == 0:
        reduced //= 2
        twos += 1
    witnesses = small
    if number.bit_length() > 64:
        witnesses = small + (37, 41, 43, 47, 53, 59, 61, 67, 71, 73)
    for witness in witnesses:
        power = pow(witness, reduced, number)
        if power == 1 or power == number - 1:
            continue
        for _ in range(twos - 1):
            power = (power * power) % number
            if power == number - 1:
                break
        else:
            return False
    return True


def _pollard_rho(number: int) -> int:
    if number % 2 == 0:
        return 2
    seed = 2
    while seed < 64:
        y = seed
        cycle = 2
        factor = 1
        while factor == 1:
            x = y
            for _ in range(cycle):
                y = (y * y + seed) % number
                factor = _gcd(abs(x - y), number)
                if factor > 1:
                    break
            cycle *= 2
        if factor != number:
            return factor
        seed += 1
    raise KernelError("square part factorization stalled")


def _factor_int(number: int) -> dict[int, int]:
    factors: dict[int, int] = {}
    stack = [number]
    while stack:
        current = stack.pop()
        if current == 1:
            continue
        square = isqrt(current)
        if square * square == current and current > 1:
            inner = _factor_int(square)
            for prime, count in inner.items():
                factors[prime] = factors.get(prime, 0) + 2 * count
            continue
        if _miller_rabin(current):
            factors[current] = factors.get(current, 0) + 1
            continue
        trial = 2
        bound = 100000
        rest = current
        split = False
        while trial <= bound and trial * trial <= rest:
            if rest % trial == 0:
                count = 0
                while rest % trial == 0:
                    rest //= trial
                    count += 1
                factors[trial] = factors.get(trial, 0) + count
                if rest == 1:
                    split = True
                    break
                stack.append(rest)
                split = True
                break
            trial = 3 if trial == 2 else trial + 2
        if split:
            continue
        if rest != current:
            stack.append(rest)
            continue
        factor = _pollard_rho(current)
        stack.append(factor)
        stack.append(current // factor)
    return factors


def _square_part(number: int) -> tuple[int, int]:
    if number < 1:
        raise KernelError("square part needs a positive integer")
    root = 1
    free = 1
    rest = number
    prime = 2
    while prime * prime <= rest and prime <= 1000:
        exponent = 0
        while rest % prime == 0:
            rest //= prime
            exponent += 1
        if exponent:
            root *= prime ** (exponent // 2)
            if exponent % 2 == 1:
                free *= prime
        prime = 3 if prime == 2 else prime + 2
    if rest > 1:
        square = isqrt(rest)
        if square * square == rest:
            root *= square
        elif _miller_rabin(rest):
            free *= rest
        else:
            for prime, exponent in _factor_int(rest).items():
                root *= prime ** (exponent // 2)
                if exponent % 2 == 1:
                    free *= prime
    if root * root * free != number:
        raise KernelError("square part disagreed")
    if free > 1 and _has_square_factor(free):
        raise KernelError("square-free part has a square factor")
    return root, free


def _has_square_factor(number: int) -> bool:
    rest = number
    prime = 2
    while prime * prime <= rest and prime <= 1000:
        if rest % (prime * prime) == 0:
            return True
        while rest % prime == 0:
            rest //= prime
        prime = 3 if prime == 2 else prime + 2
    if rest <= 1:
        return False
    square = isqrt(rest)
    if square * square == rest:
        return True
    if _miller_rabin(rest):
        return False
    for _, exponent in _factor_int(rest).items():
        if exponent >= 2:
            return True
    return False


def _gcd(left: int, right: int) -> int:
    while right:
        left, right = right, left % right
    return abs(left)


def _ratio(numerator: int, denominator: int) -> Ratio:
    return rat_normalize(numerator, denominator).value


def _lift(value: Ratio):
    return rat_normalize(value.num, value.den)


def _qadd(left: Ratio, right: Ratio) -> Ratio:
    return rat_add(_lift(left), _lift(right)).value


def _qsub(left: Ratio, right: Ratio) -> Ratio:
    return rat_sub(_lift(left), _lift(right)).value


def _qmul(left: Ratio, right: Ratio) -> Ratio:
    return rat_mul(_lift(left), _lift(right)).value


def _qdiv(left: Ratio, right: Ratio) -> Ratio:
    return rat_div(_lift(left), _lift(right)).value


def _qneg(value: Ratio) -> Ratio:
    return rat_neg(_lift(value)).value


def _inverse(value: Ratio) -> Ratio:
    return _qdiv(_ratio(1, 1), value)


def _qcmp(left: Ratio, right: Ratio) -> int:
    difference = _qsub(left, right).num
    return (difference > 0) - (difference < 0)


def _factor_square_free(number: int) -> tuple[int, ...]:
    if number < 2:
        return ()
    primes: list[int] = []
    rest = number
    prime = 2
    while prime * prime <= rest:
        if rest % prime == 0:
            primes.append(prime)
            rest //= prime
            if rest % prime == 0:
                return ()
        prime = 3 if prime == 2 else prime + 2
    if rest > 1:
        primes.append(rest)
    return tuple(primes)


def _is_monic_single_radical(form: RealForm) -> bool:
    if form.constant.num != 0 or form.terms or form.towers:
        return False
    count = 0
    for items in (
        form.nests,
        form.pairs,
        form.deeps,
        form.highs,
        form.peaks,
        form.crests,
        form.summits,
        form.apexes,
        form.shells,
        form.folds,
        form.quads,
    ):
        if items:
            count += len(items)
    return count == 1


def _iter_atoms(form: RealForm) -> list[tuple[Ratio, RealForm]]:
    atoms: list[tuple[Ratio, RealForm]] = []
    if form.constant.num != 0:
        atoms.append((form.constant, RealForm(_ratio(1, 1), ())))
    for coeff, rad in form.terms:
        atoms.append((coeff, _term_form(_ratio(1, 1), rad)))
    for coeff, base, numer, log_den in form.towers:
        atoms.append(
            (coeff, RealForm(_ratio(0, 1), (), ((_ratio(1, 1), base, numer, log_den),)))
        )
    for coeff, constant, sqrt_coeff, rad in form.nests:
        atoms.append((coeff, _nest_form(_ratio(1, 1), constant, sqrt_coeff, rad)))
    for coeff, left_c, left_r, right_c, right_r in form.pairs:
        atoms.append((coeff, _pair_form(_ratio(1, 1), left_c, left_r, right_c, right_r)))
    for coeff, mult, constant, sqrt_coeff, rad in form.deeps:
        atoms.append((coeff, _deep_form(_ratio(1, 1), mult, constant, sqrt_coeff, rad)))
    for coeff, mult, left_c, left_r, right_c, right_r in form.highs:
        atoms.append((coeff, _high_form(_ratio(1, 1), mult, left_c, left_r, right_c, right_r)))
    for coeff, pmult, hmult, left_c, left_r, right_c, right_r in form.peaks:
        atoms.append(
            (coeff, _peak_form(_ratio(1, 1), pmult, hmult, left_c, left_r, right_c, right_r))
        )
    for coeff, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.crests:
        atoms.append(
            (
                coeff,
                _crest_form(_ratio(1, 1), qmult, pmult, hmult, left_c, left_r, right_c, right_r),
            )
        )
    for coeff, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.summits:
        atoms.append(
            (
                coeff,
                _summit_form(
                    _ratio(1, 1), smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r
                ),
            )
        )
    for coeff, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.apexes:
        atoms.append(
            (
                coeff,
                _apex_form(
                    _ratio(1, 1),
                    amult,
                    smult,
                    qmult,
                    pmult,
                    hmult,
                    left_c,
                    left_r,
                    right_c,
                    right_r,
                ),
            )
        )
    for coeff, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r in form.shells:
        atoms.append(
            (
                coeff,
                _shell_form(
                    _ratio(1, 1),
                    extra,
                    amult,
                    smult,
                    qmult,
                    pmult,
                    hmult,
                    left_c,
                    left_r,
                    right_c,
                    right_r,
                ),
            )
        )
    for coeff, extra, mult, constant, sqrt_coeff, rad in form.folds:
        atoms.append(
            (coeff, _fold_form(_ratio(1, 1), extra, mult, constant, sqrt_coeff, rad))
        )
    for coeff, constant, first_coeff, first, second_coeff, second, product_coeff in form.quads:
        atoms.append(
            (
                coeff,
                _quad_form(
                    _ratio(1, 1), constant, first_coeff, first, second_coeff, second, product_coeff
                ),
            )
        )
    return atoms


def _only_family(form: RealForm, name: str) -> bool:
    if form.constant.num != 0 or form.terms or form.towers:
        return False
    families = {
        "nests": form.nests,
        "pairs": form.pairs,
        "deeps": form.deeps,
        "highs": form.highs,
        "peaks": form.peaks,
        "crests": form.crests,
        "summits": form.summits,
        "apexes": form.apexes,
        "shells": form.shells,
        "folds": form.folds,
        "quads": form.quads,
    }
    return all(
        (bool(items) and name == key) or (not items and name != key)
        for key, items in families.items()
    )


def _stack_unit(layers: tuple[tuple[Ratio, ...], ...], count: int) -> sqrt_tower.SqrtTower:
    stacked = list(layers)
    for _ in range(count):
        stacked.append(sqrt_tower.unit_last(len(stacked)))
    return sqrt_tower.SqrtTower(tuple(stacked))


def _nest_layers(constant: Ratio, sqrt_coeff: Ratio, rad: int) -> tuple[tuple[Ratio, ...], ...]:
    return ((_ratio(rad, 1),), (constant, sqrt_coeff))


def _pair_layers(
    left_c: int, left_r: int, right_c: int, right_r: int
) -> tuple[tuple[Ratio, ...], ...]:
    return (
        (_ratio(left_r, 1),),
        (_ratio(right_r, 1), _ratio(0, 1)),
        (_ratio(0, 1), _ratio(left_c, 1), _ratio(right_c, 1), _ratio(0, 1)),
    )


def _towers_from_monic(monic: RealForm) -> list[sqrt_tower.SqrtTower]:
    towers: list[sqrt_tower.SqrtTower] = []
    if (
        monic.terms
        and monic.constant.num == 0
        and len(monic.terms) == 1
        and not monic.towers
        and not monic.nests
        and not monic.pairs
        and not monic.deeps
        and not monic.highs
        and not monic.peaks
        and not monic.crests
        and not monic.summits
        and not monic.apexes
        and not monic.shells
        and not monic.folds
        and not monic.quads
    ):
        rad = monic.terms[0][1]
        towers.append(sqrt_tower.integer_tower((rad,)))
        factors = _factor_square_free(rad)
        if len(factors) > 1:
            towers.append(sqrt_tower.integer_tower(factors))
        return towers
    if monic.nests and len(monic.nests) == 1 and _only_family(monic, "nests"):
        _, constant, sqrt_coeff, rad = monic.nests[0]
        towers.append(sqrt_tower.SqrtTower(_nest_layers(constant, sqrt_coeff, rad)))
        return towers
    if monic.pairs and len(monic.pairs) == 1 and _only_family(monic, "pairs"):
        _, left_c, left_r, right_c, right_r = monic.pairs[0]
        towers.append(sqrt_tower.SqrtTower(_pair_layers(left_c, left_r, right_c, right_r)))
        if (left_c, right_c) != (1, 1):
            towers.append(sqrt_tower.SqrtTower(_pair_layers(1, left_r, 1, right_r)))
        return towers
    if monic.deeps and len(monic.deeps) == 1 and _only_family(monic, "deeps"):
        _, mult, constant, sqrt_coeff, rad = monic.deeps[0]
        nest = _nest_layers(_ratio(constant, 1), _ratio(sqrt_coeff, 1), rad)
        towers.append(_stack_unit(nest, 1))
        return towers
    if monic.highs and len(monic.highs) == 1 and _only_family(monic, "highs"):
        _, mult, left_c, left_r, right_c, right_r = monic.highs[0]
        towers.append(_stack_unit(_pair_layers(left_c, left_r, right_c, right_r), 1))
        if (left_c, right_c) != (1, 1):
            towers.append(_stack_unit(_pair_layers(1, left_r, 1, right_r), 1))
        return towers
    if monic.peaks and len(monic.peaks) == 1 and _only_family(monic, "peaks"):
        _, pmult, hmult, left_c, left_r, right_c, right_r = monic.peaks[0]
        towers.append(_stack_unit(_pair_layers(left_c, left_r, right_c, right_r), 2))
        if (left_c, right_c) != (1, 1):
            towers.append(_stack_unit(_pair_layers(1, left_r, 1, right_r), 2))
        return towers
    if monic.crests and len(monic.crests) == 1 and _only_family(monic, "crests"):
        _, qmult, pmult, hmult, left_c, left_r, right_c, right_r = monic.crests[0]
        towers.append(_stack_unit(_pair_layers(left_c, left_r, right_c, right_r), 3))
        if (left_c, right_c) != (1, 1):
            towers.append(_stack_unit(_pair_layers(1, left_r, 1, right_r), 3))
        return towers
    if monic.summits and len(monic.summits) == 1 and _only_family(monic, "summits"):
        _, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r = monic.summits[0]
        towers.append(_stack_unit(_pair_layers(left_c, left_r, right_c, right_r), 4))
        if (left_c, right_c) != (1, 1):
            towers.append(_stack_unit(_pair_layers(1, left_r, 1, right_r), 4))
        return towers
    if monic.apexes and len(monic.apexes) == 1 and _only_family(monic, "apexes"):
        _, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r = monic.apexes[0]
        towers.append(_stack_unit(_pair_layers(left_c, left_r, right_c, right_r), 5))
        if (left_c, right_c) != (1, 1):
            towers.append(_stack_unit(_pair_layers(1, left_r, 1, right_r), 5))
        return towers
    if monic.shells and len(monic.shells) == 1 and _only_family(monic, "shells"):
        _, extra, amult, smult, qmult, pmult, hmult, left_c, left_r, right_c, right_r = monic.shells[0]
        towers.append(_stack_unit(_pair_layers(left_c, left_r, right_c, right_r), 5 + len(extra)))
        if (left_c, right_c) != (1, 1):
            towers.append(_stack_unit(_pair_layers(1, left_r, 1, right_r), 5 + len(extra)))
        return towers
    if monic.folds and len(monic.folds) == 1 and _only_family(monic, "folds"):
        _, extra, mult, constant, sqrt_coeff, rad = monic.folds[0]
        nest = _nest_layers(_ratio(constant, 1), _ratio(sqrt_coeff, 1), rad)
        towers.append(_stack_unit(nest, 1 + len(extra)))
        return towers
    if monic.quads and len(monic.quads) == 1 and _only_family(monic, "quads"):
        _, constant, first_coeff, first, second_coeff, second, product_coeff = monic.quads[0]
        layers = (
            (_ratio(first, 1),),
            (_ratio(second, 1), _ratio(0, 1)),
            (constant, first_coeff, second_coeff, product_coeff),
        )
        towers.append(sqrt_tower.SqrtTower(layers))
        return towers
    return towers


def _collected_primes(*forms: RealForm) -> tuple[int, ...]:
    primes: set[int] = set()
    for form in forms:
        for _, rad in form.terms:
            factors = _factor_square_free(rad)
            if factors:
                primes.update(factors)
            else:
                primes.add(rad)
        for _, monic in _iter_atoms(form):
            for tower in _towers_from_monic(monic):
                for radicand in tower.layers[: tower.integer_prefix]:
                    value = radicand[0]
                    if value.den == 1 and value.num > 1:
                        factors = _factor_square_free(value.num)
                        if factors:
                            primes.update(factors)
                        else:
                            primes.add(value.num)
    return tuple(sorted(primes))


def _candidate_towers(*forms: RealForm) -> list[sqrt_tower.SqrtTower]:
    for form in forms:
        if form.towers:
            return []
    seen: dict[tuple[tuple[Ratio, ...], ...], sqrt_tower.SqrtTower] = {}
    for form in forms:
        for _, monic in _iter_atoms(form):
            for tower in _towers_from_monic(monic):
                seen[tower.layers] = tower
    primes = _collected_primes(*forms)
    if primes:
        integer = sqrt_tower.integer_tower(primes)
        seen[integer.layers] = integer
    candidates = list(seen.values())
    candidates.sort(
        key=lambda tower: (
            -tower.degree,
            tower.complexity,
            tuple(tuple((value.num, value.den) for value in layer) for layer in tower.layers),
        )
    )
    return candidates


_BASIS_FORMS: dict[tuple[tuple[tuple[Ratio, ...], ...], int], RealForm] = {}
_BASIS_INDEX: dict[tuple[tuple[Ratio, ...], ...], dict[RealForm, int]] = {}
_GEN_FORMS: dict[tuple[tuple[tuple[Ratio, ...], ...], int], RealForm] = {}
_GEN_POWER: dict[
    tuple[tuple[tuple[Ratio, ...], ...], int, int, int], sqrt_tower.TowerElem
] = {}


def _generator_form(tower: sqrt_tower.SqrtTower, index: int) -> RealForm:
    key = (tower.layers, index)
    cached = _GEN_FORMS.get(key)
    if cached is not None:
        return cached
    prefix = sqrt_tower.SqrtTower(tower.layers[:index])
    radicand = sqrt_tower.TowerElem(prefix, tower.layers[index])
    form = _sqrt_of_form(_write_elem(radicand))
    _GEN_FORMS[key] = form
    _BASIS_FORMS[(tower.layers, 1 << index)] = form
    return form


def _generator_power(
    tower: sqrt_tower.SqrtTower, index: int, steps: int, prefix: sqrt_tower.SqrtTower
) -> sqrt_tower.TowerElem:
    key = (tower.layers, index, steps, prefix.degree)
    cached = _GEN_POWER.get(key)
    if cached is not None:
        return cached
    short = sqrt_tower.SqrtTower(tower.layers[: index + 1])
    elem = sqrt_tower.TowerElem(short, sqrt_tower.mask_coords(short, 1 << index))
    for _ in range(steps):
        elem = sqrt_tower.mul(elem, elem)
        while (
            len(elem.tower.layers) > len(prefix.layers)
            and all(value.num == 0 for value in elem.coords[elem.tower.degree // 2 :])
        ):
            smaller = sqrt_tower.SqrtTower(elem.tower.layers[:-1])
            elem = sqrt_tower.TowerElem(smaller, elem.coords[: smaller.degree])
    if len(elem.tower.layers) <= len(prefix.layers):
        result = sqrt_tower.lift(elem, prefix)
    else:
        if any(value.num != 0 for value in elem.coords[prefix.degree :]):
            raise NotExact("this quotient stays outside")
        result = sqrt_tower.TowerElem(prefix, elem.coords[: prefix.degree])
    _GEN_POWER[key] = result
    return result


def _basis_form(tower: sqrt_tower.SqrtTower, mask: int) -> RealForm:
    key = (tower.layers, mask)
    cached = _BASIS_FORMS.get(key)
    if cached is not None:
        return cached
    if mask == 0:
        form = RealForm(_ratio(1, 1), ())
        _BASIS_FORMS[key] = form
        return form
    highest = mask.bit_length() - 1
    lower = mask ^ (1 << highest)
    if lower == 0:
        form = _generator_form(tower, highest)
        _BASIS_FORMS[key] = form
        return form
    lower_form = _basis_form(tower, lower)
    generator = _generator_form(tower, highest)
    try:
        form = _mul_forms_parts(lower_form, generator)
        _BASIS_FORMS[key] = form
        return form
    except NotExact:
        pass
    prefix_len = tower.integer_prefix
    if highest < prefix_len:
        raise NotExact("this quotient stays outside")
    steps = highest - prefix_len + 1
    prefix = sqrt_tower.SqrtTower(tower.layers[:prefix_len])
    image = sqrt_tower.one(prefix)
    bit = 0
    rest = mask
    while rest:
        if rest & 1:
            image = sqrt_tower.mul(image, _generator_power(tower, bit, steps, prefix))
        rest >>= 1
        bit += 1
    form = _write_elem(image)
    for _ in range(steps):
        form = _sqrt_of_form(form)
    _BASIS_FORMS[key] = form
    return form


def _remember_basis(tower: sqrt_tower.SqrtTower, mask: int, form: RealForm) -> None:
    index = _BASIS_INDEX.setdefault(tower.layers, {})
    index[form] = mask
    _BASIS_FORMS[(tower.layers, mask)] = form


def _lookup_monic(tower: sqrt_tower.SqrtTower, monic: RealForm) -> int | None:
    index = _BASIS_INDEX.setdefault(tower.layers, {})
    found = index.get(monic)
    if found is not None:
        return found
    unit = RealForm(_ratio(1, 1), ())
    if monic == unit:
        _remember_basis(tower, 0, unit)
        return 0
    for layer in range(len(tower.layers)):
        form = _generator_form(tower, layer)
        _remember_basis(tower, 1 << layer, form)
        if form == monic:
            return 1 << layer
    for (layers, mask), form in list(_BASIS_FORMS.items()):
        if layers == tower.layers:
            index[form] = mask
            if form == monic:
                return mask
    prefix_len = tower.integer_prefix
    for mask in range(1, 1 << prefix_len):
        try:
            form = _basis_form(tower, mask)
        except NotExact:
            continue
        _remember_basis(tower, mask, form)
        if form == monic:
            return mask
    return None


def _write_elem(elem: sqrt_tower.TowerElem) -> RealForm:
    result = RealForm(_ratio(0, 1), ())
    for mask, coeff in enumerate(elem.coords):
        if coeff.num == 0:
            continue
        piece = _basis_form(elem.tower, mask)
        _remember_basis(elem.tower, mask, piece)
        result = _add_forms(result, _scale(piece, coeff))
    return result


def _read_form(form: RealForm, tower: sqrt_tower.SqrtTower) -> sqrt_tower.TowerElem | None:
    coords = [_ratio(0, 1)] * tower.degree
    for coeff, monic in _iter_atoms(form):
        if monic == RealForm(_ratio(1, 1), ()):
            coords[0] = _qadd(coords[0], coeff)
            continue
        mask = _lookup_monic(tower, monic)
        if mask is None:
            return None
        coords[mask] = _qadd(coords[mask], coeff)
    return sqrt_tower.TowerElem(tower, tuple(coords))


def _embed_forms(forms: tuple[RealForm, ...]) -> list[sqrt_tower.TowerElem] | None:
    for tower in _candidate_towers(*forms):
        try:
            elems: list[sqrt_tower.TowerElem] = []
            ok = True
            for form in forms:
                elem = _read_form(form, tower)
                if elem is None:
                    ok = False
                    break
                elems.append(elem)
            if ok:
                return elems
        except NotExact:
            continue
    return None


def _mul_forms_tower(left: RealForm, right: RealForm) -> RealForm | None:
    if _is_rational(left):
        return _scale(right, left.constant)
    if _is_rational(right):
        return _scale(left, right.constant)
    packed = _embed_forms((left, right))
    if packed is None:
        return None
    return _write_elem(sqrt_tower.mul(packed[0], packed[1]))


def _inverse_form_tower(form: RealForm) -> RealForm | None:
    if _is_monic_single_radical(form):
        return None
    packed = _embed_forms((form,))
    if packed is None:
        return None
    try:
        return _write_elem(sqrt_tower.inv(packed[0]))
    except NotExact:
        return None


def _div_forms_tower(left: RealForm, right: RealForm) -> RealForm | None:
    if _is_monic_single_radical(right):
        return None
    packed = _embed_forms((left, right))
    if packed is None:
        return None
    try:
        inverse = sqrt_tower.inv(packed[1])
    except NotExact:
        return None
    return _write_elem(sqrt_tower.mul(packed[0], inverse))
