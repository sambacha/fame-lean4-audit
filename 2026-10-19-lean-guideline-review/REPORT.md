# `RequestProject/**` against the `writing-lean-proofs` guide — review, fixes, measurements (2026-10-19)

Scope: every Lean file under `RequestProject/` (1,001 modules, 314,884 lines), reviewed against the
guide supplied on 2026-10-19 (`SKILL.md`, `proof-style.md`, `library-design.md`, `performance.md`).
The guide is already the project's adopted rule set (`docs/standards/LEAN_GUIDE.md`,
`docs/standards/LEAN_PROOF_STYLE.md`), so this review checks the tree against it and records
departures. It does not restate the rules. Priority, as requested: performance first, then tactic
usage. Working notes, taken line by line while reading the guide and kept during the work, are in
`NOTES.md`. Raw data is in `raw/`; every number below cites a file there.

Evidence labels: **[measured]** (A/B on this host, file cited), **[static]** (read from the source),
**[estimated]** (derived; the derivation is given).

## 0. Summary

| # | Change (one commit each) | Rule of the guide | Before → after (median wall) | Speed-up |
|---|---|---|---|---|
| I1 | `Venue/SeamCorpus.lean`: all seven corpus measurements decided in **one** kernel pass | performance.md "count reduction paths"; library-design "statements are the interface" | 287.5 s → 147.8 s | **1.95×** [measured] |
| I2 | `ASP/Phase7/CallV2.lean`: 11-way `split_ifs` replaced by a clause-wise `settleGuardsV2_eq_none_iff`; **both `maxHeartbeats 1000000` overrides removed** | "every `maxHeartbeats` override is an unproven claim"; extraction ladder rung 2 | 47.4 s → 7.8 s (CPU 84.2 → 7.9 s) | **6.1×** wall, **10.7×** CPU [measured] |
| I3 | `Audit/NumericFootprint`, `Audit/ReviewFindings`, `PaperTests/CoverageSnapshot`, `FCA/Meta`: `EnvironmentHeader.moduleNames` read once per scan instead of once per constant | performance.md "measure, find where cost actually comes from" | NumericFootprint 237.7 → 16.5 s; ReviewFindings 246.5 → 13.6 s; PaperTests.Runner 246.6 → 14.7 s | **14–18×** [measured; interleaved user-CPU A/B 241.2 → 13.5 s = 17.9×] |
| I4 | `scripts/AxiomAudit.lean` (CI post-build generator, outside `RequestProject/`): the same hoist | as I3 | 1,865 s → 1,627 s, output byte-identical | 1.15× (**one run per side: indicative only**) |

No theorem statement or existing name changed. One theorem was added in I1 (`corpus_measurements`),
and two lemmas in I2 (`ite_some_eq_none_iff`, `settleGuardsV2_eq_none_iff`). Together the five
modules went from 1,066 s to 200 s of serial wall time [measured, sum of medians]. The whole-build
effect is in §6.

## 1. Method

* **Hotspot ranking.** A full `lake build RequestProject` (995 project modules rebuilt). Its log
  gives one job time per module, under 8-way contention (`raw/module_times_before.tsv`): the sum of
  all job times is 15,139 s, and the 68 modules over 30 s account for 7,225 s (48 %).
* **Attribution.** `lake env lean -Dtrace.profiler=true` on each of the top 20 modules, one serial
  run each, used to classify where the time goes and not as an A/B
  (`raw/profile_top_modules.tsv`, `raw/declaration_costs_profile.tsv`).
* **A/B protocol.** Serial runs on one host, prebuilt dependencies, 3 before and 3 after; the spread
  is reported. I3 was also re-run **interleaved** (before/after alternating), recording user CPU
  (`raw/numericfootprint_interleaved_ab.txt`). All raw rows: `raw/ab_measurements.tsv`.
* **Correctness gates per change.** The module compiles with no new warning, `#guard_msgs` outputs
  are unchanged, and dependants build (full build in §6).

### 1.1 Measurement facts established on the way (they change how profiles must be read)

| Fact | Evidence |
|---|---|
| **M1. `decide +kernel` checks inside one file run one after another.** One theorem: 8.5 s; three identical ones: 22.2 s, with user ≈ wall. | `raw/ab_measurements.tsv` rows M1 [measured] |
| **M2. `trace.profiler`'s `[Elab.async]` times are cumulative**, so each declaration's own cost is the difference from the previous entry. Read naively, the six SeamCorpus proofs appeared to cost 663 s; their real sum is about 282 s. | M1 together with `raw/declaration_costs_profile.tsv` |
| **M3. Tactic proof bodies *do* run in parallel** (CallV2: user 84 s over 47 s of wall), so M1 applies to kernel reduction, not to every proof. | rows I2 |
| **M4. `[Elab.command]` times of commands that read the checked environment include time spent waiting for earlier kernel checks.** `#detsim_runtime_checked` (233.6 s in the profile), the `example` in `Fame/Evm/Full/Selectors` (190 s) and the `structure` in `Governance/SupplyManifest` (118.8 s) are mostly waiting; `DetSim/Tiers.lean` does constant-time work. Such entries need a direct in-process timer before they count. | `raw/declaration_costs_profile.tsv`; `DetSim/Tiers.lean:101` [static] |
| **M5. `#count_heartbeats in` under-reports asynchronously elaborated proofs.** It printed "27" for `settleGuardsV2_none_imp`, which times out at the default 200,000 when compiled with `set_option maxHeartbeats 200000 in`. Compile at the budget instead of trusting the counter. | `NOTES.md` [measured] |
| **M6. Kernel reduction is cached inside one declaration, not across declarations.** Fusing two checks over the same 50 cases: 76.6 s net → 52.6 s net (−31 %, spread ≤ 3.1 s). | rows F1 [measured] |

## 2. Performance findings and fixes

### I1 — SeamCorpus: one kernel pass instead of seven  [measured, applied]

*Diagnosis.* Six `decide +kernel` theorems each re-reduced, for 1,000 cases, the clearing, the ledger
(`Ledger.bookAll`), the account list (`List.dedup`) and the emitted batch (`emit`, two
`bucketSum` scans per account) before testing their own predicate. Own costs, from the cumulative
trace (M2): boundary 18.4, one-sided 1.8, fifty 54.7, fifty-one 50.3, executions 17.5,
preflight 138.9 s. Because of M6, each theorem paid again for work the others had already done.

*Fix.* `corpus_measurements` states the seven facts as one conjunction and is closed by a single
`decide +kernel`. The seven original theorems keep their names and statements and are now its
projections (`corpus_measurements.2.2.1`, …). This is a proof-body change plus one theorem;
statements are untouched.

*Result.* 296.0/287.5/286.9 s → 151.0/147.8/146.9 s, median **−139.7 s (−48.6 %)**.

*Further gain measured but not applied (owner decision Q3/D2, §7).* A kernel-friendly duplicate
filter (`dedupLast`, keeping the last occurrence just like `List.dedup`) cut the preflight check over
the 50 fifty-account cases from 54.5 s to 48.5 s. The two per-account `bucketSum` scans
(`netCash`/`netFee`) account for most of the rest; the cost lies in instance unfolding through
`List.sum`/`foldr` and `Int` constructor matching (correction in §8). Getting that gain means a
fast form of `accounts`/`emit` next to the reference definitions, with an equality theorem
(library-design "Optimized definitions keep a readable reference").

### I2 — CallV2: two `maxHeartbeats 1000000` overrides, both unnecessary  [measured, applied]

*Diagnosis.* `settleGuardsV2_none_imp` and `settleGuardsV2_none_unsettled` each did
`unfold; split_ifs` across 11 guard clauses, then tried two closers on all 12 branches. With the
override removed, each times out at the default budget, and each took about 60 s (cumulative trace).

*Fix (extraction ladder rung 2).* Two lemmas:
`ite_some_eq_none_iff : (if c then some a else x) = none ↔ ¬c ∧ x = none` (searched first: `exact?`
over Mathlib found nothing), and `settleGuardsV2_eq_none_iff`, which states clause by clause when the
composed guard passes. Its proof is `rw [settleGuardsV2]` followed by one squeezed `simp only`
(derived at its own site; no unused-argument warning). Both theorems are now one-line projections.
Both `set_option maxHeartbeats` lines are gone; the file has no override left.

*Result.* wall 48.8/47.4/46.9 → 8.2/7.8/7.7 s; CPU 84.2 → 7.9 s. The new iff lemma is also a reusable
API lemma for `settleGuardsV2` (library-design "every definition ships its API").

### I3 — `env.header.moduleNames` inside per-constant loops  [measured, applied]

*Diagnosis.* The profile put 234 s of `Audit/NumericFootprint` on one `run_cmd`. My first hypothesis,
that every axiom collection starts from an empty visited-set, was **refuted** by in-process timers:
53 collections take 3.0 s. The enumeration takes 222.3 s. `EnvironmentHeader.moduleNames` is not a
field; it is `header.modules.map (·.module)` (Lean 4.28 `Lean/Environment.lean:203`), an array
rebuilt over every imported module on each call, and the loops called it once per theorem of a
709,000-constant environment. The same loop without that call takes 0.53 s; reading the module's
own constant list takes 6 ms. The generated C confirms where the call sits: before the fix,
`l_Lean_EnvironmentHeader_moduleNames` is called inside the `forIn` loop specialisation; after it,
the call is in the enclosing functions (`numericTheorems`, `checkRejectedInductives`,
`surfaceTheorems`, `writeCensus`). So the compiler did not move the hoisted value back into the loop.

*Fix.* `let moduleNames := env.header.moduleNames` once before each loop (4 files; same data, same
order, so obviously equivalent). Every `#guard_msgs` output is unchanged.

*Result.* NumericFootprint 237.7 → 16.5 s (interleaved user CPU 241.2 → 13.5 s, 17.9×);
ReviewFindings 246.5 → 13.6 s (18.2×); PaperTests.Runner (through `CoverageSnapshot`)
246.6 → 14.7 s (16.8×). `FCA/Meta.writeCensus` runs only when invoked, so it was not timed.

*Same pattern outside `RequestProject/` (not changed; scope):* `DetSim/Audit.lean:35,71`,
`HandoffV3/Audit.lean:30`, `AgentHandoff/Audit.lean:31` (frozen directory),
`scripts/AxiomAuditMemo.lean:204`,
`scripts/DeclarationNames.lean:933`, `scripts/ICACensus.lean:1005`,
`scripts/NativeDecideTcb.lean:72`, `audit/2026-10-17-lean-profiling/tools/ProfEnv.lean:137,143`.
Each is a one-line hoist and should get its own A/B (the axiom-audit scripts are run by CI).
`Production/AbsorptionV2Toolchain.lean:115` reads it once, outside any loop, and is fine.

### I4 — the axiom-audit generator  [measured once per side, applied]

`scripts/AxiomAudit.lean:863` had the I3 loop. With the hoist, the regeneration took 1,627 s
against 1,865 s before, and its output is **byte-identical** to the pre-hoist run (`cmp`). With one
run per side this is indicative only. It also shows that `moduleNames` is a small share there: the
remaining ≈ 1,600 s goes to one fresh `CollectAxioms` traversal per theorem (24,984 theorems). The
repository already contains a memoized variant, `scripts/AxiomAuditMemo.lean`. Switching CI to it,
or sharing the visited-set while keeping per-theorem results, is the real lever. It was not evaluated
here.

### Remaining hotspots, classified (not changed)

From `raw/declaration_costs_profile.tsv`: own cost per declaration, one serial profile run.

| Module | Largest own costs | Class | Lever | Status |
|---|---|---|---|---|
| `Fame/Testing/SeedStability` | `seed_stability_accepted` 222.5 s | kernel suite acceptance | definition fast form + equality theorem | Q3/D2 owner approval |
| `Fame/Testing/TokenCompositionTests` | `venue_composition_suite_accepted` 157.2 s, `corpus_exercises_many_refusal_reasons` 26.1 s | kernel | fusion (as in I1) or fast form | candidate |
| `Fame/Testing/LMMGovernanceTests` | accepted 93.1, `governance_corpus_reaches_every_branch` 36.0, `quote_corpus…` 17.2 s | kernel, same corpus | **fusion (M6)** | strongest next candidate |
| `Fame/Testing/LMMTests` | accepted 71.1, two `*_corpus_reaches_every_branch` 28.1 + 27.9 s | kernel, same corpus | **fusion (M6)** | candidate |
| `Fame/Testing/TokenLedgerTests` | accepted 82.6, `token_prefix_check_catches_dust_leak` 33.2 s | kernel | fusion | candidate |
| `Fame/Testing/POLSuiteRiskTests` | accepted 76.7 s plus five 13–20 s corpus checks | kernel | fusion | candidate (critical path, prior audit §12.3) |
| `EnclosureTightness` | 80.9, 67.1, 27.3, 26.3, 22.3 s | kernel, mostly different mutants | fusion shares little | low |
| `Fame/Workflow/DivergenceRate` | 53.8, 33.1, 31.5 s | kernel | fusion | candidate |
| `Fame/Evm/Full/Exec*` | 1–11 s each, many declarations, parallel (user ≈ 2.5 × wall) | elaboration | per-declaration measurement first | low |
| `DetSim/Conformance` | kernel 45.3 + 22.7 + 22.7 s; the 233.6 s command is waiting (M4) | kernel | fusion | candidate (critical path) |

**[estimated]** If fusion gives the 31 %–49 % that M6 and I1 measured, the five "fusion" rows
(about 700 s of own kernel time in the profile) would drop by roughly 220–340 s of job time. Each
one needs its own A/B before this is believed.

## 3. Tactic-usage review (whole tree)

Counts come from `scripts/audit_lean_proof_style.py` (text heuristics, comments removed; run
2026-10-19) and `rg` [static].

| Rule | State | Finding |
|---|---|---|
| No unscoped `maxHeartbeats` / debug options | **0 unscoped**; the last 2 scoped overrides were removed by I2 | Conformant. Tree-wide `maxHeartbeats` overrides: **0** |
| Unscoped budgets in general (spirit of `linter.style.setOption`) | **38 file-level `set_option maxRecDepth`** (e.g. `Venue/TaskRegister.lean:69` and `Venue/Obligations.lean:46` at 1,000,000; `DetSim/Applied/EngineModelSuite.lean:44`, `DetSim/Falsification.lean:281`, `ASP/Phase7/Meaning.lean:82`, `ASP/Phase11/Meaning.lean:99`, `ASP/Phase4/KeccakVectors.lean:21` at 100,000), plus 6 already scoped with `in` | The linter does not cover `maxRecDepth`, but the guide's reasoning does: an unmeasured file-wide budget given to every later declaration. Recommendation: scope each to the declarations that need it, found by bisection, and add `maxRecDepth` to LP5's ratchet |
| Terminal `simp` unsqueezed; non-terminal squeezed | `nonterminal_simp` = **0**; `linter.flexible` held at 0 by the repository's ratchet | Conformant. The I2 `simp only` is non-terminal-style (it closes after a `rw`) and was derived at its own site |
| `erw` / trailing `rfl` (missing-API smell) | `erw` 0; `trailing_rfl_simp` **7** (`DetSim/Log/Tagless.lean:199`, `DetSim/Log/TaglessLog.lean:64`, `Fame/Foundation/Numeric.lean:114,127,138`, `Venue/IntakeExport.lean:231`, `HandoffV3/Obligations/QuantPolicyV2Tests.lean:224`); `trailing_rfl_rw` 201 (informational) | The 7 are candidates for an equation lemma; `Numeric.lean` has three sites on one definition, which the repository's own rule names as the trigger |
| `show … from rfl` | 68 sites in 21 files; 26 in `Fame/Evm/Full/Refine.lean`, 8 in `Fame/Evm/Observe.lean` | Same smell. `Refine.lean` wants `@[simp]` projection lemmas next to its definitions |
| Downstream `unfold` | 1,824 uses in 408 files; highest: `V5/Match/Batch.lean` 23, `Fame/Testing/CampaignRecord.lean` 21, `Sim/Properties.lean` 20, `ASP/PStar/Window.lean` 20 | Many are next to the definition (allowed). I2 shows the alternative: one characterisation lemma. Big guard chains still proved by `unfold; split_ifs`: `ASP/Phase10/Intake.lean:322` (9 clauses, module 31 s), `ASP/Phase7/BatchInvariants.lean:71` (8, 24 s), `ASP/Phase6/Adapter.lean:191` (8, 13 s), `ASP/Lemmas.lean:268` (7, 9.4 s): the same treatment applies, unmeasured |
| Typed `have` | `untyped_have` 2,406 (heuristic upper bound) | Repository position: not a gate (R7). Unchanged |
| Focused goals / honest `show` | `multiGoal`, `show` linters promoted, held at 0 | Conformant |
| Long proofs | 30 declarations over 150 lines in 24 files (e.g. `TestingPlan.lean:631`, `Venue/Obligations.lean:140`, `Venue/TaskRegister.lean:111`) | Review candidates (R13), not violations |
| Trust footprint | `native_decide` 122 uses in 44 files (the axiom audit is authoritative) | `EnclosureTightness.soundness_and_tightness_are_both_needed` proves its second conjunct with `native_decide` although it is already kernel-proved as `tightness_is_load_bearing`. The theorem's axiom set stays the same (the first conjunct still needs compiled evaluation), so this only removes one redundant compiled evaluation. Trust policy is an owner decision (Q4) |
| Wholesale `import Mathlib` | 36 files with the bare line (84 god-importers by the prior audit) | Known; prior audit F1/F2 narrowed 6. Ranked by CPU saved there |
| `autoImplicit` boilerplate | 578 `set_option autoImplicit false` + 318 `relaxedAutoImplicit` lines | One `autoImplicit = false` in `[leanOptions]` would replace them; not a performance issue |

## 4. Second pass — additional findings

1. **Profile-reading traps (M2, M4, M5)** apply to the earlier profiling audit
   (`audit/2026-10-17-lean-profiling`): its Layer-2 heartbeat figures come from `#count_heartbeats`
   sentinels, and M5 shows that counter can under-report asynchronously elaborated proofs. Its
   kernel-time attribution should be checked against direct timers before being re-used.
2. **`#count_heartbeats` is not usable as the "measure before believing" tool for theorem bodies
   on this toolchain** (M5). The workable probe is compiling with `set_option maxHeartbeats N in` at
   the candidate budget, or an in-process timer.
3. **I3's class of bug is invisible to every existing gate.** It is meta-code cost, not kernel or
   tactic cost. A text check for `header.moduleNames[` inside a `for` over `env.constants` would have
   caught all 16 sites (§5 R2).
4. **The `split_ifs` guard-chain pattern** (I2) has four more sites (§3); they cost 9–31 s per
   module, so the gain is smaller, but the iff lemma is better API in every case.
5. **SeamCorpus `familyKeys_nodup`, `corpus_names_eq`** were already written the good way
   (general lemmas plus small reductions) and needed no change; this is the pattern to copy for the
   suites in §2.
6. **`#detsim_runtime_checked` at the end of a suite file does no work of its own**, but it is where
   the file's wait for kernel checks shows up in the profile (M4). Moving it would not save time.
7. **The committed axiom audit was not reproducible** (duplicate `gexPlus.eq_1` row, §6.1),
   probably because it was assembled from partial runs (the script header describes merging partial
   runs in Python). A merge step should deduplicate by `(name, module)` the same way a full run does.
8. **The axiom-audit script itself had the I3 pattern** (`scripts/AxiomAudit.lean`, one
   `moduleNames` rebuild per theorem). Its run took 1,865 s here. See I4.

## 5. Recommendations (in impact order)

| # | Recommendation | Expected effect | Needs |
|---|---|---|---|
| R1 | Fuse the per-suite kernel theorems that reduce the same corpus (LMMGovernance, LMM, TokenLedger, POLSuiteRisk, DivergenceRate, DetSim.Conformance), one commit and one A/B each | 31–49 % of each module's kernel time [estimated from M6/I1] | proof bodies plus one theorem each (within Q3 as applied in I1) |
| R2 | Make the CI axiom audit memoized (`scripts/AxiomAuditMemo.lean` exists) and hoist `moduleNames` in the 10 remaining sites outside `RequestProject/`; add a text gate for the pattern | the audit spends ≈ 1,600 s on per-theorem traversals (I4) | A/B with a byte-identical output check, as in I4 |
| R3 | Kernel-friendly fast forms of `Venue.Seam.accounts`/`emit` next to the reference definitions, with equality theorems | preflight portion −11 % measured for `dedupLast` alone; `bucketSum` is the larger share | owner decision D2 |
| R4 | Scope the 38 file-level `maxRecDepth` budgets; extend LP5 to cover them | hygiene; makes cost visible | bisection per file |
| R5 | `_eq_none_iff` lemmas for the four remaining `split_ifs` guard chains | small speed-up, better API | — |
| R6 | Equation lemmas for the 7 `trailing_rfl_simp` sites and `Refine.lean`'s 26 `show … from rfl` | readability and robustness | — |

## 6. Whole-build effect

Two full rebuilds of `RequestProject` (all 1,001 project modules; Mathlib already built; 8-way
contention), before and after the three changes. Figures are Lake job times per module
(`raw/module_times_before.tsv`, `raw/module_times_after.tsv`; after-build log
`raw/build_after.log.gz`).

| Group | Before Σ job (s) | After Σ job (s) | Δ |
|---|---|---|---|
| The 7 edited modules (SeamCorpus, CallV2, NumericFootprint, ReviewFindings, PaperTests.Runner, CoverageSnapshot, FCA.Meta) | 1,263 | 294 | **−970 s (−77 %)** [measured] |
| The 994 unchanged modules | 13,876 | 14,299 | +423 s (+3.1 %): run-to-run variation; the prior audit measured 201–253 s for unchanged groups (its §11.1) |
| All 1,001 | 15,139 | 14,593 | −547 s |

Per module, in-build (contended): SeamCorpus 376 → 233 s, CallV2 57 → 7.3 s, NumericFootprint
327 → 15 s, ReviewFindings 247 → 13 s, PaperTests.Runner 244 → 12 s.

* **CPU [estimated].** −970 s of job time at CPU/job ≈ 0.91 (prior audit §11.2) ≈ **−880 s of CPU**,
  about 8 % of a full project build's CPU (≈ 11,300 s on the prior audit's round-3 host).
* **Wall [estimated].** The before-build's wall time was not recorded, so there is no measured wall
  A/B. The after-build took 2,101 s. Using the prior audit's throughput model (Δwall ≈ ΔCPU ÷ 6.5–6.7
  busy cores) gives ≈ **−130 to −135 s** (about 6 %). Two of the fixed modules sat in the
  drain the prior audit identified (`PaperTests.Runner` ended one run's gating chain at 143 s;
  `Audit.*` and SeamCorpus were 240–376 s single jobs). Removing them shortens the tail, so the real
  wall gain may be larger than the throughput estimate; a co-located before/after pair of clean
  builds is needed to measure it.
* **Gates on the after-tree:** build exit 0, 9,040 jobs, **0 warnings** in the log;
  `check_promoted_linters.py --log` pass; `check_lean_lint_options.py` pass; `generate_counts.py
  --check` and `audit_doc_currency.py` pass (counts updated for +40 lines, +3 theorems, +2 documents);
  `#print axioms` on every changed or added theorem gives only standard axioms; the axiom-audit
  regeneration, including six rows that changed, is in §6.1.

### 6.1 Axiom audit regenerated (`lake env lean scripts/AxiomAudit.lean`, exit 0, 24,984 theorems)

Diff against the committed `docs/latex/axiom_audit.tsv` (16 lines):

* **+3 rows**, the added theorems: `ASP.Vault.ite_some_eq_none_iff` (`propext`),
  `ASP.Vault.settleGuardsV2_eq_none_iff` (`propext, Quot.sound, Classical.choice`),
  `Venue.SeamCorpus.corpus_measurements` (`propext, Quot.sound`).
* **6 changed rows, all in `RequestProject.Venue.SeamCorpus`: an I1 trade-off.**
  `corpus_empty_count`, `corpus_boundary_count`, `corpus_one_sided_count`, `corpus_fifty_count`,
  `corpus_fifty_one_count` and `corpus_reaches_executions` went from `propext` to
  `propext, Quot.sound`. They are now projections of the fused conjunction, which includes the
  preflight conjunct; that conjunct already carried `Quot.sound` (`corpus_preflight_all`, unchanged
  row). Both axioms are in the allowed footprint (`check_axiom_budget.py`), and no compiler-trust
  axiom appears. `check_axiom_audit_fresh.py --review <original TSV>` passes with `--allow-module` for exactly the three modules this work touched or that held the duplicate: `RequestProject.Venue.SeamCorpus`, `RequestProject.ASP.Phase7.CallV2` (2 new rows) and `RequestProject.GEX.FixedPoint.Conjectures`; without any one of them it fails, as designed. If the
  narrower footprint matters for those six counts, fuse the five counts without the preflight
  conjunct; that keeps `propext` alone but gives up the count/preflight sharing measured in F1.
  *An earlier draft of this report said the existing rows were unchanged; that was checked only for
  `corpus_preflight_all` and was wrong for these six.*
* **−1 row, pre-existing and unrelated to these changes:** the committed file listed
  `Fame.Economics.gexPlus.eq_1` twice, under `Fame.Economics.OrderFlow` and under
  `GEX.FixedPoint.Conjectures` (the equation lemma is generated in both modules). A full
  regeneration writes it once (`OrderFlow`). Neither module was touched here, so the committed file
  very likely could not be reproduced byte for byte before this work either. The generator was not
  run on the original tree, so that is inferred, not measured. If so, the `--regenerate` drift alarm
  of `check_axiom_audit_fresh.py` would have failed there too (§4 item 7).

## 7. Decisions touched

* **Q3 / D2 (prior audit: "apply only proof-body and import changes; statements and names never
  change; definition rewrites escalated").** I2 and I3 are proof-body or meta-code changes. I1 is a
  proof-body change plus one *added* theorem; no existing statement, name or definition changed. The
  measured-but-unapplied fast definitions (R3) stay escalated.
* **Q4 (trust policy).** No `native_decide` was added or removed.
* **Frozen files.** None touched (`HandoffV3/Kernel.lean`, `FreerBridgeChecks.lean`,
  `Resolutions.lean`, `AgentHandoff/`).

## 8. Corrections made during the work

* A first reading put the six SeamCorpus proofs at 663 s and claimed they ran in parallel. Both are
  wrong (M1, M2): the costs are cumulative, and kernel checks within a file are sequential. So
  fusion lowers wall time as well as CPU.
* An early diagnosis attributed the `bucketSum` cost to "`Int` lacking GMP acceleration". Wrong
  mechanism: the leaves are GMP `Nat` operations; the cost is instance unfolding through
  `List.sum`/`foldr` and `Int` constructor matching. The early per-element figure (~64 µs) was
  derived from an unvalidated operation count and is withdrawn.
* I3's first hypothesis (fresh collector state per theorem) was refuted by timers (§2 I3).
* One baseline batch was lost to a missing `bc` binary and an interrupted shell; it was re-run
  against copies of the original files outside the working tree. The tree was restored from the
  stash and checked before continuing.
* Process corrections adopted during the work: every background job is started with its PID
  recorded (`echo $! > pidfile`) and waited on with `kill -0`, never `pgrep -f`; build steps keep
  lake's exit code instead of letting `| tail` swallow it; the I3 result was re-run interleaved with
  user CPU as the metric of record; compiler hoisting was checked in the generated C rather than
  assumed.
