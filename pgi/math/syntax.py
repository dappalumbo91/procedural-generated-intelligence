from __future__ import annotations

import re
from dataclasses import dataclass


class ParseError(Exception):
    pass


@dataclass(frozen=True)
class IntLit:
    n: int


@dataclass(frozen=True)
class Var:
    name: str


@dataclass(frozen=True)
class App:
    op: str
    args: tuple[Term, ...]


Term = IntLit | Var | App


@dataclass(frozen=True)
class Eq:
    left: Term
    right: Term


_WORDS = (
    (re.compile(r"\bdivided by\b"), "/"),
    (re.compile(r"\bplus\b"), "+"),
    (re.compile(r"\bminus\b"), "-"),
    (re.compile(r"\btimes\b"), "*"),
)


def prepare_ask(ask: str) -> tuple[str, str] | None:
    text = ask.strip()
    kind = "value"
    for prefix, name in (
        ("what is ", "value"),
        ("compute ", "value"),
        ("simplify ", "simplify"),
        ("prove ", "prove"),
    ):
        if text.startswith(prefix):
            kind = name
            text = text[len(prefix) :].strip()
            break
    for pattern, symbol in _WORDS:
        text = pattern.sub(symbol, text)
    text = text.replace("≤", "<=").replace("≥", ">=").replace("⩽", "<=").replace("⩾", ">=")
    if not text:
        return None
    return kind, text


def parse_term(text: str) -> Term | None:
    try:
        return _Parser(text).parse_term()
    except ParseError:
        return None


def parse_equation(text: str) -> Eq | None:
    left_text, right_text = _split_eq(text)
    if right_text is None:
        return None
    left = parse_term(left_text)
    right = parse_term(right_text)
    if left is None or right is None:
        return None
    return Eq(left, right)


def pretty(term: Term, parent: int = 0, right: bool = False) -> str:
    if isinstance(term, IntLit):
        return str(term.n)
    if isinstance(term, Var):
        return term.name
    if term.op == "neg":
        inner = pretty(term.args[0], 3, False)
        body = f"(-{inner})"
        return body
    if term.op == "sqrt":
        return f"sqrt({pretty(term.args[0])})"
    if term.op == "root":
        if len(term.args) >= 4 and all(isinstance(arg, IntLit) for arg in term.args):
            from pgi.math.algebraic import show_poly

            values = tuple(arg.n for arg in term.args)
            shown = f"root({show_poly(values[2:-1])}, {values[-1]})"
            coeff_num, coeff_den = values[0], values[1]
            if coeff_num == 1 and coeff_den == 1:
                return shown
            if coeff_num == -1 and coeff_den == 1:
                return f"-{shown}"
            if coeff_den == 1:
                return f"{coeff_num} * {shown}"
            return f"({coeff_num}/{coeff_den}) * {shown}"
        return "root(" + ", ".join(pretty(arg) for arg in term.args) + ")"
    if term.op == "set":
        inner = ", ".join(pretty(arg) for arg in term.args)
        return "{" + inner + "}"
    if term.op == "sup":
        shown = pretty(term.args[0])
        if isinstance(term.args[0], App) and term.args[0].op in {"union", "inter"}:
            shown = f"({shown})"
        return f"sup {shown}"
    if term.op == "collect":
        binder = pretty(term.args[0])
        predicate = pretty(term.args[2])
        domain = term.args[1]
        if isinstance(domain, App) and domain.op == "type":
            return "{" + f"{binder}. {predicate}" + "}"
        return "{" + f"{binder} in {pretty(domain)}. {predicate}" + "}"
    if term.op == "le":
        return f"{pretty(term.args[0])} <= {pretty(term.args[1])}"
    if term.op == "lt":
        return f"{pretty(term.args[0])} < {pretty(term.args[1])}"
    if term.op == "ge":
        return f"{pretty(term.args[0])} >= {pretty(term.args[1])}"
    if term.op == "gt":
        return f"{pretty(term.args[0])} > {pretty(term.args[1])}"
    if term.op == "eq":
        return f"{pretty(term.args[0])} = {pretty(term.args[1])}"
    if term.op == "type":
        return "real"
    if term.op == "not" and term.args:
        return f"not {pretty(term.args[0])}"
    if term.op in {"and", "or", "implies"} and len(term.args) == 2:
        return f"{pretty(term.args[0])} {term.op} {pretty(term.args[1])}"
    if term.op in {"union", "inter"}:
        prec = 1 if term.op == "inter" else 0
        left = pretty(term.args[0], prec, False)
        right_text = pretty(term.args[1], prec, True)
        body = f"{left} {term.op} {right_text}"
        if prec < parent or (right and prec == parent):
            return f"({body})"
        return body
    if term.op == "row":
        return "[" + ", ".join(pretty(arg) for arg in term.args) + "]"
    if term.op == "matrix":
        return "[" + ", ".join(pretty(arg) for arg in term.args) + "]"
    if term.op in {"det", "rank", "inv", "inverse", "transpose", "charpoly", "eigenvalues", "trace", "sin", "cos", "exp", "log", "enclose", "fun", "a", "kretschmann", "einstein", "d", "partial", "diff", "transition", "compose", "jacobian", "identity", "chart", "metric", "embedding", "pullback", "vector", "apply", "dot", "christoffel", "riemann", "ricci", "scalar", "pauli", "sigma", "ket", "bra", "inner", "braket", "dagger", "commutator", "comm", "tensor", "gramschmidt", "spectral", "eigendiag", "hermitian", "unitary", "su2", "su3", "gellmann", "structure", "killing", "jacobi", "fieldstrength", "puregauge", "su2rot", "adjoint", "eta", "gamma", "boost", "so31", "anticommutator", "acomm", "clifford", "so31algebra", "ode", "harmonic", "hydrogen", "exterior", "faraday", "potential", "oneform", "wedge", "coframe", "form", "zeroform", "killingfield", "lie", "position", "momentum", "angmom", "ladder"}:
        inner = ", ".join(pretty(arg) for arg in term.args)
        return f"{term.op}({inner})"
    if term.op == "pow" and len(term.args) == 2:
        left = pretty(term.args[0], 3, False)
        right_text = pretty(term.args[1], 3, True)
        if isinstance(term.args[0], App) and term.args[0].op in {"add", "sub", "mul", "div", "neg", "pow"}:
            left = f"({pretty(term.args[0])})"
        body = f"{left}^{right_text}"
        if 3 < parent or (right and 3 == parent):
            return f"({body})"
        return body
    prec = 2 if term.op in {"mul", "div"} else 1
    symbol = {"add": "+", "sub": "-", "mul": "*", "div": "/"}[term.op]
    left = pretty(term.args[0], prec, False)
    right_text = pretty(term.args[1], prec, True)
    body = f"{left} {symbol} {right_text}"
    if prec < parent or (right and prec == parent):
        return f"({body})"
    return body


def pretty_eq(formula: Eq) -> str:
    return f"{pretty(formula.left)} = {pretty(formula.right)}"


def closed(term: Term, bound: frozenset[str] = frozenset()) -> bool:
    if isinstance(term, IntLit):
        return True
    if isinstance(term, Var):
        return term.name in bound
    if isinstance(term, App) and term.op == "collect" and len(term.args) == 3:
        binder = term.args[0]
        name = binder.name if isinstance(binder, Var) else ""
        return closed(term.args[1], bound) and closed(term.args[2], bound | {name})
    return all(closed(arg, bound) for arg in term.args)


def _split_eq(text: str) -> tuple[str, str | None]:
    depth = 0
    index = 0
    while index < len(text):
        char = text[index]
        if char in "{([":
            depth += 1
        elif char in "})]":
            depth -= 1
        elif char == "<" and index + 1 < len(text) and text[index + 1] == "=":
            index += 2
            continue
        elif char == ">" and index + 1 < len(text) and text[index + 1] == "=":
            index += 2
            continue
        elif char == "=" and depth == 0:
            return text[:index], text[index + 1 :]
        index += 1
    return text, None


class _Parser:
    def __init__(self, text: str) -> None:
        self.tokens = _tokenize(text)
        self.index = 0

    def parse_term(self) -> Term:
        term = self._expr()
        if self.index != len(self.tokens):
            raise ParseError("leftover")
        return term

    def _expr(self) -> Term:
        node = self._inter()
        while self._peek() == "union":
            self._pop()
            rhs = self._inter()
            node = App("union", (node, rhs))
        return node

    def _inter(self) -> Term:
        node = self._arith()
        while self._peek() == "inter":
            self._pop()
            rhs = self._arith()
            node = App("inter", (node, rhs))
        return node

    def _arith(self) -> Term:
        node = self._term()
        while self._peek() in {"+", "-"}:
            op = self._pop()
            rhs = self._term()
            node = App("add" if op == "+" else "sub", (node, rhs))
        return node

    def _term(self) -> Term:
        node = self._unary()
        while self._peek() in {"*", "/"}:
            op = self._pop()
            rhs = self._unary()
            node = App("mul" if op == "*" else "div", (node, rhs))
        return node

    def _unary(self) -> Term:
        token = self._peek()
        if token == "-":
            self._pop()
            inner = self._unary()
            if isinstance(inner, IntLit):
                return IntLit(-inner.n)
            return App("neg", (inner,))
        return self._power()

    def _power(self) -> Term:
        node = self._atom()
        if self._peek() == "^":
            self._pop()
            exp = self._unary()
            return App("pow", (node, exp))
        return node

    def _factor(self) -> Term:
        return self._unary()

    def _atom(self) -> Term:
        token = self._peek()
        if token == "(":
            self._pop()
            node = self._expr()
            if self._pop() != ")":
                raise ParseError("paren")
            return node
        if token == "sqrt":
            self._pop()
            if self._pop() != "(":
                raise ParseError("sqrt")
            node = self._expr()
            if self._pop() != ")":
                raise ParseError("sqrt")
            return App("sqrt", (node,))
        if token == "sup":
            self._pop()
            return App("sup", (self._factor(),))
        if token == "{":
            return self._set()
        if token == "[":
            return self._bracket()
        if token is not None and token.isdigit():
            self._pop()
            return IntLit(int(token))
        if token is not None and token[:1].isalpha() or (token or "").startswith("_"):
            name = token or ""
            if self._ahead(1) == "(":
                self._pop()
                return self._call(name)
            self._pop()
            return Var(name)
        raise ParseError("factor")

    def _set(self) -> Term:
        self._pop()
        if self._peek() == "}":
            self._pop()
            return App("set", ())
        if self._starts_collect():
            return self._collect()
        items: list[Term] = []
        while True:
            items.append(self._arith())
            if self._peek() == ",":
                self._pop()
                continue
            if self._peek() == "}":
                self._pop()
                return App("set", tuple(items))
            raise ParseError("set")

    def _bracket(self) -> Term:
        self._pop()
        if self._peek() == "]":
            raise ParseError("matrix")
        items: list[Term] = []
        while True:
            if self._peek() == "[":
                items.append(self._bracket())
            else:
                items.append(self._arith())
            if self._peek() == ",":
                self._pop()
                continue
            if self._peek() == "]":
                self._pop()
                break
            raise ParseError("matrix")
        if all(isinstance(item, App) and item.op == "row" for item in items):
            return App("matrix", tuple(items))
        if any(isinstance(item, App) and item.op in {"row", "matrix"} for item in items):
            raise ParseError("matrix")
        return App("row", tuple(items))

    def _call(self, name: str) -> Term:
        if self._pop() != "(":
            raise ParseError("call")
        if self._peek() == ")":
            self._pop()
            return App(name, ())
        args: list[Term] = []
        while True:
            token = self._peek()
            if token in {"+", "-"} and self._ahead(1) in {",", ")"}:
                self._pop()
                args.append(Var(token))
            else:
                args.append(self._expr())
            if self._peek() == ",":
                self._pop()
                continue
            if self._peek() == ")":
                self._pop()
                return App(name, tuple(args))
            raise ParseError("call")

    def _starts_collect(self) -> bool:
        token = self._peek()
        if token is None or not (token[:1].isalpha() or token.startswith("_")):
            return False
        return self._ahead(1) in {"in", "."}

    def _collect(self) -> Term:
        binder = self._pop()
        marker = self._pop()
        if binder is None or marker not in {"in", "."}:
            raise ParseError("set")
        if marker == "in":
            domain = self._expr()
            if self._pop() != ".":
                raise ParseError("set")
        else:
            domain = App("type", ())
        predicate = self._predicate()
        if self._pop() != "}":
            raise ParseError("set")
        return App("collect", (Var(binder), domain, predicate))

    def _predicate(self) -> Term:
        return self._implication()

    def _implication(self) -> Term:
        node = self._disjunction()
        if self._peek() == "implies":
            self._pop()
            return App("implies", (node, self._predicate()))
        return node

    def _disjunction(self) -> Term:
        node = self._conjunction()
        while self._peek() == "or":
            self._pop()
            node = App("or", (node, self._conjunction()))
        return node

    def _conjunction(self) -> Term:
        node = self._negation()
        while self._peek() == "and":
            self._pop()
            node = App("and", (node, self._negation()))
        return node

    def _negation(self) -> Term:
        if self._peek() == "not":
            self._pop()
            return App("not", (self._negation(),))
        if self._peek() == "(" and self._paren_holds_predicate():
            self._pop()
            node = self._predicate()
            if self._pop() != ")":
                raise ParseError("set")
            return node
        return self._comparison()

    def _comparison(self) -> Term:
        left = self._expr()
        op = self._peek()
        if op not in {"<=", "=", "<", ">=", ">"}:
            raise ParseError("set")
        self._pop()
        right = self._expr()
        name = {"<=": "le", "=": "eq", "<": "lt", ">=": "ge", ">": "gt"}[op]
        return App(name, (left, right))

    def _paren_holds_predicate(self) -> bool:
        depth = 0
        offset = 0
        while True:
            token = self._ahead(offset)
            if token is None:
                return False
            if token == "(":
                depth += 1
            elif token == ")":
                depth -= 1
                if depth == 0:
                    return False
            elif token in {"<=", "<", "=", ">=", ">", "and", "or", "not", "implies"}:
                return True
            offset += 1

    def _ahead(self, offset: int) -> str | None:
        index = self.index + offset
        if index >= len(self.tokens):
            return None
        return self.tokens[index]

    def _peek(self) -> str | None:
        if self.index >= len(self.tokens):
            return None
        return self.tokens[self.index]

    def _pop(self) -> str | None:
        token = self._peek()
        if token is not None:
            self.index += 1
        return token


def _tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    index = 0
    depth = 0
    while index < len(text):
        char = text[index]
        if char.isspace():
            index += 1
            continue
        if char.isdigit():
            end = index + 1
            while end < len(text) and text[end].isdigit():
                end += 1
            tokens.append(text[index:end])
            index = end
            continue
        if char.isalpha() or char == "_":
            end = index + 1
            while end < len(text) and (text[end].isalnum() or text[end] == "_"):
                end += 1
            tokens.append(text[index:end])
            index = end
            continue
        if char == "{":
            depth += 1
            tokens.append(char)
            index += 1
            continue
        if char == "}":
            depth = max(0, depth - 1)
            tokens.append(char)
            index += 1
            continue
        if char == ".":
            if depth <= 0:
                raise ParseError("character")
            tokens.append(".")
            index += 1
            continue
        if char == "<":
            if depth > 0 and index + 1 < len(text) and text[index + 1] == "=":
                tokens.append("<=")
                index += 2
                continue
            if depth > 0:
                tokens.append("<")
                index += 1
                continue
            raise ParseError("character")
        if char == ">":
            if depth > 0 and index + 1 < len(text) and text[index + 1] == "=":
                tokens.append(">=")
                index += 2
                continue
            if depth > 0:
                tokens.append(">")
                index += 1
                continue
            raise ParseError("character")
        if char == "=":
            if depth <= 0:
                raise ParseError("character")
            tokens.append("=")
            index += 1
            continue
        if char in "+-*/(),[]^":
            tokens.append(char)
            index += 1
            continue
        raise ParseError("character")
    return tokens

GE_IFF = "Lean ge_iff_le: a ≥ b ↔ b ≤ a. Isabelle Orderings.thy defines x ≥ y as y ≤ x."
GT_IFF = "Lean gt_iff_lt: a > b ↔ b < a. Isabelle Orderings.thy defines x > y as y < x."


def rewrite_ge_gt(term: Term) -> tuple[Term, tuple[str, ...]]:
    """Rewrite ≥ and > to ≤ and < by flipping the sides.

    The rewrite is the Lean and Isabelle definition of those symbols, not a
    silent parser swap. It is kept only as that cited identity.
    """

    lines: list[str] = []
    rewritten = _rewrite_ge_gt(term, lines)
    seen: set[str] = set()
    unique: list[str] = []
    for line in lines:
        if line not in seen:
            seen.add(line)
            unique.append(line)
    return rewritten, tuple(unique)


def _rewrite_ge_gt(term: Term, lines: list[str]) -> Term:
    if not isinstance(term, App):
        return term
    args = tuple(_rewrite_ge_gt(arg, lines) for arg in term.args)
    if term.op == "ge" and len(args) == 2:
        lines.append(GE_IFF)
        return App("le", (args[1], args[0]))
    if term.op == "gt" and len(args) == 2:
        lines.append(GT_IFF)
        return App("lt", (args[1], args[0]))
    if args == term.args:
        return term
    return App(term.op, args)
