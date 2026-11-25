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


## 2026-11-25 — a nest times the pair pgi-0.31.0

For nonnegative insides, a binomial nest times a two-radical pair is the square root of the product of those insides, by `real_sqrt_mult`. `(2 + sqrt(2)) * (sqrt(2) + sqrt(5))` is the two-prime biquadratic `2 + 2 * sqrt(2) + 2 * sqrt(5) + sqrt(10)`. The field norm of that radicand is 36, a rational square, but both relative norms fail to be squares in the intermediate fields, so the number is not a square in `Q(sqrt(2), sqrt(5))`. The nonnegative root is the nested radical itself, by `real_sqrt_unique`. A field norm that is a rational square is therefore not enough, by itself, to stay outside or to denest: when both relative norms are decided and are not squares, the root is stored as a quad.

`sqrt(2 + sqrt(2)) * sqrt(sqrt(2) + sqrt(5))` is `cauchy(sqrt(2 + 2 * sqrt(2) + 2 * sqrt(5) + sqrt(10)))`, and its square is `2 + 2 * sqrt(2) + 2 * sqrt(5) + sqrt(10)`. The product in the other order is the same class. The inverse is the root times the inverse of that square, which already lies in the field, and it multiplies back to 1 by `inverse_unique`.

`1 / (1 + sqrt(sqrt(sqrt(2 + sqrt(2)))))` stays outside. `1 / (1 + ...)` on the pair ladder stays outside. A sum of two nested binomials of the same square-free integer stays that sum: `sqrt(2 + sqrt(2)) + sqrt(2 - sqrt(2))` is not rewritten as `sqrt(4 + 2 * sqrt(2))`. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is `1 / (1 + sqrt(sqrt(sqrt(2 + sqrt(2)))))`, and `1 / (1 + ...)` on the pair ladder. A boolean connective the kernel cannot settle, a set whose upper-bound predicate the kernel cannot decide, a nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero stay outside. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 115 tests, 0 failures, about 7.89 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — inverse of one plus an admitted radical pgi-0.32.0

For a form `c + x` with `c` a nonzero rational and `x` exactly one admitted radical, the inverse is `(c - x)` times the inverse of `c^2 - x^2`, when that simpler inverse is already in the kernel and the constructed quotient multiplies back to 1 by `inverse_unique`. The same difference-of-squares step is repeated when the first denominator is itself a shifted radical.

`1 / (1 + sqrt(sqrt(2 + sqrt(2))))` is `cauchy(1 - sqrt(2) + sqrt(2 + sqrt(2)) - sqrt(4 + 2 * sqrt(2)) - sqrt(sqrt(2 + sqrt(2))) + sqrt(2 * sqrt(2 + sqrt(2))) - sqrt(sqrt(20 + 14 * sqrt(2))) + sqrt(2 * sqrt(20 + 14 * sqrt(2))))`. The same rule closes `1 / (1 + sqrt(sqrt(2) + sqrt(5)))`, `1 / (1 + sqrt(sqrt(sqrt(2) + sqrt(5))))`, `1 / (1 + sqrt(1 + sqrt(2) + sqrt(5)))`, and `1 / (1 + sqrt(2 + 2 * sqrt(2) + 2 * sqrt(5) + sqrt(10)))`. A fold times a nest on the same radicand is the square root of the already closed deep-times-nest product: `sqrt(sqrt(sqrt(2 + sqrt(2)))) * sqrt(2 + sqrt(2))` is `cauchy(sqrt(sqrt(2 * sqrt(58 + 41 * sqrt(2)))))`. The product in the other order is the same class.

`1 / (1 + sqrt(sqrt(sqrt(2 + sqrt(2)))))` stays outside, because the expanded product of the constructed inverse with `1` plus that fold does not yet reduce to 1 in the form language. `1 / (1 + ...)` from the peak downward on the pair ladder stays outside, because the products of a peak with a high or a pair are not yet in the kernel. A sum of two nested binomials of the same square-free integer stays that sum: `sqrt(2 + sqrt(2)) + sqrt(2 - sqrt(2))` is not rewritten as `sqrt(4 + 2 * sqrt(2))`. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is `1 / (1 + sqrt(sqrt(sqrt(2 + sqrt(2)))))`, and `1 / (1 + ...)` from the peak downward on the pair ladder. A boolean connective the kernel cannot settle, a set whose upper-bound predicate the kernel cannot decide, a nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero stay outside. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 116 tests, 0 failures, about 10.36 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — inverse of one plus a peak pgi-0.33.0

A peak times a pair on the same two radicands is the square root of the already closed high-times-pair product, associated through that product rather than through the field element that is the square of the pair. `sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))) * sqrt(sqrt(2) + sqrt(5))` is `cauchy(sqrt(sqrt(sqrt(229 * sqrt(2) + 145 * sqrt(5)))))`. A peak times a high is the square root of the high times the square of that high: `sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))) * sqrt(sqrt(sqrt(2) + sqrt(5)))` is `cauchy(sqrt(sqrt(sqrt(17 * sqrt(2) + 11 * sqrt(5)))))`. The product in the other order is the same class.

The shifted inverse of a rational plus one admitted radical then closes `1 / (1 + sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))`, and the quotient multiplies back to 1 by `inverse_unique`.

`1 / (1 + sqrt(sqrt(sqrt(2 + sqrt(2)))))` stays outside, because the expanded product of the constructed inverse with `1` plus that fold does not yet reduce to 1 in the form language. `1 / (1 + ...)` from the crest downward on the pair ladder stays outside, because the products of a crest with a peak, a high, or a pair are not yet in the kernel. A sum of two nested binomials of the same square-free integer stays that sum: `sqrt(2 + sqrt(2)) + sqrt(2 - sqrt(2))` is not rewritten as `sqrt(4 + 2 * sqrt(2))`. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is `1 / (1 + sqrt(sqrt(sqrt(2 + sqrt(2)))))`, and `1 / (1 + ...)` from the crest downward on the pair ladder. A boolean connective the kernel cannot settle, a set whose upper-bound predicate the kernel cannot decide, a nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero stay outside. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 116 tests, 0 failures, about 14.10 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — inverse of one plus a fold pgi-0.34.0

A deep times a fold is the same mixed product already used for a fold times a deep. With that product in both orders, the shifted inverse of a rational plus a fold multiplies back to 1 by `inverse_unique`.

`1 / (1 + sqrt(sqrt(sqrt(2 + sqrt(2)))))` is `cauchy(1 - sqrt(2) + sqrt(2 + sqrt(2)) - sqrt(4 + 2 * sqrt(2)) + sqrt(sqrt(2 + sqrt(2))) - sqrt(2 * sqrt(2 + sqrt(2))) + sqrt(sqrt(20 + 14 * sqrt(2))) - sqrt(2 * sqrt(20 + 14 * sqrt(2))) - sqrt(sqrt(sqrt(2 + sqrt(2)))) + sqrt(2 * sqrt(sqrt(2 + sqrt(2)))) - sqrt(sqrt(sqrt(20 + 14 * sqrt(2)))) + sqrt(2 * sqrt(sqrt(20 + 14 * sqrt(2)))) - sqrt(sqrt(2 * sqrt(58 + 41 * sqrt(2)))) + sqrt(2 * sqrt(2 * sqrt(58 + 41 * sqrt(2)))) - sqrt(sqrt(2 * sqrt(676 + 478 * sqrt(2)))) + sqrt(2 * sqrt(2 * sqrt(676 + 478 * sqrt(2))))`. Further finite depths of that fold close by the same rule.

`1 / (1 + ...)` from the crest downward on the pair ladder stays outside, because the products of a crest with a peak, a high, or a pair are not yet in the kernel. A sum of two nested binomials of the same square-free integer stays that sum: `sqrt(2 + sqrt(2)) + sqrt(2 - sqrt(2))` is not rewritten as `sqrt(4 + 2 * sqrt(2))`. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is `1 / (1 + ...)` from the crest downward on the pair ladder. A boolean connective the kernel cannot settle, a set whose upper-bound predicate the kernel cannot decide, a nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero stay outside. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 116 tests, 0 failures, about 20.86 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — inverse of one plus a crest pgi-0.35.0

A crest times a pair, a high, or a peak on the same two radicands is written through the already closed peak products. `sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))) * sqrt(sqrt(2) + sqrt(5))` is `cauchy(sqrt(sqrt(sqrt(sqrt(40681 * sqrt(2) + 25729 * sqrt(5))))))`. A crest times a high is `cauchy(sqrt(sqrt(sqrt(sqrt(229 * sqrt(2) + 145 * sqrt(5))))))`. A crest times a peak is `cauchy(sqrt(sqrt(sqrt(sqrt(17 * sqrt(2) + 11 * sqrt(5))))))`. The product in the other order is the same class.

The shifted inverse of a rational plus one admitted radical then closes `1 / (1 + sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))`, and the quotient multiplies back to 1 by `inverse_unique`.

`1 / (1 + ...)` from the summit downward on the pair ladder stays outside, because the products of a summit with a crest, a peak, a high, or a pair are not yet in the kernel. A sum of two nested binomials of the same square-free integer stays that sum: `sqrt(2 + sqrt(2)) + sqrt(2 - sqrt(2))` is not rewritten as `sqrt(4 + 2 * sqrt(2))`. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is `1 / (1 + ...)` from the summit downward on the pair ladder. A boolean connective the kernel cannot settle, a set whose upper-bound predicate the kernel cannot decide, a nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero stay outside. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 116 tests, 0 failures, about 87.88 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — square-root tower arithmetic pgi-0.36.0

Adding one named ladder level per version never ends, and the suite had grown to about 87.88 seconds at pgi-0.35.0. This slice replaces the per-level product and inverse rules with one checked rule for arithmetic in a finite square-root tower over Q. An element is a vector on the basis of products of the adjoined square roots. Multiplication follows `(a + b√d)(c + e√d) = (ac + bed) + (ae + bc)√d`. The inverse is the conjugate over the norm, taken down the tower, and is kept only when it multiplies back to 1.

The old named cases remain tests of that one rule. `1 / (1 + sqrt(sqrt(2) + sqrt(5)))`, `1 / (1 + sqrt(sqrt(2 + sqrt(2))))`, `1 / (1 + a peak)`, `1 / (1 + a fold)`, and `1 / (1 + a crest)` are the same atoms as before, and each still multiplies back to 1 by `inverse_unique`. The same rule closes `1 / (1 + a summit)`, `1 / (1 + an apex)`, `1 / (1 + a shell)`, and further finite depth, and also `1 / (sqrt(sqrt(2) + sqrt(5)) + sqrt(2))`, which is `cauchy(-14/31 + 6/31 * sqrt(2) - 8/31 * sqrt(5) - 1/31 * sqrt(10) - 6/31 * sqrt(sqrt(2) + sqrt(5)) + 7/31 * sqrt(2 * sqrt(2) + 2 * sqrt(5)) + 1/31 * sqrt(5 * sqrt(2) + 5 * sqrt(5)) + 4/31 * sqrt(10 * sqrt(2) + 10 * sqrt(5)))`.

A monic inverse of one named radical keeps its compact absorbed form. A nest times a pair still uses the already closed biquadratic product when the two towers are not a prefix of one another. A sum of two nested binomials of the same square-free integer stays that sum: `sqrt(2 + sqrt(2)) + sqrt(2 - sqrt(2))` is not rewritten as `sqrt(4 + 2 * sqrt(2))`. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is a boolean connective the kernel cannot settle, and a set whose upper-bound predicate the kernel cannot decide. A nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero, stay outside. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 116 tests, 0 failures, about 57.85 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — boolean connectives and affine upper bounds pgi-0.37.0

A boolean connective inside one predicate reduces by the Collect lemmas, including when a side is itself a connective. A nested conjunction is associated and met, so `{x. 1 <= x and x <= 3 and x <= 4}` is `atLeastAtMost(1, 3)`. `Collect_neg_eq` and `double_compl` close `{x. not not x <= 2}` as `atMost(2)`. `imp_conv_disj` rewrites implication as the disjunction of the negated antecedent with the consequent, so `{x. x <= 1 implies x <= 3}` is `univ`. A disjunction, or a union, of two rays is one admitted set when they overlap or touch: `{x. x <= 1 or x <= 3}` is `atMost(3)`, and `{x. x <= 3 or 1 <= x}` is `univ`.

A comparison that is affine in the binder is moved to a standard ray by cancelling a shared summand and a nonzero coefficient, by `add_le_cancel_left`, `add_le_cancel_right`, `mult_le_cancel_left_pos`, and `mult_le_cancel_left_neg`. `{x. x <= x + 1}` is `univ`, and `sup {x. x <= x + 1}` is not bounded above. `{x. 2 * x <= x + 1}` is `atMost(1)`. `{x. 2 * x = x + 1}` is `{1}`. `{x. x + 1 <= x}` is empty. `{x. x < x}` stays the `less_irrefl` refusal.

A union of two rays that leaves a gap, such as `{x. x <= 1 or 3 <= x}`, stays outside. The complement of a nonempty finite set, such as `{x. not x = 2}`, stays outside. A predicate that is not affine in the binder, such as `{x. x * x <= 2}`, stays outside the bisection. A sum of two nested binomials of the same square-free integer stays that sum: `sqrt(2 + sqrt(2)) + sqrt(2 - sqrt(2))` is not rewritten as `sqrt(4 + 2 * sqrt(2))`. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is a union of two rays that leaves a gap, the complement of a nonempty finite set, and a predicate that is not affine in the binder, such as `{x. x * x <= 2}`. A nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero, stay outside. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 117 tests, 0 failures, about 49.14 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — gapped unions and finite complements pgi-0.38.0

A union of admitted rays or intervals that leaves a gap is stored as those pieces in order, by `Un_iff`. `{x. x <= 1 or 3 <= x}` is `atMost(1) union atLeast(3)`. `{x. x <= 3} union {x. 5 <= x}` is `atMost(3) union atLeast(5)`. `{x. x <= 1 or x = 3}` is `atMost(1) union set({3})`. A meet keeps the pieces that survive: `{x. x <= 1 or 3 <= x} inter {x. x <= 4}` is `atMost(1) union atLeastAtMost(3, 4)`. If the right-hand piece is bounded above, the supremum is that upper bound: `sup {x. x <= 1 or (2 <= x and x <= 3)}` is 3. If the right-hand piece is an up-ray, the union is not bounded above.

The complement of a finite set is the open down-ray before the least member, the open interval between consecutive members, and the open up-ray after the greatest member, by `linorder_neq_iff` and `Compl_insert`. `{x. not x = 2}` is `lessThan(2) union greaterThan(2)`. `{x. not (x = 1 or x = 2)}` is `lessThan(1) union greaterThanLessThan(1, 2) union greaterThan(2)`. The complement of a closed interval is the two outer rays: `{x. not (1 <= x and x <= 3)}` is `lessThan(1) union greaterThan(3)`. `imp_conv_disj` on a gapped implication is the same union: `{x. x <= 1 implies x <= 0}` is `atMost(0) union greaterThan(1)`.

A predicate that is not affine in the binder, such as `{x. x * x <= 2}`, stays outside the bisection. A sum of two nested binomials of the same square-free integer stays that sum: `sqrt(2 + sqrt(2)) + sqrt(2 - sqrt(2))` is not rewritten as `sqrt(4 + 2 * sqrt(2))`. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is a predicate that is not affine in the binder, such as `{x. x * x <= 2}`. A nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero, stay outside. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 118 tests, 0 failures, about 40.28 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — quadratic sign charts pgi-0.39.0

A comparison that is a polynomial of degree two in the binder is settled by a sign chart at the roots the kernel can construct and check. The difference of the two sides is formed, the discriminant is built, and each root is verified by evaluating the polynomial to zero. The sign at a midpoint is checked against the leading coefficient. `{x. x * x <= 2}` is `atLeastAtMost(-sqrt(2), sqrt(2))`. `{x. x * x < 2}` is `greaterThanLessThan(-sqrt(2), sqrt(2))`. `{x. 2 <= x * x}` is `atMost(-sqrt(2)) union atLeast(sqrt(2))`. `{x. x * x = 2}` is `set({-sqrt(2), sqrt(2)})`. A factored quadratic such as `{x. (x - 1) * (x - 3) <= 0}` is `atLeastAtMost(1, 3)`. A quadratic with no real roots and a positive leading coefficient, such as `{x. x * x + 1 <= 0}`, is empty. `sup {x. x * x <= 2}` is `cauchy(sqrt(2))`. Membership follows the admitted interval or cover.

A polynomial of degree greater than two, such as `{x. x * x * x <= 2}`, stays outside the bisection, as does a quadratic whose discriminant the kernel cannot form as a nonnegative radicand. A sum of two nested binomials of the same square-free integer stays that sum: `sqrt(2 + sqrt(2)) + sqrt(2 - sqrt(2))` is not rewritten as `sqrt(4 + 2 * sqrt(2))`. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is a polynomial of degree greater than two, such as `{x. x * x * x <= 2}`, and a quadratic whose discriminant the kernel cannot form as a nonnegative radicand. A nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero, stay outside. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 119 tests, 0 failures, about 37.89 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — tower product cache pgi-0.40.0

Tower multiplication still follows `(a + b√d)(c + e√d) = (ac + bed) + (ae + bc)√d`, and a constructed inverse is still kept only when it multiplies back to 1. A zero, a unit, or a rational factor is now scaled in one step instead of recursing through every layer, and a product of the same coordinate vectors in the same tower is reused. The admitted forms are unchanged. The full suite still runs before every push; slow engine tests were not split behind a marker.

A polynomial of degree greater than two, such as `{x. x * x * x <= 2}`, stays outside the bisection, as does a quadratic whose discriminant the kernel cannot form as a nonnegative radicand. A sum of two nested binomials of the same square-free integer stays that sum: `sqrt(2 + sqrt(2)) + sqrt(2 - sqrt(2))` is not rewritten as `sqrt(4 + 2 * sqrt(2))`. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is a polynomial of degree greater than two, such as `{x. x * x * x <= 2}`, and a quadratic whose discriminant the kernel cannot form as a nonnegative radicand. A nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero, stay outside. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 119 tests, 0 failures, about 12.50 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — greater-or-equal and greater-than rewrites pgi-0.41.0

`>=` and `>` are accepted in a predicate and rewritten to `<=` and `<` by flipping the sides. The rewrite is Lean `ge_iff_le` and `gt_iff_lt`, and Isabelle Orderings.thy defines `x ≥ y` as `y ≤ x` and `x > y` as `y < x`. It is not a silent parser swap. `{x. x >= 2}` is `atLeast(2)`. `{x. x > 2}` is `greaterThan(2)`. `{x. x * x >= 2}` is `atMost(-sqrt(2)) union atLeast(sqrt(2))`. `{x. x * x > 2}` is `lessThan(-sqrt(2)) union greaterThan(sqrt(2))`. `{x in {1, 2, 3}. x >= 2}` is `{2, 3}`. `{x. not x >= 2}` is `lessThan(2)`. `prove 5 >= 2` is `le(2,5)`.

A polynomial of degree greater than two, such as `{x. x * x * x <= 2}`, stays outside the bisection, as does a quadratic whose discriminant the kernel cannot form as a nonnegative radicand. A sum of two nested binomials of the same square-free integer stays that sum: `sqrt(2 + sqrt(2)) + sqrt(2 - sqrt(2))` is not rewritten as `sqrt(4 + 2 * sqrt(2))`. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is a polynomial of degree greater than two, such as `{x. x * x * x <= 2}`, and a quadratic whose discriminant the kernel cannot form as a nonnegative radicand. A nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero, stay outside. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 120 tests, 0 failures, about 13.19 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — polynomial sign charts and real algebraic numbers pgi-0.42.0

A comparison that is a polynomial in the binder, with rational coefficients, is settled by a checked sign chart rather than a degree-by-degree rule. Yun square-free factorization and a Sturm sequence isolate the real roots. A root expressible as a nested square root is kept in that form. Otherwise the root is stored as a checked real algebraic number: a primitive irreducible integer polynomial together with the index of that real root among the real roots, ordered increasingly. A Sturm sequence isolates the root in a rational interval that contains exactly one real root, and the number is kept only when that count, the irreducibility of the polynomial, and the index all check. The sign chart is kept only when it is checked at rational test points and at every constructed root. The original leading sign of the polynomial is preserved, so an inequality is not flipped when the primitive representative is taken.

`{x. x * x * x <= 2}` is `atMost(root(x^3 - 2, 1))`. `{x. x * x * x < 2}` is `lessThan(root(x^3 - 2, 1))`. `{x. x * x * x >= 2}` is `atLeast(root(x^3 - 2, 1))`. `{x. x * x * x = 2}` is `set({root(x^3 - 2, 1)})`. `sup {x. x * x * x <= 2}` is `cauchy(root(x^3 - 2, 1))`. `{x. x * x * x * x <= 2}` is `atLeastAtMost(-sqrt(sqrt(2)), sqrt(sqrt(2)))`. `{x. (x * x * x) - x <= 0}` is `atMost(-1) union atLeastAtMost(0, 1)`. `{x. (x * x - 2) * (x - 3) <= 0}` is `atMost(-sqrt(2)) union atLeastAtMost(sqrt(2), 3)`. `{x. x * x * x + x + 1 = 0}` is `set({root(x^3 + x + 1, 1)})`. A polynomial with no real roots and a positive leading coefficient, such as `{x. x * x * x * x + 1 <= 0}`, is empty. Membership follows the admitted ray, interval, or cover.

A quadratic whose coefficients are not all rational still uses the quadratic formula when the discriminant can be formed as a nonnegative radicand. A quadratic whose discriminant the kernel cannot form as a nonnegative radicand, such as `{x. x * x <= sqrt(sqrt(2)) + sqrt(sqrt(3))}`, stays outside. A polynomial whose coefficients are not all rational and whose degree is greater than two, such as `{x. x * x * x <= sqrt(2)}`, stays outside the bisection. A nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero, stay outside. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is a quadratic whose discriminant the kernel cannot form as a nonnegative radicand, such as `{x. x * x <= sqrt(sqrt(2)) + sqrt(sqrt(3))}`, and a polynomial whose coefficients are not all rational and whose degree is greater than two, such as `{x. x * x * x <= sqrt(2)}`. A nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero, stay outside. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 124 tests, 0 failures, about 13.38 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — polynomials with algebraic coefficients pgi-0.43.0

A comparison that is a polynomial in the binder, whose coefficients are rational, tower elements, or real algebraic numbers, is settled by one general checked method rather than a case-by-case rule. Each coefficient is converted to a rational or a real algebraic number. A resultant takes the polynomial down to a rational eliminant: the field norm when the coefficients lie in one number field, or an eliminant that is a multiple of the norm when several algebraic coefficients are treated as independent symbols. Yun square-free factorization and a Sturm sequence isolate the candidate real roots of that eliminant. A candidate is kept only when an exact vanishing check shows it is a root of the original polynomial. Isolating intervals are refined until every sign in the chart is certain. A root expressible as a nested square root is kept in that form. Otherwise it is stored as a checked real algebraic number. A quadratic still uses the quadratic formula when the discriminant can be formed; when that radicand cannot be formed, the same general method covers it.

`{x. x * x <= sqrt(sqrt(2)) + sqrt(sqrt(3))}` is `atLeastAtMost(root(x^32 - 20 * x^24 - 666 * x^16 - 3860 * x^8 + 1, 1), root(x^32 - 20 * x^24 - 666 * x^16 - 3860 * x^8 + 1, 4))`. `{x. x * x * x <= sqrt(2)}` is `atMost(root(x^6 - 2, 2))`. `{x. x * x * x < sqrt(2)}` is `lessThan(root(x^6 - 2, 2))`. `{x. x * x * x >= sqrt(2)}` is `atLeast(root(x^6 - 2, 2))`. `sup {x. x * x * x <= sqrt(2)}` is `cauchy(root(x^6 - 2, 2))`. `{x. (x * x - 2) * (x - sqrt(2)) <= 0}` is `atMost(-sqrt(2)) union set({sqrt(2)})`.

A polynomial whose resultant would exceed the kernel's degree limit stays outside. A nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero, stay outside. A sum of two nested binomials of the same square-free integer stays that sum: `sqrt(2 + sqrt(2)) + sqrt(2 - sqrt(2))` is not rewritten as `sqrt(4 + 2 * sqrt(2))`. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is a sum of two nested binomials of the same square-free integer, a nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero. A polynomial whose resultant would exceed the kernel's degree limit stays outside. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 128 tests, 0 failures, about 32.44 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — sums of conjugate nested binomials pgi-0.44.0

A sum of conjugate nested binomials of the same square-free integer is rewritten by squaring. The square is formed in the tower, the nonnegative square root is taken, and the identity is kept only when the candidate multiplies back to that square and `real_sqrt_unique` applies. When the numbers are algebraic, an exact algebraic comparison is required as well. `sqrt(2 + sqrt(2)) + sqrt(2 - sqrt(2))` is `sqrt(4 + 2 * sqrt(2))`. `sqrt(2 + sqrt(2)) - sqrt(2 - sqrt(2))` is `sqrt(4 - 2 * sqrt(2))`. `sqrt(3 + 2 * sqrt(2)) + sqrt(3 - 2 * sqrt(2))` is `2 * sqrt(2)`.

A nonnegative radicand the kernel cannot see, and a divisor the kernel cannot see as nonzero, stay outside. A boolean connective whose sides the kernel can now settle individually stays outside the connective rule until those sides are composed. A polynomial whose resultant would exceed the kernel's degree limit stays outside. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is nonnegativity and nonzero visibility by the exact sign machinery, and boolean sides that are now settleable. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 129 tests, 0 failures, about 32.06 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — exact signs for nonnegativity and nonzero divisors pgi-0.45.0

A sign that an isolating enclosure cannot decide is settled by a Sturm or algebraic sign when the form is a rational, a tower element, or a real algebraic number. A radicand whose sign is certified positive has a square root, stored as a nested radical when one can be formed, otherwise as a checked real algebraic number. A divisor whose sign is certified nonzero has an inverse, checked by multiplying back to 1. `0 <= -2 + sqrt(sqrt(2)) + sqrt(sqrt(3))` holds. `sqrt(sqrt(sqrt(2)) + sqrt(sqrt(3)))` is `root(x^32 - 20 * x^24 - 666 * x^16 - 3860 * x^8 + 1, 4)`. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next gap is a boolean connective whose sides the kernel can now settle individually. A radicand or divisor whose sign the exact algebraic or Sturm test cannot decide stays outside. A polynomial whose resultant would exceed the kernel's degree limit stays outside. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are still not ingested.

`python -m unittest discover -s tests -v` finished 130 tests, 0 failures, about 48.97 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — boolean sides of settled charts pgi-0.46.0

A boolean connective whose sides the kernel can settle individually is composed by the Collect lemmas, rather than left outside. Each side is reduced first: a polynomial or algebraic-coefficient comparison becomes its checked sign chart, and a ray stays a ray. Conjunction is intersection, disjunction is union, negation is complement, and implication is rewritten to `not P or Q`. `{x. x * x <= 2 and 0 <= x}` is `atLeastAtMost(0, sqrt(2))`. `{x. not x * x <= 2}` is `lessThan(-sqrt(2)) union greaterThan(sqrt(2))`. `{x. x * x <= 2 or x * x * x <= 2}` is `atMost(sqrt(2))`. `{x. x * x <= 2 implies x <= 3}` is `univ`. `{x. x * x * x <= sqrt(2) and 0 <= x}` is `atLeastAtMost(0, root(x^6 - 2, 2))`. `sup {x. x * x <= 2 and 0 <= x}` is `cauchy(sqrt(2))`. A boolean connective whose sides the kernel cannot settle stays outside.

A radicand or divisor whose sign the exact algebraic or Sturm test cannot decide stays outside. A polynomial whose resultant would exceed the kernel's degree limit stays outside. A negative radicand stays open. Division by zero stays open. Isabelle `real_sqrt_minus` stays refused. Isabelle `inverse (0::real) = 0` stays refused.

`primitive.continuum` still blocks `law(sqrt_two_is_rational)`. Core Lean 4.36.0, with no imports, does not resolve these names. Octave is not used for this root.

The next work, in GOAL order, is linear algebra. CODATA, the Particle Data Group, gravitational-wave catalogs, and the Mercury residual in arcseconds are being admitted on a parallel stream.

`python -m unittest discover -s tests -v` finished 131 tests, 0 failures, about 51.91 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — CODATA 2022 constants on the board pgi-0.47.0

The first sourced numbers are on the board. `pgi/corpus/measured.py` holds the CODATA 2022 recommended values, P. J. Mohr, D. B. Newell, B. N. Taylor, and E. Tiesinga, Rev. Mod. Phys. 97, 025002 (2025), doi:10.1103/RevModPhys.97.025002, read from https://physics.nist.gov/cuu/Constants/Table/allascii.txt on 2026-11-25. Each record cites its own NIST page. Each value is the printed text, and the rational is parsed from it. A printed value that ends in an ellipsis is refused.

The seven SI defining constants are exact rationals, and a claim to have derived one contests the board. `c` stays `anchor.c_si`. The measured set is `G`, `α`, `1/α`, `m_e`, `m_p`, `m_n`, their MeV equivalents, `m_p/m_e`, `R_∞`, `a_0`, `μ_0`, `ε_0`, and `G_F`, each with the standard uncertainty NIST quotes. The board kinds gain `measured_anchor`. That is 22 quantities and 21 new records.

The stored numbers are checked against one another in exact rational arithmetic: `α` from `e`, `h`, `c`, and `ε_0`; `μ_0` from `α`; `μ_0 ε_0 c^2 = 1`; `1/α`; `R_∞` from `α`, `m_e`, `c`, and `h`; `a_0` from `α` and `R_∞` with a Machin enclosure of π; `m_p/m_e`; and the MeV equivalents. Each agrees inside the combined standard uncertainty. A planted ten-sigma shift in `ε_0` is caught. No relation is stored as a claim.

The next slice is the Particle Data Group: the W, Z, Higgs, and top masses, the leptons, the light quarks as quoted, `α_s(M_Z)`, `G_F`, `sin^2 θ_W`, and the CKM fit.

`python -m unittest discover -s tests -v` finished 144 tests, 0 failures, about 49.35 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — exact rational matrices pgi-0.48.0

A matrix over the rationals is a rectangular array of reduced fractions. Addition, multiplication, and transpose use those exact entries. A determinant is the Bareiss value after clearing denominators, and through degree five the cofactor expansion has to agree. `det([[1, 2], [3, 4]])` is `-2`. `det([[1, 2, 3], [4, 5, 6], [7, 8, 10]])` is `-3`. `det([[1/2, 0], [0, 1/3]])` is `1/6`. A rank is kept only when a pivot minor has a nonzero determinant and every other row is the corresponding linear combination of the pivot rows. `rank([[1, 2], [3, 4]])` is `2`. `rank([[1, 2], [2, 4]])` is `1`. An inverse is kept only when both products are the identity. `inv([[1, 2], [3, 4]])` is `[[-2, 1], [3/2, -1/2]]`. A singular inverse and a non-square determinant stay open. An entry that is not an exact rational stays open.

Characteristic polynomials and eigenvalues of these matrices are the next mathematics, using the existing algebraic-number kernel. Manifolds, differential geometry, Hilbert space, and gauge theory follow. The Particle Data Group is being admitted on a parallel stream.

`python -m unittest discover -s tests -v` finished 148 tests, 0 failures, about 47.04 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — PDG 2026 masses, couplings, and the CKM fit pgi-0.49.0

The Particle Data Group numbers are on the board, from the 2026 edition: F. Takahashi et al. (Particle Data Group), Int. J. Mod. Phys. A 41, 2630011 (2026). Masses are the summary-table rows of the PDG API database, `pdg` package 2026.0, data release 2026-05-30, each citing its pdgLive node. `α_s(m_Z) = 0.1180(9)`, `G_F/(ħc)^3 = 1.166 378 5(6) e-5 GeV^-2`, and MSbar `sin^2 θ̂_W(m_Z) = 0.231 22(6)` are from Table 1.1, revised May 2026. The CKM global fit is from review 12, revised March 2026.

`m_W`, `m_Z`, the measured `m_W/m_Z`, `m_H`, the direct `m_t`, `m_e`, `m_μ`, and `m_τ` carry PDG's one-standard-deviation errors, with the scale factor noted where PDG applied one. The u, d, and s masses are MSbar at 2 GeV, and `m_c(m_c)` and `m_b(m_b)` are MSbar running masses. PDG prints all five with CL = 90%, and the uncertainty kind says so. The Wolfenstein parameters, the nine magnitudes, and `J` keep their asymmetric errors. The uncertainty kinds gain `asymmetric standard uncertainty` and `uncertainty at CL = 90%`. That is 30 new quantities and 30 new records.

The concise forms are parsed and matched to the stored numbers. `m_W/m_Z` from the masses agrees with the measured ratio. The PDG and CODATA electron masses are the same number. The PDG and CODATA `G_F` differ in the last digit and agree inside the uncertainty. Each row and column of the CKM magnitudes squares to 1 inside the propagated uncertainty. No relation is stored as a claim.

The next slice is the Mercury perihelion residual and the gravitational-wave events.

`python -m unittest discover -s tests -v` finished 156 tests, 0 failures, about 47.54 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — Mercury's perihelion residual and the gravitational-wave events pgi-0.50.0

Clemence's 1947 reduction of Mercury's perihelion is on the board, from Rev. Mod. Phys. 19, 361 (1947), Table II, doi:10.1103/RevModPhys.19.361. The APS page needs a login, so the numbers were read from a scan of the journal pages. Observed `5599.74 ± 0.41`, computed without relativity `5557.18 ± 0.85`, residual `42.56 ± 0.94`, all in arcseconds per Julian century. The errors are Clemence's probable errors, a half-probability range widened for systematics, and the uncertainty kind says so. No conversion to a standard uncertainty is stored. The relativity effect he prints is a theory value and is left out. The residual blocks `law(newtonian_perturbations_explain_mercury_perihelion)`.

GW150914 is on the board from GWTC-1, Phys. Rev. X 9, 031040 (2019), Table III, through the GWOSC event API: the source-frame masses, chirp mass, final mass, final spin, radiated energy, `χ_eff`, luminosity distance, and redshift, each a median with a 90% credible interval. The GW170817 speed-of-gravity bound is on the board from ApJL 848, L13 (2017), Eq. (2), `−3 × 10^-15 ≤ (v_GW − v_EM)/v_EM ≤ +7 × 10^-16`, with its distance and emission-lag assumptions written on the record. The uncertainty kinds gain `probable error` and `90% credible interval`. A bound is its own object with no central value. That is 12 new quantities, one bound, and 13 new records.

Observed minus computed is exactly the residual. The probable errors combine in quadrature to 0.94 at the printed places. The GW150914 chirp mass from the median component masses sits inside its interval, and the medians close the energy budget exactly.

The next slice stores the Planck and Rayleigh–Jeans spectral formulas, with Rayleigh–Jeans marked failed at high frequency.

`python -m unittest discover -s tests -v` finished 164 tests, 0 failures, about 46.19 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — Planck and Rayleigh–Jeans as stored formulas pgi-0.51.0

Planck's spectral law and the Rayleigh–Jeans law are stored formulas. `pgi/corpus/formulas.py` keeps each in its source's notation, with its variables, source, page, and retrieval date. The board kinds gain `stored_formula`. A stored formula is not a theorem.

Planck's law is equation (12) of Annalen der Physik 309, 553–563 (1901), doi:10.1002/andp.19013090310, read from the proofread Wikisource transcription of page 561: `u = (8 π h ν^3 / c^3) / (exp(h ν / (k θ)) − 1)`. Its standing is stored, and `derived(planck_spectrum)` is blocked. The Rayleigh–Jeans law is Planck's equation (8) on page 560 with equipartition, `u = 8 π ν^2 k θ / c^3`. Its standing is failed at high frequency, and `law(rayleigh_jeans_at_high_frequency)` is blocked. Rayleigh's and Jeans' own pages were behind logins, so their notation is not copied, and `known.rayleigh_jeans` still carries the failure.

With the CODATA constants, the two agree to one part in a thousand at `h ν / k θ = 10^-4`, and Rayleigh–Jeans is more than a million times Planck at `h ν / k θ = 20`. The Rayleigh–Jeans total grows eightfold with each doubling of the cutoff. Planck's tail falls.

The physics board now holds 64 quantities, one bound, and two formulas. The next sourced data are a modern Mercury reduction with standard uncertainties, the rest of the gravitational-wave catalogs, and atomic-clock comparisons.

`python -m unittest discover -s tests -v` finished 168 tests, 0 failures, about 58.28 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — characteristic polynomials and real eigenvalues pgi-0.52.0

The characteristic polynomial of a square rational matrix is `det(tI - A)`, monic in t. It is kept only when Faddeev–LeVerrier agrees with interpolation through those determinants, the polynomial annihilates the matrix, and it matches the determinant at an extra point. `charpoly([[1, 2], [3, 4]])` is `x^2 - 5 * x - 2`. `charpoly([[0, -1], [1, 0]])` is `x^2 + 1`. `charpoly([[2, 0, 0], [0, 3, 0], [0, 0, 5]])` is `x^3 - 10 * x^2 + 31 * x - 30`. Real eigenvalues are the real roots of that polynomial, isolated by the algebraic-number kernel. `eigenvalues([[0, 1], [1, 0]])` is `{-1, 1}`. `eigenvalues([[0, 2], [1, 0]])` is `{-sqrt(2), sqrt(2)}`. `eigenvalues([[1, 2], [3, 4]])` is `{5/2 - 1/2 * sqrt(33), 5/2 + 1/2 * sqrt(33)}`. A characteristic polynomial with no real root, such as `eigenvalues([[0, -1], [1, 0]])`, yields the empty set. A non-square matrix has no characteristic polynomial here.

The next mathematics, in GOAL order, is manifolds, then differential geometry, Hilbert space, and gauge theory. A modern Mercury reduction, the rest of the gravitational-wave catalogs, and atomic-clock comparisons are being admitted on a parallel stream.

`python -m unittest discover -s tests -v` finished 169 tests, 0 failures, about 50.61 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — modern Mercury perihelion and PPN fits pgi-0.53.0

The modern Mercury numbers are on the board beside Clemence's. Park et al., Astron. J. 153, 121 (2017), doi:10.3847/1538-3881/aa5be2, read from the IOP PDF: total perihelion rate `575.3100 ± 0.0015` arcsec per Julian century along Mercury's mean orbit plane, `β − 1 = (−2.7 ± 3.9) × 10^-5`, and solar `J2 = (2.25 ± 0.09) × 10^-7`. Table 1 of that paper prints `−2.6` for `β − 1`; the abstract value is stored and the difference is recorded. Pitjeva and Pitjev, MNRAS 432, 3431 (2013), EPM2011, from arXiv:1306.3043: Mercury's additional perihelion precession `−0.020 ± 0.030` mas/yr, and `β − 1 = −0.00002 ± 0.00003`, `γ − 1 = +0.00004 ± 0.00006` at 3σ. Bertotti, Iess, and Tortora, Nature 425, 374 (2003): `γ − 1 = (2.1 ± 2.3) × 10^-5`.

The uncertainty kinds gain `uncertainty as printed, level not stated`, for Park and Bertotti, and `3 sigma`. A confidence level is not guessed. The computed relativistic contributions in Park's Table 3 are not stored. INPOP was not added in this slice.

The EPM2011 residual sits inside its uncertainty. The two `β` intervals overlap, the Cassini and EPM2011 `γ` intervals overlap, and every `β − 1` and `γ − 1` interval contains zero. That is 7 new quantities and 7 new records.

The publish step had been rewriting every copy of the old version string in GOAL.md, which moved the dates in two earlier entries. They are put back: PDG 2026 entered in `pgi-0.49.0`, and GW150914 with the GW170817 bound in `pgi-0.50.0`. Only the current-version lines change now.

The next slice is cosmology: Planck 2018, SH0ES, DESI DR2, and the CMB temperature.

`python -m unittest discover -s tests -v` finished 173 tests, 0 failures, about 52.20 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — cosmology: Planck 2018, SH0ES, DESI DR2, and the CMB temperature pgi-0.54.0

The cosmology anchors are on the board. Planck 2018 VI, A&A 641, A6 (2020), arXiv:1807.06209, Table 2, the baseline TT,TE,EE+lowE+lensing column: `H0`, `Ω_b h^2`, `Ω_c h^2`, `100θ_MC`, `τ`, `ln(10^10 A_s)`, `n_s`, `Ω_Λ`, `Ω_m`, `Ω_m h^2`, `σ_8`, and `S_8`, each a 68% interval inside base-ΛCDM. SH0ES, Riess et al., ApJL 934, L7 (2022), arXiv:2112.04510: `H0 = 73.04 ± 1.04` km/s/Mpc, with the abstract's 5σ statement about Planck+ΛCDM written on the record. DESI DR2, Phys. Rev. D 112, 083515 (2025), arXiv:2503.14738: `w0` and `wa` for DESI+CMB and for DESI+CMB with Pantheon+, Union3, and DESY5, each combination its own record. Fixsen, ApJ 707, 916 (2009), arXiv:0911.1955: `T_0 = 2.72548 ± 0.00057 K`.

The uncertainty kinds gain `68% interval`. A fitted parameter is labeled with its model and data combination. It is a measured anchor inside that model, not a model-free measurement.

Planck's printed `Ω_m + Ω_Λ` is exactly 1. `Ω_m h^2` agrees with `Ω_m (H0/100)^2`, and `S_8` agrees with `σ_8 (Ω_m/0.3)^0.5`. The SH0ES and Planck H0 values differ by more than four combined uncertainties. Both stay on the board and neither is retracted: they are two measurements by different routes, not one name with two sources. DESI's `w0` is above −1 and `wa` below 0 in every combination. That is 22 new quantities and 22 new records.

The next slice is precision particle measurements: the neutron lifetime, `g_A`, the muon and electron `g − 2`, and the proton charge radius.

`python -m unittest discover -s tests -v` finished 177 tests, 0 failures, about 54.42 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — multivariate polynomials, rational functions, and exact partial derivatives pgi-0.55.0

A multivariate polynomial over the rationals is a finite sum of reduced coefficients times monomials. A rational function is a reduced quotient: the numerator and denominator are divided by their primitive GCD, and a zero denominator stays open. A partial derivative is termwise on a polynomial, or the quotient rule on a rational function, kept only when that identity multiplies back. Mixed partials of a polynomial commute, checked exactly. `d(x^2, x)` is `2 * x`. `d(x^2 * y + 3 * x, x)` is `2 * x * y + 3`. `d(x^2 + 2 * x * y + y^2, x)` is `2 * x + 2 * y`. `d(d(x^3 * y^2, x), y)` is `6 * x^2 * y`. `(x^2 - 1) / (x - 1)` is `x + 1`. `(x^2 - y^2) / (x - y)` is `x + y`. `d((x^2 + 1) / (x + 1), x)` is `(x^2 + 2 * x - 1) / (x^2 + 2 * x + 1)`. `d(1 / x, x)` is `-1 / x^2`. `x / x` is `1`. `2^3` is `8`. `(1/2)^2` is `1/4`. A zero denominator and `0^0` stay open.

The next mathematics is charts and transition maps that compose to the identity, then Jacobians, tangent vectors, and the metric tensor. Precision particle measurements are being admitted on a parallel stream.

`python -m unittest discover -s tests -v` finished 181 tests, 0 failures, about 45.94 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — precision particle measurements: neutron lifetime, g_A, muon and electron g − 2, proton radius pgi-0.56.0

The precision particle anchors are on the board. Neutron lifetime: UCNτ 2021, Phys. Rev. Lett. 127, 162501, arXiv:2106.10375; UCNτ 2025, Phys. Rev. C 111, 045501, arXiv:2409.05560, which averages all UCNτ data; the NIST beam result, Phys. Rev. Lett. 111, 222501 (2013), arXiv:1309.2623; and the PDG 2026 average, `878.3 ± 0.4 s` with S = 1.8. PDG 2026 `λ = g_A/g_V = −1.2753 ± 0.0013`, S = 2.7. Final muon `g − 2`, Phys. Rev. Lett. 135, 101802 (2025), arXiv:2506.03069: Fermilab combined and the experimental world average, both as printed, `116 592 0705(148)` and `116 592 0715(145)` × 10^−12. PDG 2026 `a_μ`. Electron, Fan et al., Phys. Rev. Lett. 130, 071801 (2023), arXiv:2209.13084: `g/2 = 1.001 159 652 180 59(13)`. PDG 2026 `a_e`. CODATA 2022 `a_e`, `a_μ`, and `r_p`, and PDG `r_p`.

The UCNτ and beam papers print statistical and systematic uncertainties separately. A new kind, `statistical and systematic, printed separately`, carries both. The record states both, and the audit refuses the kind without its systematic part. Nothing combines them on the board. The tests add them in quadrature, larger side, only to compare.

PDG's lifetime agrees with UCNτ 2025. Beam and bottle differ by more than four combined uncertainties, and every lifetime record stays on the board with none retracted. The Fermilab, PDG, and CODATA muon anomalies agree with the world average. Fan's `g/2 − 1` agrees with CODATA and PDG `a_e`. The proton radius agrees across CODATA metres and PDG femtometres. The PDG measurement flags say which entries feed each average, and the records say so. No theory prediction for `a_μ`, `a_e`, or `τ_n` is stored. That is 14 new records.

The next slice is the NIST ASD first ionization energies, H to Ne.

`python -m unittest discover -s tests -v` finished 187 tests, 0 failures, about 49.01 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — NIST ASD first ionization energies, H to Ne pgi-0.57.0

The first ionization energies H I to Ne I are on the board as measured anchors. They come from NIST ASD version 5.12, doi:10.18434/T4W30F, Ionization Energies Data, queried in eV with the uncertainty, level, configuration, and bibliography columns. The full query URL is on every record. Values and uncertainties are kept as the CSV served them: H `13.598434599702(12)` through Ne `21.564541(7)` eV. Each row carries its ASD reference codes and its ground and ionized levels.

ASD prints the hydrogen value in parentheses, its mark for a theoretical value, and the record carries the help page's wording. The help page says eV output includes the CODATA conversion uncertainty and names no confidence level. The rows are labelled `uncertainty as printed, level not stated`. CODATA 2022 `R_∞ hc` in eV is added.

The tests check that each row loads with its uncertainty, that helium is highest and lithium lowest, and that hydrogen sits below `R_∞ hc` and within `α^2` of the reduced-mass ratio. That window is a loose test, not a stored relation. That is 11 new records.

The second physics batch is done. The open items are INPOP ephemeris numbers and the levels Park, Bertotti, Riess, and Fixsen leave unstated.

`python -m unittest discover -s tests -v` finished 190 tests, 0 failures, about 48.84 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — INPOP perihelion and PPN results pgi-0.58.0

INPOP results are on the board, each with its stated uncertainty kind. The INPOP19a and INPOP21a notes from IMCCE were read in full. Neither prints PPN `β` or `γ`. Their solar `J2` values are stored: INPOP19a `(2.010 ± 0.010) × 10^−7` in a ± 1σ column, and INPOP21a `(2.2180 ± 0.01) × 10^−7` with no level. The notes disagree on INPOP19a's `GM_⊙`. That is written down, and neither value is stored.

INPOP20a, Proc. IAU Symp. 364, Table 4: `β − 1 = (−1.12 ± 7.16) × 10^−5` and `γ − 1 = (−1.69 ± 7.49) × 10^−5`, stated at 99.7% of the WRSS distribution. The least-squares row, `−1.9 ± 6.28` and `2.64 ± 3.44` × 10^−5, has no level named. The Living Reviews reprint of that `β − 1` has the opposite sign. The original is kept, and the difference is noted. INPOP15a, MG14 proceedings: Mercury's supplementary perihelion `0.0 ± 3.1` mas/cy and `0.0 ± 1.05` mas/cy, acceptance intervals under `Δ(O − C) < 35%` and `< 5%`. Fienga and Minazzoli 2024: the overlap `β − 1 = (−0.45 ± 1.75) × 10^−5`, `γ − 1 = (0.55 ± 1.35) × 10^−5`. B-INPOP with INPOP21a, A&A 682, A175 (2024): `1 − γ < 1.73, 2.40, 2.50 × 10^−5` at 66.7%, 95%, 99.7% C.L., stored as bounds whose lower end is the prior edge.

The uncertainty kinds gain `99.7% interval` and `acceptance interval`. Every printed interval contains zero. The nested windows nest, and the B-INPOP limits rise with the level. A `ppn gamma` ask links INPOP, Cassini, and B-INPOP with nothing retracted. That is 13 new records.

The next slice is the NIST ASD first ionization energies, Na to Kr.

`python -m unittest discover -s tests -v` finished 195 tests, 0 failures, about 65.82 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — NIST ASD first ionization energies, Na to Kr pgi-0.59.0

The first ionization energies Na I to Kr I are on the board. They come from NIST ASD version 5.12, Ionization Energies Data, in eV, with the query URL on each record and each row's own ASD uncertainty, bibliography codes, and levels. Values are kept as served: Na `5.13907696(25)` through Kr `13.9996055(20)` eV. No row in this range is bracketed or parenthesized.

In each period the alkali metal is lowest and the noble gas highest, as printed. Calcium's `5 × 10^−10` eV uncertainty loads exactly. The generic `ionization` key is dropped from the ASD rows, because with 36 rows it linked every element to every ask. Each row now links by its element's phrases only. That is 26 new records.

The next slice is AME2020 atomic masses.

`python -m unittest discover -s tests -v` finished 196 tests, 0 failures, about 54.75 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — charts, transition maps, and Jacobians pgi-0.60.0

A transition map is a tuple of reduced rational functions between charts, kept only when the two-way composition is the identity. The Jacobian is the matrix of exact partial derivatives, and composition is kept only when the chain rule holds identically. `compose(transition(s2, south, north), transition(s2, north, south))` is `identity(u, v)`. The same holds for the stereographic charts on the circle, the affine charts on the real projective line, and the linear charts on the plane, which also satisfy the cocycle identity. `jacobian(transition(r2, xy, uv))` is `[[1, 1], [1, -1]]`, and its determinant is `-2`. `det(jacobian(transition(s2, north, south)))` is `-1 / (u^2 + v^2)^2`. A Jacobian inverse is kept only when both products are the identity. An unknown chart and a composition that is not an inverse pair stay open.

The next mathematics is tangent vectors and the metric tensor, first for Euclidean and Minkowski space and then for the 2-sphere. Further sourced physics data is being admitted on a parallel stream.

`python -m unittest discover -s tests -v` finished 200 tests, 0 failures, about 50.36 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — AME2020 atomic masses and binding energies, starter set pgi-0.61.0

AME2020 is on the board for n, ¹H, ²H, ³H, ³He, ⁴He, ¹²C, ¹⁶O, ⁵⁶Fe, ⁵⁸Fe, ⁶²Ni, and ²⁰⁸Pb: atomic mass in µu, mass excess in keV, and binding energy per nucleon in keV where A ≥ 2. Values come from the AMDC file `mass.mas20`, which Part II names as the full-precision version of its rounded table. Part I says every uncertainty is 1σ, so the label is `standard uncertainty`. ¹²C's mass is printed as `12 000000.0` with uncertainty 0.0 and is stored exact, by the definition of u. AME2020's `1 u = 931 494.10242(28) keV` is stored. ⁵⁸Fe was added to the requested set so the peak is shown with its real neighbours.

¹²C is exactly 12 u. ⁶²Ni `8794.5555`, ⁵⁸Fe `8792.2534`, and ⁵⁶Fe `8790.3563` keV are the top three per nucleon, as printed. Each `B/A` is recomputed from the mass excesses of the nuclide, ¹H, and n, and each mass from `A + Δ/u`. Both agree inside the printed uncertainties. No nuclear model is stored. That is 35 new records.

The next slice is PDG 2026 light hadron masses.

`python -m unittest discover -s tests -v` finished 204 tests, 0 failures, about 48.16 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — PDG 2026 light hadron masses pgi-0.62.0

PDG 2026 light hadron masses are on the board from the pdg 2026.0 database: π±, π⁰, K±, K⁰, η, ρ(770), ω(782), p, n, Λ, and Δ(1232), plus the measured `m_n − m_p`. Each record says whether it is PDG's FIT, AVERAGE, or EVALUATION, and carries the scale factor where PDG applies one: π± 1.8, π⁰ 1.1, K± 2.8, K⁰ 1.2, ω 2.0. The ρ record is the neutral e⁺e⁻ average and lists PDG's other three ρ averages. Δ(1232) is printed `1230 TO 1232 TO 1234`. It is stored under a new kind, `PDG estimated range`, because it is not a standard uncertainty.

`m_n − m_p` agrees with the two masses and with CODATA. The proton mass equals CODATA 2022 exactly. The isospin splittings run the printed way: π± above π⁰, K⁰ above K±, n above p. No quark-model mass formula is stored. That is 12 new records.

That closes the third physics batch: INPOP, ASD Na to Kr, AME2020, and the light hadrons.

`python -m unittest discover -s tests -v` finished 208 tests, 0 failures, about 49.98 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — gravity tests: binary pulsars, Gravity Probe B, VLBI, and the 16 values of G pgi-0.63.0

Gravity tests are on the board. Hulse–Taylor, Weisberg and Huang 2016, arXiv:1606.02744: `Ṗb,intr/Ṗb,GR = 0.9983 ± 0.0016`. Double Pulsar, Kramer et al. 2021, arXiv:2112.06795, Table V: `Ṗb`, `ω̇`, `s`, `r`, and `γ_E` as observed over GR, in concise form. Gravity Probe B final, arXiv:1105.3456: geodetic `−6601.8 ± 18.3` and frame-dragging `−37.2 ± 7.2` mas/yr, 1σ by the paper. VLBI, Lambert and Le Poncin-Lafitte 2011, from the HAL open copy: `γ = 0.99992 ± 0.00012`, a formal error. The pulsar ratios carry no level because neither paper's table names one. The 95% statement for the Double Pulsar `Ṗb` is written in the note. GR predictions appear only in the notes.

The 16 measured values of G in CODATA 2022 Table XXX are stored one by one, each 1σ, with lab, method, and the three printed correlations. The stored values reproduce CODATA's own numbers exactly. BIPM-14's normalized residual against `6.674 30` is `7.75` and JILA-18's is `−6.80`, the two extremes CODATA names. With the 3.9 expansion factor every residual falls to 2 or less. The spread of the 16 is more than 20 recommended uncertainties. That is the disagreement in the G data.

That is 25 new records. The next slice is atomic spectroscopy.

`python -m unittest discover -s tests -v` finished 212 tests, 0 failures, about 50.65 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — atomic spectroscopy: hydrogen 1S–2S, Lamb shift, 21 cm, H-alpha, muonic hydrogen pgi-0.64.0

Hydrogen spectroscopy is on the board. 1S–2S, Parthey et al. 2011, arXiv:1107.3101: `2 466 061 413 187 035(10)` Hz, σ by the paper's table. Matveev 2013 is taken from CODATA 2022 Table XI. The Lamb shift 2P1/2−2S1/2 is taken from the same table: Bezginov 2019 `1 057 829.8(3.2)` kHz and Lundeen–Pipkin 1981 `1 057 845.0(9.0)` kHz. 21 cm, Hellwig et al. 1970, the NIST scan: `1 420 405 751.768 ± 0.002` Hz, 1σ. The scanned abstract's exponent misprints as `10-2`, and a note says so. H-alpha, ASD 5.12 lines in air: the n = 2–3 blend, observed and Ritz, plus the strongest component, with no level. Muonic hydrogen, Antognini 2013 via PubMed, 1σ: the two frequencies, `r_E 0.84087(39)` fm, and `r_Z 1.082(37)` fm. The `202.3706(23)` meV Lamb shift is taken from CODATA Table XIV because Science is paywalled.

`parse_concise` now reads `829.8(3.2)`, with the uncertainty in the value's units. The hydrogen records link through phrases only, so "muonic hydrogen" pulls the five muonic records and nothing else.

That is 13 new records. The next slice is nuclear.

`python -m unittest discover -s tests -v` finished 219 tests, 0 failures, about 54.55 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — nuclear constants: deuteron binding, alpha mass, nucleon moments pgi-0.65.0

The nuclear constants are on the board from CODATA 2022. The deuteron binding energy `2224.566 40(38)` keV is taken from the paper's Sec. II.B, because the NIST table does not list it. The deuteron and alpha-particle masses are stored in kg, u, and MeV. The nuclear magneton, μ_p and μ_n in J/T and in nuclear magnetons, and CODATA's μ_n/μ_p ratio are stored too. All are 1σ.

The tests close the loops. The CODATA masses give the binding energy, and AME2020's ²H binding per nucleon agrees. The alpha kg-to-MeV conversion holds with the exact c and e. AME2020's u-to-keV factor is CODATA 2018's, which puts the alpha about 5 eV low against CODATA 2022, and a test pins that gap. AME ⁴He minus the alpha and two electrons gives 79 eV, which matches ASD He I plus 4 Ry. The moment ratios multiply out.

That is 13 new records. The next slice is Stefan–Boltzmann and Wien.

`python -m unittest discover -s tests -v` finished 223 tests, 0 failures, about 65.68 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — metrics, tangent vectors, and curvature pgi-0.66.0

A metric is a symmetric matrix of reduced rational functions on a chart. A tangent vector is a derivation with rational components, kept only when it annihilates constants, reproduces its components on the coordinates, and satisfies Leibniz. A pullback is `J^T g J` along the map, functorial on the plane atlas, and the identity pullback is the original metric. The unit 2-sphere metric in stereographic coordinates is the pullback of the Euclidean 3-metric through the inverse stereographic embedding, kept only when that embedding lands on `X^2 + Y^2 + Z^2 = 1` and the pullback equals `4 / (1 + ρ^2)^2` times the identity. `metric(e2)` is `[[1, 0], [0, 1]]`. `metric(minkowski2)` is `[[-1, 0], [0, 1]]`. `apply(vector(e2, 1, 0), x^2)` is `2 * x`.

Christoffel symbols, Riemann, Ricci, and the scalar curvature are computed exactly. The inverse metric multiplies back to the identity. The Levi-Civita connection is torsion-free and metric-compatible. The Riemann symmetries and both Bianchi identities hold identically. Flat Euclidean and Minkowski space have vanishing curvature. `scalar(metric(s2, north))` is `2`, and the Ricci tensor equals the metric. An unknown chart stays open.

The next mathematics is Hilbert space, then gauge theory. Further sourced physics data is being admitted on a parallel stream.

`python -m unittest discover -s tests -v` finished 227 tests, 0 failures, about 64.43 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.

## 2026-11-25 — Stefan–Boltzmann and Wien constants, exact and printed truncated pgi-0.67.0

σ, b, and b′ are on the board from CODATA 2022 as exact definitional anchors. CODATA prints them as `5.670 374 419... e-8`, `2.897 771 955... e-3`, and `5.878 925 757... e10`, and the digits are stored as printed. The new kind `exact, printed truncated` makes the record an interval [digits, digits + 1 ulp). `value` refuses it, `truncation_bounds` gives it, and the statement says so.

The tests check σ = 2π⁵k⁴/(15h³c²) with an exact Machin enclosure of π. The Wien roots of x = 5(1 − e^−x) and x = 3(1 − e^−x) are enclosed by rational Taylor bounds and a sign check. hc/(k x₅) and x₃k/h fall inside the printed intervals. All of it is exact rationals.

That is 3 new records, and batch 4 is complete.

`python -m unittest discover -s tests -v` finished 231 tests, 0 failures, about 69.11 seconds, on Python 3.13.5, with GNU Octave 9.4.0 on PATH.
