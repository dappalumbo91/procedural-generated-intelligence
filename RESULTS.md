# Results through pgi-0.37.0

Procedural Generated Intelligence (PGI) unfolds answers from compact rules, seeds, and constraints. The store is generative rules, latent seeds, constraint grammars, and context-driven synthesis functions. A prompt arrives, and the kernel saturates the active packs, retracts contradictions, and renders the settled claims at the requested level of detail.

This note records what the folder holds at rule version `pgi-0.37.0`, the goal those rules are for, the architecture that runs them, and the results measured so far. The founding brief is [CONCEPT.md](CONCEPT.md). The reaching goal, with its bars and its five steps, is [GOAL.md](GOAL.md). The running record of each slice is [LOG.md](LOG.md).

## What the kernel holds

The kernel checks closed mathematics and links sourced records. A theorem exists when a checked rule builds it. A measurement enters as `name=value@source`. Two sources that disagree on the same name are retracted together. A bare number is not a measurement. A known mistake stays blocked: re-asserting it contests the board.

In the kernel now:

- The integer ring, under the Lean 4.36 names and the matching Isabelle2025-2 HOL names, with Coq ZArith names recorded beside the equality laws. Exact division only. Non-negative addition and subtraction also reconstruct the result from the digits, and the kernel keeps the step when that reconstruction agrees with the ring.
- Integer order: reflexivity, transitivity, antisymmetry, addition on the left, `Int.le_of_eq`, a true numeral comparison, and the negation of a false one. A compound side is compared after the equality rules reduce it.
- Closed rationals: a reduced fraction, positive denominator, sign on the numerator. Field operations cite the Lean `Rat` operations and the Isabelle `Rat.thy` lemmas. Division by zero stays open.
- A Cauchy continuum for the sequences this kernel can check, from Isabelle `Real.thy`. Constant sequences are the rationals. A positive square root is a bisection sequence with a checked modulus. Order is a strict rational enclosure. Core Lean 4.36 has no `Real`.
- Nested radicals the rules below can see: a tower `base^(odd/2^k)`, a binomial nest, a two-radical sum that denests, the pair `sqrt(sqrt(2) + sqrt(5))` through every further finite outer square root, the nested binomial `sqrt(2 + sqrt(2))` through every further finite outer square root, a two-prime biquadratic under one square root when it does not denest, and a nest times a pair as the square root of the product of those insides.
- Inverses inside the admitted span, including `1 / sqrt(sqrt(2) + sqrt(3))`, which is the conjugate difference of the two nests that denesting already produced. Arithmetic in a finite square-root tower over Q is one checked rule: an element is a vector on the basis of products of the adjoined square roots, multiplication follows `(a + b√d)(c + e√d) = (ac + bed) + (ae + bc)√d`, and the inverse is the conjugate over the norm, taken down the tower and kept only when it multiplies back to 1. Named ladder levels, a summit, an apex, a shell, and any further finite depth use that one rule.
- Finite sets of those reals. The least upper bound of a nonempty finite set is its maximum.
- Quantifiers over a finite enumeration. Separation over a finite enumeration. Order rays, the set of every real, and two-sided intervals. Nested conjunction, double negation, implication by `imp_conv_disj`, and a disjunction or union of rays when they overlap or touch. A comparison that is affine in the binder cancels to a standard ray, to UNIV, to the empty set, or to a singleton. The supremum of a down-ray is the bound it contains. The supremum of an open upper end is built by the Archimedean bisection in the proof of `complete_real`. An identically true affine comparison, such as `{x. x <= x + 1}`, is UNIV and is not bounded above.
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

`python -m unittest discover -s tests -v` at pgi-0.37.0 finished 117 tests, 0 failures, in 49.137 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH. That is the about 49.14 seconds in the table. One test calls GNU Octave through the portable lookup.

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
