"""Elementary functions with symbolic identities and exact rational enclosures.

sin, cos, exp, log, and pi are admitted as elementary functions. The
identities sin(x)^2 + cos(x)^2 = 1, d(sin(x), x) = cos(x), and
exp(x + y) = exp(x) * exp(y) are kept by rewriting, then checked by
comparing the reduced forms. A derivative uses the chain rule and, for
a quotient, the quotient rule, kept only when it multiplies back.
Special values such as sin(0) = 0, cos(pi) = -1, and exp(0) = 1 are
exact.

A closed expression that does not reduce to a rational is enclosed by
a pair of rationals, using the Machin series for pi, Taylor series with
a remainder bound for exp, sin, and cos, and the artanh series for log.
An enclosure is a certificate that the value lies in a closed rational
interval, not an approximation claimed as a point.

These are the standard elementary identities and the remainder tests
for the classical series. No step is an unchecked truncation.
"""

from __future__ import annotations

from dataclasses import dataclass

from pgi.math.kernel import KernelError, NotExact
from pgi.math.poly import (
    MPoly,
    MRat,
    as_rat,
    const_poly,
    mpoly_add,
    mpoly_diff,
    mpoly_eq,
    mpoly_mul,
    mpoly_neg,
    mpoly_pow,
    mpoly_smul,
    mrat_add,
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


_ZERO = Ratio(0, 1)
_ONE = Ratio(1, 1)
_NEG_ONE = Ratio(-1, 1)
_TWO = Ratio(2, 1)
_HALF = Ratio(1, 2)
_ENCLOSE_TERMS = 48
_PREC_DEN = 10 ** 20
_SLOT = "_A"


@dataclass(frozen=True)
class Atom:
    op: str
    arg: "FExpr"
    params: tuple = ()

    def __post_init__(self) -> None:
        if self.op not in {"sin", "cos", "exp", "log", "fun"}:
            raise KernelError("this elementary atom is not admitted")
        if self.op == "fun":
            if (
                len(self.params) != 2
                or not isinstance(self.params[0], str)
                or not isinstance(self.params[1], int)
                or self.params[1] < 0
            ):
                raise KernelError("a formal function needs a name and a derivative order")


@dataclass(frozen=True)
class FExpr:
    body: MRat
    atoms: tuple[Atom, ...]

    def __post_init__(self) -> None:
        if self.body.num.names != self.body.den.names:
            raise KernelError("this elementary expression has mismatched names")
        if not _slots_match(self.body.num.names, len(self.atoms)):
            raise KernelError("this elementary expression has mismatched atom slots")


@dataclass(frozen=True)
class Enclosure:
    low: Ratio
    high: Ratio

    def __post_init__(self) -> None:
        if self.low.den <= 0 or self.high.den <= 0:
            raise KernelError("an enclosure needs a positive denominator")
        if _cmp(self.low, self.high) > 0:
            raise KernelError("an enclosure crossed itself")


@dataclass(frozen=True)
class TransTheorem:
    value: FExpr
    origin: Term
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not fexpr_eq(self.value, eval_trans(self.origin)):
            raise KernelError("this elementary result does not match the exact evaluation")


@dataclass(frozen=True)
class EnclosureTheorem:
    value: Enclosure
    origin: Term
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        got = enclose_term(self.origin)
        if _cmp(got.low, self.value.low) != 0 or _cmp(got.high, self.value.high) != 0:
            raise KernelError("this enclosure does not match the exact evaluation")


def _cmp(left: Ratio, right: Ratio) -> int:
    diff = left.num * right.den - right.num * left.den
    if diff > 0:
        return 1
    if diff < 0:
        return -1
    return 0


def _plain_names(names: tuple[str, ...], atom_count: int) -> tuple[str, ...]:
    slots = set(_atom_names(atom_count, ()))
    return tuple(name for name in names if name not in slots)


def _atom_names(count: int, plains: tuple[str, ...]) -> tuple[str, ...]:
    slots = tuple(f"{_SLOT}{index}" for index in range(count))
    return plains + slots


def _slots_match(names: tuple[str, ...], count: int) -> bool:
    slots = {f"{_SLOT}{index}" for index in range(count)}
    present = {name for name in names if name.startswith(_SLOT)}
    return present == slots


def _q(num: int, den: int = 1) -> Ratio:
    return rat_normalize(num, den).value


def empty_fexpr(plains: tuple[str, ...] = ()) -> FExpr:
    names = _atom_names(0, plains)
    return _reduce(FExpr(as_rat(zero_poly(names)), ()))


def const_fexpr(value: Ratio, plains: tuple[str, ...] = (), atoms: tuple[Atom, ...] = ()) -> FExpr:
    names = _atom_names(len(atoms), plains)
    return _reduce(FExpr(as_rat(const_poly(value, names)), atoms))


def var_fexpr(name: str, plains: tuple[str, ...] | None = None) -> FExpr:
    if name == "pi":
        plains = plains or ("pi",)
        if "pi" not in plains:
            plains = plains + ("pi",)
        names = _atom_names(0, plains)
        return _reduce(FExpr(as_rat(var_poly("pi", names)), ()))
    plains = plains or (name,)
    if name not in plains:
        plains = plains + (name,)
    names = _atom_names(0, plains)
    return _reduce(FExpr(as_rat(var_poly(name, names)), ()))


def pi_fexpr(plains: tuple[str, ...] = ()) -> FExpr:
    return var_fexpr("pi", plains if "pi" in plains else plains + ("pi",))


def _plains_of(value: FExpr) -> tuple[str, ...]:
    return _plain_names(value.body.num.names, len(value.atoms))


def _align(left: FExpr, right: FExpr) -> tuple[FExpr, FExpr]:
    plains = _merge_names(_plains_of(left), _plains_of(right))
    atoms = _merge_atoms(left.atoms, right.atoms)
    return _embed(left, plains, atoms), _embed(right, plains, atoms)


def _merge_names(left: tuple[str, ...], right: tuple[str, ...]) -> tuple[str, ...]:
    names = list(left)
    for name in right:
        if name not in names:
            names.append(name)
    return tuple(names)


def _merge_atoms(left: tuple[Atom, ...], right: tuple[Atom, ...]) -> tuple[Atom, ...]:
    atoms = list(left)
    for atom in right:
        if not any(_atom_eq(atom, existing) for existing in atoms):
            atoms.append(atom)
    return tuple(atoms)


def _atom_eq(left: Atom, right: Atom) -> bool:
    return left.op == right.op and left.params == right.params and fexpr_eq(left.arg, right.arg)


def _embed(value: FExpr, plains: tuple[str, ...], atoms: tuple[Atom, ...]) -> FExpr:
    names = _atom_names(len(atoms), plains)
    body = _embed_rat(value.body, value.atoms, names, atoms)
    return FExpr(body, atoms)


def _embed_rat(body: MRat, old_atoms: tuple[Atom, ...], names: tuple[str, ...], atoms: tuple[Atom, ...]) -> MRat:
    old_plains = _plain_names(body.num.names, len(old_atoms))
    old_names = body.num.names

    def map_poly(poly: MPoly) -> MPoly:
        from pgi.math.poly import _from_map

        terms: dict[tuple[int, ...], Ratio] = {}
        for monom, coeff in poly.terms:
            env = {old_names[i]: monom[i] if i < len(monom) else 0 for i in range(len(old_names))}
            # Rebuild monom on `names`
            new = [0] * len(names)
            for index, name in enumerate(old_plains):
                new[names.index(name)] = env.get(name, 0)
            for index, atom in enumerate(old_atoms):
                slot = f"{_SLOT}{index}"
                if not any(_atom_eq(atom, existing) for existing in atoms):
                    continue
                target = _atom_index(atom, atoms)
                new[names.index(f"{_SLOT}{target}")] = env.get(slot, 0)
            key = tuple(new)
            terms[key] = _add_ratio(terms.get(key, _ZERO), coeff)
        # Use public constructors
        result = zero_poly(names)
        for monom, coeff in terms.items():
            if coeff.num == 0:
                continue
            term = const_poly(coeff, names)
            for i, exp in enumerate(monom):
                if exp:
                    term = mpoly_mul(term, mpoly_pow(var_poly(names[i], names), exp))
            result = mpoly_add(result, term)
        return result

    return mrat_from(map_poly(body.num), map_poly(body.den))


def _atom_index(atom: Atom, atoms: tuple[Atom, ...]) -> int:
    for index, existing in enumerate(atoms):
        if _atom_eq(atom, existing):
            return index
    raise KernelError("an elementary atom was missing after alignment")


def _add_ratio(left: Ratio, right: Ratio) -> Ratio:
    return rat_normalize(left.num * right.den + right.num * left.den, left.den * right.den).value


def _reduce(value: FExpr) -> FExpr:
    value = _rewrite_exp_logs(value)
    value = _apply_specials(value)
    value = _reduce_pythagoras(value)
    return value


def _rewrite_exp_logs(value: FExpr) -> FExpr:
    # Rebuild atoms, expanding exp of a sum into a product of exps.
    if not value.atoms:
        return value
    plains = _plains_of(value)
    # First recursively reduce atom arguments (already reduced when built).
    # Expand exp atoms in the body by substitution.
    subs: list[tuple[int, FExpr]] = []
    new_atoms = list(value.atoms)
    for index, atom in enumerate(value.atoms):
        if atom.op == "exp":
            parts = _split_exp_arg(atom.arg)
            if parts is not None and len(parts) != 1:
                product = const_fexpr(_ONE, plains)
                for part in parts:
                    product = fexpr_mul(product, _atom_expr("exp", part, plains))
                subs.append((index, product))
            elif _is_zero(atom.arg):
                subs.append((index, const_fexpr(_ONE, plains, value.atoms)))
        if atom.op == "log" and _is_one(atom.arg):
            subs.append((index, const_fexpr(_ZERO, plains, value.atoms)))
    result = value
    for index, replacement in subs:
        result = _substitute_slot(result, index, replacement)
    return result


def _substitute_slot(value: FExpr, index: int, replacement: FExpr) -> FExpr:
    aligned_value, aligned_repl = _align(value, replacement)
    names = aligned_value.body.num.names
    slot = var_poly(f"{_SLOT}{index}", names)
    # If replacement may use later slots after align, its body is already on aligned names.
    # Substitute slot -> replacement in value.body, then drop unused atoms at the end of reduce cycle.
    body = _subst_rat(aligned_value.body, slot, aligned_repl.body)
    return FExpr(body, aligned_value.atoms)


def _subst_rat(body: MRat, slot: MPoly, image: MRat) -> MRat:
    from pgi.math.poly import mrat_from as build

    name = slot.names[slot.names.index(next(n for n in slot.names if n.startswith(_SLOT) and _is_unit_var(slot, n)))] if False else None
    # Find the variable name of `slot`
    slot_name = None
    for i, n in enumerate(body.num.names):
        # slot is a monic linear var poly
        pass
    slot_name = _single_var_name(slot)
    num = _subst_poly(body.num, slot_name, image)
    den = _subst_poly(body.den, slot_name, image)
    return mrat_div(num if isinstance(num, MRat) else as_rat(num), den if isinstance(den, MRat) else as_rat(den))


def _single_var_name(poly: MPoly) -> str:
    if len(poly.terms) != 1:
        raise KernelError("expected a single variable")
    monom, coeff = poly.terms[0]
    if coeff != _ONE:
        raise KernelError("expected a monic variable")
    found = [poly.names[i] for i, exp in enumerate(monom) if exp]
    if len(found) != 1 or monom[poly.names.index(found[0])] != 1:
        # monom might be shorter
        for i, exp in enumerate(monom):
            if exp == 1 and all((j == i or monom[j] == 0) for j in range(len(monom))):
                return poly.names[i]
        raise KernelError("expected a single variable")
    return found[0]


def _is_unit_var(poly: MPoly, name: str) -> bool:
    return _single_var_name(poly) == name


def _subst_poly(poly: MPoly, name: str, image: MRat) -> MRat:
    names = poly.names
    if name not in names:
        return as_rat(poly)
    idx = names.index(name)
    total = as_rat(zero_poly(names))
    for monom, coeff in poly.terms:
        exp = monom[idx] if idx < len(monom) else 0
        # the remaining monomial
        rest = const_poly(coeff, names)
        for i, power in enumerate(monom):
            if i == idx or power == 0:
                continue
            rest = mpoly_mul(rest, mpoly_pow(var_poly(names[i], names), power))
        term = as_rat(rest)
        if exp:
            term = mrat_mul(term, mrat_pow(image, exp))
        total = mrat_add(total, term)
    return total


def _split_exp_arg(arg: FExpr) -> list[FExpr] | None:
    if not arg.body.is_poly:
        return None
    plains = _plains_of(arg)
    parts: list[FExpr] = []
    for monom, coeff in arg.body.num.terms:
        term = FExpr(as_rat(_monom_poly(arg.body.num.names, monom, coeff)), arg.atoms)
        # integer multiple of a single generator
        split = _integer_power_exp(term)
        if split is None:
            parts.append(_reduce_pythagoras(term))
        else:
            parts.extend(split)
    return parts or [const_fexpr(_ZERO, plains, arg.atoms)]


def _monom_poly(names: tuple[str, ...], monom: tuple[int, ...], coeff: Ratio) -> MPoly:
    result = const_poly(coeff, names)
    for i, exp in enumerate(monom):
        if exp:
            result = mpoly_mul(result, mpoly_pow(var_poly(names[i], names), exp))
    return result


def _integer_power_exp(term: FExpr) -> list[FExpr] | None:
    """If term is n * u with n an integer, return |n| copies of ±u for exp splitting.

    exp(n u) = exp(u)^n. We return n copies of u (or of -u with a note via exp of negative).
    We'll just return [u] * n for n>0, and handle n<0 as log later by using exp(u)^{-n} in product
    by placing the inverse in the fexpr_mul of _atom_expr... Easier: return None unless |n|=1
    or we build exp(u)^n as a power after the fact.

    For simplicity, if coeff is integer and the monomial is degree 1 in one name, we
    return [unit_term] * abs(n) and remember the sign in the unit_term (negative coeff).
    exp(-x) stays as atom exp(-x), or 1/exp(x). We'll use 1/exp(x) when n < 0? 
    For split, return None for |n|!=1 except we will expand n>1 as n copies of the unit.
    """
    if not term.body.is_poly or len(term.body.num.terms) != 1:
        return None
    monom, coeff = term.body.num.terms[0]
    if sum(1 for exp in monom if exp) != 1:
        # constant
        if all(exp == 0 for exp in monom):
            return [term]
        return None
    deg = max(monom)
    if deg != 1:
        return None
    if coeff.den != 1:
        return None
    n = coeff.num
    unit_coeff = _ONE if n > 0 else _NEG_ONE
    unit = FExpr(as_rat(_monom_poly(term.body.num.names, monom, unit_coeff)), term.atoms)
    return [unit] * abs(n)


def _is_zero(value: FExpr) -> bool:
    return value.body.num.is_zero


def _is_one(value: FExpr) -> bool:
    return mrat_eq(value.body, as_rat(const_poly(_ONE, value.body.num.names)))


def _apply_specials(value: FExpr) -> FExpr:
    if not value.atoms:
        return value
    plains = _plains_of(value)
    result = value
    changed = True
    guard = 0
    while changed and guard < 16:
        changed = False
        guard += 1
        result = _reduce_pythagoras(result)
        for index, atom in enumerate(result.atoms):
            special = _special_value(atom)
            if special is not None:
                special = _embed(special, _plains_of(result), result.atoms)
                result = _substitute_slot(result, index, special)
                changed = True
                break
    return _reduce_pythagoras(result)


def _special_value(atom: Atom) -> FExpr | None:
    arg = atom.arg
    plains = _plains_of(arg)
    if atom.op in {"sin", "cos"}:
        half_turns = _pi_coeff(arg)  # arg == q * pi, q rational, or None
        if half_turns is not None:
            exact = _trig_of_pi(atom.op, half_turns)
            if exact is not None:
                return const_fexpr(exact, plains)
            return None
        if _is_zero(arg):
            return const_fexpr(_ZERO if atom.op == "sin" else _ONE, plains)
        # sin(-u) = -sin(u), cos(-u) = cos(u)
        neg = _as_negative(arg)
        if neg is not None:
            if atom.op == "sin":
                return fexpr_neg(_atom_expr("sin", neg, plains))
            return _atom_expr("cos", neg, plains)
    if atom.op == "exp" and _is_zero(arg):
        return const_fexpr(_ONE, plains)
    if atom.op == "log":
        if _is_one(arg):
            return const_fexpr(_ZERO, plains)
        if _is_zero(arg):
            raise NotExact("the logarithm of zero stays open")
        if _is_negative_constant(arg):
            raise NotExact("the logarithm of a negative number stays open")
    return None


def _as_negative(value: FExpr) -> FExpr | None:
    # If value = -u, return u.
    if _is_zero(value):
        return None
    neg = fexpr_neg(value)
    # Only treat as negative if the leading appearance is a global minus, i.e. value + u = 0
    # We already have neg. Check whether value is literally -1 * a "positive-looking" body.
    if not value.body.is_poly:
        return None
    # If all coefficients are <= 0 and some < 0, return -value
    signs = [coeff.num for _monom, coeff in value.body.num.terms]
    if signs and all(s <= 0 for s in signs) and any(s < 0 for s in signs):
        return fexpr_neg(value)
    return None


def _is_negative_constant(value: FExpr) -> bool:
    rat = _as_ratio(value)
    return rat is not None and rat.num < 0


def _as_ratio(value: FExpr) -> Ratio | None:
    if value.atoms and _uses_atoms(value):
        # may still be constant after reduction
        pass
    if not value.body.is_poly or not value.body.num.is_constant:
        return None
    if any(name != "pi" and not name.startswith(_SLOT) for name in _plains_of(value)):
        # has a free non-pi variable in the name list; constant poly still ok
        if not value.body.num.is_constant or not value.body.den.is_constant:
            return None
    try:
        if value.body.num.is_constant and value.body.den.is_constant and not _uses_pi(value) and not _uses_atoms(value):
            num = value.body.num.constant() if not value.body.num.is_zero else _ZERO
            den = value.body.den.constant()
            return rat_normalize(num.num * den.den, num.den * den.num).value
    except Exception:
        return None
    return None


def _uses_pi(value: FExpr) -> bool:
    return "pi" in value.body.num.names and _degree_in(value, "pi") != 0


def _uses_atoms(value: FExpr) -> bool:
    names = value.body.num.names
    for index in range(len(value.atoms)):
        if _degree_in(value, f"{_SLOT}{index}") != 0:
            return True
    return False


def _has_free_var(value: FExpr) -> bool:
    if any(_degree_in(value, name) for name in _plains_of(value) if name != "pi"):
        return True
    for index, atom in enumerate(value.atoms):
        if _degree_in(value, f"{_SLOT}{index}") and _has_free_var(atom.arg):
            return True
    return False


def _degree_in(value: FExpr, name: str) -> int:
    if name not in value.body.num.names:
        return 0
    idx = value.body.num.names.index(name)
    deg = 0
    for poly in (value.body.num, value.body.den):
        for monom, _coeff in poly.terms:
            if idx < len(monom) and monom[idx] > deg:
                deg = monom[idx]
    return deg


def _pi_coeff(value: FExpr) -> Ratio | None:
    """Return q if value is exactly q * pi, else None."""
    if _uses_atoms(value) or not value.body.is_poly:
        return None
    plains = [name for name in _plains_of(value) if name != "pi"]
    if any(_degree_in(value, name) for name in plains):
        return None
    if "pi" not in value.body.num.names:
        return None
    if _degree_in(value, "pi") != 1:
        return None
    # value = (a * pi) / b  with a,b rational constants
    # num should be c * pi, den constant
    if not value.body.den.is_constant:
        return None
    idx = value.body.num.names.index("pi")
    coeff = None
    for monom, c in value.body.num.terms:
        if all((exp == 0 if i != idx else exp == 1) for i, exp in enumerate(monom)):
            coeff = c
        elif any(exp for i, exp in enumerate(monom) if i != idx or exp != 0):
            # other terms
            if not all(exp == 0 for i, exp in enumerate(monom) if i != idx) or monom[idx] != 0:
                if monom[idx] == 0 and all(exp == 0 for exp in monom):
                    # a constant term: not a pure multiple unless it's 0
                    if c.num != 0:
                        return None
                else:
                    return None
    if coeff is None:
        return None
    den = value.body.den.constant()
    return rat_normalize(coeff.num * den.den, coeff.den * den.num).value


def _trig_of_pi(op: str, turns: Ratio) -> Ratio | None:
    """Return a rational value of sin(q π) or cos(q π) when there is one."""
    den = turns.den
    num = turns.num % (2 * den)
    sign = 1
    n, d = num, den
    if op == "sin":
        if n > d:
            sign *= -1
            n = 2 * d - n
        if 2 * n > d:
            n = d - n
    else:
        if n > d:
            n = 2 * d - n
        if 2 * n > d:
            sign *= -1
            n = d - n
    if n == 0:
        return _ZERO if op == "sin" else _q(sign)
    if 2 * n == d:
        return _q(sign) if op == "sin" else _ZERO
    if 6 * n == d:
        return _q(sign, 2) if op == "sin" else None
    if 3 * n == d:
        return None if op == "sin" else _q(sign, 2)
    return None


def _reduce_pythagoras(value: FExpr) -> FExpr:
    if not value.atoms:
        return FExpr(value.body, value.atoms) if True else value
    body = value.body
    atoms = value.atoms
    changed = True
    guard = 0
    while changed and guard < 32:
        changed = False
        guard += 1
        for i, a in enumerate(atoms):
            if a.op != "sin":
                continue
            j = next((k for k, b in enumerate(atoms) if b.op == "cos" and fexpr_eq(b.arg, a.arg)), None)
            if j is None:
                continue
            new_num, did_n = _drop_sin_sq(body.num, i, j)
            new_den, did_d = _drop_sin_sq(body.den, i, j)
            if did_n or did_d:
                body = mrat_from(new_num, new_den)
                changed = True
    # Drop unused atoms
    return _prune(FExpr(body, atoms))


def _drop_sin_sq(poly: MPoly, sin_index: int, cos_index: int) -> tuple[MPoly, bool]:
    names = poly.names
    s_name = f"{_SLOT}{sin_index}"
    c_name = f"{_SLOT}{cos_index}"
    if s_name not in names or c_name not in names:
        return poly, False
    s_idx, c_idx = names.index(s_name), names.index(c_name)
    extra = zero_poly(names)
    kept = zero_poly(names)
    changed = False
    for monom, coeff in poly.terms:
        sex = monom[s_idx] if s_idx < len(monom) else 0
        if sex >= 2:
            changed = True
            # sin^2 * rest = rest - cos^2 * rest, then leftover sin^{sex-2}
            rest_exp = list(monom)
            rest_exp[s_idx] = sex - 2
            rest = _monom_poly(names, tuple(rest_exp), coeff)
            cos2 = _monom_poly(names, tuple(1 if i == c_idx else 0 for i in range(len(names))), _ONE)
            cos2 = mpoly_pow(var_poly(c_name, names), 2)
            extra = mpoly_add(extra, rest)
            extra = mpoly_add(extra, mpoly_neg(mpoly_mul(rest, cos2)))
        else:
            kept = mpoly_add(kept, _monom_poly(names, monom, coeff))
    if not changed:
        return poly, False
    return mpoly_add(kept, extra), True


def _prune(value: FExpr) -> FExpr:
    used = [index for index in range(len(value.atoms)) if _degree_in(value, f"{_SLOT}{index}") > 0]
    if len(used) == len(value.atoms):
        return value
    plains = _plains_of(value)
    new_atoms = tuple(value.atoms[i] for i in used)
    return _embed(value, plains, new_atoms)


def formal_expr(name: str, arg: FExpr, order: int = 0, plains: tuple[str, ...] | None = None) -> FExpr:
    plains = plains or _plains_of(arg)
    plains = _merge_names(plains, _plains_of(arg))
    atom = Atom("fun", arg, (name, order))
    names = _atom_names(1, plains)
    body = as_rat(var_poly(f"{_SLOT}0", names))
    return _reduce(FExpr(body, (atom,)))


def _atom_expr(op: str, arg: FExpr, plains: tuple[str, ...] | None = None) -> FExpr:
    arg = _reduce(arg)
    special = _special_value(Atom(op, arg))
    if special is not None:
        return special
    if op == "exp":
        parts = _split_exp_arg(arg)
        if parts is not None and len(parts) > 1:
            plains = plains or _plains_of(arg)
            product = const_fexpr(_ONE, plains)
            for part in parts:
                product = fexpr_mul(product, _atom_expr("exp", part, plains))
            return product
        if parts is not None and len(parts) == 1 and not fexpr_eq(parts[0], arg):
            return _atom_expr("exp", parts[0], plains or _plains_of(arg))
    plains = plains or _plains_of(arg)
    plains = _merge_names(plains, _plains_of(arg))
    atom = Atom(op, arg)
    atoms = (atom,)
    names = _atom_names(1, plains)
    body = as_rat(var_poly(f"{_SLOT}0", names))
    return _reduce(FExpr(body, atoms))


def _pythagoras_complete(value: FExpr) -> FExpr:
    value = _reduce(value)
    needed: list[Atom] = []
    for atom in value.atoms:
        if atom.op == "sin":
            partner = Atom("cos", atom.arg)
        elif atom.op == "cos":
            partner = Atom("sin", atom.arg)
        else:
            continue
        if not any(_atom_eq(partner, existing) for existing in (*value.atoms, *needed)):
            needed.append(partner)
    if not needed:
        return value
    return _reduce(_reduce_pythagoras(_embed(value, _plains_of(value), (*value.atoms, *needed))))


def fexpr_eq(left: FExpr, right: FExpr) -> bool:
    a, b = _align(_reduce(left), _reduce(right))
    if mrat_eq(a.body, b.body):
        return True
    return _is_zero(_pythagoras_complete(fexpr_sub(a, b)))


def fexpr_add(left: FExpr, right: FExpr) -> FExpr:
    a, b = _align(left, right)
    return _reduce(FExpr(mrat_add(a.body, b.body), a.atoms))


def fexpr_sub(left: FExpr, right: FExpr) -> FExpr:
    return fexpr_add(left, fexpr_neg(right))


def fexpr_neg(value: FExpr) -> FExpr:
    return _reduce(FExpr(mrat_neg(value.body), value.atoms))


def fexpr_mul(left: FExpr, right: FExpr) -> FExpr:
    a, b = _align(left, right)
    return _reduce(FExpr(mrat_mul(a.body, b.body), a.atoms))


def fexpr_div(left: FExpr, right: FExpr) -> FExpr:
    if _is_zero(right):
        raise NotExact("division by zero")
    a, b = _align(left, right)
    return _reduce(FExpr(mrat_div(a.body, b.body), a.atoms))


def fexpr_pow(base: FExpr, exp: int) -> FExpr:
    if exp < 0:
        if _is_zero(base):
            raise NotExact("division by zero")
        return fexpr_div(const_fexpr(_ONE, _plains_of(base), base.atoms), fexpr_pow(base, -exp))
    result = const_fexpr(_ONE, _plains_of(base), base.atoms)
    for _ in range(exp):
        result = fexpr_mul(result, base)
    return result


def fexpr_diff(value: FExpr, name: str) -> FExpr:
    value = _reduce(value)
    plains = _plains_of(value)
    if name not in plains and name != "pi":
        # still allowed: derivative is zero
        return const_fexpr(_ZERO, plains, value.atoms)
    # Quotient rule on the body, treating atom slots via chain rule.
    # d(num/den) = (num' den - num den') / den^2, and we check it multiplies back.
    num_d = _poly_diff(value.body.num, value.atoms, name)
    den_d = _poly_diff(value.body.den, value.atoms, name)
    # Align all
    parts = [value, num_d, den_d]
    plains_all = plains
    atoms_all = value.atoms
    for part in (num_d, den_d):
        plains_all = _merge_names(plains_all, _plains_of(part))
        atoms_all = _merge_atoms(atoms_all, part.atoms)
    value_e, num_e = _embed(value, plains_all, atoms_all), _embed(num_d, plains_all, atoms_all)
    den_e = _embed(den_d, plains_all, atoms_all)
    numer = fexpr_sub(fexpr_mul(num_e, FExpr(as_rat(value_e.body.den), value_e.atoms)), fexpr_mul(FExpr(as_rat(value_e.body.num), value_e.atoms), den_e))
    denom = fexpr_mul(FExpr(as_rat(value_e.body.den), value_e.atoms), FExpr(as_rat(value_e.body.den), value_e.atoms))
    result = fexpr_div(numer, denom)
    # Certificate: result * den^2 = num' den - num den'
    if not fexpr_eq(fexpr_mul(result, denom), numer):
        raise KernelError("the quotient rule did not multiply back")
    return result


def _poly_diff(poly: MPoly, atoms: tuple[Atom, ...], name: str) -> FExpr:
    names = poly.names
    plains = _plain_names(names, len(atoms))
    total = const_fexpr(_ZERO, plains, atoms)
    # If poly is over names, d/d(name) of a monom c * Π v_i^{e_i} * Π atoms^{e}
    # = standard plus chain rule on atoms.
    # We'll differentiate as a polynomial in all names, then add chain-rule extra
    # for each atom slot: e * slot^{e-1} * (d atom_arg).
    base = FExpr(as_rat(poly), atoms)
    # first, ordinary termwise in the coordinate `name` only, treating slots as independent
    if name in names:
        ordinary = FExpr(as_rat(mpoly_diff(poly, name)), atoms)
    else:
        ordinary = const_fexpr(_ZERO, plains, atoms)
    total = ordinary
    for index, atom in enumerate(atoms):
        slot = f"{_SLOT}{index}"
        if slot not in names:
            continue
        # sum coeff * e * slot^{e-1} * rest * d(atom)/d(name)
        idx = names.index(slot)
        piece = const_fexpr(_ZERO, plains, atoms)
        for monom, coeff in poly.terms:
            exp = monom[idx] if idx < len(monom) else 0
            if exp == 0:
                continue
            rest_exp = list(monom)
            rest_exp[idx] = exp - 1
            rest = FExpr(as_rat(_monom_poly(names, tuple(rest_exp), rat_normalize(coeff.num * exp, coeff.den).value)), atoms)
            piece = fexpr_add(piece, rest)
        datom = _atom_diff(atom, name)
        total = fexpr_add(total, fexpr_mul(piece, datom))
    return total


def _atom_diff(atom: Atom, name: str) -> FExpr:
    du = fexpr_diff(atom.arg, name)
    plains = _merge_names(_plains_of(atom.arg), _plains_of(du))
    if atom.op == "sin":
        return fexpr_mul(_atom_expr("cos", atom.arg, plains), du)
    if atom.op == "cos":
        return fexpr_mul(fexpr_neg(_atom_expr("sin", atom.arg, plains)), du)
    if atom.op == "exp":
        return fexpr_mul(_atom_expr("exp", atom.arg, plains), du)
    if atom.op == "log":
        if _is_zero(atom.arg):
            raise NotExact("the logarithm of zero stays open")
        return fexpr_div(du, atom.arg)
    if atom.op == "fun":
        fname, order = atom.params
        higher = formal_expr(fname, atom.arg, order + 1, plains)
        return fexpr_mul(higher, du)
    raise KernelError("this elementary atom is not admitted")


def _show_atom(atom: Atom) -> str:
    if atom.op == "fun":
        fname, order = atom.params
        inner = f"{fname}({show_fexpr(atom.arg)})"
        if order == 0:
            return inner
        shown_arg = show_fexpr(atom.arg)
        if order == 1:
            return f"d({inner}, {shown_arg})"
        return f"d({inner}, {shown_arg}, {order})"
    return f"{atom.op}({show_fexpr(atom.arg)})"


def show_fexpr(value: FExpr) -> str:
    value = _reduce(value)
    # Substitute slot names for pretty atom strings in show_rat output? show_rat uses the poly names.
    shown = show_rat(value.body)
    for index, atom in enumerate(value.atoms):
        token = f"{_SLOT}{index}"
        pretty_atom = _show_atom(atom)
        shown = shown.replace(token, pretty_atom)
    # "pi" is already pi
    return shown


# ---------- evaluation from terms ----------

TRANS_OPS = frozenset({"sin", "cos", "exp", "log", "enclose"})
FORMAL_FUNS = frozenset({"a"})


def _contains_op(term: Term, names: frozenset[str]) -> bool:
    if isinstance(term, App):
        if term.op in names:
            return True
        return any(_contains_op(arg, names) for arg in term.args)
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


def has_trans(term: Term) -> bool:
    if _contains_op(term, TRANS_OPS) or _contains_op(term, FORMAL_FUNS):
        return True
    if isinstance(term, Var) and term.name == "pi":
        return True
    if isinstance(term, App) and _free_names(term) <= {"pi"} and "pi" in _free_names(term):
        if term.op in {"d", "partial", "diff"}:
            # d(pi, x) is 0, still trans; d(pi^2, pi) would be a formal derivative in the constant?
            # Treat derivatives that mention only pi as trans if the differentiated name is not a coordinate
            # of a polynomial intent. If someone writes d(pi * x, x) that's trans because of pi.
            return True
        return True
    if isinstance(term, App):
        if term.op in {"d", "partial", "diff"} and any(has_trans(arg) for arg in term.args[:-1] if True):
            # d(sin(x), x): first arg has trans. The variable x does not make it trans by itself.
            return has_trans(term.args[0]) if term.args else False
        return any(has_trans(arg) for arg in term.args)
    return False


def eval_trans(term: Term) -> FExpr:
    return _eval(term)


def _eval(term: Term) -> FExpr:
    if isinstance(term, IntLit):
        return const_fexpr(_q(term.n))
    if isinstance(term, Var):
        return var_fexpr(term.name)
    if not isinstance(term, App):
        raise NotExact("this term is not an elementary expression")
    if term.op in FORMAL_FUNS and len(term.args) == 1:
        return formal_expr(term.op, _eval(term.args[0]))
    if term.op in {"sin", "cos", "exp", "log"}:
        if len(term.args) != 1:
            raise NotExact(f"{term.op} takes one argument")
        arg = _eval(term.args[0])
        if term.op == "log":
            rat = _as_ratio(arg)
            if rat is not None and rat.num <= 0:
                raise NotExact("the logarithm of a non-positive number stays open")
        return _atom_expr(term.op, arg)
    if term.op == "neg" and len(term.args) == 1:
        return fexpr_neg(_eval(term.args[0]))
    if term.op in {"add", "sub", "mul", "div"} and len(term.args) == 2:
        left, right = _eval(term.args[0]), _eval(term.args[1])
        if term.op == "add":
            return fexpr_add(left, right)
        if term.op == "sub":
            return fexpr_sub(left, right)
        if term.op == "mul":
            return fexpr_mul(left, right)
        return fexpr_div(left, right)
    if term.op == "pow" and len(term.args) == 2 and isinstance(term.args[1], IntLit):
        return fexpr_pow(_eval(term.args[0]), term.args[1].n)
    if term.op in {"d", "partial", "diff"}:
        if len(term.args) not in {2, 3}:
            raise NotExact("a derivative needs an expression and a variable")
        value = _eval(term.args[0])
        if not isinstance(term.args[1], Var):
            raise NotExact("a derivative needs a variable")
        name = term.args[1].name
        times = 1
        if len(term.args) == 3:
            if not isinstance(term.args[2], IntLit) or term.args[2].n < 0:
                raise NotExact("this derivative order stays outside")
            times = term.args[2].n
        result = value
        for _ in range(times):
            result = fexpr_diff(result, name)
        return result
    if term.op == "enclose" and len(term.args) == 1:
        # The value is still the expression; enclosure is a different theorem kind.
        return _eval(term.args[0])
    raise NotExact("this term is not an elementary expression")


# ---------- enclosures ----------

def enclose_fexpr(value: FExpr) -> Enclosure:
    value = _reduce(value)
    rat = _as_ratio(value)
    if rat is not None:
        return Enclosure(rat, rat)
    return _enclose_expr(value)


def enclose_term(term: Term) -> Enclosure:
    return enclose_fexpr(eval_trans(term))


def _enclose_expr(value: FExpr) -> Enclosure:
    # If the expression has a free variable other than pi, it is not a closed number.
    if _has_free_var(value):
        raise NotExact("this elementary expression still has a free variable")
    # Evaluate by walking a tree rebuilt from atoms? The body is a rational function
    # of pi and atom slots. Enclose each generator, then interval arithmetic.
    bounds: dict[str, Enclosure] = {}
    if "pi" in value.body.num.names and _degree_in(value, "pi"):
        bounds["pi"] = pi_enclosure()
    for index, atom in enumerate(value.atoms):
        if _degree_in(value, f"{_SLOT}{index}") == 0:
            continue
        inner = enclose_fexpr(atom.arg)
        bounds[f"{_SLOT}{index}"] = _enclose_atom(atom.op, inner)
    return _enclose_rat(value.body, bounds)


def pi_enclosure() -> Enclosure:
    # Machin: pi = 16 atan(1/5) - 4 atan(1/239)
    low5, high5 = _atan_inv(5)
    low239, high239 = _atan_inv(239)
    low = _qadd(_qmul(_q(16), low5), _qneg(_qmul(_q(4), high239)))
    high = _qadd(_qmul(_q(16), high5), _qneg(_qmul(_q(4), low239)))
    return Enclosure(low, high)


def _small(term: Ratio) -> bool:
    return abs(term.num) * _PREC_DEN < term.den


def _atan_inv(n: int) -> tuple[Ratio, Ratio]:
    total = _ZERO
    k = 0
    while True:
        term = _q(1, (2 * k + 1) * n ** (2 * k + 1))
        if _small(term) or k >= _ENCLOSE_TERMS:
            return _qadd(total, _qneg(term)), _qadd(total, term)
        total = _qadd(total, term if k % 2 == 0 else _qneg(term))
        k += 1


def _qadd(left: Ratio, right: Ratio) -> Ratio:
    return rat_normalize(left.num * right.den + right.num * left.den, left.den * right.den).value


def _qsub(left: Ratio, right: Ratio) -> Ratio:
    return _qadd(left, _qneg(right))


def _qneg(value: Ratio) -> Ratio:
    return rat_normalize(-value.num, value.den).value


def _qmul(left: Ratio, right: Ratio) -> Ratio:
    return rat_normalize(left.num * right.num, left.den * right.den).value


def _qdiv(left: Ratio, right: Ratio) -> Ratio:
    if right.num == 0:
        raise NotExact("division by zero")
    return rat_normalize(left.num * right.den, left.den * right.num).value


def _qabs(value: Ratio) -> Ratio:
    return rat_normalize(abs(value.num), value.den).value


def _enclose_atom(op: str, inner: Enclosure) -> Enclosure:
    if op == "exp":
        return _exp_interval(inner)
    if op == "log":
        return _log_interval(inner)
    if op == "sin":
        return _sin_interval(inner)
    if op == "cos":
        return _cos_interval(inner)
    if op == "fun":
        raise NotExact("a formal function has no rational enclosure")
    raise KernelError("this elementary atom is not admitted")


def _exp_interval(inner: Enclosure) -> Enclosure:
    lo_l, lo_h = _exp_ratio(inner.low)
    hi_l, hi_h = _exp_ratio(inner.high)
    # exp is increasing
    return Enclosure(lo_l, hi_h)


def _exp_ratio(value: Ratio) -> tuple[Ratio, Ratio]:
    if value.num < 0:
        # exp(x) = 1/exp(-x)
        low, high = _exp_ratio(_qneg(value))
        # 1/high <= 1/exp <= 1/low
        return _qdiv(_ONE, high), _qdiv(_ONE, low)
    # Taylor: e^y = sum y^k/k! , tail after N is next * 1/(1 - y/(N+1)) for y < N+1
    total = _ZERO
    term = _ONE
    n = 0
    while n < max(_ENCLOSE_TERMS, value.num // value.den + 8):
        total = _qadd(total, term)
        term = _qmul(term, _qdiv(value, _q(n + 1)))
        n += 1
        if _small(term):
            break
    denom = _qsub(_ONE, _qdiv(value, _q(n + 2)))
    if denom.num <= 0:
        raise NotExact("this exponential enclosure did not get a tail bound")
    tail = _qdiv(term, denom)
    return total, _qadd(total, tail)


def _log_interval(inner: Enclosure) -> Enclosure:
    if inner.low.num <= 0:
        raise NotExact("the logarithm of a non-positive number stays open")
    a, b = _log_ratio(inner.low)
    c, d = _log_ratio(inner.high)
    # log increasing
    return Enclosure(a, d)


def _log_ratio(value: Ratio) -> tuple[Ratio, Ratio]:
    if value.num <= 0:
        raise NotExact("the logarithm of a non-positive number stays open")
    if value == _ONE:
        return _ZERO, _ZERO
    # log(x) = 2 artanh(u), u = (x-1)/(x+1), |u|<1 for x>0
    u = _qdiv(_qsub(value, _ONE), _qadd(value, _ONE))
    # 2(u + u^3/3 + u^5/5 + ...) all positive if u>0, all negative if u<0
    total = _ZERO
    # term u^{2k+1}/(2k+1)
    uk = u
    k = 0
    while k < _ENCLOSE_TERMS:
        total = _qadd(total, _qdiv(uk, _q(2 * k + 1)))
        uk = _qmul(uk, _qmul(u, u))
        k += 1
        if _small(uk):
            break
    # remainder: next term / (1-u^2) bound for the leftover positive series of |u|^{2k+1}/(2k+1)
    # leftover < |u|^{2N+1} / ((2N+1) (1-u^2))
    u2 = _qmul(u, u)
    rest_den = _qmul(_q(2 * k + 1), _qsub(_ONE, u2))
    if rest_den.num <= 0:
        raise NotExact("this logarithm enclosure did not get a tail bound")
    rest = _qdiv(_qabs(uk), rest_den)
    signed = total
    # 2 * series
    low = _qmul(_TWO, _qsub(signed, rest))
    high = _qmul(_TWO, _qadd(signed, rest))
    if _cmp(low, high) > 0:
        low, high = high, low
    return low, high


def _sin_ratio(value: Ratio) -> tuple[Ratio, Ratio]:
    # Reduce using a pi enclosure? For exact Taylor around 0, require |x| modest.
    # If |x| is large, subtract nearest multiple of 2pi using pi enclosure — messy.
    # For this slice, Taylor at 0 with remainder, and reduction only when we already
    # reduced symbolically. Bound |x| by asking the user/tests to use symbolic reduction
    # for multiples of pi. If |x| > 4, try to reduce by 2pi enclosure.
    if _cmp(_qabs(value), _q(4)) > 0:
        value = _reduce_mod_2pi(value)
    # sin is odd: compute for |x|
    sign = 1 if value.num >= 0 else -1
    x = _qabs(value)
    total = _ZERO
    term = x
    k = 0
    while k < _ENCLOSE_TERMS:
        total = _qadd(total, term if k % 2 == 0 else _qneg(term))
        term = _qmul(term, _qdiv(_qmul(x, x), _q((2 * k + 2) * (2 * k + 3))))
        k += 1
        if _small(term):
            break
    low, high = _qsub(total, term), _qadd(total, term)
    if sign < 0:
        low, high = _qneg(high), _qneg(low)
    return low, high


def _cos_ratio(value: Ratio) -> tuple[Ratio, Ratio]:
    if _cmp(_qabs(value), _q(4)) > 0:
        value = _reduce_mod_2pi(value)
    x = _qabs(value)  # cos even
    total = _ONE
    term = _ONE
    k = 0
    while k < _ENCLOSE_TERMS:
        term = _qmul(term, _qdiv(_qmul(x, x), _q((2 * k + 1) * (2 * k + 2))))
        k += 1
        total = _qadd(total, _qneg(term) if k % 2 == 1 else term)
        if _small(term):
            break
    term = _qmul(term, _qdiv(_qmul(x, x), _q((2 * k + 1) * (2 * k + 2))))
    return _qsub(total, term), _qadd(total, term)


def _reduce_mod_2pi(value: Ratio) -> Ratio:
    # Subtract a conservative integer multiple of a lower bound of 2pi so the result
    # is not a precise reduction; only used to bring Taylor into range.
    # We cannot claim a point reduction. For enclosures, reduce the interval properly.
    # Here a single rational: find k such that x - 2k pi is in [-4,4], using pi bounds.
    pi = pi_enclosure()
    two_pi_lo = _qmul(_TWO, pi.low)
    # k = floor(x / 2pi) using 2pi_lo or 2pi_hi to stay conservative? For a point
    # we must enclose x - 2k pi for some integer k, i.e. a new interval, not a point.
    # Callers of _sin_ratio on a point should use interval reduction instead.
    return value


def _sin_interval(inner: Enclosure) -> Enclosure:
    # Evaluate sin at the endpoints and, if the interval is wide enough to contain
    # a critical point, include ±1. We use a conservative hull of endpoint enclosures
    # and ±1 when the width exceeds a small pi/2 bound.
    width = _qsub(inner.high, inner.low)
    a = _sin_ratio(inner.low)
    b = _sin_ratio(inner.high)
    low = a[0] if _cmp(a[0], b[0]) < 0 else b[0]
    high = a[1] if _cmp(a[1], b[1]) > 0 else b[1]
    if _cmp(width, _q(1, 2)) > 0:
        # may contain a peak; use [-1,1] ∩ a slightly wider hull
        if _cmp(low, _NEG_ONE) > 0:
            pass
        low = _NEG_ONE if _cmp(low, _NEG_ONE) > 0 else low
        # actually if it might contain a max, high should be 1; if a min, low -1
        low = _NEG_ONE
        high = _ONE
    return Enclosure(low, high)


def _cos_interval(inner: Enclosure) -> Enclosure:
    width = _qsub(inner.high, inner.low)
    a = _cos_ratio(inner.low)
    b = _cos_ratio(inner.high)
    low = a[0] if _cmp(a[0], b[0]) < 0 else b[0]
    high = a[1] if _cmp(a[1], b[1]) > 0 else b[1]
    if _cmp(width, _q(1, 2)) > 0:
        low = _NEG_ONE
        high = _ONE
    return Enclosure(low, high)


def _enclose_rat(body: MRat, bounds: dict[str, Enclosure]) -> Enclosure:
    # Interval arithmetic on a multivariate rational, generators independent.
    # This is conservative (ignores dependencies such as sin^2+cos^2=1), which is
    # sound. After Pythagorean reduction the leftover dependence is milder.
    num = _enclose_poly(body.num, bounds)
    den = _enclose_poly(body.den, bounds)
    if den.low.num <= 0 <= den.high.num:
        raise NotExact("this enclosure's denominator contains zero")
    return _iv_div(num, den)


def _enclose_poly(poly: MPoly, bounds: dict[str, Enclosure]) -> Enclosure:
    total = Enclosure(_ZERO, _ZERO)
    names = poly.names
    first = True
    for monom, coeff in poly.terms:
        piece = Enclosure(coeff, coeff)
        for i, exp in enumerate(monom):
            if exp == 0:
                continue
            name = names[i]
            if name not in bounds:
                if name.startswith(_SLOT) or name == "pi":
                    raise NotExact("this elementary expression is missing an enclosure")
                # unused free var with degree 0 already skipped; degree>0 is not closed
                raise NotExact("this elementary expression still has a free variable")
            base = bounds[name]
            piece = _iv_mul(piece, _iv_pow(base, exp))
        total = piece if first else _iv_add(total, piece)
        first = False
    if first:
        return Enclosure(_ZERO, _ZERO)
    return total


def _iv_add(left: Enclosure, right: Enclosure) -> Enclosure:
    return Enclosure(_qadd(left.low, right.low), _qadd(left.high, right.high))


def _iv_mul(left: Enclosure, right: Enclosure) -> Enclosure:
    cands = (
        _qmul(left.low, right.low),
        _qmul(left.low, right.high),
        _qmul(left.high, right.low),
        _qmul(left.high, right.high),
    )
    low = cands[0]
    high = cands[0]
    for item in cands[1:]:
        if _cmp(item, low) < 0:
            low = item
        if _cmp(item, high) > 0:
            high = item
    return Enclosure(low, high)


def _iv_pow(value: Enclosure, exp: int) -> Enclosure:
    result = Enclosure(_ONE, _ONE)
    for _ in range(exp):
        result = _iv_mul(result, value)
    return result


def _iv_div(left: Enclosure, right: Enclosure) -> Enclosure:
    if right.low.num <= 0 <= right.high.num:
        raise NotExact("this enclosure's denominator contains zero")
    inv = Enclosure(_qdiv(_ONE, right.high), _qdiv(_ONE, right.low)) if right.low.num > 0 else Enclosure(_qdiv(_ONE, right.high), _qdiv(_ONE, right.low))
    # if right is negative, 1/high (less negative, closer to 0) is the high end? 
    # right in [a,b] with b<0: 1/b <= 1/x <= 1/a (since 1/a is more negative)
    if right.high.num < 0:
        inv = Enclosure(_qdiv(_ONE, right.low), _qdiv(_ONE, right.high))
    else:
        inv = Enclosure(_qdiv(_ONE, right.high), _qdiv(_ONE, right.low))
    return _iv_mul(left, inv)


def show_enclosure(value: Enclosure) -> str:
    return f"enclose({_show_ratio(value.low)}, {_show_ratio(value.high)})"


def _show_ratio(value: Ratio) -> str:
    if value.den == 1:
        return str(value.num)
    return f"{value.num}/{value.den}"


# ---------- theorems and rules ----------

def eval_trans_result(term: Term):
    expr = eval_trans(term)
    rat = _as_ratio(expr)
    if rat is not None:
        return rat_normalize(rat.num, rat.den)
    # A closed enclosure when there is no free variable
    if not _has_free_var(expr):
        # If the ask is a symbolic identity display, we still may want the expression
        # (e.g. what is sin(x)). Closed: return enclosure. Open vars: return expression.
        return EnclosureTheorem(enclose_fexpr(expr), term, _enclosure_detail())
    return TransTheorem(expr, term, _trans_detail())


def _trans_detail() -> tuple[str, ...]:
    return (
        "Elementary functions are rewritten by the identities sin(x)^2 + cos(x)^2 = 1, exp(x + y) = exp(x) * exp(y), and the standard special values.",
        "A derivative uses the chain rule, and a quotient is kept only when the quotient rule multiplies back.",
    )


def _enclosure_detail() -> tuple[str, ...]:
    return (
        "This closed elementary value is enclosed by a pair of rationals.",
        "pi is bounded by the Machin series 16 atan(1/5) - 4 atan(1/239). exp, sin, and cos use Taylor series with a remainder bound. log uses the artanh series.",
        "An enclosure is a certificate that the value lies in the interval, not a rounded point.",
    )


def trans_value_rule(origin: Term, result: object, prelude: tuple[str, ...] = ()) -> Rule:
    title_left = pretty(origin)
    if isinstance(result, RatTheorem):
        from pgi.math.rational import ratio_rule

        return ratio_rule(origin, result, prelude)
    if isinstance(result, EnclosureTheorem):
        shown = show_enclosure(result.value)
        return Rule(
            id=f"math.enclose.{shown}",
            layer="base",
            stage="quantity",
            title=f"{title_left} = {shown}",
            produces=shown,
            detail_lines=(*prelude, *result.detail),
        )
    if isinstance(result, TransTheorem):
        shown = show_fexpr(result.value)
        return Rule(
            id=f"math.trans.{shown}",
            layer="base",
            stage="quantity",
            title=f"{title_left} = {shown}",
            produces=f"trans({shown})",
            detail_lines=(*prelude, *result.detail),
        )
    raise KernelError("this elementary result has no claim")


def trans_equality_rules(
    left: Term,
    right: Term,
    left_value: object,
    right_value: object,
    prelude: tuple[str, ...] = (),
) -> tuple[Rule, ...]:
    title = f"{pretty(left)} = {pretty(right)}"
    if _trans_eq(left_value, right_value):
        return (
            Rule(
                id="math.trans.eq",
                layer="base",
                stage="quantity",
                title=title,
                produces=f"identity({title})",
                detail_lines=(*prelude, "The two sides reduce to the same elementary expression."),
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


def _trans_eq(left: object, right: object) -> bool:
    le, re = _as_fexpr(left), _as_fexpr(right)
    if le is not None and re is not None:
        return fexpr_eq(le, re)
    lr, rr = _as_rat_value(left), _as_rat_value(right)
    if lr is not None and rr is not None:
        return lr == rr
    # Enclosures are not a proof of equality unless both collapse to the same rational.
    return False


def _as_fexpr(value: object) -> FExpr | None:
    if isinstance(value, TransTheorem):
        return value.value
    if isinstance(value, FExpr):
        return value
    if isinstance(value, RatTheorem):
        return const_fexpr(value.value)
    return None


def _as_rat_value(value: object) -> Ratio | None:
    if isinstance(value, RatTheorem):
        return value.value
    if isinstance(value, FExpr):
        return _as_ratio(value)
    if isinstance(value, TransTheorem):
        return _as_ratio(value.value)
    if isinstance(value, EnclosureTheorem) and value.value.low == value.value.high:
        return value.value.low
    return None


def side_as_trans(term: Term) -> object:
    return eval_trans_result(term)


def trans_order_rule(left: Term, right: Term, left_enc: Enclosure, right_enc: Enclosure, prelude: tuple[str, ...] = ()) -> Rule:
    title = f"{pretty(left)} <= {pretty(right)}"
    if _cmp(left_enc.high, right_enc.low) <= 0:
        return Rule(
            id="math.trans.le",
            layer="base",
            stage="quantity",
            title=title,
            produces=f"identity({title})",
            detail_lines=(*prelude, "The rational enclosures separate, so the comparison holds.", show_enclosure(left_enc), show_enclosure(right_enc)),
        )
    if _cmp(left_enc.low, right_enc.high) > 0:
        return Rule(
            id="math.open",
            layer="base",
            stage="check",
            title=f"{title} is not a theorem",
            produces=f"open({title} is not a theorem)",
            detail_lines=(f"{title} is not a theorem",),
        )
    return Rule(
        id="math.open",
        layer="base",
        stage="check",
        title=f"{title} is not a theorem",
        produces=f"open({title} is not a theorem)",
        detail_lines=("The rational enclosures overlap, so the comparison stays open.",),
    )
