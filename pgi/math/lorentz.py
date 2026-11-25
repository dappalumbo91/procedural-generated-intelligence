"""The Lorentz algebra so(3,1) and the Dirac Clifford algebra.

The Minkowski metric is η = diag(-1, 1, 1, 1), matching the mostly-plus
signature already used for Minkowski and Schwarzschild. A Lorentz boost
with a rational velocity is kept only when 1 - v^2 is the square of a
positive rational, so γ and γv are exact, and only when both Λ^T η Λ
and Λ η Λ^T equal η. The so(3,1) generators satisfy the standard
brackets [J_i, J_j] = ε_ijk J_k, [K_i, K_j] = -ε_ijk J_k, and
[J_i, K_j] = ε_ijk K_k, and each generator preserves η infinitesimally:
X^T η + η X = 0.

The Dirac matrices obey {γ^μ, γ^ν} = 2 η^{μν} I, checked on every pair.
The representation is the mostly-plus Weyl form: γ^0 = [[0, I], [-I, 0]]
and γ^i = [[0, σ_i], [σ_i, 0]]. Every identity is checked exactly, with
no approximation.
"""

from __future__ import annotations

from dataclasses import dataclass

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
    c_neg,
    c_one,
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
    cmatrix_identity,
    cmatrix_mul,
    cmatrix_neg,
    cmatrix_smul,
    cmatrix_sub,
    cmatrix_zero,
    commutator,
    eval_hilbert_result,
    has_hilbert,
    has_matrix_shape,
    pauli,
    show_cmatrix,
    side_as_hilbert,
)
from pgi.math.kernel import KernelError, NotExact
from pgi.model import Rule
from pgi.math.rational import Ratio, RatTheorem, eval_rat, rat_normalize
from pgi.math.syntax import App, IntLit, Term, Var, pretty


def _c(n: int) -> CNum:
    return c_from_int(n)


def _cr(value: Ratio) -> CNum:
    return c_from_ratio(value)


def _entry(rows: list[list[CNum]]) -> CMatrix:
    return CMatrix(tuple(tuple(row) for row in rows))


def _block(aa: CMatrix, ab: CMatrix, ba: CMatrix, bb: CMatrix) -> CMatrix:
    if not (aa.nrows == aa.ncols == ab.nrows == ba.ncols == 2):
        raise KernelError("a Dirac block must be 2×2")
    rows = []
    for i in range(2):
        rows.append(aa.rows[i] + ab.rows[i])
    for i in range(2):
        rows.append(ba.rows[i] + bb.rows[i])
    return CMatrix(tuple(rows))


def cmatrix_transpose(value: CMatrix) -> CMatrix:
    return CMatrix(
        tuple(tuple(value.rows[j][i] for j in range(value.nrows)) for i in range(value.ncols))
    )


def minkowski_eta() -> CMatrix:
    z, o, n = c_zero(), c_one(), _c(-1)
    return _entry(
        [
            [n, z, z, z],
            [z, o, z, z],
            [z, z, o, z],
            [z, z, z, o],
        ]
    )


def gamma(index: int) -> CMatrix:
    if index not in {0, 1, 2, 3}:
        raise NotExact("a Dirac matrix is gamma(0), gamma(1), gamma(2), or gamma(3)")
    ident = cmatrix_identity(2)
    zero = cmatrix_zero(2, 2)
    if index == 0:
        return _block(zero, ident, cmatrix_neg(ident), zero)
    sigma = pauli({1: "x", 2: "y", 3: "z"}[index])
    return _block(zero, sigma, sigma, zero)


def anticommutator(left: CMatrix, right: CMatrix) -> CMatrix:
    return cmatrix_add(cmatrix_mul(left, right), cmatrix_mul(right, left))


def _preserves_eta(lorentz: CMatrix) -> bool:
    eta = minkowski_eta()
    left = cmatrix_mul(cmatrix_mul(cmatrix_transpose(lorentz), eta), lorentz)
    right = cmatrix_mul(cmatrix_mul(lorentz, eta), cmatrix_transpose(lorentz))
    return cmatrix_eq(left, eta) and cmatrix_eq(right, eta)


def _isqrt(n: int) -> int | None:
    if n < 0:
        return None
    if n == 0:
        return 0
    x = n
    while True:
        y = (x + n // x) // 2
        if y >= x:
            return x if x * x == n else None
        x = y


def _ratio_sqrt(value: Ratio) -> Ratio | None:
    if value.den <= 0 or value.num < 0:
        return None
    root_num = _isqrt(value.num)
    root_den = _isqrt(value.den)
    if root_num is None or root_den is None:
        return None
    return Ratio(root_num, root_den)


def _ratio_of(term: Term) -> Ratio:
    try:
        return eval_rat(term).value
    except NotExact:
        value = _eval(term)
        if isinstance(value, CNum):
            ratio = c_as_ratio(value)
            if ratio is not None:
                return ratio
        raise NotExact("a boost velocity must be a rational") from None


def _boost_factors(velocity: Ratio) -> tuple[Ratio, Ratio]:
    # γ = 1 / sqrt(1 - v^2), γv = v γ, kept only when both are rational.
    one = Ratio(1, 1)
    vsq = Ratio(velocity.num * velocity.num, velocity.den * velocity.den)
    residual_num = vsq.den - vsq.num
    residual_den = vsq.den
    # reduce later via Ratio if needed; compute 1 - v^2
    from math import gcd

    g = gcd(residual_num, residual_den)
    residual = Ratio(residual_num // g, residual_den // g)
    if residual.num <= 0:
        raise NotExact("a boost velocity must satisfy |v| < 1")
    root = _ratio_sqrt(residual)
    if root is None:
        raise NotExact("a boost is kept only when 1 - v^2 is the square of a rational")
    # γ = 1 / root
    gamma = Ratio(root.den, root.num)
    gamma_v = Ratio(velocity.num * gamma.num, velocity.den * gamma.den)
    g = gcd(gamma_v.num, gamma_v.den)
    gamma_v = Ratio(gamma_v.num // g, gamma_v.den // g)
    if gamma_v.den < 0:
        gamma_v = Ratio(-gamma_v.num, -gamma_v.den)
    return gamma, gamma_v


def boost(axis: str, velocity: Ratio) -> CMatrix:
    axis = _axis(axis)
    gamma, gamma_v = _boost_factors(velocity)
    z, o = c_zero(), c_one()
    ch, sh = _cr(gamma), _cr(gamma_v)
    nsh = c_neg(sh)
    if axis == "x":
        value = _entry(
            [
                [ch, nsh, z, z],
                [nsh, ch, z, z],
                [z, z, o, z],
                [z, z, z, o],
            ]
        )
    elif axis == "y":
        value = _entry(
            [
                [ch, z, nsh, z],
                [z, o, z, z],
                [nsh, z, ch, z],
                [z, z, z, o],
            ]
        )
    else:
        value = _entry(
            [
                [ch, z, z, nsh],
                [z, o, z, z],
                [z, z, o, z],
                [nsh, z, z, ch],
            ]
        )
    if not _preserves_eta(value):
        raise KernelError("this boost does not preserve the Minkowski metric")
    return value


def _axis(name: str) -> str:
    if name in {"x", "1"}:
        return "x"
    if name in {"y", "2"}:
        return "y"
    if name in {"z", "3"}:
        return "z"
    raise NotExact("a Lorentz axis is x, y, or z")


def _so31_label(name: str) -> str:
    aliases = {
        "jx": "jx",
        "j1": "jx",
        "jy": "jy",
        "j2": "jy",
        "jz": "jz",
        "j3": "jz",
        "kx": "kx",
        "k1": "kx",
        "ky": "ky",
        "k2": "ky",
        "kz": "kz",
        "k3": "kz",
    }
    if name not in aliases:
        raise NotExact("an so(3,1) generator is jx, jy, jz, kx, ky, or kz")
    return aliases[name]


def so31(name: str) -> CMatrix:
    z, o, n = c_zero(), c_one(), _c(-1)
    label = _so31_label(name)
    # Spatial rotations: (J_i)^j_k = -ε_ijk. Boosts: (K_i)^0_i = (K_i)^i_0 = 1.
    if label == "jx":
        value = _entry(
            [
                [z, z, z, z],
                [z, z, z, z],
                [z, z, z, n],
                [z, z, o, z],
            ]
        )
    elif label == "jy":
        value = _entry(
            [
                [z, z, z, z],
                [z, z, z, o],
                [z, z, z, z],
                [z, n, z, z],
            ]
        )
    elif label == "jz":
        value = _entry(
            [
                [z, z, z, z],
                [z, z, n, z],
                [z, o, z, z],
                [z, z, z, z],
            ]
        )
    elif label == "kx":
        value = _entry(
            [
                [z, o, z, z],
                [o, z, z, z],
                [z, z, z, z],
                [z, z, z, z],
            ]
        )
    elif label == "ky":
        value = _entry(
            [
                [z, z, o, z],
                [z, z, z, z],
                [o, z, z, z],
                [z, z, z, z],
            ]
        )
    else:
        value = _entry(
            [
                [z, z, z, o],
                [z, z, z, z],
                [z, z, z, z],
                [o, z, z, z],
            ]
        )
    eta = minkowski_eta()
    form = cmatrix_add(cmatrix_mul(cmatrix_transpose(value), eta), cmatrix_mul(eta, value))
    if not cmatrix_eq(form, cmatrix_zero(4, 4)):
        raise KernelError(f"so31({label}) does not preserve the Minkowski metric infinitesimally")
    return value


def _epsilon(i: str, j: str, k: str) -> int:
    order = (i, j, k)
    even = {("x", "y", "z"), ("y", "z", "x"), ("z", "x", "y")}
    odd = {("x", "z", "y"), ("z", "y", "x"), ("y", "x", "z")}
    if order in even:
        return 1
    if order in odd:
        return -1
    return 0


def _axes() -> tuple[str, ...]:
    return ("x", "y", "z")


def _check_clifford() -> None:
    eta = minkowski_eta()
    ident = cmatrix_identity(4)
    for mu in range(4):
        for nu in range(4):
            left = anticommutator(gamma(mu), gamma(nu))
            coeff = eta.rows[mu][nu]
            right = cmatrix_smul(c_mul(_c(2), coeff), ident)
            if not cmatrix_eq(left, right):
                raise KernelError(f"{{γ^{mu}, γ^{nu}}} is not 2 η^{{{mu}{nu}}} I")


def _check_so31() -> None:
    for i in _axes():
        for j in _axes():
            if i == j:
                if not cmatrix_eq(commutator(so31("j" + i), so31("j" + j)), cmatrix_zero(4, 4)):
                    raise KernelError("a so(3,1) rotation squared bracket must vanish")
                if not cmatrix_eq(commutator(so31("k" + i), so31("k" + j)), cmatrix_zero(4, 4)):
                    raise KernelError("a so(3,1) boost squared bracket must vanish")
                if not cmatrix_eq(commutator(so31("j" + i), so31("k" + j)), cmatrix_zero(4, 4)):
                    raise KernelError("[J_i, K_i] must vanish")
                continue
            k = ({"x", "y", "z"} - {i, j}).pop()
            sign = _epsilon(i, j, k)
            jj = commutator(so31("j" + i), so31("j" + j))
            expected_j = cmatrix_smul(_c(sign), so31("j" + k))
            if not cmatrix_eq(jj, expected_j):
                raise KernelError(f"[J_{i}, J_{j}] is not ε_{i}{j}{k} J_{k}")
            kk = commutator(so31("k" + i), so31("k" + j))
            expected_k = cmatrix_smul(_c(-sign), so31("j" + k))
            if not cmatrix_eq(kk, expected_k):
                raise KernelError(f"[K_{i}, K_{j}] is not -ε_{i}{j}{k} J_{k}")
            jk = commutator(so31("j" + i), so31("k" + j))
            expected_jk = cmatrix_smul(_c(sign), so31("k" + k))
            if not cmatrix_eq(jk, expected_jk):
                raise KernelError(f"[J_{i}, K_{j}] is not ε_{i}{j}{k} K_{k}")


_STANDING = False


def _standing() -> None:
    global _STANDING
    if _STANDING:
        return
    _check_clifford()
    _check_so31()
    # A sample rational boost is kept only when it multiplies back to η.
    sample = boost("x", Ratio(3, 5))
    if not _preserves_eta(sample):
        raise KernelError("the sample boost does not preserve η")
    _STANDING = True


def _name(term: Term) -> str:
    if isinstance(term, Var):
        return term.name
    if isinstance(term, IntLit):
        return str(term.n)
    raise NotExact("this name is not a label")


def _index(term: Term) -> int:
    name = _name(term)
    if name not in {"0", "1", "2", "3"}:
        raise NotExact("a Dirac index is 0, 1, 2, or 3")
    return int(name)


LORENTZ_OPS = frozenset({
    "eta",
    "gamma",
    "boost",
    "so31",
    "anticommutator",
    "acomm",
    "clifford",
    "so31algebra",
})


def _contains_op(term: Term, names: frozenset[str]) -> bool:
    if isinstance(term, Var) and term.name in names:
        return True
    if isinstance(term, App):
        if term.op in names:
            return True
        return any(_contains_op(arg, names) for arg in term.args)
    return False


def has_lorentz(term: Term) -> bool:
    return _contains_op(term, LORENTZ_OPS)


def _eval(term: Term):
    _standing()
    if isinstance(term, Var) and term.name == "eta":
        return minkowski_eta()
    if isinstance(term, IntLit) or (isinstance(term, Var) and term.name == "i"):
        from pgi.math.hilbert import eval_cnum

        return eval_cnum(term)
    if isinstance(term, App):
        if term.op == "eta":
            if term.args:
                raise NotExact("eta is the 4×4 Minkowski metric")
            return minkowski_eta()
        if term.op == "gamma":
            if len(term.args) != 1:
                raise NotExact("gamma takes an index 0, 1, 2, or 3")
            return gamma(_index(term.args[0]))
        if term.op == "boost":
            if len(term.args) != 2:
                raise NotExact("boost takes an axis and a rational velocity")
            return boost(_name(term.args[0]), _ratio_of(term.args[1]))
        if term.op == "so31":
            if len(term.args) != 1:
                raise NotExact("so31 takes a generator label")
            return so31(_name(term.args[0]))
        if term.op in {"anticommutator", "acomm"}:
            if len(term.args) != 2:
                raise NotExact("an anticommutator takes two matrices")
            return anticommutator(_as_matrix_term(term.args[0]), _as_matrix_term(term.args[1]))
        if term.op in {"commutator", "comm"}:
            if len(term.args) != 2:
                raise NotExact("a commutator takes two matrices")
            return commutator(_as_matrix_term(term.args[0]), _as_matrix_term(term.args[1]))
        if term.op == "clifford":
            if term.args:
                raise NotExact("clifford checks the Dirac algebra")
            _check_clifford()
            return c_zero()
        if term.op == "so31algebra":
            if term.args:
                raise NotExact("so31algebra checks the Lorentz brackets")
            _check_so31()
            return c_zero()
        if term.op == "transpose":
            if len(term.args) != 1:
                raise NotExact("transpose takes a matrix")
            return cmatrix_transpose(_as_matrix_term(term.args[0]))
        if term.op == "dagger":
            if len(term.args) != 1:
                raise NotExact("dagger takes a matrix")
            return cmatrix_dagger(_as_matrix_term(term.args[0]))
        if term.op == "neg" and len(term.args) == 1:
            value = _eval(term.args[0])
            if isinstance(value, CMatrix):
                return cmatrix_neg(value)
            if isinstance(value, CNum):
                return c_neg(value)
        if term.op in {"add", "sub", "mul", "div"} and len(term.args) == 2:
            left, right = _eval(term.args[0]), _eval(term.args[1])
            if term.op == "add":
                if isinstance(left, CMatrix) and isinstance(right, CMatrix):
                    return cmatrix_add(left, right)
                if isinstance(left, CNum) and isinstance(right, CNum):
                    return c_add(left, right)
            if term.op == "sub":
                if isinstance(left, CMatrix) and isinstance(right, CMatrix):
                    return cmatrix_sub(left, right)
                if isinstance(left, CNum) and isinstance(right, CNum):
                    from pgi.math.cnum import c_sub

                    return c_sub(left, right)
            if term.op == "mul":
                if isinstance(left, CMatrix) and isinstance(right, CMatrix):
                    return cmatrix_mul(left, right)
                if isinstance(left, CNum) and isinstance(right, CMatrix):
                    return cmatrix_smul(left, right)
                if isinstance(left, CMatrix) and isinstance(right, CNum):
                    return cmatrix_smul(right, left)
                if isinstance(left, CNum) and isinstance(right, CNum):
                    return c_mul(left, right)
            if term.op == "div" and isinstance(left, CNum) and isinstance(right, CNum):
                from pgi.math.cnum import c_div

                return c_div(left, right)
        if term.op == "matrix":
            from pgi.math.hilbert import eval_hilbert_matrix

            return eval_hilbert_matrix(term)
        if term.op == "pow" and len(term.args) == 2 and isinstance(term.args[1], IntLit):
            base = _eval(term.args[0])
            exp = term.args[1].n
            if isinstance(base, CMatrix):
                if exp < 0:
                    raise NotExact("a negative matrix power is not used here")
                result = cmatrix_identity(base.nrows)
                for _ in range(exp):
                    result = cmatrix_mul(result, base)
                return result
            if isinstance(base, CNum):
                from pgi.math.hilbert import eval_cnum

                return eval_cnum(term)
    raise NotExact("this term is not a Lorentz or Dirac matrix or scalar")


def _as_matrix_term(term: Term) -> CMatrix:
    value = _eval(term)
    if isinstance(value, CMatrix):
        return value
    raise NotExact("this term is not a matrix")


@dataclass(frozen=True)
class LorentzMatrix:
    value: CMatrix
    origin: Term
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        got = _eval(self.origin)
        if not isinstance(got, CMatrix) or not cmatrix_eq(got, self.value):
            raise KernelError("this Lorentz or Dirac matrix does not match the exact evaluation")


@dataclass(frozen=True)
class LorentzScalar:
    value: CNum
    origin: Term
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        got = _eval(self.origin)
        if not isinstance(got, CNum) or not c_eq(got, self.value):
            raise KernelError("this Lorentz or Dirac scalar does not match the exact evaluation")


def _detail() -> tuple[str, ...]:
    return (
        "The Minkowski metric is η = diag(-1, 1, 1, 1).",
        "A Lorentz boost is kept only when 1 - v^2 is a positive rational square, and when both Λ^T η Λ and Λ η Λ^T equal η.",
        "The so(3,1) generators satisfy [J_i, J_j] = ε_ijk J_k, [K_i, K_j] = -ε_ijk J_k, and [J_i, K_j] = ε_ijk K_k, and each preserves η infinitesimally.",
        "The Dirac matrices satisfy {γ^μ, γ^ν} = 2 η^{μν} I, checked on every pair.",
    )


def eval_lorentz_result(term: Term):
    _standing()
    value = _eval(term)
    if isinstance(value, CMatrix):
        return LorentzMatrix(value, term, _detail())
    if isinstance(value, CNum):
        ratio = c_as_ratio(value)
        if ratio is not None:
            return rat_normalize(ratio.num, ratio.den)
        return LorentzScalar(value, term, _detail())
    raise NotExact("this term is not a Lorentz or Dirac matrix or scalar")


def lorentz_value_rule(origin: Term, result: object, prelude: tuple[str, ...] = ()) -> Rule:
    title_left = pretty(origin)
    if isinstance(result, RatTheorem):
        from pgi.math.rational import ratio_rule

        return ratio_rule(origin, result, prelude)
    if isinstance(result, LorentzScalar):
        shown = show_cnum(result.value)
        return Rule(
            id=f"math.cnum.{shown}",
            layer="base",
            stage="quantity",
            title=f"{title_left} = {shown}",
            produces=f"cnum({shown})",
            detail_lines=(*prelude, *result.detail),
        )
    if isinstance(result, LorentzMatrix):
        shown = show_cmatrix(result.value)
        return Rule(
            id=f"math.cmatrix.{shown}",
            layer="base",
            stage="quantity",
            title=f"{title_left} = {shown}",
            produces=f"cmatrix({shown})",
            detail_lines=(*prelude, *result.detail),
        )
    raise KernelError("this Lorentz or Dirac result has no claim")


def lorentz_equality_rules(
    left: Term,
    right: Term,
    left_value: object,
    right_value: object,
    prelude: tuple[str, ...] = (),
) -> tuple[Rule, ...]:
    title = f"{pretty(left)} = {pretty(right)}"
    if _lorentz_eq(left_value, right_value):
        return (
            Rule(
                id="math.lorentz.eq",
                layer="base",
                stage="quantity",
                title=title,
                produces=f"identity({title})",
                detail_lines=(*prelude, "The two sides are the same exact matrix or scalar."),
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


def _lorentz_eq(left: object, right: object) -> bool:
    lm, rm = _as_matrix(left), _as_matrix(right)
    if lm is not None and rm is not None:
        return cmatrix_eq(lm, rm)
    ls, rs = _as_scalar(left), _as_scalar(right)
    if ls is not None and rs is not None:
        return c_eq(ls, rs)
    return False


def _as_matrix(value: object) -> CMatrix | None:
    if isinstance(value, (LorentzMatrix, HilbTheorem)):
        return value.value
    if isinstance(value, CMatrix):
        return value
    return None


def _as_scalar(value: object) -> CNum | None:
    if isinstance(value, (LorentzScalar, ScalarTheorem)):
        return value.value
    if isinstance(value, CNum):
        return value
    if isinstance(value, RatTheorem):
        return c_from_ratio(value.value)
    return None


def side_as_lorentz(term: Term) -> object:
    try:
        return eval_lorentz_result(term)
    except NotExact:
        if has_hilbert(term) or has_matrix_shape(term):
            return side_as_hilbert(term)
        try:
            return eval_rat(term)
        except NotExact:
            raise
