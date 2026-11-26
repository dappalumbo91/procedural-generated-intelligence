"""Killing vectors and the Lie derivative of a metric.

The Lie derivative of a metric along a vector field X is the symmetric
2-tensor
  (L_X g)_{μν} = X^ρ ∂_ρ g_{μν} + (∂_μ X^ρ) g_{ρν} + (∂_ν X^ρ) g_{μρ}.
X is a Killing field of g only when L_X g vanishes identically. The
identity is checked exactly, with no approximation.

Certificates include the translations and the rotation of the Euclidean
plane, and Schwarzschild's time-translation ∂_t, axial rotation ∂_φ,
and the remaining two rotation fields
  J_x = −sin(φ) ∂_θ − cot(θ) cos(φ) ∂_φ,
  J_y =  cos(φ) ∂_θ − cot(θ) sin(φ) ∂_φ.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from pgi.math.kernel import KernelError, NotExact
from pgi.math.metric import (
    Metric,
    MetricTheorem,
    Vector,
    _field_add,
    _field_diff,
    _field_embed,
    _field_eq,
    _field_is_zero,
    _field_mul,
    _field_neg,
    _field_show,
    eval_metric,
    eval_vector,
    metric_is_zero,
    named_metric,
    show_metric,
)
from pgi.math.poly import as_rat, const_poly, var_poly, mrat_neg
from pgi.math.rational import Ratio, RatTheorem, rat_normalize
from pgi.math.syntax import App, IntLit, Term, Var, pretty
from pgi.math.trans import const_fexpr, eval_trans, fexpr_div
from pgi.model import Rule


_ZERO = Ratio(0, 1)
_ONE = Ratio(1, 1)


def _const(value: Ratio | int, names: tuple[str, ...]):
    ratio = value if isinstance(value, Ratio) else Ratio(value, 1)
    return const_fexpr(ratio, names)


def _zero_like(metric: Metric):
    return _const(_ZERO, metric.names)


@dataclass(frozen=True)
class FieldVector:
    names: tuple[str, ...]
    components: tuple

    def __post_init__(self) -> None:
        if len(self.names) == 0 or len(self.names) != len(self.components):
            raise KernelError("this vector field is not in normal form")
        if len(set(self.names)) != len(self.names):
            raise KernelError("this vector field is not in normal form")


def _lift_vector(value: Vector | FieldVector, names: tuple[str, ...]) -> FieldVector:
    if value.names != names:
        raise NotExact("this vector field is not in this chart")
    components = tuple(_field_embed(component, names) for component in value.components)
    return FieldVector(names, components)


@lru_cache(maxsize=16)
def lie_metric(vector: FieldVector, metric: Metric) -> Metric:
    if vector.names != metric.names:
        raise NotExact("this vector field is not in this chart")
    names = metric.names
    n = len(names)
    rows = []
    for u in range(n):
        row = []
        for v in range(n):
            total = _zero_like(metric)
            for rho in range(n):
                total = _field_add(total, _field_mul(vector.components[rho], _field_diff(metric.rows[u][v], names[rho])))
                total = _field_add(total, _field_mul(_field_diff(vector.components[rho], names[u]), metric.rows[rho][v]))
                total = _field_add(total, _field_mul(_field_diff(vector.components[rho], names[v]), metric.rows[u][rho]))
            row.append(_field_embed(total, names))
        rows.append(tuple(row))
    result = Metric(names, tuple(rows))
    for u in range(n):
        for v in range(u + 1, n):
            if not _field_eq(result.rows[u][v], result.rows[v][u]):
                raise KernelError("the Lie derivative of the metric was not symmetric")
    return result


def is_killing(vector: FieldVector, metric: Metric) -> bool:
    return metric_is_zero(lie_metric(vector, metric))


def _euclidean_rotation() -> FieldVector:
    names = ("x", "y")
    x = as_rat(var_poly("x", names))
    y = as_rat(var_poly("y", names))
    return FieldVector(names, (mrat_neg(y), x))


def _coord_field(names: tuple[str, ...], index: int) -> FieldVector:
    components = tuple(_const(_ONE if i == index else _ZERO, names) for i in range(len(names)))
    return FieldVector(names, components)


@lru_cache(maxsize=8)
def _schwarzschild_rotation(axis: str) -> FieldVector:
    names = ("t", "r", "theta", "phi")
    zero = _const(_ZERO, names)
    from pgi.math.syntax import parse_term

    sin_phi = _field_embed(eval_trans(parse_term("sin(phi)")), names)
    cos_phi = _field_embed(eval_trans(parse_term("cos(phi)")), names)
    sin_th = _field_embed(eval_trans(parse_term("sin(theta)")), names)
    cos_th = _field_embed(eval_trans(parse_term("cos(theta)")), names)
    cot_th = fexpr_div(cos_th, sin_th)
    if axis == "jx":
        # −sin(φ) ∂_θ − cot(θ) cos(φ) ∂_φ
        return FieldVector(names, (zero, zero, _field_neg(sin_phi), _field_neg(_field_mul(cot_th, cos_phi))))
    if axis == "jy":
        #  cos(φ) ∂_θ − cot(θ) sin(φ) ∂_φ
        return FieldVector(names, (zero, zero, cos_phi, _field_neg(_field_mul(cot_th, sin_phi))))
    raise NotExact("this Schwarzschild rotation is not Jx or Jy")


def _name(term: Term) -> str:
    if isinstance(term, Var):
        return term.name
    raise NotExact("a label is a name")


def named_killing(manifold: str, label: str) -> FieldVector:
    if manifold in {"schwarzschild", "schw"}:
        metric = named_metric("schwarzschild")
        names = metric.names
        if label in {"t", "time"}:
            return _coord_field(names, 0)
        if label in {"phi", "jz"}:
            return _coord_field(names, 3)
        if label == "jx":
            return _schwarzschild_rotation("jx")
        if label == "jy":
            return _schwarzschild_rotation("jy")
        raise NotExact("this Schwarzschild Killing field is not t, phi, jx, or jy")
    if manifold in {"e2", "euclidean2", "euclidean"}:
        names = ("x", "y")
        if label in {"x", "dx"}:
            return _coord_field(names, 0)
        if label in {"y", "dy"}:
            return _coord_field(names, 1)
        if label in {"j", "rotation", "jz"}:
            return _euclidean_rotation()
        raise NotExact("this Euclidean Killing field is not x, y, or j")
    raise NotExact("a named Killing field is admitted here for Schwarzschild or the Euclidean plane")


def show_field_vector(value: FieldVector) -> str:
    inner = ", ".join(_field_show(component) for component in value.components)
    return f"vector({inner})"


def _standing() -> None:
    global _STANDING
    if _STANDING:
        return
    e2 = named_metric("e2")
    if not is_killing(_coord_field(("x", "y"), 0), e2):
        raise KernelError("a Euclidean translation was not Killing")
    if not is_killing(_euclidean_rotation(), e2):
        raise KernelError("the Euclidean rotation was not Killing")
    stretch = FieldVector(("x", "y"), (as_rat(var_poly("x", ("x", "y"))), as_rat(const_poly(_ZERO, ("x", "y")))))
    if is_killing(stretch, e2):
        raise KernelError("a coordinate dilation was wrongly treated as Killing")
    schw = named_metric("schwarzschild")
    for label in ("t", "phi", "jx", "jy"):
        field = named_killing("schwarzschild", label)
        if not is_killing(field, schw):
            raise KernelError(f"the Schwarzschild field {label} was not Killing")
    _STANDING = True


_STANDING = False


KILLING_OPS = frozenset({"killingfield", "lie"})


def _contains_op(term: Term, names: frozenset[str]) -> bool:
    if isinstance(term, App):
        if term.op in names:
            return True
        return any(_contains_op(arg, names) for arg in term.args)
    return False


def has_killing(term: Term) -> bool:
    return _contains_op(term, KILLING_OPS)


def _eval_field_vector(term: Term, names: tuple[str, ...] | None = None) -> FieldVector:
    if isinstance(term, App) and term.op == "killingfield":
        if len(term.args) != 2:
            raise NotExact("killingfield takes a metric name and a field label")
        return named_killing(_name(term.args[0]), _name(term.args[1]))
    if isinstance(term, App) and term.op == "vector":
        vector = eval_vector(term)
        target = names or vector.names
        return _lift_vector(vector, target)
    raise NotExact("lie takes a vector field and a metric")


def _eval(term: Term):
    _standing()
    if isinstance(term, App):
        if term.op == "killingfield":
            return _eval_field_vector(term)
        if term.op == "lie":
            if len(term.args) != 2:
                raise NotExact("lie takes a vector field and a metric")
            metric = eval_metric(term.args[1])
            vector = _eval_field_vector(term.args[0], metric.names)
            return lie_metric(vector, metric)
    raise NotExact("this term is not a Killing field or a Lie derivative")


@dataclass(frozen=True)
class KillingVectorTheorem:
    value: FieldVector
    origin: Term
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if _eval(self.origin) != self.value and not _same_vector(_eval(self.origin), self.value):
            raise KernelError("this Killing field does not match the exact evaluation")


def _same_vector(left, right) -> bool:
    if not isinstance(left, FieldVector) or not isinstance(right, FieldVector):
        return False
    if left.names != right.names or len(left.components) != len(right.components):
        return False
    return all(_field_eq(a, b) for a, b in zip(left.components, right.components))


@dataclass(frozen=True)
class LieTheorem:
    value: Metric
    origin: Term
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        got = _eval(self.origin)
        if not isinstance(got, Metric) or not all(
            _field_eq(got.rows[i][j], self.value.rows[i][j])
            for i in range(got.dim)
            for j in range(got.dim)
        ) or got.names != self.value.names:
            raise KernelError("this Lie derivative does not match the exact evaluation")


def eval_killing_result(term: Term):
    _standing()
    value = _eval(term)
    if isinstance(value, FieldVector):
        return KillingVectorTheorem(value, term, _detail())
    if isinstance(value, Metric):
        return LieTheorem(value, term, _detail())
    raise KernelError("this Killing result has no claim")


def _detail() -> tuple[str, ...]:
    return (
        "The Lie derivative of a metric is (L_X g)_{μν} = X^ρ ∂_ρ g_{μν} + (∂_μ X^ρ) g_{ρν} + (∂_ν X^ρ) g_{μρ}.",
        "X is a Killing field only when L_X g vanishes identically.",
        "Schwarzschild's time-translation ∂_t, axial rotation ∂_φ, and the rotation fields J_x, J_y are Killing, checked identically.",
    )


def killing_value_rule(origin: Term, result: object, prelude: tuple[str, ...] = ()) -> Rule:
    title_left = pretty(origin)
    if isinstance(result, KillingVectorTheorem):
        shown = show_field_vector(result.value)
        return Rule(
            id=f"math.killing.{shown}",
            layer="base",
            stage="quantity",
            title=f"{title_left} = {shown}",
            produces=shown,
            detail_lines=(*prelude, *result.detail),
        )
    if isinstance(result, LieTheorem):
        shown = "lie(0)" if metric_is_zero(result.value) else show_metric(result.value)
        return Rule(
            id=f"math.lie.{shown}",
            layer="base",
            stage="quantity",
            title=f"{title_left} = {shown}",
            produces=shown,
            detail_lines=(*prelude, *result.detail),
        )
    raise KernelError("this Killing result has no claim")


def killing_equality_rules(
    left: Term,
    right: Term,
    left_value: object,
    right_value: object,
    prelude: tuple[str, ...] = (),
) -> tuple[Rule, ...]:
    title = f"{pretty(left)} = {pretty(right)}"
    if _killing_eq(left_value, right_value):
        return (
            Rule(
                id="math.killing.eq",
                layer="base",
                stage="quantity",
                title=title,
                produces=f"identity({title})",
                detail_lines=(*prelude, "The two sides are the same exact vector field or Lie derivative."),
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


def _as_metric(value: object) -> Metric | None:
    if isinstance(value, (LieTheorem, MetricTheorem)):
        return value.value
    if isinstance(value, Metric):
        return value
    return None


def _as_field_vector(value: object) -> FieldVector | None:
    if isinstance(value, KillingVectorTheorem):
        return value.value
    if isinstance(value, FieldVector):
        return value
    return None


def _is_zero_side(value: object) -> bool:
    metric = _as_metric(value)
    if metric is not None:
        return metric_is_zero(metric)
    if isinstance(value, RatTheorem):
        return value.value.num == 0
    if isinstance(value, Ratio):
        return value.num == 0
    if isinstance(value, IntLit):
        return value.n == 0
    return False


def _killing_eq(left: object, right: object) -> bool:
    a, b = _as_field_vector(left), _as_field_vector(right)
    if a is not None and b is not None:
        return _same_vector(a, b)
    la, ra = _as_metric(left), _as_metric(right)
    if la is not None and ra is not None:
        from pgi.math.metric import metric_eq

        return metric_eq(la, ra)
    if la is not None and _is_zero_side(right):
        return metric_is_zero(la)
    if ra is not None and _is_zero_side(left):
        return metric_is_zero(ra)
    return False


def side_as_killing(term: Term) -> object:
    try:
        return eval_killing_result(term)
    except NotExact:
        if isinstance(term, IntLit) and term.n == 0:
            return rat_normalize(0, 1)
        from pgi.math.rational import eval_rat

        return eval_rat(term)
