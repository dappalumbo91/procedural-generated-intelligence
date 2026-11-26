"""Build kernel theorems from an ask, then hand them to the rule engine."""

from __future__ import annotations

import re
from dataclasses import replace

from pgi.math.axioms import AXIOMS, REDUCING
from pgi.math.kernel import (
    KernelError,
    NotExact,
    Theorem,
    anchor,
    apply_axiom,
    congr,
    numeral_add,
    numeral_div,
    numeral_mul,
    numeral_pow,
    numeral_neg,
    numeral_sub,
    refl,
    sym,
    trace,
    trans,
)
from pgi.math.order import rules_from_body as order_rules
from pgi.math.rational import equality_rules, eval_rat, order_rule, ratio_rule
from pgi.math.real import eval_real, real_equality_rules, real_order_rule, real_value_rule
from pgi.math.matrix import eval_lin_result, has_matrix, lin_equality_rules, lin_value_rule
from pgi.math.manifold import eval_man_result, has_manifold, man_equality_rules, man_value_rule, side_as_man_or_field
from pgi.math.hilbert import eval_hilbert_result, has_hilbert, hilbert_equality_rules, hilbert_value_rule, side_as_hilbert
from pgi.math.gauge import eval_gauge_result, has_gauge, gauge_equality_rules, gauge_value_rule, side_as_gauge
from pgi.math.lorentz import eval_lorentz_result, has_lorentz, lorentz_equality_rules, lorentz_value_rule, side_as_lorentz
from pgi.math.ode import eval_ode_result, has_ode, ode_equality_rules, ode_value_rule, side_as_ode
from pgi.math.forms import eval_forms_result, has_forms, forms_equality_rules, forms_value_rule, side_as_forms
from pgi.math.killing import eval_killing_result, has_killing, killing_equality_rules, killing_value_rule, side_as_killing
from pgi.math.poly import eval_sym_result, has_symbolic, sym_equality_rules, sym_value_rule
from pgi.math.trans import (
    enclose_term,
    eval_trans_result,
    has_trans,
    side_as_trans,
    trans_equality_rules,
    trans_order_rule,
    trans_value_rule,
)
from pgi.math.quant import is_quantifier, quantifier_rules
from pgi.math.set import (
    contains_set,
    eval_element,
    eval_set,
    member_rule,
    require_set,
    set_equality_rules,
    set_value_rule,
    subset_rule,
)
from pgi.math.syntax import App, Eq, IntLit, Term, Var, closed, parse_equation, parse_term, prepare_ask, pretty, pretty_eq, GE_IFF
from pgi.model import Rule

_OBSERVABLE = re.compile(r"^([a-z_][a-z0-9_]*)=(-?\d+)@(.+)$")
_LIMIT = 32


def rules_from_ask(ask: str, facts: tuple[str, ...]) -> tuple[Rule, ...]:
    prepared = prepare_ask(ask)
    if prepared is None:
        return ()
    kind, body = prepared
    body, order_lines = _rewrite_top_order(body)
    anchors, conflicts = _anchors(facts)
    if kind == "prove" and is_quantifier(body):
        if conflicts:
            return conflicts
        return quantifier_rules(body, anchors, _substitute)
    if kind == "prove" and _has_top_le(body):
        if conflicts:
            return conflicts
        if _mentions_set(body):
            return (_note(f"{body} is not a theorem"),)
        compared = _real_order(body, anchors)
        if compared is not None:
            return _prepend_lines(compared, order_lines)
        compared = _trans_order(body, anchors)
        if compared is not None:
            return _prepend_lines(compared, order_lines)
        compared = _rational_order(body, anchors)
        if compared is not None:
            return _prepend_lines(compared, order_lines)
        return _prepend_lines(order_rules(body, lambda term: _explain(term, anchors)), order_lines)
    if kind == "prove" and _split_relation(body, "in") is not None:
        if conflicts:
            return conflicts
        return _set_member(body, anchors)
    if kind == "prove" and _split_relation(body, "subset") is not None:
        if conflicts:
            return conflicts
        return _set_subset(body, anchors)
    if kind == "prove":
        equation = parse_equation(body)
        if equation is None:
            return ()
        if conflicts:
            return conflicts
        if _has_set(equation.left) or _has_set(equation.right):
            return _set_equation(equation, anchors)
        if has_killing(equation.left) or has_killing(equation.right):
            return _killing_equation(equation, anchors)
        if has_forms(equation.left) or has_forms(equation.right):
            return _forms_equation(equation, anchors)
        if has_ode(equation.left) or has_ode(equation.right):
            return _ode_equation(equation, anchors)
        if has_lorentz(equation.left) or has_lorentz(equation.right):
            return _lorentz_equation(equation, anchors)
        if has_gauge(equation.left) or has_gauge(equation.right):
            return _gauge_equation(equation, anchors)
        if has_hilbert(equation.left) or has_hilbert(equation.right):
            return _hilbert_equation(equation, anchors)
        if has_trans(equation.left) or has_trans(equation.right):
            return _trans_equation(equation, anchors)
        if has_manifold(equation.left) or has_manifold(equation.right):
            return _manifold_equation(equation, anchors)
        if has_matrix(equation.left) or has_matrix(equation.right):
            return _matrix_equation(equation, anchors)
        if has_symbolic(equation.left) or has_symbolic(equation.right):
            return _symbolic_equation(equation, anchors)
        if _has_sqrt(equation.left) or _has_sqrt(equation.right):
            return _real_equation(equation, anchors)
        proved = _prove_equation(equation, anchors)
        if not isinstance(proved, Theorem):
            compared = _rational_equation(equation, anchors)
            if compared is not None:
                return compared
        return _rules_for(proved, equation)
    term = parse_term(body)
    if term is None:
        return ()
    if conflicts:
        return conflicts
    if _has_set(term):
        return _set_value(term, anchors)
    if has_killing(term):
        return _killing_value(term, anchors)
    if has_forms(term):
        return _forms_value(term, anchors)
    if has_ode(term):
        return _ode_value(term, anchors)
    if has_lorentz(term):
        return _lorentz_value(term, anchors)
    if has_gauge(term):
        return _gauge_value(term, anchors)
    if has_hilbert(term):
        return _hilbert_value(term, anchors)
    if has_trans(term):
        return _trans_value(term, anchors)
    if has_manifold(term):
        return _manifold_value(term, anchors)
    if has_matrix(term):
        return _matrix_value(term, anchors)
    if has_symbolic(term):
        return _symbolic_value(term, anchors)
    if _has_sqrt(term):
        return _real_value(term, anchors)
    evaluated = _simplify(term, anchors) if kind == "simplify" else _evaluate(term, anchors)
    return _finish_term(term, anchors, evaluated)


def _mentions_set(text: str) -> bool:
    if "{" in text:
        return True
    padded = f" {text} "
    return " union " in padded or " inter " in padded or " sup " in padded


def _has_top_le(text: str) -> bool:
    depth = 0
    index = 0
    while index < len(text):
        char = text[index]
        if char in "{([":
            depth += 1
        elif char in "}])":
            depth -= 1
        elif depth == 0 and (text.startswith("<=", index) or text.startswith("≤", index)):
            return True
        index += 1
    return False


def _rewrite_top_order(body: str) -> tuple[str, tuple[str, ...]]:
    parts = _split_top_order(body)
    if parts is None:
        return body, ()
    left, op, right = parts
    if op == ">=":
        return f"{right} <= {left}", (GE_IFF,)
    return body, ()


def _split_top_order(text: str) -> tuple[str, str, str] | None:
    found: int | None = None
    op = ""
    depth = 0
    index = 0
    while index < len(text):
        char = text[index]
        if char in "{([":
            depth += 1
        elif char in "}])":
            depth -= 1
        elif depth == 0:
            for symbol in (">=", "<=", ">", "<"):
                if text.startswith(symbol, index):
                    if found is not None:
                        return None
                    found = index
                    op = symbol
                    index += len(symbol)
                    break
            else:
                index += 1
                continue
            continue
        index += 1
    if found is None or op != ">=":
        return None
    return text[:found].strip(), op, text[found + len(op) :].strip()


def _prepend_lines(rules: tuple[Rule, ...], lines: tuple[str, ...]) -> tuple[Rule, ...]:
    if not lines:
        return rules
    return tuple(replace(rule, detail_lines=(*lines, *rule.detail_lines)) for rule in rules)


def _split_relation(body: str, word: str) -> tuple[str, str] | None:
    needle = f" {word} "
    depth = 0
    found: int | None = None
    index = 0
    while index < len(body):
        char = body[index]
        if char in "{([":
            depth += 1
            index += 1
            continue
        if char in "}])":
            depth -= 1
            index += 1
            continue
        if depth == 0 and body.startswith(needle, index):
            if found is not None:
                return None
            found = index
            index += len(needle)
            continue
        index += 1
    if found is None:
        return None
    return body[:found], body[found + len(needle) :]


def _has_set(term: Term) -> bool:
    return contains_set(term)


def _has_collect(term: Term) -> bool:
    if isinstance(term, App):
        return term.op == "collect" or any(_has_collect(arg) for arg in term.args)
    return False


def _set_value(term: Term, anchors: dict[str, Theorem]) -> tuple[Rule, ...]:
    prepared = _real_closed(term, anchors)
    if prepared is None:
        if _has_collect(term):
            return (_note("a free variable stays open"),)
        return ()
    body, prelude = prepared
    from pgi.math.arbitrary import (
        BisectTheorem,
        Cover,
        CoverSupTheorem,
        Interval,
        IntervalSupTheorem,
        RaySupTheorem,
        cover_sup_rule,
        cover_value_rule,
        interpret,
        interval_sup_rule,
        interval_value_rule,
        ray_sup_rule,
        ray_value_rule,
    )
    from pgi.math.collect import CollectForm

    try:
        result, extra = interpret(body)
        lines = (*prelude, *extra)
        if isinstance(result, IntervalSupTheorem):
            return (interval_sup_rule(term, result, lines),)
        if isinstance(result, CoverSupTheorem):
            return (cover_sup_rule(term, result, lines),)
        if isinstance(result, RaySupTheorem | BisectTheorem):
            return (ray_sup_rule(term, result, lines),)
        if isinstance(result, Interval):
            return (interval_value_rule(term, result, lines),)
        if isinstance(result, Cover):
            return (cover_value_rule(term, result, lines),)
        if isinstance(result, CollectForm):
            ruled = ray_value_rule(term, result, lines)
            if ruled is None:
                return (_note("this comprehension is not a finite enumeration"),)
            return (ruled,)
    except NotExact as exc:
        return (_note(str(exc)),)
    return (set_value_rule(term, result, lines),)


def _set_member(body: str, anchors: dict[str, Theorem]) -> tuple[Rule, ...]:
    parts = _split_relation(body, "in")
    if parts is None:
        return (_note(f"{body} is not a theorem"),)
    left = parse_term(parts[0])
    right = parse_term(parts[1])
    if left is None or right is None:
        return (_note(f"{body} is not a theorem"),)
    return _set_relation(left, right, anchors, "in")


def _set_subset(body: str, anchors: dict[str, Theorem]) -> tuple[Rule, ...]:
    parts = _split_relation(body, "subset")
    if parts is None:
        return (_note(f"{body} is not a theorem"),)
    left = parse_term(parts[0])
    right = parse_term(parts[1])
    if left is None or right is None:
        return (_note(f"{body} is not a theorem"),)
    return _set_relation(left, right, anchors, "subset")


def _set_relation(left: Term, right: Term, anchors: dict[str, Theorem], kind: str) -> tuple[Rule, ...]:
    left_ready = _real_closed(left, anchors)
    right_ready = _real_closed(right, anchors)
    shown = f"{pretty(left)} in {pretty(right)}" if kind == "in" else f"{pretty(left)} subset {pretty(right)}"
    if left_ready is None or right_ready is None:
        if _has_collect(left) or _has_collect(right):
            return (_note("a free variable stays open"),)
        return (_note(f"{shown} is not a theorem"),)
    prelude = (*left_ready[1], *right_ready[1])
    try:
        if _has_collect(left_ready[0]) or _has_collect(right_ready[0]):
            from pgi.math.collect import collect_relation_rules

            return collect_relation_rules(kind, left, right, left_ready[0], right_ready[0], prelude)
        if kind == "in":
            element = eval_element(left_ready[0])
            base = require_set(right_ready[0])
            return (member_rule(left, right, element, base, prelude),)
        base_left = require_set(left_ready[0])
        base_right = require_set(right_ready[0])
    except NotExact as exc:
        return (_note(str(exc)),)
    return (subset_rule(left, right, base_left, base_right, prelude),)


def _set_equation(equation: Eq, anchors: dict[str, Theorem]) -> tuple[Rule, ...]:
    left = _set_side(equation.left, anchors)
    right = _set_side(equation.right, anchors)
    if left is None or right is None:
        return (_note(f"{pretty_eq(equation)} is not a theorem"),)
    if isinstance(left[0], str):
        return (_note(left[0]),)
    if isinstance(right[0], str):
        return (_note(right[0]),)
    return set_equality_rules(equation.left, equation.right, left[0], right[0], (*left[1], *right[1]))


def _set_side(term: Term, anchors: dict[str, Theorem]):
    prepared = _real_closed(term, anchors)
    if prepared is None:
        if _has_collect(term):
            return "a free variable stays open", ()
        return None
    body, prelude = prepared
    try:
        if contains_set(body):
            from pgi.math.arbitrary import interpret

            value, extra = interpret(body)
            return value, (*prelude, *extra)
        return eval_real(body), prelude
    except NotExact as exc:
        return str(exc), prelude


def _has_sqrt(term: Term) -> bool:
    if isinstance(term, App):
        return term.op == "sqrt" or any(_has_sqrt(arg) for arg in term.args)
    return False


def _real_closed(term: Term, anchors: dict[str, Theorem]) -> tuple[Term, tuple[str, ...]] | None:
    substituted = _substitute(term, anchors)
    body = substituted.formula.right
    if not closed(body):
        return None
    prelude = trace(substituted) if substituted.rule != "Eq.refl" else ()
    return body, prelude


def _real_value(term: Term, anchors: dict[str, Theorem]) -> tuple[Rule, ...]:
    prepared = _real_closed(term, anchors)
    if prepared is None:
        return ()
    body, prelude = prepared
    try:
        theorem = eval_real(body)
    except NotExact as exc:
        return (_note(str(exc)),)
    return (real_value_rule(term, theorem, prelude),)


def _real_equation(equation: Eq, anchors: dict[str, Theorem]) -> tuple[Rule, ...]:
    left = _real_closed(equation.left, anchors)
    right = _real_closed(equation.right, anchors)
    if left is None or right is None:
        return (_note(f"{pretty_eq(equation)} is not a theorem"),)
    try:
        left_real = eval_real(left[0])
        right_real = eval_real(right[0])
    except NotExact as exc:
        return (_note(str(exc)),)
    return real_equality_rules(equation.left, equation.right, left_real, right_real, (*left[1], *right[1]))


def _real_order(body: str, anchors: dict[str, Theorem]) -> tuple[Rule, ...] | None:
    text = body.replace("≤", "<=")
    if text.count("<=") != 1:
        return None
    left_text, _, right_text = text.partition("<=")
    left = parse_term(left_text)
    right = parse_term(right_text)
    if left is None or right is None or not (_has_sqrt(left) or _has_sqrt(right)):
        return None
    left_closed = _real_closed(left, anchors)
    right_closed = _real_closed(right, anchors)
    if left_closed is None or right_closed is None:
        return (_note(f"{pretty(left)} <= {pretty(right)} is not a theorem"),)
    try:
        left_real = eval_real(left_closed[0])
        right_real = eval_real(right_closed[0])
    except NotExact as exc:
        return (_note(str(exc)),)
    return (real_order_rule(left, right, left_real, right_real, (*left_closed[1], *right_closed[1])),)


def _killing_value(term: Term, anchors: dict[str, Theorem]) -> tuple[Rule, ...]:
    substituted = _substitute(term, anchors)
    body = substituted.formula.right
    prelude = trace(substituted) if substituted.rule != "Eq.refl" else ()
    try:
        result = eval_killing_result(body)
    except NotExact as exc:
        return (_note(str(exc)),)
    return (killing_value_rule(term, result, prelude),)


def _killing_equation(equation: Eq, anchors: dict[str, Theorem]) -> tuple[Rule, ...]:
    left_sub = _substitute(equation.left, anchors)
    right_sub = _substitute(equation.right, anchors)
    left_body = left_sub.formula.right
    right_body = right_sub.formula.right
    prelude = (
        *(trace(left_sub) if left_sub.rule != "Eq.refl" else ()),
        *(trace(right_sub) if right_sub.rule != "Eq.refl" else ()),
    )
    try:
        left_value = side_as_killing(left_body)
        right_value = side_as_killing(right_body)
    except NotExact as exc:
        return (_note(str(exc)),)
    return killing_equality_rules(equation.left, equation.right, left_value, right_value, prelude)


def _forms_value(term: Term, anchors: dict[str, Theorem]) -> tuple[Rule, ...]:
    substituted = _substitute(term, anchors)
    body = substituted.formula.right
    prelude = trace(substituted) if substituted.rule != "Eq.refl" else ()
    try:
        result = eval_forms_result(body)
    except NotExact as exc:
        return (_note(str(exc)),)
    return (forms_value_rule(term, result, prelude),)


def _forms_equation(equation: Eq, anchors: dict[str, Theorem]) -> tuple[Rule, ...]:
    left_sub = _substitute(equation.left, anchors)
    right_sub = _substitute(equation.right, anchors)
    left_body = left_sub.formula.right
    right_body = right_sub.formula.right
    prelude = (
        *(trace(left_sub) if left_sub.rule != "Eq.refl" else ()),
        *(trace(right_sub) if right_sub.rule != "Eq.refl" else ()),
    )
    try:
        left_value = side_as_forms(left_body)
        right_value = side_as_forms(right_body)
    except NotExact as exc:
        return (_note(str(exc)),)
    return forms_equality_rules(equation.left, equation.right, left_value, right_value, prelude)


def _ode_value(term: Term, anchors: dict[str, Theorem]) -> tuple[Rule, ...]:
    substituted = _substitute(term, anchors)
    body = substituted.formula.right
    prelude = trace(substituted) if substituted.rule != "Eq.refl" else ()
    try:
        result = eval_ode_result(body)
    except NotExact as exc:
        return (_note(str(exc)),)
    return (ode_value_rule(term, result, prelude),)


def _ode_equation(equation: Eq, anchors: dict[str, Theorem]) -> tuple[Rule, ...]:
    left_sub = _substitute(equation.left, anchors)
    right_sub = _substitute(equation.right, anchors)
    left_body = left_sub.formula.right
    right_body = right_sub.formula.right
    prelude = (
        *(trace(left_sub) if left_sub.rule != "Eq.refl" else ()),
        *(trace(right_sub) if right_sub.rule != "Eq.refl" else ()),
    )
    try:
        left_value = side_as_ode(left_body)
        right_value = side_as_ode(right_body)
    except NotExact as exc:
        return (_note(str(exc)),)
    return ode_equality_rules(equation.left, equation.right, left_value, right_value, prelude)


def _lorentz_value(term: Term, anchors: dict[str, Theorem]) -> tuple[Rule, ...]:
    substituted = _substitute(term, anchors)
    body = substituted.formula.right
    prelude = trace(substituted) if substituted.rule != "Eq.refl" else ()
    try:
        result = eval_lorentz_result(body)
    except NotExact as exc:
        return (_note(str(exc)),)
    return (lorentz_value_rule(term, result, prelude),)


def _lorentz_equation(equation: Eq, anchors: dict[str, Theorem]) -> tuple[Rule, ...]:
    left_sub = _substitute(equation.left, anchors)
    right_sub = _substitute(equation.right, anchors)
    left_body = left_sub.formula.right
    right_body = right_sub.formula.right
    prelude = (
        *(trace(left_sub) if left_sub.rule != "Eq.refl" else ()),
        *(trace(right_sub) if right_sub.rule != "Eq.refl" else ()),
    )
    try:
        left_value = side_as_lorentz(left_body)
        right_value = side_as_lorentz(right_body)
    except NotExact as exc:
        return (_note(str(exc)),)
    return lorentz_equality_rules(equation.left, equation.right, left_value, right_value, prelude)


def _gauge_value(term: Term, anchors: dict[str, Theorem]) -> tuple[Rule, ...]:
    substituted = _substitute(term, anchors)
    body = substituted.formula.right
    prelude = trace(substituted) if substituted.rule != "Eq.refl" else ()
    try:
        result = eval_gauge_result(body)
    except NotExact as exc:
        return (_note(str(exc)),)
    return (gauge_value_rule(term, result, prelude),)


def _gauge_equation(equation: Eq, anchors: dict[str, Theorem]) -> tuple[Rule, ...]:
    left_sub = _substitute(equation.left, anchors)
    right_sub = _substitute(equation.right, anchors)
    left_body = left_sub.formula.right
    right_body = right_sub.formula.right
    prelude = (
        *(trace(left_sub) if left_sub.rule != "Eq.refl" else ()),
        *(trace(right_sub) if right_sub.rule != "Eq.refl" else ()),
    )
    try:
        left_value = side_as_gauge(left_body)
        right_value = side_as_gauge(right_body)
    except NotExact as exc:
        return (_note(str(exc)),)
    return gauge_equality_rules(equation.left, equation.right, left_value, right_value, prelude)


def _hilbert_value(term: Term, anchors: dict[str, Theorem]) -> tuple[Rule, ...]:
    substituted = _substitute(term, anchors)
    body = substituted.formula.right
    prelude = trace(substituted) if substituted.rule != "Eq.refl" else ()
    try:
        result = eval_hilbert_result(body)
    except NotExact as exc:
        return (_note(str(exc)),)
    return (hilbert_value_rule(term, result, prelude),)


def _hilbert_equation(equation: Eq, anchors: dict[str, Theorem]) -> tuple[Rule, ...]:
    left_sub = _substitute(equation.left, anchors)
    right_sub = _substitute(equation.right, anchors)
    left_body = left_sub.formula.right
    right_body = right_sub.formula.right
    prelude = (
        *(trace(left_sub) if left_sub.rule != "Eq.refl" else ()),
        *(trace(right_sub) if right_sub.rule != "Eq.refl" else ()),
    )
    try:
        left_value = side_as_hilbert(left_body)
        right_value = side_as_hilbert(right_body)
    except NotExact as exc:
        return (_note(str(exc)),)
    return hilbert_equality_rules(equation.left, equation.right, left_value, right_value, prelude)


def _trans_value(term: Term, anchors: dict[str, Theorem]) -> tuple[Rule, ...]:
    substituted = _substitute(term, anchors)
    body = substituted.formula.right
    prelude = trace(substituted) if substituted.rule != "Eq.refl" else ()
    try:
        result = eval_trans_result(body)
    except NotExact as exc:
        return (_note(str(exc)),)
    return (trans_value_rule(term, result, prelude),)


def _trans_equation(equation: Eq, anchors: dict[str, Theorem]) -> tuple[Rule, ...]:
    left_sub = _substitute(equation.left, anchors)
    right_sub = _substitute(equation.right, anchors)
    left_body = left_sub.formula.right
    right_body = right_sub.formula.right
    prelude = (
        *(trace(left_sub) if left_sub.rule != "Eq.refl" else ()),
        *(trace(right_sub) if right_sub.rule != "Eq.refl" else ()),
    )
    try:
        left_value = side_as_trans(left_body)
        right_value = side_as_trans(right_body)
    except NotExact as exc:
        return (_note(str(exc)),)
    return trans_equality_rules(equation.left, equation.right, left_value, right_value, prelude)


def _trans_order(body: str, anchors: dict[str, Theorem]) -> tuple[Rule, ...] | None:
    text = body.replace("≤", "<=")
    if text.count("<=") != 1:
        return None
    left_text, _, right_text = text.partition("<=")
    left = parse_term(left_text)
    right = parse_term(right_text)
    if left is None or right is None:
        return None
    if not (has_trans(left) or has_trans(right)):
        return None
    left_sub = _substitute(left, anchors)
    right_sub = _substitute(right, anchors)
    prelude = (
        *(trace(left_sub) if left_sub.rule != "Eq.refl" else ()),
        *(trace(right_sub) if right_sub.rule != "Eq.refl" else ()),
    )
    try:
        left_enc = enclose_term(left_sub.formula.right)
        right_enc = enclose_term(right_sub.formula.right)
    except NotExact as exc:
        return (_note(str(exc)),)
    return (trans_order_rule(left, right, left_enc, right_enc, prelude),)


def _manifold_value(term: Term, anchors: dict[str, Theorem]) -> tuple[Rule, ...]:
    substituted = _substitute(term, anchors)
    body = substituted.formula.right
    prelude = trace(substituted) if substituted.rule != "Eq.refl" else ()
    try:
        result = eval_man_result(body)
    except NotExact as exc:
        return (_note(str(exc)),)
    return (man_value_rule(term, result, prelude),)


def _manifold_equation(equation: Eq, anchors: dict[str, Theorem]) -> tuple[Rule, ...]:
    left_sub = _substitute(equation.left, anchors)
    right_sub = _substitute(equation.right, anchors)
    left_body = left_sub.formula.right
    right_body = right_sub.formula.right
    prelude = (
        *(trace(left_sub) if left_sub.rule != "Eq.refl" else ()),
        *(trace(right_sub) if right_sub.rule != "Eq.refl" else ()),
    )
    try:
        left_value = side_as_man_or_field(left_body)
        right_value = side_as_man_or_field(right_body)
    except NotExact as exc:
        return (_note(str(exc)),)
    return man_equality_rules(equation.left, equation.right, left_value, right_value, prelude)


def _matrix_closed(term: Term, anchors: dict[str, Theorem]) -> tuple[Term, tuple[str, ...]] | None:
    substituted = _substitute(term, anchors)
    body = substituted.formula.right
    if not closed(body):
        return None
    prelude = trace(substituted) if substituted.rule != "Eq.refl" else ()
    return body, prelude


def _matrix_value(term: Term, anchors: dict[str, Theorem]) -> tuple[Rule, ...]:
    prepared = _matrix_closed(term, anchors)
    if prepared is None:
        return ()
    body, prelude = prepared
    try:
        result = eval_lin_result(body)
    except NotExact as exc:
        return (_note(str(exc)),)
    return (lin_value_rule(term, result, prelude),)


def _matrix_equation(equation: Eq, anchors: dict[str, Theorem]) -> tuple[Rule, ...]:
    left = _matrix_closed(equation.left, anchors)
    right = _matrix_closed(equation.right, anchors)
    if left is None or right is None:
        return (_note(f"{pretty_eq(equation)} is not a theorem"),)
    try:
        left_value = eval_lin_result(left[0])
        right_value = eval_lin_result(right[0])
    except NotExact as exc:
        return (_note(str(exc)),)
    return lin_equality_rules(equation.left, equation.right, left_value, right_value, (*left[1], *right[1]))


def _symbolic_closed(term: Term, anchors: dict[str, Theorem]) -> tuple[Term, tuple[str, ...]] | None:
    substituted = _substitute(term, anchors)
    body = substituted.formula.right
    prelude = trace(substituted) if substituted.rule != "Eq.refl" else ()
    return body, prelude


def _symbolic_value(term: Term, anchors: dict[str, Theorem]) -> tuple[Rule, ...]:
    prepared = _symbolic_closed(term, anchors)
    if prepared is None:
        return ()
    body, prelude = prepared
    try:
        result = eval_sym_result(body)
    except NotExact as exc:
        return (_note(str(exc)),)
    return (sym_value_rule(term, result, prelude),)


def _symbolic_equation(equation: Eq, anchors: dict[str, Theorem]) -> tuple[Rule, ...]:
    left = _symbolic_closed(equation.left, anchors)
    right = _symbolic_closed(equation.right, anchors)
    if left is None or right is None:
        return (_note(f"{pretty_eq(equation)} is not a theorem"),)
    try:
        left_value = eval_sym_result(left[0])
        right_value = eval_sym_result(right[0])
    except NotExact as exc:
        return (_note(str(exc)),)
    return sym_equality_rules(equation.left, equation.right, left_value, right_value, (*left[1], *right[1]))


def _finish_term(term: Term, anchors: dict[str, Theorem], evaluated: Theorem | str | None) -> tuple[Rule, ...]:
    if isinstance(evaluated, Theorem):
        return _rules_for(evaluated, None)
    if isinstance(evaluated, str) and "division by zero" in evaluated:
        return _rules_for(evaluated, None)
    ratio = _ratio_from_term(term, anchors)
    if ratio is not None:
        return (ratio,)
    return _rules_for(evaluated, None)


def _ratio_from_term(term: Term, anchors: dict[str, Theorem]) -> Rule | None:
    substituted = _substitute(term, anchors)
    body = substituted.formula.right
    if not closed(body):
        return None
    prelude = trace(substituted) if substituted.rule != "Eq.refl" else ()
    try:
        theorem = eval_rat(body)
    except NotExact as exc:
        return _note(str(exc))
    return ratio_rule(term, theorem, prelude)


def _rational_equation(equation: Eq, anchors: dict[str, Theorem]) -> tuple[Rule, ...] | None:
    left = _closed_rat(equation.left, anchors)
    right = _closed_rat(equation.right, anchors)
    if left is None or right is None:
        return None
    left_rat, left_lines = left
    right_rat, right_lines = right
    if isinstance(left_rat, str):
        return (_note(left_rat),)
    if isinstance(right_rat, str):
        return (_note(right_rat),)
    return equality_rules(equation.left, equation.right, left_rat, right_rat, (*left_lines, *right_lines))


def _rational_order(body: str, anchors: dict[str, Theorem]) -> tuple[Rule, ...] | None:
    text = body.replace("≤", "<=")
    if text.count("<=") != 1:
        return None
    left_text, _, right_text = text.partition("<=")
    left = parse_term(left_text)
    right = parse_term(right_text)
    if left is None or right is None:
        return None
    left_explained = _explain(left, anchors)
    right_explained = _explain(right, anchors)
    if (
        isinstance(left_explained, Theorem)
        and isinstance(right_explained, Theorem)
        and isinstance(left_explained.formula.right, IntLit)
        and isinstance(right_explained.formula.right, IntLit)
    ):
        return None
    left_rat = _closed_rat(left, anchors)
    right_rat = _closed_rat(right, anchors)
    if left_rat is None or right_rat is None:
        return None
    left_value, left_lines = left_rat
    right_value, right_lines = right_rat
    if isinstance(left_value, str):
        return (_note(left_value),)
    if isinstance(right_value, str):
        return (_note(right_value),)
    return (order_rule(left, right, left_value, right_value, (*left_lines, *right_lines)),)


def _closed_rat(term: Term, anchors: dict[str, Theorem]) -> tuple[RatTheorem | str, tuple[str, ...]] | None:
    substituted = _substitute(term, anchors)
    body = substituted.formula.right
    if not closed(body):
        return None
    prelude = trace(substituted) if substituted.rule != "Eq.refl" else ()
    try:
        return eval_rat(body), prelude
    except NotExact as exc:
        return str(exc), prelude


def _rules_for(theorem: Theorem | str | None, equation: Eq | None) -> tuple[Rule, ...]:
    if isinstance(theorem, str):
        return (_note(theorem),)
    if theorem is None:
        if equation is not None:
            return (_note(f"{pretty_eq(equation)} is not a theorem"),)
        return ()
    right = theorem.formula.right
    title = pretty_eq(theorem.formula)
    lines = trace(theorem)
    if isinstance(right, IntLit):
        return (
            Rule(
                id=f"math.value.{right.n}",
                layer="base",
                stage="quantity",
                title=title,
                produces=f"value({right.n})",
                detail_lines=lines,
            ),
        )
    return (
        Rule(
            id="math.identity",
            layer="base",
            stage="quantity",
            title=title,
            produces=f"identity({title})",
            detail_lines=lines,
        ),
    )


def _note(text: str) -> Rule:
    return Rule(
        id="math.open",
        layer="base",
        stage="check",
        title=text,
        produces=f"open({text})",
        detail_lines=(text,),
    )


def _anchors(facts: tuple[str, ...]) -> tuple[dict[str, Theorem], tuple[Rule, ...]]:
    grouped: dict[str, list[tuple[int, str]]] = {}
    for fact in facts:
        match = _OBSERVABLE.fullmatch(fact.strip())
        if match is None:
            continue
        source = match.group(3).strip()
        if not source:
            continue
        grouped.setdefault(match.group(1), []).append((int(match.group(2)), source))
    anchors: dict[str, Theorem] = {}
    conflicts: list[Rule] = []
    for name, items in grouped.items():
        values = {value for value, _ in items}
        if len(values) > 1:
            for value, source in items:
                conflicts.append(
                    Rule(
                        id=f"math.anchor.{name}.{value}",
                        layer="base",
                        stage="quantity",
                        title=f"{name} = {value}",
                        produces=f"value({value})",
                        detail_lines=(f"observable.anchor source {source}",),
                    )
                )
            continue
        value, source = items[0]
        sources = ", ".join(item_source for _, item_source in items)
        anchors[name] = anchor(name, value, sources)
    return anchors, tuple(conflicts)


def _prove_equation(equation: Eq, anchors: dict[str, Theorem]) -> Theorem | str | None:
    direct = _match_axiom(equation.left, equation.right)
    if direct is not None:
        return direct
    left = _explain(equation.left, anchors)
    right = _explain(equation.right, anchors)
    if isinstance(left, str):
        return left
    if isinstance(right, str):
        return right
    if left is None or right is None:
        return None
    if left.formula.right != right.formula.right:
        return None
    return trans(left, sym(right))


def _simplify(term: Term, anchors: dict[str, Theorem]) -> Theorem | str | None:
    return _explain(term, anchors, allow_same=False)


def _evaluate(term: Term, anchors: dict[str, Theorem]) -> Theorem | str | None:
    return _explain(term, anchors, allow_same=False)


def _explain(term: Term, anchors: dict[str, Theorem], allow_same: bool = True) -> Theorem | str | None:
    substituted = _substitute(term, anchors)
    body = substituted.formula.right
    if closed(body):
        try:
            evaluated = _prove_closed(body)
        except NotExact as exc:
            return str(exc)
        if substituted.rule == "Eq.refl":
            return evaluated
        return trans(substituted, evaluated)
    normalized = _normalize(body)
    if not allow_same and normalized.formula.right == body and substituted.rule == "Eq.refl":
        return None
    if substituted.rule == "Eq.refl":
        return normalized
    return trans(substituted, normalized)


def _match_axiom(left: Term, right: Term) -> Theorem | None:
    for axiom in AXIOMS:
        forward = apply_axiom(axiom, left)
        if forward is not None and forward.formula.right == right:
            return forward
        backward = apply_axiom(axiom, right)
        if backward is not None and backward.formula.right == left:
            return sym(backward)
    return None


def _substitute(term: Term, anchors: dict[str, Theorem], protected: frozenset[str] = frozenset()) -> Theorem:
    if isinstance(term, IntLit):
        return refl(term)
    if isinstance(term, Var):
        if term.name in protected:
            return refl(term)
        return anchors.get(term.name, refl(term))
    if isinstance(term, App) and not term.args:
        return refl(term)
    if isinstance(term, App) and term.op == "collect":
        binder = term.args[0]
        if not isinstance(binder, Var):
            raise KernelError("a comprehension needs a binder")
        domain = _substitute(term.args[1], anchors, protected)
        predicate = _substitute(term.args[2], anchors, protected | {binder.name})
        return congr("collect", (refl(binder), domain, predicate))
    children = tuple(_substitute(arg, anchors, protected) for arg in term.args)
    return congr(term.op, children)


def _prove_closed(term: Term) -> Theorem:
    if isinstance(term, IntLit):
        return refl(term)
    if isinstance(term, Var):
        raise KernelError(f"{term.name} is free")
    children = tuple(_prove_closed(arg) for arg in term.args)
    lifted = congr(term.op, children)
    numerals = []
    for child in children:
        if not isinstance(child.formula.right, IntLit):
            raise KernelError("closed term did not reduce")
        numerals.append(child.formula.right.n)
    step = _numeral(term.op, numerals)
    return trans(lifted, step)


def _numeral(op: str, numerals: list[int]) -> Theorem:
    if op == "neg":
        return numeral_neg(numerals[0])
    if op == "pow":
        return numeral_pow(numerals[0], numerals[1])
    left, right = numerals
    if op == "add":
        return numeral_add(left, right)
    if op == "sub":
        return numeral_sub(left, right)
    if op == "mul":
        return numeral_mul(left, right)
    if op == "div":
        return numeral_div(left, right)
    raise KernelError(op)


def _normalize(term: Term) -> Theorem:
    if not isinstance(term, App):
        return refl(term)
    children = tuple(_normalize(arg) for arg in term.args)
    current = congr(term.op, children)
    for _ in range(_LIMIT):
        head = current.formula.right
        step = _reduce_head(head)
        if step is None:
            return current
        current = trans(current, step)
    raise KernelError("reduction did not settle")


def _reduce_head(term: Term) -> Theorem | None:
    if not isinstance(term, App):
        return None
    for axiom in REDUCING:
        step = apply_axiom(axiom, term)
        if step is not None and step.formula.right != term:
            return step
    return None
