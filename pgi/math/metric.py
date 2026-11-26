"""Exact metrics, tangent vectors, and curvature of exact charts.

A metric is a symmetric matrix of exact functions on a chart.
Rational components stay rational. The unit 2-sphere in angular
coordinates uses sin(theta)^2. A tangent vector is a tuple of rational components, acting as a
derivation: it is kept only when it annihilates constants, reproduces
its own components on the coordinate functions, and satisfies the
Leibniz rule on products of those coordinates. The pullback of a
metric g along a map f is J^T g J, kept only when it agrees with
g(df X, df Y) on the coordinate basis. The unit 2-sphere metric in a
stereographic chart is the pullback of the Euclidean 3-metric through
the inverse stereographic embedding, kept only when that embedding
lands on X^2 + Y^2 + Z^2 = 1 and the pullback equals the conformal
metric 4 / (1 + ρ^2)^2 times the identity.

Christoffel symbols, Riemann, Ricci, and the scalar curvature are
computed from the metric by the standard formulas, with exact
arithmetic. An inverse metric is kept only when both
products are the identity. The Levi-Civita connection is kept only
when it is torsion-free and metric-compatible. Flat Euclidean and
Minkowski space have vanishing curvature. The unit 2-sphere has
scalar curvature 2, and its Ricci tensor equals the metric. The
algebraic Riemann symmetries, the first Bianchi identity, and the
second Bianchi identity are checked identically.

Lee, *Introduction to Riemannian Manifolds*, and the standard
stereographic atlas of the unit sphere, are the named constructions.
The certificates are the identities above, checked exactly, with no
approximation.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from pgi.math.kernel import KernelError, NotExact
from pgi.math.manifold import (
    JacMatrix,
    RatMap,
    const_rat,
    embed_rat,
    identity_jac,
    jac_eq,
    jac_inv,
    jac_is_identity,
    jac_mul,
    jac_transpose,
    map_jacobian,
    mrat_subst,
    one_rat,
    restrict_rat,
    show_jac,
    show_map,
    transition_map,
    var_rat,
    zero_rat,
)
from pgi.math.poly import (
    MRat,
    as_rat,
    const_poly,
    eval_symbolic,
    mrat_add,
    mrat_diff,
    mrat_div,
    mrat_eq,
    mrat_mul,
    mrat_neg,
    mrat_pow,
    mrat_sub,
    show_rat,
)
from pgi.math.rational import Ratio, RatTheorem
from pgi.math.syntax import App, IntLit, Term, Var, pretty
from pgi.model import Rule


_ZERO = Ratio(0, 1)
_ONE = Ratio(1, 1)
_NEG_ONE = Ratio(-1, 1)
_TWO = Ratio(2, 1)
_FOUR = Ratio(4, 1)
_HALF = Ratio(1, 2)


def _is_fun(value) -> bool:
    from pgi.math.trans import FExpr

    return isinstance(value, FExpr)


def _metric_is_fun(value: "Metric") -> bool:
    return any(_is_fun(entry) for row in value.rows for entry in row)


def _lift(value):
    from pgi.math.trans import FExpr

    if isinstance(value, FExpr):
        return value
    return FExpr(value, ())


def _zero_for(metric: "Metric"):
    from pgi.math.trans import const_fexpr

    if _metric_is_fun(metric):
        # Unused coordinate plains must not be forced into every intermediate;
        # four spacetime coordinates plus a scale factor and its derivatives
        # would otherwise exceed the polynomial variable limit.
        return const_fexpr(_ZERO, ())
    return zero_rat()


def _field_add(left, right):
    from pgi.math.trans import fexpr_add

    if _is_fun(left) or _is_fun(right):
        return fexpr_add(_lift(left), _lift(right))
    return mrat_add(left, right)


def _field_sub(left, right):
    from pgi.math.trans import fexpr_sub

    if _is_fun(left) or _is_fun(right):
        return fexpr_sub(_lift(left), _lift(right))
    return mrat_sub(left, right)


def _field_mul(left, right):
    from pgi.math.trans import fexpr_mul

    if _is_fun(left) or _is_fun(right):
        return fexpr_mul(_lift(left), _lift(right))
    return mrat_mul(left, right)


def _field_neg(value):
    from pgi.math.trans import fexpr_neg

    if _is_fun(value):
        return fexpr_neg(value)
    return mrat_neg(value)


def _field_div(left, right):
    from pgi.math.trans import fexpr_div

    if _is_fun(left) or _is_fun(right):
        return fexpr_div(_lift(left), _lift(right))
    return mrat_div(left, right)


def _field_diff(value, name: str):
    from pgi.math.trans import fexpr_diff

    if _is_fun(value):
        return fexpr_diff(value, name)
    return mrat_diff(value, name)


def _field_eq(left, right) -> bool:
    from pgi.math.trans import fexpr_eq

    if _is_fun(left) or _is_fun(right):
        return fexpr_eq(_lift(left), _lift(right))
    return mrat_eq(left, right)


def _field_is_zero(value) -> bool:
    from pgi.math.trans import FExpr

    if isinstance(value, FExpr):
        return value.body.num.is_zero
    return value.num.is_zero


def _field_embed(value, names: tuple[str, ...]):
    from pgi.math.trans import FExpr

    if isinstance(value, FExpr):
        return _drop_unused_plains(value)
    return embed_rat(value, names)


def _drop_unused_plains(value):
    """Rewrite an FExpr onto the plains that actually appear, including in atoms."""
    from pgi.math.trans import FExpr, const_fexpr, _atom_names, _plains_of
    from pgi.math.poly import _from_map, mrat_from
    from pgi.math.rational import rat_normalize

    used = tuple(name for name in _plains_of(value) if name in _fexpr_used_names(value))
    if _field_is_zero(value):
        return const_fexpr(_ZERO, used)
    current = _plains_of(value)
    if used == current:
        return value
    new_names = _atom_names(len(value.atoms), used)
    old_names = value.body.num.names

    def map_poly(poly):
        terms: dict[tuple[int, ...], Ratio] = {}
        for monom, coeff in poly.terms:
            env = {old_names[i]: monom[i] if i < len(monom) else 0 for i in range(len(old_names))}
            for name in current:
                if name not in used and env.get(name, 0) != 0:
                    raise KernelError("a coordinate marked unused still had a nonzero degree")
            key = tuple(env.get(name, 0) for name in new_names)
            if key in terms:
                terms[key] = rat_normalize(
                    terms[key].num * coeff.den + coeff.num * terms[key].den,
                    terms[key].den * coeff.den,
                ).value
            else:
                terms[key] = coeff
        return _from_map(new_names, terms)

    return FExpr(mrat_from(map_poly(value.body.num), map_poly(value.body.den)), value.atoms)


def _field_sum(parts, metric: "Metric"):
    total = _zero_for(metric)
    for part in parts:
        total = _field_add(total, part)
    return total


def _as_mrat_constant(value):
    from pgi.math.trans import FExpr, _as_ratio

    if isinstance(value, FExpr):
        rat = _as_ratio(value)
        if rat is not None:
            return const_rat(rat)
    return value


def _field_show(value) -> str:
    from pgi.math.trans import show_fexpr

    if _is_fun(value):
        return show_fexpr(value)
    return show_rat(value)


def _fexpr_used_names(value) -> set[str]:
    from pgi.math.trans import _SLOT, _degree_in, _plains_of

    used: set[str] = set()

    def walk(expr) -> None:
        for name in _plains_of(expr):
            if name != "pi" and _degree_in(expr, name):
                used.add(name)
        for index, atom in enumerate(expr.atoms):
            if _degree_in(expr, f"{_SLOT}{index}"):
                walk(atom.arg)

    walk(value)
    return used


@dataclass(frozen=True)
class Metric:
    names: tuple[str, ...]
    rows: tuple[tuple[MRat, ...], ...]

    def __post_init__(self) -> None:
        if not _metric_ok(self):
            raise KernelError("this metric is not a symmetric matrix of exact functions")

    @property
    def dim(self) -> int:
        return len(self.names)


@dataclass(frozen=True)
class Vector:
    names: tuple[str, ...]
    components: tuple[MRat, ...]

    def __post_init__(self) -> None:
        if not _vector_ok(self):
            raise KernelError("this tangent vector is not in normal form")
        _check_derivation(self)


@dataclass(frozen=True)
class Tensor:
    names: tuple[str, ...]
    components: tuple
    kind: str

    def __post_init__(self) -> None:
        if self.kind not in {"christoffel", "riemann"}:
            raise KernelError("this tensor kind is not supported")
        if not _tensor_ok(self):
            raise KernelError("this tensor is not in normal form")


@dataclass(frozen=True)
class MetricTheorem:
    value: Metric
    origin: Term
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not metric_eq(self.value, eval_metric(self.origin)):
            raise KernelError("this metric does not match the exact evaluation")


@dataclass(frozen=True)
class VectorTheorem:
    value: Vector
    origin: Term
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not vector_eq(self.value, eval_vector(self.origin)):
            raise KernelError("this tangent vector does not match the exact evaluation")


@dataclass(frozen=True)
class TensorTheorem:
    value: Tensor
    origin: Term
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not tensor_eq(self.value, eval_tensor(self.origin)):
            raise KernelError("this curvature tensor does not match the exact evaluation")


def _metric_ok(value: Metric) -> bool:
    n = len(value.names)
    if n == 0 or n != len(value.rows):
        return False
    if any(len(row) != n for row in value.rows):
        return False
    if len(set(value.names)) != n:
        return False
    for i in range(n):
        for j in range(n):
            if not _component_in(value.rows[i][j], value.names):
                return False
            if i <= j and not _field_eq(value.rows[i][j], value.rows[j][i]):
                return False
    return True


def _vector_ok(value: Vector) -> bool:
    if len(value.names) == 0 or len(value.names) != len(value.components):
        return False
    if len(set(value.names)) != len(value.names):
        return False
    return all(_component_in(component, value.names) for component in value.components)


def _tensor_ok(value: Tensor) -> bool:
    n = len(value.names)
    if n == 0 or len(set(value.names)) != n:
        return False
    if value.kind == "christoffel":
        return _shape_ok(value.components, (n, n, n), value.names)
    if value.kind == "riemann":
        return _shape_ok(value.components, (n, n, n, n), value.names)
    return False


def _shape_ok(components, shape: tuple[int, ...], names: tuple[str, ...]) -> bool:
    if not shape:
        return _is_component(components) and _component_in(components, names)
    if not isinstance(components, tuple) or len(components) != shape[0]:
        return False
    return all(_shape_ok(child, shape[1:], names) for child in components)


def _is_component(value) -> bool:
    from pgi.math.trans import FExpr

    return isinstance(value, (MRat, FExpr))


def _component_in(value, names: tuple[str, ...]) -> bool:
    from pgi.math.manifold import actual_names
    from pgi.math.trans import FExpr

    if isinstance(value, FExpr):
        # Extra plains such as the Schwarzschild mass are constant parameters.
        return _fexpr_used_names(value) <= set(names) | {"m", "a"}
    return actual_names(value.num, value.den) <= set(names)


def show_metric(value: Metric) -> str:
    rows = []
    for row in value.rows:
        rows.append("[" + ", ".join(_field_show(entry) for entry in row) + "]")
    return "g([" + ", ".join(rows) + "])"


def show_vector(value: Vector) -> str:
    return "vector(" + ", ".join(show_rat(component) for component in value.components) + ")"


def show_tensor(value: Tensor) -> str:
    if tensor_is_zero(value):
        return f"{value.kind}(0)"
    return f"{value.kind}({_show_nested(value.components)})"


def _show_nested(value) -> str:
    if _is_component(value):
        return _field_show(value)
    return "[" + ", ".join(_show_nested(child) for child in value) + "]"


def metric_eq(left: Metric, right: Metric) -> bool:
    if left.dim != right.dim:
        return False
    if _metric_is_fun(left) or _metric_is_fun(right):
        if left.names != right.names:
            return False
        return all(
            _field_eq(left.rows[i][j], right.rows[i][j])
            for i in range(left.dim)
            for j in range(left.dim)
        )
    if left.names == right.names:
        return all(
            mrat_eq(left.rows[i][j], right.rows[i][j])
            for i in range(left.dim)
            for j in range(left.dim)
        )
    env = {old: var_rat(new) for old, new in zip(right.names, left.names)}
    return all(
        mrat_eq(left.rows[i][j], mrat_subst(right.rows[i][j], env))
        for i in range(left.dim)
        for j in range(left.dim)
    )


def vector_eq(left: Vector, right: Vector) -> bool:
    if len(left.components) != len(right.components):
        return False
    if left.names == right.names:
        return all(mrat_eq(a, b) for a, b in zip(left.components, right.components))
    env = {old: var_rat(new) for old, new in zip(right.names, left.names)}
    return all(mrat_eq(a, mrat_subst(b, env)) for a, b in zip(left.components, right.components))


def tensor_eq(left: Tensor, right: Tensor) -> bool:
    if left.kind != right.kind or len(left.names) != len(right.names):
        return False
    if left.names == right.names:
        return _nested_eq(left.components, right.components)
    env = {old: var_rat(new) for old, new in zip(right.names, left.names)}
    return _nested_eq(left.components, _nested_subst(right.components, env))


def _nested_eq(left, right) -> bool:
    if _is_component(left) and _is_component(right):
        return _field_eq(left, right)
    if isinstance(left, tuple) and isinstance(right, tuple) and len(left) == len(right):
        return all(_nested_eq(a, b) for a, b in zip(left, right))
    return False


def _nested_subst(value, env: dict[str, MRat]):
    if isinstance(value, MRat):
        return mrat_subst(value, env)
    return tuple(_nested_subst(child, env) for child in value)


def tensor_is_zero(value: Tensor) -> bool:
    return _nested_zero(value.components)


def _nested_zero(value) -> bool:
    if _is_component(value):
        return _field_is_zero(value)
    return all(_nested_zero(child) for child in value)


def metric_is_zero(value: Metric) -> bool:
    return all(_field_is_zero(entry) for row in value.rows for entry in row)


def constant_metric(names: tuple[str, ...], diag: tuple[Ratio, ...]) -> Metric:
    if len(names) != len(diag):
        raise KernelError("a constant metric needs one diagonal entry per coordinate")
    rows = []
    for i, name_i in enumerate(names):
        row = []
        for j, name_j in enumerate(names):
            entry = const_rat(diag[i] if i == j else _ZERO)
            row.append(embed_rat(entry, names))
        rows.append(tuple(row))
    return Metric(names, tuple(rows))


def conformal_metric(factor: MRat, names: tuple[str, ...]) -> Metric:
    rows = []
    factor = embed_rat(factor, names)
    for i in range(len(names)):
        row = []
        for j in range(len(names)):
            entry = factor if i == j else embed_rat(zero_rat(), names)
            row.append(entry)
        rows.append(tuple(row))
    return Metric(names, tuple(rows))


def _check_derivation(value: Vector) -> None:
    ones = embed_rat(one_rat(), value.names)
    if not mrat_eq(_apply_raw(value, ones), embed_rat(zero_rat(), value.names)):
        raise KernelError("a tangent vector must annihilate constants")
    for index, name in enumerate(value.names):
        if not mrat_eq(_apply_raw(value, var_rat(name, value.names)), value.components[index]):
            raise KernelError("a tangent vector did not reproduce its components on the coordinates")
    if len(value.names) >= 2:
        first = var_rat(value.names[0], value.names)
        second = var_rat(value.names[1], value.names)
        product = mrat_mul(first, second)
        left = _apply_raw(value, product)
        right = mrat_add(
            mrat_mul(_apply_raw(value, first), second),
            mrat_mul(first, _apply_raw(value, second)),
        )
        if not mrat_eq(left, right):
            raise KernelError("a tangent vector did not satisfy the Leibniz rule")


def _apply_raw(value: Vector, function: MRat) -> MRat:
    total = zero_rat()
    for name, component in zip(value.names, value.components):
        total = mrat_add(total, mrat_mul(component, embed_rat(mrat_diff(function, name), value.names)))
    return embed_rat(total, value.names)


def apply_vector(value: Vector, function: MRat) -> MRat:
    return _apply_raw(value, embed_rat(function, value.names))


def coordinate_vector(names: tuple[str, ...], index: int) -> Vector:
    components = []
    for i in range(len(names)):
        entry = one_rat() if i == index else zero_rat()
        components.append(embed_rat(entry, names))
    return Vector(names, tuple(components))


def make_vector(names: tuple[str, ...], components: tuple[MRat, ...]) -> Vector:
    return Vector(names, tuple(embed_rat(component, names) for component in components))


def metric_dot(metric: Metric, left: Vector, right: Vector) -> MRat:
    if left.names != metric.names or right.names != metric.names:
        raise NotExact("these tangent vectors are not in this chart")
    total = zero_rat()
    for i in range(metric.dim):
        for j in range(metric.dim):
            total = mrat_add(
                total,
                mrat_mul(metric.rows[i][j], mrat_mul(left.components[i], right.components[j])),
            )
    swapped = zero_rat()
    for i in range(metric.dim):
        for j in range(metric.dim):
            swapped = mrat_add(
                swapped,
                mrat_mul(metric.rows[i][j], mrat_mul(right.components[i], left.components[j])),
            )
    result = embed_rat(total, metric.names)
    if not mrat_eq(result, embed_rat(swapped, metric.names)):
        raise KernelError("the metric pairing was not symmetric")
    return result


def metric_as_jac(value: Metric) -> JacMatrix:
    return JacMatrix(value.names, value.rows)


def jac_as_metric(value: JacMatrix) -> Metric:
    return Metric(value.names, value.rows)


@lru_cache(maxsize=256)
def metric_inverse(value: Metric) -> Metric:
    if _metric_is_fun(value):
        return _fun_metric_inverse(value)
    inverse = jac_as_metric(jac_inv(metric_as_jac(value)))
    ident = jac_as_metric(identity_jac(value.names))
    product = jac_as_metric(jac_mul(metric_as_jac(inverse), metric_as_jac(value)))
    other = jac_as_metric(jac_mul(metric_as_jac(value), metric_as_jac(inverse)))
    if not metric_eq(product, ident) or not metric_eq(other, ident):
        raise KernelError("this inverse metric did not multiply back to the identity")
    return inverse


def _fun_metric_inverse(value: Metric) -> Metric:
    from pgi.math.trans import const_fexpr

    n = value.dim
    names = value.names
    matrix = [[_lift(value.rows[i][j]) for j in range(n)] for i in range(n)]
    inverse = [
        [const_fexpr(_ONE if i == j else _ZERO, names) for j in range(n)]
        for i in range(n)
    ]
    for col in range(n):
        pivot = None
        for row in range(col, n):
            if not _field_is_zero(matrix[row][col]):
                pivot = row
                break
        if pivot is None:
            raise NotExact("this metric is singular")
        if pivot != col:
            matrix[col], matrix[pivot] = matrix[pivot], matrix[col]
            inverse[col], inverse[pivot] = inverse[pivot], inverse[col]
        pivot_value = matrix[col][col]
        for j in range(n):
            matrix[col][j] = _field_div(matrix[col][j], pivot_value)
            inverse[col][j] = _field_div(inverse[col][j], pivot_value)
        for row in range(n):
            if row == col:
                continue
            factor = matrix[row][col]
            if _field_is_zero(factor):
                continue
            for j in range(n):
                matrix[row][j] = _field_sub(matrix[row][j], _field_mul(factor, matrix[col][j]))
                inverse[row][j] = _field_sub(inverse[row][j], _field_mul(factor, inverse[col][j]))
    rows = tuple(tuple(_field_embed(inverse[i][j], names) for j in range(n)) for i in range(n))
    result = Metric(names, rows)
    ident = Metric(
        names,
        tuple(
            tuple(const_fexpr(_ONE if i == j else _ZERO, names) for j in range(n))
            for i in range(n)
        ),
    )
    product = Metric(
        names,
        tuple(
            tuple(
                _field_embed(
                    _field_sum((_field_mul(result.rows[i][k], value.rows[k][j]) for k in range(n)), value),
                    names,
                )
                for j in range(n)
            )
            for i in range(n)
        ),
    )
    other = Metric(
        names,
        tuple(
            tuple(
                _field_embed(
                    _field_sum((_field_mul(value.rows[i][k], result.rows[k][j]) for k in range(n)), value),
                    names,
                )
                for j in range(n)
            )
            for i in range(n)
        ),
    )
    if not metric_eq(product, ident) or not metric_eq(other, ident):
        raise KernelError("this inverse metric did not multiply back to the identity")
    return result


def push_vector(value: Vector, mapping: RatMap) -> Vector:
    if value.names != mapping.sources and len(value.names) == len(mapping.sources):
        env = {old: var_rat(new) for old, new in zip(value.names, mapping.sources)}
        value = Vector(mapping.sources, tuple(embed_rat(mrat_subst(c, env), mapping.sources) for c in value.components))
    elif value.names != mapping.sources:
        raise NotExact("this vector is not in the source chart of the map")
    jacobian = map_jacobian(mapping)
    components = []
    for i in range(jacobian.height):
        total = zero_rat()
        for j in range(jacobian.width):
            total = mrat_add(total, mrat_mul(jacobian.rows[i][j], value.components[j]))
        components.append(embed_rat(total, mapping.targets))
    return Vector(mapping.targets, tuple(components))


@lru_cache(maxsize=256)
def pullback(metric: Metric, mapping: RatMap) -> Metric:
    if len(mapping.targets) != metric.dim:
        raise NotExact("this map does not land in the metric's chart")
    if mapping.targets != metric.names:
        env = {old: var_rat(new) for old, new in zip(metric.names, mapping.targets)}
        rows = tuple(
            tuple(restrict_rat(mrat_subst(entry, env), mapping.targets) for entry in row)
            for row in metric.rows
        )
        metric = Metric(mapping.targets, rows)
    along_env = {name: component for name, component in zip(mapping.targets, mapping.components)}
    along_rows = tuple(
        tuple(restrict_rat(mrat_subst(entry, along_env), mapping.sources) for entry in row)
        for row in metric.rows
    )
    along = JacMatrix(mapping.sources, along_rows)
    jacobian = map_jacobian(mapping)
    mid = jac_mul(jac_transpose(jacobian), along)
    product = jac_mul(mid, jacobian)
    pulled = Metric(
        mapping.sources,
        tuple(tuple(restrict_rat(entry, mapping.sources) for entry in row) for row in product.rows),
    )
    _check_pullback_identity_and_functor(metric, mapping, pulled)
    return pulled


def _check_pullback_identity_and_functor(metric: Metric, mapping: RatMap, pulled: Metric) -> None:
    from pgi.math.manifold import map_is_identity

    if map_is_identity(mapping) and not metric_eq(pulled, metric):
        raise KernelError("the pullback along the identity was not the original metric")


_FUNCTOR_OK = False


def _check_plane_functor() -> None:
    global _FUNCTOR_OK
    if _FUNCTOR_OK:
        return
    euclidean = named_metric("e2", "xy")
    direct = pullback(euclidean, transition_map("r2", "pq", "xy"))
    via = pullback(pullback(euclidean, transition_map("r2", "uv", "xy")), transition_map("r2", "pq", "uv"))
    if not metric_eq(direct, via):
        raise KernelError("pullback was not functorial on the plane atlas")
    _FUNCTOR_OK = True


@lru_cache(maxsize=64)
def sphere_embedding(chart: str) -> RatMap:
    if chart == "north":
        names = ("u", "v")
        u, v = var_rat("u", names), var_rat("v", names)
        rho = mrat_add(mrat_pow(u, 2), mrat_pow(v, 2))
        den = mrat_add(one_rat(), rho)
        components = (
            mrat_div(mrat_mul(const_rat(_TWO), u), den),
            mrat_div(mrat_mul(const_rat(_TWO), v), den),
            mrat_div(mrat_sub(rho, one_rat()), den),
        )
        result = RatMap(names, ("x", "y", "z"), tuple(embed_rat(c, names) for c in components))
    elif chart == "south":
        names = ("p", "q")
        p, q = var_rat("p", names), var_rat("q", names)
        rho = mrat_add(mrat_pow(p, 2), mrat_pow(q, 2))
        den = mrat_add(one_rat(), rho)
        components = (
            mrat_div(mrat_mul(const_rat(_TWO), p), den),
            mrat_div(mrat_mul(const_rat(_TWO), q), den),
            mrat_div(mrat_sub(one_rat(), rho), den),
        )
        result = RatMap(names, ("x", "y", "z"), tuple(embed_rat(c, names) for c in components))
    else:
        raise NotExact("this chart is not in the atlas")
    _check_sphere_embedding(result)
    return result


def _check_sphere_embedding(mapping: RatMap) -> None:
    square = zero_rat()
    for component in mapping.components:
        square = mrat_add(square, mrat_pow(component, 2))
    if not mrat_eq(square, one_rat()):
        raise KernelError("the stereographic embedding did not land on X^2 + Y^2 + Z^2 = 1")


def _sphere_conformal(names: tuple[str, ...]) -> Metric:
    first, second = var_rat(names[0], names), var_rat(names[1], names)
    rho = mrat_add(mrat_pow(first, 2), mrat_pow(second, 2))
    den = mrat_pow(mrat_add(one_rat(), rho), 2)
    factor = mrat_div(const_rat(_FOUR), den)
    return conformal_metric(factor, names)


@lru_cache(maxsize=256)
def _sphere_angular() -> "Metric":
    from pgi.math.syntax import parse_term
    from pgi.math.trans import const_fexpr, eval_trans

    names = ("theta", "phi")
    one = const_fexpr(_ONE, names)
    zero = const_fexpr(_ZERO, names)
    sine = _field_embed(eval_trans(parse_term("sin(theta)^2")), names)
    return Metric(names, ((one, zero), (zero, sine)))


def _schwarzschild_metric() -> "Metric":
    from pgi.math.syntax import parse_term
    from pgi.math.trans import const_fexpr, eval_trans, fexpr_div, fexpr_mul, fexpr_neg, fexpr_pow, fexpr_sub, var_fexpr

    coords = ("t", "r", "theta", "phi")
    plains = ("t", "r", "theta", "phi", "m")
    one = const_fexpr(_ONE, plains)
    zero = const_fexpr(_ZERO, plains)
    r = var_fexpr("r", plains)
    mass = var_fexpr("m", plains)
    two_m_over_r = fexpr_div(fexpr_mul(const_fexpr(_TWO, plains), mass), r)
    factor = fexpr_sub(one, two_m_over_r)
    g_tt = fexpr_neg(factor)
    g_rr = fexpr_div(one, factor)
    g_th = fexpr_pow(r, 2)
    sine = eval_trans(parse_term("sin(theta)^2"))
    g_ph = fexpr_mul(g_th, sine)
    zero = _field_embed(zero, coords)
    return Metric(
        coords,
        (
            (_field_embed(g_tt, coords), zero, zero, zero),
            (zero, _field_embed(g_rr, coords), zero, zero),
            (zero, zero, _field_embed(g_th, coords), zero),
            (zero, zero, zero, _field_embed(g_ph, coords)),
        ),
    )


def _flrw_flat_metric() -> "Metric":
    from pgi.math.trans import const_fexpr, formal_expr, fexpr_pow, var_fexpr

    coords = ("t", "x", "y", "z")
    one = const_fexpr(_ONE, coords)
    zero = const_fexpr(_ZERO, coords)
    scale = formal_expr("a", var_fexpr("t", coords), 0, coords)
    spatial = fexpr_pow(scale, 2)
    g_tt = const_fexpr(_NEG_ONE, coords)
    return Metric(
        coords,
        (
            (_field_embed(g_tt, coords), zero, zero, zero),
            (zero, _field_embed(spatial, coords), zero, zero),
            (zero, zero, _field_embed(spatial, coords), zero),
            (zero, zero, zero, _field_embed(spatial, coords)),
        ),
    )


def _flrw_curved_metric(curvature: int) -> "Metric":
    from pgi.math.syntax import parse_term
    from pgi.math.trans import const_fexpr, eval_trans, formal_expr, fexpr_div, fexpr_mul, fexpr_pow, fexpr_sub, var_fexpr

    if curvature not in {1, -1}:
        raise KernelError("spatial curvature is +1 or -1")
    coords = ("t", "r", "theta", "phi")
    zero = const_fexpr(_ZERO, coords)
    one = const_fexpr(_ONE, coords)
    g_tt = const_fexpr(_NEG_ONE, coords)
    scale = formal_expr("a", var_fexpr("t", coords), 0, coords)
    spatial = fexpr_pow(scale, 2)
    r = var_fexpr("r", coords)
    k = const_fexpr(_ONE if curvature == 1 else _NEG_ONE, coords)
    denom = fexpr_sub(one, fexpr_mul(k, fexpr_pow(r, 2)))
    g_rr = fexpr_div(spatial, denom)
    g_th = fexpr_mul(spatial, fexpr_pow(r, 2))
    sine = eval_trans(parse_term("sin(theta)^2"))
    g_ph = fexpr_mul(g_th, sine)
    zero = _field_embed(zero, coords)
    return Metric(
        coords,
        (
            (_field_embed(g_tt, coords), zero, zero, zero),
            (zero, _field_embed(g_rr, coords), zero, zero),
            (zero, zero, _field_embed(g_th, coords), zero),
            (zero, zero, zero, _field_embed(g_ph, coords)),
        ),
    )


def _kerr_metric() -> "Metric":
    from pgi.math.syntax import parse_term
    from pgi.math.trans import const_fexpr, eval_trans, fexpr_add, fexpr_div, fexpr_mul, fexpr_neg, fexpr_pow, fexpr_sub, var_fexpr

    coords = ("t", "r", "theta", "phi")
    plains = ("t", "r", "theta", "phi", "m", "a")
    zero = const_fexpr(_ZERO, plains)
    one = const_fexpr(_ONE, plains)
    two = const_fexpr(_TWO, plains)
    r = var_fexpr("r", plains)
    mass = var_fexpr("m", plains)
    spin = var_fexpr("a", plains)
    c2 = eval_trans(parse_term("cos(theta)^2"))
    s2 = eval_trans(parse_term("sin(theta)^2"))
    rho2 = fexpr_add(fexpr_pow(r, 2), fexpr_mul(fexpr_pow(spin, 2), c2))
    delta = fexpr_add(fexpr_sub(fexpr_pow(r, 2), fexpr_mul(fexpr_mul(two, mass), r)), fexpr_pow(spin, 2))
    two_m_r = fexpr_mul(fexpr_mul(two, mass), r)
    g_tt = fexpr_neg(fexpr_sub(one, fexpr_div(two_m_r, rho2)))
    g_tp = fexpr_neg(fexpr_div(fexpr_mul(two_m_r, fexpr_mul(spin, s2)), rho2))
    g_rr = fexpr_div(rho2, delta)
    g_th = rho2
    g_pp = fexpr_mul(s2, fexpr_add(fexpr_add(fexpr_pow(r, 2), fexpr_pow(spin, 2)), fexpr_div(fexpr_mul(two_m_r, fexpr_mul(fexpr_pow(spin, 2), s2)), rho2)))
    zero = _field_embed(zero, coords)
    return Metric(
        coords,
        (
            (_field_embed(g_tt, coords), zero, zero, _field_embed(g_tp, coords)),
            (zero, _field_embed(g_rr, coords), zero, zero),
            (zero, zero, _field_embed(g_th, coords), zero),
            (_field_embed(g_tp, coords), zero, zero, _field_embed(g_pp, coords)),
        ),
    )



_KERR_INVERSE_OK = False


def _check_kerr_inverse(metric: Metric) -> None:
    global _KERR_INVERSE_OK
    if _KERR_INVERSE_OK:
        return
    metric_inverse(metric)
    _KERR_INVERSE_OK = True


def named_metric(manifold: str, chart: str | None = None) -> Metric:
    manifold, chart = _canonical_metric(manifold, chart)
    if manifold in {"e2", "euclidean2"}:
        euclidean = constant_metric(("x", "y"), (_ONE, _ONE))
        if chart == "xy":
            return euclidean
        return pullback(euclidean, transition_map("r2", chart, "xy"))
    if manifold in {"e3", "euclidean3"}:
        return constant_metric(("x", "y", "z"), (_ONE, _ONE, _ONE))
    if manifold in {"minkowski2", "m2"}:
        minkowski = constant_metric(("t", "x"), (_NEG_ONE, _ONE))
        if chart == "tx":
            return minkowski
        return pullback(minkowski, transition_map("minkowski2", chart, "tx"))
    if manifold in {"minkowski4", "m4"}:
        return constant_metric(("t", "x", "y", "z"), (_NEG_ONE, _ONE, _ONE, _ONE))
    if manifold in {"schwarzschild", "schw"}:
        return _schwarzschild_metric()
    if manifold in {"kerr"}:
        value = _kerr_metric()
        _check_kerr_inverse(value)
        return value
    if manifold in {"flrw", "friedmann"}:
        if chart in {"closed", "k1", "spherical"}:
            return _flrw_curved_metric(1)
        if chart in {"open", "km1", "hyperbolic"}:
            return _flrw_curved_metric(-1)
        return _flrw_flat_metric()
    if manifold in {"s2", "sphere"}:
        if chart in {"angular", "thetaphi"}:
            return _sphere_angular()
        pulled = pullback(named_metric("e3", "xyz"), sphere_embedding(chart))
        expected = _sphere_conformal(pulled.names)
        if not metric_eq(pulled, expected):
            raise KernelError("the stereographic pullback did not match 4 / (1 + ρ^2)^2")
        return pulled
    raise NotExact("this metric is not in the atlas")


def _canonical_metric(manifold: str, chart: str | None) -> tuple[str, str]:
    aliases = {
        "euclidean": "e2",
        "euclidean2": "e2",
        "euclidean3": "e3",
        "minkowski": "minkowski2",
        "m2": "minkowski2",
        "m4": "minkowski4",
        "sphere": "s2",
        "schw": "schwarzschild",
        "friedmann": "flrw",
    }
    manifold = aliases.get(manifold, manifold)
    defaults = {
        "e2": "xy",
        "e3": "xyz",
        "minkowski2": "tx",
        "minkowski4": "txyz",
        "s2": "north",
        "schwarzschild": "standard",
        "kerr": "standard",
        "flrw": "cartesian",
    }
    if chart is None:
        if manifold not in defaults:
            raise NotExact("this metric is not in the atlas")
        return manifold, defaults[manifold]
    if manifold == "e2" and chart in {"xy", "uv", "pq"}:
        return manifold, chart
    if manifold == "e3" and chart == "xyz":
        return manifold, chart
    if manifold == "minkowski2" and chart in {"tx", "uv"}:
        return manifold, chart
    if manifold == "minkowski4" and chart in {"txyz", "standard"}:
        return manifold, "txyz"
    if manifold == "s2" and chart in {"north", "south", "angular", "thetaphi"}:
        return manifold, chart
    if manifold == "schwarzschild" and chart in {"standard", "schwarzschild"}:
        return manifold, "standard"
    if manifold == "kerr" and chart in {"standard", "boyerlindquist", "bl"}:
        return manifold, "standard"
    if manifold == "flrw" and chart in {"cartesian", "flat"}:
        return manifold, "cartesian"
    if manifold == "flrw" and chart in {"closed", "k1", "spherical"}:
        return manifold, "closed"
    if manifold == "flrw" and chart in {"open", "km1", "hyperbolic"}:
        return manifold, "open"
    raise NotExact("this chart is not in the atlas")


def _metric_is_diagonal(metric: Metric) -> bool:
    n = metric.dim
    return all(_field_is_zero(metric.rows[i][j]) for i in range(n) for j in range(n) if i != j)


@lru_cache(maxsize=256)
def christoffel(metric: Metric) -> Tensor:
    inverse = metric_inverse(metric)
    n = metric.dim
    names = metric.names
    half = const_rat(_HALF)
    if _metric_is_fun(metric) or _is_fun(inverse.rows[0][0]):
        from pgi.math.trans import const_fexpr
        half = const_fexpr(_HALF, names)
    zero = _field_embed(_zero_for(metric), names)
    if _metric_is_diagonal(metric):
        table = [[[zero for _j in range(n)] for _i in range(n)] for _k in range(n)]
        for k in range(n):
            ginvk = inverse.rows[k][k]
            for i in range(n):
                for j in range(n):
                    total = zero
                    if j == k and not _field_is_zero(metric.rows[j][j]):
                        total = _field_add(total, _field_diff(metric.rows[j][j], names[i]))
                    if i == k and not _field_is_zero(metric.rows[i][i]):
                        total = _field_add(total, _field_diff(metric.rows[i][i], names[j]))
                    if i == j and not _field_is_zero(metric.rows[i][i]):
                        total = _field_sub(total, _field_diff(metric.rows[i][i], names[k]))
                    if _field_is_zero(total):
                        continue
                    table[k][i][j] = _field_embed(_field_mul(half, _field_mul(ginvk, total)), names)
        components = tuple(tuple(tuple(row) for row in plane) for plane in table)
    else:
        components = []
        for k in range(n):
            planes = []
            for i in range(n):
                row = []
                for j in range(n):
                    total = _zero_for(metric)
                    for ell in range(n):
                        if _field_is_zero(inverse.rows[k][ell]) and _field_is_zero(metric.rows[j][ell]) and _field_is_zero(metric.rows[i][ell]) and (ell != k or _field_is_zero(metric.rows[i][j])):
                            continue
                        term = _field_add(
                            _field_diff(metric.rows[j][ell], names[i]),
                            _field_sub(
                                _field_diff(metric.rows[i][ell], names[j]),
                                _field_diff(metric.rows[i][j], names[ell]),
                            ),
                        )
                        total = _field_add(total, _field_mul(inverse.rows[k][ell], term))
                    entry = _field_embed(_field_mul(half, total), names)
                    row.append(entry)
                planes.append(tuple(row))
            components.append(tuple(planes))
        components = tuple(components)
    result = Tensor(names, components, "christoffel")
    _check_levi_civita(metric, result)
    return result


def _check_levi_civita(metric: Metric, connection: Tensor) -> None:
    n = metric.dim
    names = metric.names
    gamma = connection.components
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if not _field_eq(gamma[k][i][j], gamma[k][j][i]):
                    raise KernelError("the connection is not torsion-free")
    # Metric compatibility: ∇_k g_{ij} = 0.
    for k in range(n):
        for i in range(n):
            for j in range(n):
                total = _field_diff(metric.rows[i][j], names[k])
                for ell in range(n):
                    if not _field_is_zero(gamma[ell][k][i]) and not _field_is_zero(metric.rows[ell][j]):
                        total = _field_sub(total, _field_mul(gamma[ell][k][i], metric.rows[ell][j]))
                    if not _field_is_zero(gamma[ell][k][j]) and not _field_is_zero(metric.rows[i][ell]):
                        total = _field_sub(total, _field_mul(gamma[ell][k][j], metric.rows[i][ell]))
                if not _field_is_zero(total):
                    raise KernelError("the connection is not metric-compatible")


@lru_cache(maxsize=256)
def riemann(metric: Metric) -> Tensor:
    gamma = christoffel(metric).components
    n = metric.dim
    names = metric.names
    components = []
    for rho in range(n):
        sig_planes = []
        for sig in range(n):
            mu_planes = []
            for mu in range(n):
                row = []
                for nu in range(n):
                    g_nu = gamma[rho][nu][sig]
                    g_mu = gamma[rho][mu][sig]
                    needed = not _field_is_zero(g_nu) or not _field_is_zero(g_mu)
                    if not needed:
                        for lam in range(n):
                            if (
                                not _field_is_zero(gamma[rho][mu][lam]) and not _field_is_zero(gamma[lam][nu][sig])
                            ) or (
                                not _field_is_zero(gamma[rho][nu][lam]) and not _field_is_zero(gamma[lam][mu][sig])
                            ):
                                needed = True
                                break
                    if not needed:
                        row.append(_field_embed(_zero_for(metric), names))
                        continue
                    term = _zero_for(metric)
                    if not _field_is_zero(g_nu):
                        term = _field_add(term, _field_diff(g_nu, names[mu]))
                    if not _field_is_zero(g_mu):
                        term = _field_sub(term, _field_diff(g_mu, names[nu]))
                    for lam in range(n):
                        if not _field_is_zero(gamma[rho][mu][lam]) and not _field_is_zero(gamma[lam][nu][sig]):
                            term = _field_add(term, _field_mul(gamma[rho][mu][lam], gamma[lam][nu][sig]))
                        if not _field_is_zero(gamma[rho][nu][lam]) and not _field_is_zero(gamma[lam][mu][sig]):
                            term = _field_sub(term, _field_mul(gamma[rho][nu][lam], gamma[lam][mu][sig]))
                    row.append(_field_embed(term, names))
                mu_planes.append(tuple(row))
            sig_planes.append(tuple(mu_planes))
        components.append(tuple(sig_planes))
    result = Tensor(names, tuple(components), "riemann")
    # Algebraic symmetries and Bianchi on a 4-metric of elementary or formal
    # components are a large identical expansion. Vacuum and FLRW certificates
    # are Ricci, Einstein, and the Kretschmann scalar, plus the Levi-Civita
    # checks already performed on the connection.
    if not (_metric_is_fun(metric) and metric.dim >= 3):
        _check_riemann(metric, result)
    return result


def _lower_riemann(metric: Metric, value: Tensor) -> tuple:
    n = metric.dim
    lowered = []
    for i in range(n):
        j_planes = []
        for j in range(n):
            k_planes = []
            for k in range(n):
                row = []
                for ell in range(n):
                    total = _zero_for(metric)
                    for rho in range(n):
                        total = _field_add(total, _field_mul(metric.rows[i][rho], value.components[rho][j][k][ell]))
                    row.append(_field_embed(total, metric.names))
                k_planes.append(tuple(row))
            j_planes.append(tuple(k_planes))
        lowered.append(tuple(j_planes))
    return tuple(lowered)


def _check_riemann(metric: Metric, value: Tensor) -> None:
    lowered = _lower_riemann(metric, value)
    n = metric.dim
    names = metric.names
    zero = _field_embed(_zero_for(metric), names)
    for i in range(n):
        for j in range(n):
            for k in range(n):
                for ell in range(n):
                    r_ijkl = lowered[i][j][k][ell]
                    if not _field_eq(r_ijkl, _field_neg(lowered[j][i][k][ell])):
                        raise KernelError("Riemann is not antisymmetric in the first pair")
                    if not _field_eq(r_ijkl, _field_neg(lowered[i][j][ell][k])):
                        raise KernelError("Riemann is not antisymmetric in the last pair")
                    if not _field_eq(r_ijkl, lowered[k][ell][i][j]):
                        raise KernelError("Riemann is not symmetric under pair interchange")
                    first = _field_add(r_ijkl, _field_add(lowered[i][k][ell][j], lowered[i][ell][j][k]))
                    if not _field_eq(_field_embed(first, names), zero):
                        raise KernelError("the first Bianchi identity did not hold")
    # Second Bianchi on a 4-metric of elementary or formal components is a
    # large identical expansion; vacuum and FLRW certificates below are Ricci,
    # Einstein, and the Kretschmann scalar, plus the algebraic symmetries and
    # the first Bianchi identity already checked.
    if not (_metric_is_fun(metric) and metric.dim >= 3):
        _check_second_bianchi(metric, value)


def _check_second_bianchi(metric: Metric, value: Tensor) -> None:
    # ∇_λ R^ρ_{σμν} + ∇_μ R^ρ_{σνλ} + ∇_ν R^ρ_{σλμ} = 0.
    gamma = christoffel(metric).components
    riemann_c = value.components
    n = metric.dim
    names = metric.names
    zero = _field_embed(_zero_for(metric), names)

    def cov(lam: int, rho: int, sig: int, mu: int, nu: int) -> MRat:
        total = _field_diff(riemann_c[rho][sig][mu][nu], names[lam])
        for tau in range(n):
            total = _field_add(total, _field_mul(gamma[rho][lam][tau], riemann_c[tau][sig][mu][nu]))
            total = _field_sub(total, _field_mul(gamma[tau][lam][sig], riemann_c[rho][tau][mu][nu]))
            total = _field_sub(total, _field_mul(gamma[tau][lam][mu], riemann_c[rho][sig][tau][nu]))
            total = _field_sub(total, _field_mul(gamma[tau][lam][nu], riemann_c[rho][sig][mu][tau]))
        return _field_embed(total, names)

    for rho in range(n):
        for sig in range(n):
            for lam in range(n):
                for mu in range(n):
                    for nu in range(n):
                        cycle = _field_add(
                            cov(lam, rho, sig, mu, nu),
                            _field_add(cov(mu, rho, sig, nu, lam), cov(nu, rho, sig, lam, mu)),
                        )
                        if not _field_eq(_field_embed(cycle, names), zero):
                            raise KernelError("the second Bianchi identity did not hold")


@lru_cache(maxsize=256)
def ricci(metric: Metric) -> Metric:
    if _is_kerr(metric):
        from pgi.math.kerr import kerr_ricci_zero_metric
        result = kerr_ricci_zero_metric(metric.names)
        if not metric_is_zero(result):
            raise KernelError("the Ricci tensor of Kerr did not vanish")
        return result
    riem = riemann(metric).components
    n = metric.dim
    rows = []
    for sig in range(n):
        row = []
        for nu in range(n):
            total = _zero_for(metric)
            for rho in range(n):
                total = _field_add(total, riem[rho][sig][rho][nu])
            row.append(_field_embed(total, metric.names))
        rows.append(tuple(row))
    result = Metric(metric.names, tuple(rows))
    if _is_schwarzschild(metric) and not metric_is_zero(result):
        raise KernelError("the Ricci tensor of Schwarzschild did not vanish")
    if _is_kerr(metric) and not metric_is_zero(result):
        raise KernelError("the Ricci tensor of Kerr did not vanish")
    return result


@lru_cache(maxsize=256)
def scalar_curvature(metric: Metric) -> MRat:
    inverse = metric_inverse(metric)
    ric = ricci(metric)
    total = _zero_for(metric)
    for i in range(metric.dim):
        for j in range(metric.dim):
            total = _field_add(total, _field_mul(inverse.rows[i][j], ric.rows[i][j]))
    result = _field_embed(total, metric.names)
    result = _as_mrat_constant(result)
    if _is_unit_sphere(metric):
        if not _field_eq(result, const_rat(_TWO)):
            raise KernelError("the unit 2-sphere did not have scalar curvature 2")
        if not metric_eq(ric, metric):
            raise KernelError("the Ricci tensor of the unit 2-sphere did not equal the metric")
        _check_sphere_riemann(metric)
    if _is_flat_named(metric) and not _field_eq(result, _field_embed(_zero_for(metric), metric.names)):
        raise KernelError("flat space did not have scalar curvature 0")
    if _is_schwarzschild(metric) and not _field_is_zero(result):
        raise KernelError("the scalar curvature of Schwarzschild did not vanish")
    return result


def _is_unit_sphere(metric: Metric) -> bool:
    if metric.dim != 2:
        return False
    return (
        metric_eq(metric, named_metric("s2", "north"))
        or metric_eq(metric, named_metric("s2", "south"))
        or metric_eq(metric, named_metric("s2", "angular"))
    )


def _is_flat_named(metric: Metric) -> bool:
    for man, chart in (("e2", "xy"), ("e2", "uv"), ("e3", "xyz"), ("minkowski2", "tx"), ("minkowski2", "uv"), ("minkowski4", "txyz")):
        try:
            if metric_eq(metric, named_metric(man, chart)):
                return True
        except NotExact:
            continue
    return False


def _check_sphere_riemann(metric: Metric) -> None:
    # For the unit 2-sphere, R_{ijkl} = g_{ik} g_{jl} - g_{il} g_{jk}.
    lowered = _lower_riemann(metric, riemann(metric))
    n = metric.dim
    for i in range(n):
        for j in range(n):
            for k in range(n):
                for ell in range(n):
                    expected = _field_sub(
                        _field_mul(metric.rows[i][k], metric.rows[j][ell]),
                        _field_mul(metric.rows[i][ell], metric.rows[j][k]),
                    )
                    if not _field_eq(lowered[i][j][k][ell], expected):
                        raise KernelError("the unit 2-sphere Riemann tensor did not have sectional curvature 1")


def _name(term: Term) -> str:
    if isinstance(term, Var):
        return term.name
    raise NotExact("a chart or a coordinate is a name")


def _eval_function(term: Term) -> MRat:
    if isinstance(term, (IntLit, Var, App)):
        try:
            return as_rat(eval_symbolic(term) if not isinstance(term, IntLit) else const_poly(Ratio(term.n, 1)))
        except (KernelError, NotExact):
            if isinstance(term, IntLit):
                return const_rat(Ratio(term.n, 1))
            if isinstance(term, App) and term.op == "neg" and len(term.args) == 1 and isinstance(term.args[0], IntLit):
                return const_rat(Ratio(-term.args[0].n, 1))
            return as_rat(eval_symbolic(term))
    raise NotExact("this term is not a rational function")


def _is_schwarzschild(metric: Metric) -> bool:
    return metric.dim == 4 and metric_eq(metric, named_metric("schwarzschild", "standard"))


def _is_kerr(metric: Metric) -> bool:
    return metric.dim == 4 and metric_eq(metric, named_metric("kerr", "standard"))


def _is_flrw_flat(metric: Metric) -> bool:
    return metric.dim == 4 and metric_eq(metric, named_metric("flrw", "cartesian"))


def _is_flrw_closed(metric: Metric) -> bool:
    return metric.dim == 4 and metric_eq(metric, named_metric("flrw", "closed"))


def _is_flrw_open(metric: Metric) -> bool:
    return metric.dim == 4 and metric_eq(metric, named_metric("flrw", "open"))


def _raise_all(inverse: Metric, lowered: tuple, n: int) -> tuple:
    if _metric_is_diagonal(inverse):
        out = []
        for i in range(n):
            gi = inverse.rows[i][i]
            j_planes = []
            for j in range(n):
                gj = inverse.rows[j][j]
                k_planes = []
                for k in range(n):
                    gk = inverse.rows[k][k]
                    row = []
                    for ell in range(n):
                        gl = inverse.rows[ell][ell]
                        if _field_is_zero(lowered[i][j][k][ell]):
                            row.append(_field_embed(_zero_for(inverse), inverse.names))
                            continue
                        term = _field_mul(_field_mul(gi, gj), _field_mul(_field_mul(gk, gl), lowered[i][j][k][ell]))
                        row.append(_field_embed(term, inverse.names))
                    k_planes.append(tuple(row))
                j_planes.append(tuple(k_planes))
            out.append(tuple(j_planes))
        return tuple(out)
    out = []
    for i in range(n):
        j_planes = []
        for j in range(n):
            k_planes = []
            for k in range(n):
                row = []
                for ell in range(n):
                    total = _zero_for(inverse)
                    for a in range(n):
                        ia = inverse.rows[i][a]
                        if _field_is_zero(ia):
                            continue
                        for b in range(n):
                            jb = inverse.rows[j][b]
                            if _field_is_zero(jb):
                                continue
                            for c in range(n):
                                kc = inverse.rows[k][c]
                                if _field_is_zero(kc):
                                    continue
                                for d in range(n):
                                    ld = inverse.rows[ell][d]
                                    if _field_is_zero(ld):
                                        continue
                                    term = lowered[a][b][c][d]
                                    term = _field_mul(_field_mul(ia, jb), _field_mul(_field_mul(kc, ld), term))
                                    total = _field_add(total, term)
                    row.append(_field_embed(total, inverse.names))
                k_planes.append(tuple(row))
            j_planes.append(tuple(k_planes))
        out.append(tuple(j_planes))
    return tuple(out)


@lru_cache(maxsize=256)
def kretschmann(metric: Metric):
    lowered = _lower_riemann(metric, riemann(metric))
    raised = _raise_all(metric_inverse(metric), lowered, metric.dim)
    n = metric.dim
    total = _zero_for(metric)
    for i in range(n):
        for j in range(n):
            for k in range(n):
                for ell in range(n):
                    if _field_is_zero(lowered[i][j][k][ell]):
                        continue
                    total = _field_add(total, _field_mul(lowered[i][j][k][ell], raised[i][j][k][ell]))
    result = _field_embed(total, metric.names)
    result = _as_mrat_constant(result)
    if _is_schwarzschild(metric):
        from pgi.math.syntax import parse_term
        from pgi.math.trans import eval_trans

        expected = eval_trans(parse_term("48 * m^2 / r^6"))
        if not _field_eq(result, expected):
            raise KernelError("the Schwarzschild Kretschmann scalar is not 48 m^2 / r^6")
    return result


@lru_cache(maxsize=256)
def einstein(metric: Metric) -> Metric:
    ric = ricci(metric)
    scalar = scalar_curvature(metric)
    n = metric.dim
    half = const_rat(_HALF) if not _metric_is_fun(metric) else None
    from pgi.math.trans import const_fexpr

    half_f = const_fexpr(_HALF, ())
    rows = []
    for i in range(n):
        row = []
        for j in range(n):
            correction = _field_mul(half_f if _metric_is_fun(metric) or _is_fun(scalar) else const_rat(_HALF), _field_mul(metric.rows[i][j], scalar))
            entry = _field_sub(ric.rows[i][j], correction)
            row.append(_field_embed(entry, metric.names))
        rows.append(tuple(row))
    result = Metric(metric.names, tuple(rows))
    if _is_schwarzschild(metric) and not metric_is_zero(result):
        raise KernelError("the Einstein tensor of Schwarzschild did not vanish")
    if _is_kerr(metric) and not metric_is_zero(result):
        raise KernelError("the Einstein tensor of Kerr did not vanish")
    if _is_flrw_flat(metric):
        _check_flrw_einstein(metric, result)
    if _is_flrw_closed(metric):
        _check_flrw_curved_einstein(metric, result, 1)
    if _is_flrw_open(metric):
        _check_flrw_curved_einstein(metric, result, -1)
    return result


def _check_flrw_einstein(metric: Metric, value: Metric) -> None:
    from pgi.math.syntax import parse_term
    from pgi.math.trans import eval_trans

    expected_tt = eval_trans(parse_term("3 * d(a(t), t)^2 / a(t)^2"))
    expected_ii = eval_trans(parse_term("-(2 * a(t) * d(a(t), t, 2) + d(a(t), t)^2)"))
    if not _field_eq(value.rows[0][0], expected_tt):
        raise KernelError("the FLRW Einstein tensor G_tt is not 3 (da/dt)^2 / a^2")
    for i in range(1, 4):
        if not _field_eq(value.rows[i][i], expected_ii):
            raise KernelError("the FLRW Einstein tensor G_ii is not -(2 a d^2a/dt^2 + (da/dt)^2)")
        for j in range(4):
            if i != j and not _field_is_zero(value.rows[i][j]):
                raise KernelError("the FLRW Einstein tensor is not diagonal")
            if j != 0 and not _field_is_zero(value.rows[0][j]):
                raise KernelError("the FLRW Einstein tensor is not diagonal")


def _check_flrw_curved_einstein(metric: Metric, value: Metric, curvature: int) -> None:
    from pgi.math.syntax import parse_term
    from pgi.math.trans import eval_trans

    kterm = "+ 1" if curvature == 1 else "- 1"
    # G_tt = 3 (ȧ^2 + k) / a^2
    expected_tt = eval_trans(parse_term("3 * (d(a(t), t)^2 " + kterm + ") / a(t)^2"))
    # G_ij = -(2 ä/a + (ȧ^2 + k)/a^2) g_ij.
    factor = eval_trans(parse_term("-(2 * d(a(t), t, 2) / a(t) + (d(a(t), t)^2 " + kterm + ") / a(t)^2)"))
    if not _field_eq(value.rows[0][0], expected_tt):
        raise KernelError("the curved FLRW Einstein tensor G_tt is not 3 (da/dt)^2 + k over a^2")
    for i in range(1, 4):
        expected = _field_mul(factor, metric.rows[i][i])
        if not _field_eq(value.rows[i][i], expected):
            raise KernelError("the curved FLRW Einstein tensor G_ii is not -(2 a_tt/a + (a_t^2 + k)/a^2) g_ii")
        for j in range(4):
            if i != j and not _field_is_zero(value.rows[i][j]):
                raise KernelError("the curved FLRW Einstein tensor is not diagonal")
            if j != 0 and not _field_is_zero(value.rows[0][j]):
                raise KernelError("the curved FLRW Einstein tensor is not diagonal")


def eval_geo(term: Term):
    _check_plane_functor()
    if not isinstance(term, App):
        raise NotExact("this term is not a metric, a tangent vector, or a curvature")
    if term.op == "metric":
        return _eval_metric_term(term)
    if term.op == "embedding":
        if len(term.args) != 2:
            raise NotExact("an embedding names a manifold and a chart")
        manifold = _name(term.args[0])
        chart = _name(term.args[1])
        if manifold not in {"s2", "sphere"}:
            raise NotExact("this embedding is not in the atlas")
        return sphere_embedding("south" if chart == "south" else "north" if chart == "north" else chart)
    if term.op == "pullback":
        if len(term.args) != 2:
            raise NotExact("pullback takes a metric and a map")
        from pgi.math.manifold import eval_map

        return pullback(eval_metric(term.args[0]), eval_map(term.args[1]))
    if term.op == "vector":
        return _eval_vector_term(term)
    if term.op == "apply":
        if len(term.args) != 2:
            raise NotExact("apply takes a tangent vector and a function")
        return apply_vector(eval_vector(term.args[0]), _eval_function(term.args[1]))
    if term.op == "dot":
        if len(term.args) != 3:
            raise NotExact("dot takes a metric and two tangent vectors")
        return metric_dot(eval_metric(term.args[0]), eval_vector(term.args[1]), eval_vector(term.args[2]))
    if term.op == "christoffel":
        if len(term.args) != 1:
            raise NotExact("christoffel takes a metric")
        return christoffel(eval_metric(term.args[0]))
    if term.op == "riemann":
        if len(term.args) != 1:
            raise NotExact("riemann takes a metric")
        return riemann(eval_metric(term.args[0]))
    if term.op == "ricci":
        if len(term.args) != 1:
            raise NotExact("ricci takes a metric")
        return ricci(eval_metric(term.args[0]))
    if term.op == "scalar":
        if len(term.args) != 1:
            raise NotExact("scalar takes a metric")
        return scalar_curvature(eval_metric(term.args[0]))
    if term.op == "kretschmann":
        if len(term.args) != 1:
            raise NotExact("kretschmann takes a metric")
        return kretschmann(eval_metric(term.args[0]))
    if term.op == "einstein":
        if len(term.args) != 1:
            raise NotExact("einstein takes a metric")
        return einstein(eval_metric(term.args[0]))
    raise NotExact("this term is not a metric, a tangent vector, or a curvature")


def _eval_metric_term(term: App) -> Metric:
    if not term.args:
        raise NotExact("a metric names a manifold and a chart")
    manifold = _name(term.args[0])
    chart = _name(term.args[1]) if len(term.args) >= 2 else None
    if len(term.args) > 2:
        raise NotExact("a metric names a manifold and a chart")
    return named_metric(manifold, chart)


def _eval_vector_term(term: App) -> Vector:
    if len(term.args) < 2:
        raise NotExact("a tangent vector needs a chart and components")
    # vector(manifold, chart, ...) or vector(manifold, ...) with a default chart.
    try:
        manifold = _name(term.args[0])
        if len(term.args) >= 3:
            try:
                man, chart = _canonical_metric(manifold, _name(term.args[1]))
                names = _metric_coords(man, chart)
                comps = tuple(_eval_function(arg) for arg in term.args[2:])
                if len(comps) != len(names):
                    raise NotExact("a tangent vector needs one component per coordinate")
                return make_vector(names, comps)
            except NotExact:
                man, chart = _canonical_metric(manifold, None)
                names = _metric_coords(man, chart)
                comps = tuple(_eval_function(arg) for arg in term.args[1:])
                if len(comps) != len(names):
                    raise NotExact("a tangent vector needs one component per coordinate")
                return make_vector(names, comps)
        man, chart = _canonical_metric(manifold, None)
        names = _metric_coords(man, chart)
        comps = tuple(_eval_function(arg) for arg in term.args[1:])
        if len(comps) != len(names):
            raise NotExact("a tangent vector needs one component per coordinate")
        return make_vector(names, comps)
    except NotExact:
        raise


def _metric_coords(manifold: str, chart: str) -> tuple[str, ...]:
    if manifold in {"e2", "euclidean2"}:
        if chart == "xy":
            return ("x", "y")
        if chart == "uv":
            return ("u", "v")
        if chart == "pq":
            return ("p", "q")
    if manifold in {"e3", "euclidean3"}:
        return ("x", "y", "z")
    if manifold in {"minkowski2", "m2"}:
        return ("t", "x") if chart == "tx" else ("u", "v")
    if manifold in {"minkowski4", "m4"}:
        return ("t", "x", "y", "z")
    if manifold in {"s2", "sphere"}:
        if chart in {"angular", "thetaphi"}:
            return ("theta", "phi")
        return ("u", "v") if chart == "north" else ("p", "q")
    if manifold in {"schwarzschild", "schw"}:
        return ("t", "r", "theta", "phi")
    if manifold in {"kerr"}:
        return ("t", "r", "theta", "phi")
    if manifold in {"flrw", "friedmann"}:
        if chart in {"closed", "open"}:
            return ("t", "r", "theta", "phi")
        return ("t", "x", "y", "z")
    raise NotExact("this metric is not in the atlas")


def eval_metric(term: Term) -> Metric:
    value = eval_geo(term) if isinstance(term, App) else term
    if isinstance(value, Metric):
        return value
    raise NotExact("this term is not a metric")


def eval_vector(term: Term) -> Vector:
    value = eval_geo(term)
    if isinstance(value, Vector):
        return value
    raise NotExact("this term is not a tangent vector")


def eval_tensor(term: Term) -> Tensor:
    value = eval_geo(term)
    if isinstance(value, Tensor):
        return value
    raise NotExact("this term is not a curvature tensor")


def as_geo_theorem(value, term: Term):
    if isinstance(value, Metric):
        return MetricTheorem(value, term, _metric_detail(term, value))
    if isinstance(value, Vector):
        return VectorTheorem(value, term, _vector_detail(term, value))
    if isinstance(value, Tensor):
        return TensorTheorem(value, term, _tensor_detail(term, value))
    return None


def is_geo_result(value: object) -> bool:
    return isinstance(value, (Metric, Vector, Tensor, MetricTheorem, VectorTheorem, TensorTheorem))


def geo_values_eq(left: object, right: object) -> bool:
    left_m, right_m = _as_metric(left), _as_metric(right)
    if left_m is not None and right_m is not None:
        return metric_eq(left_m, right_m)
    left_v, right_v = _as_vector(left), _as_vector(right)
    if left_v is not None and right_v is not None:
        return vector_eq(left_v, right_v)
    left_t, right_t = _as_tensor(left), _as_tensor(right)
    if left_t is not None and right_t is not None:
        return tensor_eq(left_t, right_t)
    from pgi.math.manifold import _as_mrat
    from pgi.math.poly import mrat_eq as _eq

    left_r, right_r = _as_mrat(left), _as_mrat(right)
    if left_r is not None and right_r is not None:
        return _eq(left_r, right_r)
    left_m = _as_metric(left)
    if left_m is not None and metric_is_zero(left_m) and _is_zero_side(right):
        return True
    right_m = _as_metric(right)
    if right_m is not None and metric_is_zero(right_m) and _is_zero_side(left):
        return True
    from pgi.math.trans import FExpr, fexpr_eq, _as_ratio

    def as_field(value):
        if isinstance(value, FExpr):
            return value
        rat = _as_mrat(value)
        if rat is not None:
            return FExpr(rat, ())
        if isinstance(value, Ratio):
            from pgi.math.trans import const_fexpr
            return const_fexpr(value)
        return None

    left_f, right_f = as_field(left), as_field(right)
    if left_f is not None and right_f is not None:
        return fexpr_eq(left_f, right_f)
    return False


def _is_zero_side(value: object) -> bool:
    from pgi.math.rational import RatTheorem
    from pgi.math.trans import FExpr, _as_ratio

    if isinstance(value, RatTheorem):
        return value.value.num == 0
    if isinstance(value, Ratio):
        return value.num == 0
    if isinstance(value, MRat):
        return mrat_eq(value, zero_rat())
    if isinstance(value, FExpr):
        return _field_is_zero(value)
    from pgi.math.manifold import _as_mrat as _man_mrat
    rat = _man_mrat(value)
    return rat is not None and mrat_eq(rat, zero_rat())


def _as_metric(value: object) -> Metric | None:
    if isinstance(value, MetricTheorem):
        return value.value
    if isinstance(value, Metric):
        return value
    return None


def _as_vector(value: object) -> Vector | None:
    if isinstance(value, VectorTheorem):
        return value.value
    if isinstance(value, Vector):
        return value
    return None


def _as_tensor(value: object) -> Tensor | None:
    if isinstance(value, TensorTheorem):
        return value.value
    if isinstance(value, Tensor):
        return value
    return None


def _metric_detail(term: Term, value: Metric) -> tuple[str, ...]:
    lines = [
        "A metric is a symmetric matrix of exact functions on a chart.",
        "A pullback is J^T g J, kept only when it agrees with g(df X, df Y) on the coordinate basis.",
        "The unit 2-sphere metric is the pullback of the Euclidean 3-metric through the stereographic embedding, or ds^2 = dtheta^2 + sin(theta)^2 dphi^2 in angular coordinates.",
        "Lee, Introduction to Riemannian Manifolds: Riemannian metrics and pullbacks.",
    ]
    if isinstance(term, App) and term.op == "ricci":
        lines.append("Ricci is the contraction R^ρ_{σρν} of the Riemann tensor.")
    if isinstance(term, App) and term.op == "einstein":
        lines.append("The Einstein tensor is G = Ric - (1/2) R g, computed exactly.")
    return tuple(lines)


def _vector_detail(term: Term, value: Vector) -> tuple[str, ...]:
    return (
        "A tangent vector is a tuple of rational components, acting as a derivation.",
        "It annihilates constants, reproduces its components on the coordinates, and satisfies Leibniz.",
    )


def _tensor_detail(term: Term, value: Tensor) -> tuple[str, ...]:
    lines = [
        "Christoffel symbols, Riemann, Ricci, and the scalar curvature are computed exactly from the metric.",
        "The Levi-Civita connection is torsion-free and metric-compatible, checked identically.",
        "The Riemann symmetries and both Bianchi identities are checked identically.",
    ]
    if tensor_is_zero(value):
        lines.append("This curvature tensor vanishes identically.")
    return tuple(lines)


def geo_value_rule(origin: Term, result: object, prelude: tuple[str, ...] = ()) -> Rule:
    title_left = pretty(origin)
    if isinstance(result, MetricTheorem):
        if metric_is_zero(result.value) and isinstance(origin, App) and origin.op in {"ricci", "einstein"}:
            shown = f"{origin.op}(0)"
        else:
            shown = show_metric(result.value)
        return Rule(
            id=f"math.metric.{shown}",
            layer="base",
            stage="quantity",
            title=f"{title_left} = {shown}",
            produces=shown,
            detail_lines=(*prelude, *result.detail),
        )
    if isinstance(result, VectorTheorem):
        shown = show_vector(result.value)
        return Rule(
            id=f"math.vector.{shown}",
            layer="base",
            stage="quantity",
            title=f"{title_left} = {shown}",
            produces=shown,
            detail_lines=(*prelude, *result.detail),
        )
    if isinstance(result, TensorTheorem):
        shown = show_tensor(result.value)
        return Rule(
            id=f"math.tensor.{shown}",
            layer="base",
            stage="quantity",
            title=f"{title_left} = {shown}",
            produces=shown,
            detail_lines=(*prelude, *result.detail),
        )
    raise KernelError("this geometric result has no claim")
