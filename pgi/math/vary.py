"""Variational principles: an action density, Euler–Lagrange, and Noether currents.

A mechanical Lagrangian is L(q, v, t), with v the velocity of the
coordinate q. The Euler–Lagrange expression is d/dt(∂L/∂v) − ∂L/∂q,
where the total time derivative uses the chain rule with a formal
acceleration. An inverse, here a coefficient in a derivative, is kept
only when it multiplies back.

The energy is v ∂L/∂v − L, and the canonical momentum is ∂L/∂v. The
off-shell Noether identity for time translation is
dE/dt − v EL + ∂L/∂t = 0, checked identically. When L has no explicit
q, the companion identity is dp/dt − EL = 0.

The action is the integral of L; until integration is admitted, the
kernel holds the integrand and checks the stationarity identity.

Certificates are identities, checked exactly, with no approximation.
"""

from __future__ import annotations

from dataclasses import dataclass

from pgi.math.kernel import KernelError, NotExact
from pgi.math.poly import MRat, as_rat, eval_symbolic
from pgi.math.rational import Ratio, RatTheorem, rat_normalize
from pgi.math.syntax import App, IntLit, Term, Var, pretty
from pgi.math.trans import (
    FExpr,
    const_fexpr,
    eval_trans,
    fexpr_add,
    fexpr_diff,
    fexpr_div,
    fexpr_eq,
    fexpr_mul,
    fexpr_neg,
    fexpr_sub,
    has_trans,
    show_fexpr,
    var_fexpr,
)
from pgi.model import Rule


_ZERO = Ratio(0, 1)
_ONE = Ratio(1, 1)
_HALF = Ratio(1, 2)


def _lift(value, plains: tuple[str, ...]) -> FExpr:
    if isinstance(value, FExpr):
        return value
    if isinstance(value, MRat):
        return FExpr(value, ())
    raise NotExact("this Lagrangian density is not an admitted expression")


def _zero(plains: tuple[str, ...]) -> FExpr:
    return const_fexpr(_ZERO, plains)


def _is_zero(value: FExpr) -> bool:
    return fexpr_eq(value, _zero(_plains(value)))


def _plains(value: FExpr) -> tuple[str, ...]:
    from pgi.math.trans import _plains_of

    return _plains_of(value)


def _merge(*groups: tuple[str, ...]) -> tuple[str, ...]:
    seen: list[str] = []
    for group in groups:
        for name in group:
            if name not in seen:
                seen.append(name)
    return tuple(seen)


@dataclass(frozen=True)
class Lagrangian:
    """A first-order mechanical Lagrangian L(q, v, t)."""

    density: FExpr
    coord: str
    velocity: str
    time: str
    accel: str = "a"

    def __post_init__(self) -> None:
        if not self.coord or not self.velocity or not self.time:
            raise KernelError("this Lagrangian is missing a coordinate, a velocity, or a time")
        if len({self.coord, self.velocity, self.time, self.accel}) != 4:
            raise KernelError("the coordinate, velocity, time, and acceleration must be distinct names")


def _plains_of_L(value: Lagrangian) -> tuple[str, ...]:
    return _merge(_plains(value.density), (value.coord, value.velocity, value.time, value.accel))


def _var(name: str, plains: tuple[str, ...]) -> FExpr:
    return var_fexpr(name, plains)


def _partial(value: FExpr, name: str) -> FExpr:
    return fexpr_diff(value, name)


def _total_dt(value: FExpr, lag: Lagrangian) -> FExpr:
    """d/dt of an expression of q, v, and t, with formal acceleration."""
    plains = _plains_of_L(lag)
    value = _lift(value, plains)
    q, v, a, t = lag.coord, lag.velocity, lag.accel, lag.time
    part_t = _partial(value, t)
    part_q = fexpr_mul(_var(v, plains), _partial(value, q))
    part_v = fexpr_mul(_var(a, plains), _partial(value, v))
    return fexpr_add(part_t, fexpr_add(part_q, part_v))


def make_lagrangian(density, coord: str, velocity: str, time: str) -> Lagrangian:
    accel = "a"
    if accel in {coord, velocity, time}:
        accel = "acc"
    plains = _merge(_plains(_lift(density, (coord, velocity, time))), (coord, velocity, time, accel))
    lag = Lagrangian(_lift(density, plains), coord, velocity, time, accel)
    return lag


def euler(lag: Lagrangian) -> FExpr:
    """d/dt(∂L/∂v) − ∂L/∂q."""
    L = lag.density
    dv = _partial(L, lag.velocity)
    dq = _partial(L, lag.coord)
    return fexpr_sub(_total_dt(dv, lag), dq)


def energy(lag: Lagrangian) -> FExpr:
    """E = v ∂L/∂v − L."""
    plains = _plains_of_L(lag)
    mom = _partial(lag.density, lag.velocity)
    return fexpr_sub(fexpr_mul(_var(lag.velocity, plains), mom), lag.density)


def canonical(lag: Lagrangian) -> FExpr:
    """p = ∂L/∂v."""
    return _partial(lag.density, lag.velocity)


def noether_time(lag: Lagrangian) -> FExpr:
    """The residual dE/dt − v EL + ∂L/∂t, identically zero."""
    plains = _plains_of_L(lag)
    dE = _total_dt(energy(lag), lag)
    residual = fexpr_sub(dE, fexpr_mul(_var(lag.velocity, plains), euler(lag)))
    residual = fexpr_add(residual, _partial(lag.density, lag.time))
    return residual


def noether_shift(lag: Lagrangian) -> FExpr:
    """The residual dp/dt − EL − ∂L/∂q, identically zero."""
    dp = _total_dt(canonical(lag), lag)
    return fexpr_sub(fexpr_sub(dp, euler(lag)), _partial(lag.density, lag.coord))


def _show_mech(value: FExpr, lag: Lagrangian) -> str:
    shown = show_fexpr(value)
    # Longer names first so 'a' is not replaced inside 'acc' if used, and
    # velocity/coord are replaced after unique-token substitution via
    # word-like tokens. These are plain identifiers in show_fexpr output.
    acc_tok = f"accel({lag.coord}, {lag.time})"
    vel_tok = f"vel({lag.coord}, {lag.time})"
    # Replace acceleration and velocity as whole identifiers.
    parts: list[str] = []
    i = 0
    text = shown
    names = {lag.accel: acc_tok, lag.velocity: vel_tok}
    # Sort longer keys first.
    keys = sorted(names, key=len, reverse=True)
    result = text
    for key in keys:
        result = _replace_ident(result, key, names[key])
    return result


def _replace_ident(text: str, name: str, image: str) -> str:
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text.startswith(name, i) and _is_ident_at(text, i, name):
            out.append(image)
            i += len(name)
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def _is_ident_at(text: str, index: int, name: str) -> bool:
    if index > 0 and _is_ident_char(text[index - 1]):
        return False
    end = index + len(name)
    if end < len(text) and _is_ident_char(text[end]):
        return False
    return True


def _is_ident_char(char: str) -> bool:
    return char.isalnum() or char == "_"


def show_vary(value) -> str:
    if isinstance(value, Lagrangian):
        return f"lagrangian({_show_mech(value.density, value)}, {value.coord}, {value.velocity}, {value.time})"
    if isinstance(value, FExpr):
        return show_fexpr(value)
    return str(value)


def _check_standing() -> None:
    from pgi.math.syntax import parse_term

    plains = ("q", "v", "t", "a")
    q = _var("q", plains)
    v = _var("v", plains)
    half = const_fexpr(_HALF, plains)
    # Harmonic oscillator, ω = m = 1: L = v²/2 − q²/2.
    L_ho = fexpr_sub(fexpr_mul(half, fexpr_mul(v, v)), fexpr_mul(half, fexpr_mul(q, q)))
    ho = make_lagrangian(L_ho, "q", "v", "t")
    a = _var("a", plains)
    el = euler(ho)
    if not fexpr_eq(el, fexpr_add(a, q)):
        raise KernelError("the Euler–Lagrange expression of the oscillator was not a + q")
    if not _is_zero(noether_time(ho)):
        raise KernelError("the time-translation identity failed for the oscillator")
    if not _is_zero(noether_shift(ho)):
        raise KernelError("the shift identity failed for the oscillator")
    # Energy of the oscillator is v²/2 + q²/2.
    expected_E = fexpr_add(fexpr_mul(half, fexpr_mul(v, v)), fexpr_mul(half, fexpr_mul(q, q)))
    if not fexpr_eq(energy(ho), expected_E):
        raise KernelError("the oscillator energy was not v²/2 + q²/2")
    # Free particle: L = v²/2, EL = a, p = v, dE/dt = v a.
    L_free = fexpr_mul(half, fexpr_mul(v, v))
    free = make_lagrangian(L_free, "q", "v", "t")
    if not fexpr_eq(euler(free), a):
        raise KernelError("the Euler–Lagrange expression of a free particle was not the acceleration")
    if not fexpr_eq(canonical(free), v):
        raise KernelError("the canonical momentum of a free particle was not v")
    if not _is_zero(noether_time(free)) or not _is_zero(noether_shift(free)):
        raise KernelError("a Noether identity failed for a free particle")
    # Pendulum: L = v²/2 + cos(q). EL = a + sin(q).
    cosine = eval_trans(parse_term("cos(q)"))
    L_pen = fexpr_add(fexpr_mul(half, fexpr_mul(v, v)), cosine)
    pen = make_lagrangian(L_pen, "q", "v", "t")
    sine = eval_trans(parse_term("sin(q)"))
    if not fexpr_eq(euler(pen), fexpr_add(a, sine)):
        raise KernelError("the Euler–Lagrange expression of the pendulum was not a + sin(q)")
    if not _is_zero(noether_time(pen)):
        raise KernelError("the time-translation identity failed for the pendulum")


_STANDING = False


def _standing() -> None:
    global _STANDING
    if _STANDING:
        return
    _check_standing()
    _STANDING = True


VARY_OPS = frozenset({
    "lagrangian",
    "euler",
    "energy",
    "canonical",
    "noether",
    "action",
    "vel",
    "accel",
})


def _contains_op(term: Term, names: frozenset[str]) -> bool:
    if isinstance(term, App):
        if term.op in names:
            return True
        return any(_contains_op(arg, names) for arg in term.args)
    return False


def has_vary(term: Term) -> bool:
    return _contains_op(term, VARY_OPS)


def _name(term: Term) -> str:
    if isinstance(term, Var):
        return term.name
    raise NotExact("a variational name is a coordinate")


def _eval_density(term: Term, plains: tuple[str, ...]) -> FExpr:
    if has_trans(term):
        return _lift(eval_trans(term), plains)
    return _lift(eval_symbolic(term), plains)


def _eval_lag(term: Term) -> Lagrangian:
    if not isinstance(term, App) or term.op != "lagrangian":
        raise NotExact("a Lagrangian names the density, the coordinate, the velocity, and the time")
    if len(term.args) != 4:
        raise NotExact("lagrangian takes L, q, v, and t")
    coord, velocity, time = _name(term.args[1]), _name(term.args[2]), _name(term.args[3])
    density = _eval_density(term.args[0], (coord, velocity, time))
    return make_lagrangian(density, coord, velocity, time)


def _eval_vary_expr(term: Term) -> FExpr | Lagrangian:
    _standing()
    if isinstance(term, App):
        if term.op == "lagrangian":
            return _eval_lag(term)
        if term.op == "action":
            if len(term.args) != 1:
                raise NotExact("action takes a Lagrangian")
            return _eval_lag(term.args[0]) if isinstance(term.args[0], App) and term.args[0].op == "lagrangian" else _eval_lag(term)
        if term.op == "euler":
            if len(term.args) != 1:
                raise NotExact("euler takes a Lagrangian")
            return euler(_eval_lag(term.args[0]))
        if term.op == "energy":
            if len(term.args) != 1:
                raise NotExact("energy takes a Lagrangian")
            return energy(_eval_lag(term.args[0]))
        if term.op == "canonical":
            if len(term.args) != 1:
                raise NotExact("canonical takes a Lagrangian")
            return canonical(_eval_lag(term.args[0]))
        if term.op == "noether":
            if len(term.args) != 2:
                raise NotExact("noether takes a Lagrangian and a symmetry name")
            lag = _eval_lag(term.args[0])
            label = _name(term.args[1])
            if label == "time":
                return noether_time(lag)
            if label == "shift":
                return noether_shift(lag)
            raise NotExact("noether admits the symmetries time and shift")
        if term.op == "vel":
            if len(term.args) != 2:
                raise NotExact("vel takes a coordinate and a time")
            # vel(q, t) is the velocity symbol d(q,t) in a comparison.
            # Evaluate as the plain velocity name matching lag? Standalone
            # vel(q, t) is the formal name "v" only in context. For equality,
            # treat vel(q, t) as an FExpr identifier that show maps to the
            # same pretty, by using a formal function derivative? Simpler:
            # we only compare after formalizing both sides with a Lagrangian
            # context. Standalone vel is shown but evaluation needs names.
            raise NotExact("vel is used in a variational identity, not as a standalone value")
        if term.op in {"add", "sub"} and len(term.args) == 2:
            left, right = _eval_vary_expr(term.args[0]), _eval_vary_expr(term.args[1])
            if isinstance(left, Lagrangian) or isinstance(right, Lagrangian):
                raise NotExact("a Lagrangian is not added as a scalar")
            return fexpr_add(left, right) if term.op == "add" else fexpr_sub(left, right)
        if term.op == "neg" and len(term.args) == 1:
            value = _eval_vary_expr(term.args[0])
            if isinstance(value, Lagrangian):
                raise NotExact("a Lagrangian is not negated as a scalar")
            return fexpr_neg(value)
    raise NotExact("this term is not a variational expression")


def context_lag(term: Term) -> Lagrangian | None:
    if isinstance(term, App):
        if term.op == "lagrangian":
            try:
                return _eval_lag(term)
            except NotExact:
                return None
        for arg in term.args:
            found = context_lag(arg)
            if found is not None:
                return found
    return None


def _display(value, lag: Lagrangian | None) -> str:
    if isinstance(value, Lagrangian):
        return show_vary(value)
    if isinstance(value, FExpr):
        if lag is not None:
            return _show_mech(value, lag)
        return show_fexpr(value)
    return str(value)


@dataclass(frozen=True)
class VaryTheorem:
    value: FExpr | Lagrangian
    origin: Term
    lag: Lagrangian | None = None
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        expected = _eval_vary_expr(self.origin)
        if isinstance(self.value, Lagrangian) or isinstance(expected, Lagrangian):
            if not (isinstance(self.value, Lagrangian) and isinstance(expected, Lagrangian)):
                raise KernelError("this variational result does not match the exact evaluation")
            if not fexpr_eq(self.value.density, expected.density) or self.value.coord != expected.coord or self.value.velocity != expected.velocity or self.value.time != expected.time:
                raise KernelError("this variational result does not match the exact evaluation")
            return
        if not fexpr_eq(self.value, expected):
            raise KernelError("this variational result does not match the exact evaluation")


def eval_vary_result(term: Term):
    _standing()
    value = _eval_vary_expr(term)
    lag = value if isinstance(value, Lagrangian) else context_lag(term)
    return VaryTheorem(value, term, lag, _detail())


def _detail() -> tuple[str, ...]:
    return (
        "The Euler–Lagrange expression is d/dt(∂L/∂v) − ∂L/∂q, with the total time derivative taken by the chain rule.",
        "The energy E = v ∂L/∂v − L satisfies dE/dt − v EL + ∂L/∂t = 0 identically.",
        "The action is the integral of L; stationarity is the Euler–Lagrange identity.",
    )


def vary_value_rule(origin: Term, result: object, prelude: tuple[str, ...] = ()) -> Rule:
    if not isinstance(result, VaryTheorem):
        raise KernelError("this variational result has no claim")
    shown = _display(result.value, result.lag)
    if isinstance(result.value, FExpr) and _is_zero(result.value):
        shown = "0"
    return Rule(
        id=f"math.vary.{shown}",
        layer="base",
        stage="quantity",
        title=f"{pretty(origin)} = {shown}",
        produces=shown,
        detail_lines=(*prelude, *result.detail),
    )


def vary_equality_rules(
    left: Term,
    right: Term,
    left_value: object,
    right_value: object,
    prelude: tuple[str, ...] = (),
) -> tuple[Rule, ...]:
    title = f"{pretty(left)} = {pretty(right)}"
    if _vary_eq(left_value, right_value):
        return (
            Rule(
                id="math.vary.eq",
                layer="base",
                stage="quantity",
                title=title,
                produces=f"identity({title})",
                detail_lines=(*prelude, "The two sides are the same exact variational expression."),
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


def _as_fexpr(value: object) -> FExpr | None:
    if isinstance(value, VaryTheorem):
        if isinstance(value.value, FExpr):
            return value.value
        return None
    if isinstance(value, FExpr):
        return value
    return None


def _is_zero_side(value: object) -> bool:
    expr = _as_fexpr(value)
    if expr is not None:
        return _is_zero(expr)
    if isinstance(value, RatTheorem):
        return value.value.num == 0
    if isinstance(value, Ratio):
        return value.num == 0
    return False


def _vary_eq(left: object, right: object) -> bool:
    a, b = _as_fexpr(left), _as_fexpr(right)
    if a is not None and b is not None:
        return fexpr_eq(a, b)
    if a is not None and _is_zero_side(right):
        return _is_zero(a)
    if b is not None and _is_zero_side(left):
        return _is_zero(b)
    if isinstance(left, VaryTheorem) and isinstance(left.value, Lagrangian) and isinstance(right, VaryTheorem) and isinstance(right.value, Lagrangian):
        return (
            fexpr_eq(left.value.density, right.value.density)
            and left.value.coord == right.value.coord
            and left.value.velocity == right.value.velocity
            and left.value.time == right.value.time
        )
    return False


def _rewrite_vel_accel(term: Term, lag: Lagrangian) -> Term:
    if isinstance(term, App):
        if term.op == "vel" and len(term.args) == 2:
            if isinstance(term.args[0], Var) and isinstance(term.args[1], Var) and term.args[0].name == lag.coord and term.args[1].name == lag.time:
                return Var(lag.velocity)
            raise NotExact("vel names the coordinate and time of this Lagrangian")
        if term.op == "accel" and len(term.args) == 2:
            if isinstance(term.args[0], Var) and isinstance(term.args[1], Var) and term.args[0].name == lag.coord and term.args[1].name == lag.time:
                return Var(lag.accel)
            raise NotExact("accel names the coordinate and time of this Lagrangian")
        return App(term.op, tuple(_rewrite_vel_accel(arg, lag) for arg in term.args))
    return term


def _eval_in_lag(term: Term, lag: Lagrangian) -> FExpr:
    rewritten = _rewrite_vel_accel(term, lag)
    plains = _plains_of_L(lag)
    if isinstance(rewritten, IntLit):
        return const_fexpr(Ratio(rewritten.n, 1), plains)
    if has_trans(rewritten):
        return _lift(eval_trans(rewritten), plains)
    return _lift(eval_symbolic(rewritten), plains)


def side_as_vary(term: Term, lag: Lagrangian | None = None) -> object:
    try:
        return eval_vary_result(term)
    except NotExact:
        if isinstance(term, IntLit) and term.n == 0:
            return rat_normalize(0, 1)
        if lag is not None:
            return _eval_in_lag(term, lag)
        raise
