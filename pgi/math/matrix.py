"""Exact matrices over the rationals.

Entries are reduced fractions. Addition, multiplication, transpose,
determinant, rank, and inverse use the rational and integer kernels.
A determinant is kept only when Bareiss elimination agrees with a
cofactor expansion (the cofactor check runs through degree five).
A rank is kept only when a pivot minor has nonzero determinant and
every other row is the corresponding exact linear combination of the
pivot rows. An inverse is kept only when both products with the
source are the identity.

Isabelle HOL-Analysis `Determinants.thy` and Lean mathlib `Matrix.det`
are the named determinant laws. Lean `Matrix.mul_nonsing_inv` and
`Matrix.nonsing_inv_mul` are the two-sided inverse identities. A
singular matrix has no inverse here; the kernel does not invent one.
A non-square determinant stays open. An entry that is not an exact
rational stays open.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import gcd, lcm

from pgi.math.kernel import KernelError, NotExact
from pgi.math.rational import Ratio, RatTheorem, eval_rat, rat_normalize
from pgi.math.syntax import App, IntLit, Term, pretty
from pgi.model import Rule


MATRIX_LIMIT = 16
_COFACTOR_LIMIT = 5
_ZERO = Ratio(0, 1)
_ONE = Ratio(1, 1)


@dataclass(frozen=True)
class Matrix:
    rows: tuple[tuple[Ratio, ...], ...]

    def __post_init__(self) -> None:
        if not self.rows or not self.rows[0]:
            raise KernelError("a matrix needs a row and a column")
        width = len(self.rows[0])
        if any(len(row) != width for row in self.rows):
            raise KernelError("matrix rows must have the same length")
        for row in self.rows:
            for entry in row:
                if entry.den <= 0 or gcd(abs(entry.num), entry.den) != 1:
                    raise KernelError("matrix entries must be reduced positive-denominator rationals")

    @property
    def nrows(self) -> int:
        return len(self.rows)

    @property
    def ncols(self) -> int:
        return len(self.rows[0])

    @property
    def square(self) -> bool:
        return self.nrows == self.ncols


@dataclass(frozen=True)
class MatTheorem:
    value: Matrix
    rule: str
    premises: tuple[MatTheorem, ...] = ()
    scalar: tuple[Ratio, ...] = ()
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _mat_justified(self):
            raise KernelError(f"{self.rule} does not justify {show_matrix(self.value)}")


@dataclass(frozen=True)
class DetTheorem:
    value: Ratio
    source: Matrix
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _det_justified(self):
            raise KernelError(f"Matrix.det does not justify {show_ratio(self.value)}")


@dataclass(frozen=True)
class RankTheorem:
    value: int
    source: Matrix
    pivot_rows: tuple[int, ...]
    pivot_cols: tuple[int, ...]
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _rank_justified(self):
            raise KernelError(f"Matrix.rank does not justify {self.value}")


@dataclass(frozen=True)
class InvTheorem:
    value: Matrix
    source: Matrix
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _inv_justified(self):
            raise KernelError("Matrix.inv does not multiply back to the identity")


def show_ratio(value: Ratio) -> str:
    if value.den == 1:
        return str(value.num)
    return f"{value.num}/{value.den}"


def show_matrix(matrix: Matrix) -> str:
    rows = []
    for row in matrix.rows:
        inner = ", ".join(show_ratio(entry) for entry in row)
        rows.append(f"[{inner}]")
    return "[" + ", ".join(rows) + "]"


def identity_matrix(size: int) -> Matrix:
    if size <= 0:
        raise KernelError("the identity needs a positive size")
    return Matrix(
        tuple(tuple(_ONE if i == j else _ZERO for j in range(size)) for i in range(size))
    )


def same_matrix(left: Matrix, right: Matrix) -> bool:
    return left.rows == right.rows


def matrix_add(left: MatTheorem, right: MatTheorem) -> MatTheorem:
    if left.value.nrows != right.value.nrows or left.value.ncols != right.value.ncols:
        raise NotExact("these matrices do not add")
    rows = tuple(
        tuple(_add(a, b) for a, b in zip(left_row, right_row))
        for left_row, right_row in zip(left.value.rows, right.value.rows)
    )
    return MatTheorem(
        Matrix(rows),
        "Matrix.add",
        (left, right),
        detail=(
            "Entrywise addition of exact rationals.",
            "Lean Matrix.add. Isabelle entrywise addition on a finite matrix.",
        ),
    )


def matrix_sub(left: MatTheorem, right: MatTheorem) -> MatTheorem:
    return matrix_add(left, matrix_neg(right))


def matrix_neg(premise: MatTheorem) -> MatTheorem:
    rows = tuple(tuple(_neg(entry) for entry in row) for row in premise.value.rows)
    return MatTheorem(
        Matrix(rows),
        "Matrix.neg",
        (premise,),
        detail=("Entrywise negation of exact rationals.", "Lean Matrix.neg."),
    )


def matrix_mul(left: MatTheorem, right: MatTheorem) -> MatTheorem:
    if left.value.ncols != right.value.nrows:
        raise NotExact("these matrices do not multiply")
    rows = []
    for i in range(left.value.nrows):
        row = []
        for j in range(right.value.ncols):
            acc = _ZERO
            for k in range(left.value.ncols):
                acc = _add(acc, _mul(left.value.rows[i][k], right.value.rows[k][j]))
            row.append(acc)
        rows.append(tuple(row))
    return MatTheorem(
        Matrix(tuple(rows)),
        "Matrix.mul",
        (left, right),
        detail=(
            "The (i, j) entry is the exact dot product of row i with column j.",
            "Lean Matrix.mul. Isabelle matrix multiplication over a ring.",
        ),
    )


def matrix_smul(scalar: Ratio, premise: MatTheorem) -> MatTheorem:
    rows = tuple(tuple(_mul(scalar, entry) for entry in row) for row in premise.value.rows)
    return MatTheorem(
        Matrix(rows),
        "Matrix.smul",
        (premise,),
        scalar=(scalar,),
        detail=("Each entry is multiplied by the exact rational scalar.", "Lean Matrix.smul."),
    )


def matrix_transpose(premise: MatTheorem) -> MatTheorem:
    rows = tuple(
        tuple(premise.value.rows[i][j] for i in range(premise.value.nrows))
        for j in range(premise.value.ncols)
    )
    return MatTheorem(
        Matrix(rows),
        "Matrix.transpose",
        (premise,),
        detail=("Lean Matrix.transpose. Isabelle transpose of a finite matrix.",),
    )


def matrix_of(matrix: Matrix) -> MatTheorem:
    return MatTheorem(
        matrix,
        "Matrix.of",
        detail=("Each entry is a reduced exact rational.",),
    )


def matrix_det(source: Matrix) -> DetTheorem:
    if not source.square:
        raise NotExact("a non-square matrix has no determinant here")
    _check_size(source)
    value, lines = _determinant(source)
    return DetTheorem(
        value,
        source,
        (
            *lines,
            "Isabelle HOL-Analysis Determinants.thy: det of a square matrix.",
            "Lean mathlib Matrix.det.",
            "Bareiss 1968: fraction-free exact elimination, after clearing denominators.",
        ),
    )


def matrix_rank(source: Matrix) -> RankTheorem:
    _check_size(source)
    rank, pivot_rows, pivot_cols, lines = _rank_certificate(source)
    return RankTheorem(
        rank,
        source,
        pivot_rows,
        pivot_cols,
        (
            *lines,
            "The rank is the number of exact rational pivots.",
            "A pivot minor has a nonzero determinant, and every other row is the corresponding linear combination of the pivot rows.",
            "Lean mathlib Matrix.rank.",
        ),
    )


def matrix_inv(source: Matrix) -> InvTheorem:
    if not source.square:
        raise NotExact("a non-square matrix has no inverse here")
    _check_size(source)
    if _determinant(source)[0].num == 0:
        raise NotExact("a singular matrix has no inverse")
    inverse = _gauss_jordan_inv(source)
    if inverse is None:
        raise NotExact("a singular matrix has no inverse")
    return InvTheorem(
        inverse,
        source,
        (
            "The inverse is computed by exact Gauss–Jordan elimination over the rationals.",
            "It is kept only when both products are the identity.",
            "Lean Matrix.mul_nonsing_inv and Matrix.nonsing_inv_mul.",
            "Isabelle: a square matrix over a field is invertible exactly when its determinant is nonzero.",
        ),
    )


def eval_lin(term: Term):
    """Evaluate a closed term to a matrix or an exact rational."""

    value = _eval(term)
    if isinstance(value, Matrix):
        return matrix_of(value)
    if isinstance(value, Ratio):
        return rat_normalize(value.num, value.den)
    raise KernelError("this linear-algebra term did not close")


def _eval(term: Term) -> Matrix | Ratio:
    if isinstance(term, IntLit):
        return Ratio(term.n, 1)
    if not isinstance(term, App):
        raise NotExact("a free variable is not a matrix or a rational")
    if term.op == "row":
        return _as_matrix(term)
    if term.op == "matrix":
        return _as_matrix(term)
    if term.op in {"det", "rank", "inv", "inverse", "transpose", "charpoly", "eigenvalues"}:
        if len(term.args) != 1:
            raise NotExact(f"{term.op} takes one matrix")
        source = _as_matrix_value(_eval(term.args[0]))
        if term.op == "det":
            return matrix_det(source).value
        if term.op == "rank":
            return Ratio(matrix_rank(source).value, 1)
        if term.op in {"inv", "inverse"}:
            return matrix_inv(source).value
        if term.op == "transpose":
            return matrix_transpose(matrix_of(source)).value
        raise NotExact(f"{term.op} is not admitted in this slice")
    if term.op == "neg":
        if len(term.args) != 1:
            raise KernelError("neg")
        inner = _eval(term.args[0])
        if isinstance(inner, Matrix):
            return matrix_neg(matrix_of(inner)).value
        return _neg(inner)
    if term.op in {"add", "sub", "mul", "div"} and len(term.args) == 2:
        left = _eval(term.args[0])
        right = _eval(term.args[1])
        return _combine(term.op, left, right)
    # A rational field expression used as an entry or a scalar.
    try:
        return eval_rat(term).value
    except KernelError as exc:
        raise NotExact("a matrix entry that is not an exact rational stays outside") from exc


def _combine(op: str, left: Matrix | Ratio, right: Matrix | Ratio) -> Matrix | Ratio:
    if op == "add":
        if isinstance(left, Matrix) and isinstance(right, Matrix):
            return matrix_add(matrix_of(left), matrix_of(right)).value
        if isinstance(left, Ratio) and isinstance(right, Ratio):
            return _add(left, right)
        raise NotExact("these sides do not add")
    if op == "sub":
        if isinstance(left, Matrix) and isinstance(right, Matrix):
            return matrix_sub(matrix_of(left), matrix_of(right)).value
        if isinstance(left, Ratio) and isinstance(right, Ratio):
            return _sub(left, right)
        raise NotExact("these sides do not subtract")
    if op == "mul":
        if isinstance(left, Matrix) and isinstance(right, Matrix):
            return matrix_mul(matrix_of(left), matrix_of(right)).value
        if isinstance(left, Ratio) and isinstance(right, Matrix):
            return matrix_smul(left, matrix_of(right)).value
        if isinstance(left, Matrix) and isinstance(right, Ratio):
            return matrix_smul(right, matrix_of(left)).value
        if isinstance(left, Ratio) and isinstance(right, Ratio):
            return _mul(left, right)
        raise NotExact("these sides do not multiply")
    if op == "div":
        if isinstance(left, Matrix) and isinstance(right, Ratio):
            if right.num == 0:
                raise NotExact("division by zero")
            return matrix_smul(_inv(right), matrix_of(left)).value
        if isinstance(left, Ratio) and isinstance(right, Ratio):
            if right.num == 0:
                raise NotExact("division by zero")
            return _div(left, right)
        raise NotExact("these sides do not divide")
    raise KernelError(op)


def _as_matrix_value(value: Matrix | Ratio) -> Matrix:
    if isinstance(value, Matrix):
        return value
    raise NotExact("this operation needs a matrix")


def _as_matrix(term: Term) -> Matrix:
    if not isinstance(term, App) or term.op not in {"matrix", "row"}:
        if isinstance(term, App) and term.op in {"inv", "inverse", "transpose", "add", "sub", "mul", "neg", "smul", "div"}:
            value = _eval(term)
            if isinstance(value, Matrix):
                return value
        raise NotExact("this term is not a matrix")
    if term.op == "row":
        entries = tuple(_eval_entry(arg) for arg in term.args)
        return Matrix((entries,))
    rows = []
    for arg in term.args:
        if isinstance(arg, App) and arg.op == "row":
            rows.append(tuple(_eval_entry(item) for item in arg.args))
            continue
        raise NotExact("a matrix is a list of rows")
    if not rows or not rows[0] or any(len(row) != len(rows[0]) for row in rows):
        raise NotExact("matrix rows must have the same length")
    matrix = Matrix(tuple(rows))
    _check_size(matrix)
    return matrix


def _eval_entry(term: Term) -> Ratio:
    value = _eval(term)
    if isinstance(value, Ratio):
        return value
    raise NotExact("a matrix entry that is not an exact rational stays outside")


def _check_size(matrix: Matrix) -> None:
    if matrix.nrows > MATRIX_LIMIT or matrix.ncols > MATRIX_LIMIT:
        raise NotExact(f"a matrix larger than {MATRIX_LIMIT} stays outside")


def _determinant(matrix: Matrix) -> tuple[Ratio, tuple[str, ...]]:
    bareiss = _bareiss_det(matrix)
    lines = [
        f"Bareiss determinant, after clearing denominators, is {show_ratio(bareiss)}.",
    ]
    if matrix.nrows <= _COFACTOR_LIMIT:
        cofactor = _cofactor_det(matrix)
        if cofactor != bareiss:
            raise KernelError("Bareiss and cofactor determinants disagreed")
        lines.append(f"The cofactor expansion agrees: {show_ratio(cofactor)}.")
    return bareiss, tuple(lines)


def _bareiss_det(matrix: Matrix) -> Ratio:
    n = matrix.nrows
    if n == 1:
        return matrix.rows[0][0]
    integer_rows, scale = _integer_rows(matrix)
    value = _bareiss_integer(integer_rows)
    return _div(Ratio(value, 1), Ratio(scale, 1))


def _integer_rows(matrix: Matrix) -> tuple[list[list[int]], int]:
    rows: list[list[int]] = []
    scale = 1
    for row in matrix.rows:
        row_scale = 1
        for entry in row:
            row_scale = lcm(row_scale, entry.den)
        scale *= row_scale
        rows.append([entry.num * (row_scale // entry.den) for entry in row])
    return rows, scale


def _bareiss_integer(rows: list[list[int]]) -> int:
    n = len(rows)
    work = [row[:] for row in rows]
    sign = 1
    previous = 1
    for k in range(n - 1):
        pivot_row = k
        while pivot_row < n and work[pivot_row][k] == 0:
            pivot_row += 1
        if pivot_row == n:
            return 0
        if pivot_row != k:
            work[k], work[pivot_row] = work[pivot_row], work[k]
            sign = -sign
        pivot = work[k][k]
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                numerator = pivot * work[i][j] - work[i][k] * work[k][j]
                if previous == 0 or numerator % previous != 0:
                    raise KernelError("Bareiss division was not exact")
                work[i][j] = numerator // previous
            work[i][k] = 0
        previous = pivot
    return sign * work[n - 1][n - 1]


def _cofactor_det(matrix: Matrix) -> Ratio:
    n = matrix.nrows
    if n == 1:
        return matrix.rows[0][0]
    if n == 2:
        a, b = matrix.rows[0]
        c, d = matrix.rows[1]
        return _sub(_mul(a, d), _mul(b, c))
    total = _ZERO
    for index, entry in enumerate(matrix.rows[0]):
        if entry.num == 0:
            continue
        term = _mul(entry, _cofactor_det(_minor(matrix, 0, index)))
        if index % 2:
            term = _neg(term)
        total = _add(total, term)
    return total


def _minor(matrix: Matrix, drop_row: int, drop_col: int) -> Matrix:
    rows = tuple(
        tuple(entry for col, entry in enumerate(row) if col != drop_col)
        for row_index, row in enumerate(matrix.rows)
        if row_index != drop_row
    )
    return Matrix(rows)


def _rank_certificate(matrix: Matrix) -> tuple[int, tuple[int, ...], tuple[int, ...], tuple[str, ...]]:
    work = [list(row) for row in matrix.rows]
    rows = list(range(matrix.nrows))
    pivot_cols: list[int] = []
    rank = 0
    for col in range(matrix.ncols):
        chosen = None
        for index in range(rank, matrix.nrows):
            if work[index][col].num != 0:
                chosen = index
                break
        if chosen is None:
            continue
        if chosen != rank:
            work[rank], work[chosen] = work[chosen], work[rank]
            rows[rank], rows[chosen] = rows[chosen], rows[rank]
        pivot = work[rank][col]
        scale = _inv(pivot)
        work[rank] = [_mul(scale, entry) for entry in work[rank]]
        for index in range(matrix.nrows):
            if index == rank or work[index][col].num == 0:
                continue
            factor = work[index][col]
            work[index] = [_sub(work[index][j], _mul(factor, work[rank][j])) for j in range(matrix.ncols)]
        pivot_cols.append(col)
        rank += 1
        if rank == matrix.nrows:
            break
    pivot_rows = tuple(rows[:rank])
    lines = (
        f"Exact rational elimination finds {rank} pivot(s).",
        f"Pivot rows {pivot_rows}, pivot columns {tuple(pivot_cols)}.",
    )
    return rank, pivot_rows, tuple(pivot_cols), lines


def _gauss_jordan_inv(matrix: Matrix) -> Matrix | None:
    n = matrix.nrows
    work = [list(row) + [_ONE if i == j else _ZERO for j in range(n)] for i, row in enumerate(matrix.rows)]
    for col in range(n):
        chosen = None
        for index in range(col, n):
            if work[index][col].num != 0:
                chosen = index
                break
        if chosen is None:
            return None
        if chosen != col:
            work[col], work[chosen] = work[chosen], work[col]
        scale = _inv(work[col][col])
        work[col] = [_mul(scale, entry) for entry in work[col]]
        for index in range(n):
            if index == col or work[index][col].num == 0:
                continue
            factor = work[index][col]
            work[index] = [_sub(entry, _mul(factor, work[col][j])) for j, entry in enumerate(work[index])]
    return Matrix(tuple(tuple(row[n:]) for row in work))


def _mat_justified(theorem: MatTheorem) -> bool:
    value = theorem.value
    rule = theorem.rule
    premises = theorem.premises
    if rule == "Matrix.of":
        return not premises and not theorem.scalar
    if rule == "Matrix.neg":
        if len(premises) != 1:
            return False
        source = premises[0].value
        expected = tuple(tuple(_neg(entry) for entry in row) for row in source.rows)
        return value.rows == expected
    if rule == "Matrix.transpose":
        if len(premises) != 1:
            return False
        source = premises[0].value
        expected = tuple(
            tuple(source.rows[i][j] for i in range(source.nrows)) for j in range(source.ncols)
        )
        return value.rows == expected
    if rule == "Matrix.smul":
        if len(premises) != 1 or len(theorem.scalar) != 1:
            return False
        scalar = theorem.scalar[0]
        expected = tuple(tuple(_mul(scalar, entry) for entry in row) for row in premises[0].value.rows)
        return value.rows == expected
    if rule == "Matrix.add":
        if len(premises) != 2:
            return False
        left, right = premises[0].value, premises[1].value
        if left.nrows != right.nrows or left.ncols != right.ncols:
            return False
        expected = tuple(
            tuple(_add(a, b) for a, b in zip(left_row, right_row))
            for left_row, right_row in zip(left.rows, right.rows)
        )
        return value.rows == expected
    if rule == "Matrix.mul":
        if len(premises) != 2:
            return False
        left, right = premises[0].value, premises[1].value
        if left.ncols != right.nrows or value.nrows != left.nrows or value.ncols != right.ncols:
            return False
        for i in range(left.nrows):
            for j in range(right.ncols):
                acc = _ZERO
                for k in range(left.ncols):
                    acc = _add(acc, _mul(left.rows[i][k], right.rows[k][j]))
                if value.rows[i][j] != acc:
                    return False
        return True
    return False


def _det_justified(theorem: DetTheorem) -> bool:
    if not theorem.source.square:
        return False
    bareiss = _bareiss_det(theorem.source)
    if theorem.value != bareiss:
        return False
    if theorem.source.nrows <= _COFACTOR_LIMIT:
        return theorem.value == _cofactor_det(theorem.source)
    return True


def _rank_justified(theorem: RankTheorem) -> bool:
    matrix = theorem.source
    rank = theorem.value
    pivot_rows = theorem.pivot_rows
    pivot_cols = theorem.pivot_cols
    if rank < 0 or rank != len(pivot_rows) or rank != len(pivot_cols):
        return False
    if len(set(pivot_rows)) != rank or len(set(pivot_cols)) != rank:
        return False
    if any(row < 0 or row >= matrix.nrows for row in pivot_rows):
        return False
    if any(col < 0 or col >= matrix.ncols for col in pivot_cols):
        return False
    if rank == 0:
        return all(entry.num == 0 for row in matrix.rows for entry in row)
    minor = _submatrix(matrix, pivot_rows, pivot_cols)
    if _bareiss_det(minor).num == 0:
        return False
    inverse = _gauss_jordan_inv(minor)
    if inverse is None:
        return False
    leftover = [index for index in range(matrix.nrows) if index not in set(pivot_rows)]
    pivot_block = [matrix.rows[row] for row in pivot_rows]
    for index in leftover:
        coords = tuple(matrix.rows[index][col] for col in pivot_cols)
        coeffs = tuple(
            _dot(coords, tuple(inverse.rows[j][i] for j in range(rank))) for i in range(rank)
        )
        # coeffs is a row: coords * inverse, since we solve coeffs * minor = coords.
        # Wait: we want coeffs such that sum_k coeffs[k] * pivot_block[k] = row.
        # On pivot columns, coeffs * minor = coords, so coeffs = coords * minor^{-1}.
        # inverse.rows[j][i] is (j,i) of inv. coords * inv has entry i = sum_j coords[j] * inv[j][i].
        rebuilt = tuple(_combo(coeffs, pivot_block, col) for col in range(matrix.ncols))
        if rebuilt != matrix.rows[index]:
            return False
    return True


def _inv_justified(theorem: InvTheorem) -> bool:
    source = theorem.source
    inverse = theorem.value
    if not source.square or not inverse.square or source.nrows != inverse.nrows:
        return False
    if _bareiss_det(source).num == 0:
        return False
    identity = identity_matrix(source.nrows)
    left = matrix_mul(matrix_of(source), matrix_of(inverse)).value
    right = matrix_mul(matrix_of(inverse), matrix_of(source)).value
    return same_matrix(left, identity) and same_matrix(right, identity)


def _submatrix(matrix: Matrix, rows: tuple[int, ...], cols: tuple[int, ...]) -> Matrix:
    return Matrix(tuple(tuple(matrix.rows[row][col] for col in cols) for row in rows))


def _dot(left: tuple[Ratio, ...], right: tuple[Ratio, ...]) -> Ratio:
    acc = _ZERO
    for a, b in zip(left, right):
        acc = _add(acc, _mul(a, b))
    return acc


def _combo(coeffs: tuple[Ratio, ...], rows: list[tuple[Ratio, ...]], col: int) -> Ratio:
    acc = _ZERO
    for coeff, row in zip(coeffs, rows):
        acc = _add(acc, _mul(coeff, row[col]))
    return acc


def _add(left: Ratio, right: Ratio) -> Ratio:
    return rat_normalize(left.num * right.den + right.num * left.den, left.den * right.den).value


def _sub(left: Ratio, right: Ratio) -> Ratio:
    return rat_normalize(left.num * right.den - right.num * left.den, left.den * right.den).value


def _mul(left: Ratio, right: Ratio) -> Ratio:
    return rat_normalize(left.num * right.num, left.den * right.den).value


def _neg(value: Ratio) -> Ratio:
    return Ratio(-value.num, value.den)


def _inv(value: Ratio) -> Ratio:
    if value.num == 0:
        raise NotExact("division by zero")
    return rat_normalize(value.den, value.num).value


def _div(left: Ratio, right: Ratio) -> Ratio:
    if right.num == 0:
        raise NotExact("division by zero")
    return rat_normalize(left.num * right.den, left.den * right.num).value


def lin_trace(result: MatTheorem | DetTheorem | RankTheorem | InvTheorem | RatTheorem) -> tuple[str, ...]:
    if isinstance(result, RatTheorem):
        from pgi.math.rational import rat_trace

        return rat_trace(result)
    if isinstance(result, DetTheorem):
        return (
            f"Matrix.det: det({show_matrix(result.source)}) = {show_ratio(result.value)}",
            *result.detail,
        )
    if isinstance(result, RankTheorem):
        return (
            f"Matrix.rank: rank({show_matrix(result.source)}) = {result.value}",
            *result.detail,
        )
    if isinstance(result, InvTheorem):
        return (
            f"Matrix.inv: inv({show_matrix(result.source)}) = {show_matrix(result.value)}",
            *result.detail,
            f"The product either way is {show_matrix(identity_matrix(result.source.nrows))}.",
        )
    lines: list[str] = []
    for premise in result.premises:
        lines.extend(lin_trace(premise))
    lines.append(f"{result.rule}: {show_matrix(result.value)}")
    lines.extend(result.detail)
    return tuple(lines)


def lin_value_rule(origin: Term, result: object, prelude: tuple[str, ...] = ()) -> Rule:
    title_left = pretty(origin)
    if isinstance(result, RatTheorem):
        from pgi.math.rational import ratio_rule

        return ratio_rule(origin, result, prelude)
    if isinstance(result, DetTheorem):
        shown = show_ratio(result.value)
        lines = (*prelude, *lin_trace(result))
        if result.value.den == 1:
            return Rule(
                id=f"math.value.{result.value.num}",
                layer="base",
                stage="quantity",
                title=f"{title_left} = {shown}",
                produces=f"value({result.value.num})",
                detail_lines=lines,
            )
        return Rule(
            id=f"math.ratio.{result.value.num}.{result.value.den}",
            layer="base",
            stage="quantity",
            title=f"{title_left} = {shown}",
            produces=f"ratio({result.value.num},{result.value.den})",
            detail_lines=lines,
        )
    if isinstance(result, RankTheorem):
        lines = (*prelude, *lin_trace(result))
        return Rule(
            id=f"math.value.{result.value}",
            layer="base",
            stage="quantity",
            title=f"{title_left} = {result.value}",
            produces=f"value({result.value})",
            detail_lines=lines,
        )
    if isinstance(result, (InvTheorem, MatTheorem)):
        matrix = result.value
        shown = show_matrix(matrix)
        lines = (*prelude, *lin_trace(result))
        return Rule(
            id=f"math.matrix.{shown}",
            layer="base",
            stage="quantity",
            title=f"{title_left} = {shown}",
            produces=f"matrix({shown})",
            detail_lines=lines,
        )
    raise KernelError("unrecognized linear-algebra result")


def lin_equality_rules(
    left: Term,
    right: Term,
    left_value: object,
    right_value: object,
    prelude: tuple[str, ...] = (),
) -> tuple[Rule, ...]:
    title = f"{pretty(left)} = {pretty(right)}"
    left_matrix = _value_matrix(left_value)
    right_matrix = _value_matrix(right_value)
    left_ratio = _value_ratio(left_value)
    right_ratio = _value_ratio(right_value)
    lines = (*prelude, *lin_trace(left_value), *lin_trace(right_value))
    if left_matrix is not None and right_matrix is not None:
        if same_matrix(left_matrix, right_matrix):
            return (
                Rule(
                    id="math.matrix.eq",
                    layer="base",
                    stage="quantity",
                    title=title,
                    produces=f"identity({title})",
                    detail_lines=(*lines, "The two matrices have the same reduced entries."),
                ),
            )
        return (_note(f"{title} is not a theorem"),)
    if left_ratio is not None and right_ratio is not None:
        if left_ratio == right_ratio:
            return (
                Rule(
                    id="math.matrix.eq",
                    layer="base",
                    stage="quantity",
                    title=title,
                    produces=f"identity({title})",
                    detail_lines=(*lines, "The two exact rationals are the same."),
                ),
            )
        return (_note(f"{title} is not a theorem"),)
    return (_note(f"{title} is not a theorem"),)


def _value_matrix(result: object) -> Matrix | None:
    if isinstance(result, (MatTheorem, InvTheorem)):
        return result.value
    return None


def _value_ratio(result: object) -> Ratio | None:
    if isinstance(result, RatTheorem):
        return result.value
    if isinstance(result, DetTheorem):
        return result.value
    if isinstance(result, RankTheorem):
        return Ratio(result.value, 1)
    return None


def eval_lin_result(term: Term) -> MatTheorem | DetTheorem | RankTheorem | InvTheorem | RatTheorem:
    """Evaluate to the most specific theorem, not a reduced wrapper."""

    if isinstance(term, App):
        if term.op == "det" and len(term.args) == 1:
            return matrix_det(_as_matrix_value(_eval(term.args[0])))
        if term.op == "rank" and len(term.args) == 1:
            return matrix_rank(_as_matrix_value(_eval(term.args[0])))
        if term.op in {"inv", "inverse"} and len(term.args) == 1:
            return matrix_inv(_as_matrix_value(_eval(term.args[0])))
        if term.op == "transpose" and len(term.args) == 1:
            return matrix_transpose(matrix_of(_as_matrix_value(_eval(term.args[0]))))
        if term.op in {"matrix", "row"}:
            return matrix_of(_as_matrix(term))
        if term.op in {"add", "sub", "mul", "div", "neg"}:
            value = _eval(term)
            if isinstance(value, Matrix):
                return matrix_of(value)
            return rat_normalize(value.num, value.den)
    value = _eval(term)
    if isinstance(value, Matrix):
        return matrix_of(value)
    return rat_normalize(value.num, value.den)


def _note(text: str) -> Rule:
    return Rule(
        id="math.open",
        layer="base",
        stage="check",
        title=text,
        produces=f"open({text})",
        detail_lines=(text,),
    )


def has_matrix(term: Term) -> bool:
    if isinstance(term, App):
        if term.op in {"matrix", "row", "det", "rank", "inv", "inverse", "transpose"}:
            return True
        return any(has_matrix(arg) for arg in term.args)
    return False
