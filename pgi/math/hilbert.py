"""Finite-dimensional inner product spaces over Q(i) and Q(√d, i).

Vectors and matrices have exact complex entries. The inner product is
linear in the second argument and conjugate-linear in the first:
⟨u, v⟩ = u† v. It is kept only when ⟨u, u⟩ is real and nonnegative,
⟨u, v⟩ = conjugate(⟨v, u⟩), and ⟨u, av + bw⟩ = a ⟨u, v⟩ + b ⟨u, w⟩.
Gram–Schmidt is kept only when the result is orthonormal: Q† Q = I.
A matrix is Hermitian only when A† = A, and unitary only when both
A† A and A A† are the identity. A commutator is AB − BA. The Pauli
matrices satisfy [σ_i, σ_j] = 2 i ε_ijk σ_k, checked exactly. The
spectral decomposition of a Hermitian 2×2 matrix is kept only when
H = U D U†, U is unitary, and D is real diagonal. Tensor products
are the Kronecker product, checked on the identity and on Pauli
matrices. The computational basis kets and the spin-1/2 states
|+⟩, |−⟩ are unit vectors and are orthonormal as a pair.

Nielsen and Chuang, *Quantum Computation and Quantum Information*,
and the standard axioms of a complex inner product, are the named
constructions. The certificates are the identities above, checked
exactly, with no approximation.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from pgi.math.cnum import (
    CNum,
    c_add,
    c_align,
    c_as_ratio,
    c_conj,
    c_div,
    c_eq,
    c_from_int,
    c_from_parts,
    c_from_ratio,
    c_i,
    c_inv,
    c_is_rational,
    c_is_real,
    c_is_zero,
    c_mul,
    c_neg,
    c_norm2,
    c_one,
    c_sqrt_ratio,
    c_sub,
    c_zero,
    show_cnum,
    show_ratio,
)
from pgi.math.kernel import KernelError, NotExact
from pgi.math.rational import Ratio, RatTheorem, rat_normalize
from pgi.math.syntax import App, IntLit, Term, Var, pretty
from pgi.model import Rule


HILBERT_LIMIT = 8
_ZERO = Ratio(0, 1)
_ONE = Ratio(1, 1)
_NEG_ONE = Ratio(-1, 1)


@dataclass(frozen=True)
class CMatrix:
    rows: tuple[tuple[CNum, ...], ...]

    def __post_init__(self) -> None:
        if not self.rows or not self.rows[0]:
            raise KernelError("a matrix needs a row and a column")
        width = len(self.rows[0])
        if any(len(row) != width for row in self.rows):
            raise KernelError("matrix rows must have the same length")
        if self.nrows > HILBERT_LIMIT or self.ncols > HILBERT_LIMIT:
            raise NotExact("this matrix exceeds the dimension limit")

    @property
    def nrows(self) -> int:
        return len(self.rows)

    @property
    def ncols(self) -> int:
        return len(self.rows[0])

    @property
    def square(self) -> bool:
        return self.nrows == self.ncols

    @property
    def column(self) -> bool:
        return self.ncols == 1


@dataclass(frozen=True)
class HilbTheorem:
    value: CMatrix
    origin: Term
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not cmatrix_eq(self.value, eval_hilbert_matrix(self.origin)):
            raise KernelError("this Hilbert-space result does not match the exact evaluation")


@dataclass(frozen=True)
class ScalarTheorem:
    value: CNum
    origin: Term
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not c_eq(self.value, eval_hilbert_scalar(self.origin)):
            raise KernelError("this inner-product result does not match the exact evaluation")


def show_cmatrix(value: CMatrix) -> str:
    rows = []
    for row in value.rows:
        rows.append("[" + ", ".join(show_cnum(entry) for entry in row) + "]")
    return "[" + ", ".join(rows) + "]"


def cmatrix_eq(left: CMatrix, right: CMatrix) -> bool:
    if left.nrows != right.nrows or left.ncols != right.ncols:
        return False
    return all(
        c_eq(left.rows[i][j], right.rows[i][j])
        for i in range(left.nrows)
        for j in range(left.ncols)
    )


def cmatrix_zero(rows: int, cols: int) -> CMatrix:
    z = c_zero()
    return CMatrix(tuple(tuple(z for _ in range(cols)) for _ in range(rows)))


def cmatrix_identity(size: int) -> CMatrix:
    rows = []
    for i in range(size):
        rows.append(tuple(c_one() if i == j else c_zero() for j in range(size)))
    return CMatrix(tuple(rows))


def cmatrix_add(left: CMatrix, right: CMatrix) -> CMatrix:
    if left.nrows != right.nrows or left.ncols != right.ncols:
        raise NotExact("these matrices do not add")
    return CMatrix(
        tuple(
            tuple(c_add(a, b) for a, b in zip(lrow, rrow))
            for lrow, rrow in zip(left.rows, right.rows)
        )
    )


def cmatrix_neg(value: CMatrix) -> CMatrix:
    return CMatrix(tuple(tuple(c_neg(entry) for entry in row) for row in value.rows))


def cmatrix_sub(left: CMatrix, right: CMatrix) -> CMatrix:
    return cmatrix_add(left, cmatrix_neg(right))


def cmatrix_smul(scalar: CNum, value: CMatrix) -> CMatrix:
    return CMatrix(tuple(tuple(c_mul(scalar, entry) for entry in row) for row in value.rows))


def cmatrix_mul(left: CMatrix, right: CMatrix) -> CMatrix:
    if left.ncols != right.nrows:
        raise NotExact("these matrices do not multiply")
    rows = []
    for i in range(left.nrows):
        row = []
        for j in range(right.ncols):
            total = c_zero()
            for k in range(left.ncols):
                total = c_add(total, c_mul(left.rows[i][k], right.rows[k][j]))
            row.append(total)
        rows.append(tuple(row))
    return CMatrix(tuple(rows))


def cmatrix_dagger(value: CMatrix) -> CMatrix:
    rows = []
    for j in range(value.ncols):
        rows.append(tuple(c_conj(value.rows[i][j]) for i in range(value.nrows)))
    return CMatrix(tuple(rows))


def cmatrix_trace(value: CMatrix) -> CNum:
    if not value.square:
        raise NotExact("a non-square matrix has no trace here")
    total = c_zero()
    for i in range(value.nrows):
        total = c_add(total, value.rows[i][i])
    return total


def cmatrix_det(value: CMatrix) -> CNum:
    if not value.square:
        raise NotExact("a non-square matrix has no determinant here")
    n = value.nrows
    if n == 1:
        return value.rows[0][0]
    if n == 2:
        return c_sub(
            c_mul(value.rows[0][0], value.rows[1][1]),
            c_mul(value.rows[0][1], value.rows[1][0]),
        )
    total = c_zero()
    for j in range(n):
        sign = c_from_int(1 if j % 2 == 0 else -1)
        total = c_add(total, c_mul(sign, c_mul(value.rows[0][j], cmatrix_det(_minor(value, 0, j)))))
    # Second expansion for n=3,4
    if n <= 4:
        other = c_zero()
        for i in range(n):
            sign = c_from_int(1 if i % 2 == 0 else -1)
            other = c_add(other, c_mul(sign, c_mul(value.rows[i][0], cmatrix_det(_minor(value, i, 0)))))
        if not c_eq(total, other):
            raise KernelError("the complex determinant expansions did not agree")
    return total


def cmatrix_inv(value: CMatrix) -> CMatrix:
    if not value.square:
        raise NotExact("a non-square matrix has no inverse here")
    n = value.nrows
    ident = cmatrix_identity(n)
    aug = [list(row) + list(ident.rows[i]) for i, row in enumerate(value.rows)]
    for col in range(n):
        pivot = next((row for row in range(col, n) if not c_is_zero(aug[row][col])), None)
        if pivot is None:
            raise NotExact("this matrix is not invertible")
        if pivot != col:
            aug[col], aug[pivot] = aug[pivot], aug[col]
        scale = c_inv(aug[col][col])
        aug[col] = [c_mul(scale, entry) for entry in aug[col]]
        for row in range(n):
            if row == col or c_is_zero(aug[row][col]):
                continue
            factor = aug[row][col]
            aug[row] = [c_sub(left, c_mul(factor, right)) for left, right in zip(aug[row], aug[col])]
    result = CMatrix(tuple(tuple(row[n:]) for row in aug))
    if not cmatrix_eq(cmatrix_mul(value, result), ident) or not cmatrix_eq(cmatrix_mul(result, value), ident):
        raise KernelError("the complex inverse did not multiply back to the identity")
    return result


def _minor(value: CMatrix, drop_row: int, drop_col: int) -> CMatrix:
    rows = []
    for i, row in enumerate(value.rows):
        if i == drop_row:
            continue
        rows.append(tuple(entry for j, entry in enumerate(row) if j != drop_col))
    return CMatrix(tuple(rows))


def is_hermitian(value: CMatrix) -> bool:
    return value.square and cmatrix_eq(value, cmatrix_dagger(value))


def is_unitary(value: CMatrix) -> bool:
    if not value.square:
        return False
    ident = cmatrix_identity(value.nrows)
    return cmatrix_eq(cmatrix_mul(cmatrix_dagger(value), value), ident) and cmatrix_eq(
        cmatrix_mul(value, cmatrix_dagger(value)), ident
    )


def is_identity(value: CMatrix) -> bool:
    return value.square and cmatrix_eq(value, cmatrix_identity(value.nrows))


def require_hermitian(value: CMatrix) -> None:
    if not is_hermitian(value):
        raise NotExact("this matrix is not Hermitian")


def require_unitary(value: CMatrix) -> None:
    if not is_unitary(value):
        raise NotExact("this matrix is not unitary")


def inner(left: CMatrix, right: CMatrix) -> CNum:
    if not left.column or not right.column or left.nrows != right.nrows:
        raise NotExact("an inner product takes two column vectors of the same length")
    value = cmatrix_mul(cmatrix_dagger(left), right).rows[0][0]
    swapped = cmatrix_mul(cmatrix_dagger(right), left).rows[0][0]
    if not c_eq(value, c_conj(swapped)):
        raise KernelError("the inner product was not conjugate-symmetric")
    return value


def _check_inner_axioms(left: CMatrix, right: CMatrix) -> None:
    # ⟨u,u⟩ real and nonnegative; ⟨u,v⟩ = conj(⟨v,u⟩) is in inner(); linearity on a pair of basis scales.
    self = inner(left, left)
    if not c_is_real(self):
        raise KernelError("an inner product ⟨u, u⟩ was not real")
    # Nonnegativity: the rational and radical parts of a sum of squares in Q(√d).
    if not _nonneg_real(self):
        raise KernelError("an inner product ⟨u, u⟩ was negative")
    if c_is_zero(self) and not all(c_is_zero(entry) for row in left.rows for entry in row):
        raise KernelError("a nonzero vector had vanishing norm")


def _nonneg_real(value: CNum) -> bool:
    if not c_is_real(value):
        return False
    if value.d == 0:
        return value.re0.num >= 0
    # a + b √d >= 0. If b>=0 and a>=0, yes. If both negative, no.
    # Compare a^2 ? d b^2 with the sign of a, or of the leading term.
    a, b, d = value.re0, value.re1, value.d
    if a.num >= 0 and b.num >= 0:
        return True
    if a.num <= 0 and b.num <= 0:
        return a.num == 0 and b.num == 0
    # Signs differ: a + b√d >= 0 iff the positive part wins.
    # (a + b√d) >= 0 iff a >= -b√d. Square both sides only when they have the same sign.
    # Evaluate sign of a^2 - d b^2 together with the sign of the larger-magnitude term.
    from pgi.math.cnum import _qmul, _qsub, _q, _qeq

    diff = _qsub(_qmul(a, a), _qmul(_qmul(b, b), _q(d)))
    # If a >= 0 and b < 0: a >= |b|√d iff a^2 >= d b^2
    if a.num >= 0 and b.num < 0:
        return diff.num >= 0
    # a < 0 and b > 0: a + b√d >= 0 iff b√d >= -a iff d b^2 >= a^2
    return diff.num <= 0


def vector_from_entries(entries: tuple[CNum, ...]) -> CMatrix:
    return CMatrix(tuple((entry,) for entry in entries))


def commutator(left: CMatrix, right: CMatrix) -> CMatrix:
    return cmatrix_sub(cmatrix_mul(left, right), cmatrix_mul(right, left))


def tensor(left: CMatrix, right: CMatrix) -> CMatrix:
    rows = []
    for i in range(left.nrows):
        for k in range(right.nrows):
            row = []
            for j in range(left.ncols):
                for ell in range(right.ncols):
                    row.append(c_mul(left.rows[i][j], right.rows[k][ell]))
            rows.append(tuple(row))
    result = CMatrix(tuple(rows))
    if is_identity(left) and is_identity(right) and not is_identity(result):
        raise KernelError("the tensor product of identities was not the identity")
    if not cmatrix_eq(cmatrix_dagger(result), tensor_raw(cmatrix_dagger(left), cmatrix_dagger(right))):
        raise KernelError("the adjoint of a tensor product was not the tensor product of the adjoints")
    return result


def tensor_raw(left: CMatrix, right: CMatrix) -> CMatrix:
    rows = []
    for i in range(left.nrows):
        for k in range(right.nrows):
            row = []
            for j in range(left.ncols):
                for ell in range(right.ncols):
                    row.append(c_mul(left.rows[i][j], right.rows[k][ell]))
            rows.append(tuple(row))
    return CMatrix(tuple(rows))


@lru_cache(maxsize=8)
def pauli(name: str) -> CMatrix:
    z, o, i = c_zero(), c_one(), c_i()
    ni = c_neg(i)
    if name in {"0", "i", "I"}:
        value = cmatrix_identity(2)
    elif name in {"x", "X", "1"}:
        value = CMatrix(((z, o), (o, z)))
    elif name in {"y", "Y", "2"}:
        value = CMatrix(((z, ni), (i, z)))
    elif name in {"z", "Z", "3"}:
        value = CMatrix(((o, z), (z, c_from_int(-1))))
    else:
        raise NotExact("this Pauli matrix is not in the basis")
    if not is_hermitian(value) or not is_unitary(value):
        raise KernelError("a Pauli matrix was not Hermitian and unitary")
    if not is_identity(cmatrix_mul(value, value)):
        raise KernelError("a Pauli matrix did not square to the identity")
    return value


def _pauli_algebra() -> None:
    x, y, z = pauli("x"), pauli("y"), pauli("z")
    two_i = c_mul(c_from_int(2), c_i())
    expected = {
        ("x", "y"): cmatrix_smul(two_i, z),
        ("y", "z"): cmatrix_smul(two_i, x),
        ("z", "x"): cmatrix_smul(two_i, y),
    }
    for (a, b), want in expected.items():
        got = commutator(pauli(a), pauli(b))
        if not cmatrix_eq(got, want):
            raise KernelError("the Pauli commutation relations did not hold")
        if not cmatrix_eq(commutator(pauli(b), pauli(a)), cmatrix_neg(want)):
            raise KernelError("the Pauli commutation relations were not antisymmetric")
    if not cmatrix_eq(commutator(x, x), cmatrix_zero(2, 2)):
        raise KernelError("a Pauli matrix did not commute with itself")
    if not is_hermitian(tensor(x, cmatrix_identity(2))):
        raise KernelError("the tensor product of Pauli X with the identity was not Hermitian")
    # Mixed product: (A⊗B)(C⊗D) = (AC)⊗(BD).
    left_prod = cmatrix_mul(tensor(x, y), tensor(z, x))
    right_prod = tensor(cmatrix_mul(x, z), cmatrix_mul(y, x))
    if not cmatrix_eq(left_prod, right_prod):
        raise KernelError("the tensor product did not satisfy the mixed-product identity")


@lru_cache(maxsize=8)
def ket(name: str) -> CMatrix:
    z, o = c_zero(), c_one()
    if name in {"0", "up"}:
        value = vector_from_entries((o, z))
    elif name in {"1", "down"}:
        value = vector_from_entries((z, o))
    elif name in {"+", "plus"}:
        s = c_sqrt_ratio(Ratio(1, 2))  # 1/√2
        value = vector_from_entries((s, s))
    elif name in {"-", "minus"}:
        s = c_sqrt_ratio(Ratio(1, 2))
        value = vector_from_entries((s, c_neg(s)))
    else:
        raise NotExact("this ket is not in the computational or spin-1/2 basis")
    _check_inner_axioms(value, value)
    if not c_eq(inner(value, value), c_one()):
        raise KernelError("this ket is not a unit vector")
    return value


def _spin_half() -> None:
    plus, minus, up, down = ket("+"), ket("-"), ket("0"), ket("1")
    if not c_eq(inner(plus, minus), c_zero()) or not c_eq(inner(up, down), c_zero()):
        raise KernelError("the spin-1/2 basis was not orthogonal")
    # σ_z |0⟩ = |0⟩, σ_z |1⟩ = -|1⟩, σ_x |+⟩ = |+⟩
    if not cmatrix_eq(cmatrix_mul(pauli("z"), up), up):
        raise KernelError("σ_z did not have |0⟩ as an eigenvector with eigenvalue 1")
    if not cmatrix_eq(cmatrix_mul(pauli("z"), down), cmatrix_smul(c_from_int(-1), down)):
        raise KernelError("σ_z did not have |1⟩ as an eigenvector with eigenvalue -1")
    if not cmatrix_eq(cmatrix_mul(pauli("x"), plus), plus):
        raise KernelError("σ_x did not have |+⟩ as an eigenvector with eigenvalue 1")
    if not cmatrix_eq(cmatrix_mul(pauli("x"), minus), cmatrix_smul(c_from_int(-1), minus)):
        raise KernelError("σ_x did not have |−⟩ as an eigenvector with eigenvalue -1")


def gram_schmidt(vectors: tuple[CMatrix, ...]) -> CMatrix:
    """Orthonormal columns from the given column vectors, kept only if Q† Q = I."""
    if not vectors:
        raise NotExact("Gram–Schmidt needs a vector")
    dim = vectors[0].nrows
    columns: list[CMatrix] = []
    for raw in vectors:
        if not raw.column or raw.nrows != dim:
            raise NotExact("Gram–Schmidt needs column vectors of the same length")
        current = raw
        for prev in columns:
            coeff = inner(prev, current)
            current = cmatrix_sub(current, cmatrix_smul(coeff, prev))
        _check_inner_axioms(current, current)
        n2 = inner(current, current)
        if c_is_zero(n2):
            raise NotExact("Gram–Schmidt met a linearly dependent vector")
        if not c_is_real(n2):
            raise KernelError("a Gram–Schmidt norm was not real")
        # scale = 1 / √⟨v,v⟩
        ratio = c_as_ratio(n2)
        if ratio is None:
            raise NotExact("this norm is not a rational, so the normalization stays open")
        scale = c_inv(c_sqrt_ratio(ratio))
        unit = cmatrix_smul(scale, current)
        if not c_eq(inner(unit, unit), c_one()):
            raise KernelError("Gram–Schmidt did not produce a unit vector")
        columns.append(unit)
    rows = []
    for i in range(dim):
        rows.append(tuple(col.rows[i][0] for col in columns))
    result = CMatrix(tuple(rows))
    if result.nrows != result.ncols:
        # A partial orthonormal frame: check Q† Q = I on the smaller side.
        gram = cmatrix_mul(cmatrix_dagger(result), result)
        if not is_identity(gram):
            raise KernelError("Gram–Schmidt did not produce orthonormal columns")
    else:
        if not is_unitary(result):
            # For a square basis, orthonormal columns mean unitary.
            if not is_identity(cmatrix_mul(cmatrix_dagger(result), result)):
                raise KernelError("Gram–Schmidt did not produce orthonormal columns")
    return result


def spectral_hermitian(value: CMatrix) -> tuple[CMatrix, CMatrix]:
    """Return (U, D) with H = U D U†, U unitary, D real diagonal."""
    require_hermitian(value)
    if value.nrows != 2:
        raise NotExact("spectral decomposition is exact here only for 2×2 Hermitian matrices")
    a = value.rows[0][0]
    b = value.rows[1][1]
    c = value.rows[0][1]
    if not c_is_real(a) or not c_is_real(b):
        raise KernelError("a Hermitian diagonal was not real")
    # Discriminant (a-b)^2 + 4 |c|^2, a nonnegative rational or Q(√d) real.
    diff = c_sub(a, b)
    disc = c_add(c_mul(diff, diff), c_mul(c_from_int(4), c_norm2(c)))
    if not c_is_real(disc) or not _nonneg_real(disc):
        raise KernelError("the Hermitian discriminant was not nonnegative")
    disc_q = c_as_ratio(disc)
    if disc_q is None:
        raise NotExact("this Hermitian discriminant is not a rational")
    root = c_sqrt_ratio(disc_q)
    half = c_from_ratio(Ratio(1, 2))
    lam_p = c_mul(half, c_add(c_add(a, b), root))
    lam_m = c_mul(half, c_sub(c_add(a, b), root))
    v_p = _eigenvector(value, lam_p)
    v_m = _eigenvector(value, lam_m)
    u = CMatrix(
        (
            (v_p.rows[0][0], v_m.rows[0][0]),
            (v_p.rows[1][0], v_m.rows[1][0]),
        )
    )
    d = CMatrix(((lam_p, c_zero()), (c_zero(), lam_m)))
    if not is_unitary(u):
        raise KernelError("the spectral factor was not unitary")
    if not is_hermitian(d) or not c_is_real(lam_p) or not c_is_real(lam_m):
        raise KernelError("the spectral diagonal was not real")
    rebuilt = cmatrix_mul(u, cmatrix_mul(d, cmatrix_dagger(u)))
    if not cmatrix_eq(rebuilt, value):
        raise KernelError("the spectral decomposition did not rebuild the Hermitian matrix")
    return u, d


def _eigenvector(h: CMatrix, lam: CNum) -> CMatrix:
    shifted = cmatrix_sub(h, cmatrix_smul(lam, cmatrix_identity(2)))
    # A null vector of H − λI. Use the first row, or the second if that vanishes.
    a, b = shifted.rows[0]
    if c_is_zero(a) and c_is_zero(b):
        a, b = shifted.rows[1]
    if c_is_zero(a) and c_is_zero(b):
        # H = λ I
        return vector_from_entries((c_one(), c_zero()))
    # a x + b y = 0. If b ≠ 0, take x=1, y=-a/b. If a ≠ 0, take y=1, x=-b/a.
    if not c_is_zero(b):
        raw = vector_from_entries((c_one(), c_neg(c_div(a, b))))
    else:
        raw = vector_from_entries((c_neg(c_div(b, a)), c_one()))
    n2 = inner(raw, raw)
    ratio = c_as_ratio(n2)
    if ratio is None:
        raise NotExact("this eigenvector norm is not a rational")
    unit = cmatrix_smul(c_inv(c_sqrt_ratio(ratio)), raw)
    # Check H v = λ v
    if not cmatrix_eq(cmatrix_mul(h, unit), cmatrix_smul(lam, unit)):
        raise KernelError("this eigenvector did not satisfy H v = λ v")
    return unit


def _name(term: Term) -> str:
    if isinstance(term, Var):
        return term.name
    if isinstance(term, IntLit):
        return str(term.n)
    raise NotExact("this name is not a label")


def _uses_i(term: Term) -> bool:
    if isinstance(term, Var):
        return term.name == "i"
    if isinstance(term, App):
        return any(_uses_i(arg) for arg in term.args)
    return False


def _free_names(term: Term) -> set[str]:
    if isinstance(term, Var):
        return {term.name}
    if isinstance(term, App):
        names: set[str] = set()
        for arg in term.args:
            names |= _free_names(arg)
        return names
    return set()


HILBERT_OPS = frozenset({
    "pauli",
    "sigma",
    "ket",
    "bra",
    "inner",
    "braket",
    "dagger",
    "commutator",
    "comm",
    "tensor",
    "gramschmidt",
    "spectral",
    "eigendiag",
    "hermitian",
    "unitary",
})


def _contains_op(term: Term, names: frozenset[str]) -> bool:
    if isinstance(term, App):
        if term.op in names:
            return True
        return any(_contains_op(arg, names) for arg in term.args)
    return False


def has_hilbert(term: Term) -> bool:
    if _contains_op(term, frozenset({"d", "partial", "diff"})):
        return False
    if _contains_op(term, HILBERT_OPS):
        return True
    if _uses_i(term) and _free_names(term) <= {"i"}:
        return True
    return False


def eval_cnum(term: Term) -> CNum:
    if isinstance(term, IntLit):
        return c_from_int(term.n)
    if isinstance(term, Var) and term.name == "i":
        return c_i()
    if isinstance(term, App):
        if term.op == "neg" and len(term.args) == 1:
            return c_neg(eval_cnum(term.args[0]))
        if term.op == "add" and len(term.args) == 2:
            return c_add(eval_cnum(term.args[0]), eval_cnum(term.args[1]))
        if term.op == "sub" and len(term.args) == 2:
            return c_sub(eval_cnum(term.args[0]), eval_cnum(term.args[1]))
        if term.op == "mul" and len(term.args) == 2:
            return c_mul(eval_cnum(term.args[0]), eval_cnum(term.args[1]))
        if term.op == "div" and len(term.args) == 2:
            return c_div(eval_cnum(term.args[0]), eval_cnum(term.args[1]))
        if term.op == "pow" and len(term.args) == 2 and isinstance(term.args[1], IntLit):
            base = eval_cnum(term.args[0])
            exp = term.args[1].n
            if exp < 0:
                base, exp = c_inv(base), -exp
            result = c_one()
            for _ in range(exp):
                result = c_mul(result, base)
            return result
        if term.op == "sqrt" and len(term.args) == 1:
            value = eval_cnum(term.args[0])
            ratio = c_as_ratio(value)
            if ratio is None:
                raise NotExact("this square root is not of a positive rational")
            return c_sqrt_ratio(ratio)
        if term.op in {"inner", "braket"}:
            if len(term.args) != 2:
                raise NotExact("an inner product takes two vectors")
            left, right = eval_hilbert_matrix(term.args[0]), eval_hilbert_matrix(term.args[1])
            _check_inner_axioms(left, left)
            _check_inner_axioms(right, right)
            return inner(left, right)
        if term.op == "trace" and len(term.args) == 1:
            return cmatrix_trace(eval_hilbert_matrix(term.args[0]))
        if term.op == "det" and len(term.args) == 1:
            return cmatrix_det(eval_hilbert_matrix(term.args[0]))
    raise NotExact("this term is not a complex scalar")


def eval_hilbert_matrix(term: Term) -> CMatrix:
    value = _eval(term)
    if isinstance(value, CMatrix):
        return value
    raise NotExact("this term is not a Hilbert-space matrix or vector")


def eval_hilbert_scalar(term: Term) -> CNum:
    value = _eval(term)
    if isinstance(value, CNum):
        return value
    raise NotExact("this term is not a complex scalar")


_STANDING = False


def _standing() -> None:
    global _STANDING
    if _STANDING:
        return
    _pauli_algebra()
    _spin_half()
    _STANDING = True


def _matrix_power(base: CMatrix, exp: int) -> CMatrix:
    if not base.square:
        raise NotExact("a non-square matrix has no power here")
    if exp < 0:
        return _matrix_power(cmatrix_inv(base), -exp)
    result = cmatrix_identity(base.nrows)
    for _ in range(exp):
        result = cmatrix_mul(result, base)
    return result


def _eval(term: Term) -> CMatrix | CNum:
    _standing()
    if isinstance(term, IntLit) or (isinstance(term, Var) and term.name == "i"):
        return eval_cnum(term)
    if isinstance(term, App):
        if term.op in {"pauli", "sigma"}:
            if len(term.args) != 1:
                raise NotExact("pauli takes a label")
            return pauli(_name(term.args[0]))
        if term.op == "ket":
            if len(term.args) != 1:
                raise NotExact("ket takes a label")
            return ket(_name(term.args[0]))
        if term.op == "bra":
            if len(term.args) != 1:
                raise NotExact("bra takes a label")
            return cmatrix_dagger(ket(_name(term.args[0])))
        if term.op == "dagger":
            if len(term.args) != 1:
                raise NotExact("dagger takes a matrix")
            return cmatrix_dagger(eval_hilbert_matrix(term.args[0]))
        if term.op in {"commutator", "comm"}:
            if len(term.args) != 2:
                raise NotExact("a commutator takes two matrices")
            return commutator(eval_hilbert_matrix(term.args[0]), eval_hilbert_matrix(term.args[1]))
        if term.op == "tensor":
            if len(term.args) != 2:
                raise NotExact("a tensor product takes two matrices")
            return tensor(eval_hilbert_matrix(term.args[0]), eval_hilbert_matrix(term.args[1]))
        if term.op == "gramschmidt":
            if len(term.args) != 1:
                raise NotExact("gramschmidt takes a matrix of column vectors")
            source = eval_hilbert_matrix(term.args[0])
            vectors = tuple(
                vector_from_entries(tuple(source.rows[i][j] for i in range(source.nrows)))
                for j in range(source.ncols)
            )
            return gram_schmidt(vectors)
        if term.op == "spectral":
            if len(term.args) != 1:
                raise NotExact("spectral takes a Hermitian matrix")
            u, _diag = spectral_hermitian(eval_hilbert_matrix(term.args[0]))
            return u
        if term.op == "eigendiag":
            if len(term.args) != 1:
                raise NotExact("eigendiag takes a Hermitian matrix")
            _u, diag = spectral_hermitian(eval_hilbert_matrix(term.args[0]))
            return diag
        if term.op in {"inner", "braket", "trace", "det"}:
            return eval_cnum(term)
        if term.op in {"inv", "inverse"}:
            if len(term.args) != 1:
                raise NotExact("an inverse takes a matrix")
            return cmatrix_inv(eval_hilbert_matrix(term.args[0]))
        if term.op in {"hermitian", "unitary"}:
            if len(term.args) != 1:
                raise NotExact(f"{term.op} takes a matrix")
            matrix = eval_hilbert_matrix(term.args[0])
            if term.op == "hermitian":
                return c_one() if is_hermitian(matrix) else c_zero()
            return c_one() if is_unitary(matrix) else c_zero()
        if term.op in {"add", "sub", "mul", "div"} and len(term.args) == 2:
            left, right = _eval(term.args[0]), _eval(term.args[1])
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
                return eval_cnum(term)
        if term.op == "pow" and len(term.args) == 2 and isinstance(term.args[1], IntLit):
            base = _eval(term.args[0])
            if isinstance(base, CMatrix):
                return _matrix_power(base, term.args[1].n)
            if isinstance(base, CNum):
                return eval_cnum(term)
        if term.op == "sqrt" and len(term.args) == 1:
            return eval_cnum(term)
        if term.op == "neg" and len(term.args) == 1:
            value = _eval(term.args[0])
            if isinstance(value, CMatrix):
                return cmatrix_neg(value)
            return c_neg(value)
        if term.op == "matrix":
            return _matrix_of(term)
        if term.op == "row":
            entries = tuple(eval_cnum(arg) for arg in term.args)
            return CMatrix((entries,))
    raise NotExact("this term is not a Hilbert-space matrix, vector, or scalar")


def has_matrix_shape(term: Term) -> bool:
    if isinstance(term, App):
        if term.op in {"matrix", "row"}:
            return True
        return any(has_matrix_shape(arg) for arg in term.args)
    return False


def _matrix_of(term: App) -> CMatrix:
    rows = []
    for arg in term.args:
        if isinstance(arg, App) and arg.op in {"row", "matrix"}:
            rows.append(tuple(eval_cnum(item) for item in arg.args))
        else:
            rows.append((eval_cnum(arg),))
    return CMatrix(tuple(rows))


def eval_hilbert_result(term: Term):
    value = _eval(term)
    if isinstance(value, CMatrix):
        return HilbTheorem(value, term, _matrix_detail(term, value))
    if isinstance(value, CNum):
        ratio = c_as_ratio(value)
        if ratio is not None:
            return rat_normalize(ratio.num, ratio.den)
        return ScalarTheorem(value, term, _scalar_detail(term, value))
    raise NotExact("this term is not a Hilbert-space matrix, vector, or scalar")


def _matrix_detail(term: Term, value: CMatrix) -> tuple[str, ...]:
    lines = [
        "Entries lie in Q(i) or Q(√d, i). An inverse is kept only when it multiplies back to 1.",
        "The inner product is ⟨u, v⟩ = u† v, conjugate-linear in the first argument.",
        "Gram–Schmidt is kept only when the result is orthonormal. Hermitian means A† = A; unitary means A† A = A A† = I.",
        "The Pauli matrices satisfy [σ_i, σ_j] = 2 i ε_ijk σ_k, checked exactly.",
    ]
    if isinstance(term, App) and term.op == "spectral":
        lines.append("A 2×2 Hermitian spectral decomposition is kept only when H = U D U† with U unitary and D real diagonal.")
    if isinstance(term, App) and term.op == "ket":
        lines.append("A computational or spin-1/2 ket is a unit vector; |+⟩ and |−⟩ are eigenvectors of σ_x.")
    if is_hermitian(value):
        lines.append("This matrix is Hermitian.")
    if is_unitary(value):
        lines.append("This matrix is unitary.")
    return tuple(lines)


def _scalar_detail(term: Term, value: CNum) -> tuple[str, ...]:
    return (
        "This scalar lies in Q(i) or Q(√d, i).",
        "The inner product is conjugate-symmetric, linear in the second argument, and positive definite, checked exactly.",
    )


def hilbert_value_rule(origin: Term, result: object, prelude: tuple[str, ...] = ()) -> Rule:
    title_left = pretty(origin)
    if isinstance(result, RatTheorem):
        from pgi.math.rational import ratio_rule

        return ratio_rule(origin, result, prelude)
    if isinstance(result, ScalarTheorem):
        shown = show_cnum(result.value)
        return Rule(
            id=f"math.cnum.{shown}",
            layer="base",
            stage="quantity",
            title=f"{title_left} = {shown}",
            produces=f"cnum({shown})",
            detail_lines=(*prelude, *result.detail),
        )
    if isinstance(result, HilbTheorem):
        shown = show_cmatrix(result.value)
        return Rule(
            id=f"math.cmatrix.{shown}",
            layer="base",
            stage="quantity",
            title=f"{title_left} = {shown}",
            produces=f"cmatrix({shown})",
            detail_lines=(*prelude, *result.detail),
        )
    raise KernelError("this Hilbert-space result has no claim")


def hilbert_equality_rules(
    left: Term,
    right: Term,
    left_value: object,
    right_value: object,
    prelude: tuple[str, ...] = (),
) -> tuple[Rule, ...]:
    title = f"{pretty(left)} = {pretty(right)}"
    if _hilbert_eq(left_value, right_value):
        return (
            Rule(
                id="math.hilbert.eq",
                layer="base",
                stage="quantity",
                title=title,
                produces=f"identity({title})",
                detail_lines=(*prelude, "The two sides are the same complex matrix or scalar."),
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


def _hilbert_eq(left: object, right: object) -> bool:
    left_m, right_m = _as_cmatrix(left), _as_cmatrix(right)
    if left_m is not None and right_m is not None:
        return cmatrix_eq(left_m, right_m)
    left_s, right_s = _as_cnum(left), _as_cnum(right)
    if left_s is not None and right_s is not None:
        return c_eq(left_s, right_s)
    return False


def _as_cmatrix(value: object) -> CMatrix | None:
    if isinstance(value, HilbTheorem):
        return value.value
    if isinstance(value, CMatrix):
        return value
    return None


def _as_cnum(value: object) -> CNum | None:
    if isinstance(value, ScalarTheorem):
        return value.value
    if isinstance(value, CNum):
        return value
    if isinstance(value, RatTheorem):
        return c_from_ratio(value.value)
    return None


def side_as_hilbert(term: Term) -> object:
    if has_hilbert(term) or has_matrix_shape(term):
        return eval_hilbert_result(term)
    # A closed rational or integer on the other side of an equation.
    try:
        return eval_hilbert_result(term)
    except NotExact:
        from pgi.math.rational import eval_rat

        return eval_rat(term)

_standing()
