"""Lie algebras su(2) and su(3), and exact U(1) and SU(2) gauge checks.

The su(2) generators are T_a = σ_a / 2. They satisfy [T_a, T_b] = i ε_abc T_c,
the Jacobi identity, and the Killing form K(T_a, T_b) = 2 δ_ab, which agrees
with both the structure-constant formula and 2n tr(T_a T_b). The su(3)
generators are T_a = λ_a / 2 for the Gell-Mann matrices. Their structure
constants, Jacobi identity, and Killing form K(T_a, T_b) = 3 δ_ab are
checked the same way, including the factors √3 / 2.

A U(1) field strength is F = ∂_x A_y − ∂_y A_x, with exact rational
partials. It is invariant under A ↦ A + dλ. An SU(2) field strength of
two connection components is F = ∂A + [A_x, A_y], with vanishing
partials when the components are constant. A constant SU(2) gauge
transformation acts by A ↦ U A U†, and F transforms covariantly:
F ↦ U F U†. The trace of F² is invariant. A position-dependent SU(2)
gauge transformation by the rational rotation already checked acts by
A_μ ↦ U A_μ U† + U ∂_μ U†, and the field strength
F_μν = ∂_μ A_ν − ∂_ν A_μ + [A_μ, A_ν] transforms as F ↦ U F U†,
checked identically as matrix-valued rational functions. A pure-gauge
connection built from that rotation has vanishing field strength,
checked identically.

These are the named constructions of su(2), su(3), and the fundamental
gauge transformation laws. The certificates are the identities above,
checked exactly, with no approximation.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from pgi.math.cnum import (
    CNum,
    c_add,
    c_as_ratio,
    c_eq,
    c_from_int,
    c_from_ratio,
    c_i,
    c_is_zero,
    c_mul,
    c_one,
    c_sqrt_ratio,
    c_zero,
    show_cnum,
)
from pgi.math.hilbert import (
    CMatrix,
    HilbTheorem,
    ScalarTheorem,
    cmatrix_add,
    cmatrix_dagger,
    cmatrix_eq,
    cmatrix_mul,
    cmatrix_smul,
    cmatrix_sub,
    cmatrix_trace,
    cmatrix_zero,
    commutator,
    eval_hilbert_matrix,
    eval_hilbert_result,
    eval_hilbert_scalar,
    has_hilbert,
    has_matrix_shape,
    hilbert_equality_rules,
    hilbert_value_rule,
    is_unitary,
    pauli,
    show_cmatrix,
    side_as_hilbert,
)
from pgi.math.kernel import KernelError, NotExact
from pgi.math.poly import (
    MRat,
    as_rat,
    const_poly,
    eval_symbolic,
    mrat_add,
    mrat_diff,
    mrat_eq,
    mrat_mul,
    mrat_neg,
    mrat_sub,
    show_rat,
    var_poly,
    zero_poly,
)
from pgi.math.rational import Ratio, RatTheorem, rat_normalize
from pgi.math.syntax import App, IntLit, Term, Var, pretty
from pgi.model import Rule


_ZERO = Ratio(0, 1)
_ONE = Ratio(1, 1)
_HALF = Ratio(1, 2)
_NEG_HALF = Ratio(-1, 2)


def _idx(name: str, algebra: str) -> int:
    if algebra == "su2":
        mapping = {"x": 1, "y": 2, "z": 3, "1": 1, "2": 2, "3": 3}
        if name not in mapping:
            raise NotExact("this su(2) generator is not in the basis")
        return mapping[name]
    if algebra == "su3":
        if name not in {str(i) for i in range(1, 9)}:
            raise NotExact("this su(3) generator is not in the basis")
        return int(name)
    raise NotExact("this Lie algebra is not su(2) or su(3)")


def _name(term: Term) -> str:
    if isinstance(term, Var):
        return term.name
    if isinstance(term, IntLit):
        return str(term.n)
    raise NotExact("this name is not a label")


@lru_cache(maxsize=8)
def su2_gen(name: str) -> CMatrix:
    value = cmatrix_smul(c_from_ratio(_HALF), pauli(name if name in {"x", "y", "z"} else { "1": "x", "2": "y", "3": "z"}[name]))
    return value


@lru_cache(maxsize=16)
def gellmann(idx: int) -> CMatrix:
    from pgi.math.cnum import c_neg

    z, o, i = c_zero(), c_one(), c_i()
    ni = c_neg(i)
    zero_row = (z, z, z)
    if idx == 1:
        rows = ((z, o, z), (o, z, z), zero_row)
    elif idx == 2:
        rows = ((z, ni, z), (i, z, z), zero_row)
    elif idx == 3:
        rows = ((o, z, z), (z, c_from_int(-1), z), zero_row)
    elif idx == 4:
        rows = ((z, z, o), zero_row, (o, z, z))
    elif idx == 5:
        rows = ((z, z, ni), zero_row, (i, z, z))
    elif idx == 6:
        rows = (zero_row, (z, z, o), (z, o, z))
    elif idx == 7:
        rows = (zero_row, (z, z, ni), (z, i, z))
    elif idx == 8:
        scale = c_inv_of_sqrt(3)
        rows = (
            (scale, z, z),
            (z, scale, z),
            (z, z, c_mul(c_from_int(-2), scale)),
        )
    else:
        raise NotExact("this Gell-Mann matrix is not in the basis")
    value = CMatrix(rows)
    if not _is_hermitian_trace_zero(value):
        raise KernelError("a Gell-Mann matrix was not Hermitian and traceless")
    return value


def c_inv_of_sqrt(n: int) -> CNum:
    return c_sqrt_ratio(Ratio(1, n))


def _is_hermitian_trace_zero(value: CMatrix) -> bool:
    from pgi.math.hilbert import is_hermitian

    return is_hermitian(value) and c_is_zero(cmatrix_trace(value))


@lru_cache(maxsize=16)
def su3_gen(name: str) -> CMatrix:
    idx = _idx(name, "su3")
    return cmatrix_smul(c_from_ratio(_HALF), gellmann(idx))


def _epsilon(a: int, b: int, c: int) -> int:
    if a == b or b == c or a == c:
        return 0
    even = (a, b, c) in {(1, 2, 3), (2, 3, 1), (3, 1, 2)}
    odd = (a, b, c) in {(3, 2, 1), (2, 1, 3), (1, 3, 2)}
    if even:
        return 1
    if odd:
        return -1
    return 0


# Independent nonzero su(3) structure constants f_abc, a < b < c after antisym.
# Standard values, written on the unordered triples, then extended by sign.
_SU3_F = {
    (1, 2, 3): Ratio(1, 1),
    (1, 4, 7): Ratio(1, 2),
    (1, 5, 6): Ratio(-1, 2),
    (2, 4, 6): Ratio(1, 2),
    (2, 5, 7): Ratio(1, 2),
    (3, 4, 5): Ratio(1, 2),
    (3, 6, 7): Ratio(-1, 2),
    # √3 / 2 triples are marked separately
}


_SU3_F_SQRT3 = {
    (4, 5, 8): True,
    (6, 7, 8): True,
}


def _perm_sign(a: int, b: int, c: int) -> tuple[int, tuple[int, int, int]]:
    triple = (a, b, c)
    if len(set(triple)) < 3:
        return 0, triple
    ordered = tuple(sorted(triple))
    sign = 1
    seq = list(triple)
    for i in range(3):
        for j in range(i + 1, 3):
            if seq[i] > seq[j]:
                sign *= -1
    return sign, ordered


def structure(algebra: str, a: int, b: int, c: int) -> CNum:
    if algebra == "su2":
        return c_from_int(_epsilon(a, b, c))
    if algebra == "su3":
        if len({a, b, c}) < 3:
            return c_zero()
        sign, ordered = _perm_sign(a, b, c)
        if sign == 0:
            return c_zero()
        if ordered in _SU3_F:
            value = c_from_ratio(_SU3_F[ordered])
            return value if sign == 1 else c_mul(c_from_int(-1), value)
        if ordered in _SU3_F_SQRT3:
            value = c_mul(c_from_ratio(Ratio(1, 2)), c_sqrt_ratio(Ratio(3, 1)))
            return value if sign == 1 else c_mul(c_from_int(-1), value)
        return c_zero()
    raise NotExact("this Lie algebra is not su(2) or su(3)")


def killing(algebra: str, a: int, b: int) -> CNum:
    dim = 3 if algebra == "su2" else 8
    total = c_zero()
    for c in range(1, dim + 1):
        for d in range(1, dim + 1):
            total = c_add(total, c_mul(structure(algebra, a, c, d), structure(algebra, b, c, d)))
    return total


def generators(algebra: str) -> dict[int, CMatrix]:
    if algebra == "su2":
        return {1: su2_gen("x"), 2: su2_gen("y"), 3: su2_gen("z")}
    if algebra == "su3":
        return {i: su3_gen(str(i)) for i in range(1, 9)}
    raise NotExact("this Lie algebra is not su(2) or su(3)")


def _algebra_checks(algebra: str) -> None:
    gens = generators(algebra)
    dim = len(gens)
    expected_kill = c_from_int(2 if algebra == "su2" else 3)
    n = 2 if algebra == "su2" else 3
    table = {
        (a, b, c): structure(algebra, a, b, c)
        for a in range(1, dim + 1)
        for b in range(1, dim + 1)
        for c in range(1, dim + 1)
    }
    nonzero: dict[tuple[int, int], list[tuple[int, CNum]]] = {}
    for (a, b, c), value in table.items():
        if not c_is_zero(value):
            nonzero.setdefault((a, b), []).append((c, value))
    for a in range(1, dim + 1):
        for b in range(1, dim + 1):
            got = commutator(gens[a], gens[b])
            want = cmatrix_zero(n, n)
            for c, coeff in nonzero.get((a, b), ()):
                want = cmatrix_add(want, cmatrix_smul(c_mul(c_i(), coeff), gens[c]))
            if not cmatrix_eq(got, want):
                raise KernelError(f"the {algebra} commutation relations did not hold")
            kill = c_zero()
            for c in range(1, dim + 1):
                for d, f_acd in nonzero.get((a, c), ()):
                    kill = c_add(kill, c_mul(f_acd, table[b, c, d]))
            traces = c_mul(c_from_int(2 * n), cmatrix_trace(cmatrix_mul(gens[a], gens[b])))
            if not c_eq(kill, traces):
                raise KernelError(f"the {algebra} Killing form did not match 2n tr(T_a T_b)")
            target = expected_kill if a == b else c_zero()
            if not c_eq(kill, target):
                raise KernelError(f"the {algebra} Killing form was not the expected multiple of the identity")
    def _clear() -> dict[int, CNum]:
        return {e: c_zero() for e in range(1, dim + 1)}
    for a in range(1, dim + 1):
        for b in range(1, dim + 1):
            for c in range(1, dim + 1):
                acc = _clear()
                for d, f_bcd in nonzero.get((b, c), ()):
                    for e, f_ade in nonzero.get((a, d), ()):
                        acc[e] = c_add(acc[e], c_mul(f_ade, f_bcd))
                for d, f_cad in nonzero.get((c, a), ()):
                    for e, f_bde in nonzero.get((b, d), ()):
                        acc[e] = c_add(acc[e], c_mul(f_bde, f_cad))
                for d, f_abd in nonzero.get((a, b), ()):
                    for e, f_cde in nonzero.get((c, d), ()):
                        acc[e] = c_add(acc[e], c_mul(f_cde, f_abd))
                if any(not c_is_zero(value) for value in acc.values()):
                    raise KernelError(f"the {algebra} Jacobi identity did not hold")
    zero = cmatrix_zero(n, n)
    sample = ((1, 2, 3), (1, 4, 8), (4, 5, 8), (6, 7, 8)) if algebra == "su3" else ((1, 2, 3),)
    for a, b, c in sample:
        one = commutator(gens[a], commutator(gens[b], gens[c]))
        two = commutator(gens[b], commutator(gens[c], gens[a]))
        three = commutator(gens[c], commutator(gens[a], gens[b]))
        if not cmatrix_eq(cmatrix_add(one, cmatrix_add(two, three)), zero):
            raise KernelError(f"the {algebra} Jacobi identity did not hold")


_STANDING = False


def _standing() -> None:
    global _STANDING
    if _STANDING:
        return
    # Fix 1/√3 in gellmann(8): verify λ8^2 trace and so on via algebra checks.
    _algebra_checks("su2")
    _algebra_checks("su3")
    _pure_gauge_check()
    _nonconst_covariance_check()
    _STANDING = True


# --- rational 2x2 matrices for a pure-gauge SU(2) connection ---


def _rat_const(value: int | Ratio, names: tuple[str, ...]) -> MRat:
    ratio = value if isinstance(value, Ratio) else Ratio(value, 1)
    return as_rat(const_poly(ratio, names))


def _rat_var(name: str, names: tuple[str, ...]) -> MRat:
    return as_rat(var_poly(name, names))


def _rm_add(left: tuple[tuple[MRat, ...], ...], right: tuple[tuple[MRat, ...], ...]):
    return tuple(
        tuple(mrat_add(a, b) for a, b in zip(lrow, rrow))
        for lrow, rrow in zip(left, right)
    )


def _rm_sub(left, right):
    return tuple(
        tuple(mrat_sub(a, b) for a, b in zip(lrow, rrow))
        for lrow, rrow in zip(left, right)
    )


def _rm_mul(left, right):
    n = len(left)
    rows = []
    for i in range(n):
        row = []
        for j in range(n):
            total = _rat_const(0, left[0][0].num.names)
            for k in range(n):
                total = mrat_add(total, mrat_mul(left[i][k], right[k][j]))
            row.append(total)
        rows.append(tuple(row))
    return tuple(rows)


def _rm_transpose(value):
    n = len(value)
    return tuple(tuple(value[i][j] for i in range(n)) for j in range(n))


def _rm_diff(value, name: str):
    return tuple(tuple(mrat_diff(entry, name) for entry in row) for row in value)


def _rm_eq0(value) -> bool:
    return all(mrat_eq(entry, _rat_const(0, entry.num.names)) for row in value for entry in row)


def _rm_eq(left, right) -> bool:
    return all(mrat_eq(a, b) for lrow, rrow in zip(left, right) for a, b in zip(lrow, rrow))


def _su2rot_matrix() -> tuple[tuple[MRat, ...], ...]:
    names = ("x", "y")
    r = mrat_add(_rat_var("x", names), _rat_var("y", names))
    one = _rat_const(1, names)
    num_c = mrat_sub(one, mrat_mul(r, r))
    den = mrat_add(one, mrat_mul(r, r))
    # c = (1-r^2)/(1+r^2), s = 2r/(1+r^2)
    from pgi.math.poly import mrat_div

    c = mrat_div(num_c, den)
    s = mrat_div(mrat_mul(_rat_const(2, names), r), den)
    if not mrat_eq(mrat_add(mrat_mul(c, c), mrat_mul(s, s)), one):
        raise KernelError("the rational SU(2) rotation was not special unitary")
    u = ((c, mrat_neg(s)), (s, c))
    ident = ((one, _rat_const(0, names)), (_rat_const(0, names), one))
    if not _rm_eq(_rm_mul(_rm_transpose(u), u), ident) or not _rm_eq(_rm_mul(u, _rm_transpose(u)), ident):
        raise KernelError("the rational SU(2) rotation was not unitary")
    return u


def _pure_gauge_connection():
    u = _su2rot_matrix()
    ax = _rm_mul(u, _rm_diff(_rm_transpose(u), "x"))
    ay = _rm_mul(u, _rm_diff(_rm_transpose(u), "y"))
    return ax, ay


def _pure_gauge_field(ax, ay):
    dax_y = _rm_diff(ax, "y")
    day_x = _rm_diff(ay, "x")
    comm = _rm_sub(_rm_mul(ax, ay), _rm_mul(ay, ax))
    return _rm_add(_rm_sub(day_x, dax_y), comm)


def _pure_gauge_check() -> None:
    ax, ay = _pure_gauge_connection()
    field = _pure_gauge_field(ax, ay)
    if not _rm_eq0(field):
        raise KernelError("a pure-gauge SU(2) connection had a nonzero field strength")



# --- position-dependent SU(2) matrices with entries in Q(i)(x, y) ---


@dataclass(frozen=True)
class CFun:
    """A position-dependent scalar a + b i, with exact rational functions a, b."""

    re: MRat
    im: MRat


def _cf_zero(names: tuple[str, ...]) -> CFun:
    return CFun(_rat_const(0, names), _rat_const(0, names))


def _cf_from_mrat(value: MRat) -> CFun:
    return CFun(value, _rat_const(0, value.num.names))


def _cf_from_cnum(value: CNum, names: tuple[str, ...]) -> CFun:
    if value.d != 0:
        raise NotExact("a position-dependent SU(2) entry is admitted here only in Q(i)")
    return CFun(_rat_const(value.re0, names), _rat_const(value.im0, names))


def _cf_add(left: CFun, right: CFun) -> CFun:
    return CFun(mrat_add(left.re, right.re), mrat_add(left.im, right.im))


def _cf_sub(left: CFun, right: CFun) -> CFun:
    return CFun(mrat_sub(left.re, right.re), mrat_sub(left.im, right.im))


def _cf_mul(left: CFun, right: CFun) -> CFun:
    return CFun(
        mrat_sub(mrat_mul(left.re, right.re), mrat_mul(left.im, right.im)),
        mrat_add(mrat_mul(left.re, right.im), mrat_mul(left.im, right.re)),
    )


def _cf_neg(value: CFun) -> CFun:
    return CFun(mrat_neg(value.re), mrat_neg(value.im))


def _cf_conj(value: CFun) -> CFun:
    return CFun(value.re, mrat_neg(value.im))


def _cf_diff(value: CFun, name: str) -> CFun:
    return CFun(mrat_diff(value.re, name), mrat_diff(value.im, name))


def _cf_eq(left: CFun, right: CFun) -> bool:
    return mrat_eq(left.re, right.re) and mrat_eq(left.im, right.im)


def _cf_is_zero(value: CFun) -> bool:
    return mrat_eq(value.re, _rat_const(0, value.re.num.names)) and mrat_eq(value.im, _rat_const(0, value.im.num.names))


def _cm_from_rm(value) -> tuple:
    return tuple(tuple(_cf_from_mrat(entry) for entry in row) for row in value)


def _cm_from_cmatrix(value: CMatrix, names: tuple[str, ...]) -> tuple:
    return tuple(
        tuple(_cf_from_cnum(value.rows[i][j], names) for j in range(value.ncols))
        for i in range(value.nrows)
    )


def _cm_add(left, right):
    return tuple(tuple(_cf_add(a, b) for a, b in zip(lrow, rrow)) for lrow, rrow in zip(left, right))


def _cm_sub(left, right):
    return tuple(tuple(_cf_sub(a, b) for a, b in zip(lrow, rrow)) for lrow, rrow in zip(left, right))


def _cm_mul(left, right):
    n = len(left)
    names = left[0][0].re.num.names
    zero = _cf_zero(names)
    rows = []
    for i in range(n):
        row = []
        for j in range(n):
            total = zero
            for k in range(n):
                total = _cf_add(total, _cf_mul(left[i][k], right[k][j]))
            row.append(total)
        rows.append(tuple(row))
    return tuple(rows)


def _cm_dagger(value):
    n = len(value)
    return tuple(tuple(_cf_conj(value[j][i]) for j in range(n)) for i in range(n))


def _cm_diff(value, name: str):
    return tuple(tuple(_cf_diff(entry, name) for entry in row) for row in value)


def _cm_eq(left, right) -> bool:
    return all(_cf_eq(a, b) for lrow, rrow in zip(left, right) for a, b in zip(lrow, rrow))


def _cm_is_zero(value) -> bool:
    return all(_cf_is_zero(entry) for row in value for entry in row)


def _cm_comm(left, right):
    return _cm_sub(_cm_mul(left, right), _cm_mul(right, left))


def _su2rot_field() -> tuple:
    u = _cm_from_rm(_su2rot_matrix())
    dagger = _cm_dagger(u)
    names = ("x", "y")
    ident = _cm_from_rm(((_rat_const(1, names), _rat_const(0, names)), (_rat_const(0, names), _rat_const(1, names))))
    if not _cm_eq(_cm_mul(u, dagger), ident) or not _cm_eq(_cm_mul(dagger, u), ident):
        raise KernelError("the rational SU(2) rotation was not unitary over Q(i)(x, y)")
    # det U = c^2 + s^2 = 1 already checked on the real matrix.
    return u, dagger



def _su3rot_matrix() -> tuple[tuple[MRat, ...], ...]:
    """The rational SU(2) rotation, embedded in the 1-2 block of SU(3)."""
    u2 = _su2rot_matrix()
    names = u2[0][0].num.names
    zero = _rat_const(0, names)
    one = _rat_const(1, names)
    u = (
        (u2[0][0], u2[0][1], zero),
        (u2[1][0], u2[1][1], zero),
        (zero, zero, one),
    )
    ident = (
        (one, zero, zero),
        (zero, one, zero),
        (zero, zero, one),
    )
    if not _rm_eq(_rm_mul(_rm_transpose(u), u), ident) or not _rm_eq(_rm_mul(u, _rm_transpose(u)), ident):
        raise KernelError("the rational SU(3) rotation was not unitary")
    # det = det(SU(2) block) * 1 = 1, already checked on the 2-block.
    return u


def _su3rot_field() -> tuple:
    u = _cm_from_rm(_su3rot_matrix())
    dagger = _cm_dagger(u)
    names = ("x", "y")
    zero = _cf_zero(names)
    one = _cf_from_mrat(_rat_const(1, names))
    ident = (
        (one, zero, zero),
        (zero, one, zero),
        (zero, zero, one),
    )
    if not _cm_eq(_cm_mul(u, dagger), ident) or not _cm_eq(_cm_mul(dagger, u), ident):
        raise KernelError("the rational SU(3) rotation was not unitary over Q(i)(x, y)")
    return u, dagger


def gauge_transform_su3(connection, coord: str):
    """A_mu maps to U A_mu U dagger plus U d_mu U dagger, for the rational SU(3) rotation."""
    if coord not in {"x", "y"}:
        raise NotExact("this non-constant SU(3) gauge transform is admitted in x or y")
    u, dagger = _su3rot_field()
    return _cm_add(_cm_mul(u, _cm_mul(connection, dagger)), _cm_mul(u, _cm_diff(dagger, coord)))


def adjoint_field_su3(value):
    """F maps to U F U dagger for the rational SU(3) rotation U(x, y)."""
    u, dagger = _su3rot_field()
    return _cm_mul(u, _cm_mul(value, dagger))


def _nonconst_su3_covariance_check() -> None:
    names = ("x", "y")
    ax = _cm_from_cmatrix(su3_gen("1"), names)
    ay = _cm_from_cmatrix(su3_gen("2"), names)
    ax_p = gauge_transform_su3(ax, "x")
    ay_p = gauge_transform_su3(ay, "y")
    field = su2_field_fun(ax, ay)
    field_p = su2_field_fun(ax_p, ay_p)
    if not _cm_eq(field_p, adjoint_field_su3(field)):
        raise KernelError("a non-constant SU(3) gauge transformation did not act covariantly on the field strength")


def gauge_transform(connection, coord: str):
    """A_μ ↦ U A_μ U† + U ∂_μ U† for the rational SU(2) rotation U(x, y)."""
    if coord not in {"x", "y"}:
        raise NotExact("this non-constant SU(2) gauge transform is admitted in x or y")
    u, dagger = _su2rot_field()
    return _cm_add(_cm_mul(u, _cm_mul(connection, dagger)), _cm_mul(u, _cm_diff(dagger, coord)))


def adjoint_field(value):
    """F ↦ U F U† for the rational SU(2) rotation U(x, y)."""
    u, dagger = _su2rot_field()
    return _cm_mul(u, _cm_mul(value, dagger))


def su2_field_fun(ax, ay):
    """F = ∂_x A_y − ∂_y A_x + [A_x, A_y], with exact rational partials."""
    return _cm_add(_cm_sub(_cm_diff(ay, "x"), _cm_diff(ax, "y")), _cm_comm(ax, ay))


def _nonconst_covariance_check() -> None:
    names = ("x", "y")
    ax = _cm_from_cmatrix(su2_gen("x"), names)
    ay = _cm_from_cmatrix(su2_gen("y"), names)
    ax_p = gauge_transform(ax, "x")
    ay_p = gauge_transform(ay, "y")
    field = su2_field_fun(ax, ay)
    field_p = su2_field_fun(ax_p, ay_p)
    if not _cm_eq(field_p, adjoint_field(field)):
        raise KernelError("a non-constant SU(2) gauge transformation did not act covariantly on the field strength")


def u1_field(ax: MRat, ay: MRat, x_name: str = "x", y_name: str = "y") -> MRat:

    return mrat_sub(mrat_diff(ay, x_name), mrat_diff(ax, y_name))


def su2_field_const(ax: CMatrix, ay: CMatrix) -> CMatrix:
    # Constant components: F = [A_x, A_y]
    return commutator(ax, ay)


def adjoint_action(u: CMatrix, value: CMatrix) -> CMatrix:
    if not is_unitary(u):
        raise NotExact("this gauge transformation is not unitary")
    from pgi.math.hilbert import cmatrix_det
    from pgi.math.cnum import c_is_one

    det = cmatrix_det(u)
    if not c_is_one(det):
        # SU(2) requires det = 1. U(1) phase with det on the circle stays open here.
        raise NotExact("this gauge transformation is not special unitary")
    return cmatrix_mul(u, cmatrix_mul(value, cmatrix_dagger(u)))


# --- term routing ---

GAUGE_OPS = frozenset({
    "su2",
    "su3",
    "gellmann",
    "structure",
    "killing",
    "jacobi",
    "fieldstrength",
    "puregauge",
    "su2rot",
    "su3rot",
    "adjoint",
    "gauge",
})


def _contains_op(term: Term, names: frozenset[str]) -> bool:
    if isinstance(term, App):
        if term.op in names:
            return True
        return any(_contains_op(arg, names) for arg in term.args)
    return False


def has_gauge(term: Term) -> bool:
    if _contains_op(term, frozenset({"d", "partial", "diff"})) and not _contains_op(term, GAUGE_OPS):
        return False
    return _contains_op(term, GAUGE_OPS)


def _algebra_of(term: Term) -> str:
    name = _name(term)
    if name in {"su2", "su(2)"}:
        return "su2"
    if name in {"su3", "su(3)"}:
        return "su3"
    if name in {"u1", "u(1)"}:
        return "u1"
    raise NotExact("this gauge group is not U(1), SU(2), or SU(3)")


def _eval(term: Term):
    _standing()
    if isinstance(term, App):
        if term.op == "su2":
            if len(term.args) != 1:
                raise NotExact("su2 takes a generator label")
            return su2_gen(_name(term.args[0]))
        if term.op == "su3":
            if len(term.args) != 1:
                raise NotExact("su3 takes a generator label")
            return su3_gen(_name(term.args[0]))
        if term.op == "gellmann":
            if len(term.args) != 1:
                raise NotExact("gellmann takes an index")
            return gellmann(_idx(_name(term.args[0]), "su3"))
        if term.op == "structure":
            if len(term.args) != 4:
                raise NotExact("structure takes an algebra and three indices")
            algebra = _algebra_of(term.args[0])
            return structure(algebra, _idx(_name(term.args[1]), algebra), _idx(_name(term.args[2]), algebra), _idx(_name(term.args[3]), algebra))
        if term.op == "killing":
            if len(term.args) != 3:
                raise NotExact("killing takes an algebra and two indices")
            algebra = _algebra_of(term.args[0])
            return killing(algebra, _idx(_name(term.args[1]), algebra), _idx(_name(term.args[2]), algebra))
        if term.op == "jacobi":
            if len(term.args) != 1:
                raise NotExact("jacobi takes an algebra")
            algebra = _algebra_of(term.args[0])
            _algebra_checks(algebra)
            return c_zero()
        if term.op == "su2rot":
            # Displayed as a stand-in; the pure-gauge check is the certificate.
            raise NotExact("ask fieldstrength(puregauge(su2rot)) for the rational pure-gauge connection")
        if term.op == "puregauge":
            raise NotExact("ask fieldstrength(puregauge(su2rot))")
        if term.op == "fieldstrength":
            return _eval_field(term)
        if term.op == "gauge":
            if len(term.args) != 3:
                raise NotExact("gauge takes a rotation, a connection component, and a coordinate")
            if _is_su3rot(term.args[0]):
                return gauge_transform_su3(_eval_connection_field(term.args[1]), _name(term.args[2]))
            if not _is_su2rot(term.args[0]):
                raise NotExact("gauge takes su2rot or su3rot, a connection component, and a coordinate")
            return gauge_transform(_eval_connection_field(term.args[1]), _name(term.args[2]))
        if term.op == "adjoint":
            if len(term.args) != 2:
                raise NotExact("adjoint takes a special unitary matrix and a connection component")
            if _is_su3rot(term.args[0]):
                return adjoint_field_su3(_eval_connection_field(term.args[1]))
            if _is_su2rot(term.args[0]):
                return adjoint_field(_eval_connection_field(term.args[1]))
            return adjoint_action(_eval_matrix(term.args[0]), _eval_matrix(term.args[1]))
        if term.op in {"add", "sub", "mul", "neg", "trace", "dagger", "commutator", "comm", "pow", "div"}:
            return _eval_mixed(term)
    raise NotExact("this term is not a gauge-theory matrix or scalar")


def _eval_field(term: App):
    if len(term.args) < 1:
        raise NotExact("fieldstrength takes a group and a connection")
    first = term.args[0]
    # fieldstrength(puregauge(su2rot))
    if isinstance(first, App) and first.op == "puregauge":
        field = _pure_gauge_field(*_pure_gauge_connection())
        if not _rm_eq0(field):
            raise KernelError("a pure-gauge SU(2) connection had a nonzero field strength")
        return cmatrix_zero(2, 2)
    group = _algebra_of(first)
    if group == "u1":
        if len(term.args) not in {3, 5}:
            raise NotExact("a U(1) field strength takes two components, and optionally two coordinates")
        ax = eval_symbolic(term.args[1])
        ay = eval_symbolic(term.args[2])
        x_name, y_name = "x", "y"
        if len(term.args) == 5:
            x_name, y_name = _name(term.args[3]), _name(term.args[4])
        return u1_field(ax, ay, x_name, y_name)
    if group == "su2":
        if len(term.args) != 3:
            raise NotExact("an SU(2) field strength takes two connection components")
        if _is_fun_connection(term.args[1]) or _is_fun_connection(term.args[2]):
            return su2_field_fun(_eval_connection_field(term.args[1]), _eval_connection_field(term.args[2]))
        return su2_field_const(_eval_matrix(term.args[1]), _eval_matrix(term.args[2]))
    if group == "su3":
        if len(term.args) != 3:
            raise NotExact("an SU(3) field strength takes two connection components")
        if _is_fun_connection(term.args[1]) or _is_fun_connection(term.args[2]):
            return su2_field_fun(_eval_connection_field(term.args[1]), _eval_connection_field(term.args[2]))
        ax = _eval_matrix(term.args[1])
        ay = _eval_matrix(term.args[2])
        if ax.nrows != 3 or ay.nrows != 3:
            raise NotExact("an SU(3) connection component must be 3x3")
        return su2_field_const(ax, ay)
    raise NotExact("a field strength for this group is not available here")


def _is_su2rot(term: Term) -> bool:
    if isinstance(term, Var) and term.name == "su2rot":
        return True
    return isinstance(term, App) and term.op == "su2rot"


def _is_su3rot(term: Term) -> bool:
    if isinstance(term, Var) and term.name == "su3rot":
        return True
    return isinstance(term, App) and term.op == "su3rot"


def _is_cfun_matrix(value) -> bool:
    return (
        isinstance(value, tuple)
        and value
        and isinstance(value[0], tuple)
        and value[0]
        and isinstance(value[0][0], CFun)
    )


def _is_fun_connection(term: Term) -> bool:
    return isinstance(term, App) and term.op in {"gauge"} or (isinstance(term, App) and term.op == "adjoint" and term.args and (_is_su2rot(term.args[0]) or _is_su3rot(term.args[0])))


def _eval_connection_field(term: Term):
    value = _eval_any(term)
    if _is_cfun_matrix(value):
        return value
    if isinstance(value, CMatrix):
        return _cm_from_cmatrix(value, ("x", "y"))
    raise NotExact("this term is not an SU(2) connection component")


def _eval_matrix(term: Term) -> CMatrix:
    value = _eval_any(term)
    if isinstance(value, CMatrix):
        return value
    raise NotExact("this term is not a gauge-theory matrix")


def _eval_any(term: Term):
    _standing()
    if isinstance(term, App) and term.op in GAUGE_OPS:
        return _eval(term)
    if isinstance(term, App) and term.op in {"add", "sub", "mul", "neg", "trace", "dagger", "commutator", "comm", "pow", "div", "hermitian", "unitary"}:
        return _eval_mixed(term)
    if has_hilbert(term) or has_matrix_shape(term):
        from pgi.math.hilbert import _eval as hilbert_eval

        return hilbert_eval(term)
    # scalars and rationals
    try:
        from pgi.math.hilbert import eval_cnum

        return eval_cnum(term)
    except NotExact:
        return eval_symbolic(term)


def _eval_mixed(term: App):
    from pgi.math.hilbert import (
        cmatrix_add,
        cmatrix_mul,
        cmatrix_neg,
        cmatrix_smul,
        cmatrix_sub,
        cmatrix_dagger,
        cmatrix_trace,
        commutator,
    )
    from pgi.math.cnum import CNum, c_inv, c_neg, c_mul, c_add, c_sub, c_div

    if term.op == "neg" and len(term.args) == 1:
        value = _eval_any(term.args[0])
        if isinstance(value, CMatrix):
            return cmatrix_neg(value)
        if isinstance(value, CNum):
            return c_neg(value)
        return mrat_neg(value)
    if term.op == "dagger" and len(term.args) == 1:
        return cmatrix_dagger(_eval_matrix(term.args[0]))
    if term.op == "trace" and len(term.args) == 1:
        return cmatrix_trace(_eval_matrix(term.args[0]))
    if term.op in {"commutator", "comm"} and len(term.args) == 2:
        return commutator(_eval_matrix(term.args[0]), _eval_matrix(term.args[1]))
    if term.op == "pow" and len(term.args) == 2 and isinstance(term.args[1], IntLit):
        from pgi.math.hilbert import _matrix_power

        base = _eval_any(term.args[0])
        if isinstance(base, CMatrix):
            return _matrix_power(base, term.args[1].n)
        raise NotExact("this power is not a gauge-theory matrix power")
    if len(term.args) == 2 and term.op in {"add", "sub", "mul", "div"}:
        left, right = _eval_any(term.args[0]), _eval_any(term.args[1])
        if isinstance(left, CMatrix) and isinstance(right, CMatrix):
            if term.op == "add":
                return cmatrix_add(left, right)
            if term.op == "sub":
                return cmatrix_sub(left, right)
            if term.op == "mul":
                return cmatrix_mul(left, right)
            raise NotExact("these matrices do not divide")
        if term.op == "mul" and isinstance(left, CNum) and isinstance(right, CMatrix):
            return cmatrix_smul(left, right)
        if term.op == "mul" and isinstance(left, CMatrix) and isinstance(right, CNum):
            return cmatrix_smul(right, left)
        if term.op == "div" and isinstance(left, CMatrix) and isinstance(right, CNum):
            return cmatrix_smul(c_inv(right), left)
        if isinstance(left, CNum) and isinstance(right, CNum):
            if term.op == "add":
                return c_add(left, right)
            if term.op == "sub":
                return c_sub(left, right)
            if term.op == "mul":
                return c_mul(left, right)
            return c_div(left, right)
        if isinstance(left, MRat) and isinstance(right, MRat):
            if term.op == "add":
                return mrat_add(left, right)
            if term.op == "sub":
                return mrat_sub(left, right)
            if term.op == "mul":
                return mrat_mul(left, right)
            from pgi.math.poly import mrat_div

            return mrat_div(left, right)
    raise NotExact("this term is not a gauge-theory matrix or scalar")


@dataclass(frozen=True)
class GaugeMatrix:
    value: CMatrix
    origin: Term
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        got = _eval_any(self.origin)
        if not isinstance(got, CMatrix) or not cmatrix_eq(got, self.value):
            raise KernelError("this gauge-theory result does not match the exact evaluation")


@dataclass(frozen=True)
class GaugeScalar:
    value: CNum
    origin: Term
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        got = _eval_any(self.origin)
        if not isinstance(got, CNum) or not c_eq(got, self.value):
            raise KernelError("this gauge-theory scalar does not match the exact evaluation")


@dataclass(frozen=True)
class GaugeRat:
    value: MRat
    origin: Term
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        got = _eval_any(self.origin)
        if not isinstance(got, MRat) or not mrat_eq(got, self.value):
            raise KernelError("this gauge-theory field strength does not match the exact evaluation")


@dataclass(frozen=True)
class GaugeField:
    value: tuple
    origin: Term
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        got = _eval_any(self.origin)
        if not _is_cfun_matrix(got) or not _cm_eq(got, self.value):
            raise KernelError("this position-dependent gauge result does not match the exact evaluation")


def eval_gauge_result(term: Term):
    _standing()
    value = _eval_any(term)
    if isinstance(value, CMatrix):
        return GaugeMatrix(value, term, _detail())
    if _is_cfun_matrix(value):
        return GaugeField(value, term, _detail())
    if isinstance(value, CNum):
        ratio = c_as_ratio(value)
        if ratio is not None:
            return rat_normalize(ratio.num, ratio.den)
        return GaugeScalar(value, term, _detail())
    if isinstance(value, MRat):
        return GaugeRat(value, term, _detail())
    if isinstance(value, RatTheorem):
        return value
    raise NotExact("this term is not a gauge-theory matrix or scalar")


def _detail() -> tuple[str, ...]:
    return (
        "The su(2) and su(3) structure constants, Jacobi identity, and Killing form are checked exactly.",
        "A U(1) field strength is invariant under A ↦ A + dλ. An SU(2) field strength of constant components transforms as F ↦ U F U†, and tr(F²) is invariant.",
        "A position-dependent SU(2) gauge transformation by the rational rotation U(x, y) acts by A_μ ↦ U A_μ U† + U ∂_μ U†, and F ↦ U F U†, checked identically.",
        "A pure-gauge connection from a rational SU(2) rotation has vanishing field strength.",
    )


def gauge_value_rule(origin: Term, result: object, prelude: tuple[str, ...] = ()) -> Rule:
    title_left = pretty(origin)
    if isinstance(result, RatTheorem):
        from pgi.math.rational import ratio_rule

        return ratio_rule(origin, result, prelude)
    if isinstance(result, GaugeScalar):
        shown = show_cnum(result.value)
        return Rule(
            id=f"math.cnum.{shown}",
            layer="base",
            stage="quantity",
            title=f"{title_left} = {shown}",
            produces=f"cnum({shown})",
            detail_lines=(*prelude, *result.detail),
        )
    if isinstance(result, GaugeMatrix):
        shown = show_cmatrix(result.value)
        return Rule(
            id=f"math.cmatrix.{shown}",
            layer="base",
            stage="quantity",
            title=f"{title_left} = {shown}",
            produces=f"cmatrix({shown})",
            detail_lines=(*prelude, *result.detail),
        )
    if isinstance(result, GaugeField):
        shown = "gaugefield"
        return Rule(
            id="math.gaugefield",
            layer="base",
            stage="quantity",
            title=f"{title_left} = {shown}",
            produces=shown,
            detail_lines=(*prelude, *result.detail),
        )
    if isinstance(result, GaugeRat):
        shown = show_rat(result.value)
        kind = "poly" if result.value.is_poly else "rat"
        return Rule(
            id=f"math.{kind}.{shown}",
            layer="base",
            stage="quantity",
            title=f"{title_left} = {shown}",
            produces=f"{kind}({shown})",
            detail_lines=(*prelude, *result.detail),
        )
    raise KernelError("this gauge-theory result has no claim")


def gauge_equality_rules(
    left: Term,
    right: Term,
    left_value: object,
    right_value: object,
    prelude: tuple[str, ...] = (),
) -> tuple[Rule, ...]:
    title = f"{pretty(left)} = {pretty(right)}"
    if _gauge_eq(left_value, right_value):
        return (
            Rule(
                id="math.gauge.eq",
                layer="base",
                stage="quantity",
                title=title,
                produces=f"identity({title})",
                detail_lines=(*prelude, "The two sides are the same exact matrix, scalar, or rational field strength."),
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


def _gauge_eq(left: object, right: object) -> bool:
    lm, rm = _as_matrix(left), _as_matrix(right)
    if lm is not None and rm is not None:
        return cmatrix_eq(lm, rm)
    ls, rs = _as_scalar(left), _as_scalar(right)
    if ls is not None and rs is not None:
        return c_eq(ls, rs)
    lr, rr = _as_ratfun(left), _as_ratfun(right)
    if lr is not None and rr is not None:
        return mrat_eq(lr, rr)
    lf, rf = _as_field(left), _as_field(right)
    if lf is not None and rf is not None:
        return _cm_eq(lf, rf)
    return False


def _as_field(value: object):
    if isinstance(value, GaugeField):
        return value.value
    if _is_cfun_matrix(value):
        return value
    return None


def _as_matrix(value: object) -> CMatrix | None:
    if isinstance(value, (GaugeMatrix, HilbTheorem)):
        return value.value
    if isinstance(value, CMatrix):
        return value
    return None


def _as_scalar(value: object) -> CNum | None:
    if isinstance(value, (GaugeScalar, ScalarTheorem)):
        return value.value
    if isinstance(value, CNum):
        return value
    if isinstance(value, RatTheorem):
        return c_from_ratio(value.value)
    return None


def _as_ratfun(value: object) -> MRat | None:
    if isinstance(value, GaugeRat):
        return value.value
    if isinstance(value, MRat):
        return value
    if isinstance(value, RatTheorem):
        return as_rat(const_poly(value.value))
    return None


def side_as_gauge(term: Term) -> object:
    try:
        return eval_gauge_result(term)
    except NotExact:
        if has_hilbert(term) or has_matrix_shape(term):
            return side_as_hilbert(term)
        try:
            from pgi.math.rational import eval_rat

            return eval_rat(term)
        except NotExact:
            return eval_symbolic(term)

_standing()
