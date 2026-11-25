"""A small LCF kernel for integer equality.

A theorem exists only when the named rule justifies that formula from its
premises. Numeral steps are checked twice: the place-value reconstruction and
the ring operation have to agree.
"""

from __future__ import annotations

from dataclasses import dataclass

from pgi.math.axioms import BY_RULE, Meta, Axiom
from pgi.math.numerals import add_from_digits, mul_from_places, sub_from_digits
from pgi.math.syntax import App, Eq, IntLit, Term, Var, pretty_eq


class KernelError(Exception):
    pass


class NotExact(KernelError):
    pass


@dataclass(frozen=True)
class Theorem:
    formula: Eq
    rule: str
    premises: tuple[Theorem, ...] = ()
    detail: tuple[str, ...] = ()
    source: str = ""

    def __post_init__(self) -> None:
        if not _justified(self):
            raise KernelError(f"{self.rule} does not justify {pretty_eq(self.formula)}")


def refl(term: Term) -> Theorem:
    return Theorem(Eq(term, term), "Eq.refl")


def sym(premise: Theorem) -> Theorem:
    formula = premise.formula
    return Theorem(Eq(formula.right, formula.left), "Eq.symm", (premise,))


def trans(left: Theorem, right: Theorem) -> Theorem:
    return Theorem(Eq(left.formula.left, right.formula.right), "Eq.trans", (left, right))


def congr(op: str, premises: tuple[Theorem, ...]) -> Theorem:
    left = App(op, tuple(premise.formula.left for premise in premises))
    right = App(op, tuple(premise.formula.right for premise in premises))
    return Theorem(Eq(left, right), "congr", premises)


def anchor(name: str, value: int, source: str) -> Theorem:
    if not source.strip():
        raise KernelError("an observable needs a source")
    return Theorem(
        Eq(Var(name), IntLit(value)),
        "observable.anchor",
        (),
        (f"observable.anchor: {name} = {value}", f"source {source.strip()}"),
        source.strip(),
    )


def apply_axiom(axiom: Axiom, term: Term) -> Theorem | None:
    env: dict[str, Term] = {}
    if not _match(axiom.left, term, env):
        return None
    right = _instantiate(axiom.right, env)
    if not isinstance(right, (IntLit, Var, App)):
        return None
    return Theorem(Eq(term, right), axiom.rule)


def numeral_add(left: int, right: int) -> Theorem:
    if left >= 0 and right >= 0:
        total, lines = add_from_digits(left, right)
        if total != left + right:
            raise KernelError("digit addition disagreed with Int.add")
    else:
        total = left + right
        lines = (f"The result is the exact integer {total}.",)
    return Theorem(Eq(App("add", (IntLit(left), IntLit(right))), IntLit(total)), "Int.add", (), lines)


def numeral_sub(left: int, right: int) -> Theorem:
    if left >= 0 and right >= 0 and left >= right:
        total, lines = sub_from_digits(left, right)
        if total != left - right:
            raise KernelError("digit subtraction disagreed with Int.sub")
    else:
        total = left - right
        lines = (f"The result is the exact integer {total}.",)
    return Theorem(Eq(App("sub", (IntLit(left), IntLit(right))), IntLit(total)), "Int.sub", (), lines)


def numeral_mul(left: int, right: int) -> Theorem:
    sign = -1 if (left < 0) ^ (right < 0) else 1
    magnitude, lines = mul_from_places(abs(left), abs(right))
    total = sign * magnitude
    if total != left * right:
        raise KernelError("place multiplication disagreed with Int.mul")
    return Theorem(Eq(App("mul", (IntLit(left), IntLit(right))), IntLit(total)), "Int.mul", (), lines)


def numeral_neg(value: int) -> Theorem:
    return Theorem(
        Eq(App("neg", (IntLit(value),)), IntLit(-value)),
        "Int.neg",
        (),
        (f"The result is the exact integer {-value}.",),
    )


def numeral_div(left: int, right: int) -> Theorem:
    if right == 0:
        raise NotExact(f"{left} / {right} is division by zero")
    quotient = exact_quotient(left, right)
    if quotient is None:
        raise NotExact(f"{left} / {right} is not an exact integer quotient")
    return Theorem(
        Eq(App("div", (IntLit(left), IntLit(right))), IntLit(quotient)),
        "Int.ediv",
        (),
        (f"Int.ediv: {right} * {quotient} = {left}",),
    )


def numeral_pow(base: int, exponent: int) -> Theorem:
    if exponent < 0:
        raise NotExact(f"{base}^{exponent} is not an exact integer")
    if exponent > 32:
        raise NotExact("this power exceeds the exponent limit")
    if exponent == 0:
        if base == 0:
            raise NotExact("0^0 stays open")
        return Theorem(
            Eq(App("pow", (IntLit(base), IntLit(0))), IntLit(1)),
            "Int.pow",
            (),
            ("Int.pow: a nonzero integer to the power 0 is 1.",),
        )
    total = 1
    for _ in range(exponent):
        step = numeral_mul(total, base)
        right = step.formula.right
        if not isinstance(right, IntLit) or right.n != total * base:
            raise KernelError("power multiplication disagreed with Int.mul")
        total = right.n
    if total != base ** exponent:
        raise KernelError("repeated multiplication disagreed with the integer power")
    return Theorem(
        Eq(App("pow", (IntLit(base), IntLit(exponent))), IntLit(total)),
        "Int.pow",
        (),
        (f"Int.pow: {base}^{exponent} = {total} by repeated Int.mul.",),
    )


def exact_quotient(left: int, right: int) -> int | None:
    if right == 0:
        return None
    quotient = left // right
    if right * quotient == left:
        return quotient
    return None


def trace(theorem: Theorem) -> tuple[str, ...]:
    lines: list[str] = []
    for premise in theorem.premises:
        lines.extend(trace(premise))
    if theorem.rule != "Eq.refl":
        lines.append(f"{theorem.rule}: {pretty_eq(theorem.formula)}")
        lines.extend(theorem.detail)
    return tuple(lines)


def _justified(theorem: Theorem) -> bool:
    formula = theorem.formula
    rule = theorem.rule
    premises = theorem.premises
    if rule == "Eq.refl":
        return formula.left == formula.right and not premises
    if rule == "Eq.symm":
        if len(premises) != 1:
            return False
        return formula == Eq(premises[0].formula.right, premises[0].formula.left)
    if rule == "Eq.trans":
        if len(premises) != 2:
            return False
        return (
            premises[0].formula.right == premises[1].formula.left
            and formula == Eq(premises[0].formula.left, premises[1].formula.right)
        )
    if rule == "congr":
        if not premises:
            return False
        if not isinstance(formula.left, App) or not isinstance(formula.right, App):
            return False
        if formula.left.op != formula.right.op or len(premises) != len(formula.left.args):
            return False
        for premise, left, right in zip(premises, formula.left.args, formula.right.args):
            if premise.formula != Eq(left, right):
                return False
        return True
    if rule == "observable.anchor":
        return (
            not premises
            and bool(theorem.source.strip())
            and isinstance(formula.left, Var)
            and isinstance(formula.right, IntLit)
        )
    if rule in {"Int.add", "Int.sub", "Int.mul", "Int.ediv", "Int.pow"}:
        return _numeral_step(formula, rule)
    if rule == "Int.neg":
        if premises or not isinstance(formula.left, App) or formula.left.op != "neg":
            return False
        inner = formula.left.args[0] if formula.left.args else None
        return isinstance(inner, IntLit) and formula.right == IntLit(-inner.n)
    if rule in BY_RULE:
        return not premises and _schema_ok(BY_RULE[rule], formula)
    return False


def _numeral_step(formula: Eq, rule: str) -> bool:
    op = {"Int.add": "add", "Int.sub": "sub", "Int.mul": "mul", "Int.ediv": "div", "Int.pow": "pow"}[rule]
    if not isinstance(formula.left, App) or formula.left.op != op or len(formula.left.args) != 2:
        return False
    left = formula.left.args[0]
    right = formula.left.args[1]
    if not isinstance(left, IntLit) or not isinstance(right, IntLit) or not isinstance(formula.right, IntLit):
        return False
    if rule == "Int.ediv":
        return exact_quotient(left.n, right.n) == formula.right.n
    if rule == "Int.pow":
        if right.n < 0 or right.n > 32:
            return False
        if right.n == 0:
            return left.n != 0 and formula.right.n == 1
        return formula.right.n == left.n ** right.n
    expected = _operate(rule, left.n, right.n)
    if formula.right.n != expected:
        return False
    if rule == "Int.add" and left.n >= 0 and right.n >= 0:
        return add_from_digits(left.n, right.n)[0] == expected
    if rule == "Int.sub" and left.n >= 0 and right.n >= 0 and left.n >= right.n:
        return sub_from_digits(left.n, right.n)[0] == expected
    if rule == "Int.mul":
        sign = -1 if (left.n < 0) ^ (right.n < 0) else 1
        return sign * mul_from_places(abs(left.n), abs(right.n))[0] == expected
    return True


def _operate(rule: str, left: int, right: int) -> int:
    if rule == "Int.add":
        return left + right
    if rule == "Int.sub":
        return left - right
    if rule == "Int.mul":
        return left * right
    raise KernelError(rule)


def _schema_ok(axiom: Axiom, formula: Eq) -> bool:
    env: dict[str, Term] = {}
    if not _match(axiom.left, formula.left, env):
        return False
    return _instantiate(axiom.right, env) == formula.right


def _match(pattern: object, term: Term, env: dict[str, Term]) -> bool:
    if isinstance(pattern, Meta):
        bound = env.get(pattern.name)
        if bound is None:
            env[pattern.name] = term
            return True
        return bound == term
    if isinstance(pattern, IntLit) and isinstance(term, IntLit):
        return pattern.n == term.n
    if isinstance(pattern, App) and isinstance(term, App):
        if pattern.op != term.op or len(pattern.args) != len(term.args):
            return False
        return all(_match(left, right, env) for left, right in zip(pattern.args, term.args))
    return False


def _instantiate(pattern: object, env: dict[str, Term]) -> Term:
    if isinstance(pattern, Meta):
        return env[pattern.name]
    if isinstance(pattern, IntLit):
        return pattern
    if isinstance(pattern, App):
        return App(pattern.op, tuple(_instantiate(arg, env) for arg in pattern.args))
    raise KernelError("pattern did not build a term")
