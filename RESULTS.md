# Results through pgi-0.28.0

Procedural Generated Intelligence (PGI) unfolds answers from compact rules, seeds, and constraints. The store is generative rules, latent seeds, constraint grammars, and context-driven synthesis functions. A prompt arrives, and the kernel saturates the active packs, retracts contradictions, and renders the settled claims at the requested level of detail.

This note records what the folder holds at rule version `pgi-0.28.0`, the goal those rules are for, the architecture that runs them, and the results measured so far. The founding brief is [CONCEPT.md](CONCEPT.md). The reaching goal, with its bars and its five steps, is [GOAL.md](GOAL.md). The running record of each slice is [LOG.md](LOG.md).

## What the kernel holds

The kernel checks closed mathematics and links sourced records. A theorem exists when a checked rule builds it. A measurement enters as `name=value@source`. Two sources that disagree on the same name are retracted together. A bare number is not a measurement. A known mistake stays blocked: re-asserting it contests the board.

In the kernel now:

- The integer ring, under the Lean 4.36 names and the matching Isabelle2025-2 HOL names, with Coq ZArith names recorded beside the equality laws. Exact division only. Non-negative addition and subtraction also reconstruct the result from the digits, and the kernel keeps the step when that reconstruction agrees with the ring.
- Integer order: reflexivity, transitivity, antisymmetry, addition on the left, `Int.le_of_eq`, a true numeral comparison, and the negation of a false one. A compound side is compared after the equality rules reduce it.
- Closed rationals: a reduced fraction, positive denominator, sign on the numerator. Field operations cite the Lean `Rat` operations and the Isabelle `Rat.thy` lemmas. Division by zero stays open.
- A Cauchy continuum for the sequences this kernel can check, from Isabelle `Real.thy`. Constant sequences are the rationals. A positive square root is a bisection sequence with a checked modulus. Order is a strict rational enclosure. Core Lean 4.36 has no `Real`.
- Nested radicals the rules below can see: a tower `base^(odd/2^k)`, a binomial nest, a two-radical sum that denests, the pair `sqrt(sqrt(2) + sqrt(5))` through every further finite outer square root, and the nested binomial `sqrt(2 + sqrt(2))` through every further finite outer square root.
- Inverses inside the admitted span, including `1 / sqrt(sqrt(2) + sqrt(3))`, which is the conjugate difference of the two nests that denesting already produced.
- Finite sets of those reals. The least upper bound of a nonempty finite set is its maximum.
- Quantifiers over a finite enumeration. Separation over a finite enumeration. Order rays, the set of every real, and two-sided intervals. The supremum of a down-ray is the bound it contains. The supremum of an open upper end is built by the Archimedean bisection in the proof of `complete_real`.
- Boolean connectives the kernel can settle: a conjunction of two comparisons, the complement of an order ray, and a disjunction of two closed equalities.
- A link board of sourced records in `pgi/corpus/records.py`. Asking about a subject unfolds the record. The record is not a settled answer. Re-asserting a forbidden law contests that law against the record.
- One domain pack: causal path risk from weather, cover, and light.
- GNU Octave 11.3.0 cross-checks closed integers inside the exact range of an IEEE double. One test calls it. Octave is not used for rationals, reals, sets, or this root.

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

`python -m unittest discover -s tests -v` at pgi-0.28.0 finished 112 tests, 0 failures, in 5.304 seconds, on Python 3.14. That is the about 5.30 seconds in the table. One test still calls GNU Octave 11.3.0.

### Why the two open radicals stayed open, and what closed them

`sqrt(sqrt(sqrt(2 + sqrt(2))))` stayed open because the square-root rule had a branch for one binomial nest and branches for the pair ladder, and no branch for one further square root of that nest. The positive nest has no last outer square root. pgi-0.28.0 stores every further finite depth as fold data and certifies it by one outer square plus the comparison already used for the deep. `sqrt(sqrt(sqrt(2 + sqrt(2))))` is `cauchy(sqrt(sqrt(sqrt(2 + sqrt(2)))))`, and its square is `sqrt(sqrt(2 + sqrt(2)))`. One more square root is the same rule. Its product with `sqrt(sqrt(sqrt(2 - sqrt(2))))` is `sqrt(sqrt(sqrt(2)))`.

`1 / sqrt(sqrt(2) + sqrt(3))` stayed open because the inverse reader expected one nest plus its `sqrt(rad)` partner. The denesting is a sum of two nests, and the second nest is not that partner. Their squares differ by the rational 1, so the inverse is the conjugate difference already admitted by the denesting: `cauchy(-1/2 * sqrt(-2 + 2 * sqrt(3)) + 1/2 * sqrt(2 + 2 * sqrt(3)))`. It multiplies back to 1. The same rule gives the inverse of `sqrt(sqrt(6) + sqrt(2))` as `cauchy(-1/4 * sqrt(-4 + 2 * sqrt(6)) + 1/4 * sqrt(4 + 2 * sqrt(6)))`.

### Still outside

The inverse of `sqrt(sqrt(sqrt(2 + sqrt(2))))` stays outside: the inverse of the deep is a difference of two deeps, and that quotient has no rule yet. `sqrt(1 + sqrt(2) + sqrt(5))` stays outside. A nest times the pair stays outside. `1 / (1 + sqrt(sqrt(sqrt(2 + sqrt(2)))))` stays outside, as does `1 / (1 + ...)` on the pair ladder. A boolean connective the kernel cannot settle, a set whose upper-bound predicate the kernel cannot decide, a nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero stay outside. A negative radicand stays open. Division by zero stays open.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Isabelle `real_sqrt_minus` and `inverse (0::real) = 0` stay refused.
