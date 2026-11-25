"""Integer laws shared by Lean 4.36, Isabelle2025-2 HOL, and Coq's ZArith.

The names were checked against this machine's Lean (`lean --version` 4.36.0)
and against `Isabelle2025-2/src/HOL/Groups.thy` and `Rings.thy`. Coq names are
the ZArith lemmas for the same equations. Subtraction in all three is addition
of the additive inverse.
"""

from __future__ import annotations

from dataclasses import dataclass

from pgi.math.syntax import App, IntLit, Term

A = "a"
B = "b"
C = "c"


@dataclass(frozen=True)
class Meta:
    name: str


Pattern = IntLit | App | Meta


@dataclass(frozen=True)
class Axiom:
    rule: str
    left: Pattern
    right: Pattern
    lean: str
    isabelle: str
    coq: str
    reduces: bool = False


def _v(name: str) -> Meta:
    return Meta(name)


def _add(left: Pattern, right: Pattern) -> App:
    return App("add", (left, right))  # type: ignore[arg-type]


def _mul(left: Pattern, right: Pattern) -> App:
    return App("mul", (left, right))  # type: ignore[arg-type]


def _neg(inner: Pattern) -> App:
    return App("neg", (inner,))  # type: ignore[arg-type]


def _sub(left: Pattern, right: Pattern) -> App:
    return App("sub", (left, right))  # type: ignore[arg-type]


_A = _v(A)
_B = _v(B)
_C = _v(C)
_ZERO = IntLit(0)
_ONE = IntLit(1)

AXIOMS: tuple[Axiom, ...] = (
    Axiom("Int.add_comm", _add(_A, _B), _add(_B, _A), "Int.add_comm", "add.commute", "Z.add_comm"),
    Axiom(
        "Int.add_assoc",
        _add(_add(_A, _B), _C),
        _add(_A, _add(_B, _C)),
        "Int.add_assoc",
        "add.assoc",
        "Z.add_assoc",
    ),
    Axiom("Int.add_zero", _add(_A, _ZERO), _A, "Int.add_zero", "add_0_right", "Z.add_0_r", True),
    Axiom("Int.zero_add", _add(_ZERO, _A), _A, "Int.zero_add", "add_0_left", "Z.add_0_l", True),
    Axiom(
        "Int.add_right_neg",
        _add(_A, _neg(_A)),
        _ZERO,
        "Int.add_right_neg",
        "right_minus",
        "Z.add_opp_diag_r",
        True,
    ),
    Axiom(
        "Int.add_left_neg",
        _add(_neg(_A), _A),
        _ZERO,
        "Int.add_left_neg",
        "left_minus",
        "Z.add_opp_diag_l",
        True,
    ),
    Axiom("Int.neg_neg", _neg(_neg(_A)), _A, "Int.neg_neg", "minus_minus", "Z.opp_involutive", True),
    Axiom(
        "Int.sub_eq_add_neg",
        _sub(_A, _B),
        _add(_A, _neg(_B)),
        "Int.sub_eq_add_neg",
        "diff_conv_add_uminus",
        "Z.sub",
        True,
    ),
    Axiom("Int.mul_comm", _mul(_A, _B), _mul(_B, _A), "Int.mul_comm", "mult.commute", "Z.mul_comm"),
    Axiom(
        "Int.mul_assoc",
        _mul(_mul(_A, _B), _C),
        _mul(_A, _mul(_B, _C)),
        "Int.mul_assoc",
        "mult.assoc",
        "Z.mul_assoc",
    ),
    Axiom("Int.mul_one", _mul(_A, _ONE), _A, "Int.mul_one", "mult_1_right", "Z.mul_1_r", True),
    Axiom("Int.one_mul", _mul(_ONE, _A), _A, "Int.one_mul", "mult_1_left", "Z.mul_1_l", True),
    Axiom("Int.mul_zero", _mul(_A, _ZERO), _ZERO, "Int.mul_zero", "mult_zero_right", "Z.mul_0_r", True),
    Axiom("Int.zero_mul", _mul(_ZERO, _A), _ZERO, "Int.zero_mul", "mult_zero_left", "Z.mul_0_l", True),
    Axiom(
        "Int.mul_add",
        _mul(_A, _add(_B, _C)),
        _add(_mul(_A, _B), _mul(_A, _C)),
        "Int.mul_add",
        "distrib_left",
        "Z.mul_add_distr_l",
    ),
    Axiom(
        "Int.add_mul",
        _mul(_add(_A, _B), _C),
        _add(_mul(_A, _C), _mul(_B, _C)),
        "Int.add_mul",
        "distrib_right",
        "Z.mul_add_distr_r",
    ),
)

BY_RULE = {axiom.rule: axiom for axiom in AXIOMS}
REDUCING = tuple(axiom for axiom in AXIOMS if axiom.reduces)

LOGIC = (
    ("Eq.refl", "Eq.refl", "refl", "eq_refl"),
    ("Eq.symm", "Eq.symm", "sym", "eq_sym"),
    ("Eq.trans", "Eq.trans", "trans", "eq_trans"),
    ("congr", "congr / congrArg", "cong", "f_equal"),
)
