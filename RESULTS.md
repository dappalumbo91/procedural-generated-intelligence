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

### Precision particle measurements: neutron lifetime, g_A, g − 2, and the proton radius

The precision particle numbers are on the board as measured anchors, each copied as its source prints it.

Neutron lifetime. UCNτ, Gonzalez et al., Phys. Rev. Lett. 127, 162501 (2021): `877.75 ± 0.28 stat +0.22/−0.16 syst s`. UCNτ, Musedinovic et al., Phys. Rev. C 111, 045501 (2025), all UCNτ data averaged: `877.82 ± 0.22 stat +0.20/−0.17 syst s`. NIST beam method, Yue et al., Phys. Rev. Lett. 111, 222501 (2013): `887.7 ± 1.2 stat ± 1.9 syst s`. PDG 2026 average (S017T): `878.3 ± 0.4 s` with scale factor 1.8. It uses eight stored-neutron results and lists the beam results without using them. A new uncertainty kind, `statistical and systematic, printed separately`, keeps the two parts apart. The board never combines them. The tests combine them only to compare numbers.

Axial coupling. PDG 2026 (S017AV): `λ = g_A/g_V = −1.2753 ± 0.0013` with scale factor 2.7. Muon `g − 2`. The final Fermilab result, Aguillard et al., Phys. Rev. Lett. 135, 101802 (2025), Runs 1–6 combined: `a_μ = 116 592 0705(148) × 10^−12` (127 ppb). The experimental world average from the same paper: `116 592 0715(145) × 10^−12` (124 ppb). PDG 2026 prints `0.00116592072 ± 0.00000000015`, and CODATA 2022 gives `1.165 920 62(41) × 10^−3`. Electron. Fan, Myers, Sukra, and Gabrielse, Phys. Rev. Lett. 130, 071801 (2023): `g/2 = 1.001 159 652 180 59(13)` (0.13 ppt). PDG 2026 prints `a_e = 0.00115965218062 ± 0.00000000000012`, and CODATA 2022 gives `1.159 652 180 46(18) × 10^−3`. Proton charge radius. CODATA 2022: `8.4075(64) × 10^−16 m`. PDG 2026: `0.8407 ± 0.0006 fm`, whose only input is the CODATA value.

The tests check the following. PDG's lifetime agrees with UCNτ 2025. The beam and UCNτ 2025 lifetimes differ by more than four combined uncertainties, and all four lifetime records stay linked with none retracted. The Fermilab, PDG, and CODATA muon anomalies agree with the world average. Fan's `g/2 − 1` agrees with the CODATA and PDG `a_e`. The CODATA radius in metres matches PDG's in femtometres. No Standard Model prediction is stored. That is 11 new particle quantities and 3 new CODATA constants, 14 new records in all.

### NIST ASD first ionization energies, H to Ne

The first ionization energies of the ten neutral atoms from hydrogen to neon are on the board as measured anchors. They come from the NIST Atomic Spectra Database, version 5.12 (7 November 2024), Kramida, Ralchenko, Reader, and NIST ASD Team, doi:10.18434/T4W30F, served by the Ionization Energies form in eV with the uncertainty column on. The values are H `13.598434599702 ± 0.000000000012`, He `24.587389011 ± 0.000000025`, Li `5.391714996 ± 0.000000022`, Be `9.322699 ± 0.000007`, B `8.298019 ± 0.000003`, C `11.2602880 ± 0.0000011`, N `14.53413 ± 0.00004`, O `13.618055 ± 0.000007`, F `17.42282 ± 0.00005`, and Ne `21.564541 ± 0.000007` eV.

Each row keeps its ASD bibliography codes, ground shells, ground level, and ionized level. ASD prints the hydrogen value in parentheses. Its help page says that marks an energy from an ab-initio calculation, or otherwise not derived from evaluated experimental data, and the record says so. ASD stores these energies in cm^-1 and folds the CODATA conversion uncertainty into eV output. The help page names no confidence level for the uncertainty column, so the rows are labelled `uncertainty as printed, level not stated`. CODATA 2022 `R_∞ hc = 13.605 693 122 990(15) eV` is added beside them.

The tests check every row's value and uncertainty, that helium is the largest and lithium the smallest of the ten, and that hydrogen's energy lies below `R_∞ hc` and within `α^2` of the reduced-mass ratio `m_p/(m_p + m_e)`. That window is loose on purpose. It is a test, not a stored relation. That is 11 new records.

### INPOP perihelion and PPN results

The INPOP team's general-relativity results are on the board, each with the uncertainty kind its paper states. Neither IMCCE note for INPOP19a (NST S109, December 2019) nor for INPOP21a (NST S110, 2021) prints PPN `β` or `γ`, so the PPN numbers come from the papers built on those ephemerides.

INPOP20a, Fienga et al., Proc. IAU Symposium 364, 31–51, Table 4, "confidence intervals given at 99.7 % of the reference WRSS distribution": `β − 1 = (−1.12 ± 7.16) × 10^−5`, `γ − 1 = (−1.69 ± 7.49) × 10^−5`. These are stored under a new kind, `99.7% interval`. From the same table, the direct least-squares row is `β − 1 = (−1.9 ± 6.28) × 10^−5` and `γ − 1 = (2.64 ± 3.44) × 10^−5`. No level is named for that row, so it is labelled `level not stated`. The Living Reviews table reprints the least-squares `β − 1` as `+1.9`. The record keeps the original paper's sign and notes the difference.

INPOP15a, Fienga, Laskar, Manche, and Gastineau, Proc. 14th Marcel Grossmann Meeting, Table 1: Mercury's possible supplementary perihelion advance is `0.0 ± 3.1` mas/cy under `Δ(O − C) < 35%` and `0.0 ± 1.05` mas/cy under `Δ(O − C) < 5%`. These are ranges of acceptable refitted ephemerides, not confidence intervals. They get a new kind, `acceptance interval`.

Sun `J2`: INPOP19a `(2.010 ± 0.010) × 10^−7` (± 1σ column), and INPOP21a with the Lense–Thirring term `(2.2180 ± 0.01) × 10^−7` (level not stated). The two IMCCE notes print different INPOP19a `GM_⊙` values, 40.042 ± 0.01 and 42.0322 ± 0.13 for `GM − 132712440000` km³ s⁻². Neither is stored, and the disagreement is written on the record. Fienga and Minazzoli, Living Rev. Relativ. 27, 1 (2024), Eq. (102), give the overlap of published ephemeris intervals: `β − 1 = (−0.45 ± 1.75) × 10^−5` and `γ − 1 = (0.55 ± 1.35) × 10^−5`. That is an overlap of intervals with no named level. Mariani et al., A&A 682, A175 (2024), ran INPOP21a in an MCMC (B-INPOP) with a uniform prior `0 ≤ 1 − γ ≤ 15 × 10^−5`. Their upper limits on `1 − γ` are `1.73`, `2.40`, and `2.50 × 10^−5` at 66.7%, 95%, and 99.7% C.L. They are stored as three bounds whose lower end is the prior edge.

The tests check that every printed PPN and perihelion interval contains zero, that the tighter acceptance window sits inside the looser one, that the overlap sits inside the INPOP20a WRSS intervals, and that the B-INPOP limits grow with the level. A `ppn gamma` ask links INPOP, Cassini, and B-INPOP together with nothing retracted. The Cassini record gains a note that Mariani et al. read its `±2.3 × 10^−5` as 1σ. Its label stays `level not stated` because Bertotti et al. do not say. That is 10 new quantities and 3 new bounds, 13 new records.

### Current open math gaps

This list is the current state as of `pgi-0.58.0`. Earlier sections above are historical and are not rewritten when a later slice closes a gap they recorded.

- A radicand or divisor whose sign the exact algebraic or Sturm test cannot decide stays outside.
- A boolean connective whose sides the kernel cannot settle stays outside.
- A polynomial whose resultant would exceed the kernel's degree limit stays outside.
- A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` and `inverse (0::real) = 0` stay refused.
- `primitive.continuum` still blocks `law(sqrt_two_is_rational)`.
- An unbounded quantifier stays open unless a uniform reason covers it. The least-upper-bound proof for a completely general set stays outside.
- Charts, transition maps that compose to the identity, Jacobians, tangent vectors, and the metric tensor, then differential geometry, Hilbert space, and gauge theory, are still ahead of any physical law.
- CODATA 2022, PDG 2026, Clemence's Mercury residual, GW150914, the GW170817 bound, and the Planck and Rayleigh–Jeans formulas are on the board. Rayleigh's and Jeans' own pages are not. The modern Mercury fits are on the board since `pgi-0.53.0`. The rest of the gravitational-wave catalogs are not.
