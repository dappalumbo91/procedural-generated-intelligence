"""Tetrads, the spin connection, and the Dirac operator on a diagonal metric.

A tetrad is a coframe e^a of 1-forms satisfying g_μν = η_ab e^a_μ e^b_ν,
with η = diag(-1, 1, 1, 1). The spin connection is the unique metric-
compatible, torsion-free so(3,1)-valued 1-form obeying Cartan's first
structure equation, de^a + ω^a_b ∧ e^b = 0. The Dirac operator is
D = γ^a e_a^μ (∂_μ + (1/4) ω_μ^{bc} γ_b γ_c).

The first admitted frames are the identity tetrad on Minkowski spacetime
and the diagonal tetrad of flat FLRW, e^0 = dt and e^i = a(t) dx^i. On
Minkowski the connection vanishes and D is γ^μ ∂_μ. On flat FLRW the
connection is ω^0_i = ω^i_0 = (da/dt)/a e^i, torsion vanishes, the
metric rebuilds exactly, and a constant spinor ψ satisfies
Dψ = (3/2) (da/dt)/a γ^0 ψ.

Certificates are identities, checked exactly, with no approximation.
"""

from __future__ import annotations

from dataclasses import dataclass

from pgi.math.cnum import (
    CNum,
    c_add,
    c_as_ratio,
    c_eq,
    c_from_ratio,
    c_is_zero,
    c_mul,
    c_neg,
    c_zero,
    show_cnum,
)
from pgi.math.forms import (
    Form,
    coframe,
    exterior,
    form_add,
    form_eq,
    form_is_zero,
    form_neg,
    form_scale,
    merge_names,
    oneform,
    show_form,
    wedge,
    zero_form,
    _eval_form,
    _reembed,
)
from pgi.math.hilbert import CMatrix
from pgi.math.kernel import KernelError, NotExact
from pgi.math.lorentz import gamma, minkowski_eta
from pgi.math.metric import (
    Metric,
    _field_add,
    _field_embed,
    _field_eq,
    _field_is_zero,
    _field_mul,
    _field_neg,
    _zero_for,
    metric_eq,
    named_metric,
)
from pgi.math.poly import as_rat, const_poly
from pgi.math.rational import Ratio, RatTheorem, rat_normalize
from pgi.math.syntax import App, IntLit, Term, Var, pretty
from pgi.math.trans import (
    FExpr,
    _plains_of,
    _reduce,
    const_fexpr,
    eval_trans,
    fexpr_add,
    fexpr_div,
    fexpr_eq,
    fexpr_mul,
    fexpr_neg,
    formal_expr,
    show_fexpr,
    var_fexpr,
)
from pgi.model import Rule


_ZERO = Ratio(0, 1)
_ONE = Ratio(1, 1)
_HALF = Ratio(1, 2)
_THREE_HALVES = Ratio(3, 2)
_NEG_ONE = Ratio(-1, 1)
_ETA = (-1, 1, 1, 1)


def _r(n: int, d: int = 1) -> Ratio:
    return rat_normalize(n, d).value


def _f_one(names: tuple[str, ...]) -> FExpr:
    return const_fexpr(_ONE, names)


def _f_zero(names: tuple[str, ...]) -> FExpr:
    return const_fexpr(_ZERO, names)


def _as_f(value, names: tuple[str, ...] = ()) -> FExpr:
    from pgi.math.poly import MRat
    from pgi.math.metric import _lift

    if isinstance(value, FExpr):
        return value
    if isinstance(value, Ratio):
        return const_fexpr(value, names)
    if isinstance(value, CNum):
        rat = c_as_ratio(value)
        if rat is None:
            raise NotExact("this complex coefficient is not a rational")
        return const_fexpr(rat, names)
    if isinstance(value, MRat):
        return _lift(value)
    if isinstance(value, int):
        return const_fexpr(Ratio(value, 1), names)
    raise NotExact("this coefficient is not an admitted expression")


def _coeff_of(form: Form, name: str):
    if form.degree != 1:
        raise NotExact("a tetrad coframe is a 1-form")
    if name not in form.names:
        return _f_zero(form.names)
    index = form.names.index(name)
    for indices, coeff in form.terms:
        if indices == (index,):
            return coeff
    return _f_zero(form.names)


@dataclass(frozen=True)
class Tetrad:
    """An orthonormal coframe e^0, e^1, e^2, e^3 on a 4-chart."""

    names: tuple[str, ...]
    coframes: tuple[Form, Form, Form, Form]

    def __post_init__(self) -> None:
        if len(self.names) != 4 or len(set(self.names)) != 4:
            raise KernelError("a tetrad is a coframe on a 4-chart")
        for frame in self.coframes:
            if frame.degree != 1:
                raise KernelError("each tetrad leg is a 1-form")
            if frame.names != self.names:
                raise KernelError("every tetrad leg must use the same chart")


@dataclass(frozen=True)
class SpinConnection:
    """ω^a_b as a 4×4 array of 1-forms on the tetrad's chart."""

    names: tuple[str, ...]
    components: tuple[tuple[Form, ...], ...]

    def __post_init__(self) -> None:
        if len(self.components) != 4 or any(len(row) != 4 for row in self.components):
            raise KernelError("a spin connection is 4 by 4")
        for row in self.components:
            for form in row:
                if form.degree != 1 and not form_is_zero(form):
                    raise KernelError("each spin-connection component is a 1-form")
                if form.names != self.names and not form_is_zero(form):
                    raise KernelError("the spin connection must use the tetrad chart")


def minkowski_tetrad() -> Tetrad:
    names = ("t", "x", "y", "z")
    frames = tuple(coframe(names, i) for i in range(4))
    return Tetrad(names, frames)  # type: ignore[arg-type]


def flrw_tetrad() -> Tetrad:
    from pgi.math.trans import formal_expr, var_fexpr

    names = ("t", "x", "y", "z")
    scale = formal_expr("a", var_fexpr("t", names), 0, names)
    e0 = coframe(names, 0)
    ei = tuple(form_scale(coframe(names, i), scale) for i in range(1, 4))
    return Tetrad(names, (e0, ei[0], ei[1], ei[2]))


def named_tetrad(name: str) -> Tetrad:
    if name in {"minkowski4", "m4", "minkowski"}:
        return minkowski_tetrad()
    if name in {"flrw", "friedmann"}:
        return flrw_tetrad()
    raise NotExact("a tetrad is admitted here for minkowski4 or flrw")


def tetrad_metric(tetrad: Tetrad) -> Metric:
    names = tetrad.names
    rows = []
    for mu, _mu_name in enumerate(names):
        row = []
        for nu, _nu_name in enumerate(names):
            total = const_fexpr(_ZERO, ())
            for a, ea in enumerate(tetrad.coframes):
                ea_mu = _coeff_of(ea, names[mu])
                for b, eb in enumerate(tetrad.coframes):
                    if _ETA[a] == 0:
                        continue
                    eb_nu = _coeff_of(eb, names[nu])
                    piece = _field_mul(ea_mu, eb_nu)
                    if _ETA[a] < 0:
                        piece = _field_neg(piece)
                    # η_ab is diagonal, so only a == b contributes.
                    if a == b:
                        total = _field_add(total, piece)
            row.append(_field_embed(total, names))
        rows.append(tuple(row))
    return Metric(names, tuple(rows))


def inverse_tetrad(tetrad: Tetrad) -> tuple[tuple[object, ...], ...]:
    """e_a^μ, checked by e^a_μ e_a^ν = δ^ν_μ and e^a_μ e_b^μ = δ^a_b."""
    names = tetrad.names
    # Diagonal frames only: e^a = λ_a dx^a (no sum), λ_a ≠ 0, e_a^a = 1/λ_a.
    lambdas = []
    for a, frame in enumerate(tetrad.coframes):
        # The frame must be a multiple of a single coframe vector.
        if len(frame.terms) != 1:
            raise NotExact("this tetrad is not diagonal")
        (idx,), coeff = frame.terms[0]
        if idx != a:
            raise NotExact("this tetrad is not aligned with the coordinate chart")
        if _field_is_zero(coeff):
            raise NotExact("a tetrad leg cannot vanish")
        lambdas.append(coeff)
    # inverse components
    inv = []
    for a in range(4):
        row = []
        for mu in range(4):
            if a == mu:
                row.append(fexpr_div(_as_f(_f_one(names), names), _as_f(lambdas[a], names)))
            else:
                row.append(_f_zero(names))
        inv.append(tuple(row))
    _check_inverse(tetrad, tuple(inv))
    return tuple(inv)


def _as_fexpr(value, names: tuple[str, ...]) -> FExpr:
    if isinstance(value, FExpr):
        return value
    if isinstance(value, Ratio):
        return const_fexpr(value, names)
    from pgi.math.poly import MRat
    from pgi.math.trans import FExpr as FE

    if isinstance(value, MRat):
        return FE(value, ())
    raise NotExact("this tetrad coefficient is not an admitted expression")


def _check_inverse(tetrad: Tetrad, inv) -> None:
    names = tetrad.names
    # e^a_μ e_a^ν = δ^ν_μ
    for nu, nu_name in enumerate(names):
        for mu, mu_name in enumerate(names):
            total = _f_zero(names)
            for a, frame in enumerate(tetrad.coframes):
                ea_mu = _as_fexpr(_coeff_of(frame, mu_name), names)
                ea_inv = _as_fexpr(inv[a][nu], names)
                total = fexpr_add(total, fexpr_mul(ea_mu, ea_inv))
            expected = _f_one(names) if mu == nu else _f_zero(names)
            if not fexpr_eq(total, expected):
                raise KernelError("the inverse tetrad did not multiply back to the identity")
    # e^a_μ e_b^μ = δ^a_b
    for a, fa in enumerate(tetrad.coframes):
        for b in range(4):
            total = _f_zero(names)
            for mu, mu_name in enumerate(names):
                total = fexpr_add(total, fexpr_mul(_as_fexpr(_coeff_of(fa, mu_name), names), _as_fexpr(inv[b][mu], names)))
            expected = _f_one(names) if a == b else _f_zero(names)
            if not fexpr_eq(total, expected):
                raise KernelError("the inverse tetrad did not multiply back on the left")


def flrw_spin_connection(tetrad: Tetrad) -> SpinConnection:
    names = tetrad.names
    zero = zero_form(names, 1)
    # ω^0_i = ω^i_0 = (ȧ/a) e^i
    scale = formal_expr("a", var_fexpr("t", names), 0, names)
    adot = formal_expr("a", var_fexpr("t", names), 1, names)
    houd = fexpr_div(adot, scale)
    rows = [[zero for _ in range(4)] for _ in range(4)]
    for i in range(1, 4):
        form = form_scale(tetrad.coframes[i], houd)
        rows[0][i] = form
        rows[i][0] = form
    return SpinConnection(names, tuple(tuple(row) for row in rows))


def minkowski_spin_connection(tetrad: Tetrad) -> SpinConnection:
    zero = zero_form(tetrad.names, 1)
    return SpinConnection(tetrad.names, tuple(tuple(zero for _ in range(4)) for _ in range(4)))


def spin_connection(tetrad: Tetrad) -> SpinConnection:
    if _is_minkowski_tetrad(tetrad):
        return minkowski_spin_connection(tetrad)
    if _is_flrw_tetrad(tetrad):
        return flrw_spin_connection(tetrad)
    raise NotExact("the spin connection is admitted here for the Minkowski and flat FLRW tetrads")


def _is_minkowski_tetrad(tetrad: Tetrad) -> bool:
    return metric_eq(tetrad_metric(tetrad), named_metric("minkowski4")) and all(
        form_eq(tetrad.coframes[i], coframe(tetrad.names, i)) for i in range(4)
    )


def _is_flrw_tetrad(tetrad: Tetrad) -> bool:
    try:
        return metric_eq(tetrad_metric(tetrad), named_metric("flrw"))
    except Exception:
        return False


def torsion(tetrad: Tetrad, omega: SpinConnection | None = None) -> tuple[Form, Form, Form, Form]:
    if omega is None:
        omega = spin_connection(tetrad)
    out = []
    for a in range(4):
        total = exterior(tetrad.coframes[a])
        for b in range(4):
            total = form_add(total, wedge(omega.components[a][b], tetrad.coframes[b]))
        out.append(total)
    return tuple(out)  # type: ignore[return-value]


def torsion_is_zero(tetrad: Tetrad, omega: SpinConnection | None = None) -> bool:
    return all(form_is_zero(form) for form in torsion(tetrad, omega))


# ---- Dirac operator -------------------------------------------------------

@dataclass(frozen=True)
class CFExpr:
    """A complex elementary expression, with exact real and imaginary parts."""

    re: FExpr
    im: FExpr


def _cf_zero(names: tuple[str, ...] = ()) -> CFExpr:
    z = const_fexpr(_ZERO, names)
    return CFExpr(z, z)


def _cf_from_cnum(value: CNum, names: tuple[str, ...] = ()) -> CFExpr:
    rat = c_as_ratio(value)
    if rat is not None:
        return CFExpr(const_fexpr(rat, names), const_fexpr(_ZERO, names))
    # a + i b with a, b rational (no further radicands required here)
    from pgi.math.cnum import c_is_real, c_conj, c_add as add, c_mul as mul, c_from_parts

    # Re and Im via (z + conj)/2 and (z - conj)/(2i)
    # Our Dirac matrices only use rationals and i, so parts are ratios.
    # Fall back: if value is p + i q with p,q in Q.
    # CNum layout: re0, im0 are the rational real and imag when d=0,e=0.
    if value.d == 0 and value.e == 0:
        return CFExpr(const_fexpr(value.re0, names), const_fexpr(value.im0, names))
    raise NotExact("this Dirac coefficient is not in Q(i)")


def _cf_from_fexpr(value: FExpr) -> CFExpr:
    return CFExpr(value, const_fexpr(_ZERO, _plains_of(value)))


def _cf_add(left: CFExpr, right: CFExpr) -> CFExpr:
    return CFExpr(fexpr_add(left.re, right.re), fexpr_add(left.im, right.im))


def _cf_neg(value: CFExpr) -> CFExpr:
    return CFExpr(fexpr_neg(value.re), fexpr_neg(value.im))


def _cf_mul_f(value: CFExpr, scale: FExpr) -> CFExpr:
    return CFExpr(fexpr_mul(value.re, scale), fexpr_mul(value.im, scale))


def _cf_mul_c(value: CFExpr, scale: CNum) -> CFExpr:
    # (re + i im) * (a + i b) = (re a - im b) + i (re b + im a)
    if scale.d != 0 or scale.e != 0:
        raise NotExact("this Dirac coefficient is not in Q(i)")
    a, b = scale.re0, scale.im0
    names = ()
    ar = const_fexpr(a, names)
    br = const_fexpr(b, names)
    re = fexpr_add(fexpr_mul(value.re, ar), fexpr_neg(fexpr_mul(value.im, br)))
    im = fexpr_add(fexpr_mul(value.re, br), fexpr_mul(value.im, ar))
    return CFExpr(re, im)


def _cf_eq(left: CFExpr, right: CFExpr) -> bool:
    return fexpr_eq(left.re, right.re) and fexpr_eq(left.im, right.im)


def _cf_is_zero(value: CFExpr) -> bool:
    return fexpr_eq(value.re, const_fexpr(_ZERO, ())) and fexpr_eq(value.im, const_fexpr(_ZERO, ()))


def _show_cf(value: CFExpr) -> str:
    re_z = fexpr_eq(value.re, const_fexpr(_ZERO, ()))
    im_z = fexpr_eq(value.im, const_fexpr(_ZERO, ()))
    if re_z and im_z:
        return "0"
    if im_z:
        return show_fexpr(value.re)
    if re_z:
        im = show_fexpr(value.im)
        if im == "1":
            return "i"
        if im == "-1":
            return "-i"
        return f"i * {im}"
    return f"{show_fexpr(value.re)} + i * {show_fexpr(value.im)}"


@dataclass(frozen=True)
class Spinor:
    names: tuple[str, ...]
    components: tuple[CFExpr, CFExpr, CFExpr, CFExpr]


def _show_spinor(value: Spinor) -> str:
    return "[" + ", ".join(_show_cf(c) for c in value.components) + "]"


def _gamma_lower(index: int) -> CMatrix:
    # γ_a = η_ab γ^b, so γ_0 = -γ^0 and γ_i = γ^i.
    mat = gamma(index)
    if index == 0:
        from pgi.math.hilbert import cmatrix_neg

        return cmatrix_neg(mat)
    return mat


def _gamma_upper(index: int) -> CMatrix:
    return gamma(index)


def _mat_mul_spinor(mat: CMatrix, spinor: Spinor) -> Spinor:
    from pgi.math.hilbert import cmatrix_neg  # noqa: F401

    out = []
    for i in range(4):
        total = _cf_zero(spinor.names)
        for j in range(4):
            entry = mat.rows[i][j]
            if c_is_zero(entry):
                continue
            total = _cf_add(total, _cf_mul_c(spinor.components[j], entry))
        out.append(total)
    return Spinor(spinor.names, tuple(out))  # type: ignore[arg-type]


def _spinor_add(left: Spinor, right: Spinor) -> Spinor:
    return Spinor(left.names, tuple(_cf_add(a, b) for a, b in zip(left.components, right.components)))  # type: ignore[arg-type]


def _spinor_scale_f(spinor: Spinor, scale: FExpr) -> Spinor:
    return Spinor(spinor.names, tuple(_cf_mul_f(c, scale) for c in spinor.components))  # type: ignore[arg-type]


def _spinor_eq(left: Spinor, right: Spinor) -> bool:
    return all(_cf_eq(a, b) for a, b in zip(left.components, right.components))


def _spinor_is_zero(value: Spinor) -> bool:
    return all(_cf_is_zero(c) for c in value.components)


def _omega_upper(omega: SpinConnection, a: int, b: int) -> Form:
    # ω^{ab} = ω^a_c η^{cb}; η diagonal, so ω^{a0} = -ω^a_0, ω^{ai} = ω^a_i.
    form = omega.components[a][b]
    if b == 0:
        return form_neg(form) if not form_is_zero(form) else form
    return form


def _spinor_diff(spinor: Spinor, name: str) -> Spinor:
    from pgi.math.trans import fexpr_diff

    def d_cf(value: CFExpr) -> CFExpr:
        return CFExpr(fexpr_diff(value.re, name), fexpr_diff(value.im, name))

    return Spinor(spinor.names, tuple(d_cf(c) for c in spinor.components))  # type: ignore[arg-type]


def dirac_operator(tetrad: Tetrad, spinor: Spinor) -> Spinor:
    omega = spin_connection(tetrad)
    inv = inverse_tetrad(tetrad)
    names = tetrad.names
    # Precompute (1/4) ω_μ^{bc} γ_b γ_c as a CMatrix-valued 1-form, applied to ψ.
    # For each coordinate μ, the connection term is a constant (or FExpr-scaled) matrix.
    total = Spinor(names, tuple(_cf_zero(names) for _ in range(4)))  # type: ignore[arg-type]
    quarter = const_fexpr(_HALF, names)  # will multiply by 1/2 more? Use 1/4.
    quarter = const_fexpr(Ratio(1, 4), names)
    for a in range(4):
        ga = _gamma_upper(a)
        for mu, mu_name in enumerate(names):
            ea_mu = _as_fexpr(inv[a][mu], names)
            if fexpr_eq(ea_mu, const_fexpr(_ZERO, names)):
                continue
            # partial_μ ψ
            dpsi = _spinor_diff(spinor, mu_name)
            # (1/4) ω_μ^{bc} γ_b γ_c ψ
            conn = Spinor(names, tuple(_cf_zero(names) for _ in range(4)))  # type: ignore[arg-type]
            for b in range(4):
                for c in range(4):
                    w_form = _omega_upper(omega, b, c)
                    w_mu = _as_fexpr(_coeff_of(w_form, mu_name) if not form_is_zero(w_form) else _f_zero(names), names)
                    if fexpr_eq(w_mu, const_fexpr(_ZERO, names)):
                        continue
                    # γ_b γ_c ψ, then * ω_μ^{bc}
                    gb_gc_psi = _mat_mul_spinor(_gamma_lower(c), spinor)
                    gb_gc_psi = _mat_mul_spinor(_gamma_lower(b), gb_gc_psi)
                    conn = _spinor_add(conn, _spinor_scale_f(gb_gc_psi, w_mu))
            conn = _spinor_scale_f(conn, quarter)
            piece = _spinor_add(dpsi, conn)
            piece = _spinor_scale_f(piece, ea_mu)
            piece = _mat_mul_spinor(ga, piece)
            total = _spinor_add(total, piece)
    return total


def constant_spinor(components: tuple, names: tuple[str, ...]) -> Spinor:
    out = []
    for value in components:
        if isinstance(value, CFExpr):
            out.append(value)
        elif isinstance(value, FExpr):
            out.append(_cf_from_fexpr(value))
        elif isinstance(value, CNum):
            out.append(_cf_from_cnum(value, names))
        elif isinstance(value, Ratio):
            out.append(CFExpr(const_fexpr(value, names), const_fexpr(_ZERO, names)))
        elif isinstance(value, int):
            out.append(CFExpr(const_fexpr(Ratio(value, 1), names), const_fexpr(_ZERO, names)))
        else:
            out.append(_cf_from_fexpr(_as_fexpr(value, names)))
    if len(out) != 4:
        raise NotExact("a Dirac spinor has four components")
    return Spinor(names, tuple(out))  # type: ignore[arg-type]


def _check_standing() -> None:
    from pgi.math.syntax import parse_term
    from pgi.math.trans import eval_trans

    m4 = named_tetrad("minkowski4")
    if not metric_eq(tetrad_metric(m4), named_metric("minkowski4")):
        raise KernelError("the Minkowski tetrad did not rebuild the Minkowski metric")
    if not torsion_is_zero(m4):
        raise KernelError("the Minkowski spin connection is not torsion-free")
    psi = constant_spinor((1, 0, 0, 0), m4.names)
    if not _spinor_is_zero(dirac_operator(m4, psi)):
        raise KernelError("the flat Dirac operator did not annihilate a constant spinor")

    flrw = named_tetrad("flrw")
    if not metric_eq(tetrad_metric(flrw), named_metric("flrw")):
        raise KernelError("the FLRW tetrad did not rebuild the FLRW metric")
    if not torsion_is_zero(flrw):
        raise KernelError("the FLRW spin connection is not torsion-free")
    inverse_tetrad(flrw)  # multiplies back
    psi = constant_spinor((1, 0, 0, 0), flrw.names)
    left = dirac_operator(flrw, psi)
    # (3/2) (ȧ/a) γ^0 ψ
    scale = formal_expr("a", var_fexpr("t", flrw.names), 0, flrw.names)
    adot = formal_expr("a", var_fexpr("t", flrw.names), 1, flrw.names)
    factor = fexpr_mul(const_fexpr(_THREE_HALVES, flrw.names), fexpr_div(adot, scale))
    right = _spinor_scale_f(_mat_mul_spinor(_gamma_upper(0), psi), factor)
    if not _spinor_eq(left, right):
        raise KernelError("the FLRW Dirac operator on a constant spinor was not (3/2) (da/dt)/a γ^0 ψ")


_STANDING = False


def _standing() -> None:
    global _STANDING
    if _STANDING:
        return
    _check_standing()
    _STANDING = True


TETRAD_OPS = frozenset({"tetrad", "spinconnection", "torsion", "tetradmetric", "dirac", "spinor"})


def _contains_op(term: Term, names: frozenset[str]) -> bool:
    if isinstance(term, App):
        if term.op in names:
            return True
        return any(_contains_op(arg, names) for arg in term.args)
    return False


def has_tetrad(term: Term) -> bool:
    return _contains_op(term, TETRAD_OPS)


def _eval_tetrad(term: Term) -> Tetrad:
    if isinstance(term, App) and term.op == "tetrad" and len(term.args) == 1:
        arg = term.args[0]
        if isinstance(arg, Var):
            return named_tetrad(arg.name)
        if isinstance(arg, App) and arg.op == "metric" and len(arg.args) == 1 and isinstance(arg.args[0], Var):
            return named_tetrad(arg.args[0].name)
    raise NotExact("a tetrad is tetrad(minkowski4) or tetrad(flrw)")


def _eval_spinor(term: Term, names: tuple[str, ...]) -> Spinor:
    if not isinstance(term, App) or term.op != "spinor" or len(term.args) != 4:
        raise NotExact("spinor takes four components")
    comps = []
    for arg in term.args:
        if isinstance(arg, IntLit):
            comps.append(Ratio(arg.n, 1))
        else:
            from pgi.math.trans import has_trans
            from pgi.math.poly import eval_symbolic, has_symbolic

            if has_trans(arg) or (isinstance(arg, Var) and arg.name == "pi"):
                comps.append(eval_trans(arg))
            else:
                comps.append(eval_symbolic(arg))
    return constant_spinor(tuple(comps), names)


def _eval_connection(term: Term) -> SpinConnection:
    if isinstance(term, App) and term.op == "spinconnection" and len(term.args) == 1:
        return spin_connection(_eval_tetrad(term.args[0]))
    raise NotExact("spinconnection takes a tetrad")


def _show_connection(omega: SpinConnection) -> str:
    if all(form_is_zero(form) for row in omega.components for form in row):
        return "0"
    rows = []
    for row in omega.components:
        rows.append("[" + ", ".join(show_form(form) if not form_is_zero(form) else "0" for form in row) + "]")
    return "[" + ", ".join(rows) + "]"


def _show_torsion(forms: tuple[Form, ...]) -> str:
    if all(form_is_zero(form) for form in forms):
        return "0"
    return "[" + ", ".join(show_form(form) for form in forms) + "]"


def _eval_tetrad_value(term: Term):
    _standing()
    if isinstance(term, App):
        if term.op == "tetradmetric" and len(term.args) == 1:
            return tetrad_metric(_eval_tetrad(term.args[0]))
        if term.op == "spinconnection" and len(term.args) == 1:
            return spin_connection(_eval_tetrad(term.args[0]))
        if term.op == "torsion" and len(term.args) in {1, 2}:
            tetrad = _eval_tetrad(term.args[0])
            omega = _eval_connection(term.args[1]) if len(term.args) == 2 else None
            return torsion(tetrad, omega)
        if term.op == "dirac" and len(term.args) == 2:
            tetrad = _eval_tetrad(term.args[0])
            return dirac_operator(tetrad, _eval_spinor(term.args[1], tetrad.names))
        if term.op == "tetrad":
            return _eval_tetrad(term)
        if term.op in {"add", "sub"} and len(term.args) == 2:
            # residual of two spinors or two metrics is handled in equality
            raise NotExact("this term is not a single tetrad, connection, torsion, or Dirac value")
    raise NotExact("this term is not a tetrad, spin connection, torsion, or Dirac operator")


@dataclass(frozen=True)
class TetradTheorem:
    value: object
    origin: Term
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if has_tetrad(self.origin):
            expected = _eval_tetrad_value(self.origin)
            if not _tetrad_value_eq(self.value, expected):
                raise KernelError("this tetrad result does not match the exact evaluation")


def _tetrad_value_eq(left: object, right: object) -> bool:
    if isinstance(left, Metric) and isinstance(right, Metric):
        return metric_eq(left, right)
    if isinstance(left, SpinConnection) and isinstance(right, SpinConnection):
        return all(form_eq(a, b) for ra, rb in zip(left.components, right.components) for a, b in zip(ra, rb))
    if isinstance(left, tuple) and isinstance(right, tuple) and left and isinstance(left[0], Form):
        return len(left) == len(right) and all(form_eq(a, b) for a, b in zip(left, right))
    if isinstance(left, Spinor) and isinstance(right, Spinor):
        return _spinor_eq(left, right)
    if isinstance(left, Tetrad) and isinstance(right, Tetrad):
        return left.names == right.names and all(form_eq(a, b) for a, b in zip(left.coframes, right.coframes))
    return False


def _is_zero_value(value: object) -> bool:
    if isinstance(value, SpinConnection):
        return all(form_is_zero(form) for row in value.components for form in row)
    if isinstance(value, tuple) and value and isinstance(value[0], Form):
        return all(form_is_zero(form) for form in value)
    if isinstance(value, Spinor):
        return _spinor_is_zero(value)
    if isinstance(value, RatTheorem):
        return value.value.num == 0
    if isinstance(value, Ratio):
        return value.num == 0
    if isinstance(value, IntLit):
        return value.n == 0
    return False


def _show_value(value: object) -> str:
    if isinstance(value, Metric):
        from pgi.math.metric import show_metric

        return show_metric(value)
    if isinstance(value, SpinConnection):
        return _show_connection(value)
    if isinstance(value, tuple) and value and isinstance(value[0], Form):
        return _show_torsion(value)
    if isinstance(value, Spinor):
        return _show_spinor(value)
    if isinstance(value, Tetrad):
        return "[" + ", ".join(show_form(frame) for frame in value.coframes) + "]"
    return str(value)


def eval_tetrad_result(term: Term):
    _standing()
    return TetradTheorem(_eval_tetrad_value(term), term, _detail())


def _detail() -> tuple[str, ...]:
    return (
        "A tetrad rebuilds the metric by g_μν = η_ab e^a_μ e^b_ν.",
        "The spin connection is the torsion-free solution of de^a + ω^a_b ∧ e^b = 0.",
        "An inverse tetrad is kept only when both products are the identity.",
        "The Dirac operator is γ^a e_a^μ (∂_μ + (1/4) ω_μ^{bc} γ_b γ_c), checked identically.",
    )


def tetrad_value_rule(origin: Term, result: object, prelude: tuple[str, ...] = ()) -> Rule:
    if not isinstance(result, TetradTheorem):
        raise KernelError("this tetrad result has no claim")
    shown = _show_value(result.value)
    return Rule(
        id=f"math.tetrad.{shown}",
        layer="base",
        stage="quantity",
        title=f"{pretty(origin)} = {shown}",
        produces=shown,
        detail_lines=(*prelude, *result.detail),
    )


def tetrad_equality_rules(left: Term, right: Term, left_value: object, right_value: object, prelude: tuple[str, ...] = ()):
    title = f"{pretty(left)} = {pretty(right)}"
    if _sides_eq(left_value, right_value):
        return (
            Rule(
                id="math.tetrad.eq",
                layer="base",
                stage="quantity",
                title=title,
                produces=f"identity({title})",
                detail_lines=(*prelude, "The two sides are the same exact tetrad, connection, torsion, metric, or Dirac spinor."),
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


def _as_value(value: object) -> object:
    if isinstance(value, TetradTheorem):
        return value.value
    return value


def _sides_eq(left: object, right: object) -> bool:
    a, b = _as_value(left), _as_value(right)
    if _tetrad_value_eq(a, b):
        return True
    if _is_zero_value(a) and _is_zero_side(right):
        return True
    if _is_zero_value(b) and _is_zero_side(left):
        return True
    # dirac(...) = (3/2)*... evaluated as a spinor on the right, if provided
    if isinstance(a, Spinor) and isinstance(b, Spinor):
        return _spinor_eq(a, b)
    if isinstance(a, Metric) and isinstance(b, Metric):
        return metric_eq(a, b)
    return False


def _is_zero_side(value: object) -> bool:
    if isinstance(value, IntLit):
        return value.n == 0
    if isinstance(value, Ratio):
        return value.num == 0
    raw = _as_value(value)
    return _is_zero_value(raw)


def side_as_tetrad(term: Term) -> object:
    if has_tetrad(term):
        return eval_tetrad_result(term)
    if isinstance(term, IntLit):
        return term
    # metric(flrw) / metric(minkowski4) on the other side of tetradmetric equality
    if isinstance(term, App) and term.op == "metric":
        from pgi.math.metric import eval_metric

        return eval_metric(term)
    if isinstance(term, Var) and term.name in {"minkowski4", "m4", "flrw", "friedmann", "minkowski"}:
        return named_metric(term.name if term.name != "minkowski" else "minkowski4")
    raise NotExact("this term is not a tetrad, spin connection, torsion, Dirac operator, or metric")
