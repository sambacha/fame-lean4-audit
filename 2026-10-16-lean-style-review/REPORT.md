# Lean 4 proof-style review against the writing-lean-proofs guide — 2026-10-16

This document stands on its own. It reviews the whole Lean code base of this repository against
five documents of the Lean proof-writing guide:

* `SKILL.md`
* `references/library-design.md`
* `references/proof-style.md`
* `references/performance.md`
* `references/tactics.md`

It reports every finding, says which rule each one falls under, sets out a phased plan for
remediation and refactoring, and records what changed between the first and the second review
pass (§8).

---

## 0. Scope, inputs and ground rules

### 0.1 Where the guide is in this repository

The request names `rules/writing-lean-proofs/SKILL.md` and `rules/writing-lean-proofs/references/`.
**There is no `rules/` directory in the repository.** The same five files are kept verbatim under
`docs/specs/lean-guide/` (`SKILL.md` next to a `references/` folder, so the relative links work).
`docs/standards/LEAN_GUIDE.md` adopts them as the project's authoritative Lean rules.

Their SHA-256 digests were recomputed for this review, and all five match the table in
`LEAN_GUIDE.md`:

| File | SHA-256 (recomputed 2026-10-16) |
|---|---|
| `SKILL.md` | `fb2ad9c463ac5185a014892ce33202460b3423d64405024b95b534f0d3b4d3e0` |
| `references/library-design.md` | `23310d7a0f1d7aef86d1c4e333ec97b5569b344bf9f26c61e958ca00d0f23f99` |
| `references/proof-style.md` | `d631ddb9dc607229e025a53807e8dca63a9865f59e2f67b265d36888a0c39424` |
| `references/performance.md` | `f108a3e8dc1882684759ddbbad0ca5a521c84a80493246256acc82d8250e395b` |
| `references/tactics.md` | `68786c8dc7dc4ad0f0743717c72472efb6179d3f78cbbfc16a980e96a6d8db0e` |

The review was therefore carried out against `docs/specs/lean-guide/`. Whether to *also* keep a
copy at `rules/writing-lean-proofs/` is listed as an open decision (D-1 in §7). Two verbatim copies
would need two hash checks.

### 0.2 How this review relates to the repository's own standards

* `SKILL.md` ("When NOT to Use") tells a verified-software project that has its own house style
  to check that style first and defer to it. This repository has one:
  `docs/standards/LEAN_PROOF_STYLE.md` (rules R1–R27 and the recorded departures),
  `LEAN_GUIDE.md` (the precedence rules) and `LEAN_LINT_POLICY.md`.
* `LEAN_GUIDE.md` §"What authoritative means" sets the precedence. The guide is the rule. A
  departure counts only if it is recorded in `LEAN_PROOF_STYLE.md` with a reason. An unrecorded
  habit of the tree is "the thing to change, or to record".
* This review classifies every finding against that precedence. A finding is one of:
  * **conformant** (C);
  * **covered by a recorded departure** (D), with the departure named;
  * **non-conformant and unrecorded** (N);
  * **informational** (I): the guide states a preference, not a rule, or the observation is a
    measurement with no verdict.
* Two earlier audits exist: `audit/2026-10-14-lean-proof-style/REPORT.md` and
  `audit/2026-10-15-lean-proof-style/REPORT.md`. This review re-measures what they measured, says
  where the figures have moved, and goes further in three places:
  * the goal-state linters were run over **every** library module, not only the edited ones;
  * the load-bearing proofs were read by hand;
  * `library-design.md`, `performance.md` and `tactics.md` were reviewed, which the earlier audits
    covered only in part.

### 0.3 Severity scale

| Severity | Meaning |
|---|---|
| **High** | Affects what a theorem *claims*, or affects the maintainability of a load-bearing proof family as a whole (a refactor of one definition breaks dozens of proofs at once). |
| **Medium** | A rule broken in a way that makes proofs harder to read or repair, or a check that can silently pass. |
| **Low** | A local deviation with limited blast radius, or a mechanical fix. |
| **Info** | A measurement, a positive exemplar, or a guide preference with no verdict. |

---

## 1. Method, step by step

1. **Inventory.** All 1,088 tracked `.lean` files (333,803 lines) were split into 31,768 top-level
   declarations: 14,068 theorems/lemmas, 14,713 `def`, 736 `abbrev`, 1,052 `structure`,
   494 `inductive`, 565 `instance`, 133 `example` and 7 `class`
   (`tools/style_metrics.py` → `data/decls.tsv`).
2. **Build.** A full `lake build` was run (9,088 jobs, exit 0).
3. **Kernel check of the load-bearing theorems.** `#print axioms` was run on 14 load-bearing
   theorems (`tools/AxiomSpotCheck.lean.txt`).
4. **Goal-state linters over the whole tree.** All 1,054 library modules were re-elaborated with
   eight options (`tools/run_linters.sh` → `data/linter_sites.tsv`, `data/linter_rc.list`):
   * `linter.flexible`, `linter.style.multiGoal`, `linter.style.show` and
     `linter.unnecessarySimpa`;
   * `linter.style.missingEnd`, `linter.style.openClassical`, `linter.unusedDecidableInType` and
     `linter.unusedFintypeInType` (the guide's reusable-library profile).

   Every module elaborated (exit 0 for all 1,054). Before the run was trusted, a known-trigger
   fixture (`tools/LinterTriggerFixture.lean.txt`) confirmed that each linter fires under the same
   flags. The guide requires this check: "a check that can't fail proves nothing".
5. **Text measurements.**
   * The project's own `scripts/audit_lean_proof_style.py`.
   * Five new measurement scripts written for this review:
     * `tools/style_metrics.py`: per-declaration tactic and naming counts;
     * `tools/tactic_heads.py`: counts tactics only in tactic position, so a variable named
       `delta` or a function named `admit` is not counted as a tactic;
     * `tools/downstream_unfold.py`: classifies each `unfold` target as same-file or downstream;
     * `tools/duplicate_statements.py`: theorems whose statement text occurs in more than one file;
     * a reflexive-statement scan (`A = A`), whose results are listed in Appendix B.
   * Comments and strings are removed before matching in every script.
6. **Selecting what to read by hand** (§3). Three overlapping criteria:
   * **load-bearing**: the headline correctness theorem of each subsystem;
   * **cross-cutting**: lemmas or APIs that many files use or repeat;
   * **non-trivial**: theorems of 50 lines or more (85 of them), plus every metaprogram (macro,
     `elab`, attribute).

   The 23 items are listed in §3, each with its verdict.
7. **Checks by experiment** where reading alone could not settle a question. Each check is cited
   where it is used:
   * removing `set_option hygiene false` from `frame_tac`;
   * the dotted-identifier blind spot of `linter.flexible`;
   * the claim that `wset` equals `Function.update`;
   * a generic version of the duplicated fold lemmas;
   * whether Mathlib already has those lemmas (it does not, by `exact?`).
8. **Second pass.** Every claim of the first draft was re-checked against the data, and the
   corrections are recorded in §8.

Caveats on the text measurements:
* Name resolution in `downstream_unfold.py` and in the reference counts uses the last name
  component, so these figures are approximate.
* Measurements labelled *heuristic* are upper bounds or candidate lists, not verdicts.
* The kernel and Lean's linters are authoritative wherever they apply.

---

## 2. Summary of findings

### 2.1 Headline results

* **The mechanical floor holds.**
  * A full build passes with 5 warnings, all of them unused variables in the byte-pinned
    `HandoffV3/FreerBridgeChecks.lean`.
  * No `sorry`, `axiom` or `@[implemented_by]` appears anywhere in the tree.
  * All 14 load-bearing theorems that were spot-checked have the standard footprint
    `[propext, Classical.choice, Quot.sound]`; `det_t02_runWith` is smaller still,
    `[propext, Quot.sound]`.
  * The full-tree linter run gives `multiGoal` 0, `show` 0, `unnecessarySimpa` 0, `missingEnd` 0
    and `openClassical` 0. `flexible` reports 2 sites.
* **Where the tree departs most from the guide is library design rather than tactic hygiene.**
  The deviations that cost the most maintenance come from missing API: proofs unfold definitions
  that live in other files (1,019 sites in 206 files) where the guide asks for API lemmas.
  * The ASP vault proofs repeat a 6-line `unfold`/`split_ifs`/`injEq`/`subst` block once per entry
    point. `Outcome.ok.injEq] at` occurs 93 times.
  * Only 5 of 1,051 structures have an `@[ext]` lemma.
  * The same helper lemmas are proved again and again: 40 private fold-max/min lemmas in 17 files,
    and 11 copies of `replay_append`.
* **Thirteen theorems state `x = x`**, mostly named `*_deterministic` and discharged by `rfl`.
  Three say in their docstrings that they are tautologies kept verbatim from a specification. Ten
  do not, and one docstring (`create2_address_deterministic`) claims more than the theorem states.
  These are the only findings that affect what a theorem *claims*.
* **One `SKILL.md` workflow rule is essentially unadopted:** open each `·` block with a `show`.
  Of 6,952 focus blocks, 3 open with `show` and 41 with `change`. No departure is recorded for
  this.
* **The metaprograms are small and mostly appropriate.** `tactics.md` findings:
  * The EVM symbolic-execution macros run `simp [*]` inside the macro and depend on goal order
    (`rotate_left; rfl; rfl`). Their failure messages are the raw `rw` errors, and no failure-path
    tests exist.
  * `frame_tac` relies on `set_option hygiene false`. Verified: removing it breaks the file.
  * In `FCA/Meta.lean` the one-change diff unifies speculatively without rolling the state back.
* **Naming follows the recorded departure, but two systematic conventions are unrecorded:**
  * 561 `Prop`-valued `def`/`abbrev` names are in `lowerCamelCase` (the guide asks for
    `UpperCamelCase`);
  * 223 `def`s are named in `snake_case` (`guard_*`, `*_mutant_*`).

  13 upper-case theorem names fall outside the recorded specification-identifier departure.

### 2.2 Finding counts by guide document

| Document | High | Medium | Low | Info / positive |
|---|---:|---:|---:|---:|
| `SKILL.md` (workflow, extraction ladder, quick reference, rationalizations) | 2 | 4 | 2 | 3 |
| `library-design.md` | 1 | 5 | 2 | 4 |
| `proof-style.md` | 0 | 4 | 4 | 3 |
| `performance.md` | 0 | 2 | 2 | 2 |
| `tactics.md` | 0 | 3 | 2 | 2 |
| Naming (`SKILL.md` quick reference; `naming-conventions.md` for detail) | 0 | 2 | 3 | 1 |

The full list is in §4, and the plan is in §6.

---

## 3. The review corpus (load-bearing, cross-cutting, non-trivial)

Categories: **LB** load-bearing, **CC** cross-cutting, **NT** non-trivial, **M** metaprogram.
Line counts are declaration lengths, including the statement.

| # | Declaration(s) | Location | Lines | Cat. | What the reading found | Verdict |
|---|---|---|---:|---|---|---|
| 1 | `Fame.Operator.simulation_square` | `RequestProject/Fame/Operator/Refinement.lean:47` | 362 | LB | 127 `·` blocks and no `show`. 17 `rename_i` in the file. 77 calls of `simp [wset]` although `wset_hit`/`wset_miss` exist in `Chain.lean`. The same `Wf`-preservation sub-proof is rebuilt in every arm. A positional 6-hole `refine` after `State.mk.injEq`. | Refactor — **High** (SR-03, SR-04, SR-14, SR-27) |
| 2 | `Fame.Operator.concreteStep_defined` | same file `:429` | 104 | LB | `rename_i` in the middle of a proof (`rename_i h` after a `rw`). `rw [word_phase_encode …, hph]; rfl` is a trailing-`rfl` smell. | Medium (SR-27, SR-15) |
| 3 | `Fame.Evm.VaultFull.entry_gas_le` | `RequestProject/Fame/Evm/Full/Gas.lean:110` | 208 | LB | Good: one named path lemma per branch (`run_deposit_zero` …), and each arm starts with an honest `change`. But the arms spell `fuel` as the literal `320`, and the case tree is repeated by #4. | Low/Medium (SR-18, SR-05) |
| 4 | `Fame.Evm.VaultFull.entry_never_fails` | same file `:323` | 197 | LB | The same path enumeration as #3, written out a second time. | Medium (SR-05) |
| 5 | `ASP.Vault.Step.totalDeposits_mono` | `RequestProject/ASP/Phase7/LedgerCap.lean:293` | 174 | LB | 16 identical arms (`cases hr : Vault.X …`, `unfold Vault.X at hr`, `split_ifs at hr`, `simp only [Outcome.ok.injEq] at hr`, `subst hr`, `simp`). | **High** (SR-14, SR-05) |
| 6 | `ASP.Vault.price_reference_is_written_only_by_settlement_and_seed` | `RequestProject/ASP/Phase7/Frame.lean:413` | 152 | LB | The same block as #5, closed by a trailing `rfl` after `subst`. `split_ifs … with g1 g2 g3` names hypotheses that are never used. | **High** (SR-14, SR-15) |
| 7 | `ASP.WholeContract.stepV2_inv` | `RequestProject/ASP/WholeContract/GreenInv.lean:161` | 141 | LB | `Inv` is a structure, yet the proof destructures and rebuilds it positionally 15 times (`⟨⟨hb, hc, hh⟩, hcons, …⟩`). `(try dsimp only); omega` appears. Good: a named inline invariant `Q` with a typed `hQ`. | Medium (SR-17, SR-31) |
| 8 | `SWC.reachable_invariants`, `invariant_preservation`, `*_preserved` | `RequestProject/SWC/Invariants.lean:394–620` | 51–91 | LB | The headline composes per-invariant lemmas through named structure fields, which is exemplary. The per-invariant proofs use `cases a <;> simp only … <;> obtain … <;> try exact h …` and then positional bullets labelled only by comments (`· -- openWindow`). 25 `rename_i` in the file. | Medium (SR-26, SR-27) |
| 9 | `Venue.step_preserves_wf` | `RequestProject/Venue/Engine.lean:478` | 99 | LB | Honest `change`, good use of the `Book.wf_*` API. Type ascriptions restate the conjunction that `State.WF` unfolds to. | Low (SR-17) |
| 10 | `Venue.step_deterministic`, `replay_deterministic`, `matchOrder_deterministic`, … (13) | Appendix B | 1–2 | LB (as claimed) | The statement is `f x = f x`. | **High** (SR-01) |
| 11 | `Handoff.QuantPolicyV2.rel_step` | `HandoffV3/Obligations/QuantPolicyV2.lean:410` | 55 | LB | Good use of the `classify_cons_*` API. But `rw [show … from rfl, …]`, an `unfold classifyItems` in the middle of the proof, and the same side-condition `simp [PItem.names, PItem.version?]` seven times. | Low (SR-15, SR-16) |
| 12 | `FCA.WeightedOpt.levelled_le_greedy_nat` | `RequestProject/FCA/WeightedOptimality.lean:269` | 114 | NT | A spine of typed `have`s, `suffices`, comments at the decisions, and a `Nat.find` witness. `cumg`, `cumy_le` and `hD` are candidates for extraction (rung 2). | **Exemplar** (SR-35) |
| 13 | `DetSim.Logging.det_t02_runWith`, `HandlerLawful.sum` | `RequestProject/DetSim/Log/Freer.lean:182, 224` | 3–6 | CC | Short structured proofs; dot notation (`handleSim_lawful.sum handleRead_lawful`); the lemma sits in the namespace of its type. | **Exemplar** |
| 14 | `MaximinRecursion` API (`maximinOrder_spec`, `le_maximinValue`, `maximinValue_perm`, …) | `RequestProject/MaximinRecursion.lean:63–125` | 3–8 | CC | An API built around a `Classical.choose` definition, with names computed from the statements. The binder block is repeated on every declaration instead of a `variable`. | **Exemplar** (Info) |
| 15 | The `replay_append` family | 11 files (Appendix C) | 2–5 | CC | Each module defines `replay` as a `foldl` and proves `replay_append` again. `V3Proofs.replay_append/replay_nil/replay_cons` (`HandoffV3/Proofs/Merge.lean:32–39`) duplicate `Handoff.replay_*` (`HandoffV3/Obligations/Replay.lean:26–33`) for the same `Handoff.replay`, including the `@[simp]` attributes, and `HandoffV3.lean` imports both. | Medium (SR-06, SR-12) |
| 16 | Fold max/min helpers (`le_foldr_max`, `foldr_min_le_seed`, …) | 40 theorems in 17 files | 3–8 | CC | Private copies over `ℝ`, `ℚ`, `ℕ`, `Money` and `Qty`. A single lemma over a `LinearOrder` replaces all of them (checked by compilation, §1 step 7). | Medium (SR-06) |
| 17 | `Fame.Operator.Chain` API (`wset`, `observe`, `wf_of_observe`) | `RequestProject/Fame/Operator/Chain.lean:135–215` | — | CC | `wset f s v` is pointwise `Function.update f s v` (checked). The API (`wset_hit`, `wset_miss`) is defined but used nowhere downstream. The simp lemmas for `decodeState` and `upd` live in `Refinement.lean`, not next to the definitions. | Medium (SR-13, SR-19) |
| 18 | EVM symbolic-execution macros (`vstep`, `vpush1/2/4`, `vjumpi_*`, `venter_*`, `evm_*`) and the scripts that use them (e.g. `run_fill_success_pos_pos`) | `RequestProject/Fame/Evm/Full/Tactics.lean:87–143`, `Full/Dispatch.lean:32–238`, `Evm/Exec.lean:98–138`, `Full/ExecRisk.lean:206` | — | M/NT | `macro` is the right extension point. But `simp [*]` runs inside each step, `rotate_left; rfl; rfl` depends on goal order, a failure surfaces as a raw `rw` error, and there are no `fail_if_success`/`#guard_msgs` tests. The 70-line scripts read as instruction traces, which is acceptable. | Medium (SR-36, SR-37) |
| 19 | `frame_tac` | `RequestProject/V5/Step/Triples.lean:20–27` | — | M | `set_option hygiene false` is load-bearing: without it the `rfl` patterns of `rcases` are hygienised into a hypothesis named `rfl✝`, and the first triple fails (verified). It also hard-codes a 12-way `rcases`. No test. | Medium (SR-38) |
| 20 | `FCA.oneChangeDiff`, `closedDecidesFalse`, the FCA attributes | `RequestProject/FCA/Meta.lean:100–200, 228–245` | — | M | Good: `throwErrorAt` on the narrow syntax node, tagged messages (`[FCA-TAG]`), and negative tests in `VacuityLintTests.lean`. Problems: `isDefEq` runs in a candidate loop with no rollback, `try … catch _ => return false` around `synthInstance`/`whnf`, and `componentsRev.head!`. | Medium (SR-39) |
| 21 | `#register_property` | `RequestProject/Fame/Foundation/Registry.lean:26–41` | — | M | `throwErrorAt` on the right token. The `catch _` turns any resolution failure, including ambiguity, into "unknown declaration". | Low (SR-40) |
| 22 | `ASP.PlanA.sequenced_admits` | `RequestProject/ASP/PlanA/Dependency.lean:182` | 55 | NT | `linter.flexible` site at `:223` (`simp [idsOf] at hz` then `exact Or.inr hz`), and an unused `[DecidableEq ι]`. The file was added after the 2026-10-15 audit. | Low (SR-23, SR-11) |
| 23 | `Fame.Evm.execOp_gasUsed_le` | `RequestProject/Fame/Evm/Gas.lean:70` | — | NT | The `linter.flexible` site that the 2026-10-15 report left open (`all_goals try simp_all` feeding `rcases`). | Low (SR-23) |

---

## 4. Findings, by guide document and rule

Each finding has an identifier (`SR-nn`), the rule it falls under (document and section), the
evidence, a classification (C / D / N / I, as in §0.2), a severity, and a recommendation. Counts
come from `data/`.

### 4.1 `SKILL.md`

**SR-01 — Reflexive theorems presented as properties.** `SKILL.md` "Core principle" and
`library-design.md` "Statements are the interface; proofs are disposable"; the rationalization
"The proof compiles, ship it".
* 13 theorems have a conclusion whose two sides are textually identical (Appendix B).
* 3 of them say so in their docstrings ("a tautology, kept because the specification states it"):
  `Fame/Flywheel/Capacity.lean:52`, `Fame/LMM/Theorems.lean:174`, `:292`.
* 10 do not: `Venue/Engine.lean:331` (`step_deterministic`) and `:655`, `Venue/Matching.lean:320`,
  `Venue/Instrument.lean:229`, `MatchingPriority/PriceTime.lean:104`,
  `GEX/Match/Obligations.lean:94`, `Feeds/Create2.lean:42`, `Feeds/SyntheticIndex.lean:36`, and
  the two aliases in `Venue/DisciplineScope.lean:97, 144`.
* The docstring of `create2_address_deterministic` says the address "does not depend on the
  deployer's nonce". That fact comes from the *type* of `create2Address`, which has no nonce
  parameter, not from the theorem.

A statement is the interface, and these statements constrain nothing.
*Class N. **High**.* Either state the property that has content (for example "the result depends
only on these inputs", as an equation between two calls whose other inputs differ), or keep each
one verbatim and mark it as a tautology in its docstring, as the three acknowledged ones already
do. Add a reflexive-statement check to `audit_lean_proof_style.py`.

**SR-02 — "Open each block with a redundant `show`" is not practised.** `SKILL.md` §3; also the
rationalization "Adding `show` lines is redundant noise".
* 6,952 `·` blocks in the tree; 3 open with `show`
  (`RequestProject/Venue/Mvp/Rigor.lean:285, 290, 354`) and 41 with `change`.
* Of the 281 theorems of 30 lines or more, 59 contain any `show`.
* `simulation_square` has 127 blocks and no `show`.

`LEAN_PROOF_STYLE.md` R8 records the *honesty* half of the rule, which `linter.style.show` checks
(0 sites), but not the *presence* half, and no departure is recorded.
*Class N. Medium.* `proof-style.md` "Structure at the decisions, terseness at the routine" makes
this negotiable. Recommendation: record a scoped departure ("`show` is required at the decision
points of load-bearing proofs; routine bullets may omit it"), then apply it to the corpus in §3.

**SR-03 — Extraction ladder: monolithic case analyses.** `SKILL.md` "The extraction ladder",
rungs 1 to 3; `proof-style.md` "When review says split it".
* 85 theorems are 50 lines or longer, 11 are 100 or longer, and 5 are 150 or longer.
* `simulation_square` (362 lines) rebuilds the same well-formedness argument in each of its arms.
* Theorems #5 and #6 of §3 repeat a 6-line block 16 times each.
* `entry_gas_le` and `entry_never_fails` write the same path tree out twice.

The repository already has the target shape: `RequestProject/Fame/Evm/Observe.lean` proves the
same kind of square one primitive at a time (`simulation_square_deposit` `:303`,
`simulation_square_withdraw` `:367`), with `show` at the decision points.
*Class N. Medium.* See SR-14 and Phase 2 of §6.

**SR-04 — "Never unfold definitions downstream".** `SKILL.md` §1 and the first row of the quick
reference; `library-design.md` "Every definition ships its API".
* 2,741 `unfold` targets in tactic position. 1,720 unfold a definition from the same file, 1,019
  one from another file (206 files), and 2 a definition that could not be resolved
  (`data/unfold_sites.tsv`).
* By subsystem: ASP 381, FameWins 97, Fame 94, HandoffV3/Obligations 60, Venue 51, PaperTests 49,
  V5 46, SWC 37.
* Most-unfolded downstream targets: `notePayoff` (21), `conservation` (19), `band` (19),
  `deq` (18), `withdrawInstant` (16), `noteEquity` (16), `deposit` (14), `noteCollateral` (14),
  `absDiff` (13), `settleNetDeltas` (13).

`delta` is used in tactic position at 4 sites only.
*Class N. Medium (High for the ASP vault, see SR-14).*

**SR-05 — Repeated sub-arguments not lifted.** `SKILL.md` "extraction ladder", rung 1 ("A
sub-argument repeats within one proof → name it as a local `have`") and rung 2. Evidence: the
16-arm blocks of #5 and #6, the two copies of the EVM path tree (#3 and #4), and the `Wf`
preservation sub-proofs in #1. *Class N. Medium.*

**SR-06 — "Search a bare goal by shape before writing a helper".** `SKILL.md` "extraction
ladder", rung 0, and the quick-reference row of the same name.
* 380 statement texts occur in more than one file (818 declarations,
  `data/duplicate_statements.tsv`).
* 257 of these groups are the deliberate AgentHandoff (v2.1) ↔ HandoffV3 regression pin
  (ADJ-18), which is exempt. That leaves 123 groups, of three kinds:
  * **(a) Aliases proved by reference**, such as `F2_digest_binds := digest_binds …` and
    `pt05_backed := replay_agrees_with_live …`. These are legitimate traceability.
  * **(b) The same helper proved again**: 40 private fold-max/min lemmas in 17 files (e.g.
    `le_foldr_max` over `ℝ` in `BoundedLevelCeiling`, `CheapLevelCeiling`, `JointLevelCeiling`,
    `NestedChainCeiling` and `PrefixLevelCeiling`, and over `ℕ`/`Money`/`Qty` in
    `HandoffV3/Proofs/Corpus.lean:157`, `Production/Absorption/Core.lean:389` and
    `Venue/BatchClearing.lean:200`); `perm_pair_cases` 4 times; `replay_append` 11 times.
  * **(c) Per-module boilerplate about different constants**, such as `reports_accepted` 16 times.
    These are not semantic duplicates.

`exact?` finds no Mathlib lemma for `x ∈ L → x ≤ L.foldr max s`. A single generic
`List.le_foldr_max_of_mem` over a `LinearOrder` was compiled and closes both the `ℝ` and the `ℕ`
instances.
*Class N for (b), C for (a), I for (c). Medium.*

**SR-07 — Verify mechanically (positive).** `SKILL.md` §4.
* Build exit 0.
* No `sorry`, `axiom` or `@[implemented_by]` in the source text.
* Axiom footprint standard on all 14 load-bearing theorems checked.
* `scripts/AxiomAudit.lean` gathers axioms for each declaration with `collectAxioms`, as the
  guide asks.

*Class C. Info.*

**SR-08 — `#print axioms` outside `#guard_msgs` asserts nothing.** `SKILL.md` §4 ("`#print axioms`
for a spot check; for CI … assert the whole expected footprint").
* 637 `#print axioms` lines in 14 files. 333 are wrapped in `#guard_msgs` (`GEX/Audit.lean` 171,
  `CLF/Audit.lean` 95, `DetSim/Timeline/AxiomPins.lean` 36, …).
* 304 only print: `Fame/Production.lean` 131, `Verification.lean` 72, `HandoffV3/Audit.lean` 37,
  `DetSim/Audit.lean` 15, and others.
* They add to the 1,544 `info:` lines of the build log.

The real gate is the TSV produced by `AxiomAudit`, so nothing goes unchecked.
*Class I. Low.* Wrap them in `#guard_msgs` or delete them.

**SR-09 — The lint profile in the build is narrower than the guide's profile.** `SKILL.md` §4
("Choose lints by project role…").
* The build enables `linter.style.maxHeartbeats`, `setOption`, `refine`, `cases` and `induction`.
* `multiGoal`, `show` and `flexible` run on demand only. Warnings do not fail the build.
* This review ran the guide's full self-contained and reusable-library profiles over the whole
  tree. Results:

| Linter | Sites |
|---|---:|
| `multiGoal`, `show`, `unnecessarySimpa`, `missingEnd`, `openClassical` | 0 each |
| `flexible` | 2 |
| `unusedDecidableInType` | 16 |
| `unusedFintypeInType` | 14 |

This is the full-tree evidence that the open decisions LN-F4 and LN-F5 of `LEAN_GUIDE.md` asked
for. `linter.auxLemma` remains unknown in the pinned toolchain (SK-F2 in the notes).
*Class N (recorded as open decisions). Medium.* See Phase 0 of §6.

**SR-10 — A gate that can silently pass: a blind spot in `linter.flexible`.** `SKILL.md`
rationalization "The check passed, so we're clean".
* Verified with `tools/FlexibleBlindSpotFixture.lean.txt`: `linter.flexible` flags `simp at h`
  followed by `exact h` or `exact Eq.symm h`, but **not** followed by `exact h.symm`.
* A use of the stained hypothesis through a dotted identifier (`h.symm`, `h.1`, `h.2`) is
  invisible to the linter.
* A text heuristic finds two such sites: `Fame/Operator/Chain.lean:147` (`wf_of_observe`) and
  `ASP/Phase5/Watchdog.lean:240`.

*Class I (a limit of the tool). Medium.* Keep `audit_lean_proof_style.py nonterminal_simp` as a
second check, extend it to dotted identifiers, and fix the two sites.

**SR-11 — Unused `Decidable`/`Fintype` instance hypotheses (30 sites).** `SKILL.md` §4
(reusable-library profile: "the two `unused*InType` checks").
* Files: `EpochFeasibility.lean` (7), `SingleBucketEvents.lean` (6), `Governance/Deputies.lean`
  (5), `ASP/PlanA/Dependency.lean` (2), `AdmissionBranch.lean` (2),
  `AnnualizedYieldBracket.lean` (2), and others (`data/linter_sites.tsv`).
* The fix is to drop the binder and use `classical` in the proof. Dropping a binder changes the
  statement (R15), but the registry keys on names, so callers are unaffected.

*Class N. Low.*

**SR-12 — Custom linters for project conventions.** `SKILL.md` §4 ("Write a custom linter for
every project-specific convention").
* There is no `@[env_linter]`. The project enforces its conventions with Python checks.
* `#fca_vacuity_lint` (`FCA/Meta.lean:313`) is a command-level linter with negative tests, and is
  a good model.
* Candidates for an `env_linter`:
  * the specification-identifier naming departure;
  * duplicate `@[simp]` lemmas (SR-06's `V3Proofs.replay_nil`);
  * reflexive statements (SR-01).

*Class N (recorded as SK-F4). Low.*

### 4.2 `library-design.md`

**SR-13 — API not in the definition's file.** "Every definition ships its API, immediately, in the
same file".
* The `@[simp]` lemmas for `Concrete.upd` and `decodeState` are in
  `Fame/Operator/Refinement.lean:21–43`, while the definitions are in `Chain.lean:125, 212`.
* `replay_nil` and `replay_cons` for `Handoff.replay` (`HandoffV3/Kernel.lean:166`) are in
  `Obligations/Replay.lean` and again in `Proofs/Merge.lean`. `Kernel.lean` is byte-pinned, which
  explains the move. The duplication is not explained.

*Class N. Medium.*

**SR-14 — Missing success-characterisation API for the ASP vault entry points.** "Every definition
ships its API"; "the smell test: needing … a trailing `rfl` … is the official signal of missing
API".
* `Outcome.ok.injEq] at` occurs 93 times.
* `unfold Vault.*` occurs 33 times in `ASP/Phase7/` (Frame 18, LedgerCap 14, InstantCap 1).
* Every frame and monotonicity theorem re-derives "if `Vault.X … = .ok s'` then `s'` is the
  `XState` of …" by unfolding the implementation.

One lemma per entry point (`Vault.deposit_eq_ok : deposit p s c a m = .ok s' → s' = depositState …`,
together with projection simp lemmas for each `…State`) would reduce each of the 16 arms of #5 and
#6 to a single line, and would decouple ~30 theorems from the bodies of the entry points.
*Class N. **High**.*

**SR-15 — Trailing `rfl` and `show … from rfl` (the missing-API smell).** "The smell test".
* The text audit counts 7 `rfl` sites straight after `simp`; the 2026-10-15 report explains them
  as legitimate.
* It counts 197 straight after `rw` (194 on 2026-10-15; the tree has grown from 1,078 to 1,088
  files since then).
* The reading adds:
  * `concreteStep_defined` (`rw [word_phase_encode …, hph]; rfl`: a missing `encodePhase_open`
    lemma);
  * `price_reference…` (`subst hr; rfl` ×16);
  * `rel_step` (`rw [show RState.classify … = … from rfl, …]`).

*Class N. Low.*

**SR-16 — Unfolding inside the module, despite API in scope.** "Downstream proofs use the API,
never unfold".
* `simulation_square` calls `simp [wset]` 77 times although `wset_hit` and `wset_miss` exist.
  Neither is used anywhere outside `Chain.lean`.
* `rel_step` unfolds `classifyItems` next to the `classifyItems_snoc_*` lemmas.

*Class N. Medium.*

**SR-17 — Invariants as anonymous conjunctions; positional construction.** "Bundling" (property
proofs as structure fields).
* `State.WF` (Venue), `LedgerInv` (WholeContract) and `Wf` (Operator) are `∧`-chains. Proofs
  destructure them positionally (65 `obtain` patterns with 8 or more components) and restate them
  in type ascriptions (`step_preserves_wf`).
* Where a structure does exist, as with `Inv` in `GreenInv.lean:33`, the proofs still use the
  anonymous constructor in field order, so adding a field breaks every arm.
* Positive counter-example: `SWC.invariant_preservation` uses named fields (`hInv.identity …`).

*Class N. Medium.* Turn invariants into structures, and use `{ hs with ledger := … }` and
field-name access in proofs.

**SR-18 — One canonical spelling per constant.** "Simp-normal form"; `proof-style.md` "One
canonical spelling per domain constant — including numerals".
* `fuel` is defined as `320` (`Fame/Evm/Full/Program.lean:466`), but `320` is written out about
  88 times across `Fame/Evm/Full/*.lean`, including in the `change` steps of `entry_gas_le`.
* `wordModulus := 2 ^ 256` (`ASP/Phase4/ABI.lean:31`) is re-spelled in the middle of a proof
  (`have hmod : (wordModulus : Int) = 2 ^ 256`, `:155`).
* `2 ^ 64` and `18446744073709551616` appear in the same files (`HandoffV3/Digest.lean`,
  `HandoffV3/Proofs/Merge.lean`, `DetSim/Schema/WireRecords.lean`). `2 ^ 32` and `4294967296` both
  appear in the tree as well.

*Class N. Medium.*

**SR-19 — Re-implemented library function.** "Choosing the abstraction level is the dominant
proof-shortener". `Fame.Operator.wset` is pointwise `Function.update` (checked: `funext s; simp
[Function.update_apply]`). Using `Function.update` brings Mathlib's `update_self`/`update_of_ne`
simp set, which `GreenInv.lean` already uses. *Class N. Low.*

**SR-20 — `@[ext]` lemmas are almost absent.** "Every definition ships its API" (an `@[ext]`
lemma).
* 1,051 structures; 5 `@[ext]` attributes.
* 86 `.mk.injEq` uses, typically followed by a positional `refine ⟨?_, …⟩`. There are 21
  `refine` calls with 5 or more holes.

*Class N. Medium.* Add `@[ext]` to the state records that proofs compare (`State`, `Concrete`,
`VaultState`, …).

**SR-21 — Reducible `Prop` definitions without a recorded reason.** "Abstraction boundaries are
explicit decisions" (semireducible by default; any deviation justified).
* 736 `abbrev`s: 449 have type `Prop` (mostly registry "law" statements such as
  `nonceMonotoneLaw`), 26 `Type`, and 252 have no declared type.
* No `irreducible` anywhere. Sealed boundaries are not used, and none is needed.

*Class N for the `Prop` abbrevs. Low.* Make them `def` unless something relies on reducibility,
or record why it is needed.

**SR-22 — Positive conformance.** *Class C. Info.*
* No global `Fact` instance.
* `open Classical` appears only in scoped `… in` form (21 sites; `openClassical` linter 0).
* Total functions: refusals are modelled as `Option`/`Outcome`, which the notes (LD-F3) read as
  conformant, and subtypes are rare (6).
* Optimised definitions keep a readable reference: `MatchingPriority.replayRec = replay`
  (`ReferenceEngine.lean:96`), and the executable-model ≡ specification theorems.

### 4.3 `proof-style.md`

**SR-23 — Non-terminal `simp` (`linter.flexible`): 2 sites.** "simp discipline".
`ASP/PlanA/Dependency.lean:223` (new since 2026-10-15) and `Fame/Evm/Gas.lean:70` (carried over),
plus the 2 dotted-identifier sites of SR-10. *Class N. Low.*

**SR-24 — Non-terminal `simp` that the linter accepts.** "Non-terminal `simp` … squeeze it".
* The guide's text is stricter than the linter. `simp [wset]; omega` and `subst hw; simp [wset];
  omega` (≈80 sites in `Refinement.lean`) are non-terminal bare `simp` calls followed by `omega`,
  which the linter accepts because `omega` is in its flexible set.
* `simp … at *` occurs 155 times; it rewrites every hypothesis and couples the following steps to
  the whole simp set.

*Class I (accepted by the linter; the guide's wording is stricter). Low.* Prefer `simpa [wset]
using …` or `simp only`.

**SR-25 — `calc` and `suffices` are rare.** "calc replaces rewrite chains"; "have and suffices".
* 141 `calc` blocks (87 files) against 6,309 `rw` in tactic position; 16 `rw [...]` calls carry 6
  or more rewrites (e.g. `ArrivalDisplacement.lean:432, 438`, `HandoffV3/Digest.lean:107`).
* `suffices` is used 10 times.

The guide sets no threshold. The reading found no long rewrite chain in the load-bearing corpus
whose intermediate terms a reader needs; most inequalities are closed by `omega`/`linarith`.
*Class I. Info.*

**SR-26 — Goal ownership after `<;> try …`.** "One focused goal at a time" (named `case` blocks
when the names add information).
* `multiGoal` reports 0, but a pattern defeats its intent: `cases a <;> simp only [...] at h <;>
  obtain … <;> try exact h …`, followed by positional bullets whose only label is a comment.
* There are 71 comment-labelled bullets in the tree (e.g. `SWC/Invariants.lean:399, 410, 420`) and
  8 `<;> try` chains.
* Which goals survive the `try` depends on the proof, so the bullets depend on goal order.

*Class N. Medium.* Use `case deposit => …` with the constructor names.

**SR-27 — Inaccessible names (`rename_i`).** "Structure at the decisions" (the reader must see
the decision); robustness.
* 147 `rename_i` in 51 files; `Refinement.lean` has 17 and `SWC/Invariants.lean` 25.
* `concreteStep_defined` renames *in the middle of a proof*, after a `rw`.

The guide has no `rename_i` rule as such. This finding is filed under robustness and readability:
auto-generated names couple the proof to the shape of `split`/`cases`.
*Class I/N. Medium.* Use `split at h with | …`, `obtain ⟨…⟩`, `case … =>` with binder names, or
`next x y =>`.

**SR-28 — `have` with explicit statements.** "Always give `have` an explicit statement when the
type is not obvious".
* 7,595 `have`s; 5,126 have an explicit type.
* The heuristic counts 2,352 untyped `have h := term`. It cannot tell whether the type is obvious,
  so this is an upper bound; it was 2,316 on 2026-10-15, on 10 fewer files.
* In the load-bearing corpus the untyped `have`s are almost all obvious (`have hescw := hesc w`).

*Class C/I. Info.*

**SR-29 — One tactic invocation per line.** "One tactic invocation per line, in general".
* 2,789 lines carry more than one `;`-separated tactic (heuristic).
* Many of them express one idea (`simp [wset]; omega`). Others pack unrelated state changes
  (`subst hw; simp [wset]; omega`; `simp only [Option.some.injEq] at h; subst h` in
  `GreenInv.lean`).

*Class I (qualitative rule). Low.*

**SR-30 — Honest `show`/`change` (positive).** "Announce goals with show" (honesty). Linter 0 on
the whole tree; `change` is used where the goal is restated by definitional unfolding (e.g.
`entry_gas_le`, `step_preserves_wf`). *Class C. Info.*

**SR-31 — `try` as a fallback inside proofs.** "simp discipline" (stable intermediate goals) and
"Golfing" (never golf away the skeleton).
* `(try dsimp only); omega` occurs 12 times in 4 files (e.g. `GreenInv.lean`).
* `try exact h …` after `<;>` (SR-26).
* A `try` hides whether a step is needed. When the definitions change, the proof keeps compiling
  until it does not, and then the reason is hidden.

*Class N. Low.*

**SR-32 — Golfing and readability (positive).** The corpus contains no golfed proof of a
non-trivial argument. The short proofs (#13, #14) are trivial results or compositions of lemmas.
*Class C. Info.*

### 4.4 `performance.md`

**SR-33 — Resource budgets with no measurement.** "Treat every existing `set_option maxHeartbeats`
as an unproven claim"; "Keep overrides scoped per declaration … and only where measured".
* `maxHeartbeats`: 2 scoped overrides (`ASP/Phase7/CallV2.lean:141, 240`, both `1000000`), with a
  comment but no measurement. This is PF-F1 in the notes, still open.
* There is no `#count_heartbeats` anywhere in the tree.
* `maxRecDepth`, by analogy: 38 **unscoped** file-level settings. The values are copied: `8000` in
  20 files of `ASP/Phase7`, `ASP/Phase8` and `Fame/Evm/Full`, and `100000` and `1000000`
  elsewhere (`Venue/Obligations.lean:46` and `Venue/TaskRegister.lean:69` at `1000000`).
* `LEAN_LINT_POLICY.md` explicitly exempts `maxRecDepth` from LP5, so this is a policy gap rather
  than a gate failure.

*Class N. Medium.* Measure, scope each setting with `in` to the declaration that needs it, and
record the figure next to it.

**SR-34 — Kernel-replayed decision procedures.** "When a goal is closed by `Eq.refl`/`rfl`/
`decide`, the kernel replays the whole reduction".
* `decide +kernel` occurs 1,148 times (461 under `Fame/`) and `native_decide` 122 times (44
  files).
* The `native_decide` uses are covered by the recorded Tier-2 departure (`check_axiom_budget.py`).
* `decide +kernel` adds no axiom, but its cost is not measured anywhere. Lake does not print a
  per-module time for every module, so the build log is not a usable measure; the guide warns
  against it in any case.

*Class D for `native_decide`, I for cost. Medium (for lack of measurement).*

**SR-35 — Readable reference plus fast form (positive).** "Optimize the definition, keep the
semantics". Pairs exist (`replayRec`/`replay`; the venue and kernel oracles), and the typed-`have`
proofs of #12 are cheap. *Class C. Info.*

**SR-36 — Symbolic execution cost is paid at every step.** "Count reduction paths, not term size";
"Measure per-declaration cost".
* Each `vstep` runs `rw [run_unfold …]` and then `simp [*]` over every hypothesis in scope.
* `ExecRisk.lean`/`ExecCollateral.lean` contain about 16 theorems of 70–78 lines, each a sequence
  of about 60 such steps.
* No per-declaration cost is recorded.

*Class I. Low.* Measure one representative script with `#count_heartbeats`. If it dominates,
replace `simp [*]` with a fixed `simp only` set or a named simp set.

### 4.5 `tactics.md`

**SR-37 — EVM macros: contract, failure messages, tests.** "Define the tactic contract"; "Make
failures local and actionable"; "Test the failure surface".
* **The extension point is right.** These are hygienic macros, the smallest tool for a syntax-only
  expansion.
* **The contract is unstated.**
  * `simp [*]` inside the macro changes behaviour with every hypothesis in scope.
  * `rotate_left; rfl; rfl` (in `vpush1`/`vpush2`/`vpush4`) depends on `rw` producing its side
    goals in a particular order.
* **Failures are not actionable.** A wrong opcode reports the raw `rw` "motive"/"pattern not
  found" error, not "expected opcode 0x57 at pc N".
* **No tests.** There is no `fail_if_success` or `#guard_msgs` under `Fame/Evm` or `V5`.

*Class N. Medium.*

**SR-38 — `frame_tac` depends on unhygienic expansion.** "Generate syntax and declarations
safely: use `unhygienic` only when name capture is the explicit interface, and cover that
behaviour with tests".
* Verified by experiment: with `set_option hygiene false` removed, `V5/Step/Triples.lean:48` fails.
  `rcases hc with rfl | …` binds a hypothesis called `rfl✝` instead of substituting.
* The unhygienic expansion is therefore a workaround, and nothing tests it.

*Class N. Medium.* Rewrite without capture. One option: `simp only [List.forall_mem_cons]` and
then `refine ⟨?_, …⟩ <;> simp [Agree, refuse]`; another: `obtain h | h … := hc <;> subst h`.
Add a `#guard_msgs` test.

**SR-39 — `FCA/Meta.lean`: speculative unification and broad recovery.** "Make speculative state
transactional"; "Keep recovery scopes small"; "Prefer optional destructors over panics".
* `oneChangeDiff` (`:175–188`) calls `isDefEq mTy hTy` and then `isDefEq m rHyps[j]!` inside a
  candidate loop, without `withoutModifyingState`/`commitWhen`. A first unification that succeeds
  followed by a second that fails leaves metavariable assignments behind, and they affect later
  candidates.
* `closedDecidesFalse` (`:231–238`) catches everything around `synthInstance` and a
  default-transparency `whnf`, so heartbeat exhaustion is reported as "not known false".
* `componentsRev.head!` (`:338`) can panic.

Good points: `throwErrorAt v "[FCA-TAG] …"` attaches the error to the narrow token, and
`VacuityLintTests.lean` contains negative tests.
*Class N. Medium.*

**SR-40 — Minor items: commands, attributes, tracing.** "Make failures local and actionable";
"Build tracing in from the start".
* `#register_property` maps every resolution failure to "unknown". `throwError "malformed
  load_bearing attribute"` has no syntax reference.
* There are no trace classes anywhere. The current tools are small enough that this is acceptable.
* `DetSim/Tiers.lean:117–121` uses `args[i]!` only after an `isAppOfArity` check, so it is safe.

*Class I/N. Low.*

### 4.6 Naming (the `SKILL.md` quick-reference row; detail in `naming-conventions.md`)

**SR-41 — Upper-case theorem names.**
* 96 theorems have a last name component that starts with an upper-case letter. 83 carry a
  specification or paper identifier (`HL_*`, `F6_*`, `F13_*`, …) and are covered by the recorded
  R26 departure.
* 13 are not covered (`data/names.tsv`):
  * `WellFormedB_iff` ×2 (should be `wellFormedB_iff`);
  * `KcEff_pos`, `G_mono`, `W_unit`, `W_unit_bidAllocation`;
  * `S_star_safety_bound`, `P_star_union_S_star_coherent`, `P_star_performance_bound`;
  * `JS_DetSim_*` ×4 (`docs/design/evidence/`).

*Class N. Low.*

**SR-42 — `Prop`-valued definitions in `lowerCamelCase`.** 561 `def`/`abbrev` declarations of
type `Prop` start with a lower-case letter: `invariant`, `priceLiq`, `nonceMonotoneLaw`, … The
guide and `LEAN_PROOF_STYLE.md` R26 ask for `UpperCamelCase`, and no departure is recorded. Many
of them are registry keys. *Class N. Medium.*

**SR-43 — `snake_case` definitions.** 223 `def`s use underscores: `guard_floatNonAssoc`,
`applyTransition_mutant_ungated`, `reject_wrong_version`. This is a systematic local convention
for guards, mutants and fixtures, not recorded as a departure. *Class N. Low.* Record it, since
renaming has little value.

**SR-44 — Names not computed from the statement.**
* `MatchingPriority.replay_deterministic` states `replayRec s es = replay s es`; the name should be
  `replayRec_eq_replay`.
* `Fame.POL.replay_append` states `replay o (j ++ [e]) = applyEvent (replay o j) e.event`; the
  name should be `replay_concat` or `replay_append_singleton`.
* The ten `*_deterministic` reflexive theorems (SR-01).
* 58 statements use `≥`/`>` (47 names contain `ge`/`gt`, e.g. `decodePackageBody_length_ge_17`),
  where the guide asks for `≤`/`<`.

*Class N. Low.*

**SR-45 — Namespaces and dot notation (positive).** Lemmas about a type sit in that type's
namespace (`HandlerLawful.sum`, `Book.wf_insert`, `StepsTo.invariant`), so dot notation works.
*Class C. Info.*

---

## 5. Exemplars to copy

| What | Where | Why |
|---|---|---|
| A long proof with a typed-`have` spine | `FCA.WeightedOpt.levelled_le_greedy_nat` (`FCA/WeightedOptimality.lean:269`) | `set`/`have` with stated types, `suffices`, a comment at each decision |
| A headline theorem that composes named lemmas | `SWC.invariant_preservation`, `reachable_invariants` (`SWC/Invariants.lean:603–620`) | Field-named composition; induction on reachability in 2 lines |
| A simulation square proved one primitive at a time | `Fame/Evm/Observe.lean:303, 367` | The target shape for #1 of §3 |
| API around a choice-based definition | `MaximinRecursion.lean:63–125` | Names computed from the statements; term-mode proofs |
| Lawfulness composition | `DetSim/Log/Freer.lean:224–257` | Dot notation, namespace placement |
| A command-level custom linter with negative tests | `FCA/Meta.lean:313`, `FCA/VacuityLintTests.lean` | The model for SR-12 |

---

## 6. Remediation and refactoring plan

The phases are ordered by value per unit of effort and by dependency. Each phase ends with the
verification steps in §6.6. Two constraints apply throughout:
* The byte-pinned files (`HandoffV3/Kernel.lean`, `HandoffV3/FreerBridgeChecks.lean`,
  `HandoffV3/Resolutions.lean`) and the v2.1 regression pin (`AgentHandoff/`, ADJ-18) are out of
  scope.
* Any statement or name change goes through the registry, claim-index and axiom-audit
  regeneration of §6.6.

### 6.1 Phase 0 — Gates and policy (1–2 days; no proof changes beyond the listed sites)

| Step | Action | Closes |
|---|---|---|
| 0.1 | Promote `linter.style.multiGoal` and `linter.style.show` into `lakefile.toml` (`weak.`), with rows in `LEAN_LINT_POLICY.tsv`. Their full-tree backlog is 0 (§4.1 SR-09). | SR-09; LN-F5 |
| 0.2 | Make the promoted linters fail CI: run `lake build` with these options and fail on any `linter.style.(multiGoal\|show)` warning. Add the known-trigger fixture (`tools/LinterTriggerFixture.lean.txt`) as a vacuity anchor. | SR-09; LN-F4, LN-F6 |
| 0.3 | Fix the 2 `linter.flexible` sites and the 2 dotted-identifier sites; then add `linter.flexible` to the on-demand gate with a ratchet at 0. Extend `nonterminal_simp` in `audit_lean_proof_style.py` to dotted identifiers. | SR-10, SR-23 |
| 0.4 | Remove the 30 unused `DecidableEq`/`Fintype` binders (use `classical` in the proof); then enable both `unused*InType` linters. | SR-11 |
| 0.5 | Reflexive theorems: for each of the 10 unacknowledged ones, either restate the content-bearing property or add the "tautology, kept verbatim" note that the three others carry. Fix the `create2_address_deterministic` docstring. | SR-01 |
| 0.6 | Record decisions in `LEAN_PROOF_STYLE.md`: the scope of `show` (SR-02), `snake_case` guards/mutants (SR-43), the `Prop`-def casing policy (SR-42), and a `maxRecDepth` policy (SR-33). | SR-02, SR-33, SR-42, SR-43 |
| 0.7 | Add ratchet metrics to `audit_lean_proof_style.py`: downstream `unfold`, reflexive statements, duplicate statements outside the pin, `·` blocks opening with `show` in the §3 corpus, unscoped `maxRecDepth`, and `rename_i`. | Keeps Phases 1–3 from regressing |

### 6.2 Phase 1 — Cross-cutting API (1–2 weeks)

| Step | Action | Expected effect | Closes |
|---|---|---|---|
| 1.1 | Create one shared module (e.g. `RequestProject/Util/ListFold.lean`) with generic `LinearOrder` lemmas: `le_foldr_max_of_mem`, `foldr_max_le`, `seed_le_foldr_max`, `foldr_min_le_of_mem`, `foldr_min_le_seed`, `le_foldr_min`, `foldr_max_eq_seed_or_mem`. Add `List.perm_pair_cases`. Replace the 40 + 4 private copies. | −44 declarations; one place to fix | SR-06 |
| 1.2 | Delete `V3Proofs.replay_append/replay_nil/replay_cons` (`HandoffV3/Proofs/Merge.lean:32–39`) and use the `Handoff.` lemmas (`Merge.lean` is not byte-pinned). Where a module's `replay` is literally `List.foldl step`, state `replay_append` through `List.foldl_append` once per module, keeping it a one-liner, or instantiate `DetSim/Trace.lean`'s `Machine`. | Removes duplicate `@[simp]` lemmas | SR-06, SR-13 |
| 1.3 | **ASP vault API.** For each entry point `Vault.X` add `X_eq_ok_iff` (or `X_ok_state`), plus `@[simp]` projection lemmas for each `XState`. Rewrite the arms of `Step.totalDeposits_mono`, `price_reference_is_written_only_by_settlement_and_seed` and the other `Frame.lean` theorems to use them. | Remove most of the 93 `Outcome.ok.injEq] at` and the 33 `unfold Vault.*`; theorems #5 and #6 shrink from 150+ lines to about 40 | SR-14, SR-04, SR-05, SR-15 |
| 1.4 | **Fame.Operator.** Move the `decodeState`/`upd` simp lemmas into `Chain.lean`. Replace `wset` with `Function.update`, or keep `wset` and use `wset_hit`/`wset_miss`. Extract `Wf.upd_wset…` preservation lemmas. | Prerequisite for 2.1 | SR-13, SR-16, SR-19 |
| 1.5 | Add `@[ext]` to the state structures that proofs compare through `.mk.injEq` (start with the 86 sites). | Named-field goals instead of positional `refine` | SR-20 |
| 1.6 | Canonical constants: use `fuel` (not `320`) in statements and `change` steps; never re-spell `wordModulus`; one spelling of `2 ^ 64`/`2 ^ 32` per module. | Removes numeral-spelling fragility | SR-18 |
| 1.7 | Equation lemmas for the most-unfolded downstream targets (`notePayoff`, `conservation`, `band`, `deq`, `noteEquity`, `noteCollateral`, `absDiff`, …), then replace the `unfold`s. | Downstream `unfold` count falls (ratchet from 0.7) | SR-04 |

### 6.3 Phase 2 — Restructuring the load-bearing proofs (ongoing, by subsystem; after Phase 1)

| Step | Proof(s) | Refactor |
|---|---|---|
| 2.1 | `simulation_square`, `concreteStep_defined` | One lemma per primitive (`simulation_square_deposit`, …) as in `Fame/Evm/Observe.lean`; the headline becomes a `cases p` dispatch. Replace `rename_i` with `split at hstep with …` or `obtain`. Add `show` at each decision. |
| 2.2 | `entry_gas_le`, `entry_never_fails` | State the path enumeration once (`entry_run_cases : ∀ e, ∃ path, run … = resultOf path ∧ …`) and derive both theorems from it. |
| 2.3 | `stepV2_inv` | Per-call lemmas; build `Inv` with field syntax (`{ hs with ledger := … }`); remove `(try dsimp only)`. |
| 2.4 | `SWC.*_preserved` | Replace `<;> try exact h …` and the comment-labelled bullets with `case <ctor> =>`; remove `rename_i`. |
| 2.5 | `Venue.step_preserves_wf` and others using conjunction invariants | Turn `State.WF`/`LedgerInv`/`Wf` into structures; drop the restating type ascriptions. |
| 2.6 | All 85 theorems of 50 lines or more | Review each against the extraction ladder; record "keep as is" where a case tree is the clearest form (e.g. the EVM scripts). |

### 6.4 Phase 3 — Naming (with a migration window)

| Step | Action | Closes |
|---|---|---|
| 3.1 | Rename the 13 upper-case theorem names outside the departure, the 2 misnamed theorems of SR-44, and the reflexive `*_deterministic` names (after 0.5). Keep `@[deprecated] alias` entries for one release so that the registry and the claim index can migrate. | SR-41, SR-44 |
| 3.2 | `Prop`-valued definitions: either record a departure for registry "law" `abbrev`s (`…Law`, `claim…`) or rename them to `UpperCamelCase` with deprecated aliases. Rename the remaining non-registry `Prop` definitions. | SR-42 |
| 3.3 | Turn the 449 `abbrev … : Prop` into `def` where nothing relies on reducibility (check with a build); otherwise document why reducibility is needed. | SR-21 |
| 3.4 | Restate the 58 `≥`/`>` statements with `≤`/`<` where that is not a breaking change (new code: always). | SR-44 |

### 6.5 Phase 4 — Performance and metaprograms

| Step | Action | Closes |
|---|---|---|
| 4.1 | Measure the two `maxHeartbeats 1000000` overrides in `CallV2.lean` with `#count_heartbeats`; lower them or remove them, and record the figure. | SR-33 (PF-F1) |
| 4.2 | Measure the 38 `maxRecDepth` settings; scope each with `in` to the declarations that need it; record the figures. | SR-33 |
| 4.3 | EVM macros: write down the contract in each docstring; wrap each step as `first \| (rw …) \| fail "vstep: expected opcode {op} at the current pc"`; replace `simp [*]` with a fixed `simp only` set or a named simp set; replace `rotate_left; rfl; rfl` with named side goals; add `fail_if_success` and `#guard_msgs` tests for a wrong opcode and a wrong jump. Measure one 70-line script before and after. | SR-36, SR-37 |
| 4.4 | Rewrite `frame_tac` without `hygiene false` (§4.5 SR-38) and add a test. | SR-38 |
| 4.5 | `FCA/Meta.lean`: wrap each candidate pair in `withoutModifyingState`/`commitWhen`; narrow the `catch` in `closedDecidesFalse` to the expected exception and keep resource errors; replace `head!`; add a syntax reference to the "malformed" errors. | SR-39, SR-40 |
| 4.6 | Wrap the 304 unguarded `#print axioms` in `#guard_msgs` or remove them, and cut the `#check` noise in the build log (1,199 `#check` in 923 files; 1,544 `info:` lines). | SR-08 |

### 6.6 Verification after every phase

1. `lake build` exits 0, and the warning count does not rise (currently 5, all in the pinned file).
2. `bash audit/2026-10-16-lean-style-review/tools/run_linters.sh OUT 8`: no new sites, and the
   fixture still triggers every enabled linter.
3. Regenerate the axiom audit (`scripts/AxiomAudit.lean` → `docs/latex/axiom_audit.tsv`);
   `check_axiom_budget.py` and `check_no_axioms.py` pass.
4. Run `python3 scripts/audit_lean_proof_style.py --tsv …` and the 0.7 ratchets; each changed
   metric moves only in the right direction.
5. Statement or name changes: regenerate the registry, the claim index and the derived documents
   with the repository's own generators (`scripts/regen.py`, `audit_test_census.py --write`), then
   run the source-only check battery.

### 6.7 Effort and priority overview

| Priority | Items | Rough effort |
|---|---|---|
| P0 (now) | 0.1–0.7 | 1–2 days |
| P1 | 1.1, 1.2, 1.3, 1.4 | 1 week |
| P1 | 1.5, 1.6, 1.7 | 1 week |
| P2 | 2.1–2.5 | 1–2 weeks, by subsystem |
| P2 | 2.6, Phase 4 | 1 week |
| P3 | Phase 3 | Depends on the registry migration; 2–4 days of renames plus the migration window |

---

## 7. Open decisions

| ID | Decision | Owner (suggested) |
|---|---|---|
| D-1 | Keep a second verbatim copy of the guide at `rules/writing-lean-proofs/` (where the request expects it), or point all references at `docs/specs/lean-guide/`. | Standards owner |
| D-2 | Scope of the `show` rule (SR-02): every block, or decision points of load-bearing proofs only. | Standards owner |
| D-3 | Promote `multiGoal`/`show` into the build and gate on warnings (SR-09; LN-F4, LN-F5). | Lint-policy owner |
| D-4 | `Prop`-definition casing and `snake_case` guard/mutant names: rename or record (SR-42, SR-43). | Standards and registry owners |
| D-5 | Restate or annotate the reflexive `*_deterministic` theorems (SR-01). | Venue, GEX and Feeds module owners |
| D-6 | The ASP vault success-characterisation API (SR-14): who owns the new lemmas. | ASP owner |
| D-7 | `maxRecDepth` policy (SR-33). | Lint-policy owner |

---

## 8. Second-pass review: what changed from the first draft

After the first draft, every claim was re-checked against the data and, where possible, against
Lean. These beliefs were revised:

| # | First-draft belief | Second-pass result | Effect on the report |
|---:|---|---|---|
| 1 | The `claim` arm of `simulation_square` contains three duplicated bullets. | Wrong. Two separate excerpts (lines 140–200 and 380–520) had been read as one passage. | Dropped. |
| 2 | 401 definitions lack docstrings (heuristic: no `-/` on the line above). | Wrong. `scripts/lint_lean_docs.py` passes; the heuristic missed docstrings separated by attributes. | Dropped. The project's stricter docstring rule is met. |
| 3 | `set_option hygiene false` in `frame_tac` is probably unnecessary. | Wrong. Removing it breaks `V5/Step/Triples.lean:48`, because the `rfl` patterns become hygienic names. | SR-38 rewritten: load-bearing workaround, untested. |
| 4 | `delta` is used 400 times and `admit` 102 times. | These were identifier counts. In tactic position `delta` is a tactic at 4 sites; `admit` is a project function (as the 2026-10-14 report found). | Counts come from `tactic_heads.py`/`downstream_unfold.py`. |
| 5 | 25 "uninformative" theorem names. | The sample was mostly false positives (`…_key`, `…_main` with a domain meaning). | Dropped. |
| 6 | 346 `def`s violate casing by starting upper-case. | These are mostly type abbreviations (`abbrev Store`) and `Prop`-valued pattern-matching definitions (`def Before : … → Prop`), which are correctly cased. | Dropped. Only `Prop`-valued lower-case definitions remain (SR-42). |
| 7 | `linter.flexible` = 2 means at most 2 non-terminal `simp` sites. | Its blind spot with dotted identifiers was verified by fixture, and two more candidate sites were found. | New SR-10. |
| 8 | 21 top-level `open Classical` are `openClassical` violations. | All 21 are scoped `open … in`; the linter reports 0. | Moved to positives (SR-22). |
| 9 | "Use Mathlib's lemma" for the fold helpers. | `exact?` finds none. A generic local lemma was compiled instead. | SR-06 recommends a shared project lemma. |
| 10 | `wset` duplicates `Function.update`. | Confirmed by compilation (with `DecidableEq Slot`). | Kept (SR-19). |
| 11 | Build timings rank the slow modules. | Lake printed timing lines only for modules with output (1,058 of 9,088 jobs), and the guide warns against Lake's per-module figure. | Not used. SR-34/SR-36 call for `#count_heartbeats` instead. |
| 12 | "32 proofs over 150 lines." | The project script's 32 includes `def`s (test-suite data tables). Theorems alone: 5 of 150 lines or more, 11 of 100 or more, 85 of 50 or more. | Figures corrected (SR-03). |
| 13 | "13 vacuous theorems, none acknowledged." | 3 already carry an explicit tautology note. Of the other 10, 2 are aliases of the Venue originals. | SR-01 counts 3 + 10 and names each. |
| 14 | `multiGoal`/`show` = 0 was known. | Known only for the files edited on 2026-10-15. This review measured all 1,054 modules. | SR-09 now supplies the full-tree evidence for LN-F5. |
| 15 | Duplicate statements: 380 groups. | 257 are the deliberate AgentHandoff ↔ HandoffV3 regression pin. Of the other 123, aliases by reference are legitimate. | SR-06 splits the groups into (a), (b) and (c). |
| 16 | The FCA attribute `load_bearing` marks the load-bearing theorems. | In this repository `load_bearing` means an FCA *tooth* (a refutation certificate), not "load-bearing" in the sense of this review. | Not used to select the corpus. |

Omissions checked in the second pass (all five documents, section by section):
* **`SKILL.md`.**
  * Workflow steps 1–4: covered (SR-02, SR-04, SR-07, SR-09).
  * Extraction ladder: covered (SR-03, SR-05, SR-06).
  * Each quick-reference row:
    * missing API: SR-04, SR-14, SR-15;
    * terminal/non-terminal `simp`: SR-23, SR-24;
    * focusing: SR-26;
    * `show` honesty: SR-30;
    * `set_option`: SR-33;
    * simp-normal form / `<`: SR-18, SR-44;
    * golfing: SR-32;
    * `Fact`: SR-22;
    * naming: SR-41 to SR-45;
    * search by shape: SR-06;
    * one tactic per line: SR-29;
    * axiom gate: SR-07, SR-08;
    * numeral spelling: SR-18;
    * `simp?` per site: SR-23 (the 2026-10-15 report derived every list with `simp?`; no new
      squeezed lists were added since);
    * heartbeats: SR-33;
    * `maxDischargeDepth`: no site, so no finding;
    * custom linters: SR-12.
  * Rationalizations: SR-01, SR-02, SR-10.
* **`library-design.md`.**
  * Spec-driven development: a statement-first culture is visible, with no `sorry` committed.
  * Statements as interface: SR-01.
  * API in the same file: SR-13, SR-16.
  * Abstraction boundaries: SR-21.
  * Optimised reference: SR-22, SR-35.
  * Simp-normal form: SR-18.
  * Junk values: SR-22.
  * Bundling: SR-17, SR-20. There are no morphisms or subobjects, so `FunLike`/`SetLike` do not
    apply.
  * Restraint and `Fact`: SR-22.
  * Abstraction level: SR-19.
* **`proof-style.md`.**
  * Skeleton first: not observable in committed code. The notes (LD-F2) record it as a drafting
    method.
  * `calc`: SR-25.
  * `have`/`suffices`: SR-25, SR-28.
  * `show`: SR-02, SR-30.
  * Focusing: SR-26.
  * One tactic per line: SR-29.
  * `simp` discipline: SR-23, SR-24, SR-31; `simp ↓` and `maxDischargeDepth`: no site.
  * Decisions and routine: SR-02, SR-27.
  * Golfing: SR-32.
  * Splitting: SR-03.
* **`performance.md`.**
  * Measure per declaration: SR-33, SR-36.
  * Heartbeat claims: SR-33.
  * Lazy probes: not applicable, as no probe tooling exists.
  * Kernel replay: SR-34.
  * Reduction paths and accumulators: SR-36. No left-nested `++` fold was found in the corpus.
  * Readable reference: SR-35.
  * Working habits: §6 keeps performance work in its own phase (Phase 4), as the guide asks.
* **`tactics.md`.**
  * Extension point: SR-37.
  * Contract: SR-37.
  * Normalisation and transparency: SR-39 (default-transparency `whnf`).
  * Transactional state: SR-39.
  * Failures: SR-37, SR-40.
  * Bounded search: no unbounded loop was found. The FCA loops are bounded by array sizes.
  * Tracing: SR-40.
  * Generated syntax: SR-38.
  * Structure for change: SR-37.
  * Failure-surface tests: SR-37, SR-38.
  * The review checklist was applied to all metaprograms in §3 (#18–#21).

---

## Appendix A — Theorems of 50 lines or more (85)

The full table with per-declaration counts is generated by `tools/style_metrics.py` into
`data/decls.tsv` (filter: `kind ∈ {theorem, lemma}`, `lines ≥ 50`). Top 20:

| Lines | Declaration | `·` | `show` | `have` (typed) | `unfold` | `rename_i` |
|---:|---|---:|---:|---|---:|---:|
| 362 | `Fame/Operator/Refinement.lean:47` `simulation_square` | 127 | 0 | 24 (18) | 0 | 8 |
| 208 | `Fame/Evm/Full/Gas.lean:110` `entry_gas_le` | 94 | 0 | 10 (0) | 0 | 0 |
| 197 | `Fame/Evm/Full/Gas.lean:323` `entry_never_fails` | 94 | 0 | 10 (0) | 0 | 0 |
| 174 | `ASP/Phase7/LedgerCap.lean:293` `Step.totalDeposits_mono` | 8 | 0 | 0 | 14 | 0 |
| 152 | `ASP/Phase7/Frame.lean:413` `price_reference_is_written_only_by_settlement_and_seed` | 0 | 0 | 0 | 12 | 0 |
| 141 | `ASP/WholeContract/GreenInv.lean:161` `stepV2_inv` | 30 | 0 | 12 (2) | 5 | 0 |
| 114 | `FCA/WeightedOptimality.lean:269` `levelled_le_greedy_nat` | 18 | 3 | 33 (23) | 0 | 0 |
| 112 | `SWC/Escrow.lean:761` `attributed_preserved` | 14 | 0 | 8 (7) | 0 | 0 |
| 104 | `Fame/Operator/Refinement.lean:429` `concreteStep_defined` | 16 | 0 | 21 (19) | 0 | 9 |
| 104 | `Venue/NoCross.lean:200` `submit_leaves_the_book_uncrossed` | 18 | 0 | 21 (19) | 1 | 0 |
| 101 | `Fame/Evm/Full/ExecDispatch.lean:27` `run_unknown_selector` | 0 | 13 | 1 (1) | 0 | 0 |
| 99 | `Venue/Engine.lean:478` `step_preserves_wf` | 31 | 0 | 13 (10) | 4 | 0 |
| 95 | `Fame/Evm/Full/Refine.lean:523` `simulation_square_fill` | 6 | 4 | 18 (16) | 0 | 0 |
| 91 | `GEX/Match/PriorityLaw.lean:159` `exists_bump_of_crossed` | 26 | 0 | 20 (11) | 0 | 0 |
| 91 | `SWC/Invariants.lean:394` `window_preserved` | 24 | 0 | 8 (8) | 0 | 8 |
| 84 | `Fame/Evm/Full/Refine.lean:407` `simulation_square_release` | 2 | 1 | 22 (18) | 0 | 0 |
| 82 | `BoundedLevelCeiling.lean:284` `jointCeiling_pair` | 7 | 0 | 19 (17) | 0 | 0 |
| 81 | `IndependentBlocks.lean:200` `exists_block_split` | 18 | 0 | 20 (17) | 0 | 0 |
| 80 | `ASP/Properties.lean:312` `exec_simple_fields` | 8 | 0 | 8 (8) | 0 | 0 |
| 79 | `AnnualizedYieldBracket.lean:694` `apy_hypotheses_are_satisfiable` | 9 | 0 | 17 (16) | 7 | 0 |

(`show` counts include `show … from` terms. All paths are under `RequestProject/`.)

## Appendix B — Reflexive theorems (`A = A`)

| File:line | Name | Acknowledged in docstring |
|---|---|---|
| `RequestProject/Fame/Flywheel/Capacity.lean:52` | `systemicCapacity_has_no_individual_account_term` | yes |
| `RequestProject/Fame/LMM/Theorems.lean:174` | `toxic_flow_signal_is_account_blind` | yes |
| `RequestProject/Fame/LMM/Theorems.lean:292` | `lmm_clears_through_same_system` | yes |
| `RequestProject/Feeds/Create2.lean:42` | `create2_address_deterministic` | no (and claims nonce independence) |
| `RequestProject/Feeds/SyntheticIndex.lean:36` | `synthetic_index_deterministic` | no |
| `RequestProject/GEX/Match/Obligations.lean:94` | `clearTie_det` | no |
| `RequestProject/MatchingPriority/PriceTime.lean:104` | `priceTime_replay_deterministic` | no |
| `RequestProject/Venue/DisciplineScope.lean:97` | `di_match_deterministic` (alias) | no |
| `RequestProject/Venue/DisciplineScope.lean:144` | `di_replay_deterministic` (alias) | no |
| `RequestProject/Venue/Engine.lean:331` | `step_deterministic` | no |
| `RequestProject/Venue/Engine.lean:655` | `replay_deterministic` | no |
| `RequestProject/Venue/Instrument.lean:229` | `settlePrice_deterministic` | no |
| `RequestProject/Venue/Matching.lean:320` | `matchOrder_deterministic` | no |

## Appendix C — `replay_append` copies

`DetSim/Trace.lean:121`, `AgentHandoff/Replay.lean:24` (pin), `HandoffV3/Obligations/Replay.lean:26`,
`HandoffV3/Proofs/Merge.lean:32` (duplicate of the previous one), `RequestProject/DetSim/Log/Core.lean:167`,
`RequestProject/Fame/Token/Invariants.lean:469`, `RequestProject/Venue/Engine.lean:659`,
`RequestProject/Venue/DedupSnapshot.lean:164`, `RequestProject/MatchingPriority/ReferenceEngine.lean:102`,
`RequestProject/Fame/POL/SuiteJournal.lean:97` (states the singleton case; misnamed, SR-44),
`docs/design/evidence/SigningReviewLemmas.lean:99`.

## Appendix D — Measurements at a glance (2026-10-16)

| Measure | Value | Source |
|---|---:|---|
| Tracked `.lean` files / lines | 1,088 / 333,803 | `audit_lean_proof_style.py` |
| Build jobs / warnings / `info:` lines | 9,088 / 5 / 1,544 | full `lake build` |
| Library modules linted / elaboration failures | 1,054 / 0 | `run_linters.sh` |
| `sorry` / `axiom` / `@[implemented_by]` / `erw` / `irreducible` / global `Fact` | 0 / 0 / 0 / 0 / 0 / 0 | text audit |
| `native_decide` / `decide +kernel` | 122 / 1,148 | text |
| `rfl` after `simp` / after `rw` (heuristic) | 7 / 197 | text audit |
| Untyped `have` (heuristic upper bound) | 2,352 | text audit |
| Tactic-position counts: `have` 7,573; `rw` 6,309; `simp` 4,949; `simp only` 3,648; `unfold` 2,135; `omega` 1,362; `simp_all` 470; `grind` 302; `show` 200; `calc` 141; `suffices` 10; `aesop` 2 | — | `tactic_heads.py` |
| `·` blocks / opening with `show` / with `change` | 6,952 / 3 / 41 | text |
| `rename_i` / `at *` / `<;> try` | 147 / 155 / 8 | text |
| `@[simp]` / `@[ext]` / structures | 435 / 5 / 1,051 | text |
| `abbrev` (of which `: Prop`) | 736 (449) | text |
| `set_option maxHeartbeats` (scoped) / `maxRecDepth` unscoped / scoped | 2 / 38 / 6 | `data/options.tsv` |
| Metaprogram commands: `macro` 35, `syntax` 21, `elab` 19, `run_cmd` 19, `initialize` 10, `macro_rules` 4, `declare_syntax_cat` 3, `run_meta` 2 | — | `data/meta.tsv` |

## Appendix E — Reproducing this review

```bash
# text measurements (≈1 min)
python3 scripts/audit_lean_proof_style.py --tsv /tmp/lean_style.tsv
python3 audit/2026-10-16-lean-style-review/tools/style_metrics.py
python3 audit/2026-10-16-lean-style-review/tools/tactic_heads.py
python3 audit/2026-10-16-lean-style-review/tools/downstream_unfold.py
python3 audit/2026-10-16-lean-style-review/tools/duplicate_statements.py
# build, then every library module through the guide's linter profiles (≈1.5 h at 8 jobs)
lake build
bash audit/2026-10-16-lean-style-review/tools/run_linters.sh /tmp/lint 8
# vacuity anchor and blind-spot fixtures (copy to .lean first)
cp audit/2026-10-16-lean-style-review/tools/LinterTriggerFixture.lean.txt /tmp/T.lean
lake env lean -Dweak.linter.flexible=true -Dweak.linter.style.multiGoal=true \
  -Dweak.linter.style.show=true -Dweak.linter.style.openClassical=true /tmp/T.lean
cp audit/2026-10-16-lean-style-review/tools/FlexibleBlindSpotFixture.lean.txt /tmp/F.lean
lake env lean -Dweak.linter.flexible=true /tmp/F.lean
# kernel spot check of the load-bearing theorems
cp audit/2026-10-16-lean-style-review/tools/AxiomSpotCheck.lean.txt /tmp/A.lean
lake env lean /tmp/A.lean
```

The fixtures are stored as `.lean.txt` so that they are not tracked Lean sources. This keeps the
repository's file-count based checks unchanged.

Files in `data/`:
* `decls.tsv`, `tactics.tsv`, `tactic_heads.tsv`, `names.tsv`, `options.tsv`, `meta.tsv`,
  `refs.tsv`;
* `unfold_sites.tsv`, `duplicate_statements.tsv`;
* `linter_sites.tsv`, `linter_rc.list`, `linter_outputs/` (raw output for the modules with
  warnings).
