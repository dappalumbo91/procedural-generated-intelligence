# Results through pgi-0.42.0

Procedural Generated Intelligence (PGI) unfolds answers from compact rules, seeds, and constraints. The store is generative rules, latent seeds, constraint grammars, and context-driven synthesis functions. A prompt arrives, and the kernel saturates the active packs, retracts contradictions, and renders the settled claims at the requested level of detail.

This note records what the folder holds at rule version `pgi-0.42.0`, the goal those rules are for, the architecture that runs them, and the results measured so far. The founding brief is [CONCEPT.md](CONCEPT.md). The reaching goal, with its bars and its five steps, is [GOAL.md](GOAL.md). The running record of each slice is [LOG.md](LOG.md).

## What the kernel holds

The kernel checks closed mathematics and links sourced records. A theorem exists when a checked rule builds it. A measurement enters as `name=value@source`. Two sources that disagree on the same name are retracted together. A bare number is not a measurement. A known mistake stays blocked: re-asserting it contests the board.

In the kernel now:

- The integer ring, under the Lean 4.36 names and the matching Isabelle2025-2 HOL names, with Coq ZArith names recorded beside the equality laws. Exact division only. Non-negative addition and subtraction also reconstruct the result from the digits, and the kernel keeps the step when that reconstruction agrees with the ring.
- Integer order: reflexivity, transitivity, antisymmetry, addition on the left, `Int.le_of_eq`, a true numeral comparison, and the negation of a false one. A compound side is compared after the equality rules reduce it.
- Closed rationals: a reduced fraction, positive denominator, sign on the numerator. Field operations cite the Lean `Rat` operations and the Isabelle `Rat.thy` lemmas. Division by zero stays open.
- A Cauchy continuum for the sequences this kernel can check, from Isabelle `Real.thy`. Constant sequences are the rationals. A positive square root is a bisection sequence with a checked modulus. Order is a strict rational enclosure. Core Lean 4.36 has no `Real`.
- Nested radicals the rules below can see: a tower `base^(odd/2^k)`, a binomial nest, a two-radical sum that denests, the pair `sqrt(sqrt(2) + sqrt(5))` through every further finite outer square root, the nested binomial `sqrt(2 + sqrt(2))` through every further finite outer square root, a two-prime biquadratic under one square root when it does not denest, and a nest times a pair as the square root of the product of those insides.
- Inverses inside the admitted span, including `1 / sqrt(sqrt(2) + sqrt(3))`, which is the conjugate difference of the two nests that denesting already produced. Arithmetic in a finite square-root tower over Q is one checked rule: an element is a vector on the basis of products of the adjoined square roots, multiplication follows `(a + b√d)(c + e√d) = (ac + bed) + (ae + bc)√d`, and the inverse is the conjugate over the norm, taken down the tower and kept only when it multiplies back to 1. A zero, a unit, or a rational factor is scaled in one step, and a product of the same vectors in the same tower is reused. Named ladder levels, a summit, an apex, a shell, and any further finite depth use that one rule.
- Finite sets of those reals. The least upper bound of a nonempty finite set is its maximum.
- Quantifiers over a finite enumeration. Separation over a finite enumeration. Order rays, the set of every real, and two-sided intervals. Nested conjunction, double negation, implication by `imp_conv_disj`, and a disjunction or union of rays when they overlap, touch, or leave a gap. A gapped union is stored as those admitted pieces in order. The complement of a finite set is the open rays and open intervals around its members. The complement of a two-sided interval is the two outer rays. A comparison that is affine in the binder cancels to a standard ray, to UNIV, to the empty set, or to a singleton. A quadratic comparison is settled by its sign chart at the roots the kernel can construct and check, so `{x. x * x <= 2}` is `atLeastAtMost(-sqrt(2), sqrt(2))` and its supremum is `sqrt(2)`. `>=` and `>` are rewritten to `<=` and `<` by flipping the sides, by `ge_iff_le` and `gt_iff_lt`. The supremum of a down-ray is the bound it contains. The supremum of an open upper end is built by the Archimedean bisection in the proof of `complete_real`. The supremum of a bounded gapped union is the upper bound of its right-hand piece. An identically true affine comparison, such as `{x. x <= x + 1}`, is UNIV and is not bounded above.
- Boolean connectives the kernel can settle: a conjunction of two comparisons, the complement of an order ray, and a disjunction of two closed equalities.
- A link board of sourced records in `pgi/corpus/records.py`. Asking about a subject unfolds the record. The record is not a settled answer. Re-asserting a forbidden law contests that law against the record.
- One domain pack: causal path risk from weather, cover, and light.
- GNU Octave cross-checks closed integers inside the exact range of an IEEE double. One test calls it. The binary is taken from `PGI_OCTAVE`, then `octave-cli` on PATH, then the Windows 11.3.0 install path used on this project's machine. The test skips when none of those is found. Octave is not used for rationals, reals, sets, or this root.

## The goal

The reaching goal is a theory of reality in the sense of source code. Physical law is the rule. Observed reality is what that rule does when it runs. The theory is built from sourced information, mathematical proof, and recorded failures.

A checked theorem is the discipline by which a claim settles, and by which information is connected as it is learned. The intelligence is the whole path: seed, rules, retraction, and rendering. The theorem is how a claim is allowed to become settled.

[GOAL.md](GOAL.md) writes the bars a candidate has to meet before it deserves that name. Meeting a bar means a proof or a sourced comparison inside this system.

- Physical: recover gravity and spacetime, including frame-dragging, gravitational waves, and black-hole thermodynamics; recover quantum mechanics and the Standard Model, including the observed particles and masses; give quantum theory and gravity one framework; at macroscopic high-entropy scales recover classical mechanics, the conservation laws, and the thermodynamic arrow.
- Structural: a small axiom list, with measured parameters labeled as measured and derived quantities labeled as derived; Lorentz, gauge, and CPT symmetries in the update or reliably emergent; locality and causality, with entanglement allowed and signaling by entanglement excluded; explicit coarse-graining from the small scale through atoms, chemistry, biology, and cosmology; an unambiguous state space and update.
- Empirical: agreement with the precision record already in hand, plus a new observation that could show the candidate is wrong. An approximation, an effective theory, or a reduction is labeled as an approximation.

The five steps in that document are: name the primitive state; name the evolution or the relation; derive spacetime and the observables; recover known physics as limits; face experiments. The current primitive is the integer, plus a sourced observable. The current relation is the integer ring, integer order, the continuum and set theory this kernel can check, and the retraction of a contradiction. The board is the start of the negative half of the last step: claims that already failed stay failed. Spacetime, general relativity, and the Standard Model are later steps. CODATA recommended values, Particle Data Group listings, gravitational-wave catalogs, atomic-clock comparisons, and the Mercury perihelion residual stay out until a sourced record admits them.

## Architectural design

The four layers in [CONCEPT.md](CONCEPT.md) are the shape of the system.

1. Seed and context anchoring. If the request names a seed, that seed is used. Otherwise `derive_seed` hashes the rule version, the ask, the sorted facts, and the domain with SHA-256 and keeps the first eight bytes as an integer. The same seed and rule version replay the same path. A new seed may reorder independent reasons and pick another legal detail line. A seed does not invent a missing fact, pick a winner in a clash, or turn a hypothesis into a theorem.
2. Layered generative rules. The base pack is the mathematics. The domain pack active in this slice is causal path risk. The detail layer is the level-of-detail text under a claim that has already settled. `rules/local.json` is the editable rule store and ships empty.
3. Constraint solvers. Saturation may derive both sides of a contradiction. `settle` then retracts the clash and every claim that rests only on a retracted atom. The two sides are not blended. Disagreeing measurements of one name are a clash. Known mistakes on the board contest a re-asserted law.
4. On-demand expansion. The claim set is fixed before rendering. Lod 0 is the outline. Lod 1 names the claims. Lod 2 unfolds the detail. A zoom opens one node.

`unfold` in `pgi/engine.py` normalizes the request, loads the active packs and the local store, derives the seed, saturates ready rules, settles, and returns the session. An open note is `math.open`. A check-stage note still leaves the gap "No answer rule fired from the given facts."

The math kernel is sealed in the style of a proof assistant. A real theorem is kept only when `_justified` accepts the form. A forged form raises `KernelError`. Detail text is not itself a proof. Citations used for these roots are `real_sqrt_unique`, `real_sqrt_pow2`, `real_sqrt_ge_zero`, `real_le_lsqrt`, `cauchy`, `eq_Real`, and `inverse_unique`.

The continuum is one expression with a family for each shape the rules can see:

| Family | What it holds |
| --- | --- |
| Constant, term | Rationals and a single square root |
| Tower | One square-free integer to the power `1/2^k` |
| Nest | One positive binomial `a + b*sqrt(n)` under a square root |
| Pair, high, peak, crest, summit, apex | The first six outer depths of `sqrt(sqrt(2) + sqrt(5))` |
| Shell | Every further finite outer depth of that pair, as multiplier data |
| Fold | Every further finite outer depth of one positive binomial nest, as multiplier data |
| Quad | A two-prime biquadratic under one square root when it does not denest |

A new family is a last field with a default empty tuple, so older positional constructors stay on the families they named. Display of a fold wraps the deep, then one `sqrt` for each extra multiplier. The certificate of a further square root squares once and compares the inner radical. It does not raise the power with the depth. A further square root of a nested binomial is not attained at a rational endpoint, so the value stays strictly inside the interval.

The inverse of a sum of two binomial nests on the same radicand is their conjugate difference when the squares of those nests differ by a nonzero rational. The quotient is kept when it multiplies back to 1. A gap that is not a nonzero rational stays outside.

## Results so far

Each line is the post-stamp suite for that slice, from [LOG.md](LOG.md). Times are the runner's, rounded to two decimals.

| Version | What closed | Tests | Time |
| --- | --- | --- | --- |
| pgi-0.4.0 | Integer order | 40 | |
| pgi-0.5.0 | Closed rationals | 47 | about 0.30 s |
| pgi-0.6.0 | Cauchy reals and positive square roots | 56 | about 0.33 s |
| pgi-0.7.0 | Finite sets and the maximum as least upper bound | 64 | about 0.35 s |
| pgi-0.8.0 | Quantifiers over a finite enumeration | 74 | about 0.37 s |
| pgi-0.9.0 | Separation and singleton equality | 84 | about 0.41 s |
| pgi-0.10.0 | Order rays and the set of every real | 95 | about 0.40 s |
| pgi-0.11.0 | Least upper bound of a down-ray | 95 | about 0.40 s |
| pgi-0.12.0 | Archimedean bisection for an open ray | 96 | about 0.44 s |
| pgi-0.13.0 | Two-sided intervals | 97 | about 0.45 s |
| pgi-0.14.0 | Boolean connectives the kernel can settle | 98 | about 0.45 s |
| pgi-0.15.0 | Towers and `sqrt(3 + 2*sqrt(2))` | 99 | about 0.49 s |
| pgi-0.16.0 | Division by a different irrational | 100 | about 0.56 s |
| pgi-0.17.0 | Products of radicals at different levels | 101 | about 0.65 s |
| pgi-0.18.0 | `sqrt(2 + sqrt(2))` as itself | 102 | about 0.78 s |
| pgi-0.19.0 | Denesting `sqrt(sqrt(2) + sqrt(3))` | 103 | about 0.99 s |
| pgi-0.20.0 | `sqrt(sqrt(2) + sqrt(5))` as itself | 104 | about 1.23 s |
| pgi-0.21.0 | `sqrt(sqrt(2 + sqrt(2)))` as itself | 105 | about 1.35 s |
| pgi-0.22.0 through pgi-0.26.0 | Five further named depths of the pair | 106 to 110 | about 1.59 s to about 3.60 s |
| pgi-0.27.0 | Every further finite depth of the pair, as shells | 111 | about 5.22 s |
| pgi-0.28.0 | Every further finite depth of the nested binomial, and the inverse of the denested sum | 112 | about 5.30 s |
| pgi-0.29.0 | Inverse of a further square root of the nested binomial | 113 | about 5.60 s |
| pgi-0.30.0 | `sqrt(1 + sqrt(2) + sqrt(5))` as itself | 114 | about 6.97 s |
| pgi-0.31.0 | A nest times the pair | 115 | about 7.89 s |
| pgi-0.32.0 | Inverse of one plus an admitted radical | 116 | about 10.36 s |
| pgi-0.33.0 | Inverse of one plus a peak | 116 | about 14.10 s |
| pgi-0.34.0 | Inverse of one plus a fold | 116 | about 20.86 s |
| pgi-0.35.0 | Inverse of one plus a crest | 116 | about 87.88 s |
| pgi-0.36.0 | Square-root tower arithmetic | 116 | about 57.85 s |
| pgi-0.37.0 | Boolean connectives and affine upper bounds | 117 | about 49.14 s |
| pgi-0.38.0 | Gapped unions and finite complements | 118 | about 40.28 s |
| pgi-0.39.0 | Quadratic sign charts | 119 | about 37.89 s |
| pgi-0.40.0 | Tower product cache | 119 | about 12.50 s |
| pgi-0.41.0 | Greater-or-equal and greater-than rewrites | 120 | about 13.19 s |
| pgi-0.42.0 | Polynomial sign charts and real algebraic numbers | 124 | about 13.38 s |

`python -m unittest discover -s tests -v` at pgi-0.41.0 finished 120 tests, 0 failures, in 13.186 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH. That is the about 13.19 seconds in the table. One test calls GNU Octave through the portable lookup.

`python -m unittest discover -s tests -v` at pgi-0.42.0 finished 124 tests, 0 failures, in 13.378 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH. That is the about 13.38 seconds in the table. One test calls GNU Octave through the portable lookup.

### Why the two open radicals stayed open, and what closed them

`sqrt(sqrt(sqrt(2 + sqrt(2))))` stayed open because the square-root rule had a branch for one binomial nest and branches for the pair ladder, and no branch for one further square root of that nest. The positive nest has no last outer square root. pgi-0.28.0 stores every further finite depth as fold data and certifies it by one outer square plus the comparison already used for the deep. `sqrt(sqrt(sqrt(2 + sqrt(2))))` is `cauchy(sqrt(sqrt(sqrt(2 + sqrt(2)))))`, and its square is `sqrt(sqrt(2 + sqrt(2)))`. One more square root is the same rule. Its product with `sqrt(sqrt(sqrt(2 - sqrt(2))))` is `sqrt(sqrt(sqrt(2)))`.

`1 / sqrt(sqrt(2) + sqrt(3))` stayed open because the inverse reader expected one nest plus its `sqrt(rad)` partner. The denesting is a sum of two nests, and the second nest is not that partner. Their squares differ by the rational 1, so the inverse is the conjugate difference already admitted by the denesting: `cauchy(-1/2 * sqrt(-2 + 2 * sqrt(3)) + 1/2 * sqrt(2 + 2 * sqrt(3)))`. It multiplies back to 1. The same rule gives the inverse of `sqrt(sqrt(6) + sqrt(2))` as `cauchy(-1/4 * sqrt(-4 + 2 * sqrt(6)) + 1/4 * sqrt(4 + 2 * sqrt(6)))`.

### The inverse of a further fold

The inverse of `sqrt(sqrt(sqrt(2 + sqrt(2))))` stayed outside because the fold inverse asked for the square root of the inverse of the deep, and that inverse is a difference of two deeps. pgi-0.29.0 uses the same field law as the inverse of a deep: the fold times the inverse of its square. A fold times a deep on the same square-free integer is the square root of the core times the square of that deep, by `real_sqrt_unique`. The product is a difference of two folds, and it multiplies back to 1 by `inverse_unique`. `1 / sqrt(sqrt(sqrt(2 + sqrt(2))))` is `cauchy(sqrt(sqrt(2 * sqrt(676 + 478 * sqrt(2)))) - 1/2 * sqrt(2 * sqrt(2 * sqrt(676 + 478 * sqrt(2)))))`. One more square root has the same rule, and it also multiplies back to 1.

### The two-prime biquadratic

`sqrt(1 + sqrt(2) + sqrt(5))` stayed outside because the square-root rule had a branch for a binomial, a branch for a two-radical sum, and no branch for a constant plus two distinct primes. The number is not a square in `Q(sqrt(2), sqrt(5))`: the field norm is -4, which is not a rational square. pgi-0.30.0 stores that nonnegative root as itself, by `real_sqrt_unique`, and its square is `1 + sqrt(2) + sqrt(5)`. The inverse is the root times the inverse of that square, which already lies in the field, and it multiplies back to 1 by `inverse_unique`. When the field norm is a rational square and the relative denesting succeeds, the root is written in the field: `sqrt(8 + 2 * sqrt(2) + 2 * sqrt(5) + 2 * sqrt(10))` is `1 + sqrt(2) + sqrt(5)`. The same family closes `sqrt(1 + sqrt(2) + sqrt(3))`. A rational square factor in the radicand moves into the coefficient: `sqrt(4 + 4 * sqrt(2) + 4 * sqrt(5))` is `2 * sqrt(1 + sqrt(2) + sqrt(5))`.

### A nest times the pair

A nest times a pair stayed outside because multiplication had a rule for two nests on the same radicand and a rule for two pairs on the same pair of radicands, and no rule that mixed a binomial nest with a two-radical pair. For nonnegative insides, `real_sqrt_mult` writes the product as the square root of the product of those insides. `sqrt(2 + sqrt(2)) * sqrt(sqrt(2) + sqrt(5))` is `cauchy(sqrt(2 + 2 * sqrt(2) + 2 * sqrt(5) + sqrt(10)))`. That biquadratic has field norm 36, a rational square, but both relative norms fail to be squares in the intermediate fields, so it does not denest, and pgi-0.31.0 stores the root as itself by `real_sqrt_unique`. The inverse is the root times the inverse of that square, and it multiplies back to 1 by `inverse_unique`.

### Still outside


### Inverse of one plus an admitted radical

The inverse of a rational plus one admitted radical stayed outside when the kernel could invert the radical, or a field element, but not the constant shift. For a form `c + x` with `c` a nonzero rational and `x` exactly one admitted radical, the inverse is `(c - x)` times the inverse of `c^2 - x^2`, when that simpler inverse is already in the kernel and the constructed quotient multiplies back to 1 by `inverse_unique`. `1 / (1 + sqrt(sqrt(2 + sqrt(2))))` is `cauchy(1 - sqrt(2) + sqrt(2 + sqrt(2)) - sqrt(4 + 2 * sqrt(2)) - sqrt(sqrt(2 + sqrt(2))) + sqrt(2 * sqrt(2 + sqrt(2))) - sqrt(sqrt(20 + 14 * sqrt(2))) + sqrt(2 * sqrt(20 + 14 * sqrt(2))))`. The same rule closes `1 / (1 + sqrt(sqrt(2) + sqrt(5)))`, `1 / (1 + sqrt(sqrt(sqrt(2) + sqrt(5))))`, `1 / (1 + sqrt(1 + sqrt(2) + sqrt(5)))`, and `1 / (1 + sqrt(2 + 2 * sqrt(2) + 2 * sqrt(5) + sqrt(10)))`. A fold times a nest on the same radicand is written by associating through the already closed deep-times-nest product: `sqrt(sqrt(sqrt(2 + sqrt(2)))) * sqrt(2 + sqrt(2))` is `cauchy(sqrt(sqrt(2 * sqrt(58 + 41 * sqrt(2)))))`.


### Inverse of one plus a peak

`1 / (1 + sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))` stayed outside because a peak times a pair, or a peak times a high, was not in the kernel, so the last multiply in the shifted inverse could not be formed. A peak times a pair is the square root of the already closed high-times-pair product, associated so the field element does not split: `sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))) * sqrt(sqrt(2) + sqrt(5))` is `cauchy(sqrt(sqrt(sqrt(229 * sqrt(2) + 145 * sqrt(5)))))`. A peak times a high is the square root of the high times the square of that high: `sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))) * sqrt(sqrt(sqrt(2) + sqrt(5)))` is `cauchy(sqrt(sqrt(sqrt(17 * sqrt(2) + 11 * sqrt(5)))))`. The shifted inverse then closes `1 / (1 + sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))`, and the quotient multiplies back to 1 by `inverse_unique`.


### Inverse of one plus a fold

`1 / (1 + sqrt(sqrt(sqrt(2 + sqrt(2)))))` stayed outside because a deep times a fold was not in the kernel, so the constructed inverse could not be multiplied back by `1` plus that fold. That product is the same mixed rule already used for a fold times a deep. With it in place, the shifted inverse multiplies back to 1 by `inverse_unique`. The closed form is `cauchy(1 - sqrt(2) + sqrt(2 + sqrt(2)) - sqrt(4 + 2 * sqrt(2)) + sqrt(sqrt(2 + sqrt(2))) - sqrt(2 * sqrt(2 + sqrt(2))) + sqrt(sqrt(20 + 14 * sqrt(2))) - sqrt(2 * sqrt(20 + 14 * sqrt(2))) - sqrt(sqrt(sqrt(2 + sqrt(2)))) + sqrt(2 * sqrt(sqrt(2 + sqrt(2)))) - sqrt(sqrt(sqrt(20 + 14 * sqrt(2)))) + sqrt(2 * sqrt(sqrt(20 + 14 * sqrt(2)))) - sqrt(sqrt(2 * sqrt(58 + 41 * sqrt(2)))) + sqrt(2 * sqrt(2 * sqrt(58 + 41 * sqrt(2)))) - sqrt(sqrt(2 * sqrt(676 + 478 * sqrt(2)))) + sqrt(2 * sqrt(2 * sqrt(676 + 478 * sqrt(2)))))`. Further finite depths of that fold close by the same rule.


### Inverse of one plus a crest

`1 / (1 + sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))` stayed outside because a crest times a pair, a high, or a peak was not in the kernel. A crest times a pair is the square root of the already closed peak-times-pair product, associated so the field element does not split: `sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))) * sqrt(sqrt(2) + sqrt(5))` is `cauchy(sqrt(sqrt(sqrt(sqrt(40681 * sqrt(2) + 25729 * sqrt(5))))))`. A crest times a high is `cauchy(sqrt(sqrt(sqrt(sqrt(229 * sqrt(2) + 145 * sqrt(5))))))`. A crest times a peak is `cauchy(sqrt(sqrt(sqrt(sqrt(17 * sqrt(2) + 11 * sqrt(5))))))`. The shifted inverse then closes `1 / (1 + sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))`, and the quotient multiplies back to 1 by `inverse_unique`.

`1 / (1 + ...)` from the summit downward on the pair ladder stays outside, because the products of a summit with a crest, a peak, a high, or a pair are not yet in the kernel. A boolean connective the kernel cannot settle, a set whose upper-bound predicate the kernel cannot decide, a nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero stay outside. A negative radicand stays open. Division by zero stays open.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Isabelle `real_sqrt_minus` and `inverse (0::real) = 0` stay refused.

### Boolean connectives and affine upper bounds

A nested conjunction is associated and met, so `{x. 1 <= x and x <= 3 and x <= 4}` is `atLeastAtMost(1, 3)`. `not not` is `double_compl`, so `{x. not not x <= 2}` is `atMost(2)`. `imp_conv_disj` rewrites implication: `{x. x <= 1 implies x <= 3}` is `univ`. A disjunction or a union of two rays is one admitted set when they overlap or touch: `{x. x <= 1 or x <= 3}` is `atMost(3)`, and `{x. x <= 3 or 1 <= x}` is `univ`. A comparison that is affine in the binder cancels to a standard ray: `{x. x <= x + 1}` is `univ` and is not bounded above, `{x. 2 * x <= x + 1}` is `atMost(1)`, `{x. 2 * x = x + 1}` is `{1}`, and `{x. x + 1 <= x}` is empty.

A union of two rays that leaves a gap, such as `{x. x <= 1 or 3 <= x}`, stays outside. The complement of a nonempty finite set, such as `{x. not x = 2}`, stays outside. A predicate that is not affine in the binder, such as `{x. x * x <= 2}`, stays outside the bisection. A nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero, stay outside. A negative radicand stays open. Division by zero stays open.

### Gapped unions and finite complements

A union of admitted rays or intervals that leaves a gap is stored as those pieces in order, by `Un_iff`. `{x. x <= 1 or 3 <= x}` is `atMost(1) union atLeast(3)`. `{x. x <= 3} union {x. 5 <= x}` is `atMost(3) union atLeast(5)`. `{x. x <= 1 or x = 3}` is `atMost(1) union set({3})`. A meet keeps the pieces that survive: `{x. x <= 1 or 3 <= x} inter {x. x <= 4}` is `atMost(1) union atLeastAtMost(3, 4)`. If the right-hand piece is bounded above, the supremum is that upper bound: `sup {x. x <= 1 or (2 <= x and x <= 3)}` is 3. If the right-hand piece is an up-ray, the union is not bounded above.

The complement of a finite set is the open down-ray before the least member, the open interval between consecutive members, and the open up-ray after the greatest member, by `linorder_neq_iff` and `Compl_insert`. `{x. not x = 2}` is `lessThan(2) union greaterThan(2)`. `{x. not (x = 1 or x = 2)}` is `lessThan(1) union greaterThanLessThan(1, 2) union greaterThan(2)`. The complement of a closed interval is the two outer rays: `{x. not (1 <= x and x <= 3)}` is `lessThan(1) union greaterThan(3)`.

### Quadratic sign charts

A comparison that is a polynomial of degree two in the binder is settled by a sign chart at the roots the kernel can construct and check. The difference of the two sides is formed, the discriminant is built, and each root is verified by evaluating the polynomial to zero. The sign at a midpoint is checked against the leading coefficient. `{x. x * x <= 2}` is `atLeastAtMost(-sqrt(2), sqrt(2))`. `{x. x * x < 2}` is `greaterThanLessThan(-sqrt(2), sqrt(2))`. `{x. 2 <= x * x}` is `atMost(-sqrt(2)) union atLeast(sqrt(2))`. `{x. x * x = 2}` is `set({-sqrt(2), sqrt(2)})`. A factored quadratic such as `{x. (x - 1) * (x - 3) <= 0}` is `atLeastAtMost(1, 3)`. A quadratic with no real roots and a positive leading coefficient, such as `{x. x * x + 1 <= 0}`, is empty. `sup {x. x * x <= 2}` is `cauchy(sqrt(2))`. Membership follows the admitted interval or cover.


### Tower product cache

Tower multiplication still follows `(a + b√d)(c + e√d) = (ac + bed) + (ae + bc)√d`, and a constructed inverse is still kept only when it multiplies back to 1. A zero, a unit, or a rational factor is now scaled in one step instead of recursing through every layer, and a product of the same coordinate vectors in the same tower is reused. The admitted forms are unchanged. The full suite still runs before every push.


### Greater-or-equal and greater-than

`>=` and `>` are accepted in a predicate and rewritten to `<=` and `<` by flipping the sides. The rewrite is Lean `ge_iff_le` and `gt_iff_lt`, and Isabelle Orderings.thy defines `x ≥ y` as `y ≤ x` and `x > y` as `y < x`. `{x. x >= 2}` is `atLeast(2)`. `{x. x > 2}` is `greaterThan(2)`. `{x. x * x >= 2}` is `atMost(-sqrt(2)) union atLeast(sqrt(2))`. `{x. x * x > 2}` is `lessThan(-sqrt(2)) union greaterThan(sqrt(2))`. `{x in {1, 2, 3}. x >= 2}` is `{2, 3}`. `{x. not x >= 2}` is `lessThan(2)`. `prove 5 >= 2` is `le(2,5)`.

### Polynomial sign charts and real algebraic numbers

A comparison that is a polynomial in the binder, with rational coefficients, is settled by a checked sign chart rather than a degree-by-degree rule. Yun square-free factorization and a Sturm sequence isolate the real roots. A root expressible as a nested square root is kept in that form. Otherwise the root is stored as a checked real algebraic number: a primitive irreducible integer polynomial together with the index of that real root among the real roots, ordered increasingly. A Sturm sequence isolates the root in a rational interval that contains exactly one real root, and the number is kept only when that count, the irreducibility of the polynomial, and the index all check. The sign chart is kept only when it is checked at rational test points and at every constructed root. The original leading sign of the polynomial is preserved, so an inequality is not flipped when the primitive representative is taken.

`{x. x * x * x <= 2}` is `atMost(root(x^3 - 2, 1))`. `{x. x * x * x < 2}` is `lessThan(root(x^3 - 2, 1))`. `{x. x * x * x >= 2}` is `atLeast(root(x^3 - 2, 1))`. `{x. x * x * x = 2}` is `set({root(x^3 - 2, 1)})`. `sup {x. x * x * x <= 2}` is `cauchy(root(x^3 - 2, 1))`. `{x. x * x * x * x <= 2}` is `atLeastAtMost(-sqrt(sqrt(2)), sqrt(sqrt(2)))`. `{x. (x * x * x) - x <= 0}` is `atMost(-1) union atLeastAtMost(0, 1)`. `{x. (x * x - 2) * (x - 3) <= 0}` is `atMost(-sqrt(2)) union atLeastAtMost(sqrt(2), 3)`. `{x. x * x * x + x + 1 = 0}` is `set({root(x^3 + x + 1, 1)})`. A polynomial with no real roots and a positive leading coefficient, such as `{x. x * x * x * x + 1 <= 0}`, is empty. Membership follows the admitted ray, interval, or cover.

A quadratic whose coefficients are not all rational still uses the quadratic formula when the discriminant can be formed as a nonnegative radicand. A quadratic whose discriminant the kernel cannot form as a nonnegative radicand, such as `{x. x * x <= sqrt(sqrt(2)) + sqrt(sqrt(3))}`, stays outside. A polynomial whose coefficients are not all rational and whose degree is greater than two, such as `{x. x * x * x <= sqrt(2)}`, stays outside the bisection. A nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero, stay outside. A negative radicand stays open. Division by zero stays open.


### Polynomials with algebraic coefficients

A comparison that is a polynomial in the binder, whose coefficients are rational, tower elements, or real algebraic numbers, is settled by one general checked method rather than a case-by-case rule. Each coefficient is converted to a rational or a real algebraic number. A resultant takes the polynomial down to a rational eliminant: the field norm when the coefficients lie in one number field, or an eliminant that is a multiple of the norm when several algebraic coefficients are treated as independent symbols. Yun square-free factorization and a Sturm sequence isolate the candidate real roots of that eliminant. A candidate is kept only when an exact vanishing check shows it is a root of the original polynomial. Isolating intervals are refined until every sign in the chart is certain. A root expressible as a nested square root is kept in that form. Otherwise it is stored as a checked real algebraic number. A quadratic still uses the quadratic formula when the discriminant can be formed; when that radicand cannot be formed, the same general method covers it.

`{x. x * x <= sqrt(sqrt(2)) + sqrt(sqrt(3))}` is `atLeastAtMost(root(x^32 - 20 * x^24 - 666 * x^16 - 3860 * x^8 + 1, 1), root(x^32 - 20 * x^24 - 666 * x^16 - 3860 * x^8 + 1, 4))`. `{x. x * x * x <= sqrt(2)}` is `atMost(root(x^6 - 2, 2))`. `{x. x * x * x < sqrt(2)}` is `lessThan(root(x^6 - 2, 2))`. `{x. x * x * x >= sqrt(2)}` is `atLeast(root(x^6 - 2, 2))`. `sup {x. x * x * x <= sqrt(2)}` is `cauchy(root(x^6 - 2, 2))`. `{x. (x * x - 2) * (x - sqrt(2)) <= 0}` is `atMost(-sqrt(2)) union set({sqrt(2)})`.

A polynomial whose resultant would exceed the kernel's degree limit stays outside. A nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero, stay outside. A sum of two nested binomials of the same square-free integer stays that sum: `sqrt(2 + sqrt(2)) + sqrt(2 - sqrt(2))` is not rewritten as `sqrt(4 + 2 * sqrt(2))`. A negative radicand stays open. Division by zero stays open.


### Sums of conjugate nested binomials

A sum of conjugate nested binomials of the same square-free integer is rewritten by squaring. The square is formed in the tower, the nonnegative square root is taken, and the identity is kept only when the candidate multiplies back to that square and `real_sqrt_unique` applies. When the numbers are algebraic, an exact algebraic comparison is required as well. `sqrt(2 + sqrt(2)) + sqrt(2 - sqrt(2))` is `sqrt(4 + 2 * sqrt(2))`. `sqrt(2 + sqrt(2)) - sqrt(2 - sqrt(2))` is `sqrt(4 - 2 * sqrt(2))`. `sqrt(3 + 2 * sqrt(2)) + sqrt(3 - 2 * sqrt(2))` is `2 * sqrt(2)`.

### Exact signs for nonnegativity and nonzero divisors

A sign that an isolating enclosure cannot decide is settled by a Sturm or algebraic sign when the form is a rational, a tower element, or a real algebraic number. A radicand whose sign is certified positive has a square root, stored as a nested radical when one can be formed, otherwise as a checked real algebraic number. A divisor whose sign is certified nonzero has an inverse, checked by multiplying back to 1. `0 <= -2 + sqrt(sqrt(2)) + sqrt(sqrt(3))` holds. `sqrt(sqrt(sqrt(2)) + sqrt(sqrt(3)))` is `root(x^32 - 20 * x^24 - 666 * x^16 - 3860 * x^8 + 1, 4)`. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` and `inverse (0::real) = 0` stay refused.

### Boolean sides of settled charts

A boolean connective whose sides the kernel can settle individually is composed by the Collect lemmas, rather than left outside. Each side is reduced first: a polynomial or algebraic-coefficient comparison becomes its checked sign chart, and a ray stays a ray. Conjunction is intersection, disjunction is union, negation is complement, and implication is rewritten to `not P or Q`. `{x. x * x <= 2 and 0 <= x}` is `atLeastAtMost(0, sqrt(2))`. `{x. not x * x <= 2}` is `lessThan(-sqrt(2)) union greaterThan(sqrt(2))`. `{x. x * x <= 2 or x * x * x <= 2}` is `atMost(sqrt(2))`. `{x. x * x <= 2 implies x <= 3}` is `univ`. `{x. x * x * x <= sqrt(2) and 0 <= x}` is `atLeastAtMost(0, root(x^6 - 2, 2))`. `sup {x. x * x <= 2 and 0 <= x}` is `cauchy(sqrt(2))`. A boolean connective whose sides the kernel cannot settle stays outside.

### CODATA 2022 constants on the board

The first sourced numbers are the CODATA 2022 recommended values, P. J. Mohr, D. B. Newell, B. N. Taylor, and E. Tiesinga, Rev. Mod. Phys. 97, 025002 (2025), as the NIST Reference on Constants served them on 2026-11-25. They live in `pgi/corpus/measured.py`. Each value is the text NIST prints, and the rational is parsed from that text. A value NIST prints with a trailing ellipsis, such as `hbar`, is refused by the parser and is not stored.

The seven SI defining constants are exact rationals: `Δν_Cs = 9 192 631 770 Hz`, `c = 299 792 458 m s^-1`, `h = 6.626 070 15 e-34 J Hz^-1`, `e = 1.602 176 634 e-19 C`, `k = 1.380 649 e-23 J K^-1`, `N_A = 6.022 140 76 e23 mol^-1`, `K_cd = 683 lm W^-1`. The measured core set carries its standard uncertainty: `G = 6.674 30(15) e-11 m^3 kg^-1 s^-2`, `α = 7.297 352 5643(11) e-3`, `1/α = 137.035 999 177(21)`, `m_e = 9.109 383 7139(28) e-31 kg`, `m_p = 1.672 621 925 95(52) e-27 kg`, `m_n = 1.674 927 500 56(85) e-27 kg`, the three MeV energy equivalents, `m_p/m_e = 1836.152 673 426(32)`, `R_∞ = 10 973 731.568 157(12) m^-1`, `a_0 = 5.291 772 105 44(82) e-11 m`, `μ_0 = 1.256 637 061 27(20) e-6 N A^-2`, `ε_0 = 8.854 187 8188(14) e-12 F m^-1`, and `G_F/(ħc)^3 = 1.166 3787(6) e-5 GeV^-2`. That is 22 quantities and 21 new board records; `c` stays `anchor.c_si`.

The tests check the stored numbers against each other in exact rational arithmetic, never against a number this system derived. `e^2/(2 ε_0 h c)` agrees with `α` inside the combined standard uncertainty. So do `2 α h/(e^2 c)` with `μ_0`, `μ_0 ε_0 c^2` with 1, `1/α` with the inverse, `α^2 m_e c/(2h)` with `R_∞`, `α/(4π R_∞)` with `a_0` at both ends of a Machin enclosure of π, `m_p/m_e` with the ratio, and each `m c^2/e` with its MeV equivalent. Moving `ε_0` by ten standard uncertainties fails the `α` check. Asserting `derived(codata2022.h)` contests the board.

### Exact rational matrices

A matrix over the rationals is a rectangular array of reduced fractions. Addition, multiplication, and transpose use those exact entries. A determinant is the Bareiss value after clearing denominators, and through degree five the cofactor expansion has to agree. `det([[1, 2], [3, 4]])` is `-2`. `det([[1, 2, 3], [4, 5, 6], [7, 8, 10]])` is `-3`. `det([[1/2, 0], [0, 1/3]])` is `1/6`. A rank is kept only when a pivot minor has a nonzero determinant and every other row is the corresponding linear combination of the pivot rows. `rank([[1, 2], [3, 4]])` is `2`. `rank([[1, 2], [2, 4]])` is `1`. An inverse is kept only when both products are the identity. `inv([[1, 2], [3, 4]])` is `[[-2, 1], [3/2, -1/2]]`. A singular inverse and a non-square determinant stay open. An entry that is not an exact rational stays open. Characteristic polynomials and eigenvalues are still ahead.

### PDG 2026 masses, couplings, and the CKM fit

The Particle Data Group numbers are from the 2026 edition, F. Takahashi et al. (Particle Data Group), Int. J. Mod. Phys. A 41, 2630011 (2026). It is the current edition, so it is used rather than 2024 or 2025. Masses come from the summary-table rows of the PDG API database shipped as the `pdg` Python package 2026.0, data release 2026-05-30, as PDG displays them, and each record cites its pdgLive node. `α_s(m_Z)`, `G_F`, and the MSbar weak-mixing angle come from Table 1.1, Physical Constants, revised May 2026. The CKM values are the global unitarity fit of review 12, revised March 2026, Eq. (12.26) and Eq. (12.27).

`m_W = 80.3625 ± 0.0077 GeV`. `m_Z = 91.1879 ± 0.0020 GeV`. The measured ratio `m_W/m_Z = 0.88136 ± 0.00015`. `m_H = 125.13 ± 0.11 GeV`. The direct `m_t = 172.60 ± 0.27 GeV`. `m_e = 0.51099895069 ± 0.00000000016 MeV`, `m_μ = 105.6583755 ± 0.0000023 MeV`, `m_τ = 1776.93 ± 0.09 MeV`. `α_s(m_Z) = 0.1180(9)`. `G_F/(ħc)^3 = 1.166 378 5(6) e-5 GeV^-2`. `sin^2 θ̂_W(m_Z)` in MSbar is `0.231 22(6)`. The quark masses carry the label PDG prints: `m_u = 2.16 ± 0.07 MeV`, `m_d = 4.70 ± 0.07 MeV`, and `m_s = 92.9 ± 0.7 MeV` are MSbar at `μ = 2 GeV`. `m_c(m_c) = 1.2729 ± 0.0045 GeV` and `m_b(m_b) = 4.186 ± 0.006 GeV` are MSbar running masses. All five are printed with CL = 90%, so they are stored as that, not as one standard deviation. The CKM fit keeps its asymmetric errors as printed: `λ = 0.22517 ± 0.00068`, `A = 0.826 +0.017 −0.015`, `ρ̄ = 0.1576 +0.0092 −0.0091`, `η̄ = 0.3556 +0.0071 −0.0069`, the nine magnitudes from `|V_ud| = 0.97431 ± 0.00016` to `|V_tb| = 0.999115 +0.000029 −0.000034`, and `J = 3.16 +0.13 −0.11 × 10^-5`. That is 30 new quantities and 30 new records.

The concise forms `0.1180(9)`, `1.166 378 5(6) e-5`, and `0.231 22(6)` are parsed and checked against the stored value and uncertainty. `m_W/m_Z` from the two masses agrees with the measured ratio. The PDG electron mass equals the CODATA MeV equivalent. PDG `G_F` and CODATA `G_F` differ in the last digit and agree inside the uncertainty. Every row and column of the CKM magnitudes squares to 1 inside the propagated uncertainty, and `λ` equals `|V_us|`.

### Mercury's perihelion residual and the gravitational-wave events

The Mercury residual is G. M. Clemence, The Relativity Effect in Planetary Motions, Rev. Mod. Phys. 19, 361 (1947), Table II, read from a scan of the journal pages. The observed motion of Mercury's perihelion at 1850, referred to the moving equinox, is `5599.74 ± 0.41` arcseconds per Julian century. The sum of general precession and every Newtonian planetary and oblateness contribution is `5557.18 ± 0.85`. The difference is `42.56 ± 0.94`. Clemence's errors are probable errors: a half-probability range widened by his judgment of the largest systematic error. They are stored under that name and are not converted. The relativity effect Clemence prints beside the residual is a theory value and is not stored. The test checks that observed minus computed is exactly the residual, and that 0.41 and 0.85 in quadrature give 0.94 at his printed places. Asserting `law(newtonian_perturbations_explain_mercury_perihelion)` contests the residual.

GW150914 is from GWTC-1, B. P. Abbott et al., Phys. Rev. X 9, 031040 (2019), Table III, read through the GWOSC event API and checked against the paper. Source-frame `m_1 = 35.6 +4.7 −3.1`, `m_2 = 30.6 +3.0 −4.4`, chirp mass `28.6 +1.7 −1.5`, and final mass `63.1 +3.4 −3.0` solar masses; final spin `0.69 +0.05 −0.04`; radiated energy `3.1 ± 0.4` solar masses times c²; `χ_eff = −0.01 +0.12 −0.13`; `d_L = 440 +150 −170` Mpc; `z = 0.09 ± 0.03`. These are medians with 90% credible intervals. The chirp mass from the two median masses falls inside the chirp-mass interval, and the medians close the energy budget exactly: `35.6 + 30.6 − 63.1 = 3.1`.

The speed-of-gravity bound is B. P. Abbott et al., ApJL 848, L13 (2017), Eq. (2): `−3 × 10^-15 ≤ (v_GW − v_EM)/v_EM ≤ +7 × 10^-16`. The record keeps its conditions: the observed 1.74 ± 0.05 s delay, D = 26 Mpc, an emission lag from 0 to 10 s, and the paper's note that exotic models widen the window. No central value is stored. That is 12 new quantities, one bound, and 13 new records.

### Planck and Rayleigh–Jeans as stored formulas

`pgi/corpus/formulas.py` stores a sourced expression in the notation of its source. A stored formula is not a theorem and is not derived here. The board kinds gain `stored_formula`, with standing `stored` or `failed`.

`formula.planck_spectrum` is Planck, Ueber das Gesetz der Energieverteilung im Normalspectrum, Annalen der Physik 309, 553–563 (1901), equation (12) on page 561: `u = (8 π h ν^3 / c^3) / (exp(h ν / (k θ)) − 1)`. It was read from the proofread Wikisource transcription of the journal pages, because the Wiley page needs a login. Claiming `derived(planck_spectrum)` contests the board.

`formula.rayleigh_jeans` is Planck's equation (8) on page 560, `u = 8 π ν^2 U / c^3`, with the classical equipartition energy `U = k θ`: `u = 8 π ν^2 k θ / c^3`. Its standing is failed at high frequency. Rayleigh's 1900 and Jeans' 1905 pages were not reachable without a login, so their own notation is not copied; the failure itself stays on `known.rayleigh_jeans`. Asserting `law(rayleigh_jeans_at_high_frequency)` contests the board.

The tests evaluate both stored texts with the CODATA `h`, `k`, and `c`. At `h ν / k θ = 10^-4` they agree to better than one part in a thousand. At `h ν / k θ = 20` Rayleigh–Jeans is more than a million times Planck. Doubling the frequency cutoff multiplies the Rayleigh–Jeans total by exactly 8 with no limit, while Planck's density falls by more than 25 orders of magnitude between `h ν / k θ = 10` and `80`.

### Characteristic polynomials and real eigenvalues

The characteristic polynomial of a square rational matrix is `det(tI - A)`, monic in t. It is kept only when Faddeev–LeVerrier agrees with interpolation through those determinants, the polynomial annihilates the matrix, and it matches the determinant at an extra point. `charpoly([[1, 2], [3, 4]])` is `x^2 - 5 * x - 2`. `charpoly([[0, -1], [1, 0]])` is `x^2 + 1`. `charpoly([[2, 0, 0], [0, 3, 0], [0, 0, 5]])` is `x^3 - 10 * x^2 + 31 * x - 30`. Real eigenvalues are the real roots of that polynomial, isolated by the algebraic-number kernel. `eigenvalues([[0, 1], [1, 0]])` is `{-1, 1}`. `eigenvalues([[0, 2], [1, 0]])` is `{-sqrt(2), sqrt(2)}`. `eigenvalues([[1, 2], [3, 4]])` is `{5/2 - 1/2 * sqrt(33), 5/2 + 1/2 * sqrt(33)}`. A characteristic polynomial with no real root, such as `eigenvalues([[0, -1], [1, 0]])`, yields the empty set. A non-square matrix has no characteristic polynomial here.

### Modern Mercury perihelion and PPN fits

Clemence's 1947 table stays on the board. Beside it are the modern ephemeris numbers, each in the notation and with the uncertainty label of its paper.

Park, Folkner, Konopliv, Williams, Smith, and Zuber, Astron. J. 153, 121 (2017), fitted JPL's ephemeris with MESSENGER ranging from 2011 March to 2014 August. The total precession rate of Mercury's perihelion is `575.3100 ± 0.0015` arcseconds per Julian century, measured along Mercury's mean orbit plane. That frame has no general precession, so the number is not comparable to Clemence's `5599.74`. With `γ` held at the Cassini value as a considered parameter, `β − 1 = (−2.7 ± 3.9) × 10^-5` and the solar `J2 = (2.25 ± 0.09) × 10^-7`. The abstract and conclusions print `−2.7`. Table 1 prints `−2.6`. The abstract value is stored and the difference is written on the record. The paper names no confidence level, so the kind is `uncertainty as printed, level not stated`. The computed contributions in its Table 3, the relativistic ones included, are not stored.

Pitjeva and Pitjev, Mon. Not. R. Astron. Soc. 432, 3431 (2013), fitted EPM2011 to about 780 thousand observations. Mercury's additional perihelion precession beyond every modeled effect is `−0.020 ± 0.030` mas/yr, with the uncertainty called σ. That is the modern residual. The same paper gives `β − 1 = −0.00002 ± 0.00003` and `γ − 1 = +0.00004 ± 0.00006` at 3σ. Bertotti, Iess, and Tortora, Nature 425, 374 (2003), give `γ − 1 = (2.1 ± 2.3) × 10^-5` from Cassini.

The tests check that the EPM2011 residual sits inside its own uncertainty, that the two `β` intervals overlap, that the Cassini and EPM2011 `γ` intervals overlap, and that each `β − 1` and `γ − 1` interval contains zero. That is 7 new quantities and 7 new records.

### Cosmology: Planck 2018, SH0ES, DESI DR2, and the CMB temperature

The cosmological numbers are on the board as measured anchors. Each one is a fit inside a named model or a named data combination, and the record says which.

Planck 2018 VI, A&A 641, A6 (2020), Table 2, the baseline column TT,TE,EE+lowE+lensing, 68% intervals in base-ΛCDM: `H0 = 67.36 ± 0.54` km/s/Mpc, `Ω_b h^2 = 0.02237 ± 0.00015`, `Ω_c h^2 = 0.1200 ± 0.0012`, `100θ_MC = 1.04092 ± 0.00031`, `τ = 0.0544 ± 0.0073`, `ln(10^10 A_s) = 3.044 ± 0.014`, `n_s = 0.9649 ± 0.0042`, `Ω_Λ = 0.6847 ± 0.0073`, `Ω_m = 0.3153 ± 0.0073`, `Ω_m h^2 = 0.1430 ± 0.0011`, `σ_8 = 0.8111 ± 0.0060`, and `S_8 = 0.832 ± 0.013`. SH0ES, Riess et al., ApJL 934, L7 (2022), baseline Cepheid-SN result: `H0 = 73.04 ± 1.04` km/s/Mpc. DESI DR2, Phys. Rev. D 112, 083515 (2025), Eqs. (25)–(28): `w0 = −0.42 ± 0.21`, `wa = −1.75 ± 0.58` for DESI+CMB; `w0 = −0.838 ± 0.055`, `wa = −0.62 +0.22 −0.19` with Pantheon+; `w0 = −0.667 ± 0.088`, `wa = −1.09 +0.31 −0.27` with Union3; `w0 = −0.752 ± 0.057`, `wa = −0.86 +0.23 −0.20` with DESY5. Fixsen, ApJ 707, 916 (2009): `T_0 = 2.72548 ± 0.00057 K`. SH0ES and Fixsen do not name a confidence level in the text that was read, so none is assigned.

The tests check that Planck's printed `Ω_m + Ω_Λ` is exactly 1, that `Ω_m h^2` agrees with `Ω_m (H0/100)^2`, and that `σ_8 (Ω_m/0.3)^0.5` agrees with `S_8`. The SH0ES and Planck H0 values differ by more than four combined uncertainties. Both records stay on the board and neither is retracted, because they are different measurements, not two sources for one name. In every DESI combination `w0` is above −1 and `wa` is below 0. No dark-energy model is stored as a claim. That is 22 new quantities and 22 new records.

### Multivariate polynomials, rational functions, and exact partial derivatives

A multivariate polynomial over the rationals is a finite sum of reduced coefficients times monomials. A rational function is a reduced quotient: the numerator and denominator are divided by their primitive GCD, and a zero denominator stays open. A partial derivative is termwise on a polynomial, or the quotient rule on a rational function, kept only when that identity multiplies back. Mixed partials of a polynomial commute, checked exactly. `d(x^2, x)` is `2 * x`. `d(x^2 * y + 3 * x, x)` is `2 * x * y + 3`. `d(x^2 + 2 * x * y + y^2, x)` is `2 * x + 2 * y`. `d(d(x^3 * y^2, x), y)` is `6 * x^2 * y`. `(x^2 - 1) / (x - 1)` is `x + 1`. `(x^2 - y^2) / (x - y)` is `x + y`. `d((x^2 + 1) / (x + 1), x)` is `(x^2 + 2 * x - 1) / (x^2 + 2 * x + 1)`. `d(1 / x, x)` is `-1 / x^2`. `x / x` is `1`. `2^3` is `8`. `(1/2)^2` is `1/4`. A zero denominator and `0^0` stay open.

### Charts, transition maps, and Jacobians

A transition map is a tuple of reduced rational functions between charts, kept only when the two-way composition is the identity on the source coordinates. The Jacobian is the matrix of exact partial derivatives. Composition is substitution, kept only when the chain rule holds identically: `J(g ∘ f)` equals `J(g)` along `f`, times `J(f)`. A Jacobian determinant is kept when cofactor expansions along the first row and the first column agree. An inverse is kept only when both products are the identity. `compose(transition(s2, south, north), transition(s2, north, south))` is `identity(u, v)`. The same holds for the stereographic charts on the circle, the affine charts on the real projective line, and the linear charts `xy`, `uv`, and `pq` on the plane, which also satisfy the cocycle identity. `jacobian(transition(r2, xy, uv))` is `[[1, 1], [1, -1]]`, and its determinant is `-2`. `det(jacobian(transition(s2, north, south)))` is `-1 / (u^2 + v^2)^2`. An unknown chart, including an angular chart that would need trigonometric functions, stays open. A composition that is not an inverse pair is not the identity.

### NIST ASD first ionization energies, Na to Kr

The first ionization energies of the 26 neutral atoms from sodium to krypton are on the board. They come from the same source as the H to Ne rows: NIST ASD version 5.12, Ionization Energies Data, queried in eV with the uncertainty, configuration, level, and bibliography columns. The Na-Kr query URL is on every record. Values and uncertainties are kept as served. Na `5.13907696 ± 0.00000025`, Mg `7.646236 ± 0.000004`, Al `5.985769 ± 0.000003`, Si `8.15168 ± 0.00003`, P `10.486686 ± 0.000015`, S `10.3600167 ± 0.0000014`, Cl `12.967633 ± 0.000016`, Ar `15.7596119 ± 0.0000005`. K `4.34066373 ± 0.00000009`, Ca `6.1131549210 ± 0.0000000005`, Sc `6.56149 ± 0.00006`, Ti `6.828120 ± 0.000012`, V `6.746187 ± 0.000021`, Cr `6.76651 ± 0.00004`, Mn `7.4340380 ± 0.0000012`, Fe `7.9024681 ± 0.0000012`, Co `7.88101 ± 0.00012`, Ni `7.639878 ± 0.000017`, Cu `7.726380 ± 0.000004`, Zn `9.394197 ± 0.000006`, Ga `5.9993020 ± 0.0000012`, Ge `7.899435 ± 0.000012`, As `9.78855 ± 0.00025`, Se `9.752368 ± 0.000006`, Br `11.81381 ± 0.00006`, Kr `13.9996055 ± 0.0000020` eV.

None of the 26 values is in brackets or parentheses, so all are evaluated experimental values in ASD's own terms. The level of the uncertainty column is not stated, as before. The tests check every row's uncertainty, and that the alkali metal is lowest and the noble gas highest in each period, as printed. They also check Calcium's `0.0000000005` eV uncertainty exactly. The ionization rows no longer share a generic key, so an ask about one element links only that element. That is 26 new records, and the board now holds 36 ASD rows.

### AME2020 atomic masses and binding energies, starter set

A starter set from the 2020 atomic mass evaluation is on the board. The sources are Huang, Wang, Kondev, Audi, and Naimi, Chinese Phys. C 45, 030002 (2021), and Wang, Huang, Kondev, Audi, and Naimi, Chinese Phys. C 45, 030003 (2021). Part I states that all uncertainties are one standard deviation, so these are standard uncertainties. The printed table in Part II rounds some values and writes `a` for uncertainties below 0.5 eV, and it points to the AMDC ASCII file for full precision. The values here are from that file, `mass.mas20`, as written.

For n, ¹H, ²H, ³H, ³He, ⁴He, ¹²C, ¹⁶O, ⁵⁶Fe, ⁵⁸Fe, ⁶²Ni, and ²⁰⁸Pb the board holds the atomic mass in µu and the mass excess in keV. It also holds the binding energy per nucleon in keV for every nuclide with A ≥ 2. A few values: n `1 008664.91590 ± 0.00047` µu, ¹H `1 007825.031898 ± 0.000014` µu, ⁴He `4 002603.25413 ± 0.00016` µu, and ¹²C `12 000000.0` µu. AME prints the ¹²C uncertainty as 0.0, and since 1 u = m(¹²C)/12 it is stored as exact. Binding energy per nucleon: ²H `1112.2831(2)`, ⁴He `7073.9156(2)`, ¹²C `7680.1446(2)`, ¹⁶O `7976.2072(2)`, ⁵⁶Fe `8790.3563(48)`, ⁵⁸Fe `8792.2534(55)`, ⁶²Ni `8794.5555(69)`, ²⁰⁸Pb `7867.4530(55)` keV. AME2020's `1 u = 931 494.10242 ± 0.00028 keV` is stored beside them. ⁵⁸Fe was added to the requested set because it sits between ⁵⁶Fe and ⁶²Ni at the peak.

The tests check the following. ¹²C is exactly 12 000 000 µu with mass excess 0. ⁶²Ni, ⁵⁸Fe, and ⁵⁶Fe are the top three in binding energy per nucleon, in that order and within 5 keV of each other, as printed. Every `B/A` agrees with `(1/A)[Z Δ(¹H) + N Δ(n) − Δ]` from the stored mass excesses, and every atomic mass agrees with `A + Δ/u` within its printed uncertainty. That is 35 new records.

### PDG 2026 light hadron masses

The light hadron masses are on the board from the PDG 2026 database (pdg package 2026.0), each with its PDG summary label and scale factor. π± `139.57039 ± 0.00018` MeV, OUR FIT, S = 1.8; PDG's OUR AVERAGE of 139.57039 ± 0.00017 is noted. π⁰ `134.9768 ± 0.0005`, fit. K± `493.677 ± 0.015`, fit, S = 2.8. K⁰ `497.611 ± 0.013`, fit. η `547.862 ± 0.017`. ω(782) `782.66 ± 0.13`, S = 2.0. Λ `1115.683 ± 0.006`, fit. Proton `938.27208943 ± 0.00000029`, PDG's evaluation taken from CODATA 2022. Neutron `939.5654219 ± 0.0000005`. The measured difference `m_n − m_p = 1.2933325 ± 0.0000004` MeV is stored as its own average, not computed.

ρ(770) is a broad resonance, and PDG gives several averages by charge and reaction. The stored one is the neutral e⁺e⁻ value, `775.26 ± 0.23` MeV, and the record lists the other three: 763.0 ± 1.2, 769.6 ± 0.8, and 769.0 ± 0.9. For Δ(1232) PDG prints `1230 TO 1232 TO 1234` MeV, an estimated range, not a statistical uncertainty. It gets a new kind, `PDG estimated range`, and is stored as 1232 with the half-width of the printed range.

The tests check the following. `m_n − m_p` agrees with the difference of the two PDG masses, and with CODATA's to 10⁻⁶ MeV. PDG's proton mass is the CODATA 2022 value exactly. π± is above π⁰, K⁰ above K±, and n above p, and the eleven masses run in the expected order, as printed. Δ(1232) carries a range kind. A `pion mass` ask links both pions with nothing retracted. That is 12 new records.

### Gravity tests: binary pulsars, Gravity Probe B, VLBI, and the spread in G

The strong-field and solar-system gravity tests are on the board as measured anchors, along with the measured values of G that CODATA 2022 combines.

Hulse–Taylor PSR B1913+16, Weisberg and Huang, ApJ 829, 55 (2016), Eq. (23): the intrinsic orbital decay over the GR prediction is `0.9983 ± 0.0016`. The paper calls this within about 1σ but does not name the level of the ±, so none is assigned. Double Pulsar PSR J0737−3039A/B, Kramer et al., Phys. Rev. X 11, 041050 (2021), Table V, observed over GR: `Ṗb 0.999963(63)`, `ω̇ 1.000015(26)`, `s 1.00009(18)`, `r 1.0016(34)`, `γ_E 1.00012(25)`. The paper states the `Ṗb` test as 1.3 × 10^−4 at 95% confidence. Table V names no level, so the records say so. Each ratio is the paper's own comparison. No GR prediction is stored on the board.

Gravity Probe B, Everitt et al., Phys. Rev. Lett. 106, 221101 (2011), Table II, joint result: geodetic `−6601.8 ± 18.3` mas/yr and frame-dragging `−37.2 ± 7.2` mas/yr. These are 1σ by the paper's statement, the square roots of the total covariance diagonal. The paper's GR predictions, −6606.1 and −39.2, are written in the notes and not stored. VLBI light deflection, Lambert and Le Poncin-Lafitte, A&A 529, A70 (2011), solution S5 from more than seven million group delays: `γ = 0.99992 ± 0.00012`, a least-squares formal error with no level named. The A&A page is behind a bot check. The abstract and paper came from the HAL open copy, hal-03785812.

Big G. CODATA 2022 Table XXX lists the 16 input values of G, all 1σ, unchanged since 2018. They run from LENS-14 `6.671 91(99)` and HUST-05 `6.672 22(87)` up to BIPM-01 `6.675 59(27)` and BIPM-14 `6.675 54(16)` × 10^−11 m³ kg⁻¹ s⁻². Each is stored with its laboratory, method, and the three correlations in the caption. CODATA's recommended `6.674 30(15)` uses an expansion factor of 3.9.

The tests check the following. Both pulsar `Ṗb` ratios sit within twice their printed uncertainty of 1, and the Double Pulsar's is more than 25 times tighter. Every Table V ratio matches its concise form. Gravity Probe B's frame-dragging is more than 5σ from zero. VLBI `γ − 1` agrees with Cassini. For G, the normalized residuals computed from the stored values give exactly CODATA's printed 7.75 for BIPM-14 and −6.80 for JILA-18. Those are the extremes, and the 3.9 factor brings every residual to 2 or less. The spread of the 16 values is more than 20 times the recommended uncertainty. That is 25 new records.

### Atomic spectroscopy: hydrogen 1S–2S, Lamb shift, 21 cm, H-alpha, and muonic hydrogen

Hydrogen's best-measured lines are on the board as measured anchors.

The 1S–2S frequency comes from Parthey et al., Phys. Rev. Lett. 107, 203001 (2011), arXiv:1107.3101: `f = 2 466 061 413 187 035(10)` Hz, the hyperfine centroid, 4.2 × 10^−15. The paper's Table I heads its column "σ - uncertainty", so the record is a standard uncertainty. The MPQ remeasurement by Matveev et al. (2013), `2 466 061 413 187.018(11)` kHz, is taken from CODATA 2022 Table XI, which lists both as input data with relative standard uncertainties.

The n = 2 Lamb shift, ΔE_H(2P1/2 − 2S1/2)/h, is also taken from CODATA 2022 Table XI: York, Bezginov et al., Science 365, 1007 (2019), `1 057 829.8(3.2)` kHz, and Harvard, Lundeen and Pipkin (1981), `1 057 845.0(9.0)` kHz. Science is paywalled. Bezginov's abstract prints only the proton radius it implies, `0.833 ± 0.010` fm, so the interval comes through CODATA. The concise reader now accepts a decimal point inside the parentheses, as in `(3.2)`, which gives the uncertainty in the value's own units.

The 21 cm line comes from Hellwig, Vessot, Levine, Zitzewitz, Allan, and Glaze, IEEE Trans. Instrum. Meas. IM-19, 200 (1970), NIST's scan: `ν_H = 1 420 405 751.768 ± 0.002` Hz, one sigma by the abstract. The scanned abstract's exponent reads "2 X 10-2 Hz". The Conclusions print ±0.002 Hz, and that is what is stored, with a note.

Balmer H-alpha comes from the NIST ASD 5.12 lines query for H I, 656.2–656.3 nm in air. The n = 2–3 blend is observed at `656.279 ± 0.003` nm, with relative intensity 500000, and its Ritz value is `656.2819 ± 0.0007` nm. The strongest fine-structure component, 2p ²P3/2 − 3d ²D5/2, is observed at `656.285175 ± 0.000007` nm. ASD names no level, so none is assigned.

Muonic hydrogen comes from Antognini et al., Science 339, 417 (2013), via the PubMed abstract, which states one standard deviation. It gives `ν_s = 54611.16(1.05)` GHz and `ν_t = 49881.35(65)` GHz, the charge radius `r_E = 0.84087(39)` fm, and the Zemach radius `r_Z = 1.082(37)` fm. The magnetic radius `0.87(6)` fm is printed in the abstract but not stored. The experimental muonic Lamb shift, `E_L = 202.3706(23)` meV, is taken from CODATA 2022 Table XIV (CREMA-13), because the paper body is paywalled.

The tests check the following. Parthey and Matveev differ by 17 Hz, inside 2σ combined. The 1S–2S frequency over `(3/4) R∞ c` with the reduced mass sits between α³ and α² of 1. York and Harvard agree within 2σ but not 1σ. `c/ν_H` is between 21.10 and 21.11 cm. The H-alpha blend and its Ritz value agree. The strongest component is within 3 printed uncertainties of the blend, and the reduced-mass Balmer wavelength in vacuum is longer than the air Ritz value by less than 0.2 nm. The muonic `r_E` agrees with CODATA 2022 `r_p` and with PDG 2026, and with York's `0.833 ± 0.010` fm. The muonic and H-alpha asks link exactly their records. That is 13 new records.

### Nuclear constants: deuteron binding, alpha-particle mass, nucleon magnetic moments

The nuclear constants come from CODATA 2022 as measured anchors. All are 1σ and served by the NIST constants table, except one: the deuteron binding energy has no table entry. It is printed in the CODATA 2022 paper, Sec. II.B, as `E_B(d) = 2224.566 40(38)` keV, from the Kessler et al. (1999) neutron-capture gamma-ray wavelength, and it is cited to that sentence.

The deuteron mass is stored in kg, u, and MeV. The alpha-particle mass is `6.644 657 3450(21) × 10^−27` kg, `4.001 506 179 129(62)` u, and `3727.379 4118(12)` MeV. The nuclear magneton is stored. The proton and neutron magnetic moments are stored in J/T and in nuclear magnetons, along with CODATA's own neutron-to-proton ratio, `−0.684 979 35(16)`.

The tests check the following. `m_n c² + m_p c² − m_d c²` reproduces `E_B(d)` within the combined uncertainty, and so does twice the AME2020 binding energy per nucleon of ²H. The alpha mass in kg, converted with the exact c and e, gives the MeV entry. AME2020's keV-per-u is the CODATA 2018 conversion, and against CODATA 2022 it reads the alpha about 5 eV low, more than 3σ. A test records that edition gap. The AME2020 ⁴He atomic mass, minus the alpha and two electrons, leaves a 79 eV electron binding energy. That matches the ASD He I ionization energy plus 4 Ry within 3 AME uncertainties. Each moment equals its ratio times μ_N, and μ_n/μ_p computed both ways equals CODATA's ratio entry. The "nucleon magnetic moment" ask links exactly the five moment records. That is 13 new records.

### Metrics, tangent vectors, and curvature

A metric is a symmetric matrix of reduced rational functions on a chart. A tangent vector is a tuple of rational components, kept only when it annihilates constants, reproduces its components on the coordinates, and satisfies the Leibniz rule. A pullback is `J^T g J` along the map, kept only when pullback along the identity is the original metric and pullback is functorial on the plane atlas. The unit 2-sphere metric in a stereographic chart is the pullback of the Euclidean 3-metric through the inverse stereographic embedding, kept only when that embedding lands on `X^2 + Y^2 + Z^2 = 1` and the pullback equals `4 / (1 + ρ^2)^2` times the identity. `metric(e2)` is `[[1, 0], [0, 1]]`. `metric(e2, uv)` is `[[1/2, 0], [0, 1/2]]`. `metric(minkowski2)` is `[[-1, 0], [0, 1]]`. `metric(minkowski2, uv)` is `[[0, -1/2], [-1/2, 0]]`. `apply(vector(e2, 1, 0), x^2)` is `2 * x`.

Christoffel symbols, Riemann, Ricci, and the scalar curvature are computed from the metric by the standard formulas. The inverse metric is kept only when both products are the identity. The Levi-Civita connection is kept only when it is torsion-free and metric-compatible. The Riemann symmetries and both Bianchi identities are checked identically. `christoffel(metric(e2))`, `riemann(metric(e2))`, and `ricci(metric(e2))` vanish, and `scalar(metric(e2))` and `scalar(metric(minkowski2))` are `0`. `scalar(metric(s2, north))` is `2`, and `ricci(metric(s2, north))` equals the metric. An unknown chart, including an angular chart that would need trigonometric functions, stays open.
### Stefan–Boltzmann and Wien constants: exact, printed truncated

CODATA 2022 lists the Stefan–Boltzmann constant and both Wien displacement constants as exact, because they are fixed by h, c, and k. The table prints only leading digits followed by "...": σ = `5.670 374 419... × 10^−8` W m^−2 K^−4, b = `2.897 771 955... × 10^−3` m K, and b′ = `5.878 925 757... × 10^10` Hz K^−1. A rounded number would be invented, so the board stores the digits exactly as printed. A new uncertainty kind, `exact, printed truncated`, reads such a print as the half-open interval from the printed digits to one more unit in the last place. `value` refuses these records, and `truncation_bounds` returns the interval. `parse_decimal` still refuses "...". The records are definitional anchors and forbid `derived(id)`, like the other exact constants.

The tests derive all three in exact rationals. `2π⁵k⁴/(15h³c²)`, evaluated at both ends of a Machin π enclosure to 30 digits, sits inside σ's printed interval. For Wien, the roots of `x = 5(1 − e^−x)` and `x = 3(1 − e^−x)` are enclosed to 2 × 10^−13. The enclosures are checked with Taylor bounds on `e^x` and the sign of `x − n + n e^−x` at both ends. `hc/(k x₅)` then sits inside b's interval, and `x₃ k/h` inside b′'s. That also confirms CODATA truncates these prints rather than rounding them. That is 3 new records.

### Finite-dimensional Hilbert space over Q(i)

Finite-dimensional inner product spaces have exact entries in Q(i) or Q(√d, i). An inverse is kept only when it multiplies back to 1. The inner product is ⟨u, v⟩ = u† v, conjugate-linear in the first argument, and is kept only when it is conjugate-symmetric, linear in the second argument, and positive definite. Gram–Schmidt is kept only when the result is orthonormal: `gramschmidt([[1, 1], [0, 1]])` is `[[1, 0], [0, 1]]`. A matrix is Hermitian only when A† = A, and unitary only when both A† A and A A† are the identity. The Pauli matrices satisfy [σ_i, σ_j] = 2 i ε_ijk σ_k, checked exactly, so `commutator(pauli(x), pauli(y))` is `2 * i * pauli(z)`, and `pauli(x)^2` is the identity. A 2×2 Hermitian spectral decomposition is kept only when H = U D U† with U unitary, D real diagonal, and eigenvector norms positive rationals, so the normalization stays in Q(√d, i). `spectral(pauli(x)) * eigendiag(pauli(x)) * dagger(spectral(pauli(x)))` is `pauli(x)`. Tensor products are the Kronecker product, and `(A ⊗ B)(C ⊗ D) = (AC) ⊗ (BD)` holds. `ket(0)`, `ket(1)`, `ket(+)`, and `ket(-)` are unit vectors; |+⟩ and |−⟩ are eigenvectors of σ_x, and `inner(ket(+), ket(-))` is `0`. `i * i` is `-1`. A polynomial derivative in the variable i is not treated as the imaginary unit: `d(i^2, i)` is `2 * i`. A 3×3 spectral decomposition, a Hermitian matrix whose eigenvector norm is not rational, a linearly dependent Gram–Schmidt input, and mixing two different square-free radicands stay open.

### Lie algebras and exact gauge transformations

The su(2) generators are T_a = σ_a / 2 and satisfy [T_a, T_b] = i ε_abc T_c, so `commutator(su2(x), su2(y))` is `i * su2(z)`. The su(3) generators are T_a = λ_a / 2 for the Gell-Mann matrices. Their structure constants are checked, including `structure(su3, 4, 5, 8)` = `1/2 * sqrt(3)`. The Jacobi identity holds for both algebras. The Killing form, computed from the structure constants, agrees with 2n tr(T_a T_b): it is `2 δ_ab` for su(2) and `3 δ_ab` for su(3).

A U(1) field strength is F = ∂_x A_y − ∂_y A_x, with exact rational partials, and is invariant under A ↦ A + dλ. `fieldstrength(u1, x * y, x)` is `-x + 1`. An SU(2) field strength of constant components is F = [A_x, A_y]. A constant special unitary U acts by A ↦ U A U†, and F transforms covariantly as F ↦ U F U†. The trace of F² is invariant. A connection built as U dU† from the rational SU(2) rotation in x + y is pure gauge, and `fieldstrength(puregauge(su2rot))` is the zero matrix. An SU(3) gauge transformation on a connection, and an SU(2) gauge transformation that is not a constant special unitary matrix or that rational rotation, stay open.

### Chemistry: atomic weights, diatomic molecules, pKa and pKw, enthalpies of formation

Chemistry data is on the board, each value as printed with the uncertainty its source states. Where a source prints none, the board says so. A new kind, `no uncertainty printed`, stores no number in that case. A second new kind, `IUPAC standard atomic weight uncertainty`, carries CIAAW's own wording: normal materials are expected to lie in the given interval "with great certitude". That is not a standard uncertainty.

The IUPAC 2021 standard atomic weights for H through Kr come from the CIAAW table. The page is headed 2024, but its only 2024 changes are Gd, Lu, and Zr. Twenty-four elements have a value with an uncertainty, such as Fe `55.845(2)` and Co `58.933 194(3)`. Twelve have an interval, such as H `[1.007 84, 1.008 11]` and Ar `[39.792, 39.963]`. Those are stored as intervals with no central value. The g, m, and r footnotes are kept on each record.

The diatomic molecules come from two NIST sources. Huber–Herzberg ground-state `r_e` via the NIST WebBook: H₂ `0.74144`, N₂ `1.097685`, O₂ `1.20752`, CO `1.128323`, H³⁵Cl `1.274552` Å, all printed without uncertainty. Dissociation energies `D₀` are the CCCBDB Release 22 experimental 0 K atomization energies: H₂ `432.1` (no uncertainty printed), N₂ `941.6 ± 0.8`, O₂ `493.7 ± 0.2`, CO `1071.8 ± 0.5`, HCl `427.8 ± 0.1` kJ/mol. The WebBook pages do not carry the Huber–Herzberg `D₀` header values, so CCCBDB is the source for `D₀`.

The phenol pKa is `9.994` at 25 °C. It is the Reliable entry in the IUPAC Digitized pKa Dataset v2.4, from Serjeant and Dempsey, measured by Fickling et al. (1959). The CRC Handbook, 91st edition, prints `9.99`. The CRC inorganic table gives water `13.995` at 25 °C. IAPWS R11-24 Table 3 gives pKw `13.99` at 25 °C. Enthalpies of formation at 298.15 K come from the CODATA key values: H₂O(l) `−285.830 ± 0.040` and CO₂(g) `−393.51 ± 0.13` kJ/mol. CODATA's stated meaning is a high probability that the true value lies within the limits. Methane is not a CODATA key value, so the NIST WebBook gives two: JANAF `−74.87` (no uncertainty) and Gurvich via Manion `−74.6 ± 0.3` kJ/mol.

The tests are data-only. All 36 elements are present, and every value matches its printed concise form. Each interval is ordered. Going up in Z, atomic weight rises except at exactly two places, Ar → K and Co → Ni. CCCBDB's 298 K atomization energy exceeds its 0 K value for all five molecules, and CO's is the largest. Overlapping sources agree to their printed digits: phenol 9.994 against 9.99, water 13.995 against 13.99, and JANAF methane within Gurvich's ±0.3. The atomic-weight ask links all 36 elements, and the phenol ask links exactly the two phenol rows. That is 54 new records.

### Condensed matter: silicon lattice, band gaps, superconductors, quantum electrical constants, iron, water

The condensed-matter anchors are on the board, each as printed.

Silicon, from CODATA 2022: lattice parameter `a = 5.431 020 511(89) × 10^−10` m, {220} spacing `d220 = 1.920 155 716(32) × 10^−10` m, and molar volume `1.205 883 199(60) × 10^−5` m³/mol. All are 1σ, for an ideal crystal of natural Si in vacuum at 22.5 °C. The von Klitzing constant `25 812.807 45...` Ω and the Josephson constant `483 597.848 4... × 10^9` Hz/V are exact and printed truncated, so they use the 0.67 truncation kind. The exact conventional values R_K-90 `25 812.807` and K_J-90 `483 597.9 × 10^9` are stored as separate records.

The band gaps at 300 K come from the Ioffe NSM archive: Si `1.12`, Ge `0.661`, GaAs `1.424` eV, with no uncertainty printed. ioffe.ru did not answer from the box, so the Internet Archive copies were read. The Si and GaAs pages print 300 K in the figure caption. For Ge the 300 K label comes from its Basic Parameters page, and a note says so.

Superconducting transitions come from the NIST SRM 767a certificate (1992), measured on device PP: Nb `9.2488` K, Pb `7.19974` K, Al `1.18074` K. The certificate gives the transition widths and a ±0.3 mK reproducibility, but no uncertainty on T_c itself. YBCO is `93` K, as printed in the title of Wu et al., PRL 58, 908 (1987). The abstract was not reachable.

Iron's ferromagnetic Curie temperature is `1044 ± 2` K, from Arajs and Colvin, J. Appl. Phys. 35, 2424 (1964). Water's critical point comes from IAPWS R2-83(1992): T_c `647.096 + δ₁` K with `δ₁ = 0.000 ± 0.100`, p_c `22.064 + 0.27δ₁ ± 0.005` MPa (the coupling is kept in a note), and ρ_c `322 ± 3` kg/m³. These are estimated uncertainties with no level stated. The triple point is `273.16` K and `611.657` Pa, from IAPWS R14-08(2011), with no uncertainty printed.

The tests are data-only. The silicon entries satisfy CODATA's own table definitions, d220 = a/√8 and V_m = N_A a³/8, within the printed uncertainties. R_K-90 and K_J-90 fall outside the truncation intervals of R_K and K_J. The orderings are checked: Ge < Si < GaAs, Al < Pb < Nb, and YBCO more than ten times Nb. The triple point lies below the critical point. The superconductor and critical-point asks link exactly their records. That is 20 new records.

### Particle data: neutrino oscillations, Higgs width, lifetimes, W masses, lattice alpha_s

The neutrino oscillation parameters are on the board, as PDG 2026 prints them in its summary table: sin²θ12 `0.307±0.012`, Δm²21 `(7.60±0.17)E-5` eV², and sin²θ13 `0.0217±0.0007`. PDG gives the atmospheric pair only under an assumed mass ordering, so each ordering is its own record. Normal ordering: sin²θ23 `0.533±0.018` and Δm²32 `0.002445±0.000023` eV². Inverted ordering: sin²θ23 `0.523+0.031-0.027` and Δm²32 `-0.00252±0.00004` eV². Where the PDG database stores a scale factor, a note records it.

The Higgs total width is a PDG average now, `3.0+1.5-0.7` MeV, built from three off-shell measurements. The direct ATLAS limit is stored as a bound: Γ_H < 160 MeV at 95% CL (PL B861 139277, 2025). PDG lists that limit but does not use it in the average. The bound's lower end of 0 is the edge of a width, not a measurement.

Lifetimes: τ_τ `(2.903±0.005)E-13` s. The B lifetimes are PDG's HFLAV summary values: B+ `1637±4E-15` s, B0 `1511.3±2.7E-15` s, and Bs `1.515±0.006E-12` s. PDG's own averages are named in the notes but are not stored.

The W mass measurements are kept apart so the tension stays visible. CDF II: `80,433.5 ± 6.4 stat ± 6.9 syst = 80,433.5 ± 9.4` MeV (Science 2022). ATLAS: `80366.5 ± 9.8 (stat.) ± 12.5 (syst.)` MeV = `80366.5 ± 15.9` MeV (EPJC 2024). CMS: `80 360.2 ± 9.9` MeV (Nature 2026), with a level that is not stated. The test uses each paper's own printed total. CDF sits more than 3σ from both ATLAS and CMS, while ATLAS and CMS agree within 1σ. The PDG average `80.3625±0.0077` GeV is already on the board.

FLAG 2024 gives the lattice strong coupling as α_s^(5)(M_Z) = `0.11833(67)` = `0.1183(7)`, Eq. (399). FLAG calls the error 'our range', so the level is recorded as not stated. It agrees with PDG's `0.1180(9)` within the combined error.

The tests are data-only: the comparisons above, sin² values inside [0, 1] with their errors, the sign of Δm²32 by ordering, the Higgs width inside the ATLAS bound, and the tau lifetime as the shortest. This adds 16 quantities and 1 bound, 17 records in all.

### Elementary functions and exact rational enclosures

`sin`, `cos`, `exp`, `log`, and `pi` are elementary functions. The identities `sin(x)^2 + cos(x)^2 = 1`, `d(sin(x), x) = cos(x)`, `d(cos(x), x) = -sin(x)`, `d(exp(x), x) = exp(x)`, `d(log(x), x) = 1/x`, and `exp(x + y) = exp(x) * exp(y)` are kept by rewriting, then checked by comparing the reduced forms. A derivative uses the chain rule, and a quotient is kept only when the quotient rule multiplies back. Special values that are rational are exact: `sin(0) = 0`, `cos(0) = 1`, `exp(0) = 1`, `log(1) = 0`, `sin(pi) = 0`, `cos(pi) = -1`, `sin(pi/2) = 1`, `cos(pi/2) = 0`, `sin(pi/6) = 1/2`, and `cos(pi/3) = 1/2`. An angle such as `sin(pi/4)` whose exact value is not rational stays the elementary expression. The logarithm of a non-positive number stays open. Division by zero stays open. A polynomial derivative is not stolen: `d(x^2, x)` is still `2 * x`, and `d(i^2, i)` is still `2 * i`.

A closed expression that does not reduce to a rational is enclosed by a pair of rationals. `pi` is bounded by the Machin series `16 atan(1/5) - 4 atan(1/239)`. `exp`, `sin`, and `cos` use Taylor series with a remainder bound. `log` uses the artanh series. An enclosure is a certificate that the value lies in a closed rational interval, not a rounded point claimed as the value. Overlapping enclosures are not a proof of equality. Disjoint enclosures prove an inequality: `prove pi >= 3` and `prove pi <= 22 / 7` hold, and `prove pi <= 3` stays open.

### The unit 2-sphere in angular coordinates

`metric(s2, angular)` is the metric `ds^2 = dθ^2 + sin(θ)^2 dφ^2` on the unit 2-sphere. The inverse is kept only when both products are the identity, and is `diag(1, 1/sin(θ)^2)`. The Levi-Civita connection is torsion-free and metric-compatible, checked identically. The Riemann symmetries and both Bianchi identities hold. The scalar curvature is `2`, and the Ricci tensor equals the metric, so `scalar(metric(s2, angular))` is `2` and `ricci(metric(s2, angular)) = metric(s2, angular)`. Equality of components uses the Pythagorean identity when one side is written as `1 - cos(θ)^2` and the other as `sin(θ)^2`. The unknown chart `metric(s2, spherical)` stays open.

### Astrophysics and the solar system: IAU nominal values, GM, the au, the Moon, Sirius B, PSR J0740+6620

IAU 2015 Resolution B3 is on the board as it prints it. Its eleven nominal conversion constants are exact by resolution: R_sun `6.957 × 10^8` m, S_sun `1361` W m^-2, L_sun `3.828 × 10^26` W, T_eff `5772` K, (GM)_sun `1.327 124 4 × 10^20` m³ s⁻², the Earth radii `6.3781`/`6.3568 × 10^6` m, the Jupiter radii `7.1492`/`6.6854 × 10^7` m, (GM)_E `3.986 004 × 10^14`, and (GM)_J `1.266 865 3 × 10^17`. The best estimates from the resolution's notes are stored beside them and are not the nominal values: S_sun `1361 (± 1)` W m^-2 (2σ, a new kind on the board), L_sun `3.8275 (± 0.0014) × 10^26` W, T_eff `5772.0 (± 0.8)` K, and the Haberreiter photospheric radius `695 658 (± 140)` km. The au is `149 597 870 700` m exactly (IAU 2012 B2, quoted in B3 note 4).

GM comes from the IAU 2026 System of Astronomical Constants (Commission A3, updated 2026-11-20). GM_S is `1.327 124 420 995 × 10^20` [TCB] and `1.327 124 400 418 × 10^20` [TDB] m³ s⁻², each ± `1.0 × 10^8`. GM_E is `3.986 004 417`, `414`, and `355 × 10^14` [TCB, TT, TDB], each ± `3 × 10^5`. The table states no level for these uncertainties. The IERS Conventions PDF failed TLS from the box, so the IAU table is the GM source.

The Moon: lunar laser ranging gives da/dt = `38.30 ± 0.08` mm/year (Williams & Boggs 2016). The NSSDCA fact sheet gives a semimajor axis of `0.3844 × 10^6` km and a recession of `3.8` cm/yr, both with no uncertainty printed.

Sirius B: Bond et al. 2017 give a dynamical mass of `1.018 ± 0.011` M_sun and a flux radius of `0.008098 ± 0.000046` R_sun (internal errors only, as the paper says). Joyce et al. 2018 give a redshift mass of `1.017 ± 0.025` M_sun with a radius of `0.803 ± 0.011` R_sun/100, unit kept as printed.

PSR J0740+6620: the Fonseca 2021 Shapiro-delay mass is `2.08^{+0.07}_{-0.07}` M_sun at 68.3% credibility, also a new kind. Four NICER radii are stored, each as its abstract prints it: Riley 2021 `12.39^{+1.30}_{-0.98}`, Miller 2021 `13.7^{+2.6}_{-1.5}`, Salmi 2024 `12.49^{+1.28}_{-0.88}`, and Dittmann 2024 `12.92^{+2.09}_{-1.13}` km.

The tests are data-only. The nominal values are exact, and each sits inside the uncertainty of the estimate it was rounded from. B3's own rule holds: the nominal GM digits are where the TCB, TT, and TDB values agree. Bond and Joyce agree on the mass and on the radius. The four NICER intervals overlap. NSSDC's 3.8 cm/yr matches the LLR rate to its printed digit. This adds 33 records.

### Nuclear and particle extras: light nuclei, neutron Q, pion, kaon, and muon lifetimes

AME2020 now covers the stable nuclides from lithium to oxygen: ⁶Li, ⁷Li, ⁹Be, ¹⁰B, ¹¹B, ¹³C, ¹⁴N, ¹⁵N, ¹⁷O, and ¹⁸O, joining the ¹²C and ¹⁶O already present. Each has its atomic mass, mass excess, and binding energy per nucleon, copied unrounded from mass.mas20 at 1σ. The neutron row's beta-decay column gives Q_β− = `782.3470 ± 0.0004` keV. That is the energy the brief calls the decay endpoint. The record stores AME's Q as printed and does not compute an electron endpoint from it.

The PDG 2026 lifetimes are stored as the summary table prints them. τ(π±) `(2.6033±0.0005)E-8` s and τ(π0) `(8.43±0.13)E-17` s. τ(K±) `(1.2380±0.0020)E-8` s, which is PDG's fit. τ(K_S) `(8.954±0.004)E-11` s, which assumes CPT. τ(K_L) `(5.116±0.021)E-8` s, also a fit. τ(μ) `(2.1969811±0.0000022)E-6` s. PDG's alternative entries (the average where the fit is shown, and the result without CPT) are named in notes but not stored. MuLan's own result is `2196980.3(2.2)` ps (1.0 ppm). Its abstract states no level, so the record says so.

The tests are data-only. Each AME row's mass, excess, and A agree under AME's own definition Δ = (M − A)·u, using AME's u. ¹⁶O has the highest B/A among the light set and ⁶Li the lowest. The neutron Q equals Δ(n) − Δ(¹H) to its printed digit. The lifetimes order as π0 < K_S < K± < π± < K_L < μ. MuLan agrees with the PDG average. This adds 38 records.

### Atomic and molecular: second ionization energies, electron affinities, H2 dissociation

The second ionization energies from NIST ASD 5.12 for He through Ne are on the board, each with ASD's own uncertainty. Hydrogen has no second ionization energy, so the H to Ne range starts at He II. The values are He II `54.4177655282`, Li II `75.6400970`, Be II `18.21115`, B II `25.15483`, C II `24.383143`, N II `29.60125`, O II `35.12112`, F II `34.97081`, and Ne II `40.96297` eV. ASD prints He II and Li II in parentheses, which marks them as theoretical, and N II in square brackets, which marks it as semi-empirical. Notes on those records say so.

The electron affinities come from Rienstra-Kiracofe et al., Chem. Rev. 102 (2002), Table 10: H `0.75419 ± 0.00002`, C `1.262119 ± 0.000020`, O `1.4611100 ± 0.00000007`, F `3.401290 ± 0.000003`, and Cl `3.612724 ± 0.00003` eV. The live repository served a bot check, so the review was read from the authors' institutional copy in the Internet Archive. The F value is kept exactly as printed. The NIST WebBook shows the underlying Blondel 2001 value as 3.4011895(25) eV, and the note records that difference without resolving it.

H2: Hölsch et al. 2019 measured D_0^{N=1} of ortho-H2 as `35 999.582 834(11)` cm⁻¹. Puchalski's theoretical value from the same abstract is a calculation, so it is not stored. This is the ortho (N = 1) quantity and is not compared with CCCBDB's 0 K value.

The tests are data-only. Every second ionization energy exceeds the first. The EAs order H < C < O < F < Cl, and each sits below its atom's first ionization energy. The asks link exactly their records. This adds 15 records.

### Fluorine's second record; early universe: BBN abundances and N_eff

Fluorine now has two electron-affinity records. `rk2002.ea.f` stays as the review printed it, `3.401290 ± 0.000003` eV. `blondel2001.ea.f` is Blondel, Delsart, and Goldfarb's own value, `3.401 1895(25)` eV, read from the NIST WebBook's citation of the paper, since the IOP article page returned an error and Crossref has no abstract. The two differ by about 1.0 × 10⁻⁴ eV, which is more than ten times their combined uncertainty. Both records carry notes that point at each other, and nothing decides between them. The review's Table 10 cites Blondel, Phys. Scr. 1995 for its number, and the WebBook also lists Blondel 1989 as 3.401190 ± 0.000004 eV. That line is noted, not stored.

The early-universe numbers come from the PDG 2026 BBN review (Fields, Molaro, Sarkar, revised August 2025). Y_p is `0.245 ± 0.003` (eq. 24.3), and the review says its systematic part, ±0.002, dominates. D/H × 10⁶ is `25.08 ± 0.29` (eq. 24.2, scaled by S = 1.08). Li/H from the Spite plateau is `(1.45 ± 0.25) × 10⁻¹⁰` (eq. 24.4), which the review says is really a lower bound. Primary values sit beside them: Aver 2021 Y_p `0.2453 ± 0.0034` and Cooke 2018 D/H `(2.527 ± 0.030) × 10⁻⁵`. The lithium problem shows up as data. Eq. 24.10 quotes the standard-BBN value from Fields 2020 as `(4.72 ± 0.7) × 10⁻¹⁰`, and the review calls the gap a factor of 3.3 and 4.4σ. That BBN value is the source's number, not computed here. Planck 2018 gives N_eff `2.99 ± 0.17` (abstract, 68%, Planck+BAO) and `2.99 +0.34 −0.33` (eq. 67b, 95%), which brings in a new kind, 95% interval. The 3.046 theory value is not stored.

The tests are data-only. The fluorine gap is wider than ten combined uncertainties. Aver agrees with PDG on Y_p, and Cooke agrees with PDG on D/H. The printed numbers reproduce the review's own 3.3 and 4.4σ. The 68% N_eff interval sits inside the 95% one. The asks link the right records. This adds 10 records.

### Exotic QED systems: positronium, muonium, helium 2³P

Positronium's ground-state hyperfine interval has two records. Ishida et al. 2014 print `203.394 2 ± 0.001 6 (stat) ± 0.001 3 (sys)` GHz, and Ritter et al. 1984 print `203.389 10(74)` GHz. The gap between them, 0.0051 GHz, is larger than all their printed uncertainty terms added together. Ishida's abstract says it disfavors the earlier experimental average by 2.6 s.d. Both records stay. The decay rates are Kataoka 2009's orthopositronium `7.0401 ± 0.0007` μs⁻¹, which is the source's own combination with three earlier results, and Al-Ramadhan and Gidley 1994's parapositronium `7990.9 ± 1.7` μs⁻¹. Vallery 2003 prints 7.0404(10)(8) with two uncertainty terms its abstract does not name, so it is noted but not stored. Muonium comes from Liu et al. 1999: Δν = `4 463 302 765(53)` Hz, and μ_μ/μ_p = `3.183 345 13(39)`.

The helium 2³P intervals come from four sources. Zelevinsky's 2004 Harvard thesis measured all three in a discharge cell: ν12 `2 291 175.4(6)`, ν01 `29 616 951.5(8)`, and ν02 `31 908 126.6(1.0)` kHz. George et al. 2001 give ν01 `29616950.9 ± 0.9` kHz. The Hessels group's FOSOF measurements give ν12 `2 291 176 590(25)` Hz (Kato 2018) and ν01 `29 616 955 018(60)` Hz (Heydarizadmotlagh 2024). The newer ν01 sits about 3.5 kHz above both older values, far outside their uncertainties, and the board shows that without picking a side.

APS abstracts were behind a bot check, so Ritter, Al-Ramadhan, Liu, and George were read from INSPIRE's copies of the APS abstracts. The others came from arXiv. Zelevinsky's PRL 95, 203001 (2005) and its erratum were not read.

The tests are data-only. The thesis's three intervals close, with ν01 + ν12 = ν02 within the printed uncertainties. The para rate is more than 1000 times the ortho rate. The disagreements are visible. The asks link the right records. This adds 12 records.

### Null results and bounds: EDMs, proton decay, photon, neutrino and graviton masses, equivalence principle

Each bound is stored as its paper printed it, and the measured central values sit beside them where they are printed. JILA 2023 (Roussy et al., Science 381, 46) measured d_e = `(−1.3 ± 2.0 stat ± 0.6 syst) × 10⁻³⁰` e cm and gives \|d_e\| < `4.1 × 10⁻³⁰` e cm at 90% confidence. Abel 2020 measured d_n = `(0.0 ± 1.1 stat ± 0.2 sys) × 10⁻²⁶` e cm and gives \|d_n\| < `1.8 × 10⁻²⁶` e cm at 90% C.L. Super-Kamiokande (Takenaka 2020) gives τ/B(p → e⁺π⁰) > `2.4 × 10³⁴` years at 90% CL. That is the board's first bound with no upper end. A Bound can now leave its upper end empty, but the audit then requires a condition saying it is a lower limit only, and the record reads "is at least".

The photon mass is PDG 2026's summary, < `1 × 10⁻¹⁸` eV (Ryutov 2007, solar-wind MHD; PDG gives no CL). KATRIN 2025 gives m_ν < `0.45` eV at 90% CL. The graviton has two bounds. GWTC-3 gives m_g ≤ `2.42 × 10⁻²³` eV/c² at 90% credibility. Its arXiv v1 abstract printed 1.27 × 10⁻²³, but v3 says it "fixed graviton mass bound in abstract", and the v3 text and Table VII give 2.42, so v3 is kept and the change is noted. PDG 2026 still lists < `1.76 × 10⁻²³` eV from GWTC-2, which is stored separately. MICROSCOPE's final result is η(Ti, Pt) = `[−1.5 ± 2.3 (stat) ± 1.5 (syst)] × 10⁻¹⁵`, stored with its split.

The tests are data-only. Each EDM central value lies inside its own bound. The proton bound has no upper end, and its record says "at least". The printed limits are stored exactly. \|η\| is below its statistical error. The asks link the bounds. This adds 3 values and 7 bounds.

### Coverage audit; thermodynamics and fluids

`COVERAGE.md` is new. It sorts every board record into one of 15 physics domains, plus two bookkeeping rows for the SI defining constants and the foundations records, and lists the most important observables each domain is missing. The sorting lives in `pgi/corpus/coverage.py`, and a test fails if a record has no domain or if the table in the file stops matching the board. At 0.79.0 the audit found mechanics, optics, and fluids empty, and electromagnetism (7), condensed matter (11), and thermodynamics (11) the next thinnest. The top gaps it lists are mechanics, optics, and fluids, then electromagnetism's missing geomagnetic and material data, nuclear half-lives and charge radii, the Z lineshape, and the gravitational redshift.

The first fill is thermodynamics and fluids. CODATA 2022 adds R `8.314 462 618...` J mol⁻¹ K⁻¹, both molar volumes and both Loschmidt constants, c₁, c₂, and the standard atmosphere, all exact. The tests check that they follow from N_A, k, h, and c as CODATA defines them. That is a definitional check, the same as the silicon one. The ITS-90 adds its 14 defining fixed points from Table 1 of Preston-Thomas 1990, read from the page image of NIST's scanned copy: e-H₂ `13.8033`, Ne `24.5561`, O₂ `54.3584`, Ar `83.8058`, Hg `234.3156`, H₂O `273.16`, Ga `302.9146`, In `429.7485`, Sn `505.078`, Zn `692.677`, Al `933.473`, Ag `1234.93`, Au `1337.33`, and Cu `1357.77` K. They are exact on the scale, and the notes say the scale only approximates thermodynamic temperature. The ⁴He λ point, `2.1768 K`, comes from Sect. 3.1.

Water at 0.101325 MPa comes from the NIST WebBook, which computes it from the IAPWS formulations. At 25 °C that gives ρ `997.05` kg/m³, c_p `4.1813` J/(g K), w `1496.7` m/s, η `0.00089002` Pa s, and λ `0.60652` W/(m K), and η at 20 °C is `0.0010016` Pa s. These are reference-formulation values, printed without an uncertainty, and the notes carry the WebBook's stated uncertainty percentages. The IAPWS R1-76(2014) surface tension gives the experimental column at 0.01, 20, 25, and 100 °C with its uncertainty column, for example `71.98 ± 0.36` mN/m at 25 °C.

The speed of sound in standard dry air is disputed. Wong 1986 gives `331.29` m/s with a maximum uncertainty of about 200 ppm, and Greenspan's 1987 comment keeps the older `331.44` m/s. The gap between them is about 450 ppm, wider than Wong's own figure, and both records stay. Wong prints his uncertainty only as a ppm figure, so there is a new kind, *maximum relative uncertainty, ppm as printed*. That figure is never turned into m/s.

This adds 35 records.

### Optics: reference lines, glass and water indices, standard frequencies

The glass-catalogue letters now point to real lines. NIST ASD 5.12 gives the observed air wavelengths of the Na D2 and D1 lines, `588.995095(3)` and `589.592424(3)` nm, Hg e `546.0750(1)`, Hg g `435.8335(1)`, He d `587.5621` (a blend), Cd C′ `643.84695`, Cd F′ `479.99123`, and H-beta `486.135(5)` nm. ASD prints no uncertainty for He d or the two cadmium lines, so none is stored. A test checks that each line rounds to the wavelength SCHOTT prints for its letter, with H-alpha standing in for C.

SCHOTT's N-BK7 data sheet (2014) gives n_d `1.51680`, n_D `1.51673`, n_e `1.51872`, n_F `1.52238`, n_C `1.51432`, n_g `1.52668`, n at 632.8 nm `1.51509`, and n at 1060 nm `1.50669`, along with ν_d `64.17` and n_F − n_C `0.008054`. These are catalogue values with no uncertainty, and the notes say a given melt varies. The tests check that n falls as wavelength rises and that the sheet's own Abbe definition, (n_d − 1)/(n_F − n_C), reproduces 64.17. IAPWS R9-97 adds water's index at 0 °C and 0.1 MPa at 0.2265, 0.589, and 1.014 µm. Those are the release's program-verification values, calculated from its formulation, and Table 2's uncertainty estimate is kept in the notes.

The standard frequencies come from the CIPM list. The I₂-stabilised He-Ne laser has f = `473 612 353 604(10)` kHz and λ = `632 991 212.579(13)` fm, and their product matches c within those uncertainties. The 2025 list (active since 27 March 2026) gives ⁸⁷Sr `429 228 004 229 872.992` Hz and ¹⁷¹Yb `518 295 836 590 863.632` Hz, each with a relative standard uncertainty of `1.7 × 10⁻¹⁶`. That brings in a second relative kind, *relative standard uncertainty*, which is stored as printed and never turned into hertz.

This adds 25 records.

### Mechanics and electromagnetism: standard gravity, GRS80, local g, IGRF-14

Mechanics had no records. It now has CODATA's standard acceleration of gravity, g_n = `9.806 65` m s⁻², stored exact as an adopted value, and the Geodetic Reference System 1980 from Moritz's Geodesist's Handbook text. Its four defining constants are stored exact: a = `6378 137` m, GM = `3 986 005 × 10⁸` m³ s⁻², J₂ = `108 263 × 10⁻⁸`, and ω = `7 292 115 × 10⁻¹¹` rad s⁻¹. Three derived constants are stored as printed with no uncertainty: 1/f = `298.257 222 101`, normal gravity at the equator γ_e = `9.780 326 7715` m s⁻², and at the pole γ_p = `9.832 186 3685` m s⁻². Moritz says the derived values are accurate to the places given, and the notes say so.

Measured g comes from three Kibble-balance sites. Leaman et al. give `980103140.2(4.3)` µGal at the NIST-4 test mass in Gaithersburg. Liu et al. (2024) quote `980 122 922.8` µGal (standard uncertainty `1.0`) at the NIM Changping key-comparison point and transfer it to `980 139 581.2 ± 2.3` µGal (k = 1) at the Tsinghua tabletop balance. The values stay in µGal, as printed. A test checks that all three sit between GRS80's γ_e and γ_p, as does g_n.

Electromagnetism adds CODATA's Faraday constant and flux quantum (both exact, printed truncated), the vacuum impedance `376.730 313 412(59)` Ω, and the Bohr magneton `9.274 010 0657(29) × 10⁻²⁴` J T⁻¹. Definitional tests check F = N_A e, Φ₀ = h/2e, and Z₀ = μ₀c within the printed uncertainties. IGRF-14 adds the degree-1 Gauss coefficients: g₁⁰ = `-29350.0`, g₁¹ = `-1410.3`, and h₁¹ = `4545.5` nT for 2025.0, g₁⁰ at 2020.0 (`-29403.41`, definitive) and 1900.0 (`-31543`), and its forecast secular variation `12.6` nT/yr. The file prints no uncertainties. A test checks that |g₁⁰| falls from 1900 to 2020 to 2025. The board does not compute a dipole moment from these coefficients.

The conductance quantum was planned but left out because its NIST page code could not be found. This adds 21 records.

### Earth rotation and figure: IERS Conventions, length of day, WGS 84, Love numbers

Mechanics now has Earth's adopted figure and rotation. From IERS Conventions (2010) Table 1.1 come GM_E = `3.986004418 × 10¹⁴` m³ s⁻² (± `8 × 10⁵`), a_E = `6378136.6 ± 0.1` m, J₂ = `1.0826359 × 10⁻³`, 1/f = `298.25642`, mean equatorial gravity `9.7803278` m s⁻², the geoid potential W₀ = `62636853.4` m² s⁻² (the 2017 update), the dynamical flattening H = `3273795 × 10⁻⁹`, the J2000 obliquity `84381.406″`, and the Earth Rotation Angle at J2000 and its rate, which are defining. The table's uncertainties are stored as printed, at an unstated level. Chapter 5 adds the IAU 2006 precession of the equator in longitude, whose linear term is `5038.481507″` per century, and the IAU 2000 correction to the 1976 rate, `−0.29965 ± 0.00040″` per century. The chapter does not print the general precession p_A, so that is still a gap. Chapters 6 and 7 add the nominal Love numbers k₂₀, k₂₁, and k₂₂ (elastic and anelastic) and the displacement numbers h₂ = `0.6078` and l₂ = `0.0847`. They are model values, and the notes say so.

Length of day comes from three rows of the EOP 20 C04 series: the shortest day since 1962 (2024-07-05, `−0.0016508 ± 0.0000246` s), the longest (1972-04-12, `0.0043550 ± 0.0007000` s), and the last row served (2026-10-26, `0.0014827 ± 0.0000095` s). C04's page gives a nominal angular velocity of `72921151.467064` picorad/s. Computing 2π times the ERA rate per 86 400 s with certified bounds on π gives `72921151.4670698…`, which agrees to about one part in 10¹³ but not in the last printed digit, and the test records that. WGS 84's four defining parameters come from NGA's page, read through a Wayback copy because the live page timed out. WGS 84 shares a and ω with GRS80 and GM with the IERS table, but its 1/f differs from GRS80's, and a test checks all three.

The NIST-4 local-g record keeps its `leaman2015` id. Crossref confirms IEEE Trans. Instrum. Meas. 64, 1663-1669 (June 2015), and the source line now lists all eight authors.

This adds 26 records.

### Gravitational redshift and the Z lineshape

The clock test of GR is on the board now. Galileo satellites 5 and 6, accidentally launched into eccentric orbits, give two analyses. Delva et al. (2018) measure the fractional deviation from GR's redshift as `(+0.19 ± 2.48) × 10⁻⁵` at 1σ. Herrmann et al. (2018) take their final result from one clock, `(2.2 ± 1.6) × 10⁻⁵` for the combined redshift and Doppler test, and give `(4.5 ± 3.1) × 10⁻⁵` for the redshift alone. Pound and Snider (1965) measured the 57Fe gamma-ray shift over 75 ft at `0.9990 ± 0.0076` times the equivalence-principle value, with an estimated systematic limit of `0.010`. Gravity Probe A's abstract says agreement 'at the 70×10⁻⁶ level', with no confidence level stated, so that is stored as a bound and the condition says so. The original Pound–Rebka 1960 letter has no reachable abstract and is not stored. The tests check that the Galileo uncertainties are below GP-A's level, that each α is within 2σ of zero, and that Pound–Snider's ratio is within its errors of 1.

The Z lineshape comes from the 2006 LEP/SLD combination, Table 2.13 with lepton universality: m_Z = `91.1875 ± 0.0021` GeV, Γ_Z = `2.4952 ± 0.0023` GeV, σ⁰_had = `41.540 ± 0.037` nb, R⁰_ℓ = `20.767 ± 0.025`, and A⁰,ℓ_FB = `0.0171 ± 0.0010`. The abstract adds N_ν = `2.9840 ± 0.0082` and sin²θ_eff = `0.23153 ± 0.00016`. Their printed correlations stay in the notes. PDG 2026 adds Γ_Z = `2.4955 ± 0.0023` GeV, σ⁰_had = `41.4802 ± 0.0325` nb, and A⁰,ℓ_FB = `(1.71 ± 0.10)%`. LEP and PDG agree on m_Z and Γ_Z within their uncertainties. PDG's σ⁰_had sits more than one LEP uncertainty below the 2006 value, the API record doesn't say why, and both are kept. N_ν is about 2σ below 3, which a test records without reading anything into it.

This adds 15 records.

### Nuclear half-lives and charge radii

Nuclear data had masses but no clocks and no sizes. Half-lives now come from two evaluations side by side. The DDEP tables from LNHB give ³H `12.312(25)` a, ¹⁴C `5700(30)` a, ⁴⁰K `1.2522(27) × 10⁹` a (a 2025 evaluation), ⁶⁰Co `5.2711(8)` a, ²³⁸U `4.468(5) × 10⁹` a, and ²³²Th `14.02(6) × 10⁹` a. ENSDF, read through the IAEA LiveChart API, gives the same six plus the free neutron, `613.9(6)` s. The board stores ENSDF's ⁶⁰Co in days as printed (`1925.28(14)` d) and doesn't convert it to years, so that pair is not compared. The other five pairs agree within their combined uncertainties, and a test checks them. ENSDF's neutron entry has a 2005 publication cut-off, and the board doesn't set it against the PDG lifetime.

Charge radii come from Angeli and Marinova (2013), via the same API, because the IAEA radii page is behind a browser check. There are 13 nuclei: the proton, deuteron, triton, ⁴He, ¹²C, ¹⁴C, ¹⁶O, ⁴⁰K, ⁴⁰Ca, ⁴⁸Ca, ²⁰⁸Pb, ²³²Th, and ²³⁸U. Two features show directly. ⁴⁰Ca and ⁴⁸Ca have the same radius within errors (`3.4776(19)` and `3.4771(20)` fm), even with eight extra neutrons. And the table's proton radius, `0.8783(86)` fm, sits above the muonic-hydrogen value already on the board (`0.84087(39)` fm) by more than their combined uncertainty. That is the proton-radius puzzle as the data stood before CODATA moved, and both values stay.

This adds 26 records.

### Electromagnetism extras: conductance quantum, copper, water permittivity, Coulomb's law

The conductance quantum is in now. Its NIST page code turned out to be `conqu2e2sh`, which batch 8 couldn't find. G₀ = `7.748 091 729... × 10⁻⁵` S and its inverse, `12 906.403 72...` Ω, are both exact and printed truncated, and the tests check G₀ = 2e²/h and its inverse against the truncation bounds.

Copper comes from NBS Handbook 100's International Annealed Copper Standard: `1.7241` µΩ cm at 20 °C (the handbook also prints it as 100/58), a mass resistivity of `0.15328` Ω g m⁻², a density of `8.89` g cm⁻³, and a temperature coefficient of `0.00393` per °C. These are adopted reference values, not measurements, and the notes say so. Matula's 1979 measured resistivity tables are a scan with no text layer, so measured copper is still a gap.

Water's static permittivity comes from IAPWS R8-97, a scanned release read from page images. The board stores `69.96 ± 0.04` at 323 K and `55.57 ± 0.2` at 373 K, both at 0.101 325 MPa. Those uncertainties are the release's own estimates, which it says 'could not be based on rigorous statistics'. It also stores the code-verification value `77.747 35` at 300 K, which reflects the formulation's digits, not its accuracy. A test checks that ε falls as temperature rises.

Coulomb's law has two tests. Williams, Faller, and Hill (1971) found q = `(2.7 ± 3.1) × 10⁻¹⁶` for a 1/r^(2+q) force, a null result, along with a Proca photon mass squared of `(1.04 ± 1.2) × 10⁻¹⁹` cm⁻². Plimpton and Lawton (1936) found the exponent correct 'within 1 part in 10⁹', which is stored as a bound and labelled as the board's reading of that phrase. The tests check that q is within its uncertainty of zero and inside the 1936 bound.

This adds 12 records.

### Condensed matter: elastic constants, Debye temperatures, superconductors, graphene, QHE

Condensed matter was the thinnest domain, and this slice fills it out. The elastic stiffnesses are c₁₁, c₁₂, c₄₄ = `165.7, 63.9, 79.6` GPa for silicon and `168.4, 121.4, 75.4` GPa for copper, from Knowles's 2017 compilation, and `1078.6, 126.6, 577.6` GPa for diamond, Migliori's resonant-ultrasound values as quoted by Tanigaki et al. Aluminium comes straight from two 1964 abstracts. Kamm and Alers extrapolate to 0 K (`11.430, 6.192, 3.162` × 10¹¹ dyn cm⁻²), and Vallin et al. measure at 4 K (`11.63, 6.48, 3.09` × 10¹⁰ N m⁻², the same unit). They differ by up to about 5% in c₁₂, and both are kept. A test checks that Knowles's own anisotropy ratio 2c₄₄/(c₁₁ − c₁₂) reproduces his printed 1.56 for Si and 3.21 for Cu.

The Debye temperatures here come from elastic constants: aluminium `430.3` K (Kamm–Alers) and `425` K (Vallin), and diamond `2244` K (Migliori). The calorimetric values for copper and silicon had no primary source I could reach, so they're left as a gap rather than taken from a textbook table.

MgB₂ superconducts at `39` K (Nagamatsu 2001), and sulfur hydride at `203` K at 155 GPa (Drozdov 2015), which brackets the YBCO entry already on the board. Graphene's white-light transmittance is `97.7 ± 0.1`% (Nair 2008), so its opacity is 2.3%. The paper ties that to πα, but the board leaves that step alone. Finally, the quantum Hall resistance in graphene matches GaAs/AlGaAs to `(−0.9 ± 8.2) × 10⁻¹¹`, or `(−2.7 ± 6.0) × 10⁻¹¹` combined with Janssen et al. (Ribeiro-Palau 2015). Both are null within their standard uncertainty.

The superconductor ask now links MgB₂ and H₃S as well, and the old test's expected set is widened to match.

This adds 24 records.

### Fluids: air transport properties and superfluid helium

Air now has transport properties. Lemmon and Jacobsen's 2004 equations give the dilute-gas viscosity at 300 K as `18.5230` µPa s and the thermal conductivity as `26.3529` mW m⁻¹ K⁻¹. At 5.0 mol/dm³ they're `21.3241` and `32.6062`. These are the paper's program-verification values, whose extra digits 'do not reflect the accuracy of the equations'. The notes keep the paper's own uncertainty statement: 1% for dilute-gas air viscosity, and within 5% overall for air. The PDF prints the viscosity unit in a symbol font that comes out as 'mPa s', but the values are in µPa s, and that's how they're stored, with a note saying why. Nitrogen (`17.8771`) and oxygen (`20.6307`) are included too, and a test checks that air falls between them.

Superfluid helium-4 comes from Donnelly and Barenghi's 1998 review of liquid helium at saturated vapour pressure. It gives density at 0 K (`0.1451397` g cm⁻³) and at 1.5 K (`0.1451646`), the λ-point density used in their fit (`0.1461087`), and the superfluid and normal densities at 1.5 K, `0.12900` and `0.01617`. The two-fluid split adds back to the total density within the printed digits, and a test checks that. First sound at 1.5 K is `235.5` m/s, and second sound is `18.93`, `20.03`, and `16.78` m/s at 1.0, 1.5, and 2.0 K. So second sound rises and then falls toward the λ point, and it runs more than ten times slower than first sound.

This adds 15 records.

### Gravitation: clocks, frame dragging, and lunar laser ranging

Clocks can now see gravity at everyday scales. Chou and colleagues raised one of two Al⁺ clocks by 33 cm and measured a fractional frequency change of `(4.1 ± 1.6)×10⁻¹⁷`. Read as a height, that's `37 ± 15` cm. Bothwell and colleagues resolved the redshift inside a single millimetre-scale strontium sample, with a final gradient of `−9.8(2.3)×10⁻²⁰` per mm, and `−1.28(27)×10⁻¹⁹` per mm from a synchronous comparison of two regions. Those numbers are from the arXiv text, since the published version wasn't reachable. The paper's expected value (`−1.09×10⁻¹⁹`/mm) stays in a note, not in a record, because it's a prediction.

LAGEOS, LAGEOS 2, and LARES measure Earth's frame dragging at μ = `0.994 ± 0.002 ± 0.05` of the general-relativity value. The 0.002 is the formal error and the 0.05 is systematic, stored separately as printed. That now sits next to Gravity Probe B's frame-dragging record, and a test checks that one ask links both.

Lunar laser ranging adds the Nordtvedt parameter and Ġ/G from two analyses. Williams, Turyshev, and Boggs (2004) give η = `(4.4 ± 4.5)×10⁻⁴` and Ġ/G = `(4 ± 9)×10⁻¹³` yr⁻¹. Hofmann and Müller (2018) give η = `(−0.2 ± 1.1)×10⁻⁴` and Ġ/G₀ = `(7.1 ± 7.6)×10⁻¹⁴` yr⁻¹. The tests check only that the later uncertainties are the smaller ones.

This adds 9 records.

### Particle: heavy flavour, SLD, the top width, and Higgs signal strengths

The Z-pole set from batch 9 now has its other half. SLD's combined leptonic asymmetry is `A_l = 0.1513 ± 0.0021`, and that total includes a `±0.0011` systematic. The LEP/SLD 14-parameter heavy-flavour fit gives R_b⁰ = `0.21629 ± 0.00066`, R_c⁰ = `0.1721 ± 0.0030`, A_FB⁰ᵇ = `0.0992 ± 0.0016`, A_FB⁰ᶜ = `0.0707 ± 0.0035`, A_b = `0.923 ± 0.020`, and A_c = `0.670 ± 0.027`. PDG 2026 quotes those fits directly, adding R_l = `20.767 ± 0.025` and A(e) = `0.1515 ± 0.0019`. PDG prints the heavy-flavour asymmetries in percent, and that's how they're kept. A test checks that PDG's values equal the LEP table's after the percent conversion.

The top quark's width is now stored as PDG prints it, `1.42 +0.19 −0.15` GeV, with the asymmetric uncertainty intact. The Higgs boson gets signal strengths: PDG's combined average of `1.03 ± 0.04`, and its per-final-state averages for WW, ZZ, γγ, bb, ττ, and μμ. The ten-year ATLAS and CMS global values are `1.05 ± 0.06` and `1.002 ± 0.057`. ATLAS's four-way breakdown of uncertainty and CMS's three-way breakdown are kept in notes.

This adds 22 records.

### Coverage: the gap list is now generated from the board

COVERAGE.md's gap list had gone stale: it said optics had no reference lines or refractive indices, but 0.81 had already added the NIST lines and the N-BK7 and water indices. The hand-written text is gone. `python -m pgi.corpus.coverage gaps` now builds the whole section from the board.

It has two parts. `coverage.HELD` describes what each domain holds by id prefix, and the counts come from the board. Every record has to fall under an entry, and every entry has to match at least one record, so an undescribed record or an emptied entry fails the tests. `coverage.GAPS` lists what's missing, and each gap carries the terms or id prefixes that would close it. A gap stops being listed as soon as a record in its own domain matches. A record in another domain doesn't count, which stops the GW170817 bound, for example, from closing the gravitational-wave-events gap. The tests check that COVERAGE.md's generated block equals the generator's output, and that a gap closes when a matching probe record is added but not when the probe sits in another domain.

This adds no records.

### Optics: fused silica, air, Verdet constants, and more lines

Fused silica now has its standard dispersion formula: Malitson's 1965 three-term Sellmeier coefficients at 20 °C, B = `0.6961663`, `0.4079426`, `0.8974794` and C = `0.0684043`, `0.1162414`, `9.896161` µm. The JOSA page is blocked from the box, so they come from the refractiveindex.info reprint, which cites the paper and its 0.21–3.71 µm range. A test evaluates the formula exactly on a grid across that range and checks that n² stays above 1 and falls with wavelength.

The refractive index of air comes from NIST's comparison of the Ciddor and modified Edlén equations. In dry air at 20 °C and 101.325 kPa, Ciddor gives `1.000271800` at 633 nm and Edlén gives `1.000271799`, a difference the table prints as 0.1×10⁻⁸. Ciddor also gives `1.000286581` at 300 nm and `1.000268479` at 1700 nm, plus the 633 nm value at 60 and 120 kPa and at 100% humidity. The page's k = 2 uncertainty estimate (about 2×10⁻⁸ in a lab) is in the notes, because Table 1 itself prints none.

The board also has its first Verdet constants. Sivaramakrishnan's 1956 fused-quartz measurements rise from `0.01540` arcmin cm⁻¹ Oe⁻¹ at 5780 Å to `0.04224` at 3650 Å. Turvey's water value is `3.98 ± 0.03` µrad A⁻¹ at 643.3 nm. Seven more NIST lines join the reference set: the He-Ne neon line, two mercury lines, the calcium H and K lines, and the potassium D doublet.

This adds 25 records.

### Particle: heavier hadrons and branching fractions

The hadron list now goes past the light mesons and the Λ. PDG 2026 masses are on the board for D⁺, D⁰, D_s, B⁺, B⁰, B_s, J/ψ, Υ(1S), the three Σ, both Ξ, Ω⁻, Λ_c, and Λ_b, each with its own node and PDG's OUR FIT or OUR AVERAGE label. Where a node prints both, the other value is in the notes. A test checks the printed isospin splittings: Σ⁻ > Σ⁰ > Σ⁺, Ξ⁻ > Ξ⁰, D⁺ > D⁰, and B⁰ > B⁺.

The Higgs measured branching fractions sit beside its signal strengths: bb `53 ± 8` %, WW `25.7 ± 2.5` %, ZZ `2.80 ± 0.30` %, ττ `6.0 +0.8 −0.7` %, γγ `(2.50 ± 0.20)×10⁻³`, and μμ `(3.0 ± 0.9)×10⁻⁴`. For WW, the API keeps slightly asymmetric errors, but PDG's display rounds them to ±2.5. The printed value is stored, and the raw errors go in a note. The Z gets its invisible branching fraction (`20.000 ± 0.055` %), its hadronic branching fraction, and its invisible width (`499.3 ± 1.5` MeV). Because B = Γ_inv/Γ_Z by definition, a test checks that PDG's two invisible entries agree within their uncertainties.

This adds 25 records.

### Gravitation: Tokyo Skytree and more gravitational-wave events

The 2018 Tokyo Skytree test is now on the board. Two transportable strontium lattice clocks, one on the ground floor and one on the observatory floor, measured the height difference as `452.650 ± 0.039` m. Laser ranging over the same period gave `452.631 ± 0.013` m. The result is α = `(1.4 ± 9.1)×10⁻⁵`, and back at RIKEN the clocks read `(−0.3 ± 4.7)×10⁻¹⁸` apart at equal height. The Nature Photonics paper is blocked from the box, so the numbers come from the 2025 review by three of its authors, which reports the same measurement. The source string says so.

GW150914 is no longer the only event. Eight more come from the GWOSC event API, each from its own catalogue data release: GW170817 (GWTC-1), GW190521, GW190814, and GW190425 (GWTC-2.1), GW200115 (GWTC-3), GW230529 and GW231123 (GWTC-4.0), and GW250114 (GWTC-5.0). Each has its source-frame component masses and luminosity distance, with the 90% credible bounds as printed. For example, GW170817 is `1.46`, `1.27` M_sun at `40` Mpc, and GW231123 is `137`, `101` M_sun at `2200` Mpc. The tests check the catalogue's own labels (m₁ ≥ m₂, positive lower distance bound) and that GW170817 is the nearest. Event descriptions like "heaviest" or "mass gap" are left out because they're interpretation, not printed values.

This adds 28 records.

### Electromagnetism: metal resistivities and dielectric permittivities

The board now has resistivities of real metals, not just the IACS copper standard. The values are the JPCRD recommended totals. Matula 1979 covers copper, silver, and gold, and Desai and co-workers (1984) cover aluminium and tungsten. At 293 K, in 10⁻⁸ Ω m: silver `1.587`, copper `1.678`, gold `2.214`, aluminium `2.650`, and tungsten `5.28`, plus 273 K and 300 K rows for each and copper at 100 K. The text layers are OCR, so every value was checked against the page image (Matula's gold row reads `~9~` for 293 K in the text). Each paper's uncertainty statement for the range is in the notes, for example 0.5% for copper from 250 to 350 K. The tests check the room-temperature order (Ag < Cu < Au < Al < W) and that each metal's resistivity rises with temperature. This also closes the old gap for copper resistivity versus temperature, which had stayed open because the earlier Matula copy was an image-only scan.

Dielectrics come from NIST Technical Note 1512, with each method's standard uncertainty taken from the table caption as a relative standard uncertainty. Values: Corning 7980 fused silica `3.84` at 5.07 GHz; PTFE `2.05` at 9.93 GHz and `2.055` at 9.816 GHz; PMMA `2.634`; sapphire `11.58` parallel and `9.40` perpendicular to the c-axis at 12.4 GHz; crystalline quartz `4.443` and `4.59`; rutile `163.7` and `85.6`. A test checks that the printed anisotropy runs the same way for sapphire and rutile.

This adds 27 records.

### Cosmology: DESI DR2 BAO distances

The board had DESI DR2's dark-energy parameters but not the distances they come from. It now holds Table IV of the DR2 BAO paper (arXiv:2503.14738): D_V/r_d for all seven baseline bins, and D_M/r_d and D_H/r_d for the six bins that have them. That is BGS, LRG1, LRG2, LRG3+ELG1, ELG2, QSO, and Lyα, from z_eff `0.295` to `2.330`. Each value is the posterior mean with its standard deviation, systematics included, read from the paper's LaTeX source. The table's correlation coefficients are left out, as asked, and each record says so. The superseded LRG3 and ELG1 rows are not stored.

The only check is definitional: D_V = (z D_M² D_H)^(1/3). The printed means satisfy it in every bin to well within one printed sigma.

This adds 19 records.

### The Schwarzschild metric and flat FLRW

The Schwarzschild metric in Schwarzschild coordinates is on the atlas, with mass parameter `m`. `metric(schwarzschild)` is `diag((2m - r)/r, -r/(2m - r), r^2, r^2 sin(theta)^2)`, which is `-(1 - 2m/r) dt^2 + (1 - 2m/r)^{-1} dr^2 + r^2 dΩ^2`. An inverse is kept only when both products are the identity. The Levi-Civita connection is torsion-free and metric-compatible, checked identically. Ricci vanishes, the Einstein tensor vanishes, and the scalar curvature is `0`. The Kretschmann scalar is the full contraction `R_{ρσμν} R^{ρσμν}`, and `kretschmann(metric(schwarzschild))` is `48 m^2 / r^6`.

Flat FLRW is on the atlas in Cartesian coordinates, with a formal scale factor `a(t)` whose derivatives are exact: `d(a(t), t)` and `d(a(t), t, 2)`. `metric(flrw)` is `diag(-1, a(t)^2, a(t)^2, a(t)^2)`. The Einstein tensor `G = Ric - (1/2) R g` is exact: `G_tt` is `3 * d(a(t), t)^2 / a(t)^2`, and each spatial diagonal is `-(2 * a(t) * d(a(t), t, 2) + d(a(t), t)^2)`.

### The Lorentz algebra and the Dirac matrices

The Minkowski metric `eta()` is `diag(-1, 1, 1, 1)`, matching the mostly-plus signature already used for Minkowski and Schwarzschild. A boost such as `boost(x, 3/5)` is kept only when `1 - v^2` is the square of a positive rational, so that `γ = 5/4` and `γv = 3/4` are exact, and only when both `Λ^T η Λ` and `Λ η Λ^T` equal `η`. A velocity such as `1/2`, whose residual is not a rational square, stays open.

The so(3,1) generators `so31(jx)` through `so31(kz)` satisfy `[J_i, J_j] = ε_ijk J_k`, `[K_i, K_j] = -ε_ijk J_k`, and `[J_i, K_j] = ε_ijk K_k`, checked on every triple, and each generator preserves `η` infinitesimally: `X^T η + η X = 0`.

The Dirac matrices are the mostly-plus Weyl form: `γ^0` is `[[0, I], [-I, 0]]` and `γ^i` is `[[0, σ_i], [σ_i, 0]]`. The anticommutator `{γ^μ, γ^ν}` equals `2 η^{μν} I` on every pair, which is the certificate `clifford() = 0`.

### 3×3 spectral decompositions and SU(3) gauge transformations

A Hermitian spectral decomposition is now kept for size up to 8, not only 2×2, when the characteristic polynomial splits into factors in Q or Q(√d), the eigenvector norms are positive rationals, `U` is unitary, `D` is real diagonal, and `H = U D U†` rebuilds exactly. The identity 3×3 matrix gives `U = D = I`. The path graph `[[0, 1, 0], [1, 0, 1], [0, 1, 0]]` has `eigendiag` equal to `diag(-√2, 0, √2)` and rebuilds. The matrix of all ones plus the identity stays open, because an orthonormal eigenbasis would mix √2, √3, and √6, and the scalar field does not mix two different square-free radicands.

An SU(3) gauge transformation by a constant special unitary matrix, such as the 3-4-5 rotation embedded in the first two coordinates, acts on a constant connection by `A ↦ U A U†`. For constant components the field strength is `F = [A_x, A_y]`, it transforms as `F ↦ U F U†`, and `tr(F²)` is invariant, checked exactly for `su3(1)` and `su3(2)`.

### Exact ODE checks for the harmonic oscillator and hydrogen

A candidate solution is kept only when its residual in a linear ODE vanishes identically, checked by exact elementary differentiation. The harmonic oscillator, with ħ = ω = m = 1, is admitted for n = 0, 1, and 2. The states are ψ_0 = exp(-x²/2), ψ_1 = x exp(-x²/2), and ψ_2 = (2x² − 1) exp(-x²/2). Each satisfies ψ'' − (x² − 2n − 1) ψ = 0, which is the Schrödinger equation at E_n = n + 1/2, and `ode(harmonic(n)) = 0`.

The hydrogen radial function is the reduced wave u_{n,ℓ}(r) = r R_{nℓ}(r) in atomic units with Z = 1. The admitted states are u_10 = r exp(-r), u_20 = r (1 − r/2) exp(-r/2), and u_21 = r² exp(-r/2). Each satisfies u'' − ℓ(ℓ+1)/r² u + 2/r u − u/n² = 0, which is the radial equation at E = −1/(2n²), and `ode(hydrogen(n, l)) = 0`. A level or angular momentum outside that list stays open.

### Astrophysics: Borexino solar neutrino fluxes

The board now holds Borexino's solar neutrino fluxes as the collaboration printed them, read from each paper's arXiv source. From Phase-II (Phys. Rev. D 100, 082004, Table II): pp `(6.1 ± 0.5 +0.3 −0.5)×10¹⁰`, ⁷Be `(4.99 ± 0.11 +0.06 −0.08)×10⁹`, and pep `(1.27 ± 0.19 +0.08 −0.12)×10⁸` or `(1.39 ± 0.19 +0.08 −0.13)×10⁸`, depending on whether CNO is held at the high- or low-metallicity solar model. These are in cm⁻² s⁻¹, with statistical and systematic parts kept separate. ⁸B comes from Phys. Rev. D 101, 062001: `2.57 +0.17 −0.18 (stat) ± 0.07 (syst) ×10⁶`. That is the equivalent flux assuming no flavour conversion, which is what the paper prints, so it is labelled that way rather than as a total ⁸B flux. CNO comes from the 2020 Nature discovery (`7.0 +3.0 −2.0 ×10⁸`; the paper names no level for the final interval, so none is assigned) and the 2022 PRL (`6.6 +2.0 −0.9 ×10⁸`, a 68% quantile including systematics). The Standard Solar Model predictions printed beside these values are model numbers and are not stored.

The ⁸B value needed a split statistical part that is itself asymmetric, so the split kind now accepts a lower statistical bound. There is also a new kind, "asymmetric, level not stated", for the 2020 CNO value.

This adds 7 records.

### Thermodynamics and QED: Boltzmann-constant inputs and the Penning-trap electron mass

The board had the exact SI value of k but none of the measurements that fixed it. It now holds the key k data from the CODATA 2017 Special Adjustment (Newell et al., Metrologia 55, L13, Table 1), which is open access. There are ten acoustic-gas-thermometry values of the molar gas constant, from NIST-88 (`8.314 470(15)`, argon) to LNE-17 (`8.314 4614(50)`, helium) and NPL-17 (`8.314 4603(58)`, argon). There is also PTB-17's dielectric-constant gas thermometry ratio A_ε(⁴He)/R `6.221 140(12)×10⁻⁸` m³ K J⁻¹, NIM/NIST-17's Johnson-noise k/h `2.083 6630(56)×10¹⁰` Hz K⁻¹, and the adjusted k `1.380 649 03(51)×10⁻²³` J K⁻¹ before it was fixed. The method and gas for each datum come from the paper's Figure 2 legend and labels. Each record keeps the uncertainty in concise form, as printed, and a test checks it against the printed relative uncertainty. The one other check is definitional: the adjusted k truncates to the fixed SI value.

The electron's atomic mass comes from Sturm et al. 2014 (12C5+ g-factor in a Penning trap): `0.000 548 579 909 067(14)(9)(2)` u. The statistical and systematic parts are stored separately. The third part, the theory uncertainty, is quoted in the note, because the split kind holds only two parts.

This adds 13 records.

### Null results and gravitation: SME limits and Pound-Rebka 1960

The board now holds Lorentz-invariance limits from the Kostelecky-Russell Data Tables (arXiv:0801.0287v19, January 2026 edition, read from the LaTeX source). There are 18 entries from the summary Tables S2-S5:

- b̃_X, b̃_Y, b̃_Z, and b̃_T for the electron, proton, and neutron;
- three photon coefficients: the isotropic d = 3 k_(V)00, κ̃_tr, and the birefringence coefficient k_(E)20 at d = 4;
- one neutrino coefficient, Re(a_L)^T in the μτ sector;
- two gravity coefficients, α ā_T for the electron and s̄^TT.

The authors describe each entry as a conservative 2σ limit on the modulus, rounded logarithmically to the nearest power of ten, with only one coefficient nonzero at a time. Because of that rounding, each value is stored as the printed order of magnitude, without an uncertainty, and not as a hard bound edge. A sharp bound would wrongly block anything between 10ⁿ and about 3×10ⁿ. Each record quotes the convention.

Pound and Rebka's 1960 letter was reachable after all, as a scan of the printed page on the University of Pavia physics site. The records cite the APS DOI and were checked against the page image. It gives a net fractional shift of `-(5.13 ± 0.51)×10⁻¹⁵` over the two-way 148 ft tower, described as 'the rms statistical deviation', and the paper's own ratio `(Δν)exp/(Δν)theor = +1.05 ± 0.10`. The prediction it compares against is not stored. The Pound-Snider 1965 note now points to these records instead of saying the paper was unreachable.

This adds 20 records.

### Differential forms and Maxwell's homogeneous equations

A k-form on a coordinate chart has exact components, either multivariate rationals or elementary expressions. The wedge product of 1-forms is alternating, checked identically. The exterior derivative satisfies d² = 0, checked identically on polynomial 0-forms and 1-forms and on elementary 1-forms. On flat Minkowski spacetime with coordinates (t, x, y, z), a 4-potential A is a 1-form, the Faraday 2-form is F = dA, and dF = 0 is the identity d²A = 0. That is the homogeneous Maxwell system in the language of forms. The inhomogeneous equation d⋆F = J stays outside until the Hodge star is admitted.

### Null results: double-beta decay, WIMPs, axions, short-range gravity, alpha drift, charge equality

All of the null-result gaps are now closed. Every bound keeps the confidence level the paper or PDG prints:

- **KamLAND-Zen 2023:** 0νββ half-life of ¹³⁶Xe `> 2.3×10²⁶ yr` at 90% C.L. This is a lower limit only. The effective-Majorana-mass range depends on nuclear matrix elements, so it is left out.
- **LZ 4.2 t·yr (PRL 135, 2025):** strongest spin-independent exclusion `2.2×10⁻⁴⁸ cm²` at 40 GeV/c², 90% C.L.
- **CAST 2017:** `g_aγ < 0.66×10⁻¹⁰ GeV⁻¹` (95% C.L.), valid for m_a ≲ 0.02 eV.
- **Eöt-Wash 2020:** gravitational-strength Yukawa interactions limited to ranges `< 38.6 µm` (95%).
- **PTB Yb⁺ clocks (Filzinger 2023):** `α̇/α = 1.8(2.5)×10⁻¹⁹ /yr` and `(c²/α)dα/dΦ = −2.4(3.0)×10⁻⁹`. Both are stored as measured values with the uncertainty as printed, because the paper names no level.
- **PDG 2026:** `|q_p+q_e|/e < 1×10⁻²¹`, `|q(e⁺)+q(e⁻)|/e < 4×10⁻⁸`, the neutron charge average `(−0.2 ± 0.8)×10⁻²¹ e`, and the free-neutron n→n̄ transition time `> 8.6×10⁷ s` (90%). The bound-neutron limits depend on nuclear suppression factors, so they are named in the notes but not stored.

This adds 10 records.

### Cosmology: age, reionization, curvature, baryon-to-photon ratio, and weak-lensing S8

Planck 2018 VI adds three values in the baseline column TT,TE,EE+lowE+lensing (68%): age `13.797 ± 0.023 Gyr` and reionization redshift `7.67 ± 0.73`. The third is curvature, `Ω_K = 0.0007 ± 0.0019`, from Sect. 7.3 with BAO, since Planck alone prefers a closed model.

The baryon-to-photon ratio comes from deuterium: Cooke et al. 2018 give η₁₀ = `5.931 ± 0.051` from their D/H, and Fields et al. 2020 give BBN+D `6.148 ± 0.191`. Fields' CMB-only `6.104 ± 0.058` is kept beside them.

Weak-lensing S8 is now on the board next to Planck's `0.832 ± 0.013`:

- **KiDS-1000 cosmic shear:** `0.759 +0.024 −0.021`. This is best fit plus PJ-HPD, and the paper doesn't state the level for that pair.
- **DES Y3 cosmic shear:** `0.759 +0.025 −0.023` (68%).
- **DES Y3 3×2pt:** `0.776 ± 0.017` (68%).

The tension stays visible: both sides are stored as printed, and nothing is reconciled or retracted. The only test is that the printed lensing values sit below Planck's printed value.

This adds 9 records.

### QED: positronium, muonium, HD+, and helium-3

This adds five values as printed:

- **Positronium 1³S₁–2³S₁ (Fee et al. 1993):** `1 233 607 216.4 ± 3.2 MHz`.
- **Muonium 1s-2s (Meyer et al. 2000):** `2 455 528 941.0(9.8) MHz`. The paper's theory value is not stored.
- **HD⁺ v=0→9 two-photon overtone, spin-averaged (Patra et al. 2020):** `415 264 925 500.5(1.2) kHz`. This is the total of the printed (0.4)exp(1.1)theo parts. The paper's derived m_p/m_e is not stored.
- **³He 2³S→2¹S line (van der Werf et al., Science 2025, read from arXiv v1):** `192 504 914 418.96(17) kHz`.
- **Helion-alpha radius difference (same paper):** `r_h² − r_α² = 1.0757(15) fm²`. This is the paper's own isotope-shift result, using QED theory, and it is not recomputed here.

None of the papers states a confidence level, so all five carry "level not stated". These close the Ps/Mu 1S-2S, HD⁺, and helium isotope-shift gaps. The antiproton gap is still open.

This adds 5 records.

### Killing vectors and the Lie derivative

The Lie derivative of a metric along a vector field X is (L_X g)μν = X^ρ ∂_ρ g_μν + (∂_μ X^ρ) g_ρν + (∂_ν X^ρ) g_μρ. X is a Killing field only when that 2-tensor vanishes identically. The translations and the rotation −y ∂_x + x ∂_y of the Euclidean plane are Killing, and a coordinate dilation is not. On Schwarzschild spacetime, the time-translation ∂_t, the axial rotation ∂_φ, and the remaining rotation fields J_x = −sin(φ) ∂_θ − cot(θ) cos(φ) ∂_φ and J_y = cos(φ) ∂_θ − cot(θ) sin(φ) ∂_φ are Killing, checked identically.

### Canonical commutators, angular momentum, and oscillator ladders

Position and momentum are polynomial operators, with ħ = 1 and P = −i ∂. A commutator is kept only as an identity of operators in normal form, with coefficients on the left and derivatives on the right. [X_i, P_j] = i δ_ij, and the angular-momentum operators L_i = ε_ijk X_j P_k satisfy [L_i, L_j] = i ε_ijk L_k. The oscillator ladders a = (X + iP)/√2 and a† = (X − iP)/√2 satisfy [a, a†] = 1. These identities are checked exactly, with no approximation.

### Astrophysics: Sgr A* with GRAVITY, and EHT ring and shadow sizes

GRAVITY gives the distance to the Galactic Center and the mass of Sgr A* in two editions, and both are kept:

- **2019:** R₀ = `8178 ± 13stat ± 22sys pc`, M = `4.152 ± 0.014 ×10⁶ M☉`.
- **2022 (four-star fit):** R₀ = `8277 ± 9 pc` and M = `4.297 ± 0.012 ×10⁶ M☉`, both statistical. The approximate systematics (about 30 pc and about 40,000 M☉) are noted but not stored.

The S2 redshift parameter is stored as printed: f = `0.90 ± 0.09stat ± 0.15sys` (2018) and `1.04 ± 0.05` (2019). Here f = 0 is Newtonian and f = 1 is GR, and no check is made here.

From the EHT:

- **M87\* ring diameter:** `42 ± 3 µas` (Paper I prints no separate M87\* shadow diameter).
- **M87\* mass:** `(6.5 ± 0.7)×10⁹ M☉` (68%).
- **Sgr A\* ring diameter:** `51.8 ± 2.3 µas` (68% credible).
- **Sgr A\* shadow diameter:** `48.7 ± 7.0 µas` (68% credible).

These close the Sgr A* and shadow gaps. This adds 10 records.

### Non-constant SU(2) gauge transformations

A position-dependent SU(2) gauge transformation by the rational rotation U(x, y) already checked acts on a connection by A_μ ↦ U A_μ U† + U ∂_μ U†. The field strength F = ∂_x A_y − ∂_y A_x + [A_x, A_y] transforms as F ↦ U F U†, checked identically as matrix-valued rational functions. A non-constant SU(3) gauge transformation, and an SU(2) transformation that is not this rotation or a constant special unitary matrix, stay outside.

### Fluids: measured air viscosity, dilute-gas viscosities, and TEOS-10

Five measured dry-air viscosities come from Table 1 of NBS Technical Note 1186 (Jones 1984). That table reprints Kestin and Leidenfrost 1959 and DiPippo and Kestin 1968:

- `181.94 µg/(cm·s)` at 20.00 °C and 1.00 atm;
- `187.70` at 34.97 atm;
- `183.75` at 23.44 °C;
- `184.62` at 25.00 °C;
- `197.25` at 49.91 °C.

The table prints no per-point uncertainty, so none is stored. The note's fitted interpolation formula is not stored either.

Berg and Moldover 2012 give viscosities at 25 °C and zero density, with standard uncertainties. They come from 235 measured ratios anchored to the ab initio helium value:

- He `19.8253 ± 0.0002`;
- Ne `31.7088 ± 0.0100`;
- Ar `22.5666 ± 0.0060`;
- Kr `25.3062 ± 0.0080`;
- Xe `23.0183 ± 0.0072`;
- N₂ `17.7494 ± 0.0048` µPa·s.

TEOS-10 adds two defined (exact) values and one computed reference value:

- S_SO = `35.165 04 g/kg` (exact);
- c_p⁰ = `3991.867 957 119 63 J/(kg·K)` (exact);
- the standard-ocean latent heat of evaporation, `2 498 510 J/kg`, which is computed by TEOS-10, not measured.

This closes the measured-air, noble-gas, and seawater gaps. It adds 14 records.

### Condensed matter: calorimetric Debye temperatures

Martin 1973 (Phys. Rev. B 8, 5357) measured specific heats from 2.5 to 30 K in an automatic calorimeter and analysed them together with data from 0.4 to 3.0 K. That gives these limiting low-temperature Debye temperatures:

- Cu `344.3 ± 0.2 K`;
- Ag `226.6 ± 0.2 K`;
- Au `161.8 ± 0.2 K`.

It also gives the electronic coefficients γ, `0.691`, `0.640`, and `0.689 ± 0.001 mJ/(K²·mol)`. All are 95% confidence limits from the statistical analysis, which, as the abstract says, exclude systematics.

The values come from the published abstract. The 1974 erratum could not be reached.

The elastic Debye temperatures already on the board are kept beside these; the two are not compared. Silicon still has no reachable calorimetric source.

No source for measured heat-capacity ratios of gases could be reached: the Royal Society, ACS, and IOP PDFs were blocked. So that thermo gap stays open, and no ratios are stored.

This adds 6 records.

### Mechanics: CCM.G-K2.2017 absolute-gravity key comparison

This adds the nine official key comparison reference values from Table 5 of the CCM.G-K2.2017 final report (NIM Changping, 2017). Each is stored exactly as printed, with 980 122 000.0 µGal subtracted:

- sites 1–5: `575.1`, `568.9`, `579.0`, `575.6`, `581.1 µGal`;
- sites 6–9: `649.6`, `641.9`, `653.9`, `647.3 µGal`.

All values refer to 1.25 m above the marker, with expanded uncertainties (k=2, 95%) of 1.3–1.4 µGal. The subtracted constant stays in the symbol and is not added back.

Standard gravity was already on the board as `codata2022.g_n` (9.806 65 m/s², exact), so it is not duplicated.

This adds 9 records.

### QED and astrophysics: BASE antiproton q/m, eclipsing binaries, solar abundances

BASE (Borchert et al., Nature 2022) gives the antiproton-to-proton charge-to-mass ratio R = `-1.000 000 000 003(16)`. That is 16 p.p.t. at C.L. 0.68, measured against H⁻ in a Penning trap. The paper's WEP limit is not stored.

Torres, Andersen, and Giménez 2010 give masses for both components of five detached eclipsing binaries, with mean errors as printed:

- V3903 Sgr: `27.27 ± 0.55` / `19.01 ± 0.44 M☉`;
- V1143 Cyg: `1.388 ± 0.016` / `1.344 ± 0.013`;
- AI Phe: `1.2336 ± 0.0045` / `1.1934 ± 0.0041`;
- EW Ori: `1.174 ± 0.012` / `1.1238 ± 0.0089`;
- CM Dra: `0.23102 ± 0.00089` / `0.21409 ± 0.00083`.

Asplund, Amarsi, and Grevesse 2021 give the solar abundance scale:

- photospheric log ε: C `8.46 ± 0.04`, N `7.83 ± 0.07`, O `8.69 ± 0.04`, Fe `7.46 ± 0.04`;
- surface mass fractions: X `0.7438 ± 0.0054`, Y `0.2423 ± 0.0054`, Z `0.0139 ± 0.0006`, Z/X `0.0187 ± 0.0009`.

The printed X, Y, and Z are kept as printed, and no sum is imposed on them.

With these, QED and astrophysics list no gaps. This adds 19 records.

### Mixed square-free radicands, and toolkit status

A complex scalar may now lie in Q(√d, √e, i) when d and e are coprime square-free integers, with basis 1, √d, √e, √(de). √d, √e, and √(de) are the same field. Arithmetic follows the field laws, and an inverse is kept only when both products are 1. The Hermitian matrix [[2, 1, 1], [1, 2, 1], [1, 1, 2]] has eigenvalues 1, 1, and 4. Its spectral factor has columns in Q(√2, √3), and H = U D U† rebuilds exactly. Three or more independent square-free radicands, or two that do not lie in one coprime biquadratic field, stay open.

GOAL.md now carries a TOOLKIT_STATUS section: the mathematics still missing before a derivation or prediction check of general relativity or quantum mechanics against the board can start.

### Hodge star and the inhomogeneous Maxwell equation

The Hodge star of a k-form is the complementary (n-k)-form built from the inverse metric and the exact volume density √|g|, kept only when that density squares back to |det g|. On Minkowski spacetime, ⋆⋆ of a 2-form is minus the form. A uniform charge density with potential A_t = -x²/2 satisfies d⋆F = ⋆(dt). On the Schwarzschild metric, the Coulomb potential A = dt/r has ⋆F = -sin(θ) dθ ∧ dφ and d⋆F = 0 away from the origin.

### Condensed matter and fluids: thermal conductivities, water self-diffusion, helium II viscosity

Ho, Powell, and Liley 1972 (J. Phys. Chem. Ref. Data 1, 279) give thermal conductivities in W cm⁻¹ K⁻¹, read from the scanned reprint:

- copper: `4.03` at 273.2 K and `4.01` at 300 K (recommended, ±2% near room temperature);
- aluminum: `2.36` at 273.2 K and `2.37` at 300 K (recommended, ±5% below room temperature, ±2–3% above);
- silicon: `1.48` at 300 K (recommended, ±5% from 300 to 1000 K);
- diamond at 273.2 K: type I `9.94`, type IIa `26.2`. The table calls these typical values.

The tables print no per-value uncertainty, so the stated accuracies stay in the notes.

Mills 1973 (J. Phys. Chem. 77, 685) gives water self-diffusion at 25 °C:

- measured tracer value for HTO in H₂O: `2.236 ± 0.004` ×10⁻⁹ m²/s;
- calculated pure-water values: H₂O `2.299` and D₂O `1.872`, from Table III.

Donnelly and Barenghi 1998 add recommended values for liquid helium-4:

- viscosity: `1.346` µPa s at 1.5 K, `1.468` at 2.0 K and `3.319` at 4.0 K;
- mutual-friction coefficients B and B′: `1.296` and `0.317` at 1.5 K; `1.024` and `0.052` at 1.8 K.

The Pound-Rebka 1960 gap now closes against the `pound1960.*` records by id. This adds 17 records.

### Variational principles and Noether identities

A mechanical Lagrangian L(q, v, t) has Euler–Lagrange expression d/dt(∂L/∂v) − ∂L/∂q, with the total time derivative taken by the chain rule. The energy E = v ∂L/∂v − L satisfies dE/dt − v EL + ∂L/∂t = 0 identically. The harmonic oscillator L = v²/2 − q²/2 has EL = a + q and E = v²/2 + q²/2. A free particle L = v²/2 has EL equal to the acceleration and canonical momentum v. The pendulum L = v²/2 + cos(q) has EL = a + sin(q). The action is the integral of L; stationarity is the Euler–Lagrange identity.

### Mechanics: GRAIL lunar Love numbers and Earth moments of inertia

The Moon's tidal Love numbers from GRAIL are stored from both analysis groups:

- GSFC (Lemoine et al. 2013), with VCE error sigmas: k₂₀ `0.024615 ± 0.0000914`, k₂₁ `0.023915 ± 0.0000132`, k₂₂ `0.024852 ± 0.0000167`, and a preliminary k₃₀ `0.00734 ± 0.0015`;
- JPL (Konopliv et al. 2013): k₂ `0.02405 ± 0.00018`;
- Williams et al. 2014: the unweighted average `0.02416 ± 0.00022` (R = 1738 km), and the solid Moon's normalized mean moment of inertia Iₛ/MR² `0.392728 ± 0.000012`.

Chen, Li, Ray, Shen, and Huang 2015 give the Earth's principal moments of inertia from the EGM-IERS model: A `80,085.1`, B `80,086.8`, C `80,349.0`, and mean I `80,173.6`, each ± 9.6 ×10³³ kg m².

The Earth's J₂ (`1.0826359e-3`), dynamical flattening, and nominal k₂ and h₂ were already stored from the IERS Conventions (2010). They are nominal model values, not measurements. With these, mechanics lists no gaps. This adds 11 records.

### Atomic: transition probabilities, oscillator strengths, excited-state lifetimes

NIST ASD lines data (queried 2026-11-25) give A and f for these resonance lines:

| Line | A (s⁻¹) | f | ASD accuracy |
|---|---|---|---|
| H Lyman-α to 2p₃/₂ | `6.2647e+08` | `2.7760e-01` | AAA |
| H Lyman-α to 2p₁/₂ | `6.2648e+08` | `1.3880e-01` | AAA |
| Na D2 | `6.16e+07` | `6.41e-01` | AA |
| Na D1 | `6.14e+07` | `3.20e-01` | AA |
| Cs D2 | `3.279e+07` | `7.142e-01` | AAA |
| Cs D1 | `2.863e+07` | `3.435e-01` | AAA |
| Rb D2 | `3.812e+07` | `6.958e-01` | AAA |
| Rb D1 | `3.614e+07` | `3.424e-01` | AAA |

ASD prints accuracy grades, not numeric uncertainties: AAA means ≤ 0.3% and AA means ≤ 1%.

Measured lifetimes, from published abstracts and the arXiv source:

- Na (Volz et al. 1996, 1σ): 3p ²P₁/₂ `16.299(21)` ns and 3p ²P₃/₂ `16.254(22)` ns.
- ⁸⁷Rb (Gutterres et al. 2002): 5P₃/₂ `26.25(8)` ns and 5P₁/₂ `27.75(8)` ns. These come from photoassociation spectroscopy, not a direct decay measurement.
- Cs 6p ²P₃/₂, three results that are all kept: Young et al. 1994 `30.41(10)` ns, Rafac et al. 1999 `30.57 ± 0.07` ns, and Patterson et al. 2015 `30.462(46)` ns.
- Cs 6p ²P₁/₂, two results that are both kept: Young et al. 1994 `34.75(7)` ns and Rafac et al. 1999 `35.07 ± 0.10` ns.

No measured H 2p lifetime was found; only the ASD A values are stored. This adds 25 records.

### Electromagnetism, optics, thermodynamics: susceptibilities, thermo-optic coefficients, heat-capacity ratios

Kaye & Laby (NPL online, Sect. 2.6.6, cited from the Wayback copy because the site is retired) give mass susceptibilities at 20 °C in ×10⁻⁸ m³/kg:

- water `-0.90`;
- bismuth `-1.70`;
- aluminium `+0.82`;
- oxygen `+133.6`;
- copper `-0.107`.

Khatiwada et al. (Meas. Sci. Technol. 27, 025902) measured water's volume susceptibility directly: `-0.716 ± 0.094` ×10⁻⁶ (cgs volume). Their errors are dominated by systematics.

Havens 1933 gives N₂ `-11.938` ×10⁻⁶ (cgs molar). It also gives the provisional O₂ value `3335` ×10⁻⁶ at 20 °C, which is his calibration basis, not a result.

CHARMS thermo-optic coefficients dn/dT, in 1/K, as tabulated:

- Corning 7980 fused silica (Leviton & Frey, arXiv:0805.0091): `9.12E-06` at 0.5 µm, `8.86E-06` at 0.6 µm and `8.48E-06` at 1.0 µm, all at 295 K; `3.60E-06` at 0.5 µm and 100 K.
- Silicon (Frey, Leviton, and Madison 2006): `1.87E-04` at 1.5 µm and `1.70E-04` at 4.0 µm, at 295 K.
- Germanium (same paper): `4.25E-04` at 4.0 µm and 295 K.

Gas heat-capacity ratios, which were unreachable in batch 14, now come from Kaye & Laby Sect. 2.3.6:

- helium `1.63` (0 °C);
- argon `1.667` (0 °C);
- nitrogen `1.401` (20 °C);
- oxygen `1.400` (5–14 °C);
- dry air `1.405` (−79.3 °C);
- carbon dioxide `1.300` (4–11 °C);
- methane `1.307` (20 °C).

None of these print an uncertainty. Electromagnetism now lists no gaps, and the thermo-optic and heat-capacity-ratio gaps close. This adds 22 records.

### Kerr metric and curved FLRW

The Kerr metric in Boyer–Lindquist coordinates, with mass m and spin a, is admitted, and its inverse multiplies back to the identity. Ricci = 0 for Kerr stays outside: the generic Levi-Civita computation exceeds the polynomial degree and term limits. FLRW with spatial curvature k = +1 and k = −1 has an exact Einstein tensor: G_tt is 3 ((da/dt)² + k)/a², and the spatial components satisfy G_ij = -(2 (d²a/dt²)/a + ((da/dt)² + k)/a²) g_ij.

### Spherical harmonics and more hydrogen states

The solid harmonics r^ℓ Y_ℓ^m for ℓ = 0, 1, and 2 are homogeneous polynomials in x, y, z. L² has eigenvalue ℓ(ℓ+1) and Lz has eigenvalue m, checked by applying the angular-momentum operators. Hydrogen radial states for n = 1, 2, 3, and 4, with 0 ≤ ℓ < n, satisfy the radial equation identically.

### Condensed matter: lattice constants beyond silicon

NBS Circular 539 (Swanson et al., 1953), read from the NIST page scans, gives these powder-pattern lattice constants in ångströms:

- aluminium `4.0494`, copper `3.6150`, and germanium `5.6576`, all at 25 °C (Vol. I);
- diamond `3.5667` and sodium chloride `5.6402`, both at 26 °C (Vol. II).

The Ioffe NSM "Basic Parameters at 300 K" pages, read from Internet Archive copies, give Ge `5.658`, GaAs `5.65325`, and diamond `3.567` Å.

Neither source prints an uncertainty. Where the two sources overlap (Ge and diamond), both values are kept. The lattice-constant gap closes. This adds 8 records.

### Thermodynamics: second virial coefficients and critical constants

Kaye & Laby Sect. 3.5 (NPL online, read from the Wayback copy because the site is retired) fits the second virial coefficient as B/(cm³ mol⁻¹) = a − b exp{c (K/T)}. The fit is "usually within experimental errors" over the measured range. The coefficients are stored as printed:

- helium: a `114.1`, b `98.7`, c `3.245`, for 7–150 K;
- argon: a `154.2`, b `119.3`, c `105.1`, for 80–1024 K;
- nitrogen: a `185.4`, b `141.8`, c `88.7`, for 75–700 K.

These are fit coefficients, not measured B values. The page refers readers to Dymond and Smith (1980) for the measurements, which were not reachable. A search of open sources turned up only ab initio B tables, which are excluded.

The same table gives these critical constants:

- helium: T_c `5.19` K, p_c `0.227` MPa;
- nitrogen: T_c `126.2` K, p_c `3.39` MPa;
- carbon dioxide: T_c `304.1` K, p_c `7.38` MPa.

None of these print an uncertainty. The virial-coefficient and critical-point gaps close. This adds 15 records.

### Molecular: vibrational frequencies and rotational constants

The NIST WebBook's Huber–Herzberg diatomic tables give these ground-state harmonic wavenumbers ω_e, in cm⁻¹:

- H₂ `4401.213`;
- N₂ `2358.57`;
- O₂ `1580.193`;
- CO `2169.81358`;
- H³⁵Cl `2990.9463`.

The same tables give these rotational constants B_e, in cm⁻¹:

- H₂ `60.8530`;
- N₂ `1.998241`;
- CO `1.93128087`;
- H³⁵Cl `10.593416`.

Where the WebBook prints the last digit as a subscript, that digit is kept as an ordinary digit. O₂'s B_e is printed in brackets and is not stored.

Shimanouchi's tables (via the WebBook) give the water fundamentals ν₁ `3657`, ν₂ `1595`, and ν₃ `3756` cm⁻¹. All three are rated A, which the table defines as "0~1 cm⁻¹".

The vibrational-frequency and rotational-constant gap closes. This adds 12 records.

### Optics, atomic, nuclear: CIPM frequencies, polarizabilities, medical half-lives

The rest of the 2025 CIPM list of standard frequencies (BIPM data sheets, approved by the CCTF in September 2025 and active from March 27, 2026) gives these frequencies, with relative standard uncertainties:

- ⁴⁰Ca⁺: `411 042 129 776 400.30` Hz (5.5 × 10⁻¹⁶);
- ¹¹⁵In⁺: `1 267 402 452 901 039.07` Hz (1.8 × 10⁻¹⁶);
- ¹⁹⁹Hg: `1 128 575 290 808 154.33` Hz (2.5 × 10⁻¹⁶);
- ¹⁹⁹Hg⁺: `1 064 721 609 899 146.95` Hz (2.5 × 10⁻¹⁶);
- ¹⁷⁶Lu⁺: `353 638 794 073 800.35` Hz (2.8 × 10⁻¹⁵), the mean of three lines;
- ⁸⁷Rb hyperfine: `6 834 682 610.904 312 9` Hz (3.4 × 10⁻¹⁶);
- ⁸⁸Sr: `429 228 066 418 007.008` Hz (1.9 × 10⁻¹⁶);
- ⁸⁸Sr⁺: `444 779 044 095 485.347` Hz (1.7 × 10⁻¹⁶);
- ¹⁷¹Yb⁺ E2: `688 358 979 309 308.31` Hz (1.9 × 10⁻¹⁶);
- ¹⁷¹Yb⁺ E3: `642 121 496 772 645.18` Hz (1.7 × 10⁻¹⁶).

The 2025 list has no ²⁷Al⁺ sheet.

Static polarizabilities:

- cesium: `6.611 ± 0.009` × 10⁻³⁹ C m²/V (Amini & Gould 2003 abstract);
- sodium: `24.11(6)` statistical `(6)` systematic × 10⁻²⁴ cm³ (Ekstrom et al. 1995 abstract);
- helium: `0.208` Å³, from the CCCBDB experimental list, which cites Olney et al. 1997 dipole sum rules.

The helium value is a substitute. Schmidt et al. 2007 measured helium's molar polarizability, but the abstract prints only its ratio to theory, so no value is taken from it.

DDEP half-lives, with uncertainties in the last digits:

- ¹⁸F: `1.82890(23)` h;
- ⁹⁹ᵐTc: `6.0067(10)` h;
- ¹³¹I: `8.0233(19)` d;
- ¹¹C: `20.361(23)` min;
- ¹⁵O: `122.266(49)` s.

The CIPM, polarizability, and medical half-life gaps close, and optics now lists no gaps. This adds 18 records.

### Stokes' theorem on admitted charts

The integral of a top-degree form over an axis-aligned box is the iterated exact definite integral of its coefficient. An antiderivative is kept only when its derivative is the integrand. Stokes' theorem is the identity of that integral of dω with the integral of ω over the oriented boundary. The fundamental theorem on an interval, the unit square, the unit cube, an angular rectangle, and the area of the coordinate sphere, which is 4 pi, are checked identically.

### Tetrad, spin connection, and the curved Dirac operator

The identity tetrad on Minkowski spacetime and the diagonal tetrad of flat FLRW, e^0 = dt and e^i = a(t) dx^i, are admitted. The metric rebuilds from the tetrad, and an inverse tetrad is kept only when both products are the identity. The spin connection is the torsion-free solution of Cartan's first structure equation, checked identically. The Dirac operator is gamma^a e_a^mu (partial_mu + (1/4) omega_mu^{bc} gamma_b gamma_c). On Minkowski it annihilates a constant spinor. On flat FLRW a constant spinor psi satisfies D psi = (3/2) (da/dt)/a gamma^0 psi, checked identically.

### Condensed matter and thermodynamics: saturation magnetization and latent heats

Kaye & Laby Sect. 2.6.6 (Wayback copy) gives these saturation polarizations J_s, with no temperature or uncertainty:

- high-purity iron `2.16` T;
- cobalt `1.76` T;
- nickel `0.615` T.

Danan, Herr and Meyer (1968 abstract) give the absolute saturation at 0 K:

- iron: `221.71 ± 0.08` emu/g, which the paper prints as `2.216` μ_B;
- nickel: `58.57 ± 0.03` emu/g, which the paper prints as `0.616` μ_B.

Myers and Sucksmith (1951) extrapolate hexagonal cobalt to `162.55` at 0 K. The abstract prints no unit, so none is stored.

Nigh, Legvold and Spedding (1963) give gadolinium's absolute saturation moment as `7.55` μ_B per atom.

Kaye & Laby Sect. 3.10.4 gives these latent heats for water:

- enthalpy of fusion `333` J/g;
- enthalpy of vaporization `2257` J/g;
- the Osborne–Stimson–Ginnings values `2500.58` J/g at 273.150 K and `2256.57` J/g at 373.124 K.

Kaye & Laby Sect. 3.10.1 prints molar enthalpies for the elements in units of R·K, and they are stored that way:

- nitrogen: fusion `87` (63.2 K), vaporization `672` (77.34 K);
- helium: fusion `2.4` (3.5 K), vaporization `9.6` (4.22 K).

The ferromagnet and latent-heat gaps close. This adds 17 records.

### Non-constant SU(3) gauge transformation

The rational rotation already checked, embedded in the 1-2 block of SU(3), is a position-dependent special unitary 3x3 matrix in x and y. It acts by A_mu |-> U A_mu U dagger + U d_mu U dagger, and the field strength F = dA + [A, A] transforms as F |-> U F U dagger, checked identically.

### Molecular and chemistry: dipole moments, electrode potentials, solubility products, combustion

The CCCBDB experimental dipole list gives these values in debye:

- H₂O `1.857` (Shostak et al. 1991);
- NH₃ `1.476 ± 0.0029` (Shimizu 1970);
- HCl `1.093`;
- CO `0.112` (NSRDS-NBS 10);
- HF `1.827`.

Kaye & Laby Sect. 3.9.3 gives these standard potentials at 25 °C:

- Li⁺/Li `−3.045` V;
- Na⁺/Na `−2.714` V;
- Zn²⁺/Zn `−0.762 6` V;
- Cu²⁺/Cu `+0.340` V;
- Ag⁺/Ag `+0.799 1` V;
- AgCl/Ag `+0.222 3` V;
- Cl₂/Cl⁻ `+1.358 3` V;
- O₂/H₂O `+1.229` V.

The digit grouping is kept as printed. The page's introduction rounds Zn to −0.763 V.

Kaye & Laby Sect. 3.9.8 gives these pK_s0 values:

- AgCl `9.749`;
- AgBr `12.30`;
- AgI `16.08`;
- BaSO₄ `9.99`;
- CaCO₃ `8.32`;
- CaF₂ `10.31`;
- Mg(OH)₂ `11.3`;
- Fe(OH)₃ `39.43`.

The WebBook gives these enthalpies of combustion:

- methane: `−890.7 ± 0.4` kJ/mol (Pittam & Pilcher) and `−890.35 ± 0.30` kJ/mol (Prosen & Rossini), both kept;
- ethane: `−1560.7 ± 0.3` kJ/mol;
- propane: `−2219.2 ± 0.46` kJ/mol;
- liquid ethanol: `−1367.6 ± 0.3` kJ/mol.

All four molecular gaps close. This adds 26 records.

### Atomic: ionization energies Rb–Cs and isotope shifts

NIST ASD gives first ionization energies for Z = 37–55, each with ASD's own per-row uncertainty. None of these rows is bracketed or parenthesised. Examples:

- Rb `4.1771281 ± 0.0000012` eV;
- Sr `5.69486745 ± 0.00000012` eV;
- In `5.7863558 ± 0.0000005` eV;
- Xe `12.1298437 ± 0.0000015` eV;
- Cs `3.89390572743 ± 0.00000000017` eV.

The H–D 1S–2S isotope shift is `670 994 334 606(15)` Hz (Parthey et al. 2010) and `670 994 334.64(15)` kHz (Huber et al. 1998). Both are kept.

Knollmann, Patel and Doret (2019) measured the Ca⁺ 4s ²S₁/₂ → 3d ²D₅/₂ isotope shifts relative to ⁴⁰Ca⁺:

- ⁴²Ca⁺: `2 771 872 467.6(7.6)` Hz;
- ⁴⁴Ca⁺: `5 340 887 394.6(7.8)` Hz;
- ⁴⁸Ca⁺: `9 990 381 870.0(6.3)` Hz.

The atomic gaps both close, and atomic now lists no gaps. This adds 24 records.

### Nuclear: thermal neutron cross sections, spins, quadrupole moments, Q-values

Sears (1992), as tabulated by NIST NCNR, gives these 2200 m/s absorption cross sections in barns:

- ¹H `0.3326`;
- ³He `5333.(7.)`;
- ⁶Li `940.(4.)`;
- ¹⁰B `3835.(9.)`;
- ¹¹³Cd `20600.(400.)`;
- ¹⁵⁷Gd `259000.(700.)`;
- ²³⁵U `680.9(1.1)`.

ENSDF ground-state spins, read via LiveChart, are stored with parity in the notes: ²H 1⁺, ⁷Li 3/2⁻, ¹⁰B 3⁺, ¹⁴N 1⁺, ¹⁷O 5/2⁺, ²⁷Al 5/2⁺, ¹³³Cs 7/2⁺ and ²³⁵U 7/2⁻.

LiveChart gives these quadrupole moments in barns:

- ²H `0.0028578(3)`;
- ⁷Li `−0.04(3)`;
- ¹⁰B `0.0846(2)`;
- ¹⁴N `0.02044(3)`;
- ¹⁷O `−0.0256(2)`;
- ²⁷Al `0.1466(10)`;
- ¹³³Cs `−0.00343(10)`;
- ²³⁵U `4.936(6)`.

AME2020's reaction-energy files print these Q-values in keV, each with a 1σ uncertainty:

- Q_α: ²¹⁰Po `5407.5307`, ²²⁶Ra `4870.7028`, ²³⁸U `4269.8581`, ²⁴¹Am `5637.8203`;
- Q(d,α) on ³H, which is D–T fusion: `17589.2999 ± 0.0005`;
- Q(d,α) on ³He: `18353.0548 ± 0.0002`;
- Q(d,α) on ⁶Li: `22372.7716`;
- Q(p,α) on ⁷Li: `17346.2440`;
- Q(n,α) on ⁶Li: `4783.4717`;
- Q(n,α) on ¹⁰B: `2789.9082`.

No fission Q-value is printed in the AME files, so none is stored. This closes the cross-section, spin and quadrupole, and Q-value gaps, and adds 33 records.

### Ricci = 0 for the Kerr metric

Ricci = 0 is checked identically in the rational chart x = cos(theta). The metric is a rational function of (r, x, m, a). The denominators Sigma = r^2 + a^2 x^2, Delta = r^2 - 2 m r + a^2, and Xi = 1 - x^2 are kept as named factors and reduced by exact polynomial division. The inverse in that chart multiplies back to the identity. The Einstein tensor vanishes as well.

### Continuum L2 identities and finite-mode Fock space

L2 inner products of polynomial-Gaussian and polynomial-exponential waves are exact integrals. Hermite-Gaussians are orthonormal, and their Fourier transforms are (-i)^n psi_n. Position and momentum act on that domain, and [X, P] = i with hbar = 1. Plane waves are generalized free-particle eigenfunctions, not L2 vectors. The free Gaussian packet satisfies the free Schrodinger equation identically. Finite-mode Fock operators obey the CCR, and the quadratures satisfy [phi, pi] = i.

### Gap catalogue, Bothwell, top-pair cross sections, per-channel Higgs, laser radii

The gap catalogue in `coverage.py` gains eleven entries for physics not yet on the board: the PREM Earth profile, NRL plasma reference values, NuFIT oscillation parameters, PMNS magnitudes, direct CKM determinations, proton spin and structure, Solar Fusion S-factors, ¹²C(α,γ)¹⁶O, superconducting elements, and sound speeds in solids and in other fluids. Each was checked against the board first; the muon g−2 final value, the PDG CKM fit, PDG neutrino mixing, and the Nb/Pb/Al/YBCO/MgB₂/H₃S transition temperatures were already held and got no entry.

The three open gaps close:

- Bothwell 2022: the author accepted manuscript prints `−9.8(2.3)×10⁻²⁰/mm`, `−1.00(12)×10⁻¹⁹/mm` (weighted mean) and `−1.28(27)×10⁻¹⁹/mm` (synchronous), the same as arXiv v1. The typeset Nature version is paywalled and was not read.
- Top pair at 13 TeV: ATLAS `829 ± 1 (stat) ± 13 (syst) ± 8 (lumi) ± 2 (beam)` pb, ATLAS ℓ+jets `830 ± 0.4 ± 36 ± 14` pb, CMS `803 ± 2 ± 25 ± 20` pb, and ATLAS at 13.6 TeV `850 ± 3 ± 18 ± 20` pb. Statistical and systematic parts are stored; luminosity and beam parts stay in the notes, not combined.
- Per-channel Higgs signal strengths: ATLAS from its HEPData record (ggF+bbH `1.026`, VBF `1.1018`, WH `1.1583`, ZH `0.96205`, ttH `0.73963`, tH `6.6137`; bb `0.90952`, WW `1.1951`, ττ `0.9613`, ZZ `1.0415`, γγ `1.0883`, Zγ `2.0991`, μμ `1.2135`) and CMS from Fig. 2 (ggH `0.97`, VBF `0.80`, WH `1.44`, ZH `1.29`, ttH `0.94`, tH `6.05`; γγ `1.13`, ZZ `0.97`, WW `0.97`, ττ `0.85`, bb `1.05`, μμ `1.21`, Zγ `2.59`), each with its 68% interval.
- Charge radii: laser spectroscopy gives ⁸He `1.93(3)` and ⁶He `2.068(11)` fm (Mueller 2007), ⁹Li `2.217(35)` and ¹¹Li `2.467(37)` fm (Sanchez 2006). Sixteen more Angeli-Marinova rows are added, including ⁶He `2.0660(111)` and ¹¹Li `2.4820(430)`; both sides stay.

That adds 53 records.

### General non-constant SU(2)

A non-constant SU(2) matrix is kept in the general form U = [[alpha, beta], [-conj(beta), conj(alpha)]] when alpha and beta are rational functions with values in Q(i), |alpha|^2 + |beta|^2 = 1, both products U U dagger and U dagger U are the identity, and det U = 1. The one-parameter family alpha = (1 - x^2)/(1 + x^2), beta = 2 i x / (1 + x^2) is checked, distinct from the real rational rotation already admitted. It acts by A_mu |-> U A_mu U dagger + U d_mu U dagger, and F |-> U F U dagger, checked identically.

### Tri-quadratic scalars and denesting norms

Complex scalars now lie in the radical tower Q(i), Q(sqrt(d), i), Q(sqrt(d), sqrt(e), i), or Q(sqrt(d), sqrt(e), sqrt(f), i) when d, e, and f are pairwise coprime square-free integers. The real basis is the eight products of 1, sqrt(d), sqrt(e), and sqrt(f). An inverse is kept only when both products are 1. A square root is kept for a nonnegative rational, or for a nonnegative field element that denests in this tower, including sqrt(4 + 2*sqrt(3)) = 1 + sqrt(3). The off-diagonal Hermitian matrix with entries sqrt(2) + sqrt(3) + sqrt(5) has eigenvalues plus or minus that sum and rebuilds exactly. The Hermitian matrix [[2 + sqrt(3), 1], [1, 2 - sqrt(3)]] has a non-rational eigenvector norm that denests in Q(sqrt(2), sqrt(3)) and rebuilds exactly. Four or more independent square-free radicands stay open, as does a minimal polynomial of degree three or more that does not denest in the tower.

### Coulomb continuum identities

The regular reduced Coulomb wave u_l(rho) = rho^{l+1} exp(-i rho) 1F1(l + 1 - i eta; 2 l + 2; 2 i rho) satisfies u'' + (1 - 2 eta / rho - l(l+1)/rho^2) u = 0 identically for l = 0, 1, 2, and 3, after the confluent equation is used to eliminate the second z-derivative. Gamma(1 + i eta) is kept as a named symbol whose modulus identity |Gamma(1 + i eta)|^2 = pi eta / sinh(pi eta) is even and agrees with the recurrence Gamma(z+1) = z Gamma(z). The exact Rutherford amplitude then has modulus squared eta^2 / (4 k^2 sin(theta/2)^4). A general L2 function outside the already admitted classes, completeness of L2, the spectral theorem for an unbounded operator, and a field theory with infinitely many modes stay open.

### Current open math gaps

This list is the current state as of `pgi-0.141.0`. Earlier sections above are historical and are not rewritten when a later slice closes a gap they recorded.
- A general L2 function outside the polynomial-Gaussian and polynomial-exponential classes, completeness of L2 as a metric space, the spectral theorem for an unbounded operator, Coulomb continuum waves and the Rutherford amplitude, and a field theory with infinitely many modes stay outside.

- A radicand or divisor whose sign the exact algebraic or Sturm test cannot decide stays outside.
- A boolean connective whose sides the kernel cannot settle stays outside.
- A polynomial whose resultant would exceed the kernel's degree limit stays outside.
- A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` and `inverse (0::real) = 0` stay refused.
- `primitive.continuum` still blocks `law(sqrt_two_is_rational)`.
- An unbounded quantifier stays open unless a uniform reason covers it. The least-upper-bound proof for a completely general set stays outside.
- A Hermitian matrix whose eigenvalues leave the radical tower Q, Q(√d), Q(√d, √e), or Q(√d, √e, √f), or whose eigenvector norm does not have a square root that denests in that tower, stays open. Four or more independent square-free radicands stay open. An algebraic eigenvalue given only as a minimal polynomial of degree three or more that does not denest in the tower stays open.
- CODATA 2022, PDG 2026, Clemence's Mercury residual, GW150914, the GW170817 bound, and the Planck and Rayleigh–Jeans formulas are on the board. Rayleigh's and Jeans' own pages are not. The modern Mercury fits are on the board since `pgi-0.53.0`. The neutron lifetime, `g_A`, muon and electron `g − 2`, and the proton radius entered in `pgi-0.56.0`. NIST ASD first ionization energies H to Ne entered in `pgi-0.57.0`, and Na to Kr in `pgi-0.59.0`. INPOP perihelion and PPN results entered in `pgi-0.58.0`. AME2020 atomic masses entered in `pgi-0.61.0`. PDG 2026 light hadron masses entered in `pgi-0.62.0`. Binary pulsar, Gravity Probe B, VLBI, and the 16 values of G entered in `pgi-0.63.0`. Hydrogen spectroscopy (1S–2S, Lamb shift, 21 cm, H-alpha, muonic hydrogen) entered in `pgi-0.64.0`. Nuclear constants (deuteron binding, alpha mass, nucleon moments) entered in `pgi-0.65.0`. Stefan–Boltzmann and Wien constants entered in `pgi-0.67.0`. The rest of the gravitational-wave catalogs are not.
