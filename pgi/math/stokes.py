"""Integration of forms and Stokes' theorem on admitted chart rectangles.

A box is a product of closed intervals in the coordinates of a chart
already admitted by the kernel. The integral of a top-degree form over
a box is the iterated exact definite integral of its coefficient. The
integral of a form of degree one less over the boundary uses the
induced orientation: on the face where the k-th coordinate is the upper
bound the sign is (−1)^k, and the opposite on the lower face.

Stokes' theorem is the identity ∫_Ω dω = ∫_∂Ω ω, checked by evaluating
both sides exactly. An antiderivative is kept only when its derivative
is the integrand. Bounds may be rationals or admitted elementary values
such as π.

Certificates are identities, checked exactly, with no approximation.
"""

from __future__ import annotations

from dataclasses import dataclass

from pgi.math.forms import (
    Form,
    _eval_form,
    form_is_zero,
    merge_names,
    show_form,
)
from pgi.math.kernel import KernelError, NotExact
from pgi.math.metric import _field_is_zero, _field_show, _lift
from pgi.math.poly import (
    MRat,
    _deg_in,
    _from_map,
    as_rat,
    const_poly,
    mpoly_eq,
    mrat_div,
    mrat_sub,
    show_rat,
    var_poly,
    zero_poly,
)
from pgi.math.rational import Ratio, RatTheorem, rat_normalize
from pgi.math.syntax import App, IntLit, Term, Var, pretty
from pgi.math.trans import (
    FExpr,
    _plains_of,
    _reduce,
    _subst_poly,
    const_fexpr,
    eval_trans,
    fexpr_add,
    fexpr_diff,
    fexpr_eq,
    fexpr_mul,
    fexpr_neg,
    fexpr_sub,
    show_fexpr,
    var_fexpr,
)
from pgi.model import Rule


_ZERO = Ratio(0, 1)
_ONE = Ratio(1, 1)


def _as_fexpr(value, plains: tuple[str, ...] = ()) -> FExpr:
    if isinstance(value, FExpr):
        return value
    if isinstance(value, MRat):
        return FExpr(value, ())
    if isinstance(value, Ratio):
        return const_fexpr(value, plains)
    raise NotExact("this coefficient is not an admitted expression")


def _zero_f(plains: tuple[str, ...] = ()) -> FExpr:
    return const_fexpr(_ZERO, plains)


def _is_zero_f(value: FExpr) -> bool:
    return fexpr_eq(value, _zero_f(_plains_of(value)))


def _eval_bound(term: Term) -> FExpr:
    if isinstance(term, IntLit):
        return const_fexpr(Ratio(term.n, 1), ())
    if isinstance(term, Var) and term.name == "pi":
        return var_fexpr("pi", ("pi",))
    from pgi.math.trans import has_trans, eval_trans
    from pgi.math.poly import eval_symbolic

    if has_trans(term) or (isinstance(term, Var) and term.name == "pi"):
        return _as_fexpr(eval_trans(term))
    return _as_fexpr(eval_symbolic(term))


@dataclass(frozen=True)
class Box:
    """An axis-aligned product of intervals, with the given coordinate order."""

    names: tuple[str, ...]
    bounds: tuple[tuple[FExpr, FExpr], ...]

    def __post_init__(self) -> None:
        if not self.names or len(self.names) != len(self.bounds):
            raise KernelError("a box needs one interval for each coordinate")
        if len(set(self.names)) != len(self.names):
            raise KernelError("a box cannot repeat a coordinate")


@dataclass(frozen=True)
class Boundary:
    box: Box


def _fexpr_subst(value: FExpr, name: str, image: FExpr) -> FExpr:
    from pgi.math.trans import Atom, _align, as_rat, mrat_div, _reduce

    image = _as_fexpr(image)
    if not image.atoms:
        image = _clean_fexpr(image)
    else:
        image = _reduce(image)
    value = _reduce(value)
    # A bare variable must become the image itself, without leftover unused names.
    if fexpr_eq(value, var_fexpr(name, _plains_of(value))):
        return image
    # Substitute inside atoms first, then collapse special values without
    # embedding a constant that still carries leftover plains such as pi.
    new_atoms = tuple(Atom(atom.op, _fexpr_subst(atom.arg, name, image), atom.params) for atom in value.atoms)
    mid = _collapse_specials(FExpr(value.body, new_atoms))
    mid, image = _align(mid, image)
    if name not in mid.body.num.names and name not in mid.body.den.names:
        return _clean_fexpr(mid)
    num = _subst_poly(mid.body.num, name, image.body)
    den = _subst_poly(mid.body.den, name, image.body)
    if not isinstance(num, MRat):
        num = as_rat(num)
    if not isinstance(den, MRat):
        den = as_rat(den)
    return _clean_fexpr(_collapse_specials(FExpr(mrat_div(num, den), mid.atoms)))


def _collapse_specials(value: FExpr) -> FExpr:
    from pgi.math.trans import _prune, _reduce_pythagoras, _special_value, _substitute_slot

    changed = True
    guard = 0
    while changed and guard < 16:
        changed = False
        guard += 1
        value = _reduce_pythagoras(value)
        for index, atom in enumerate(value.atoms):
            special = _special_value(atom)
            if special is not None:
                value = _substitute_slot(value, index, _clean_fexpr(special))
                changed = True
                break
    return _prune(_reduce_pythagoras(value))


def _clean_fexpr(value: FExpr) -> FExpr:
    from pgi.math.trans import _as_ratio

    if value.atoms:
        value = _collapse_specials(value)
    rat = _as_ratio(value)
    if rat is not None:
        return const_fexpr(rat, ())
    return value


def _independent_of(value: FExpr, name: str) -> bool:
    from pgi.math.trans import _degree_in

    if _degree_in(value, name):
        return False
    for atom in value.atoms:
        if not _independent_of(atom.arg, name):
            return False
    return True


def _atom_is(atom, op: str, name: str) -> bool:
    return atom.op == op and fexpr_eq(atom.arg, var_fexpr(name, _plains_of(atom.arg)))


def _antideriv(value: FExpr, name: str) -> FExpr:
    """An antiderivative in `name`, kept only when its derivative is the integrand."""
    value = _reduce(value)
    plains = _merge(_plains_of(value), (name,))
    result = _antideriv_body(value, name, plains)
    if not fexpr_eq(fexpr_diff(result, name), value):
        raise KernelError("this antiderivative did not differentiate back to the integrand")
    return result


def _merge(*groups: tuple[str, ...]) -> tuple[str, ...]:
    seen: list[str] = []
    for group in groups:
        for name in group:
            if name not in seen:
                seen.append(name)
    return tuple(seen)


def _antideriv_body(value: FExpr, name: str, plains: tuple[str, ...]) -> FExpr:
    from pgi.math.trans import Atom, _degree_in, _SLOT, _plain_names

    value = _reduce(value)
    # If the expression does not depend on name, the antiderivative is value * name.
    if _independent_of(value, name):
        return fexpr_mul(value, var_fexpr(name, plains))

    # Polynomial in `name` with coefficients independent of `name`, including
    # atoms that do not depend on `name`.
    if all(_independent_of(atom.arg, name) for atom in value.atoms) and _deg_in(value.body.den, name) <= 0:
        return _integrate_poly_fexpr(value, name, plains)

    # Linear combination of 1, name^k (handled above), sin(name), cos(name), exp(name)
    # with coefficients independent of name.
    special = _integrate_trig_exp(value, name, plains)
    if special is not None:
        return special
    raise NotExact("this integrand has no exact elementary antiderivative in the kernel")


def _integrate_poly_fexpr(value: FExpr, name: str, plains: tuple[str, ...]) -> FExpr:
    from pgi.math.trans import _atom_names, as_rat, mrat_from

    names = value.body.num.names
    if name not in names:
        # den already independent; multiply by name
        return fexpr_mul(value, var_fexpr(name, plains))
    if _deg_in(value.body.den, name) > 0:
        raise NotExact("this rational function has no exact elementary antiderivative in the kernel")
    idx = names.index(name)
    # Integrate the numerator termwise, keep the denominator.
    terms: dict[tuple[int, ...], Ratio] = {}
    for monom, coeff in value.body.num.terms:
        k = monom[idx] if idx < len(monom) else 0
        new = list(monom) if len(monom) == len(names) else list(monom) + [0] * (len(names) - len(monom))
        new[idx] = k + 1
        new_coeff = rat_normalize(coeff.num, coeff.den * (k + 1)).value
        key = tuple(new)
        if key in terms:
            terms[key] = rat_normalize(
                terms[key].num * new_coeff.den + new_coeff.num * terms[key].den,
                terms[key].den * new_coeff.den,
            ).value
        else:
            terms[key] = new_coeff
    anti_num = _from_map(names, terms)
    anti = FExpr(mrat_div(as_rat(anti_num), as_rat(value.body.den)), value.atoms)
    return _reduce(anti)


def _integrate_trig_exp(value: FExpr, name: str, plains: tuple[str, ...]) -> FExpr | None:
    from pgi.math.trans import Atom, _degree_in, _SLOT

    # Require: body has degree 0 in `name` itself; each atom that depends on name
    # is sin(name), cos(name), or exp(name); body is at most degree 1 in those slots.
    names = value.body.num.names
    if name in names and _deg_in(value.body.num, name) > 0:
        return None
    if _deg_in(value.body.den, name) > 0:
        return None
    slot_map: dict[int, str] = {}
    for index, atom in enumerate(value.atoms):
        if _independent_of(atom.arg, name):
            continue
        if atom.op in {"sin", "cos", "exp"} and fexpr_eq(atom.arg, var_fexpr(name, _plains_of(atom.arg))):
            slot_map[index] = atom.op
            if _deg_in(value.body.num, f"{_SLOT}{index}") > 1 or _deg_in(value.body.den, f"{_SLOT}{index}") > 0:
                return None
        else:
            return None
    if not slot_map:
        return None
    # Split the numerator into terms that are constant, *sin, *cos, or *exp in name.
    # Because degree in each special slot is at most 1, a monom has at most one such slot
    # to power 1, or none.
    anti = _zero_f(plains)
    x = var_fexpr(name, plains)
    from pgi.math.trans import _atom_expr, _embed, _merge_atoms, _merge_names, as_rat

    def coeff_from_monom(monom, coeff, skip: int | None):
        rest = list(monom)
        if skip is not None:
            slot = f"{_SLOT}{skip}"
            if slot in names:
                rest[names.index(slot)] = 0
        # remaining monom must not involve `name`
        if name in names and (monom[names.index(name)] if names.index(name) < len(monom) else 0):
            return None
        return FExpr(as_rat(_from_map(names, {tuple(rest): coeff})), value.atoms)

    den = FExpr(as_rat(value.body.den), value.atoms)
    # termwise
    for monom, coeff in value.body.num.terms:
        specials = []
        for index, op in slot_map.items():
            slot = f"{_SLOT}{index}"
            if slot in names and names.index(slot) < len(monom) and monom[names.index(slot)]:
                specials.append(index)
        if len(specials) > 1:
            return None
        if not specials:
            # constant in the specials: ∫ c d name = c * name, but c/den
            c = coeff_from_monom(monom, coeff, None)
            if c is None:
                return None
            anti = fexpr_add(anti, fexpr_div_safe(fexpr_mul(c, x), den, plains))
            continue
        index = specials[0]
        op = slot_map[index]
        c = coeff_from_monom(monom, coeff, index)
        if c is None:
            return None
        piece = _atom_expr(op, x, plains)
        if op == "sin":
            prim = fexpr_neg(_atom_expr("cos", x, plains))
        elif op == "cos":
            prim = _atom_expr("sin", x, plains)
        else:
            prim = _atom_expr("exp", x, plains)
        anti = fexpr_add(anti, fexpr_div_safe(fexpr_mul(c, prim), den, plains))
    return _reduce(anti)


def fexpr_div_safe(num: FExpr, den: FExpr, plains: tuple[str, ...]) -> FExpr:
    from pgi.math.trans import fexpr_div

    if _is_zero_f(den):
        raise NotExact("division by zero")
    if fexpr_eq(den, const_fexpr(_ONE, plains)):
        return num
    return fexpr_div(num, den)


def _definite(value: FExpr, name: str, lo: FExpr, hi: FExpr) -> FExpr:
    anti = _antideriv(value, name)
    return fexpr_sub(_fexpr_subst(anti, name, hi), _fexpr_subst(anti, name, lo))


def _iterated_integral(coeff, names: tuple[str, ...], bounds: tuple[tuple[FExpr, FExpr], ...]) -> FExpr:
    value = _as_fexpr(coeff, names)
    for name, (lo, hi) in reversed(list(zip(names, bounds))):
        value = _definite(value, name, lo, hi)
    return _reduce(value)


def _component(form: Form, indices: tuple[int, ...]):
    for found, coeff in form.terms:
        if found == indices:
            return coeff
    return _zero_f(form.names)


def _volume_sign_and_indices(form: Form, box_names: tuple[str, ...]) -> tuple[int, tuple[int, ...]]:
    if form.degree != len(box_names):
        raise NotExact("a volume integral needs a form whose degree is the dimension of the box")
    # Map box coordinates into the form's chart.
    missing = [name for name in box_names if name not in form.names]
    if missing:
        raise NotExact("this box uses a coordinate that is not on the form")
    form_indices = tuple(form.names.index(name) for name in box_names)
    from pgi.math.forms import _sort_indices

    sign, ordered = _sort_indices(form_indices)
    return sign, ordered


def volume_integral(form: Form, box: Box) -> FExpr:
    sign, ordered = _volume_sign_and_indices(form, box.names)
    coeff = _component(form, ordered)
    value = _iterated_integral(coeff, box.names, box.bounds)
    if sign < 0:
        value = fexpr_neg(value)
    return _reduce(value)


def boundary_integral(form: Form, box: Box) -> FExpr:
    n = len(box.names)
    if form.degree != n - 1:
        raise NotExact("a boundary integral needs a form whose degree is one less than the dimension of the box")
    missing = [name for name in box.names if name not in form.names]
    if missing:
        raise NotExact("this box uses a coordinate that is not on the form")
    total = _zero_f(box.names)
    from pgi.math.forms import _sort_indices

    for k, name in enumerate(box.names):
        face_names = tuple(other for i, other in enumerate(box.names) if i != k)
        face_bounds = tuple(bound for i, bound in enumerate(box.bounds) if i != k)
        # Component of dx^{all except k} in box order, pulled back to the form chart.
        box_indices = tuple(form.names.index(other) for other in face_names)
        # The n-1 form in box order omitting k corresponds to inserting k at position k.
        # Sign of (k, 0, 1, ..., hat k, ...): (-1)^k times the ordered face.
        sign_place = -1 if (k % 2) else 1
        face_sign, ordered = _sort_indices(box_indices)
        coeff = _component(form, ordered)
        orient = sign_place * face_sign
        lo, hi = box.bounds[k]
        # ∫_{x_k=hi} orient * coeff − ∫_{x_k=lo} orient * coeff
        at_hi = _fexpr_subst(_as_fexpr(coeff, form.names), name, hi)
        at_lo = _fexpr_subst(_as_fexpr(coeff, form.names), name, lo)
        if face_names:
            i_hi = _iterated_integral(at_hi, face_names, face_bounds)
            i_lo = _iterated_integral(at_lo, face_names, face_bounds)
        else:
            # 0-form on an interval: just the values.
            i_hi, i_lo = at_hi, at_lo
        piece = fexpr_sub(i_hi, i_lo)
        if orient < 0:
            piece = fexpr_neg(piece)
        total = fexpr_add(total, piece)
    return _reduce(total)


def stokes_residual(form: Form, box: Box) -> FExpr:
    from pgi.math.forms import exterior

    left = volume_integral(exterior(form), box)
    right = boundary_integral(form, box)
    return _reduce(fexpr_sub(left, right))


def _check_standing() -> None:
    from pgi.math.forms import exterior, oneform, zeroform, wedge, coframe
    from pgi.math.poly import eval_symbolic
    from pgi.math.syntax import parse_term

    def R(text):
        return eval_symbolic(parse_term(text))

    # FTC: ∫_0^2 d(x^2) = 4 = (x^2)|_0^2.
    z = const_fexpr(_ZERO, ())
    two = const_fexpr(Ratio(2, 1), ())
    one = const_fexpr(_ONE, ())
    box1 = Box(("x",), ((z, two),))
    f = zeroform(R("x^2"), ("x",))
    if not fexpr_eq(volume_integral(exterior(f), box1), const_fexpr(Ratio(4, 1), ())):
        raise KernelError("the fundamental theorem on [0, 2] for x^2 failed")
    if not fexpr_eq(boundary_integral(f, box1), const_fexpr(Ratio(4, 1), ())):
        raise KernelError("the endpoint evaluation of x^2 on [0, 2] failed")
    if not _is_zero_f(stokes_residual(f, box1)):
        raise KernelError("Stokes failed for a 0-form on an interval")

    # ω = −y dx + x dy on the unit square: both sides 2.
    box2 = Box(("x", "y"), ((z, one), (z, one)))
    omega = oneform((R("-y"), R("x")), ("x", "y"))
    two_v = const_fexpr(Ratio(2, 1), ())
    if not fexpr_eq(volume_integral(exterior(omega), box2), two_v):
        raise KernelError("the unit-square integral of d(−y dx + x dy) was not 2")
    if not fexpr_eq(boundary_integral(omega, box2), two_v):
        raise KernelError("the unit-square boundary integral of −y dx + x dy was not 2")
    if not _is_zero_f(stokes_residual(omega, box2)):
        raise KernelError("Stokes failed for −y dx + x dy on the unit square")

    # ω = x dy on the unit square: both sides 1.
    omega2 = oneform((R("0"), R("x")), ("x", "y"))
    if not fexpr_eq(volume_integral(exterior(omega2), box2), one):
        raise KernelError("the unit-square integral of dx ∧ dy was not 1")
    if not _is_zero_f(stokes_residual(omega2, box2)):
        raise KernelError("Stokes failed for x dy on the unit square")

    # 2-form x dy ∧ dz on the unit cube: dω = dx∧dy∧dz, both sides 1.
    from pgi.math.forms import form_scale

    dy = coframe(("x", "y", "z"), 1)
    dz = coframe(("x", "y", "z"), 2)
    omega3 = form_scale(wedge(dy, dz), R("x"))
    box3 = Box(("x", "y", "z"), ((z, one), (z, one), (z, one)))
    if not fexpr_eq(volume_integral(exterior(omega3), box3), one):
        raise KernelError("the unit-cube integral of dx ∧ dy ∧ dz was not 1")
    if not _is_zero_f(stokes_residual(omega3, box3)):
        raise KernelError("Stokes failed for x dy ∧ dz on the unit cube")

    # Angular rectangle: ω = −cos(θ) dφ, dω = sin(θ) dθ ∧ dφ.
    from pgi.math.trans import eval_trans

    def T(text):
        return eval_trans(parse_term(text))

    lo, hi = const_fexpr(Ratio(1, 1), ()), const_fexpr(Ratio(2, 1), ())
    box_ang = Box(("theta", "phi"), ((lo, hi), (z, one)))
    omega_s = oneform((_zero_f(("theta", "phi")), T("-cos(theta)")), ("theta", "phi"))
    if not _is_zero_f(stokes_residual(omega_s, box_ang)):
        raise KernelError("Stokes failed for -cos(theta) d phi on an angular rectangle")


_STANDING = False


def _standing() -> None:
    global _STANDING
    if _STANDING:
        return
    _check_standing()
    _STANDING = True


STOKES_OPS = frozenset({"integral", "box", "boundary", "stokes"})


def _contains_op(term: Term, names: frozenset[str]) -> bool:
    if isinstance(term, App):
        if term.op in names:
            return True
        return any(_contains_op(arg, names) for arg in term.args)
    return False


def has_stokes(term: Term) -> bool:
    return _contains_op(term, STOKES_OPS)


def _name(term: Term) -> str:
    if isinstance(term, Var):
        return term.name
    raise NotExact("a box coordinate is a name")


def _eval_box(term: Term) -> Box:
    if not isinstance(term, App) or term.op != "box":
        raise NotExact("a region is a box of coordinates and bounds")
    args = term.args
    if len(args) % 3 != 0 or not args:
        raise NotExact("box takes groups of a coordinate, a lower bound, and an upper bound")
    names: list[str] = []
    bounds: list[tuple[FExpr, FExpr]] = []
    for i in range(0, len(args), 3):
        names.append(_name(args[i]))
        bounds.append((_eval_bound(args[i + 1]), _eval_bound(args[i + 2])))
    return Box(tuple(names), tuple(bounds))


def _eval_region(term: Term):
    if isinstance(term, App) and term.op == "boundary":
        if len(term.args) != 1:
            raise NotExact("boundary takes a box")
        return Boundary(_eval_box(term.args[0]))
    return _eval_box(term)


def _show_value(value: FExpr) -> str:
    if _is_zero_f(value):
        return "0"
    from pgi.math.trans import _as_ratio

    rat = _as_ratio(_reduce(value))
    if rat is not None:
        if rat.den == 1:
            return str(rat.num)
        return show_rat(as_rat(const_poly(rat, ())))
    return show_fexpr(value)


def _eval_stokes_expr(term: Term) -> FExpr:
    _standing()
    if isinstance(term, App):
        if term.op == "stokes":
            if len(term.args) != 2:
                raise NotExact("stokes takes a form and a box")
            return stokes_residual(_eval_form(term.args[0]), _eval_box(term.args[1]))
        if term.op == "integral":
            if len(term.args) != 2:
                raise NotExact("integral takes a form and a region")
            form = _eval_form(term.args[0])
            region = _eval_region(term.args[1])
            if isinstance(region, Boundary):
                return boundary_integral(form, region.box)
            return volume_integral(form, region)
        if term.op in {"add", "sub"} and len(term.args) == 2:
            left, right = _eval_stokes_expr(term.args[0]), _eval_stokes_expr(term.args[1])
            return fexpr_add(left, right) if term.op == "add" else fexpr_sub(left, right)
        if term.op == "neg" and len(term.args) == 1:
            return fexpr_neg(_eval_stokes_expr(term.args[0]))
    if isinstance(term, IntLit):
        return const_fexpr(Ratio(term.n, 1), ())
    raise NotExact("this term is not an integral or a Stokes identity")


@dataclass(frozen=True)
class StokesTheorem:
    value: FExpr
    origin: Term
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if has_stokes(self.origin):
            expected = _eval_stokes_expr(self.origin)
            if not fexpr_eq(self.value, expected):
                raise KernelError("this integral does not match the exact evaluation")


def eval_stokes_result(term: Term):
    _standing()
    return StokesTheorem(_eval_stokes_expr(term), term, _detail())


def _detail() -> tuple[str, ...]:
    return (
        "The integral of a top-degree form over a box is the iterated exact definite integral of its coefficient.",
        "An antiderivative is kept only when its derivative is the integrand.",
        "Stokes' theorem is the identity of the integral of dω over the box with the integral of ω over the oriented boundary.",
    )


def stokes_value_rule(origin: Term, result: object, prelude: tuple[str, ...] = ()) -> Rule:
    if not isinstance(result, StokesTheorem):
        raise KernelError("this integral has no claim")
    shown = _show_value(result.value)
    return Rule(
        id=f"math.stokes.{shown}",
        layer="base",
        stage="quantity",
        title=f"{pretty(origin)} = {shown}",
        produces=shown,
        detail_lines=(*prelude, *result.detail),
    )


def stokes_equality_rules(left: Term, right: Term, left_value: object, right_value: object, prelude: tuple[str, ...] = ()):
    title = f"{pretty(left)} = {pretty(right)}"
    if _stokes_eq(left_value, right_value):
        return (
            Rule(
                id="math.stokes.eq",
                layer="base",
                stage="quantity",
                title=title,
                produces=f"identity({title})",
                detail_lines=(*prelude, "The two sides are the same exact integral."),
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


def _as_value(value: object) -> FExpr | None:
    if isinstance(value, StokesTheorem):
        return value.value
    if isinstance(value, FExpr):
        return value
    return None


def _is_zero_side(value: object) -> bool:
    expr = _as_value(value)
    if expr is not None:
        return _is_zero_f(expr)
    if isinstance(value, RatTheorem):
        return value.value.num == 0
    if isinstance(value, Ratio):
        return value.num == 0
    return False


def _stokes_eq(left: object, right: object) -> bool:
    a, b = _as_value(left), _as_value(right)
    if a is not None and b is not None:
        return fexpr_eq(a, b)
    if a is not None and _is_zero_side(right):
        return _is_zero_f(a)
    if b is not None and _is_zero_side(left):
        return _is_zero_f(b)
    return False


def side_as_stokes(term: Term) -> object:
    if has_stokes(term):
        return eval_stokes_result(term)
    if isinstance(term, IntLit):
        return StokesTheorem(const_fexpr(Ratio(term.n, 1), ()), term, ())
    from pgi.math.trans import has_trans, eval_trans

    if has_trans(term):
        return _as_fexpr(eval_trans(term))
    from pgi.math.poly import eval_symbolic, has_symbolic

    if has_symbolic(term) or isinstance(term, Var):
        return _as_fexpr(eval_symbolic(term))
    raise NotExact("this term is not an integral, a Stokes identity, or an exact scalar")
