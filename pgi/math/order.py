"""Integer order, checked the same way as integer equality.

Lean 4.36.0 accepted these names with no imports:

- Int.le_refl (a : Int) : a ≤ a
- Int.le_trans {a b c : Int} : a ≤ b → b ≤ c → a ≤ c
- Int.le_antisymm {a b : Int} : a ≤ b → b ≤ a → a = b
- Int.add_le_add_left {a b : Int} (h : a ≤ b) (c : Int) : c + a ≤ c + b
- Int.le_of_eq {a b : Int} (hab : a = b) : a ≤ b
- Int.not_le {a b : Int} : ¬a ≤ b ↔ b < a
- Int.le_total (a b : Int) : a ≤ b ∨ b ≤ a

Isabelle2025-2, read from source, uses the class assumptions order_refl and
order_trans in Orderings.thy (preorder), order_antisym in the order class,
eq_refl inside that preorder ("x = y ⟹ x ≤ y"), not_le in the linorder
section ("¬ x ≤ y ⟷ y < x"), and add_left_mono in Groups.thy.

A compound comparison is proved by reducing each side with the equality
kernel, then comparing the integers those theorems produced. not_le_by_eq
is that transfer for a rejected numeral comparison. It is not a separate
Lean declaration. Totality still does not choose a direction for two free
variables. Coq names are not recorded in this slice.
"""

from __future__ import annotations

from collections.abc import Callable

from dataclasses import dataclass

from pgi.math.kernel import KernelError, Theorem, sym, trace
from pgi.math.syntax import App, IntLit, Term, Var, parse_term, pretty
from pgi.model import Rule

Reducer = Callable[[Term], Theorem | str | None]


@dataclass(frozen=True)
class Bound:
    rel: str
    left: Term
    right: Term


@dataclass(frozen=True)
class OrderTheorem:
    formula: Bound
    rule: str
    premises: tuple[OrderTheorem, ...] = ()
    shifted: Term | None = None
    equalities: tuple[Theorem, ...] = ()
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _justified(self):
            raise KernelError(f"{self.rule} does not justify {show(self.formula)}")


def le_refl(term: Term) -> OrderTheorem:
    return OrderTheorem(
        Bound("le", term, term),
        "Int.le_refl",
        detail=("Lean Int.le_refl. Isabelle order_refl: x ≤ x.",),
    )


def le_trans(left: OrderTheorem, right: OrderTheorem) -> OrderTheorem:
    return OrderTheorem(
        Bound("le", left.formula.left, right.formula.right),
        "Int.le_trans",
        (left, right),
        detail=("Lean Int.le_trans. Isabelle order_trans.",),
    )


def le_antisymm(left: OrderTheorem, right: OrderTheorem) -> OrderTheorem:
    return OrderTheorem(
        Bound("eq", left.formula.left, left.formula.right),
        "Int.le_antisymm",
        (left, right),
        detail=("Lean Int.le_antisymm. Isabelle order_antisym.",),
    )


def add_le_add_left(premise: OrderTheorem, shift: Term) -> OrderTheorem:
    return OrderTheorem(
        Bound("le", App("add", (shift, premise.formula.left)), App("add", (shift, premise.formula.right))),
        "Int.add_le_add_left",
        (premise,),
        shift,
        detail=("Lean Int.add_le_add_left. Isabelle add_left_mono: a ≤ b implies c + a ≤ c + b.",),
    )


def le_of_eq(equality: Theorem) -> OrderTheorem:
    formula = equality.formula
    return OrderTheorem(
        Bound("le", formula.left, formula.right),
        "Int.le_of_eq",
        equalities=(equality,),
        detail=(
            "Lean Int.le_of_eq: a = b → a ≤ b.",
            "Isabelle Orderings.thy, preorder class, eq_refl: x = y ⟹ x ≤ y.",
        ),
    )


def numeral_le(left: int, right: int) -> OrderTheorem:
    return OrderTheorem(
        Bound("le", IntLit(left), IntLit(right)),
        "numeral_le",
        detail=(
            "numeral_le compares the two integers directly.",
            "Lean discharges the same comparison with decide. Same trust boundary as Int.add.",
        ),
    )


def numeral_not_le(left: int, right: int) -> OrderTheorem:
    return OrderTheorem(
        Bound("not_le", IntLit(left), IntLit(right)),
        "Int.not_le",
        detail=(
            "Lean Int.not_le: ¬a ≤ b ↔ b < a.",
            "Isabelle not_le, Orderings.thy: ¬ x ≤ y ↔ y < x.",
            "The integers were compared directly, the same trust boundary as Int.add.",
        ),
    )


def le_by_eq(left_eq: Theorem, right_eq: Theorem) -> OrderTheorem:
    """a = n and b = m and n ≤ m give a ≤ b."""
    left_value = _int_right(left_eq)
    right_value = _int_right(right_eq)
    up_to_left = le_trans(le_of_eq(left_eq), numeral_le(left_value, right_value))
    up_to_right = le_of_eq(sym(right_eq))
    return le_trans(up_to_left, up_to_right)


def not_le_by_eq(left_eq: Theorem, right_eq: Theorem) -> OrderTheorem:
    """a = n and b = m and ¬(n ≤ m) give ¬(a ≤ b)."""
    rejected = numeral_not_le(_int_right(left_eq), _int_right(right_eq))
    return OrderTheorem(
        Bound("not_le", left_eq.formula.left, right_eq.formula.left),
        "not_le_by_eq",
        (rejected,),
        equalities=(left_eq, right_eq),
        detail=(
            "Each side was replaced by the integer its equality theorem produced.",
            "Int.not_le rejects that numeral comparison, so the original comparison is rejected.",
        ),
    )


def rules_from_body(body: str, reduce: Reducer | None = None) -> tuple[Rule, ...]:
    text = body.replace("≤", "<=")
    if text.count("<=") != 1:
        return (_note("an order claim needs one <="),)
    left_text, _, right_text = text.partition("<=")
    left = parse_term(left_text)
    right = parse_term(right_text)
    if left is None or right is None:
        return (_note("the two sides of <= did not parse"),)
    if isinstance(left, IntLit) and isinstance(right, IntLit):
        if left.n <= right.n:
            return (_from_theorem(numeral_le(left.n, right.n)),)
        return (_from_theorem(numeral_not_le(left.n, right.n)),)
    if left == right:
        return (_from_theorem(le_refl(left)),)
    if reduce is None:
        return (_note(f"{pretty(left)} <= {pretty(right)} is not a theorem"),)
    return _from_reduced(left, right, reduce)


def show(formula: Bound) -> str:
    if formula.rel == "le":
        return f"{pretty(formula.left)} <= {pretty(formula.right)}"
    if formula.rel == "not_le":
        return f"not ({pretty(formula.left)} <= {pretty(formula.right)})"
    return f"{pretty(formula.left)} = {pretty(formula.right)}"


def order_trace(theorem: OrderTheorem) -> tuple[str, ...]:
    lines: list[str] = []
    for equality in theorem.equalities:
        lines.extend(trace(equality))
    for premise in theorem.premises:
        lines.extend(order_trace(premise))
    lines.append(f"{theorem.rule}: {show(theorem.formula)}")
    lines.extend(theorem.detail)
    return tuple(lines)


def _from_reduced(left: Term, right: Term, reduce: Reducer) -> tuple[Rule, ...]:
    left_result = reduce(left)
    right_result = reduce(right)
    if isinstance(left_result, str):
        return (_note(left_result),)
    if isinstance(right_result, str):
        return (_note(right_result),)
    if not isinstance(left_result, Theorem) or not isinstance(right_result, Theorem):
        return (_note(f"{pretty(left)} <= {pretty(right)} is not a theorem"),)
    if left_result.formula.left != left or right_result.formula.left != right:
        return (_note(f"{pretty(left)} <= {pretty(right)} is not a theorem"),)
    if left_result.formula.right == right:
        return (_from_theorem(le_of_eq(left_result)),)
    if right_result.formula.right == left:
        return (_from_theorem(le_of_eq(sym(right_result))),)
    left_value = left_result.formula.right
    right_value = right_result.formula.right
    if isinstance(left_value, IntLit) and isinstance(right_value, IntLit):
        if left_value.n <= right_value.n:
            return (_from_theorem(le_by_eq(left_result, right_result)),)
        return (_from_theorem(not_le_by_eq(left_result, right_result)),)
    if left_value == right_value:
        proved = le_trans(le_of_eq(left_result), le_of_eq(sym(right_result)))
        return (_from_theorem(proved),)
    return (_note(f"{pretty(left)} <= {pretty(right)} is not a theorem"),)


def _from_theorem(theorem: OrderTheorem) -> Rule:
    formula = theorem.formula
    title = show(formula)
    pair = _numeral_pair(theorem)
    if formula.rel == "not_le" and isinstance(formula.left, IntLit) and isinstance(formula.right, IntLit):
        atom = f"not_le({formula.left.n},{formula.right.n})"
        rule_id = f"math.not_le.{formula.left.n}.{formula.right.n}"
    elif formula.rel == "le" and isinstance(formula.left, IntLit) and isinstance(formula.right, IntLit):
        atom = f"le({formula.left.n},{formula.right.n})"
        rule_id = f"math.le.{formula.left.n}.{formula.right.n}"
    elif formula.rel == "le" and isinstance(formula.left, Var) and formula.left == formula.right:
        atom = f"le({formula.left.name},{formula.left.name})"
        rule_id = f"math.le.refl.{formula.left.name}"
    elif pair is not None and formula.rel == "not_le":
        atom = f"not_le({pretty(formula.left)},{pretty(formula.right)})"
        rule_id = f"math.order.not_le.{pair[0]}.{pair[1]}"
    elif pair is not None and formula.rel == "le":
        atom = f"le({pretty(formula.left)},{pretty(formula.right)})"
        rule_id = f"math.order.le.{pair[0]}.{pair[1]}"
    else:
        atom = f"le({pretty(formula.left)},{pretty(formula.right)})"
        rule_id = f"math.order.{formula.rel}"
    return Rule(
        id=rule_id,
        layer="base",
        stage="quantity",
        title=title,
        produces=atom,
        detail_lines=order_trace(theorem),
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


def _int_right(equality: Theorem) -> int:
    value = equality.formula.right
    if not isinstance(value, IntLit):
        raise KernelError("order transfer needs an integer")
    return value.n


def _numeral_pair(theorem: OrderTheorem) -> tuple[int, int] | None:
    formula = theorem.formula
    if theorem.rule in {"numeral_le", "Int.not_le"} and isinstance(formula.left, IntLit) and isinstance(formula.right, IntLit):
        return formula.left.n, formula.right.n
    for premise in theorem.premises:
        found = _numeral_pair(premise)
        if found is not None:
            return found
    return None


def _bare(theorem: OrderTheorem) -> bool:
    return theorem.shifted is None and not theorem.equalities


def _justified(theorem: OrderTheorem) -> bool:
    formula = theorem.formula
    rule = theorem.rule
    premises = theorem.premises
    if rule == "Int.le_refl":
        return _bare(theorem) and formula.rel == "le" and formula.left == formula.right and not premises
    if rule == "Int.le_trans":
        if len(premises) != 2 or not _bare(theorem):
            return False
        first, second = premises
        return (
            first.formula.rel == "le"
            and second.formula.rel == "le"
            and first.formula.right == second.formula.left
            and formula == Bound("le", first.formula.left, second.formula.right)
        )
    if rule == "Int.le_antisymm":
        if len(premises) != 2 or not _bare(theorem):
            return False
        first, second = premises
        return (
            first.formula.rel == "le"
            and second.formula.rel == "le"
            and second.formula == Bound("le", first.formula.right, first.formula.left)
            and formula == Bound("eq", first.formula.left, first.formula.right)
        )
    if rule == "Int.add_le_add_left":
        if len(premises) != 1 or theorem.equalities or theorem.shifted is None:
            return False
        premise = premises[0]
        if premise.formula.rel != "le":
            return False
        shifted = theorem.shifted
        return formula == Bound(
            "le",
            App("add", (shifted, premise.formula.left)),
            App("add", (shifted, premise.formula.right)),
        )
    if rule == "Int.le_of_eq":
        if premises or theorem.shifted is not None or len(theorem.equalities) != 1:
            return False
        equality = theorem.equalities[0]
        return formula == Bound("le", equality.formula.left, equality.formula.right)
    if rule == "numeral_le":
        return (
            _bare(theorem)
            and not premises
            and formula.rel == "le"
            and isinstance(formula.left, IntLit)
            and isinstance(formula.right, IntLit)
            and formula.left.n <= formula.right.n
        )
    if rule == "Int.not_le":
        return (
            _bare(theorem)
            and not premises
            and formula.rel == "not_le"
            and isinstance(formula.left, IntLit)
            and isinstance(formula.right, IntLit)
            and formula.left.n > formula.right.n
        )
    if rule == "not_le_by_eq":
        if len(premises) != 1 or theorem.shifted is not None or len(theorem.equalities) != 2:
            return False
        left_eq, right_eq = theorem.equalities
        rejected = premises[0]
        if not isinstance(left_eq.formula.right, IntLit) or not isinstance(right_eq.formula.right, IntLit):
            return False
        return rejected.formula == Bound(
            "not_le", left_eq.formula.right, right_eq.formula.right
        ) and formula == Bound("not_le", left_eq.formula.left, right_eq.formula.left)
    return False
