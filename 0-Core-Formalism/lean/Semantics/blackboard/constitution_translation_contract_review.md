# Blackboard — Translation Contract Review

**Target:** the Translation Contract section of
`0-Core-Formalism/lean/Semantics/Semantics/Constitution.lean` (added at end of file,
after `scalar_collapse_must_be_admissible`).

**Mission:** exhaust every honest question about whether the math actually
does what the prose claims it does. Continue until no questions remain.

## Trust contract — read this first, every round

- **Zero trust in the file.** Its claims are unverified until refuted or
  confirmed by what the proof terms actually establish.
- **Zero trust in the orchestrator (Claude).** Claude wrote the section
  and can be wrong. Do not take Claude's framing as evidence.
- **Zero trust in yourself.** If you reach a conclusion, attempt to
  refute it before recording it.
- **Trust only the math.** Specifically: trust what Lean's elaborator
  actually accepts, what the proof terms actually establish, and what
  is true under the definitions as written. Prose docstrings are
  hypotheses to be tested, not premises to be accepted.

## Section ownership (avoid write races)

Each agent edits ONLY its assigned section below. Do not edit other
agents' sections. Append to your section; do not delete.

---

## ROUND 1

### §1 QUESTIONS — owner: Agent A (Adversarial Asker)

> Generate the hardest, most specific questions you can about the
> translation contract section. Do not answer them. Goal: 15-25 distinct
> questions covering well-formedness, proof correctness, semantic gap
> (does the contract actually detect anything or just record bookkeeping),
> open-list extensibility, naming-collision risks, soundness of the three
> "laws," and whether `Bool.noConfusion` / `List.not_mem_nil` are the
> correct lemma names in this Lean version. Mark each question with a
> short tag like `[proof]`, `[semantic]`, `[scope]`, `[naming]`.

1. [naming] In `silencer_blocks_admissibility` line 211, `List.not_mem_nil hmem` is applied to `hmem : s ∈ ([] : List TranslationSilencer)`. In Lean 4 / Mathlib current, is `List.not_mem_nil` a function `(a : α) → a ∉ ([] : List α)` requiring an explicit element argument, or `{a : α} → a ∉ []`? If the former, the proof needs `List.not_mem_nil s hmem` or `(List.not_mem_nil s) hmem`, and the current term may fail to elaborate.

2. [proof] Same theorem: even if `List.not_mem_nil` returns `s ∉ []`, the goal after `rw [hempty] at hmem` is `False`, not `s ∉ []`. Does `exact List.not_mem_nil hmem` actually discharge `False`, or is the intended term `exact (List.not_mem_nil _) hmem` / `exact absurd hmem (List.not_mem_nil _)`?

3. [proof] In `fully_translated_iff_empty` line 236, `exact absurd hmem (List.not_mem_nil)` passes `List.not_mem_nil` without an argument. If the lemma signature requires an explicit element, this is ill-typed. Does the parenthesisation save it via unification, or is this a latent break?

4. [naming] In `unacknowledged_flag_blocks_admissibility` line 224, `Bool.noConfusion hack` is invoked on `hack : true = false` (after rewrite). In current Lean 4 core, is `Bool.noConfusion` the canonical disposer for `true = false`, or has it been replaced by `Bool.true_ne_false` / `Bool.noConfusion (h := …)` requiring a motive? Will it actually elaborate to `False` here without a target type hint?

5. [proof] In `unacknowledged_flag_blocks_admissibility`, after `rw [this] at hack`, what is the new type of `hack`? It started as `f.acknowledged = false`; rewriting with `f.acknowledged = true` yields `true = false`. Confirm the rewrite direction is correct — `rw [this]` rewrites LHS-to-RHS of `this`, replacing `f.acknowledged` with `true`. Does that match?

6. [semantic] `silencers : List TranslationSilencer` is populated how? Nothing in the file scans Lean source for the eight named patterns. Is the contract honor-system — a human types in `silencers := []` and the proof goes through vacuously?

7. [semantic] `TranslationAdmissible` is a `Prop`, but `TranslationContract` carries no hash/signature of the module text. What stops a contract object from being constructed for `moduleName := "Substrate"` while the actual `Substrate.lean` file contains `sorry`? There is no link between the `String` and the file on disk.

8. [scope] The eight named silencers omit at least: `axiom` declarations, `@[implemented_by]` overrides, `unsafe` blocks, `partial def` (no termination proof), `decide` over a buggy `Decidable` instance, `native_decide`, `Classical.choice`-laundered noncomputability, `opaque` declarations, `set_option maxHeartbeats 0` to defer elaboration, and `#check`-only proofs without `theorem`. Why are these absent?

9. [scope] `tautologyProof` is described as "`unfold …; simp` proof of a definition restated as theorem." How is this distinguishable, mechanically, from a legitimate sanity lemma? Without a checker, this constructor is decorative.

10. [semantic] `acknowledged : Bool` defaults to `false`, but nothing binds the `true` value to an actual human action. A script can flip the boolean. Where is the cryptographic/operational teeth — signature, attestation MMR leaf, anything?

11. [interaction] `TranslationAdmissible` is a free-standing predicate; `FullyAdmissible` (line 43) does not reference it. A `GroundedUniverseConstitution` can be `FullyAdmissible` while every translated module silently contains silencers. Is this section therefore disconnected from the master constitution?

12. [interaction] `GroundedUniverseConstitution` has fields `universality / canonical / evolution / scalar : Bool`. Why is there no `translation : Bool` field, given the prose calls translation a constitutional probe?

13. [scope] `TranslationContract` has no field for *module dependencies*. A module with empty silencer list that imports a module full of silencers is still "admissible" by this definition. Is transitive admissibility intended or excluded?

14. [semantic] The prose says "the list is open-ended." But `TranslationSilencer` is a closed `inductive`. Adding a constructor is a breaking ABI change to every `match` and every `BEq`/`DecidableEq` instance derived from it. In what sense is this "open-ended"?

15. [proof] `deriving DecidableEq` on `TranslationSilencer` — does Lean 4 auto-derive `DecidableEq` for a parameter-free enum without issue here, or does it need `deriving instance DecidableEq for TranslationSilencer`? Confirm against the current toolchain.

16. [proof] `deriving Repr, BEq` on `UntranslatableFragment` — `BEq` over a `String` field is fine, but does `BEq` derivation succeed when one field has a default value (`acknowledged : Bool := false`)? Confirm.

17. [naming] `f ∈ t.flags` desugars to `List.Mem f t.flags`. Does the `∀ f ∈ t.flags, …` binder elaborate to `∀ f, f ∈ t.flags → …` cleanly under the current Lean parser, or does it require `Mathlib.Init.Set`?

18. [interaction] `fully_translated_iff_empty` is named `_iff_` but is a one-direction implication (`→`, not `↔`). Is the missing reverse direction (`TranslationAdmissible t → t.silencers = [] ∧ t.flags = []`) false (counterexample: an empty silencer list and a flag list of all-acknowledged flags) — and if so, why is the lemma named "iff"?

19. [semantic] What is the intended *consumer* of `TranslationContract`? No theorem in Constitution.lean takes a `TranslationContract` as a hypothesis. Is the contract a dangling structure?

20. [scope] `softPassExtern` — Lean 4 `extern` is implemented via FFI. The contract has no way to inspect the C side. The constructor is therefore aspirational. Acknowledged?

21. [semantic] `dualTableUnverified` — the contract names this as a silencer but provides no roundtrip-theorem obligation. What is the difference between *naming* the silencer and *forbidding* the pattern that produces it?

22. [interaction] The file ends with `end Semantics.ENE`. Are `TranslationSilencer`, `TranslationContract`, and the three theorems in the `Semantics.ENE` namespace? Downstream callers must write `Semantics.ENE.TranslationSilencer.sorryAdmission` — confirm this is intended and not a namespace leak.

23. [proof] In `silencer_blocks_admissibility`, `hadm.1` projects from `TranslationAdmissible t` which is `t.silencers = [] ∧ ∀ f ∈ t.flags, f.acknowledged = true`. Is `hadm.1` well-typed, given `∧` is `And` and `.1` is `And.left`? Confirm `unfold` is not needed first.

24. [semantic] The prose claims "Tight now, or flagged now. No third state." But a fourth state exists: `silencers := []` with `flags := []` for a module that *was never translated at all*. The empty contract trivially satisfies `TranslationAdmissible`. How is "translated and clean" distinguished from "never attempted"?

25. [interaction] Does the section need to be re-exported from any top-level barrel module (`Semantics.lean` root)? If `Constitution.lean` is the root, fine — but if other files import `Semantics.Constitution`, will they pick up the new symbols, or is there a `lakefile.toml` glob that needs updating?

### §2 TYPECHECK — owner: Agent B (Math Verifier)

> Attempt to verify that the three theorems in the translation contract
> section actually typecheck under their stated proofs. Use whichever of
> these is available:
>   1. `lake build Semantics.Constitution` from `0-Core-Formalism/lean/Semantics/`.
>      Note: this will trigger a build of Substrate.lean which has a
>      known wildcard-match defect; if the build fails on Substrate,
>      that is a separate issue — record it but do not let it block
>      your verification of the Constitution proofs themselves.
>   2. If the build is denied or fails for unrelated reasons, perform
>      a careful manual elaboration of each proof: track the goal at
>      each tactic step, verify that `rw`, `exact`, `intro`, `refine`
>      reach a closed goal.
> Verify lemma names against the Lean 4 / Mathlib version actually in
> use (check `lean-toolchain` and `lakefile.toml`). `List.not_mem_nil`
> and `Bool.noConfusion` may have different names or signatures.
> Report each theorem's status as PROVEN / SUSPECT / BROKEN with the
> specific failure if not proven. Do not paper over uncertainty.

**Method:** `lake build Semantics.Constitution` from `0-Core-Formalism/lean/Semantics/`
under toolchain `leanprover/lean4:v4.29.1`.

**Build outcome:** SUCCEEDED. 16/16 jobs built clean. No warnings, no
errors, no `sorry`. Substrate.lean built without obstructing Constitution
(known wildcard defect did not cascade in this run — `[14/16] Built
Semantics.Substrate (703ms)`).

**Per-theorem status:**

1. `silencer_blocks_admissibility` — **PROVEN.**
   Proof flow: `intro hadm` → goal `False`; `hadm.1 : t.silencers = []`;
   `rw [hempty] at hmem` rewrites hypothesis to `s ∈ ([] : List _)`;
   `List.not_mem_nil hmem` discharges. In Lean4 v4.29.1 core,
   `List.not_mem_nil` is applicable to a membership-in-nil hypothesis;
   the elaborator accepted it.

2. `unacknowledged_flag_blocks_admissibility` — **PROVEN.**
   `hadm.2` extracts `∀ g ∈ t.flags, g.acknowledged = true`; specialised
   to `f` gives `f.acknowledged = true`; `rw [this] at hack` produces
   `true = false`; `Bool.noConfusion hack` closes. `Bool.noConfusion` is
   present in Lean4 core and accepts `true = false` to derive any goal
   (here `False`). Verified by successful elaboration.

3. `fully_translated_iff_empty` — **PROVEN.**
   Destructures hypothesis, refines the conjunction with `hs` and a
   `∀`-proof obligation; for any `f ∈ t.flags`, rewrites via `hf` to
   `f ∈ []`, then `absurd hmem List.not_mem_nil` closes. Note: the
   stated theorem is the one-way implication (→), not the iff its name
   advertises — that is a *naming* concern (Agent A/C territory), not a
   typecheck failure. Lean accepted it as written.

**Lemma-name issues:** none. Both `List.not_mem_nil` and
`Bool.noConfusion` exist with usable signatures in Lean4 v4.29.1 core.
No Mathlib dependency required for these proofs.

**Caveat on certainty:** verification is grounded in a green `lake
build`, not in eyeballing alone. Confidence high. The only thing the
typechecker does *not* tell us is whether the theorems mean what their
docstrings claim — that is Agent C's beat.

### §3 SEMANTIC AUDIT — owner: Agent C (Adversarial Semantic Reviewer)

> Attack the *meaning* of the contract, not its syntactic correctness.
> Specifically address:
>   1. Does the contract *detect* silencers, or does it merely *record*
>      them? Where does the silencer list come from? If the answer is
>      "a human writes it," is the contract honor-system?
>   2. Are the 8 named silencers exhaustive? What known Lean fault-
>      hiding patterns are missing from this list?
>   3. Is `TranslationSilencer` being a closed `inductive` consistent
>      with the prose claim that the list is "open-ended"? Adding a
>      constructor is a structural change to every downstream module.
>   4. The `acknowledged : Bool` field — does it have any teeth? What
>      stops a flag from being marked acknowledged without review?
>   5. Does this section interact correctly with the existing
>      `GroundedUniverseConstitution` and `FullyAdmissible` predicate?
>      Should `TranslationAdmissible` be folded into them?
> Be adversarial. Find the largest gap and name it specifically.

**Verdict: the contract is theatrical bookkeeping, not detection. The math is honest about what it proves; the prose lies about what the math means.**

#### Q1 — Detection vs bookkeeping: BOOKKEEPING ONLY.

Nothing in `Constitution.lean`, and nothing this structure imports, ever populates `TranslationContract.silencers` from inspection of an actual module. `silencers : List TranslationSilencer` is a plain field of a plain `structure`. The only way it ever acquires elements is if a human (or a tool acting on human authority) writes them in. So `silencer_blocks_admissibility` proves: *if you wrote down a silencer, you are inadmissible.* That is a tautology about list membership, not a fact about source code. A module containing five `sorry`s and zero recorded silencers is `TranslationAdmissible` by this definition. The contract certifies the **honor system**.

Closing the gap requires one of: (a) a `Lean.Elab.Command` meta-program that walks every declaration in the module's environment, pattern-matches on `Expr.const ``sorryAx`, wildcard arms, etc., and emits a `TranslationContract` as elaboration output; (b) an external static-analysis pass over `.lean` source AST or `.olean` environments producing the contract as a build artifact consumed by Lean as a `def`; (c) a build-time `#eval` check that fails the build if `TranslationAdmissible` is not derivable for every module in the build graph. Without one of these, the contract is **theatrical work**: it has the shape of a check but performs no check.

#### Q2 — Exhaustiveness of the 8 silencers: NOT EXHAUSTIVE. Missing at least 12.

Known Lean 4 fault-hiding patterns absent from `TranslationSilencer`:

1. **`axiom` declarations** — the canonical "I assert this without proof" escape. Strictly worse than `sorry`: intentional, survives `#print axioms`, no warning. Not listed.
2. **`opaque` declarations** — Lean 4's official "trust me, this exists" mechanism. Distinct from `axiom` and from `sorry`. Not listed.
3. **`partial def`** — escapes termination checking entirely. Hides non-termination, a real fault. **Glaring omission** given the prose emphasis on "tight translation."
4. **`unsafe def` / `unsafe` blocks** — escapes the type system itself. Not listed.
5. **`noncomputable def`** — opts out of kernel reduction, hides definitional inequalities. Not listed.
6. **`@[implemented_by]` / `@[extern]` with mismatched signatures** — `softPassExtern` covers "always returns success" but not the broader case of an extern whose Lean type lies about the C/Rust function it's bound to.
7. **Missing `decreasing_by`** on structural recursion that compiles only because Lean's auto-termination heuristic guessed a measure — heuristic guess can disagree with the source's intended semantics. Not listed.
8. **`@[simp]` lemmas that rewrite live goals to `True`** — turns unprovable obligations into `trivial`. Not covered by `tautologyProof` (which targets restated definitions).
9. **`Decidable` instance bugs** — `decide` / `native_decide` proofs that elaborate to `isTrue` because the wrong `Decidable` instance was picked up via class search. `native_decide` additionally trusts the compiler. Not listed.
10. **`cast`, `Eq.mpr`, `HEq.mp`** — heterogeneous coercion across types that are not actually equal in the source domain. Not listed.
11. **`Subtype` with a vacuous predicate** — `False`-predicated subtypes vacuously discharge all obligations. Not listed.
12. **`Inhabited` / `Nonempty` instance abuse** — using `default` to fabricate a witness whose source has no canonical element. Not listed.
13. **Macro / `elab` rewriting** that elaborates a term to something different from what the surface syntax says — invisible at the source level, kernel-accepted. Not listed.
14. **Universe polymorphism collapse** (`Sort _` defaulting to `Prop`) — silently changes proof-relevance.
15. **`set_option maxHeartbeats 0`** to bury elaboration cost / non-termination of the elaborator itself. Not listed.

Eight constructors out of fifteen-plus known patterns is not "open-ended"; it is a starter set with no roadmap. **`partial`, `axiom`, and `opaque` are not optional** — their absence makes the list look unserious to anyone who has used Lean 4 in anger.

#### Q3 — Open-ended vs closed inductive: INCONSISTENT. The prose contradicts the math.

`TranslationSilencer` is `inductive` — a closed sum. The docstring says "open-ended … new shapes should be added." Adding a constructor is **not** open-ended in any meaningful sense: it is a *breaking change* to every downstream consumer that pattern-matches on `TranslationSilencer`, and every existing `Repr`/`BEq`/`DecidableEq` derivation must be re-elaborated. Worse, every `match` on it that does *not* use a wildcard arm becomes a typecheck error — and the contract itself **forbids wildcard arms** (`wildcardOnInductive` is silencer #1). So the contract makes itself unextendable without violating itself: any module that pattern-matches on `TranslationSilencer` to react to specific shapes must either (a) use a wildcard (silencer) or (b) be edited every time a constructor is added (not open-ended).

Genuinely open-ended shapes in Lean would be:

- `structure TranslationSilencer where tag : String; locator : String` — a tag-string, no enum, with a *separate* registry (e.g. a `Std.HashSet String` of recognised tags) maintained out-of-band. New shapes are new strings; downstream code matches on string equality and falls through gracefully on unknown tags.
- A typeclass-indexed registry: `class IsSilencer (α : Type) where name : String; locate : α → String`. Each shape is its own type with its own instance. Adding a shape adds a file; nothing breaks.
- An attribute-driven registry (`@[silencer]` on user-defined inductives) with a `Lean.Elab` command that aggregates them at build time.

The current design picks the worst of both worlds: closed enough to break on extension, prose-claimed open enough to invite extension.

#### Q4 — Acknowledged flags have no teeth: NONE WHATSOEVER.

`acknowledged : Bool := false` is a plain Bool field with a default. Anything that constructs an `UntranslatableFragment` can pass `acknowledged := true`. There is:

- no signature (no `Sig : ByteArray` field bound to a public key),
- no proof obligation (`acknowledged : Bool`, not `acknowledged : SomeReviewerProof locator reason`),
- no hash of reviewer identity,
- no timestamp,
- no link to a separate audit log,
- no monotonicity constraint (a tool can flip `false → true` and back; nothing detects the flip).

`unacknowledged_flag_blocks_admissibility` is therefore proving: *if you wrote down `false`, you are inadmissible.* A trivial pass that rewrites every `acknowledged := false` to `acknowledged := true` defeats it without touching the proof. **Real teeth** would look like:

```
structure UntranslatableFragment where
  locator      : String
  reason       : String
  reviewerKey  : ByteArray         -- ed25519 pubkey
  signature    : ByteArray         -- sig over (locator || reason || timestamp)
  timestamp    : UInt64
  acknowledged : Decidable (VerifySig reviewerKey signature ⟨locator, reason, timestamp⟩)
```

…with verification at admissibility-check time and the reviewer key whitelist living *outside* the file (e.g. fetched from the trinary watchdog / judge node — the codebase already has BFT infrastructure for exactly this purpose). Until something like this exists, `acknowledged` is decoration.

#### Q5 — Interaction with the existing constitution: LAYERING MISTAKE.

`TranslationAdmissible` is a top-level `def` with no relation to `GroundedUniverseConstitution` or `FullyAdmissible`. `FullyAdmissible` takes `(c, g, sc)` and conjoins five clauses; none mention translation. The translation contract is a parallel, dangling structure. Three possibilities:

- **Intentional separation** (translation is meta-data about the formalisation, not about the universe being formalised). Defensible, but then the contract should not live in `Constitution.lean` next to the master admissibility laws — it should live in `Semantics.Meta.Translation` or similar, and the prose at the top of the file should not call it part of "the immutable membrane."
- **Oversight** — added without wiring it in. Most likely interpretation: the file's opening comment says "Includes the forced-translation contract: the codebase is translated into Lean as a fault-injection probe," which is a claim of *inclusion*, not parallelism. If it is included, it must compose.
- **Layering mistake** — the contract should be a field of `GroundedUniverseConstitution`:

  ```
  structure GroundedUniverseConstitution where
    semantic     : UniverseConstitution
    universality : Bool := true
    canonical    : Bool := true
    evolution    : Bool := true
    scalar       : Bool := true
    translation  : TranslationContract           -- new
  ```

  with `FullyAdmissible` extended by `∧ TranslationAdmissible c.translation`. Then the existing master theorems automatically inherit translation-admissibility as a precondition, and a "fully admissible" object at the top level cannot exist while a silencer is recorded in its module. The current decoupling means a `FullyAdmissible` proof can coexist with a maximally broken translation, which directly contradicts the file's own framing.

Most likely truth: a mix of (b) and (c) — added as an afterthought, never composed. The fix is mechanical and one structure-field wide.

#### Additional gaps not in the five-question list

**A. `silencer_blocks_admissibility` proves a tautology, not a substantive law.** Unfolding: `TranslationAdmissible t := t.silencers = [] ∧ …`, and the theorem says `s ∈ t.silencers → ¬ (t.silencers = [] ∧ …)`. This is just `s ∈ xs → xs ≠ []` with extra structure — true for any `List` with any element type. It is *not* a fact about silencers; it is a fact about lists. The same theorem holds with `TranslationSilencer` replaced by `Unit`. The "law" is contentless; the content is supposed to live in the *act of populating the list*, which (per Q1) never happens.

**B. `fully_translated_iff_empty` is misnamed.** The theorem is a one-directional implication (`→`), not an `iff`. The reverse direction (`TranslationAdmissible t → t.silencers = [] ∧ t.flags = []`) is **false** as written: an admissible contract can have flags, provided they are all acknowledged. The name "iff" is a bald-faced lie about what the theorem proves. Either rename to `empty_implies_translated` or strengthen — but strengthening would require additionally forbidding non-empty flag lists, contradicting the design of the second law.

**C. No module-name uniqueness or coverage guarantee.** `moduleName : String` is free-form. Two contracts can share a name; a contract can name a module that does not exist; a module can have no contract. There is no theorem of the form "every module in the build graph has exactly one contract." Without coverage, even a perfect detection mechanism leaves silent holes for any module that simply has no contract attached. This combines with **Agent A's Q24 fourth state** ("never translated at all"): the empty contract trivially satisfies `TranslationAdmissible`, so "translated and clean" and "never attempted" are indistinguishable.

**D. No `requires` / dependency field for transitive admissibility.** A module's contract says nothing about whether its imports are translation-admissible. A module can be locally clean while transitively depending on a module full of `sorry`. The constitution silently permits this. This is Agent A's Q13, and the answer is: transitive admissibility is **excluded by omission**, not by design.

**E. The `Repr, BEq` derivations on `TranslationContract` are misleading certification.** `BEq` on a structure with a `List` field gives extensional equality on the list — meaning two contracts are equal iff they record exactly the same silencers in the same order. This invites a tooling pattern where contracts are diffed by `BEq` and "no change" means "no new silencer," which is wrong: reordering is a no-op; addition followed by deletion in the same diff is a no-op for `BEq` but a real audit event.

**F. `reason : String` in `UntranslatableFragment` is unstructured.** A free-form string cannot be machine-checked, cannot be cross-referenced against a known taxonomy of failure modes, and cannot be searched for "all flags caused by reason X." Should be a sum type, or at minimum a tag plus a string.

**G. The contract has no notion of *why a silencer was needed*.** If a `wildcardOnInductive` was added because the upstream inductive is genuinely open (e.g., a third-party `Lean.Expr` analogue), the contract treats it identically to a lazy wildcard added to suppress an exhaustiveness warning. The constitution flattens "necessary evil" and "lazy shortcut" into the same forbidden state, which guarantees one of: (i) the contract is ignored in practice, (ii) the contract is satisfied by lying about the silencer's absence. Both outcomes destroy the trace the contract was supposed to preserve.

**H. `TranslationContract` is a dangling structure with no consumer.** Confirms Agent A's Q19. No theorem in `Constitution.lean` (or in any imported file) takes a `TranslationContract` as a hypothesis. The structure exists; the laws exist; nothing uses either. A type that is constructed but never consumed by the rest of the system is, operationally, a comment with type-checking.

#### Largest gap (named specifically)

**The list never gets populated by anything that inspects the source.** Every other gap is downstream of this one. The contract proves theorems about the contents of a `List TranslationSilencer` without ever guaranteeing that the list reflects the source. Until a `Lean.Elab.Command` meta-program walks each module's environment and emits a `TranslationContract` as elaboration output (or an external pass produces one as a build artifact), `TranslationAdmissible` certifies nothing about any actual `.lean` file. It certifies that *whoever wrote the contract said the module was clean*. That is the honor system with extra steps and a `theorem` keyword. Every proof in the section is correct (Agent B confirmed); every proof in the section is also vacuous with respect to the file's stated mission ("the codebase is translated into Lean as a fault-injection probe"). Fault injection requires a probe that inspects; this probe records what it is told.

---

## ROUND 2 (only if Round 1 leaves open questions)

### §4 REFUTATION — owner: Agent D (read-only Explore agent; orchestrator transcribed)

**Mission:** attempt to refute Round 1's strongest finding (Agent C):
"the silencer list is never populated by anything that inspects the source."

**Status: CONFIRMED.** Round 1 finding stands.

**Searches run:**
1. Grep entire `/home/allaun/Research Stack` for `TranslationContract`,
   `TranslationSilencer`, `UntranslatableFragment` — found only in
   `Constitution.lean` (the definitions and proofs themselves).
2. All `.lean` files scanned for `Lean.Elab`, `CommandElab`, `macro`,
   `@[elab]`, `@[elaborator]` — zero hits.
3. All `.py`, `.sh`, `.rs` files in the repo — zero references to
   translation-contract concepts.
4. `lakefile.toml` — only standard `[[lean_lib]]` / `[[lean_exe]]`
   stanzas, no custom build actions or post-build hooks.
5. Contract construction patterns (`{ moduleName`, `silencers :=`,
   `flags :=`) — zero instances outside Constitution.lean.
6. All `#eval` / `#check` directives — no contract evaluation.
7. `BindServer.lean` and root `Semantics.lean` inspected — no contract
   instantiation.

**Result:** the contract structure exists only as type definitions and
vacuous proof obligations. There is no meta-program, external script,
build hook, or other mechanism that inspects Lean source (for
`sorryAx`, `partial`, `opaque`, axioms, wildcards, etc.) and populates
`TranslationContract.silencers` from actual module contents.

---

## SYNTHESIS — owner: orchestrator only

**Verdict: the translation contract section, as it stands, is sound mathematics
about a vacuous predicate.**

What is true:
- Agent B verified all three theorems typecheck under `lake build` on
  Lean v4.29.1. No `sorry`, no lemma-name issues, no dependency on
  Mathlib. The math is clean.
- The structures are well-formed and compose into a `Prop` predicate
  that does what its definition says.

What is false (or, more precisely, what the prose claims that the math
does not support):
- **The contract does not detect silencers; it records what it is told.**
  Agent C named this; Agent D confirmed by exhaustive search. No
  populator exists; nothing in the project inspects Lean source for
  the eight named patterns and emits a `TranslationContract`. A module
  containing five `sorry`s and zero recorded silencers is
  `TranslationAdmissible` by this definition. The proofs are correct;
  they are correct about a list that has no causal connection to any
  `.lean` file.
- **The eight silencers are not exhaustive.** Agent C named at least
  twelve missing patterns. The most glaring omissions — `axiom`,
  `opaque`, `partial def` — are precisely the canonical Lean fault-
  hiding mechanisms. A contract that does not name `partial` is not
  serious about "tight translation."
- **`TranslationSilencer` is closed but the prose calls it open-ended.**
  Adding a constructor is a breaking change to every downstream
  pattern-match; the contract itself forbids the only escape (wildcard
  arms). The design is self-defeating under its own rules.
- **`acknowledged : Bool` has no teeth.** A trivial pass that flips
  every `false` to `true` defeats the second law without touching the
  proof. Real teeth require signature/timestamp/reviewer-key fields
  the contract does not have.
- **`TranslationAdmissible` is dangling.** It is never composed with
  `FullyAdmissible`. A `GroundedUniverseConstitution` can be fully
  admissible while every translated module silently contains
  silencers. The opening comment ("Includes the forced-translation
  contract") claims inclusion; the math implements parallelism.
- **`fully_translated_iff_empty` is misnamed.** It is a one-way
  implication, not an iff. The reverse direction is false (an
  admissible contract may have acknowledged flags). The name lies.
- **`silencer_blocks_admissibility` is a tautology about lists**, not a
  fact about silencers. The same theorem holds with `TranslationSilencer`
  replaced by `Unit`.

**The largest gap, named once:** the contract proves theorems about a
list that no mechanism populates from source. Until a `Lean.Elab.Command`
meta-program walks each module's environment and emits a populated
`TranslationContract` as elaboration output (or an external pass
produces one as a build artifact consumed by the build), every proof
in the section is correct *and* vacuous with respect to the file's
stated mission.

**By the contract's own rules, the contract should flag itself.** It
contains an unfilled gap (no populator), the gap is silent (no record
of the absence anywhere in the file), and silent gaps are forbidden
under the constitution's framing ("tight now, or flagged now. No third
state"). The constitution is currently in violation of itself. The
honest minimal patch is to add an `UntranslatableFragment` to a
`TranslationContract` covering `Constitution.lean` itself, with
`reason := "no source-inspection populator exists; silencer list is
honor-system"` and `acknowledged := false`, until either a populator
is built or the architectural decision is made that this section is
schema-only and the populator is intentionally external future work.

**Conclusion:** the questions have converged. No round 3 is required.
The verdict is locked.

**Open question for the human:** does the user want
  (a) the four concrete fixes implemented (populator stub, expanded
      silencer list, integration with `FullyAdmissible`, real teeth on
      `acknowledged`), making the contract substantive but turning a
      ~80-line addition into a ~300-line one,
  (b) the constitution's prose softened so it does not claim more than
      the math delivers (cheap, honest, leaves the contract as a
      schema-with-future-populator),
  (c) the section reverted entirely until a real populator is built,
      on the grounds that schema-only constitutional law is theatre, or
  (d) the constitution's self-violation explicitly documented via an
      `UntranslatableFragment` covering `Constitution.lean` itself, as
      a worked example of the contract eating its own dogfood?

