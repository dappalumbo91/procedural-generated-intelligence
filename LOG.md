# Log

## 2026-11-24 — kernel pgi-0.1.0

First runnable slice. From this folder, `python -m unittest discover -s tests -v` finished 24 tests, 0 failures, about 0.011 seconds, on Python 3.14.

The kernel derives a 64-bit seed from the rule version, the ask, and the sorted facts. An explicit seed is kept as given. The base pack unfolds one addition or one subtraction from the digits, including carry. The causal pack unfolds path risk from rain, cover, freezing, and dusk. Rules saturate, then a contradiction and every claim that rests on it are retracted together, so rule order cannot pick a winner.

Lod 0 is the stage outline. Lod 1 names the claims. Lod 2 adds the detail line chosen by the seed. A zoom raises one rule without recomputing the claim set. `rules/local.json` can add a rule and ships as an empty list.

An ask outside the packs stays an open gap. That includes open English. Learned modules are not in this slice.

## 2026-11-24 — integer kernel pgi-0.2.0

`python -m unittest discover -s tests -v` finished 32 tests, 0 failures, about 0.29 seconds, on Python 3.14. One of those tests calls the local GNU Octave 11.3.0.

The base pack now asks `pgi/math` for a theorem. The kernel accepts equality, symmetry, transitivity, congruence, and the integer ring laws under the names checked on this machine: Lean 4.36.0 (`Int.add_comm`, `Int.add_assoc`, `Int.add_zero`, `Int.zero_add`, `Int.add_left_neg`, `Int.add_right_neg`, `Int.neg_neg`, `Int.sub_eq_add_neg`, `Int.mul_comm`, `Int.mul_assoc`, `Int.mul_one`, `Int.one_mul`, `Int.mul_zero`, `Int.zero_mul`, `Int.mul_add`, `Int.add_mul`) and the matching assumptions in `Isabelle2025-2/src/HOL/Groups.thy` and `Rings.thy`. Coq's ZArith names for the same equations are recorded beside them. A forged `1 + 1 = 3` is rejected by the checker.

Closed expressions reduce through those rules. Non-negative sums and differences also rebuild the integer from the digits, and the step stands only when both paths agree. `17 + 13 + 1` is 31. `2 + 3 * 4` is 14. `(2 + 3) * 4` is 20. `8 / 2` is 4. `8 / 3` and `8 / 0` stay open. Octave agreed on eight closed integers. Its floating division was not adopted.

`x + 0` simplifies by `Int.add_zero`. `(x - x) + 1` reduces to 1. An observable is a fact `name=value@source`. `length=4@meter stick` and `width=3@meter stick` give `length * width = 12`. The same name from two sources, 4 and 5, is retracted and the answer stays open. `length=4` with no source does not bind.

Order, real numbers, sets, quantifiers, and physics are still outside the kernel. The observable anchor is the socket those rules will use.

## 2026-11-24 — goal and link board pgi-0.3.0

The reaching goal is [GOAL.md](GOAL.md). A theorem remains the way a claim settles. It is not the whole system. Sourced records in `pgi/corpus/records.py` link onto the board when an ask names them, and a re-asserted forbidden law is contested instead of blended.

The board holds the OPERA fibre-optic timing retraction (CERN, 8 June 2012 update), the Michelson–Morley null result with the FitzGerald–Lorentz caveat (American Journal of Science 34 (1887) 333–345), the Goroff–Sagnotti two-loop divergence, the Super-Kamiokande 2020 partial-lifetime bounds (`2.4e34` and `1.6e34` years at 90% CL), the BIPM definition `c = 299792458` m/s, and Weinberg's 1989 cosmological-constant problem with no ratio stored. None of these emits a `value(...)` atom.

Integer order is in the kernel for numerals and for `x <= x`: Lean 4.36 names `Int.le_refl`, `Int.le_trans`, `Int.le_antisymm`, `Int.add_le_add_left`, and `Int.not_le`, matched to Isabelle `order_refl`, `order_trans`, `order_antisym`, `add_left_mono`, and `not_le`. `prove 2 <= 5` is `le(2,5)`. `prove 5 <= 2` is `not_le(5,2)`. Compound inequalities stay open. Totality on free variables is not applied.

CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are not ingested. Rayleigh–Jeans is named in the goal as the next known mistake and is not a record yet.

`python -m unittest discover -s tests -v` finished 39 tests, 0 failures, about 0.33 seconds, on Python 3.14. One test still calls GNU Octave 11.3.0.

## 2026-11-24 — compound order pgi-0.4.0

A compound inequality is proved from the equality kernel. `prove 1 + 1 <= 3` reduces `1 + 1` to 2 by `Int.add`, then compares 2 and 3. `prove 3 <= 1 + 1` is rejected by `Int.not_le` after the same reduction. `prove x + 0 <= 0 + x` uses `Int.add_zero`, `Int.zero_add`, and `Int.le_of_eq`. Lean 4.36.0 accepted `Int.le_of_eq`. Isabelle's matching lemma is `eq_refl` in the preorder class of `Orderings.thy`: `x = y ⟹ x ≤ y`. `not_le_by_eq` is the kernel's transfer of a rejected numeral comparison across those equalities. It is not a separate Lean declaration. Two free variables still do not receive a direction. `8 / 3 <= 4` stays open because the quotient is not an integer.

`known.rayleigh_jeans` is on the board. Rayleigh, Phil. Mag. 49 (1900) 539–540. Jeans, Phil. Mag. 10 (1905) 91–98, and Proc. R. Soc. A 76 (1905) 545–552. The record blocks classical equipartition as the blackbody law. It does not store a spectral formula.

The rationals are the next mathematical primitive. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 40 tests, 0 failures, about 0.30 seconds, on Python 3.14. One test still calls GNU Octave 11.3.0.

## 2026-11-24 — rationals pgi-0.5.0

Closed rationals are in the kernel. A value is a reduced fraction with a positive denominator and a coprime numerator, the form Lean `Rat.normalize` and Isabelle `Rat_cases` use. Sign stays on the numerator. `8 / 6` is 4/3. `1/2 + 1/3` is 5/6. `1/2 * 2/3` is 1/3. `1/2 - 1/3` is 1/6. `-1/2` is -1/2. A denominator of 1 is an integer, so `(8 / 6) * 3` is 4 and `(1 / 2) / (1 / 4)` is 2. An exact integer quotient stays on the integer path: `8 / 2` is still 4, and `0 / 5` is still 0 by `Int.ediv`.

The operations cite Lean `Rat.add`, `Rat.mul`, `Rat.neg`, `Rat.sub`, `Rat.div`, and `Rat.normalize`. The Isabelle statements read from `Rat.thy` are `add_rat`, `mult_rat`, `minus_rat`, `diff_rat_def`, `diff_rat`, `divide_rat`, `eq_rat`, and `le_rat`. Equality is cross multiplication. Comparison of positive denominators is the same cross multiplication, then the integer comparison. `prove 8 / 3 <= 4` holds. `prove 1 / 2 <= 1 / 3` is rejected. `prove 2 / 4 = 1 / 2` holds by `eq_rat`. `prove 8 / 2 <= 5` still uses the integer order path.

Lean 4.36.0, with no imports, evaluates `(1 : Rat) / 0` to 0, and Isabelle sets `Fract a 0 = Fract 0 1`. This kernel refuses both. `8 / 0` stays open. A free variable does not receive a field identity: `prove x / x = 1` stays open. Octave is not used for rationals. `primitive.rationals` is on the board and blocks `law(division_by_zero_is_zero)`.

The next mathematical primitive is a constructed continuum. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 47 tests, 0 failures, about 0.30 seconds, on Python 3.14. One test still calls GNU Octave 11.3.0.

## 2026-11-24 — Cauchy reals pgi-0.6.0

The continuum in this kernel is the construction in Isabelle2025-2 `Real.thy`: a real is an equivalence class of Cauchy sequences of rationals. `cauchy` demands a modulus. `realrel` identifies two Cauchy sequences when their difference vanishes. `of_rat` is the constant sequence. Core Lean 4.36 has no `Real`; `#check Real` is an unknown identifier.

Constant sequences are the rationals already in the kernel. A positive square root is the bisection sequence on a rational interval whose squares bracket the radicand. The width is the initial width divided by `2^k`, and that equality is checked. The square gap is at most the width times twice the initial upper bound, so the squared sequence differs from the radicand by a vanishing sequence. Square factors move into the coefficient. `sqrt(4)` is 2. `sqrt(4/9)` is 2/3. `sqrt(2)` is the class `cauchy(sqrt(2))`. `sqrt(8)` is `2 * sqrt(2)`. `sqrt(2) * sqrt(2)` is 2. `sqrt(2) + sqrt(8)` is `3 * sqrt(2)`.

Order is a strict rational enclosure of those sequences. `prove sqrt(2) <= 3/2` holds. `prove sqrt(2) <= 1` is rejected. Equality is identity of the normal form. A negative radicand stays open. `sqrt(sqrt(2))` stays open. Division by zero stays open. Division by a different non-rational stays open. The same nonzero class divided by itself is 1. Isabelle proves `inverse (0::real) = 0`. That convention is refused.

`complete_real` is a least upper bound for a nonempty set of reals that is bounded above. Sets are not objects here, so that statement is not a rule. `primitive.continuum` is on the board and blocks `law(sqrt_two_is_rational)`. Octave is not used for reals.

The next mathematical primitive is a set. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 56 tests, 0 failures, about 0.33 seconds, on Python 3.14. One test still calls GNU Octave 11.3.0.

## 2026-11-24 — Finite sets pgi-0.7.0

A set in this kernel is a finite enumeration of reals the earlier slices can already check. Isabelle `Set.thy` gives `empty`, `insert`, `member`, `insert_iff`, `empty_iff`, `Un_iff`, `Int_iff`, `subset_eq`, and `set_eqI`. `Finite_Set.thy` gives `finite.emptyI`, `finite.insertI`, `finite_Un`, and `finite_Int`. The same elements in another order are the same set. A repeated element is one member. `{2, 2, 1}` is `{1, 2}`. `{1, 2} union {2, 3}` is `{1, 2, 3}`. `{1/2, 1/3}` is `{1/3, 1/2}`.

`complete_real` says a nonempty set of reals that is bounded above has a least upper bound. For a finite enumeration the maximum is that bound. The check uses `Max_in`, `Max_ge`, `bdd_aboveI`, `cSup_eq_maximum`, and `cSup_eq_Max`. `sup {1, 2, sqrt(2)}` is 2. `sup {1, sqrt(2)}` is the class `cauchy(sqrt(2))`. `sup {1/3, 1/2}` is 1/2. A singleton uses `cSup_singleton`. The empty set is outside the statement. An arbitrary set, and a comprehension, stays outside the rule because it needs a quantifier.

Core Lean 4.36.0 resolves `EmptyCollection`, `Membership`, `Insert`, `Union`, `Inter`, and `Singleton`. `#check Set` and `#check Finset` are unknown identifiers. Octave is not used for sets. A forged membership, equality, or supremum is rejected. `primitive.finite_set` is on the board and blocks `law(empty_set_has_a_least_upper_bound)`.

The next mathematical primitive is a quantifier. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 64 tests, 0 failures, about 0.35 seconds, on Python 3.14. One test still calls GNU Octave 11.3.0.

## 2026-11-24 — Quantifiers pgi-0.8.0

A quantifier in this kernel is Isabelle `Ball` or `Bex` over a finite enumeration, plus a small unbounded fragment. `all x in {1, 2}. x <= 2` holds by `ballI`. A failing universal names the first counterexample, by `ball_simps`. `ex x in {1, 2, 3}. x = 2` names the witness 2, by `bexI`. The empty universal holds (`ball_empty`) and the empty existential fails (`bex_empty`). That body is not evaluated.

`prove complete {1, sqrt(2)}` is the finite form of `complete_real`. The witness is the class `sqrt(2)`. The check uses `ex_in_conv`, `ballI`, `Max_ge`, `bexI`, `Max_in`, `bspec`, and `Max_le_iff`, then cites `cSup_eq_maximum` and `cSup_eq_Max`. The proof for an arbitrary set stays outside the rule. `complete {}` stays open.

Leastness `all z. (all x in {1, 2}. x <= z) --> 2 <= z` holds by `impI`, `allI`, and `bspec` because 2 is a member. The same shape for 3 is refuted at the maximum 2 by `spec`. A bound below the maximum stays open. The empty set stays open.

Unbounded `all x. x <= x` and `ex x. x = x` are `allI` and `exI` with the axiom `refl`. `ex x. x = 1 + 1` uses the closed term as the witness. `all x. x <= 1` and `ex x. x <= 5` stay open. A finite check does not prove an unbounded quantifier. `primitive.quantifier` blocks `law(finite_checks_prove_an_unbounded_quantifier)`.

Core Lean 4.36.0 resolves `Exists`, `And`, `Not`, `Iff`, `True`, `False`, and `Decidable`. `#check forall` is a keyword, not a constant. Octave is not used for quantifiers. A comprehension `{x. P x}` stays outside the rule.

The next mathematical primitive is an arbitrary set. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 74 tests, 0 failures, about 0.37 seconds, on Python 3.14. One test still calls GNU Octave 11.3.0.

## 2026-11-25 — Comprehension pgi-0.9.0

A comprehension in this kernel is Isabelle `Collect`, on the fragment that stays a finite checked set. Separation `{x in {1, 2, 3}. x <= 2}` is `{1, 2}`. Each member is kept or dropped by `mem_Collect_eq`, `CollectI`, and `CollectD`. `Collect_subset` and `finite_subset` make the result a finite subset of the domain. The empty domain is `{}`, and that body is not evaluated. A filter that no member satisfies is the empty set. An open comparison stays unsettled and does not emit a partial subset.

`{x. x = 2}` is `{2}` by `singleton_conv`. `{x. sqrt(2) = x}` is `{sqrt(2)}` by `singleton_conv2`. `{x. x = x}`, `{x. x <= x}`, and `{x. x <= 2}` stay open. They are not finite enumerations. `prove 1 in {x. x <= 5}` holds. `prove 9 in {x. x <= 5}` does not. `{} subset {x. x / 0 <= 1}` holds by `empty_subsetI`, and that body is not evaluated. `{x. x <= 1 + 1}` and `{x. x <= 2}` are the same set by `Collect_cong`.

`sup {x in {1, sqrt(2), 3}. x <= 2}` is the class `sqrt(2)`. `prove complete {x in {1, sqrt(2), 4}. x <= 2}` exhibits the maximum of `{1, sqrt(2)}`. The proof of `complete_real` for an arbitrary set stays outside the rule. `primitive.comprehension` blocks `law(every_real_predicate_is_a_finite_set)`.

Core Lean 4.36.0, with no imports, does not resolve `Collect`, `Set.sep`, or `setOf`. Octave is not used for comprehensions.

The next mathematical primitive is an arbitrary set. An unbounded predicate that is not the singleton equality stays open. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 84 tests, 0 failures, about 0.41 seconds, on Python 3.14. One test still calls GNU Octave 11.3.0.

## 2026-11-25 — Arbitrary set pgi-0.10.0

An arbitrary set in this kernel is an order ray or the set of every real. `{x. x <= 2}` is atMost 2, by Isabelle `atMost_def` and `atMost_iff`. `{x. sqrt(2) <= x}` is atLeast of that class. `{x. x = x}` and `{x. x <= x}` are UNIV, by `UNIV_def` and reflexivity. `infinite_Iic` and `infinite_Ici` say a ray is not a finite enumeration. The witness that a ray has a real above it, and a real below it, is the bound shifted by 1, and the kernel checks that comparison before it emits the witness. `less_add_one` is that shift.

`{x. x <= 1}` is a subset of `{x. x <= 2}` by `atMost_subset_iff`. `{x. x <= 1}` is not equal to `{x. x <= 2}`. `{x. x <= 2}` intersect `{x. 2 <= x}` is the singleton of 2, by `atMost_Int_atLeast`. `{x. x <= 1}` intersect `{x. x <= 2}` is atMost 1, by `Int_atMost`. Two up-rays meet at the greater bound by `atLeast_iff`. A proper overlap such as `{x. 1 <= x}` intersect `{x. x <= 3}` stays open: a two-sided interval stays outside this rule.

`prove all x in {y. y <= 5}. x <= 5` holds. A failing quantifier names a witness on the ray. `sup {x. x <= 5}` and `prove complete {x. x <= 5}` stay open. The proof of `complete_real` for an order ray stays outside this rule. `primitive.arbitrary_set` blocks `law(an_order_ray_is_a_finite_enumeration)`.

Core Lean 4.36.0, with no imports, does not resolve `Set.Iic`, `Set.Ici`, or `Set.univ`. Octave is not used for order rays.

The next gap is the least upper bound of an order ray. A two-sided interval stays outside. Boolean connectives inside a predicate stay outside. Nested radicals and division by a different irrational stay open. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested. The Theory of Everything criteria in GOAL.md remain unmet.

`python -m unittest discover -s tests -v` finished 95 tests, 0 failures, about 0.40 seconds, on Python 3.14. One test still calls GNU Octave 11.3.0.

## 2026-11-25 — Least upper bound of a down-ray pgi-0.11.0

`complete_real` says a nonempty set of reals that is bounded above has a least upper bound. For the down-ray `{x. x <= a}` the bound is already a member, by `atMost_iff` and `order_refl`, and `bdd_above_Iic` says that same bound is an upper bound. `cSup_eq_maximum` names a member that bounds the set as the supremum. `cSup_atMost` is that fact for `{..x}`: the supremum is `x`. `sup {x. x <= 5}` is 5. `sup {x. x <= sqrt(2)}` is the class `sqrt(2)`. `prove complete {x. x <= 5}` states that claim. The kernel checks those premises. It does not call the real instance of `cSup_upper`, and it does not run the Archimedean bisection.

An up-ray and the set of every real are not bounded above. `less_add_one` exhibits a strictly greater member, and `no_top` says a greater real exists. `complete_real` assumes a set that is bounded above. A two-sided interval stays outside this rule. `primitive.arbitrary_set` still blocks `law(an_order_ray_is_a_finite_enumeration)`.

Core Lean 4.36.0, with no imports, does not resolve `Set.Iic`, `Set.Ici`, or `Set.univ`. Octave is not used for this supremum.

The next gap is the Archimedean bisection in the proof of `complete_real`, for a nonempty set that is bounded above and does not contain its bound. A two-sided interval stays outside. Boolean connectives inside a predicate stay outside. Nested radicals and division by a different irrational stay open. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested. The Theory of Everything criteria in GOAL.md remain unmet.

`python -m unittest discover -s tests -v` finished 95 tests, 0 failures, about 0.40 seconds, on Python 3.14. One test still calls GNU Octave 11.3.0.

## 2026-11-25 — Archimedean bisection pgi-0.12.0

`{x. x < a}` is a lessThan ray. The bound is not a member, by `less_irrefl`. `less_add_one` exhibits a member one below the bound, and `bdd_above_Iio` says the bound is an upper bound. The kernel then runs the construction in the proof of `complete_real`. `of_int_floor_le` gives a rational where the upper-bound predicate fails. `le_of_int_ceiling` gives a rational where it holds. Each midpoint keeps the half on which that predicate changes. The width is the initial gap divided by a power of two, and `reals_Archimedean2` puts that gap below 1. The two endpoint sequences are Cauchy, `eq_Real` identifies them, and `le_RealI` with `Real_leI` identifies that real with the bound. `cSup_lessThan` is the name of the result. `sup {x. x < 5}` is 5. `sup {x. x < sqrt(2)}` is the class `sqrt(2)`. `prove complete {x. x < 5}` states that claim.

`{x. a < x}` is a greaterThan ray and is not bounded above. `less_add_one` exhibits a strictly greater member, and `no_top` says a greater real exists. A down-ray that already contains its bound stays on `cSup_atMost`. A predicate that is not a lessThan ray stays outside this bisection, because the kernel has to decide whether each midpoint is an upper bound. A two-sided interval stays outside. `primitive.arbitrary_set` still blocks `law(an_order_ray_is_a_finite_enumeration)`.

Core Lean 4.36.0, with no imports, does not resolve `Set.Iio`. Octave is not used for this supremum.

The next gap is a two-sided interval. Its predicate is a conjunction, and boolean connectives inside a predicate stay outside. Nested radicals and division by a different irrational stay open. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 96 tests, 0 failures, about 0.44 seconds, on Python 3.14. One test still calls GNU Octave 11.3.0.

## 2026-11-25 — Two-sided interval pgi-0.13.0

A proper overlap of one lower ray and one upper ray is the two-sided interval. Isabelle defines `{l..u}` as `{l..} ∩ {..u}`, and the three mixed ends the same way: `{l<..u}`, `{l..<u}`, and `{l<..<u}`. The same closed bound stays the singleton, by `atMost_Int_atLeast`. The meet is empty when the lower bound is above the upper bound, and when an open end makes the two bounds equal.

The supremum is the upper bound. A closed upper end is a member, so `cSup_eq_maximum` applies. `cSup_atLeastAtMost` needs the lower bound at or below the upper bound. `cSup_greaterThanAtMost` needs it strictly below. The bisection stays outside those two rules. An open upper end is not a member, by `less_irrefl`. `cSup_atLeastLessThan` and `cSup_greaterThanLessThan` name that supremum. The kernel builds it by the same Archimedean bisection, and each failing rational is checked against a member of the interval. `{x. 1 <= x}` intersect `{x. x <= 3}` is `atLeastAtMost(1, 3)`, and its supremum is 3. `{x. 1 <= x}` intersect `{x. x < 3}` has the same supremum, and 3 is not a member. `primitive.arbitrary_set` still blocks `law(an_order_ray_is_a_finite_enumeration)`.

Core Lean 4.36.0, with no imports, does not resolve an interval name. Octave is not used for this supremum.

The next gap is boolean connectives inside a predicate. Nested radicals and division by a different irrational stay open. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 97 tests, 0 failures, about 0.45 seconds, on Python 3.14. One test still calls GNU Octave 11.3.0.

## 2026-11-25 — boolean connectives pgi-0.14.0

A boolean connective inside one predicate reduces by the Collect lemmas in `Set.thy`. `Collect_conj_eq` says `{x. P x and Q x}` is the intersection of the two comprehensions. `{x. 1 <= x and x <= 3}` is `atLeastAtMost(1, 3)`, and its supremum is 3 by `cSup_atLeastAtMost`. `{x. 1 <= x and x < 3}` has the same supremum by `cSup_atLeastLessThan`, and the kernel runs the Archimedean bisection. `Collect_conj_eq2` meets the two separations of one finite enumeration. `{x in {1, 2, 3, 4}. 1 <= x and x <= 3}` is `{1, 2, 3}`.

`Collect_neg_eq` says `{x. not P x}` is the complement of `{x. P x}`. `Compl_atMost`, `Compl_greaterThan`, `Compl_atLeast`, and `Compl_lessThan` name the opposite ray. `{x. not x <= 5}` is `greaterThan(5)`. `Compl_UNIV_eq` says the complement of the set of every real is empty. `{x. not x = x}` is `{}`.

`Collect_disj_eq` says `{x. P x or Q x}` is the union of the two comprehensions. The kernel builds that union when both sides are finite enumerations. `{x. x = 1 or x = 2}` is `{1, 2}`, and its supremum is 2. A disjunction of two rays stays outside this rule. Implication, the complement of a singleton, and a nested connective stay outside this rule. `primitive.arbitrary_set` still blocks `law(an_order_ray_is_a_finite_enumeration)`.

Core Lean 4.36.0, with no imports, does not resolve `Collect`. Octave is not used for this supremum.

The next gap is nested radicals and division by a different irrational. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 98 tests, 0 failures, about 0.45 seconds, on Python 3.14. One test still calls GNU Octave 11.3.0.

## 2026-11-25 — nested radicals pgi-0.15.0

A nested radical of one square-free integer is a tower `base^(odd/2^k)`. The exponent is a positive odd numerator over a power of two, and a denominator of 2 stays an ordinary square root. `sqrt(sqrt(2))` is `cauchy(sqrt(sqrt(2)))`. Its square is `sqrt(2)`. `sqrt(sqrt(sqrt(2)))` is `cauchy(sqrt(sqrt(sqrt(2))))`. `sqrt(4*sqrt(2))` is `cauchy(2 * sqrt(sqrt(2)))`. `sqrt(2)*sqrt(sqrt(2))` is `cauchy(sqrt(sqrt(8)))`. `sqrt(sqrt(2))*sqrt(sqrt(3))` is `cauchy(sqrt(sqrt(6)))`.

The positive root is the bisection of a rational interval that starts at `[1, base]`. The comparison of a rational endpoint with that root is an integer comparison of powers. At depth 4 the width is the initial width divided by 16. The certificate cites `cauchy`, `eq_Real`, `real_sqrt_pow2`, `real_sqrt_ge_zero`, `real_sqrt_unique`, and `real_le_lsqrt`. `real_sqrt_mult` multiplies nonnegative factors.

`real_sqrt_unique` denests `a + b*sqrt(n)` when `a^2 - n*b^2` is a rational square and the square of the candidate is the radicand. `sqrt(3 + 2*sqrt(2))` is `cauchy(1 + sqrt(2))`. `sqrt(4 + 2*sqrt(3))` is `cauchy(1 + sqrt(3))`.

`sqrt(2 + sqrt(2))` stays outside. A product of radicals of different bases at different levels stays outside. A negative radicand stays open. Isabelle `real_sqrt_minus` stays refused. Division by a different irrational stays open. The same nonzero class divided by itself is 1.

`{x. x <= sqrt(sqrt(2))}` is `atMost(sqrt(sqrt(2)))`, and its supremum is that tower by `cSup_atMost`. `{sqrt(sqrt(2))}` is the singleton of that class. `prove all x in {1}. sqrt(sqrt(2)) <= x` fails at 1. `primitive.continuum` still blocks `law(sqrt_two_is_rational)`.

Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is division by a different irrational. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 99 tests, 0 failures, about 0.49 seconds, on Python 3.14. One test still calls GNU Octave 11.3.0.

## 2026-11-25 — division by a different irrational pgi-0.16.0

Division is multiplication by the inverse. Isabelle `divide_real_def` defines `x div y = x * inverse y`, and `divide_inverse` is that field law. The kernel builds a multiplier in the span it already admits. It keeps the multiplier when the product with the divisor is the constant sequence 1. `inverse_unique` names that multiplier the inverse. The divisor is bounded away from zero. Isabelle's `inverse (0::real) = 0` stays refused.

`sqrt(2)/sqrt(3)` is `cauchy(1/3 * sqrt(6))`. `real_div_sqrt` says `0 <= x` implies `x / sqrt x = sqrt x`, so the inverse of a positive square root is that root over the radicand. `sqrt(8)/sqrt(2)` is 2. `sqrt(2)/sqrt(sqrt(2))` is `sqrt(sqrt(2))`. `sqrt(sqrt(8))/sqrt(sqrt(2))` is `sqrt(2)`. `2/sqrt(2)` is `sqrt(2)`. `1/(1+sqrt(2))` is `cauchy(-1 + sqrt(2))`. `1/(sqrt(2)+sqrt(3))` is `cauchy(-sqrt(2) + sqrt(3))`. `1/(1+sqrt(2)+sqrt(3))` is `cauchy(1/2 + 1/4 * sqrt(2) - 1/4 * sqrt(6))`. `1/(1+sqrt(sqrt(2)))` is `cauchy(-1 - sqrt(2) + sqrt(sqrt(2)) + sqrt(sqrt(8)))`. `{sqrt(2)/sqrt(3)}` is that class. `sup {x. x <= sqrt(2)/sqrt(3)}` is the same class by `cSup_atMost`.

`sqrt(sqrt(2))/sqrt(sqrt(3))` stays outside. The quotient asks for a product of radicals of different bases at different levels, and that product stays outside. A divisor the kernel cannot see as nonzero stays open. Division by zero stays open. `sqrt(2 + sqrt(2))` stays outside. A boolean connective the kernel cannot settle stays outside.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this quotient.

The next gap is a product of radicals of different bases at different levels. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 100 tests, 0 failures, about 0.56 seconds, on Python 3.14. One test still calls GNU Octave 11.3.0.

## 2026-11-25 — products of radicals at different levels pgi-0.17.0

A product of radicals at different levels is one integer raised to `1/2^k`. Isabelle `real_root_mult` gives `root n (x * y) = root n x * root n y`. `real_root_power` gives, for `0 < n`, `root n (x ^ k) = root n x ^ k`. `real_root_mult_exp` gives `root (m * n) x = root m (root n x)`, so nested square roots are one `2^k`-th root. A full power of that root moves into the rational coefficient. Equal prime exponents stay the square-free tower `base^(odd/2^k)`. Unequal prime exponents stay one packed radical, `N^(1/2^k)`.

`sqrt(2)*sqrt(sqrt(3))` is `cauchy(sqrt(sqrt(12)))`. `sqrt(sqrt(12))*sqrt(sqrt(12))` is `2 * sqrt(3)`. `sqrt(sqrt(12))*sqrt(sqrt(108))` is 6. `sqrt(3*sqrt(2))` is `cauchy(sqrt(sqrt(18)))`, and `sqrt(sqrt(18))` is that same class. `sqrt(sqrt(2))*sqrt(sqrt(3))` is `cauchy(sqrt(sqrt(6)))`. `sqrt(2)*sqrt(sqrt(2))` is `cauchy(sqrt(sqrt(8)))`. `sqrt(4*sqrt(2))` is `cauchy(2 * sqrt(sqrt(2)))`. `sqrt(8)` is `2 * sqrt(2)`.

`sqrt(sqrt(2))/sqrt(sqrt(3))` is `cauchy(1/3 * sqrt(sqrt(54)))`. Division multiplies by the inverse. The complement power over the integer multiplies back to the constant sequence 1, and `inverse_unique` names it. `1/(sqrt(sqrt(2))+sqrt(sqrt(3)))` is `cauchy(-sqrt(sqrt(8)) + sqrt(sqrt(27)) + sqrt(sqrt(12)) - sqrt(sqrt(18)))`. `1/(1+sqrt(sqrt(12)))` is `cauchy(-1/11 - 2/11 * sqrt(3) + 1/11 * sqrt(sqrt(12)) + 2/11 * sqrt(sqrt(108)))`. Each of those multipliers times its divisor is 1. `{sqrt(2)*sqrt(sqrt(3))}` is `set({sqrt(sqrt(12))})`. `sup {x. x <= sqrt(2)*sqrt(sqrt(3))}` is that class by `cSup_atMost`.

`sqrt(2+sqrt(2))` stays outside. A negative radicand stays open. Division by zero stays open. A divisor the kernel cannot see as nonzero stays open. A boolean connective the kernel cannot settle stays outside. Isabelle `inverse (0::real) = 0` stays refused. Isabelle `real_sqrt_minus` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this product.

The next gap is a radicand the kernel cannot denest, `sqrt(2+sqrt(2))`. A boolean connective the kernel cannot settle, a set whose upper-bound predicate the kernel cannot decide, a nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero stay outside. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 101 tests, 0 failures, about 0.65 seconds, on Python 3.14. One test still calls GNU Octave 11.3.0.

## 2026-11-25 — denesting sqrt(2 + sqrt(2)) pgi-0.18.0

`sqrt(2 + sqrt(2))` is a positive binomial whose discriminant `a^2 - n*b^2` is 2, not a rational square. The older denest into a sum of rational square roots does not apply. The kernel admits the nonnegative root as the nested radical itself. Isabelle `real_sqrt_unique` says `y^2 = x` and `0 <= y` imply `sqrt x = y`. The certificate also cites `real_sqrt_pow2`, `real_sqrt_ge_zero`, `real_le_lsqrt`, `cauchy`, and `eq_Real`. The square of the stored root is the radicand, and a forged constant, a forged `1 + sqrt(2)`, a forged packed radical, or a nest the classical denest already reduces is rejected.

`sqrt(2 + sqrt(2))` is `cauchy(sqrt(2 + sqrt(2)))`, and its square is `2 + sqrt(2)`. `sqrt(2 - sqrt(2))` is `cauchy(sqrt(2 - sqrt(2)))`. Their product is `sqrt(2)`. `sqrt(3) * sqrt(2 + sqrt(2))` is `cauchy(sqrt(6 + 3 * sqrt(2)))`. `sqrt(2) * sqrt(2 + sqrt(2))` is `cauchy(sqrt(4 + 2 * sqrt(2)))`, the same class as `sqrt(4 + 2 * sqrt(2))`. Integer square content moves into the coefficient: `sqrt(8 + 8 * sqrt(2))` is `2 * sqrt(2 + 2 * sqrt(2))`. `sqrt(2 + sqrt(3))` still denests, to `1/2 * sqrt(2) + 1/2 * sqrt(6)`, because that discriminant is a rational square. `sqrt(3 + 2 * sqrt(2))` is still `1 + sqrt(2)`. `sqrt(3 + sqrt(2))` is `cauchy(sqrt(3 + sqrt(2)))`.

`1 / sqrt(2 + sqrt(2))` is `cauchy(sqrt(2 + sqrt(2)) - 1/2 * sqrt(4 + 2 * sqrt(2)))`. `1 / (1 + sqrt(2 + sqrt(2)))` is `cauchy(1 - sqrt(2) - sqrt(2 + sqrt(2)) + sqrt(4 + 2 * sqrt(2)))`. Each multiplier times its divisor is the constant sequence 1, by `inverse_unique`. `{sqrt(2 + sqrt(2))}` is `set({sqrt(2 + sqrt(2))})`. `sup {x. x <= sqrt(2 + sqrt(2))}` is that class by `cSup_atMost`.

`sqrt(sqrt(2) + sqrt(3))` stays outside. `sqrt(sqrt(2 + sqrt(2)))` stays outside. A sum of two nested binomials of the same square-free integer stays that sum: `sqrt(2 + sqrt(2)) + sqrt(2 - sqrt(2))` is not rewritten as `sqrt(4 + 2 * sqrt(2))`. A negative radicand stays open. Division by zero stays open. A divisor the kernel cannot see as nonzero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is a square root of a sum of two different square-free radicals, `sqrt(sqrt(2)+sqrt(3))`. `sqrt(sqrt(2+sqrt(2)))` stays outside. A boolean connective the kernel cannot settle, a set whose upper-bound predicate the kernel cannot decide, a nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero stay outside. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 102 tests, 0 failures, about 0.78 seconds, on Python 3.14. One test still calls GNU Octave 11.3.0.

## 2026-11-25 — denesting sqrt(sqrt(2) + sqrt(3)) pgi-0.19.0

`sqrt(sqrt(2) + sqrt(3))` is a square root of a sum of two different square-free radicals. The squares are 2 and 3, and their difference is 1, a rational square. Isabelle `real_sqrt_unique` says `y^2 = x` and `0 <= y` imply `sqrt x = y`. Each half is a binomial whose own discriminant is negative, so the half stays a nested radical. The certificate also cites `real_sqrt_pow2`, `real_sqrt_ge_zero`, `real_le_lsqrt`, `cauchy`, and `eq_Real`. A forged single nest, and the conjugate difference sealed as this square root, are rejected.

`sqrt(sqrt(2) + sqrt(3))` is `cauchy(1/2 * sqrt(-2 + 2 * sqrt(3)) + 1/2 * sqrt(2 + 2 * sqrt(3)))`, and its square is `sqrt(2) + sqrt(3)`. `sqrt(sqrt(3) - sqrt(2))` is `cauchy(-1/2 * sqrt(-2 + 2 * sqrt(3)) + 1/2 * sqrt(2 + 2 * sqrt(3)))`. Their product is 1. `sqrt(2 * sqrt(3) + 2 * sqrt(2))` is `cauchy(sqrt(-1 + sqrt(3)) + sqrt(1 + sqrt(3)))`. `sqrt(sqrt(6) + sqrt(2))` is `cauchy(1/2 * sqrt(-4 + 2 * sqrt(6)) + 1/2 * sqrt(4 + 2 * sqrt(6)))`. `{sqrt(sqrt(2) + sqrt(3))}` is that denested class. `sup {x. x <= sqrt(sqrt(2) + sqrt(3))}` is the same class by `cSup_atMost`.

`sqrt(sqrt(2) + sqrt(5))` stays outside, because 5 - 2 = 3 is not a rational square. `sqrt(1 + sqrt(2) + sqrt(3))` stays outside. `sqrt(sqrt(2 + sqrt(2)))` stays outside. `1 / sqrt(sqrt(2) + sqrt(3))` stays outside. A sum of two nested binomials of the same square-free integer stays that sum: `sqrt(2 + sqrt(2)) + sqrt(2 - sqrt(2))` is not rewritten as `sqrt(4 + 2 * sqrt(2))`. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is a square root of two square-free radicals whose squares differ by a non-square, `sqrt(sqrt(2)+sqrt(5))`. `sqrt(sqrt(2+sqrt(2)))` stays outside. The inverse of the denested sum stays outside. A boolean connective the kernel cannot settle, a set whose upper-bound predicate the kernel cannot decide, a nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero stay outside. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 103 tests, 0 failures, about 0.99 seconds, on Python 3.14. One test still calls GNU Octave 11.3.0.

## 2026-11-25 — denesting sqrt(sqrt(2) + sqrt(5)) pgi-0.20.0

`sqrt(sqrt(2) + sqrt(5))` is a square root of a sum of two different square-free radicals. The squares are 2 and 5. Their difference is 3, and 3 is not a square of a rational, so the rational-square denesting does not apply. Feeding that gap back into the same formula produces square roots of two-radical sums, and one more step returns a multiple of the original root. Isabelle `real_sqrt_unique` says `y^2 = x` and `0 <= y` imply `sqrt x = y`, so the nonnegative root is the nested radical itself. The certificate also cites `real_sqrt_pow2`, `real_sqrt_ge_zero`, `real_le_lsqrt`, `cauchy`, and `eq_Real`. A forged denestable pair, an unreduced content pair, and the conjugate sealed as this square root are rejected.

`sqrt(sqrt(2) + sqrt(5))` is `cauchy(sqrt(sqrt(2) + sqrt(5)))`, and its square is `sqrt(2) + sqrt(5)`. `sqrt(sqrt(5) - sqrt(2))` is `cauchy(sqrt(-sqrt(2) + sqrt(5)))`. Their product is `sqrt(3)`. The inverse is `cauchy(1/3 * sqrt(-3 * sqrt(2) + 3 * sqrt(5)))`, and it multiplies back to 1 by `inverse_unique`. `sqrt(4 * sqrt(2) + 4 * sqrt(5))` is `cauchy(2 * sqrt(sqrt(2) + sqrt(5)))`. `sqrt(2) * sqrt(sqrt(2) + sqrt(5))` is `cauchy(sqrt(2 * sqrt(2) + 2 * sqrt(5)))`. `{sqrt(sqrt(2) + sqrt(5))}` is that class. `sup {x. x <= sqrt(sqrt(2) + sqrt(5))}` is the same class by `cSup_atMost`.

`sqrt(sqrt(2 + sqrt(2)))` stays outside. `sqrt(sqrt(sqrt(2) + sqrt(5)))` stays outside. `sqrt(1 + sqrt(2) + sqrt(5))` stays outside. `1 / sqrt(sqrt(2) + sqrt(3))` stays outside. A nest times this pair stays outside. A sum of two nested binomials of the same square-free integer stays that sum: `sqrt(2 + sqrt(2)) + sqrt(2 - sqrt(2))` is not rewritten as `sqrt(4 + 2 * sqrt(2))`. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is a square root of a nested binomial, `sqrt(sqrt(2+sqrt(2)))`. A square root of `sqrt(sqrt(2)+sqrt(5))` stays outside. The inverse of `sqrt(sqrt(2)+sqrt(3))` stays outside. A boolean connective the kernel cannot settle, a set whose upper-bound predicate the kernel cannot decide, a nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero stay outside. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 104 tests, 0 failures, about 1.23 seconds, on Python 3.14. One test still calls GNU Octave 11.3.0.

## 2026-11-25 — denesting sqrt(sqrt(2 + sqrt(2))) pgi-0.21.0

`sqrt(sqrt(2 + sqrt(2)))` is a square root of one positive binomial nest. The nest `sqrt(2 + sqrt(2))` has discriminant 2, which is not a rational square, so it stays a nest. The fourth root satisfies `x^8 - 4x^4 + 2 = 0`. That polynomial is irreducible, so the root is not a term, a tower, one binomial nest, or a pair. Isabelle `real_sqrt_unique` says `y^2 = x` and `0 <= y` imply `sqrt x = y`, so the nonnegative root is the nested radical itself. The certificate also cites `real_sqrt_pow2`, `real_sqrt_ge_zero`, `real_le_lsqrt`, `cauchy`, and `eq_Real`. The comparison isolates one radical and squares twice. A forged denestable binomial, an unreduced multiplier, and a different nest sealed as this square root are rejected.

`sqrt(sqrt(2 + sqrt(2)))` is `cauchy(sqrt(sqrt(2 + sqrt(2))))`, and its square is `sqrt(2 + sqrt(2))`. `sqrt(sqrt(2 - sqrt(2)))` is `cauchy(sqrt(sqrt(2 - sqrt(2))))`. Their product is `sqrt(sqrt(2))`. The inverse is `cauchy(sqrt(sqrt(20 + 14 * sqrt(2))) - 1/2 * sqrt(2 * sqrt(20 + 14 * sqrt(2))))`, and it multiplies back to 1 by `inverse_unique`. `sqrt(4 * sqrt(2 + sqrt(2)))` is `cauchy(2 * sqrt(sqrt(2 + sqrt(2))))`. `sqrt(2) * sqrt(sqrt(2 + sqrt(2)))` is `cauchy(sqrt(2 * sqrt(2 + sqrt(2))))`. `{sqrt(sqrt(2 + sqrt(2)))}` is that class. `sup {x. x <= sqrt(sqrt(2 + sqrt(2)))}` is the same class by `cSup_atMost`.

`sqrt(sqrt(sqrt(2 + sqrt(2))))` stays outside. `sqrt(sqrt(sqrt(2) + sqrt(5)))` stays outside. `sqrt(1 + sqrt(2) + sqrt(5))` stays outside. `1 / sqrt(sqrt(2) + sqrt(3))` stays outside. `1 / (1 + sqrt(sqrt(2 + sqrt(2))))` stays outside. A nest times the pair stays outside. A sum of two nested binomials of the same square-free integer stays that sum: `sqrt(2 + sqrt(2)) + sqrt(2 - sqrt(2))` is not rewritten as `sqrt(4 + 2 * sqrt(2))`. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is a square root of the pair radical, `sqrt(sqrt(sqrt(2)+sqrt(5)))`. A further square root of `sqrt(sqrt(2+sqrt(2)))` stays outside. The inverse of `sqrt(sqrt(2)+sqrt(3))` stays outside. A boolean connective the kernel cannot settle, a set whose upper-bound predicate the kernel cannot decide, a nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero stay outside. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 105 tests, 0 failures, about 1.35 seconds, on Python 3.14. One test still calls GNU Octave 11.3.0.

## 2026-11-25 — denesting sqrt(sqrt(sqrt(2) + sqrt(5))) pgi-0.22.0

`sqrt(sqrt(sqrt(2) + sqrt(5)))` is a square root of one positive pair radical. The pair `sqrt(sqrt(2) + sqrt(5))` does not denest, because 5 - 2 = 3 is not a rational square. This root squares to that pair. The pair has degree 8 over the rationals, so the root is not a term, a tower, one binomial nest, a pair, or a square root of a nested binomial. Isabelle `real_sqrt_unique` says `y^2 = x` and `0 <= y` imply `sqrt x = y`, so the nonnegative root is the nested radical itself. The certificate also cites `real_sqrt_pow2`, `real_sqrt_ge_zero`, `real_le_lsqrt`, `cauchy`, and `eq_Real`. The comparison isolates the two radicals and squares twice. A forged denestable pair, an unreduced multiplier, and a different pair sealed as this square root are rejected.

`sqrt(sqrt(sqrt(2) + sqrt(5)))` is `cauchy(sqrt(sqrt(sqrt(2) + sqrt(5))))`, and its square is `sqrt(sqrt(2) + sqrt(5))`. `sqrt(sqrt(sqrt(5) - sqrt(2)))` is `cauchy(sqrt(sqrt(-sqrt(2) + sqrt(5))))`. Their product is `sqrt(sqrt(3))`. The inverse is `cauchy(1/3 * sqrt(3 * sqrt(-3 * sqrt(2) + 3 * sqrt(5))))`, and it multiplies back to 1 by `inverse_unique`. `sqrt(4 * sqrt(sqrt(2) + sqrt(5)))` is `cauchy(2 * sqrt(sqrt(sqrt(2) + sqrt(5))))`. `sqrt(2) * sqrt(sqrt(sqrt(2) + sqrt(5)))` is `cauchy(sqrt(2 * sqrt(sqrt(2) + sqrt(5))))`. `{sqrt(sqrt(sqrt(2) + sqrt(5)))}` is that class. `sup {x. x <= sqrt(sqrt(sqrt(2) + sqrt(5)))}` is the same class by `cSup_atMost`.

`sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))` stays outside. `sqrt(sqrt(sqrt(2 + sqrt(2))))` stays outside. `sqrt(1 + sqrt(2) + sqrt(5))` stays outside. `1 / sqrt(sqrt(2) + sqrt(3))` stays outside. `1 / (1 + sqrt(sqrt(sqrt(2) + sqrt(5))))` stays outside. A nest times the pair stays outside. A sum of two nested binomials of the same square-free integer stays that sum: `sqrt(2 + sqrt(2)) + sqrt(2 - sqrt(2))` is not rewritten as `sqrt(4 + 2 * sqrt(2))`. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is a further square root of this radical, `sqrt(sqrt(sqrt(sqrt(2)+sqrt(5))))`. A further square root of `sqrt(sqrt(2+sqrt(2)))` stays outside. The inverse of `sqrt(sqrt(2)+sqrt(3))` stays outside. A boolean connective the kernel cannot settle, a set whose upper-bound predicate the kernel cannot decide, a nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero stay outside. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 106 tests, 0 failures, about 1.59 seconds, on Python 3.14. One test still calls GNU Octave 11.3.0.

## 2026-11-25 — denesting sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))) pgi-0.23.0

`sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))` is a square root of one positive high. The high `sqrt(sqrt(sqrt(2) + sqrt(5)))` squares to the pair `sqrt(sqrt(2) + sqrt(5))`. That pair does not denest, because 5 - 2 = 3 is not a rational square, and the pair has degree 8 over the rationals. This root squares to that high, its fourth power is the pair, and its eighth power is the two-radical sum. It is not a term, a tower, one binomial nest, a pair, a square root of a nested binomial, or a square root of a pair. Isabelle `real_sqrt_unique` says `y^2 = x` and `0 <= y` imply `sqrt x = y`, so the nonnegative root is the nested radical itself. The certificate also cites `real_sqrt_pow2`, `real_sqrt_ge_zero`, `real_le_lsqrt`, `cauchy`, and `eq_Real`. The comparison isolates the two radicals and squares enough times that the eighth power meets the two-radical sum. A forged denestable pair, an unreduced multiplier, and a different pair sealed as this square root are rejected.

`sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))` is `cauchy(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))`, and its square is `sqrt(sqrt(sqrt(2) + sqrt(5)))`. `sqrt(sqrt(sqrt(sqrt(5) - sqrt(2))))` is `cauchy(sqrt(sqrt(sqrt(-sqrt(2) + sqrt(5)))))`. Their product is `sqrt(sqrt(sqrt(3)))`. The inverse is `cauchy(1/3 * sqrt(3 * sqrt(3 * sqrt(-3 * sqrt(2) + 3 * sqrt(5)))))`, and it multiplies back to 1 by `inverse_unique`. `sqrt(4 * sqrt(sqrt(sqrt(2) + sqrt(5))))` is `cauchy(2 * sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))`. `sqrt(2) * sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))` is `cauchy(sqrt(2 * sqrt(sqrt(sqrt(2) + sqrt(5)))))`. `{sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))}` is that class. `sup {x. x <= sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))}` is the same class by `cSup_atMost`.

`sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))` stays outside. `sqrt(sqrt(sqrt(2 + sqrt(2))))` stays outside. `sqrt(1 + sqrt(2) + sqrt(5))` stays outside. `1 / sqrt(sqrt(2) + sqrt(3))` stays outside. `1 / (1 + sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))` stays outside. A nest times the pair stays outside. A sum of two nested binomials of the same square-free integer stays that sum: `sqrt(2 + sqrt(2)) + sqrt(2 - sqrt(2))` is not rewritten as `sqrt(4 + 2 * sqrt(2))`. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is a further square root of this radical, `sqrt(sqrt(sqrt(sqrt(sqrt(2)+sqrt(5)))))`. A further square root of `sqrt(sqrt(2+sqrt(2)))` stays outside. The inverse of `sqrt(sqrt(2)+sqrt(3))` stays outside. A boolean connective the kernel cannot settle, a set whose upper-bound predicate the kernel cannot decide, a nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero stay outside. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 107 tests, 0 failures, about 1.89 seconds, on Python 3.14. One test still calls GNU Octave 11.3.0.

## 2026-11-25 — denesting sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))) pgi-0.24.0

`sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))` is a square root of one positive peak. The peak `sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))` squares to the high `sqrt(sqrt(sqrt(2) + sqrt(5)))`. That high squares to the pair `sqrt(sqrt(2) + sqrt(5))`. That pair does not denest, because 5 - 2 = 3 is not a rational square, and the pair has degree 8 over the rationals. This root squares to that peak, its fourth power is the high, its eighth power is the pair, and its sixteenth power is the two-radical sum. It is not a term, a tower, one binomial nest, a pair, a square root of a nested binomial, a square root of a pair, or a square root of a high. Isabelle `real_sqrt_unique` says `y^2 = x` and `0 <= y` imply `sqrt x = y`, so the nonnegative root is the nested radical itself. The certificate also cites `real_sqrt_pow2`, `real_sqrt_ge_zero`, `real_le_lsqrt`, `cauchy`, and `eq_Real`. The comparison isolates the two radicals and squares enough times that the sixteenth power meets the two-radical sum. A forged denestable pair, an unreduced multiplier, and a different pair sealed as this square root are rejected.

`sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))` is `cauchy(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))`, and its square is `sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))`. `sqrt(sqrt(sqrt(sqrt(sqrt(5) - sqrt(2)))))` is `cauchy(sqrt(sqrt(sqrt(sqrt(-sqrt(2) + sqrt(5))))))`. Their product is `sqrt(sqrt(sqrt(sqrt(3))))`. The inverse is `cauchy(1/3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(-3 * sqrt(2) + 3 * sqrt(5))))))`, and it multiplies back to 1 by `inverse_unique`. `sqrt(4 * sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))` is `cauchy(2 * sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))`. `sqrt(2) * sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))` is `cauchy(sqrt(2 * sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))`. `{sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))}` is that class. `sup {x. x <= sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))}` is the same class by `cSup_atMost`.

`sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))` stays outside. `sqrt(sqrt(sqrt(2 + sqrt(2))))` stays outside. `sqrt(1 + sqrt(2) + sqrt(5))` stays outside. `1 / sqrt(sqrt(2) + sqrt(3))` stays outside. `1 / (1 + sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))` stays outside. A nest times the pair stays outside. A sum of two nested binomials of the same square-free integer stays that sum: `sqrt(2 + sqrt(2)) + sqrt(2 - sqrt(2))` is not rewritten as `sqrt(4 + 2 * sqrt(2))`. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is a further square root of this radical, `sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2)+sqrt(5))))))`. A further square root of `sqrt(sqrt(2+sqrt(2)))` stays outside. The inverse of `sqrt(sqrt(2)+sqrt(3))` stays outside. A boolean connective the kernel cannot settle, a set whose upper-bound predicate the kernel cannot decide, a nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero stay outside. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 108 tests, 0 failures, about 2.34 seconds, on Python 3.14. One test still calls GNU Octave 11.3.0.

## 2026-11-25 — denesting sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))) pgi-0.25.0

`sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))` is a square root of one positive crest. The crest `sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))` squares to the peak `sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))`. That peak squares to the high `sqrt(sqrt(sqrt(2) + sqrt(5)))`. That high squares to the pair `sqrt(sqrt(2) + sqrt(5))`. That pair does not denest, because 5 - 2 = 3 is not a rational square, and the pair has degree 8 over the rationals. This root squares to that crest, its fourth power is the peak, its eighth power is the high, its sixteenth power is the pair, and its thirty-second power is the two-radical sum. It is not a term, a tower, one binomial nest, a pair, a square root of a nested binomial, a square root of a pair, a square root of a high, or a square root of a peak. Isabelle `real_sqrt_unique` says `y^2 = x` and `0 <= y` imply `sqrt x = y`, so the nonnegative root is the nested radical itself. The certificate also cites `real_sqrt_pow2`, `real_sqrt_ge_zero`, `real_le_lsqrt`, `cauchy`, and `eq_Real`. The comparison isolates the two radicals and squares enough times that the thirty-second power meets the two-radical sum. A forged denestable pair, an unreduced smult, qmult, pmult, or hmult, and a different pair sealed as this square root are rejected.

`sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))` is `cauchy(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))`, and its square is `sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))`. `sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(5) - sqrt(2))))))` is `cauchy(sqrt(sqrt(sqrt(sqrt(sqrt(-sqrt(2) + sqrt(5)))))))`. Their product is `sqrt(sqrt(sqrt(sqrt(sqrt(3)))))`. The inverse is `cauchy(1/3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(-3 * sqrt(2) + 3 * sqrt(5)))))))`, and it multiplies back to 1 by `inverse_unique`. `sqrt(4 * sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))` is `cauchy(2 * sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))`. `sqrt(2) * sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))` is `cauchy(sqrt(2 * sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))`. `{sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))}` is that class. `sup {x. x <= sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))}` is the same class by `cSup_atMost`.

`sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))` stays outside. `sqrt(sqrt(sqrt(2 + sqrt(2))))` stays outside. `sqrt(1 + sqrt(2) + sqrt(5))` stays outside. `1 / sqrt(sqrt(2) + sqrt(3))` stays outside. `1 / (1 + sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))` stays outside. A nest times the pair stays outside. A sum of two nested binomials of the same square-free integer stays that sum: `sqrt(2 + sqrt(2)) + sqrt(2 - sqrt(2))` is not rewritten as `sqrt(4 + 2 * sqrt(2))`. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is a further square root of this radical, `sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2)+sqrt(5)))))))`. A further square root of `sqrt(sqrt(2+sqrt(2)))` stays outside. The inverse of `sqrt(sqrt(2)+sqrt(3))` stays outside. A boolean connective the kernel cannot settle, a set whose upper-bound predicate the kernel cannot decide, a nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero stay outside. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 109 tests, 0 failures, about 2.87 seconds, on Python 3.14. One test still calls GNU Octave 11.3.0.

## 2026-11-25 — denesting sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))) pgi-0.26.0

`sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))` is a square root of one positive summit. The summit `sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))` squares to the crest `sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))`. That crest squares to the peak `sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))`. That peak squares to the high `sqrt(sqrt(sqrt(2) + sqrt(5)))`. That high squares to the pair `sqrt(sqrt(2) + sqrt(5))`. That pair does not denest, because 5 - 2 = 3 is not a rational square, and the pair has degree 8 over the rationals. This root squares to that summit, its fourth power is the crest, its eighth power is the peak, its sixteenth power is the high, its thirty-second power is the pair, and its sixty-fourth power is the two-radical sum. It is not a term, a tower, one binomial nest, a pair, a square root of a nested binomial, a square root of a pair, a square root of a high, a square root of a peak, or a square root of a crest. Isabelle `real_sqrt_unique` says `y^2 = x` and `0 <= y` imply `sqrt x = y`, so the nonnegative root is the nested radical itself. The certificate also cites `real_sqrt_pow2`, `real_sqrt_ge_zero`, `real_le_lsqrt`, `cauchy`, and `eq_Real`. The comparison isolates the two radicals and squares enough times that the sixty-fourth power meets the two-radical sum. A forged denestable pair, an unreduced amult, smult, qmult, pmult, or hmult, and a different pair sealed as this square root are rejected.

`sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))` is `cauchy(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))))`, and its square is `sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))`. `sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(5) - sqrt(2)))))))` is `cauchy(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(-sqrt(2) + sqrt(5))))))))`. Their product is `sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(3))))))`. The inverse is `cauchy(1/3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(-3 * sqrt(2) + 3 * sqrt(5))))))))`, and it multiplies back to 1 by `inverse_unique`. `sqrt(4 * sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))` is `cauchy(2 * sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))))`. `sqrt(2) * sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))` is `cauchy(sqrt(2 * sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))))`. `{sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))}` is that class. `sup {x. x <= sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))}` is the same class by `cSup_atMost`.

`sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))))` stays outside. `sqrt(sqrt(sqrt(2 + sqrt(2))))` stays outside. `sqrt(1 + sqrt(2) + sqrt(5))` stays outside. `1 / sqrt(sqrt(2) + sqrt(3))` stays outside. `1 / (1 + sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))))` stays outside. A nest times the pair stays outside. A sum of two nested binomials of the same square-free integer stays that sum: `sqrt(2 + sqrt(2)) + sqrt(2 - sqrt(2))` is not rewritten as `sqrt(4 + 2 * sqrt(2))`. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is a further square root of this radical, `sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2)+sqrt(5))))))))`. A further square root of `sqrt(sqrt(2+sqrt(2)))` stays outside. The inverse of `sqrt(sqrt(2)+sqrt(3))` stays outside. A boolean connective the kernel cannot settle, a set whose upper-bound predicate the kernel cannot decide, a nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero stay outside. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 110 tests, 0 failures, about 3.60 seconds, on Python 3.14. One test still calls GNU Octave 11.3.0.

## 2026-11-25 — every further square root of sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))) pgi-0.27.0

The outer depth of this radical continues through every finite step. The pair `sqrt(sqrt(2) + sqrt(5))` does not denest, because 5 - 2 = 3 is not a rational square, and the pair has degree 8 over the rationals. Each added outer square root doubles that degree, and the doubling continues. The six named layers cover outer depths 1 through 6: the pair, the high, the peak, the crest, the summit, and the apex `sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))`. Every further finite depth is that nested radical, one square root deeper, by `real_sqrt_unique`. The extra depth is multiplier data on the same rule. The new certificate takes one outer square and then uses the apex comparison. The sixty-fourth-power comparison stays on the apex certificate. The certificate cites `real_sqrt_unique`, `real_sqrt_pow2`, `real_sqrt_ge_zero`, `real_le_lsqrt`, `cauchy`, and `eq_Real`. A further square root of an apex is not attained at a rational endpoint, so the value stays strictly inside the interval.

`sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))))` is `cauchy(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))))`, and its square is `sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))`. `sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))))` is the same rule, and its square is `sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))))`. `sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))))))` is the same rule again. `sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(5) - sqrt(2))))))))` is `cauchy(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(-sqrt(2) + sqrt(5)))))))))`. Their product is `sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(3)))))))`. The inverse is `cauchy(1/3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(-3 * sqrt(2) + 3 * sqrt(5)))))))))`, and it multiplies back to 1 by `inverse_unique`. `sqrt(4 * sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))))` is `cauchy(2 * sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))))`. `sqrt(2) * sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))))` is `cauchy(sqrt(2 * sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))))`. `{sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))))}` is that class. `sup {x. x <= sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))))}` is the same class by `cSup_atMost`.

`sqrt(sqrt(sqrt(2 + sqrt(2))))` stays outside. `sqrt(1 + sqrt(2) + sqrt(5))` stays outside. `1 / sqrt(sqrt(2) + sqrt(3))` stays outside. `1 / (1 + sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))))` stays outside. A nest times the pair stays outside. A sum of two nested binomials of the same square-free integer stays that sum: `sqrt(2 + sqrt(2)) + sqrt(2 - sqrt(2))` is not rewritten as `sqrt(4 + 2 * sqrt(2))`. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is a further square root of the nested binomial, `sqrt(sqrt(sqrt(2+sqrt(2))))`. The inverse of `sqrt(sqrt(2)+sqrt(3))` stays outside. A boolean connective the kernel cannot settle, a set whose upper-bound predicate the kernel cannot decide, a nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero stay outside. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 111 tests, 0 failures, about 5.22 seconds, on Python 3.14. One test still calls GNU Octave 11.3.0.





## 2026-11-25 — square roots of the nested binomial, and the inverse of sqrt(sqrt(2) + sqrt(3)) pgi-0.28.0

The nested binomial `sqrt(2 + sqrt(2))` already had one outer square root, the deep `sqrt(sqrt(2 + sqrt(2)))`. There is no finite last outer square root of that positive nest. Every further finite depth is the same nested radical, one square root deeper, by `real_sqrt_unique`. The extra depth is multiplier data on the same rule. The new certificate takes one outer square and then uses the deep comparison. The deep comparison stays on the deep. The certificate cites `real_sqrt_unique`, `real_sqrt_pow2`, `real_sqrt_ge_zero`, `real_le_lsqrt`, `cauchy`, and `eq_Real`. A further square root of a nested binomial is not attained at a rational endpoint, so the value stays strictly inside the interval.

`sqrt(sqrt(sqrt(2 + sqrt(2))))` is `cauchy(sqrt(sqrt(sqrt(2 + sqrt(2)))))`, and its square is `sqrt(sqrt(2 + sqrt(2)))`. One more square root is the same rule: `sqrt(sqrt(sqrt(sqrt(2 + sqrt(2)))))` squares to that radical. `sqrt(sqrt(sqrt(2 - sqrt(2))))` is the conjugate nest at the same depth. Their product is `sqrt(sqrt(sqrt(2)))`.

`sqrt(sqrt(2) + sqrt(3))` denests to `1/2 * sqrt(-2 + 2 * sqrt(3)) + 1/2 * sqrt(2 + 2 * sqrt(3))`. The squares of those two nests differ by the rational 1, so the inverse is the conjugate difference `-1/2 * sqrt(-2 + 2 * sqrt(3)) + 1/2 * sqrt(2 + 2 * sqrt(3))`. It multiplies back to 1 by `inverse_unique`. The same difference-of-squares rule gives the inverse of `sqrt(sqrt(6) + sqrt(2))` as `-1/4 * sqrt(-4 + 2 * sqrt(6)) + 1/4 * sqrt(4 + 2 * sqrt(6))`.

The inverse of `sqrt(sqrt(sqrt(2 + sqrt(2))))` stays outside. `sqrt(1 + sqrt(2) + sqrt(5))` stays outside. A nest times the pair stays outside. `1 / (1 + sqrt(sqrt(sqrt(2 + sqrt(2)))))` stays outside. A sum of two nested binomials of the same square-free integer stays that sum: `sqrt(2 + sqrt(2)) + sqrt(2 - sqrt(2))` is not rewritten as `sqrt(4 + 2 * sqrt(2))`. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is the inverse of `sqrt(sqrt(sqrt(2+sqrt(2))))`. `sqrt(1+sqrt(2)+sqrt(5))` stays outside. A nest times the pair stays outside. `1 / (1 + sqrt(sqrt(sqrt(2 + sqrt(2)))))` stays outside. A boolean connective the kernel cannot settle, a set whose upper-bound predicate the kernel cannot decide, a nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero stay outside. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 112 tests, 0 failures, about 5.30 seconds, on Python 3.14. One test still calls GNU Octave 11.3.0.


## 2026-11-25 — inverse of a further square root of the nested binomial pgi-0.29.0

The inverse of a fold is the fold times the inverse of its square, the same field law the inverse of a deep already uses. The square of `sqrt(sqrt(sqrt(2 + sqrt(2))))` is the deep `sqrt(sqrt(2 + sqrt(2)))`. The inverse of that deep is the difference of two deeps already admitted. A fold times a deep on the same square-free integer is the square root of the core times the square of that deep, by `real_sqrt_unique`. The product is a difference of two folds, and it multiplies back to 1 by `inverse_unique`.

`1 / sqrt(sqrt(sqrt(2 + sqrt(2))))` is `cauchy(sqrt(sqrt(2 * sqrt(676 + 478 * sqrt(2)))) - 1/2 * sqrt(2 * sqrt(2 * sqrt(676 + 478 * sqrt(2)))))`. One more square root has the same rule: `1 / sqrt(sqrt(sqrt(sqrt(2 + sqrt(2)))))` is `cauchy(sqrt(sqrt(2 * sqrt(2 * sqrt(780100 + 551614 * sqrt(2))))) - 1/2 * sqrt(2 * sqrt(2 * sqrt(2 * sqrt(780100 + 551614 * sqrt(2))))))`. Each multiplies back to 1.

`sqrt(1 + sqrt(2) + sqrt(5))` stays outside. A nest times the pair stays outside. `1 / (1 + sqrt(sqrt(sqrt(2 + sqrt(2)))))` stays outside. A sum of two nested binomials of the same square-free integer stays that sum: `sqrt(2 + sqrt(2)) + sqrt(2 - sqrt(2))` is not rewritten as `sqrt(4 + 2 * sqrt(2))`. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is `sqrt(1+sqrt(2)+sqrt(5))`. A nest times the pair stays outside. `1 / (1 + sqrt(sqrt(sqrt(2 + sqrt(2)))))` stays outside. A boolean connective the kernel cannot settle, a set whose upper-bound predicate the kernel cannot decide, a nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero stay outside. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

The Octave cross-check finds `octave-cli` from `PGI_OCTAVE`, then PATH, then the Windows 11.3.0 install path, and the test skips when none is found. The folder carries the Apache License, Version 2.0.

`python -m unittest discover -s tests -v` finished 113 tests, 0 failures, about 5.60 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.


## 2026-11-25 — sqrt(1 + sqrt(2) + sqrt(5)) as itself pgi-0.30.0

A two-prime biquadratic `a + b*sqrt(p) + c*sqrt(q) + d*sqrt(p*q)` is a square in `Q(sqrt(p), sqrt(q))` only when its field norm is a rational square and the relative denesting succeeds. The field norm of `1 + sqrt(2) + sqrt(5)` is -4, which is not a rational square, so the number is not a square in that field. The nonnegative root is the nested radical itself, by `real_sqrt_unique`. The certificate is the positive bisection sequence whose squares bracket the biquadratic. The comparison is exact: a rational square sits below the biquadratic when their difference has an order decided by enclosure. The certificate cites `real_sqrt_unique`, `real_sqrt_pow2`, `real_sqrt_ge_zero`, `real_le_lsqrt`, `cauchy`, and `eq_Real`. A square root of a two-prime biquadratic is not attained at a rational endpoint, so the value stays strictly inside the interval.

`sqrt(1 + sqrt(2) + sqrt(5))` is `cauchy(sqrt(1 + sqrt(2) + sqrt(5)))`, and its square is `1 + sqrt(2) + sqrt(5)`. A rational square factor moves into the coefficient: `sqrt(4 + 4 * sqrt(2) + 4 * sqrt(5))` is `2 * sqrt(1 + sqrt(2) + sqrt(5))`. `sqrt(2) * sqrt(1 + sqrt(2) + sqrt(5))` is `sqrt(2 + 2 * sqrt(2) + 2 * sqrt(5))`. When the field norm is a rational square and the relative denesting succeeds, the root is written in the field: `sqrt(8 + 2 * sqrt(2) + 2 * sqrt(5) + 2 * sqrt(10))` is `1 + sqrt(2) + sqrt(5)`. The same family closes `sqrt(1 + sqrt(2) + sqrt(3))`.

The inverse is the root times the inverse of its square, which already lies in `Q(sqrt(2), sqrt(5))`. `1 / sqrt(1 + sqrt(2) + sqrt(5))` is `cauchy(3/2 * sqrt(1 + sqrt(2) + sqrt(5)) + sqrt(2 + 2 * sqrt(2) + 2 * sqrt(5)) - 1/2 * sqrt(5 + 5 * sqrt(2) + 5 * sqrt(5)) - 1/2 * sqrt(10 + 10 * sqrt(2) + 10 * sqrt(5)))`. It multiplies back to 1 by `inverse_unique`.

A nest times the pair stays outside. `1 / (1 + sqrt(sqrt(sqrt(2 + sqrt(2)))))` stays outside. A sum of two nested binomials of the same square-free integer stays that sum: `sqrt(2 + sqrt(2)) + sqrt(2 - sqrt(2))` is not rewritten as `sqrt(4 + 2 * sqrt(2))`. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is a nest times the pair, `sqrt(2 + sqrt(2)) * sqrt(sqrt(2) + sqrt(5))`. `1 / (1 + sqrt(sqrt(sqrt(2 + sqrt(2)))))` stays outside. A boolean connective the kernel cannot settle, a set whose upper-bound predicate the kernel cannot decide, a nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero stay outside. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 114 tests, 0 failures, about 6.97 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.
