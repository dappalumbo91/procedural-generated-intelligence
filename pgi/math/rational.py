"""Exact rationals as reduced fractions.

Lean 4.36.0 evaluates these with no imports. `Rat.normalize 8 6` is `4/3`.
`(1 : Rat) / 2 + (1 : Rat) / 3` is `5/6`. `(1 : Rat) / 0` evaluates to `0`,
and `Rat.normalize` refuses a zero denominator. Isabelle2025-2 `Rat.thy`
defines `Fract`, proves `eq_rat`, `add_rat`, `mult_rat`, `minus_rat`,
`diff_rat`, and `divide_rat`, and also sets `Fract a 0 = Fract 0 1`.

This kernel does not adopt either system's division by zero. A zero
denominator stays open.

A value is a pair `num/den` with `den > 0` and `gcd(|num|, den) = 1`, the
normal form in Lean's `Rat.normalize` and in Isabelle's `Rat_cases`.
Closed arithmetic uses those field operations and then normalizes. Two
fractions are equal exactly when `eq_rat` says so: `a * d = c * b`.
Comparison of positive-denominator fractions uses Isabelle `le_rat`. The
products are checked with the integer kernel.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import gcd

from pgi.math.kernel import KernelError, NotExact, numeral_mul
from pgi.math.order import numeral_le, numeral_not_le, order_trace
from pgi.math.syntax import App, IntLit, Term, pretty
from pgi.model import Rule


@dataclass(frozen=True)
class Ratio:
    num: int
    den: int


@dataclass(frozen=True)
class RatTheorem:
    value: Ratio
    rule: str
    premises: tuple[RatTheorem, ...] = ()
    raw: tuple[int, int] | None = None
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _justified(self):
            shown = f"{self.value.num}/{self.value.den}"
            raise KernelError(f"{self.rule} does not justify {shown}")


def rat_normalize(num: int, den: int) -> RatTheorem:
    if den == 0:
        raise NotExact(f"{num} / {den} is division by zero")
    value = _reduced(num, den)
    divisor = gcd(abs(num), abs(den))
    return RatTheorem(
        value,
        "Rat.normalize",
        raw=(num, den),
        detail=(
            f"gcd({abs(num)}, {abs(den)}) = {divisor}.",
            "The denominator is positive and the numerator carries the sign.",
            "Lean Rat.normalize. Isabelle Rat_cases: denominator positive and coprime.",
        ),
    )


def rat_of_int(value: int) -> RatTheorem:
    return rat_normalize(value, 1)


def rat_add(left: RatTheorem, right: RatTheorem) -> RatTheorem:
    raw_num = left.value.num * right.value.den + right.value.num * left.value.den
    raw_den = left.value.den * right.value.den
    return _from_raw(
        "Rat.add",
        (left, right),
        raw_num,
        raw_den,
        (
            "Isabelle add_rat: Fract a b + Fract c d = Fract (a*d + c*b) (b*d).",
            "Lean Rat.add, then Rat.normalize.",
        ),
    )


def rat_mul(left: RatTheorem, right: RatTheorem) -> RatTheorem:
    return _from_raw(
        "Rat.mul",
        (left, right),
        left.value.num * right.value.num,
        left.value.den * right.value.den,
        (
            "Isabelle mult_rat: Fract a b * Fract c d = Fract (a*c) (b*d).",
            "Lean Rat.mul, then Rat.normalize.",
        ),
    )


def rat_neg(premise: RatTheorem) -> RatTheorem:
    return _from_raw(
        "Rat.neg",
        (premise,),
        -premise.value.num,
        premise.value.den,
        (
            "Isabelle minus_rat: - Fract a b = Fract (-a) b.",
            "Lean Rat.neg.",
        ),
    )


def rat_sub(left: RatTheorem, right: RatTheorem) -> RatTheorem:
    raw_num = left.value.num * right.value.den - right.value.num * left.value.den
    raw_den = left.value.den * right.value.den
    return _from_raw(
        "Rat.sub",
        (left, right),
        raw_num,
        raw_den,
        (
            "Isabelle diff_rat_def: q - r = q + - r.",
            "Isabelle diff_rat: Fract a b - Fract c d = Fract (a*d - c*b) (b*d).",
            "Lean Rat.sub, then Rat.normalize.",
        ),
    )


def rat_div(left: RatTheorem, right: RatTheorem) -> RatTheorem:
    if right.value.num == 0:
        raise NotExact("division by zero")
    return _from_raw(
        "Rat.div",
        (left, right),
        left.value.num * right.value.den,
        left.value.den * right.value.num,
        (
            "Isabelle divide_rat: Fract a b div Fract c d = Fract (a*d) (b*c).",
            "Lean Rat.div, then Rat.normalize.",
            "A zero divisor is refused. Lean evaluates (1 : Rat) / 0 to 0, and Isabelle sets Fract a 0 = Fract 0 1. Neither convention is a rule here.",
        ),
    )


def rat_pow(base: RatTheorem, exponent: int) -> RatTheorem:
    if exponent > 32 or exponent < -32:
        raise NotExact("this power exceeds the exponent limit")
    if exponent == 0:
        if base.value.num == 0:
            raise NotExact("0^0 stays open")
        return rat_of_int(1)
    if exponent > 0:
        result = rat_of_int(1)
        for _ in range(exponent):
            result = rat_mul(result, base)
        return result
    if base.value.num == 0:
        raise NotExact("division by zero")
    inverse = rat_div(rat_of_int(1), base)
    result = rat_of_int(1)
    for _ in range(-exponent):
        result = rat_mul(result, inverse)
    return result


def eval_rat(term: Term) -> RatTheorem:
    if isinstance(term, IntLit):
        return rat_of_int(term.n)
    if not isinstance(term, App):
        raise KernelError("a free variable is not a rational numeral")
    if term.op == "pow" and len(term.args) == 2:
        base = eval_rat(term.args[0])
        exp = eval_rat(term.args[1])
        if exp.value.den != 1:
            raise NotExact("this exponent is not a closed integer")
        return rat_pow(base, exp.value.num)
    args = tuple(eval_rat(arg) for arg in term.args)
    if term.op == "add":
        return rat_add(args[0], args[1])
    if term.op == "sub":
        return rat_sub(args[0], args[1])
    if term.op == "mul":
        return rat_mul(args[0], args[1])
    if term.op == "neg":
        return rat_neg(args[0])
    if term.op == "div":
        return rat_div(args[0], args[1])
    raise KernelError(term.op)


def same_ratio(left: RatTheorem, right: RatTheorem) -> bool:
    """Isabelle eq_rat, checked by the integer product."""
    cross_left = _product(left.value.num, right.value.den)
    cross_right = _product(right.value.num, left.value.den)
    return cross_left == cross_right


def comparison_lines(left: Ratio, right: Ratio) -> tuple[bool, tuple[str, ...]]:
    """Isabelle le_rat on positive denominators.

    le_rat says Fract a b ≤ Fract c d exactly when
    (a*d)*(b*d) ≤ (c*b)*(b*d), for nonzero denominators. Both denominators
    here are positive, so b*d is positive and the test is the same as
    a*d ≤ c*b. The two integer comparisons have to agree.
    """
    if left.den <= 0 or right.den <= 0:
        raise KernelError("le_rat needs positive denominators")
    cross_left = _product(left.num, right.den)
    cross_right = _product(right.num, left.den)
    scale = _product(left.den, right.den)
    wide_left = _product(cross_left, scale)
    wide_right = _product(cross_right, scale)
    if scale <= 0 or (wide_left <= wide_right) != (cross_left <= cross_right):
        raise KernelError("le_rat scale disagreed with cross multiplication")
    holds = cross_left <= cross_right
    compared = numeral_le(cross_left, cross_right) if holds else numeral_not_le(cross_left, cross_right)
    lines = (
        f"le_rat: {left.num}/{left.den} against {right.num}/{right.den}.",
        f"Cross multiplication: {left.num} * {right.den} = {cross_left}, {right.num} * {left.den} = {cross_right}.",
        f"Isabelle multiplies both sides by the positive scale {scale}.",
        *order_trace(compared),
    )
    return holds, lines


def rat_trace(theorem: RatTheorem) -> tuple[str, ...]:
    lines: list[str] = []
    for premise in theorem.premises:
        lines.extend(rat_trace(premise))
    shown = f"{theorem.value.num}/{theorem.value.den}"
    if theorem.raw is None:
        lines.append(f"{theorem.rule}: {shown}")
    else:
        lines.append(f"{theorem.rule}: {theorem.raw[0]}/{theorem.raw[1]} = {shown}")
    lines.extend(theorem.detail)
    return tuple(lines)


def ratio_rule(origin: Term, theorem: RatTheorem, prelude: tuple[str, ...] = ()) -> Rule:
    title_left = pretty(origin)
    lines = (*prelude, *rat_trace(theorem))
    if theorem.value.den == 1:
        number = theorem.value.num
        return Rule(
            id=f"math.value.{number}",
            layer="base",
            stage="quantity",
            title=f"{title_left} = {number}",
            produces=f"value({number})",
            detail_lines=(*lines, f"The denominator is 1, so the exact integer is {number}."),
        )
    return Rule(
        id=f"math.ratio.{theorem.value.num}.{theorem.value.den}",
        layer="base",
        stage="quantity",
        title=f"{title_left} = {theorem.value.num}/{theorem.value.den}",
        produces=f"ratio({theorem.value.num},{theorem.value.den})",
        detail_lines=lines,
    )


def equality_rules(left: Term, right: Term, left_rat: RatTheorem, right_rat: RatTheorem, prelude: tuple[str, ...] = ()) -> tuple[Rule, ...]:
    title = f"{pretty(left)} = {pretty(right)}"
    lines = (
        *prelude,
        *rat_trace(left_rat),
        *rat_trace(right_rat),
        f"eq_rat: {left_rat.value.num} * {right_rat.value.den} against {right_rat.value.num} * {left_rat.value.den}.",
        "Isabelle eq_rat: Fract a b = Fract c d exactly when a * d = c * b, for nonzero denominators.",
    )
    if same_ratio(left_rat, right_rat):
        return (
            Rule(
                id="math.ratio.eq",
                layer="base",
                stage="quantity",
                title=title,
                produces=f"identity({title})",
                detail_lines=lines,
            ),
        )
    return (_note(f"{title} is not a theorem"),)


def order_rule(left: Term, right: Term, left_rat: RatTheorem, right_rat: RatTheorem, prelude: tuple[str, ...] = ()) -> Rule:
    holds, compared = comparison_lines(left_rat.value, right_rat.value)
    title_body = f"{pretty(left)} <= {pretty(right)}"
    lines = (*prelude, *rat_trace(left_rat), *rat_trace(right_rat), *compared)
    if holds:
        return Rule(
            id=f"math.rat.le.{left_rat.value.num}.{left_rat.value.den}.{right_rat.value.num}.{right_rat.value.den}",
            layer="base",
            stage="quantity",
            title=title_body,
            produces=f"le({pretty(left)},{pretty(right)})",
            detail_lines=lines,
        )
    return Rule(
        id=f"math.rat.not_le.{left_rat.value.num}.{left_rat.value.den}.{right_rat.value.num}.{right_rat.value.den}",
        layer="base",
        stage="quantity",
        title=f"not ({title_body})",
        produces=f"not_le({pretty(left)},{pretty(right)})",
        detail_lines=lines,
    )


def _note(text: str) -> Rule:
    return Rule(
        id="math.open",
        layer="base",
        stage="check",
        title=text,
        produces=f"open({text})",
        detail_lines=(text,),
    )


def _from_raw(rule: str, premises: tuple[RatTheorem, ...], raw_num: int, raw_den: int, detail: tuple[str, ...]) -> RatTheorem:
    if raw_den == 0:
        raise NotExact("division by zero")
    return RatTheorem(_reduced(raw_num, raw_den), rule, premises, (raw_num, raw_den), detail)


def _reduced(num: int, den: int) -> Ratio:
    if den == 0:
        raise KernelError("zero denominator")
    if den < 0:
        num, den = -num, -den
    divisor = gcd(abs(num), den)
    return Ratio(num // divisor, den // divisor)


def _product(left: int, right: int) -> int:
    theorem = numeral_mul(left, right)
    value = theorem.formula.right
    if not isinstance(value, IntLit) or value.n != left * right:
        raise KernelError("rational product disagreed with Int.mul")
    return value.n


def _canonical(value: Ratio) -> bool:
    return value.den > 0 and gcd(abs(value.num), value.den) == 1


def _justified(theorem: RatTheorem) -> bool:
    value = theorem.value
    if not _canonical(value):
        return False
    rule = theorem.rule
    premises = theorem.premises
    raw = theorem.raw
    if rule == "Rat.normalize":
        if premises or raw is None or raw[1] == 0:
            return False
        return value == _reduced(raw[0], raw[1])
    if rule == "Rat.neg":
        if len(premises) != 1 or raw is None:
            return False
        premise = premises[0]
        return raw == (-premise.value.num, premise.value.den) and value == _reduced(raw[0], raw[1])
    if rule in {"Rat.add", "Rat.sub", "Rat.mul", "Rat.div"}:
        if len(premises) != 2 or raw is None:
            return False
        left, right = premises
        if not _canonical(left.value) or not _canonical(right.value):
            return False
        expected = _expected_raw(rule, left.value, right.value)
        if expected is None or raw != expected:
            return False
        return value == _reduced(raw[0], raw[1])
    return False


def _expected_raw(rule: str, left: Ratio, right: Ratio) -> tuple[int, int] | None:
    if rule == "Rat.add":
        return (left.num * right.den + right.num * left.den, left.den * right.den)
    if rule == "Rat.sub":
        return (left.num * right.den - right.num * left.den, left.den * right.den)
    if rule == "Rat.mul":
        return (left.num * right.num, left.den * right.den)
    if rule == "Rat.div":
        if right.num == 0:
            return None
        return (left.num * right.den, left.den * right.num)
    return None
