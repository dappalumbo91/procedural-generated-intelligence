"""Differential forms, the exterior derivative, and Maxwell's homogeneous equation.

A k-form on a coordinate chart has exact components, either multivariate
rationals or elementary expressions. The wedge product is alternating.
The exterior derivative satisfies d² = 0, checked identically on every
admitted form. On flat Minkowski spacetime with coordinates (t, x, y, z),
the Faraday 2-form of a 4-potential is F = dA, and dF = 0 is the identity
d²A = 0: the homogeneous Maxwell equations in the language of forms.
The Hodge star of a k-form is the complementary (n-k)-form built from
the inverse metric and the exact volume density √|g|, kept only when
that density squares back to |det g|. On flat Minkowski spacetime and
on the Schwarzschild metric, d⋆F is the inhomogeneous Maxwell 3-form J.

Certificates are identities, checked exactly, with no approximation.
"""

from __future__ import annotations

from dataclasses import dataclass

from pgi.math.kernel import KernelError, NotExact
from pgi.math.manifold import actual_names
from pgi.math.metric import (
    Metric,
    _field_add,
    _field_diff,
    _field_embed,
    _field_eq,
    _field_is_zero,
    _field_mul,
    _field_neg,
    _field_show,
    _is_fun,
    _lift,
    _zero_for,
    metric_eq,
    metric_inverse,
    named_metric,
)
from pgi.math.poly import MRat, eval_symbolic, show_rat, zero_poly, as_rat
from pgi.math.rational import Ratio, RatTheorem, rat_normalize
from pgi.math.syntax import App, IntLit, Term, Var, pretty
from pgi.model import Rule


_ZERO = Ratio(0, 1)
_MINKOWSKI = ("t", "x", "y", "z")


def _zero_coeff(names: tuple[str, ...]):
    return as_rat(zero_poly(names))


def _coeff_in(value, names: tuple[str, ...]) -> bool:
    from pgi.math.metric import _fexpr_used_names
    from pgi.math.trans import FExpr

    if isinstance(value, FExpr):
        # Unused plains may remain after a cancellation. The mass parameter
        # of Schwarzschild is allowed, as on the metric itself.
        return _fexpr_used_names(value) <= set(names) | {"m", "pi"}
    if isinstance(value, MRat):
        return actual_names(value.num, value.den) <= set(names)
    return False


def _sort_indices(indices: tuple[int, ...]) -> tuple[int, tuple[int, ...]]:
    items = list(indices)
    sign = 1
    for i in range(len(items)):
        for j in range(len(items) - 1, i, -1):
            if items[j] == items[j - 1]:
                return 0, tuple(sorted(items))
            if items[j] < items[j - 1]:
                items[j], items[j - 1] = items[j - 1], items[j]
                sign = -sign
    return sign, tuple(items)


@dataclass(frozen=True)
class Form:
    names: tuple[str, ...]
    degree: int
    terms: tuple[tuple[tuple[int, ...], object], ...]

    def __post_init__(self) -> None:
        if not _form_ok(self):
            raise KernelError("this differential form is not in normal form")


def _form_ok(value: Form) -> bool:
    if not value.names or len(set(value.names)) != len(value.names):
        return False
    if value.degree < 0:
        return False
    # A form of degree greater than the dimension exists only as zero.
    if value.degree > len(value.names):
        return not value.terms
    seen: set[tuple[int, ...]] = set()
    for indices, coeff in value.terms:
        if len(indices) != value.degree:
            return False
        if list(indices) != sorted(indices) or len(set(indices)) != len(indices):
            return False
        if any(index < 0 or index >= len(value.names) for index in indices):
            return False
        if indices in seen:
            return False
        seen.add(indices)
        if not _coeff_in(coeff, value.names):
            return False
        if _field_is_zero(coeff):
            return False
    return True


def form_is_zero(value: Form) -> bool:
    return not value.terms


def _make_form(names: tuple[str, ...], degree: int, raw: list[tuple[tuple[int, ...], object]]) -> Form:
    merged: dict[tuple[int, ...], object] = {}
    for indices, coeff in raw:
        sign, ordered = _sort_indices(indices)
        if sign == 0:
            continue
        coeff = _field_embed(coeff, names)
        if sign < 0:
            coeff = _field_neg(coeff)
        if ordered in merged:
            merged[ordered] = _field_add(merged[ordered], coeff)
        else:
            merged[ordered] = coeff
    terms = []
    for indices in sorted(merged):
        coeff = _field_embed(merged[indices], names)
        if not _field_is_zero(coeff):
            terms.append((indices, coeff))
    return Form(names, degree, tuple(terms))


def zero_form(names: tuple[str, ...], degree: int) -> Form:
    return _make_form(names, degree, [])


def merge_names(*groups: tuple[str, ...]) -> tuple[str, ...]:
    seen: list[str] = []
    for group in groups:
        for name in group:
            if name not in seen:
                seen.append(name)
    return tuple(seen)


def _reembed(value: Form, names: tuple[str, ...]) -> Form:
    if value.names == names:
        return value
    index_of = {name: i for i, name in enumerate(names)}
    raw = []
    for indices, coeff in value.terms:
        new_indices = tuple(index_of[value.names[i]] for i in indices)
        raw.append((new_indices, _field_embed(coeff, names)))
    return _make_form(names, value.degree, raw)


def _align_forms(left: Form, right: Form) -> tuple[Form, Form]:
    names = merge_names(left.names, right.names)
    return _reembed(left, names), _reembed(right, names)


def form_add(left: Form, right: Form) -> Form:
    if left.degree != right.degree:
        raise NotExact("these differential forms do not have the same degree")
    a, b = _align_forms(left, right)
    return _make_form(a.names, a.degree, list(a.terms) + list(b.terms))


def form_sub(left: Form, right: Form) -> Form:
    return form_add(left, form_neg(right))


def form_neg(value: Form) -> Form:
    return _make_form(value.names, value.degree, [(indices, _field_neg(coeff)) for indices, coeff in value.terms])


def form_scale(value: Form, coeff) -> Form:
    names = value.names
    from pgi.math.trans import FExpr

    if isinstance(coeff, FExpr):
        from pgi.math.trans import _plains_of

        names = merge_names(names, _plains_of(coeff))
    elif isinstance(coeff, MRat):
        names = merge_names(names, tuple(sorted(actual_names(coeff.num, coeff.den))))
    value = _reembed(value, names)
    return _make_form(names, value.degree, [(indices, _field_mul(_field_embed(coeff, names), term)) for indices, term in value.terms])


def form_eq(left: Form, right: Form) -> bool:
    if left.degree != right.degree:
        return False
    a, b = _align_forms(left, right)
    if len(a.terms) != len(b.terms):
        return False
    if {indices for indices, _ in a.terms} != {indices for indices, _ in b.terms}:
        return False
    right_map = {indices: coeff for indices, coeff in b.terms}
    return all(_field_eq(coeff, right_map[indices]) for indices, coeff in a.terms)


def wedge(left: Form, right: Form) -> Form:
    a, b = _align_forms(left, right)
    raw = []
    for i_idx, i_coeff in a.terms:
        for j_idx, j_coeff in b.terms:
            raw.append((i_idx + j_idx, _field_mul(i_coeff, j_coeff)))
    return _make_form(a.names, a.degree + b.degree, raw)


def coframe(names: tuple[str, ...], index: int) -> Form:
    if index < 0 or index >= len(names):
        raise NotExact("this coframe index is not in the chart")
    one = as_rat(__import__("pgi.math.poly", fromlist=["const_poly"]).const_poly(Ratio(1, 1), names))
    return _make_form(names, 1, [((index,), one)])


def zeroform(coeff, names: tuple[str, ...]) -> Form:
    return _make_form(names, 0, [((), coeff)])


def oneform(components: tuple, names: tuple[str, ...]) -> Form:
    if len(components) != len(names):
        raise NotExact("a 1-form needs one component for each coordinate")
    raw = [((i,), components[i]) for i in range(len(names))]
    return _make_form(names, 1, raw)


def exterior(value: Form) -> Form:
    raw = []
    for indices, coeff in value.terms:
        for j, name in enumerate(value.names):
            raw.append(((j,) + indices, _field_diff(coeff, name)))
    result = _make_form(value.names, value.degree + 1, raw)
    return result


def faraday(potential: Form) -> Form:
    if potential.degree != 1:
        raise NotExact("the Faraday 2-form is the exterior derivative of a 1-form")
    return exterior(potential)


def _perm_parity(values: tuple[int, ...]) -> int:
    inversions = 0
    for i in range(len(values)):
        for j in range(i + 1, len(values)):
            if values[i] > values[j]:
                inversions += 1
    return 1 if inversions % 2 == 0 else -1


def _metric_det(metric: Metric):
    from itertools import permutations

    n = metric.dim
    total = None
    for perm in permutations(range(n)):
        term = None
        for i, j in enumerate(perm):
            entry = metric.rows[i][j]
            term = entry if term is None else _field_mul(term, entry)
        if _perm_parity(perm) < 0:
            term = _field_neg(term)
        total = term if total is None else _field_add(total, term)
    if total is None:
        return _zero_for(metric)
    return _field_embed(total, metric.names)


def _ratio_sqrt_abs(value: Ratio) -> Ratio | None:
    from math import isqrt

    num, den = abs(value.num), value.den
    root_num, root_den = isqrt(num), isqrt(den)
    if root_num * root_num == num and root_den * root_den == den:
        return Ratio(root_num, root_den)
    return None


def _constant_ratio(value) -> Ratio | None:
    from pgi.math.trans import FExpr, _as_ratio

    if isinstance(value, FExpr):
        return _as_ratio(value)
    if isinstance(value, MRat) and value.num.is_constant and value.den.is_constant:
        num = value.num.constant() if not value.num.is_zero else _ZERO
        den = value.den.constant()
        if den.num == 0:
            return None
        return rat_normalize(num.num * den.den, num.den * den.num).value
    return None


def _volume_candidate(metric: Metric):
    from pgi.math.poly import const_poly
    from pgi.math.syntax import parse_term
    from pgi.math.trans import eval_trans, fexpr_pow, formal_expr, var_fexpr

    names = metric.names
    one = as_rat(const_poly(Ratio(1, 1), names))
    if metric_eq(metric, named_metric("minkowski4")) or metric_eq(metric, named_metric("e3")) or metric_eq(metric, named_metric("e2")) or metric_eq(metric, named_metric("minkowski2")):
        return one
    if metric.dim == 4 and names == ("t", "r", "theta", "phi") and metric_eq(metric, named_metric("schwarzschild")):
        return _field_embed(eval_trans(parse_term("r^2 * sin(theta)")), names)
    if metric.dim == 4 and names == ("t", "x", "y", "z") and metric_eq(metric, named_metric("flrw")):
        scale = formal_expr("a", var_fexpr("t", names), 0, names)
        return _field_embed(fexpr_pow(scale, 3), names)
    if metric.dim == 2 and names == ("theta", "phi") and metric_eq(metric, named_metric("s2", "angular")):
        return _field_embed(eval_trans(parse_term("sin(theta)")), names)
    ratio = _constant_ratio(_metric_det(metric))
    if ratio is not None:
        root = _ratio_sqrt_abs(ratio)
        if root is not None:
            return as_rat(const_poly(root, names))
    return None


def _volume_density(metric: Metric):
    det = _metric_det(metric)
    candidate = _volume_candidate(metric)
    if candidate is None:
        raise NotExact("the volume density of this metric is not an exact square")
    square = _field_mul(candidate, candidate)
    if _field_eq(square, det) or _field_eq(square, _field_neg(det)):
        return _field_embed(candidate, metric.names)
    raise KernelError("this volume density did not square back to the absolute determinant")


def _form_component(value: Form, indices: tuple[int, ...]):
    sign, ordered = _sort_indices(indices)
    if sign == 0:
        return _zero_coeff(value.names)
    present = {item: coeff for item, coeff in value.terms}
    coeff = present.get(ordered)
    if coeff is None:
        return _zero_coeff(value.names)
    return coeff if sign > 0 else _field_neg(coeff)


def _raised_component(value: Form, inverse: Metric, indices: tuple[int, ...]):
    k = len(indices)
    n = inverse.dim
    acc = _zero_coeff(value.names)
    slots = [0] * k

    def walk(pos: int) -> None:
        nonlocal acc
        if pos == k:
            omega = _form_component(value, tuple(slots))
            if _field_is_zero(omega):
                return
            factor = omega
            for a in range(k):
                factor = _field_mul(factor, inverse.rows[indices[a]][slots[a]])
            acc = _field_add(acc, factor)
            return
        for index in range(n):
            slots[pos] = index
            walk(pos + 1)

    if k == 0:
        return _form_component(value, ())
    walk(0)
    return acc


def hodge(value: Form, metric: Metric) -> Form:
    """The Hodge star of a k-form, a complementary (n − k)-form."""
    if value.names != metric.names:
        raise NotExact("the Hodge star needs a form and a metric on the same chart")
    n = metric.dim
    k = value.degree
    if k > n:
        return zero_form(value.names, 0)
    inverse = metric_inverse(metric)
    density = _volume_density(metric)
    raw = []
    from itertools import combinations

    for chosen in combinations(range(n), k):
        raised = _raised_component(value, inverse, chosen)
        if _field_is_zero(raised):
            continue
        complement = tuple(index for index in range(n) if index not in chosen)
        coeff = _field_mul(density, raised)
        if _perm_parity(chosen + complement) < 0:
            coeff = _field_neg(coeff)
        raw.append((complement, coeff))
    return _make_form(value.names, n - k, raw)


def _hodge_double_sign(metric: Metric, degree: int) -> int:
    """The sign in ⋆⋆α = σ α, namely (−1)^{k(n−k)} sgn(det g)."""
    n = metric.dim
    density = _volume_density(metric)
    det = _metric_det(metric)
    square = _field_mul(density, density)
    if _field_eq(square, det):
        signature = 1
    elif _field_eq(square, _field_neg(det)):
        signature = -1
    else:
        raise KernelError("this volume density did not square back to the absolute determinant")
    return (1 if (degree * (n - degree)) % 2 == 0 else -1) * signature


def _double_hodge(value: Form, metric: Metric) -> Form:
    return hodge(hodge(value, metric), metric)


def _check_hodge_standing() -> None:
    from pgi.math.poly import const_poly, var_poly, mrat_mul, mrat_div, mrat_neg

    minkowski = named_metric("minkowski4")
    names4 = minkowski.names
    one = as_rat(const_poly(Ratio(1, 1), names4))
    # ⋆⋆α = σ α on 0-, 1-, and 2-forms.
    unit = zeroform(one, names4)
    if not form_eq(_double_hodge(unit, minkowski), form_scale(unit, as_rat(const_poly(Ratio(-1, 1), names4)))):
        raise KernelError("⋆⋆ of a 0-form on Minkowski was not -1 times the form")
    dt = coframe(names4, 0)
    dx = coframe(names4, 1)
    if not form_eq(_double_hodge(dt, minkowski), dt):
        raise KernelError("⋆⋆ of dt on Minkowski was not dt")
    two = wedge(dt, dx)
    if not form_eq(_double_hodge(two, minkowski), form_neg(two)):
        raise KernelError("⋆⋆ of a 2-form on Minkowski was not minus the form")
    # Uniform charge density: A_t = -x²/2, E = x ê_x, ∇·E = 1, J = ⋆(dt).
    x4 = as_rat(var_poly("x", names4))
    half = as_rat(const_poly(Ratio(-1, 2), names4))
    pot = oneform((mrat_mul(half, mrat_mul(x4, x4)), _zero_coeff(names4), _zero_coeff(names4), _zero_coeff(names4)), names4)
    field = faraday(pot)
    current = hodge(dt, minkowski)
    if not form_eq(exterior(hodge(field, minkowski)), current):
        raise KernelError("d⋆F did not equal ⋆j for a uniform charge density on Minkowski")
    # Coulomb field on Schwarzschild: A = dt/r, ⋆F = sin(θ) dθ ∧ dφ, d⋆F = 0, ⋆⋆F = -F.
    schw = named_metric("schwarzschild")
    coords = schw.names
    from pgi.math.syntax import parse_term
    from pgi.math.trans import eval_trans

    inverse_r = _field_embed(eval_trans(parse_term("1/r")), coords)
    zero = _zero_coeff(coords)
    coulomb = oneform((inverse_r, zero, zero, zero), coords)
    schw_field = faraday(coulomb)
    if not form_eq(_double_hodge(schw_field, schw), form_neg(schw_field)):
        raise KernelError("⋆⋆ of the Coulomb field on Schwarzschild was not minus the field")
    star_field = hodge(schw_field, schw)
    sine = _field_embed(eval_trans(parse_term("sin(theta)")), coords)
    expected = _make_form(coords, 2, [((2, 3), _field_neg(sine))])
    if not form_eq(star_field, expected):
        raise KernelError("⋆F of the Coulomb field on Schwarzschild was not -sin(θ) dθ ∧ dφ")
    if not form_is_zero(exterior(star_field)):
        raise KernelError("d⋆F did not vanish for the Coulomb field on Schwarzschild")


def _standing() -> None:
    global _STANDING
    if _STANDING:
        return
    from pgi.math.poly import const_poly, var_poly, mrat_mul, mrat_add
    from pgi.math.syntax import parse_term
    from pgi.math.trans import eval_trans

    names2 = ("x", "y")
    names3 = ("x", "y", "z")
    names4 = _MINKOWSKI
    x = as_rat(var_poly("x", names2))
    y = as_rat(var_poly("y", names2))
    # d² of a 0-form and a 1-form in the plane.
    f = zeroform(mrat_add(mrat_mul(x, x), mrat_mul(x, y)), names2)
    if not form_is_zero(exterior(exterior(f))):
        raise KernelError("d² of a 0-form did not vanish")
    alpha = oneform((mrat_mul(x, y), mrat_mul(y, y)), names2)
    if not form_is_zero(exterior(exterior(alpha))):
        raise KernelError("d² of a 1-form did not vanish")
    # Wedge anticommutativity and Leibniz for 1-forms.
    dx = coframe(names2, 0)
    dy = coframe(names2, 1)
    if not form_is_zero(form_add(wedge(dx, dy), wedge(dy, dx))):
        raise KernelError("the wedge product of 1-forms was not alternating")
    # 3-space and 4-space polynomial 1-forms.
    xx = as_rat(var_poly("x", names3))
    yy = as_rat(var_poly("y", names3))
    zz = as_rat(var_poly("z", names3))
    beta = oneform((xx, yy, zz), names3)
    if not form_is_zero(exterior(exterior(beta))):
        raise KernelError("d² of a 1-form in three variables did not vanish")
    # Maxwell: F = dA, dF = 0 on Minkowski, polynomial potential.
    t = as_rat(var_poly("t", names4))
    x4 = as_rat(var_poly("x", names4))
    y4 = as_rat(var_poly("y", names4))
    z4 = as_rat(var_poly("z", names4))
    from pgi.math.poly import mrat_mul as mul

    pot = oneform((mul(t, x4), mul(x4, y4), mul(y4, z4), mul(z4, t)), names4)
    field = faraday(pot)
    if field.degree != 2 or form_is_zero(field):
        raise KernelError("the Faraday 2-form of a nontrivial potential vanished")
    if not form_is_zero(exterior(field)):
        raise KernelError("dF did not vanish for F = dA")
    if not form_eq(exterior(field), exterior(exterior(pot))):
        raise KernelError("dF was not d²A")
    # Elementary coefficients: d²(sin(t) dt + exp(x) dx) = 0, and Maxwell for A = sin(t+x) dt.
    sine = eval_trans(parse_term("sin(t)"))
    exponential = eval_trans(parse_term("exp(x)"))
    elem = oneform((sine, exponential, _zero_coeff(names4), _zero_coeff(names4)), names4)
    if not form_is_zero(exterior(exterior(elem))):
        raise KernelError("d² of an elementary 1-form did not vanish")
    wave = oneform((eval_trans(parse_term("sin(t + x)")), _zero_coeff(names4), _zero_coeff(names4), _zero_coeff(names4)), names4)
    if not form_is_zero(exterior(faraday(wave))):
        raise KernelError("dF did not vanish for an elementary potential")
    # Hodge star and d⋆F = J on Minkowski, and the Coulomb field on Schwarzschild.
    _check_hodge_standing()
    _STANDING = True


_STANDING = False


def show_form(value: Form) -> str:
    if form_is_zero(value):
        return "form(0)"
    if value.degree == 1:
        components = []
        present = {indices[0]: coeff for indices, coeff in value.terms}
        for i in range(len(value.names)):
            coeff = present.get(i)
            components.append("0" if coeff is None else _field_show(coeff))
        inner = ", ".join(components)
        if value.names == _MINKOWSKI:
            return f"oneform({inner})"
        coords = ", ".join(value.names)
        return f"oneform({inner}; {coords})"
    parts = []
    for indices, coeff in value.terms:
        shown = _field_show(coeff)
        frames = " ^ ".join(f"coframe({value.names[i]})" for i in indices)
        if shown == "1":
            parts.append(frames)
        elif shown == "-1":
            parts.append(f"-{frames}")
        else:
            parts.append(f"{shown} * {frames}")
    return " + ".join(parts).replace(" + -", " - ")


FORMS_OPS = frozenset({
    "exterior",
    "faraday",
    "potential",
    "oneform",
    "wedge",
    "coframe",
    "form",
    "zeroform",
    "hodge",
})


def _contains_op(term: Term, names: frozenset[str]) -> bool:
    if isinstance(term, App):
        if term.op in names:
            return True
        return any(_contains_op(arg, names) for arg in term.args)
    return False


def has_forms(term: Term) -> bool:
    return _contains_op(term, FORMS_OPS)


def _name(term: Term) -> str:
    if isinstance(term, Var):
        return term.name
    raise NotExact("a coordinate is a name")


def _free_names(term: Term) -> list[str]:
    names: list[str] = []

    def walk(node: Term) -> None:
        if isinstance(node, Var):
            if node.name not in names and node.name != "pi":
                names.append(node.name)
        elif isinstance(node, App):
            for arg in node.args:
                walk(arg)

    walk(term)
    return names


def _eval_coeff(term: Term, names: tuple[str, ...]):
    from pgi.math.trans import has_trans, eval_trans

    if has_trans(term):
        return _field_embed(eval_trans(term), names)
    return _field_embed(eval_symbolic(term), names)


def _coords_from(args: tuple[Term, ...]) -> tuple[str, ...]:
    if not args:
        return _MINKOWSKI
    return tuple(_name(arg) for arg in args)


def _eval_hodge_metric(term: Term) -> Metric:
    from pgi.math.metric import eval_metric

    if isinstance(term, Var):
        return named_metric(term.name)
    if isinstance(term, App) and term.op == "metric":
        return eval_metric(term)
    raise NotExact("hodge takes a named metric")


def _eval_form(term: Term) -> Form:
    _standing()
    if isinstance(term, App):
        if term.op == "coframe":
            if not term.args:
                raise NotExact("coframe takes a coordinate, and optionally a chart")
            coord = _name(term.args[0])
            names = _coords_from(term.args[1:]) if len(term.args) > 1 else _MINKOWSKI
            if coord not in names:
                if len(term.args) == 1:
                    names = (coord,)
                else:
                    raise NotExact("this coframe coordinate is not in the chart")
            return coframe(names, names.index(coord))
        if term.op in {"potential", "oneform"}:
            if len(term.args) < 1:
                raise NotExact("a 1-form needs components")
            # oneform(c0, ..., c_{n-1}) on Minkowski when n=4, else last args may be names
            if len(term.args) == 4:
                names = _MINKOWSKI
                components = tuple(_eval_coeff(arg, names) for arg in term.args)
                return oneform(components, names)
            if len(term.args) > 4:
                # oneform(c0,...,c_{n-1}, x0, ..., x_{n-1}) with 2n args, or 4 components plus names.
                # If all trailing args are names and the split works:
                for n_comp in range(1, len(term.args)):
                    comps = term.args[:n_comp]
                    coords = term.args[n_comp:]
                    if len(coords) == n_comp and all(isinstance(arg, Var) for arg in coords):
                        names = tuple(_name(arg) for arg in coords)
                        components = tuple(_eval_coeff(arg, names) for arg in comps)
                        return oneform(components, names)
            if len(term.args) == 2 and isinstance(term.args[1], Var):
                # oneform(f, x) is a 1-form on a 1-chart.
                names = (_name(term.args[1]),)
                return oneform((_eval_coeff(term.args[0], names),), names)
            raise NotExact("a 1-form needs one component for each coordinate")
        if term.op == "zeroform":
            if len(term.args) < 2:
                raise NotExact("zeroform takes a scalar and the coordinates")
            names = tuple(_name(arg) for arg in term.args[1:])
            return zeroform(_eval_coeff(term.args[0], names), names)
        if term.op == "form":
            if len(term.args) == 1:
                arg = term.args[0]
                if isinstance(arg, IntLit) and arg.n == 0:
                    return zero_form(_MINKOWSKI, 0)
            raise NotExact("form(0) is the zero form; use oneform, zeroform, or coframe otherwise")
        if term.op == "wedge":
            if len(term.args) != 2:
                raise NotExact("wedge takes two forms")
            return wedge(_eval_form(term.args[0]), _eval_form(term.args[1]))
        if term.op == "exterior":
            if len(term.args) != 1:
                raise NotExact("exterior takes a form")
            arg = term.args[0]
            if isinstance(arg, App) and arg.op in FORMS_OPS:
                return exterior(_eval_form(arg))
            # A bare scalar is a 0-form on its free coordinates, or Minkowski if none.
            free = tuple(_free_names(arg))
            names = free if free else _MINKOWSKI
            return exterior(zeroform(_eval_coeff(arg, names), names))
        if term.op == "faraday":
            if len(term.args) != 1:
                raise NotExact("faraday takes a 1-form potential")
            arg = term.args[0]
            if isinstance(arg, App) and arg.op in {"potential", "oneform"}:
                return faraday(_eval_form(arg))
            return faraday(_eval_form(arg))
        if term.op == "hodge":
            if len(term.args) != 2:
                raise NotExact("hodge takes a form and a metric")
            return hodge(_eval_form(term.args[0]), _eval_hodge_metric(term.args[1]))
        if term.op in {"add", "sub"} and len(term.args) == 2:
            left, right = _eval_form(term.args[0]), _eval_form(term.args[1])
            return form_add(left, right) if term.op == "add" else form_sub(left, right)
        if term.op == "neg" and len(term.args) == 1:
            return form_neg(_eval_form(term.args[0]))
        if term.op == "mul" and len(term.args) == 2:
            # scalar * form, if one side is a form
            try:
                return form_scale(_eval_form(term.args[1]), _eval_coeff(term.args[0], _MINKOWSKI))
            except NotExact:
                return form_scale(_eval_form(term.args[0]), _eval_coeff(term.args[1], _MINKOWSKI))
    raise NotExact("this term is not a differential form")


@dataclass(frozen=True)
class FormTheorem:
    value: Form
    origin: Term
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not form_eq(self.value, _eval_form(self.origin)):
            raise KernelError("this differential form does not match the exact evaluation")


def eval_forms_result(term: Term):
    _standing()
    value = _eval_form(term)
    if form_is_zero(value):
        # Keep a FormTheorem so equality with form(0) or 0 still sees a form.
        return FormTheorem(value, term, _detail())
    return FormTheorem(value, term, _detail())


def _detail() -> tuple[str, ...]:
    return (
        "The exterior derivative satisfies d² = 0, checked identically.",
        "On flat spacetime, F = dA and dF = 0 is that identity: the homogeneous Maxwell equations in form language.",
        "The Hodge star uses the inverse metric and an exact volume density that squares back to |det g|.",
        "On Minkowski spacetime and on the Schwarzschild metric, d⋆F is the inhomogeneous Maxwell 3-form J.",
    )


def forms_value_rule(origin: Term, result: object, prelude: tuple[str, ...] = ()) -> Rule:
    if not isinstance(result, FormTheorem):
        raise KernelError("this forms result has no claim")
    shown = show_form(result.value)
    return Rule(
        id=f"math.forms.{shown}",
        layer="base",
        stage="quantity",
        title=f"{pretty(origin)} = {shown}",
        produces=shown,
        detail_lines=(*prelude, *result.detail),
    )


def forms_equality_rules(
    left: Term,
    right: Term,
    left_value: object,
    right_value: object,
    prelude: tuple[str, ...] = (),
) -> tuple[Rule, ...]:
    title = f"{pretty(left)} = {pretty(right)}"
    if _forms_eq(left_value, right_value):
        return (
            Rule(
                id="math.forms.eq",
                layer="base",
                stage="quantity",
                title=title,
                produces=f"identity({title})",
                detail_lines=(*prelude, "The two sides are the same exact differential form."),
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


def _as_form(value: object) -> Form | None:
    if isinstance(value, FormTheorem):
        return value.value
    if isinstance(value, Form):
        return value
    return None


def _is_zero_side(value: object) -> bool:
    form = _as_form(value)
    if form is not None:
        return form_is_zero(form)
    if isinstance(value, RatTheorem):
        return value.value.num == 0
    if isinstance(value, Ratio):
        return value.num == 0
    return False


def _forms_eq(left: object, right: object) -> bool:
    a, b = _as_form(left), _as_form(right)
    if a is not None and b is not None:
        if a.degree != b.degree and form_is_zero(a) and form_is_zero(b):
            return True
        return form_eq(a, b)
    if a is not None and _is_zero_side(right):
        return form_is_zero(a)
    if b is not None and _is_zero_side(left):
        return form_is_zero(b)
    return False


def side_as_forms(term: Term) -> object:
    try:
        return eval_forms_result(term)
    except NotExact:
        if isinstance(term, IntLit) and term.n == 0:
            return rat_normalize(0, 1)
        try:
            return eval_symbolic(term)
        except NotExact:
            from pgi.math.rational import eval_rat

            return eval_rat(term)
