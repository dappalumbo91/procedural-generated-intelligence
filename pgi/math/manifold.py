"""Exact charts, transition maps, and Jacobians of rational maps.

A chart is a named coordinate system. A transition map between two
charts is a tuple of reduced rational functions, kept only when the
two-way composition is the identity on the source coordinates. The
Jacobian is the matrix of exact partial derivatives. Composition of
maps is substitution, kept only when the chain rule holds identically:
J(g ∘ f) equals J(g) along f, times J(f). A determinant of a Jacobian
is kept when cofactor expansions along the first row and the first
column agree. An inverse is kept only when both products are the
identity.

The atlases in this slice are the stereographic charts on the circle
and the 2-sphere, the standard affine charts on the real projective
line, and three linear charts on the plane. Angular charts that need
transcendental functions stay outside.

Lee, *Introduction to Smooth Manifolds*, and the standard stereographic
and affine atlases, are the named constructions. The certificates are
the identity composition and the chain rule, checked exactly, with no
approximation.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from pgi.math.kernel import KernelError, NotExact
from pgi.math.poly import (
    MRat,
    as_rat,
    const_poly,
    eval_symbolic,
    mpoly_add,
    mpoly_mul,
    mpoly_pow,
    mrat_add,
    mrat_diff,
    mrat_div,
    mrat_eq,
    mrat_from,
    mrat_mul,
    mrat_neg,
    mrat_pow,
    mrat_sub,
    show_rat,
    var_poly,
    zero_poly,
)
from pgi.math.rational import Ratio, RatTheorem, rat_normalize
from pgi.math.syntax import App, IntLit, Term, Var, pretty
from pgi.model import Rule


MAP_LIMIT = 8
_METRIC_OPS = frozenset({
    "metric",
    "embedding",
    "pullback",
    "vector",
    "apply",
    "dot",
    "christoffel",
    "riemann",
    "ricci",
    "scalar",
    "kretschmann",
    "einstein",
})
_ZERO = Ratio(0, 1)
_ONE = Ratio(1, 1)
_NEG_ONE = Ratio(-1, 1)
_TWO = Ratio(2, 1)

# Chart coordinates, and every genuine transition of the atlases below.
# Names are case-sensitive as written in an ask; aliases are listed here.
_CHART_COORDS: dict[tuple[str, str], tuple[str, ...]] = {
    ("s1", "north"): ("u",),
    ("s1", "south"): ("v",),
    ("circle", "north"): ("u",),
    ("circle", "south"): ("v",),
    ("s2", "north"): ("u", "v"),
    ("s2", "south"): ("p", "q"),
    ("sphere", "north"): ("u", "v"),
    ("sphere", "south"): ("p", "q"),
    ("r2", "xy"): ("x", "y"),
    ("r2", "uv"): ("u", "v"),
    ("r2", "pq"): ("p", "q"),
    ("rp1", "u0"): ("t",),
    ("rp1", "u1"): ("s",),
    ("minkowski2", "tx"): ("t", "x"),
    ("minkowski2", "uv"): ("u", "v"),
    ("m2", "tx"): ("t", "x"),
    ("m2", "uv"): ("u", "v"),
}

_CHART_ALIASES: dict[tuple[str, str], tuple[str, str]] = {
    ("circle", "north"): ("s1", "north"),
    ("circle", "south"): ("s1", "south"),
    ("sphere", "north"): ("s2", "north"),
    ("sphere", "south"): ("s2", "south"),
    ("m2", "tx"): ("minkowski2", "tx"),
    ("m2", "uv"): ("minkowski2", "uv"),
}


@dataclass(frozen=True)
class RatMap:
    sources: tuple[str, ...]
    targets: tuple[str, ...]
    components: tuple[MRat, ...]

    def __post_init__(self) -> None:
        if not _map_ok(self):
            raise KernelError("this rational map is not in normal form")


@dataclass(frozen=True)
class JacMatrix:
    names: tuple[str, ...]
    rows: tuple[tuple[MRat, ...], ...]

    def __post_init__(self) -> None:
        if not _jac_ok(self):
            raise KernelError("this Jacobian is not in normal form")

    @property
    def height(self) -> int:
        return len(self.rows)

    @property
    def width(self) -> int:
        return len(self.rows[0]) if self.rows else 0


@dataclass(frozen=True)
class MapTheorem:
    value: RatMap
    origin: Term
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not map_eq(self.value, eval_map(self.origin)):
            raise KernelError("this transition does not match the exact evaluation")


@dataclass(frozen=True)
class JacTheorem:
    value: JacMatrix
    origin: Term
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not jac_eq(self.value, eval_jac(self.origin)):
            raise KernelError("this Jacobian does not match the exact evaluation")


def _map_ok(value: RatMap) -> bool:
    if not value.sources or not value.targets:
        return False
    if len(value.sources) > MAP_LIMIT or len(value.targets) > MAP_LIMIT:
        return False
    if len(value.components) != len(value.targets):
        return False
    if len(set(value.sources)) != len(value.sources):
        return False
    if len(set(value.targets)) != len(value.targets):
        return False
    if not all(_component_in(component, value.sources) for component in value.components):
        return False
    for component in value.components:
        _subst_fixes_identity(component)
    return True


def _jac_ok(value: JacMatrix) -> bool:
    if not value.rows:
        return False
    width = len(value.rows[0])
    if width == 0 or len(value.rows) > MAP_LIMIT or width > MAP_LIMIT:
        return False
    if any(len(row) != width for row in value.rows):
        return False
    if len(set(value.names)) != len(value.names):
        return False
    return all(_component_in(entry, value.names) for row in value.rows for entry in row)


def _component_in(value: MRat, names: tuple[str, ...]) -> bool:
    used = set(value.num.names) | set(value.den.names)
    return used <= set(names)


def show_map(value: RatMap) -> str:
    if map_is_identity(value):
        return "identity(" + ", ".join(value.sources) + ")"
    return "map(" + ", ".join(show_rat(component) for component in value.components) + ")"


def show_jac(value: JacMatrix) -> str:
    rows = []
    for row in value.rows:
        rows.append("[" + ", ".join(show_rat(entry) for entry in row) + "]")
    return "[" + ", ".join(rows) + "]"


def zero_rat() -> MRat:
    return as_rat(const_poly(_ZERO))


def one_rat() -> MRat:
    return as_rat(const_poly(_ONE))


def const_rat(value: Ratio) -> MRat:
    return as_rat(const_poly(value))


def var_rat(name: str, names: tuple[str, ...] | None = None) -> MRat:
    if names is None:
        return as_rat(var_poly(name))
    return embed_rat(as_rat(var_poly(name)), names)


def actual_names(*polys) -> set[str]:
    present: set[str] = set()
    for poly in polys:
        for monom, _coeff in poly.terms:
            for name, exp in zip(poly.names, monom):
                if exp:
                    present.add(name)
    return present


def restrict_rat(value: MRat, names: tuple[str, ...]) -> MRat:
    extra = actual_names(value.num, value.den) - set(names)
    if extra:
        raise KernelError("a map component has a variable outside the source coordinates")
    return mrat_from(_restrict_poly(value.num, names), _restrict_poly(value.den, names))


def _restrict_poly(poly, names: tuple[str, ...]):
    result = zero_poly(names)
    for monom, coeff in poly.terms:
        term = const_poly(coeff, names)
        for name, exp in zip(poly.names, monom):
            if exp:
                term = mpoly_mul(term, mpoly_pow(var_poly(name, names), exp))
        result = mpoly_add(result, term)
    return result


def embed_rat(value: MRat, names: tuple[str, ...]) -> MRat:
    result = value
    for name in names:
        result = mrat_add(result, as_rat(zero_poly((name,))))
    return restrict_rat(result, names)


def mrat_subst(value: MRat, env: dict[str, MRat]) -> MRat:
    num = _poly_subst(value.num, env)
    den = _poly_subst(value.den, env)
    if _is_zero(den):
        raise NotExact("this substitution makes the denominator identically zero")
    return mrat_div(num, den)


def _poly_subst(poly, env: dict[str, MRat]) -> MRat:
    result = zero_rat()
    if not poly.terms:
        return result
    for monom, coeff in poly.terms:
        term = const_rat(coeff)
        for name, exp in zip(poly.names, monom):
            if exp == 0:
                continue
            image = env.get(name)
            if image is None:
                image = var_rat(name)
            term = mrat_mul(term, mrat_pow(image, exp))
        result = mrat_add(result, term)
    return result


def _is_zero(value: MRat) -> bool:
    return mrat_eq(value, zero_rat())


def _is_one(value: MRat) -> bool:
    return mrat_eq(value, one_rat())


def _subst_fixes_identity(value: MRat) -> None:
    names = tuple(sorted(set(value.num.names) | set(value.den.names)))
    if not names:
        return
    env = {name: var_rat(name) for name in names}
    again_num = _poly_subst(value.num, env)
    again_den = _poly_subst(value.den, env)
    if _is_zero(again_den) or not mrat_eq(mrat_div(again_num, again_den), value):
        raise KernelError("substitution did not fix a rational function along the identity")


@lru_cache(maxsize=256)
def identity_map(names: tuple[str, ...]) -> RatMap:
    if not names or len(names) > MAP_LIMIT:
        raise NotExact("an identity map needs a finite list of coordinates")
    if len(set(names)) != len(names):
        raise KernelError("coordinate names must be distinct")
    components = tuple(var_rat(name, names) for name in names)
    return RatMap(names, names, components)


def map_eq(left: RatMap, right: RatMap) -> bool:
    if len(left.sources) != len(right.sources) or len(left.targets) != len(right.targets):
        return False
    # Equality is as functions of the source coordinates in order, after
    # renaming the right-hand sources to the left-hand names.
    env = {old: var_rat(new) for old, new in zip(right.sources, left.sources)}
    for left_c, right_c in zip(left.components, right.components):
        renamed = mrat_subst(right_c, env) if env else right_c
        if not mrat_eq(left_c, renamed):
            return False
    return True


def map_is_identity(value: RatMap) -> bool:
    if len(value.sources) != len(value.targets):
        return False
    return all(
        mrat_eq(component, var_rat(name, value.sources))
        for name, component in zip(value.sources, value.components)
    )


@lru_cache(maxsize=256)
def map_compose(outer: RatMap, inner: RatMap) -> RatMap:
    if len(outer.sources) != len(inner.targets):
        raise NotExact("these maps do not compose")
    env = {
        name: embed_rat(component, inner.sources)
        for name, component in zip(outer.sources, inner.components)
    }
    components = tuple(embed_rat(mrat_subst(component, env), inner.sources) for component in outer.components)
    result = RatMap(inner.sources, outer.targets, components)
    along = jac_subst(map_jacobian(outer), env, inner.sources)
    product = jac_mul(along, map_jacobian(inner))
    expected = map_jacobian(result)
    if not jac_eq(product, expected):
        raise KernelError("the chain rule did not hold for this composition")
    return result


@lru_cache(maxsize=256)
def map_jacobian(value: RatMap) -> JacMatrix:
    rows = []
    for component in value.components:
        row = tuple(embed_rat(mrat_diff(component, name), value.sources) for name in value.sources)
        rows.append(row)
    result = JacMatrix(value.sources, tuple(rows))
    if map_is_identity(value) and not jac_is_identity(result):
        raise KernelError("the Jacobian of an identity map was not the identity")
    return result


def jac_eq(left: JacMatrix, right: JacMatrix) -> bool:
    if left.height != right.height or left.width != right.width:
        return False
    if left.names == right.names:
        return all(
            mrat_eq(left_entry, right_entry)
            for left_row, right_row in zip(left.rows, right.rows)
            for left_entry, right_entry in zip(left_row, right_row)
        )
    if len(left.names) != len(right.names):
        return False
    env = {old: var_rat(new) for old, new in zip(right.names, left.names)}
    return all(
        mrat_eq(left_entry, mrat_subst(right_entry, env))
        for left_row, right_row in zip(left.rows, right.rows)
        for left_entry, right_entry in zip(left_row, right_row)
    )


def jac_is_identity(value: JacMatrix) -> bool:
    if value.height != value.width:
        return False
    for i, row in enumerate(value.rows):
        for j, entry in enumerate(row):
            expected = one_rat() if i == j else zero_rat()
            if not mrat_eq(entry, expected):
                return False
    return True


def identity_jac(names: tuple[str, ...]) -> JacMatrix:
    size = len(names)
    rows = []
    for i in range(size):
        row = []
        for j in range(size):
            entry = one_rat() if i == j else zero_rat()
            row.append(embed_rat(entry, names))
        rows.append(tuple(row))
    return JacMatrix(names, tuple(rows))


def jac_mul(left: JacMatrix, right: JacMatrix) -> JacMatrix:
    if left.width != right.height:
        raise NotExact("these Jacobians do not multiply")
    names = _join_names(left.names, right.names)
    rows = []
    for i in range(left.height):
        row = []
        for j in range(right.width):
            total = zero_rat()
            for k in range(left.width):
                total = mrat_add(
                    total,
                    mrat_mul(embed_rat(left.rows[i][k], names), embed_rat(right.rows[k][j], names)),
                )
            row.append(embed_rat(total, names))
        rows.append(tuple(row))
    return JacMatrix(names, tuple(rows))


def jac_transpose(value: JacMatrix) -> JacMatrix:
    rows = []
    for j in range(value.width):
        rows.append(tuple(value.rows[i][j] for i in range(value.height)))
    return JacMatrix(value.names, tuple(rows))


def jac_subst(value: JacMatrix, env: dict[str, MRat], names: tuple[str, ...]) -> JacMatrix:
    rows = []
    for row in value.rows:
        rows.append(tuple(embed_rat(mrat_subst(entry, env), names) for entry in row))
    return JacMatrix(names, tuple(rows))


@lru_cache(maxsize=256)
def jac_det(value: JacMatrix) -> MRat:
    if value.height != value.width:
        raise NotExact("a non-square Jacobian has no determinant here")
    along_row = _det_cofactor(value, True)
    along_col = _det_cofactor(value, False)
    if not mrat_eq(along_row, along_col):
        raise KernelError("the Jacobian determinant expansions did not agree")
    return embed_rat(along_row, value.names)


@lru_cache(maxsize=256)
def jac_inv(value: JacMatrix) -> JacMatrix:
    if value.height != value.width:
        raise NotExact("a non-square Jacobian has no inverse here")
    det = jac_det(value)
    if _is_zero(det):
        raise NotExact("this Jacobian is identically singular")
    adj = _adjugate(value)
    rows = []
    for row in adj.rows:
        rows.append(tuple(embed_rat(mrat_div(entry, det), value.names) for entry in row))
    inverse = JacMatrix(value.names, tuple(rows))
    ident = identity_jac(value.names)
    if not jac_eq(jac_mul(inverse, value), ident) or not jac_eq(jac_mul(value, inverse), ident):
        raise KernelError("this Jacobian inverse did not multiply back to the identity")
    return inverse


def _adjugate(value: JacMatrix) -> JacMatrix:
    size = value.height
    if size == 1:
        return JacMatrix(value.names, ((embed_rat(one_rat(), value.names),),))
    rows = []
    for j in range(size):
        row = []
        for i in range(size):
            minor = _minor(value, i, j)
            cofactor = jac_det(minor)
            if (i + j) % 2 == 1:
                cofactor = mrat_neg(cofactor)
            row.append(embed_rat(cofactor, value.names))
        rows.append(tuple(row))
    return JacMatrix(value.names, tuple(rows))


def _det_cofactor(value: JacMatrix, along_row: bool) -> MRat:
    size = value.height
    if size == 1:
        return value.rows[0][0]
    total = zero_rat()
    for index in range(size):
        if along_row:
            entry = value.rows[0][index]
            minor = _minor(value, 0, index)
            sign_odd = index % 2 == 1
        else:
            entry = value.rows[index][0]
            minor = _minor(value, index, 0)
            sign_odd = index % 2 == 1
        piece = mrat_mul(entry, _det_cofactor(minor, True))
        if sign_odd:
            piece = mrat_neg(piece)
        total = mrat_add(total, piece)
    return total


def _minor(value: JacMatrix, drop_row: int, drop_col: int) -> JacMatrix:
    rows = []
    for i, row in enumerate(value.rows):
        if i == drop_row:
            continue
        rows.append(tuple(entry for j, entry in enumerate(row) if j != drop_col))
    return JacMatrix(value.names, tuple(rows))


def _join_names(*groups: tuple[str, ...]) -> tuple[str, ...]:
    seen: list[str] = []
    for group in groups:
        for name in group:
            if name not in seen:
                seen.append(name)
    if len(seen) > MAP_LIMIT:
        raise NotExact("this map exceeds the coordinate limit")
    return tuple(seen)


@lru_cache(maxsize=256)
def chart_identity(manifold: str, chart: str) -> RatMap:
    names = _chart_coords(manifold, chart)
    return identity_map(names)


@lru_cache(maxsize=256)
def transition_map(manifold: str, source: str, target: str) -> RatMap:
    manifold, source = _canonical_chart(manifold, source)
    manifold, target = _canonical_chart(manifold, target)
    if source == target:
        return chart_identity(manifold, source)
    try:
        builder = _TRANSITIONS[(manifold, source, target)]
    except KeyError as exc:
        raise NotExact("this chart is not in the atlas") from exc
    result = builder()
    inverse = _TRANSITIONS[(manifold, target, source)]()
    forth = map_compose(inverse, result)
    back = map_compose(result, inverse)
    if not map_is_identity(forth) or not map_is_identity(back):
        raise KernelError("these transition maps did not compose to the identity")
    return result


def _canonical_chart(manifold: str, chart: str) -> tuple[str, str]:
    key = (manifold, chart)
    if key in _CHART_ALIASES:
        return _CHART_ALIASES[key]
    if key in _CHART_COORDS:
        return key
    raise NotExact("this chart is not in the atlas")


def _chart_coords(manifold: str, chart: str) -> tuple[str, ...]:
    manifold, chart = _canonical_chart(manifold, chart)
    return _CHART_COORDS[(manifold, chart)]


def _var(name: str, names: tuple[str, ...]) -> MRat:
    return var_rat(name, names)


def _plus(left: MRat, right: MRat) -> MRat:
    return mrat_add(left, right)


def _minus(left: MRat, right: MRat) -> MRat:
    return mrat_sub(left, right)


def _times(left: MRat, right: MRat) -> MRat:
    return mrat_mul(left, right)


def _over(left: MRat, right: MRat) -> MRat:
    return mrat_div(left, right)


def _scale(value: Ratio, term: MRat) -> MRat:
    return mrat_mul(const_rat(value), term)


def _s1_north_south() -> RatMap:
    u = _var("u", ("u",))
    return RatMap(("u",), ("v",), (_over(one_rat(), u),))


def _s1_south_north() -> RatMap:
    v = _var("v", ("v",))
    return RatMap(("v",), ("u",), (_over(one_rat(), v),))


def _s2_north_south() -> RatMap:
    names = ("u", "v")
    u, v = _var("u", names), _var("v", names)
    rho = _plus(mrat_pow(u, 2), mrat_pow(v, 2))
    return RatMap(names, ("p", "q"), (_over(u, rho), _over(v, rho)))


def _s2_south_north() -> RatMap:
    names = ("p", "q")
    p, q = _var("p", names), _var("q", names)
    rho = _plus(mrat_pow(p, 2), mrat_pow(q, 2))
    return RatMap(names, ("u", "v"), (_over(p, rho), _over(q, rho)))


def _r2_xy_uv() -> RatMap:
    names = ("x", "y")
    x, y = _var("x", names), _var("y", names)
    return RatMap(names, ("u", "v"), (_plus(x, y), _minus(x, y)))


def _r2_uv_xy() -> RatMap:
    names = ("u", "v")
    u, v = _var("u", names), _var("v", names)
    half = Ratio(1, 2)
    return RatMap(names, ("x", "y"), (_scale(half, _plus(u, v)), _scale(half, _minus(u, v))))


def _r2_xy_pq() -> RatMap:
    names = ("x", "y")
    x, y = _var("x", names), _var("y", names)
    return RatMap(names, ("p", "q"), (_scale(_TWO, x), y))


def _r2_pq_xy() -> RatMap:
    names = ("p", "q")
    p, q = _var("p", names), _var("q", names)
    return RatMap(names, ("x", "y"), (_scale(Ratio(1, 2), p), q))


def _r2_uv_pq() -> RatMap:
    names = ("u", "v")
    u, v = _var("u", names), _var("v", names)
    return RatMap(names, ("p", "q"), (_plus(u, v), _scale(Ratio(1, 2), _minus(u, v))))


def _r2_pq_uv() -> RatMap:
    names = ("p", "q")
    p, q = _var("p", names), _var("q", names)
    half_p = _scale(Ratio(1, 2), p)
    return RatMap(names, ("u", "v"), (_plus(half_p, q), _minus(half_p, q)))


def _rp1_u0_u1() -> RatMap:
    t = _var("t", ("t",))
    return RatMap(("t",), ("s",), (_over(one_rat(), t),))


def _rp1_u1_u0() -> RatMap:
    s = _var("s", ("s",))
    return RatMap(("s",), ("t",), (_over(one_rat(), s),))


def _m2_tx_uv() -> RatMap:
    names = ("t", "x")
    time, space = _var("t", names), _var("x", names)
    return RatMap(names, ("u", "v"), (_minus(time, space), _plus(time, space)))


def _m2_uv_tx() -> RatMap:
    names = ("u", "v")
    u, v = _var("u", names), _var("v", names)
    half = Ratio(1, 2)
    return RatMap(names, ("t", "x"), (_scale(half, _plus(u, v)), _scale(half, _minus(v, u))))


_TRANSITIONS: dict[tuple[str, str, str], object] = {
    ("s1", "north", "south"): _s1_north_south,
    ("s1", "south", "north"): _s1_south_north,
    ("s2", "north", "south"): _s2_north_south,
    ("s2", "south", "north"): _s2_south_north,
    ("r2", "xy", "uv"): _r2_xy_uv,
    ("r2", "uv", "xy"): _r2_uv_xy,
    ("r2", "xy", "pq"): _r2_xy_pq,
    ("r2", "pq", "xy"): _r2_pq_xy,
    ("r2", "uv", "pq"): _r2_uv_pq,
    ("r2", "pq", "uv"): _r2_pq_uv,
    ("rp1", "u0", "u1"): _rp1_u0_u1,
    ("rp1", "u1", "u0"): _rp1_u1_u0,
    ("minkowski2", "tx", "uv"): _m2_tx_uv,
    ("minkowski2", "uv", "tx"): _m2_uv_tx,
}


def _r2_cocycle() -> None:
    # τ_pq ← τ_uv ∘ τ_xy  equals the direct transition xy → pq.
    left = map_compose(transition_map("r2", "uv", "pq"), transition_map("r2", "xy", "uv"))
    right = transition_map("r2", "xy", "pq")
    if not map_eq(left, right):
        raise KernelError("the plane atlas cocycle did not hold")


def eval_map(term: Term) -> RatMap:
    value = _eval(term)
    if isinstance(value, RatMap):
        return value
    raise NotExact("this term is not a chart or a transition map")


def eval_jac(term: Term) -> JacMatrix:
    value = _eval(term)
    if isinstance(value, JacMatrix):
        return value
    if isinstance(value, RatMap):
        return map_jacobian(value)
    raise NotExact("this term is not a Jacobian")


def _eval(term: Term) -> RatMap | JacMatrix | MRat:
    if isinstance(term, IntLit):
        return const_rat(Ratio(term.n, 1))
    if isinstance(term, App) and term.op == "neg" and len(term.args) == 1 and isinstance(term.args[0], IntLit):
        return const_rat(Ratio(-term.args[0].n, 1))
    if not isinstance(term, App):
        raise NotExact("this term is not a chart, a transition, or a Jacobian")
    if term.op == "transition":
        if len(term.args) != 3:
            raise NotExact("a transition map names a manifold and two charts")
        return transition_map(_name(term.args[0]), _name(term.args[1]), _name(term.args[2]))
    if term.op == "identity":
        return _eval_identity(term)
    if term.op == "chart":
        if len(term.args) != 2:
            raise NotExact("a chart names a manifold and a chart")
        return chart_identity(_name(term.args[0]), _name(term.args[1]))
    if term.op == "compose":
        if len(term.args) != 2:
            raise NotExact("compose takes two maps")
        return map_compose(eval_map(term.args[0]), eval_map(term.args[1]))
    if term.op == "jacobian":
        if len(term.args) != 1:
            raise NotExact("jacobian takes a map")
        return map_jacobian(eval_map(term.args[0]))
    if term.op == "det":
        if len(term.args) != 1:
            raise NotExact("det takes a Jacobian")
        return jac_det(eval_jac(term.args[0]))
    if term.op in {"inv", "inverse"}:
        if len(term.args) != 1:
            raise NotExact("inv takes a Jacobian")
        return jac_inv(eval_jac(term.args[0]))
    if term.op in _METRIC_OPS:
        from pgi.math.metric import eval_geo

        return eval_geo(term)
    raise NotExact("this term is not a chart, a transition, a Jacobian, or a metric")


def _eval_identity(term: App) -> RatMap:
    if not term.args:
        raise NotExact("an identity map needs a chart or a list of coordinates")
    if len(term.args) == 2 and _looks_like_chart(term.args[0], term.args[1]):
        return chart_identity(_name(term.args[0]), _name(term.args[1]))
    names = tuple(_name(arg) for arg in term.args)
    return identity_map(names)


def _looks_like_chart(manifold: Term, chart: Term) -> bool:
    try:
        _canonical_chart(_name(manifold), _name(chart))
    except NotExact:
        return False
    return True


def _name(term: Term) -> str:
    if isinstance(term, Var):
        return term.name
    raise NotExact("a chart or a coordinate is a name")


def has_manifold(term: Term) -> bool:
    if isinstance(term, App):
        if term.op in {"transition", "compose", "jacobian", "identity", "chart"} | _METRIC_OPS:
            return True
        if term.op in {"det", "inv", "inverse"} and term.args and has_manifold(term.args[0]):
            return True
        return any(has_manifold(arg) for arg in term.args)
    return False


_COCYCLE_OK = False


def eval_man_result(term: Term) -> MapTheorem | JacTheorem | RatTheorem | object:
    # The plane cocycle is a standing check on the atlas, not on every ask.
    global _COCYCLE_OK
    if not _COCYCLE_OK:
        _r2_cocycle()
        _COCYCLE_OK = True
    value = _eval(term)
    if isinstance(value, RatMap):
        return MapTheorem(value, term, _map_detail(term, value))
    if isinstance(value, JacMatrix):
        return JacTheorem(value, term, _jac_detail(term, value))
    if isinstance(value, MRat):
        constant = _as_constant(value)
        if constant is not None:
            return rat_normalize(constant.num, constant.den)
        return _RatFn(value, term)
    from pgi.math.trans import FExpr, _as_ratio

    if isinstance(value, FExpr):
        rat = _as_ratio(value)
        if rat is not None:
            return rat_normalize(rat.num, rat.den)
        if not value.atoms:
            return _RatFn(value.body, term)
        return _FunFn(value, term)
    from pgi.math.metric import as_geo_theorem

    wrapped = as_geo_theorem(value, term)
    if wrapped is not None:
        return wrapped
    raise NotExact("this term is not a chart, a transition, a Jacobian, or a metric")


@dataclass(frozen=True)
class _RatFn:
    value: MRat
    origin: Term


@dataclass(frozen=True)
class _FunFn:
    value: object
    origin: Term


def _as_constant(value: MRat) -> Ratio | None:
    if not value.num.is_constant or not value.den.is_constant:
        return None
    num = value.num.constant() if not value.num.is_zero else _ZERO
    den = value.den.constant()
    if den == _ZERO:
        return None
    return _ratio_from(num, den)


def _ratio_from(num: Ratio, den: Ratio) -> Ratio:
    # num/den as rationals: (n1/d1) / (n2/d2) = (n1 d2) / (d1 n2)
    from math import gcd

    top = num.num * den.den
    bottom = num.den * den.num
    if bottom < 0:
        top, bottom = -top, -bottom
    if bottom == 0:
        raise NotExact("division by zero")
    scale = gcd(abs(top), bottom)
    return Ratio(top // scale, bottom // scale)


def _map_detail(term: Term, value: RatMap) -> tuple[str, ...]:
    lines = [
        "A transition map is a tuple of reduced rational functions between charts.",
        "The two-way composition of a genuine pair of transitions is the identity, checked exactly.",
        "Lee, Introduction to Smooth Manifolds: charts, atlases, and transition maps.",
    ]
    if isinstance(term, App) and term.op == "compose":
        lines.append("Composition is substitution, kept only when the chain rule holds identically.")
    if map_is_identity(value):
        lines.append("These maps compose to the identity on the source coordinates.")
    return tuple(lines)


def _jac_detail(term: Term, value: JacMatrix) -> tuple[str, ...]:
    lines = [
        "The Jacobian is the matrix of exact partial derivatives of a rational map.",
        "Composition is kept only when J(g ∘ f) equals J(g) along f, times J(f).",
        "A Jacobian inverse is kept only when both products are the identity.",
    ]
    if jac_is_identity(value):
        lines.append("This Jacobian is the identity matrix.")
    return tuple(lines)


def man_value_rule(origin: Term, result: object, prelude: tuple[str, ...] = ()) -> Rule:
    title_left = pretty(origin)
    if isinstance(result, RatTheorem):
        from pgi.math.rational import ratio_rule

        return ratio_rule(origin, result, prelude)
    if isinstance(result, MapTheorem):
        shown = show_map(result.value)
        return Rule(
            id=f"math.map.{shown}",
            layer="base",
            stage="quantity",
            title=f"{title_left} = {shown}",
            produces=shown if shown.startswith("identity(") else f"map({', '.join(show_rat(c) for c in result.value.components)})",
            detail_lines=(*prelude, *result.detail),
        )
    if isinstance(result, JacTheorem):
        shown = show_jac(result.value)
        return Rule(
            id=f"math.jac.{shown}",
            layer="base",
            stage="quantity",
            title=f"{title_left} = {shown}",
            produces=f"jac({shown})",
            detail_lines=(*prelude, *result.detail),
        )
    if isinstance(result, _RatFn):
        shown = show_rat(result.value)
        kind = "poly" if result.value.is_poly else "rat"
        detail = "The exact evaluation of this geometric or symbolic term is this reduced rational function."
        if isinstance(origin, App) and origin.op == "det":
            detail = "The determinant of this Jacobian is this reduced rational function."
        elif isinstance(origin, App) and origin.op == "apply":
            detail = "A tangent vector acts as a derivation, checked by the Leibniz rule."
        elif isinstance(origin, App) and origin.op == "dot":
            detail = "The metric pairing is the contraction g_ij X^i Y^j, checked to be symmetric."
        elif isinstance(origin, App) and origin.op == "scalar":
            detail = "The scalar curvature is the contraction of Ricci with the inverse metric."
        elif isinstance(origin, App) and origin.op == "kretschmann":
            detail = "The Kretschmann scalar is the full contraction R_{ρσμν} R^{ρσμν}, computed exactly."
        return Rule(
            id=f"math.{kind}fn.{shown}",
            layer="base",
            stage="quantity",
            title=f"{title_left} = {shown}",
            produces=f"{kind}({shown})",
            detail_lines=(*prelude, detail),
        )
    if isinstance(result, _FunFn):
        from pgi.math.trans import show_fexpr

        shown = show_fexpr(result.value)
        detail = "The exact evaluation of this geometric term is this elementary expression."
        if isinstance(origin, App) and origin.op == "kretschmann":
            detail = "The Kretschmann scalar is the full contraction R_{ρσμν} R^{ρσμν}, computed exactly."
        return Rule(
            id=f"math.trans.{shown}",
            layer="base",
            stage="quantity",
            title=f"{title_left} = {shown}",
            produces=f"trans({shown})",
            detail_lines=(*prelude, detail),
        )
    from pgi.math.metric import geo_value_rule, is_geo_result

    if is_geo_result(result):
        return geo_value_rule(origin, result, prelude)
    raise KernelError("this manifold result has no claim")


def man_equality_rules(
    left: Term,
    right: Term,
    left_value: object,
    right_value: object,
    prelude: tuple[str, ...] = (),
) -> tuple[Rule, ...]:
    title = f"{pretty(left)} = {pretty(right)}"
    if _man_values_eq(left_value, right_value):
        return (
            Rule(
                id="math.map.eq",
                layer="base",
                stage="quantity",
                title=title,
                produces=f"identity({title})",
                detail_lines=(*prelude, "The two sides are the same map, Jacobian, or rational function."),
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


def _man_values_eq(left: object, right: object) -> bool:
    left_map = _as_map(left)
    right_map = _as_map(right)
    if left_map is not None and right_map is not None:
        return map_eq(left_map, right_map)
    left_jac = _as_jac(left)
    right_jac = _as_jac(right)
    if left_jac is not None and right_jac is not None:
        return jac_eq(left_jac, right_jac)
    from pgi.math.metric import geo_values_eq, is_geo_result

    if is_geo_result(left) or is_geo_result(right):
        return geo_values_eq(left, right)
    left_rat = _as_mrat(left)
    right_rat = _as_mrat(right)
    if left_rat is not None and right_rat is not None:
        return mrat_eq(left_rat, right_rat)
    from pgi.math.trans import FExpr, fexpr_eq

    def as_field(value):
        if isinstance(value, _FunFn):
            return value.value
        if isinstance(value, FExpr):
            return value
        rat = _as_mrat(value)
        if rat is not None:
            return FExpr(rat, ())
        return None

    left_f, right_f = as_field(left), as_field(right)
    if left_f is not None and right_f is not None:
        return fexpr_eq(left_f, right_f)
    return False


def _as_map(value: object) -> RatMap | None:
    if isinstance(value, MapTheorem):
        return value.value
    if isinstance(value, RatMap):
        return value
    return None


def _as_jac(value: object) -> JacMatrix | None:
    if isinstance(value, JacTheorem):
        return value.value
    if isinstance(value, JacMatrix):
        return value
    return None


def _as_mrat(value: object) -> MRat | None:
    if isinstance(value, _RatFn):
        return value.value
    if isinstance(value, MRat):
        return value
    if isinstance(value, RatTheorem):
        return const_rat(value.value)
    from pgi.math.poly import SymTheorem

    if isinstance(value, SymTheorem):
        return value.value
    return None


def side_as_man_or_field(term: Term) -> object:
    """Evaluate a manifold term, or a rational function or closed number used beside one."""
    if has_manifold(term):
        return eval_man_result(term)
    try:
        from pgi.math.poly import eval_sym_result

        return eval_sym_result(term)
    except (KernelError, NotExact):
        from pgi.math.rational import eval_rat

        return eval_rat(term)
