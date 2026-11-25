# Procedural Generated Intelligence

*No Man's Sky* does not store billions of planets on a hard drive. It stores compact mathematical rules, deterministic seeds, and layered composition functions that unfold rich, coherent structure on demand.

Applying that philosophy to artificial intelligence flips traditional deep learning on its head. A procedurally generated intelligence (PGI) stores generative rules, latent seeds, constraint grammars, and context-driven synthesis functions, and unfolds thoughts, reasoning chains, and world models dynamically as a prompt arrives.

Large language model design and other artificial intelligence systems are reference points while this is built. The target is the same kind of compact world-building *No Man's Sky* uses, applied to an intelligence.

The realistic version is a hybrid neuro-procedural architecture. Compact learned modules supply intuition and representations. Procedural rule engines handle structure, verification, and on-demand expansion.

## How *No Man's Sky* translates to AI

| Dimension | Traditional neural nets / LLMs | Procedural intelligence |
| --- | --- | --- |
| Knowledge storage | Billions of learned parameter weights frozen during training | Compact rulesets, semantic grammars, constraint graphs, and seeds |
| How answers form | Statistical token prediction across dense layers | Deterministic or seeded unfolding of concepts, logic, and analogies |
| Memory footprint | Massive model checkpoints and KV caches | Tiny rule-engine core plus a lightweight state/seed log |
| Novelty and edge cases | Interpolates from the training distribution; can hallucinate plausibly | Generates fresh combinations via rule interaction; can hit rule-clash dead ends |
| Consistency | Relies on the context window and RLHF alignment | Can preserve deterministic consistency from a shared seed or world-rule set |

## Four core layers

These mirror how a procedural world generates terrain, biomes, flora, and rules without breaking.

### 1. Seed and context anchoring

Every query or session gets a seed, or derives one from the prompt and constraints. The same seed and rule version reproduce the same reasoning path. Shifting the seed explores alternative angles or hypotheses.

### 2. Layered generative rules

Rules stand in place of a frozen weight store.

- **Base layer (physics / logic rules).** Formal constraints, causality, math, and consistency checks. Analogous to planetary terrain rules.
- **Domain layer (biomes).** Specialized rule packs for coding, biology, law, or creative writing that activate based on context.
- **Detail layer (flora and fauna).** Specific idioms, examples, metaphors, and edge cases synthesized on the fly rather than retrieved verbatim.

### 3. Constraint solvers and co-occurrence filters

In *No Man's Sky*, rules prevent a planet from spawning contradictory features that break immersion. In procedural AI, semantic and logical constraint solvers prune contradictions mid-generation, keeping an argument internally consistent without a massive statistical prior.

### 4. On-demand expansion (level of detail)

A game renders distant stars coarsely and nearby rocks in high detail. Procedural AI sketches a high-level outline first and procedurally expands sub-steps, proofs, or counterarguments when zoomed in on.

## Where it shines and where it hits walls

**Strengths.** Radical parameter efficiency. Transparent and inspectable rules. Strong structural consistency on constrained problems. Combinatorial novelty without memorizing training data.

**Limitations.** Natural language and open-ended human nuance are messy. Human common sense and cultural context resist clean hand-crafted rule sets, unlike terrain heightmaps or alien creature parts. Pure procedural rules without learned statistical intuition often feel rigid, brittle, or overly literal unless paired with learned components.

## Mathematics first

The first rigorous layer is the integer ring. Equality, congruence, and the ring laws are the ones Lean 4.36, Isabelle2025-2, and Coq's ZArith already use for the integers. Closed rationals are the next layer: a reduced fraction with a positive denominator. The continuum after that is the Cauchy quotient of those rationals: constant sequences, and positive square-root sequences with a checked modulus. A finite set is an enumeration of those reals. The least upper bound of a nonempty finite set is its maximum. A bounded quantifier checks a predicate at each member, and `complete` states that least upper bound. Separation `{x in S. P x}` keeps the members that satisfy the predicate, and `{x. x = a}` is the singleton of a closed term. An order ray is in the kernel: `{x. x <= a}` is the reals at most that bound, `{x. a <= x}` is the reals at least that bound, and `{x. x = x}` is the set of every real. The least upper bound of a down-ray is the bound it already contains. The least upper bound of `{x. x < a}` is that same bound, and the bound is not a member: the kernel builds it by the Archimedean bisection. A proper overlap of a lower ray and an upper ray is a two-sided interval, and its supremum is the upper bound. A closed upper end contains that bound. An open upper end is built by the same bisection. A conjunction of two comparisons is their intersection. The complement of an order ray is the opposite ray. A disjunction of two closed equalities is their union. A connective the kernel cannot settle stays outside this rule. A nested radical of one square-free integer is a tower. `sqrt(sqrt(2))` is that fourth root, and `sqrt(3 + 2*sqrt(2))` is `1 + sqrt(2)`. `sqrt(2 + sqrt(2))` is `sqrt(2 + sqrt(2))` by `real_sqrt_unique`. `sqrt(sqrt(2) + sqrt(3))` is `1/2 * sqrt(-2 + 2*sqrt(3)) + 1/2 * sqrt(2 + 2*sqrt(3))` by the same rule. A sum of two different square roots stays that sum. `sqrt(sqrt(2) + sqrt(5))` is `sqrt(sqrt(2) + sqrt(5))` by the same rule, and its square is `sqrt(2) + sqrt(5)`. `sqrt(sqrt(2 + sqrt(2)))` is `sqrt(sqrt(2 + sqrt(2)))` by the same rule, and its square is `sqrt(2 + sqrt(2))`. Its inverse is `sqrt(sqrt(20 + 14 * sqrt(2))) - 1/2 * sqrt(2 * sqrt(20 + 14 * sqrt(2)))`. `sqrt(sqrt(sqrt(2) + sqrt(5)))` is `sqrt(sqrt(sqrt(2) + sqrt(5)))` by the same rule, and its square is `sqrt(sqrt(2) + sqrt(5))`. Its inverse is `1/3 * sqrt(3 * sqrt(-3 * sqrt(2) + 3 * sqrt(5)))`. `sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))` is `sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))` by the same rule, and its square is `sqrt(sqrt(sqrt(2) + sqrt(5)))`. Its inverse is `1/3 * sqrt(3 * sqrt(3 * sqrt(-3 * sqrt(2) + 3 * sqrt(5))))`. `sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))` is `sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))` by the same rule, and its square is `sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))`. Its inverse is `1/3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(-3 * sqrt(2) + 3 * sqrt(5)))))`. `sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))` is `sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))` by the same rule, and its square is `sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))`. Its inverse is `1/3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(-3 * sqrt(2) + 3 * sqrt(5))))))`. `sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))` is `sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))` by the same rule, and its square is `sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))`. Its inverse is `1/3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(3 * sqrt(-3 * sqrt(2) + 3 * sqrt(5)))))))`. `sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5))))))))` is that nested radical by `real_sqrt_unique`, and its square is `sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(sqrt(2) + sqrt(5)))))))`. Every further finite square root of this radical is the same rule, one square root deeper. Every further finite square root of one positive binomial nest is the same nested radical, one square root deeper. `sqrt(sqrt(sqrt(2 + sqrt(2))))` is that nested radical by `real_sqrt_unique`, and its square is `sqrt(sqrt(2 + sqrt(2)))`. The inverse of `sqrt(sqrt(2) + sqrt(3))` is `-1/2 * sqrt(-2 + 2 * sqrt(3)) + 1/2 * sqrt(2 + 2 * sqrt(3))`. Division by another element of this span multiplies by a checked inverse. A product of radicals at different levels is one integer to the power `1/2^k`. `sqrt(2)*sqrt(sqrt(3))` is `sqrt(sqrt(12))`. Division by zero stays open. A result is a theorem built by those rules. A measurement can enter only as a sourced observable, `name=value@source`, and later science rules will have to start from those anchors.

The reaching goal is [GOAL.md](GOAL.md). A checked theorem is how a claim settles. Incoming information is linked under the same discipline, toward a theory of reality treated as source code. That theory is not in this folder.

## Working stance

- The store is rules, seeds, grammars, and synthesis functions.
- Learned modules are allowed where intuition and representation need them.
- A repeated seed plus a named rule version must be able to replay the same path.
- A rule clash is a recorded dead end, not a smoothed-over answer.
- Detail is expanded only when something asks to zoom in.
