# Lean test guidelines — guide, review and suite audit (2026-10-17)

This report covers the request to (1) turn the supplied testing guidelines (sections A–G, the
vacuity / falsifiability / tightness rules, and the requirements-first workflow) into a guide in the
style of `docs/specs/lean-guide/`, (2) review that guide for errors and omissions, (3) refine it in a
second pass against the Lean proof-writing guide, and (4) audit every Lean test in the repository
against it, fixing each violation.

## 1. Scope and method

| Step | What was done | Output |
|---|---|---|
| 1. Write | Guidelines rewritten as a skill: an entry point plus nine topic references | `docs/specs/lean-testing-guide/SKILL.md`, `references/*.md` |
| 2. Review | Every quantitative or logical claim in the brief checked, by Lean proof where possible | §2 below; `RequestProject/TestMethod/*.lean` |
| 3. Second pass | Guide re-read against `docs/specs/lean-guide/` (naming, rule ids, Mathlib conventions, `decide` vs `native_decide`, axiom policy) | §2.3 |
| 4. Enforce | Mechanical rules turned into a checker with a ledger and self-tests | `scripts/check_lean_test_style.py`, `docs/standards/LEAN_TEST_STYLE.md`, `docs/standards/LEAN_TEST_STYLE_LEDGER.tsv` |
| 5. Audit | Every Lean file with `#eval`/`#guard`/`Plausible`/`TestSeq`/`example` scanned by the checker, then the flagged and the high-risk files read by hand | §4 |
| 6. Verify | Full build of the default targets, test executable, checker, checker self-test, property-registry audit | §5 |

Scope is Lean only (`RequestProject/**`). The Node, Python and Solidity suites were reviewed
against the related anti-patterns on 2026-10-14 (`audit/2026-10-14-test-guidelines/REPORT.md`) and
are not repeated here.

## 2. Review of the supplied guidelines

### 2.1 Errors found in the brief (and how the guide states them instead)

Each correction is backed by a Lean artifact in `RequestProject/TestMethod/` (built as part of the
default targets) or by a direct calculation.

| # | Brief section | Claim in the brief | Finding | Evidence |
|---|---|---|---|---|
| E1 | A5 | A test is load-bearing **iff** its proof term mentions the function under test | Wrong both ways: `fun n => rfl` for `n + 0 = n` mentions `HAdd.hAdd` (passes the criterion while being definitional), and a lemma-based proof need not mention the constant. The guide replaces it with "delete-the-body" and mutation checks | `ProofTermAudit.lean` (`addZeroByRfl`, `addZeroByLemma`, `criterionVerdicts`) |
| E2 | A5 | `n + 0 = n` by `rfl` makes the suite vacuous | It is a valid proof of a true statement; the issue is only that it tests nothing about an implementation. Guide: definitional facts are not tests, but they are not errors either | same |
| E3 | B1 | `x + 1.0 == x` for every double `x > 2⁵³` | Guaranteed only for `x ≥ 2⁵⁴`; in `[2⁵³, 2⁵⁴)` the sum rounds to even, so it holds for half the values | `FloatAudit.lean` (`two53`, `plusOneAbsorbed`, `b1Suite`) |
| E4 | B1 conjecture | Disagreement set has measure `≤ Σ ulp(tᵢ)` | Fails when the implementation cancels before the comparison; the disagreement interval can be far wider than one ulp | `FloatAudit.lean` (`cancellingDecision`, `b1ConjectureSuite`) |
| E5 | B2 | Composed bound `ε₁L₂…Lₙ + … + εₙ` | Holds with Lipschitz constants of the downstream stages on the relevant range; proved in that form, and per-stage bounds alone shown insufficient | `NumericAudit.lean` (`error_budget_composes`, `per_stage_bounds_do_not_bound_composition`) |
| E6 | B3 | Random pairs on `√x` give ratio ≈ 1 | The ratio is `1/(√x+√y)`: at least 1/2 on `[0, 1]`, and > 2 on a corner of positive measure; the qualitative point (global pairs miss local blow-up) stands | `NumericAudit.lean` (`sqrt_secant_identity`, `sqrt_secant_gt_two`, `grid_hits_count`) |
| E7 | B4 | DKW at `ε = 10⁻³` needs `n ≈ 3.8×10⁵` | At `n = 3.8×10⁵` the tail bound `2·exp(−2nε²)` is above 0.4, so it guarantees nothing at 95 %; the brief's figure corresponds to `δ ≈ 0.94`. At `δ = 0.05`, `n = ln(2/δ)/(2ε²) ≈ 1.84×10⁶` (1.8×10⁶ is not enough, 2×10⁶ is) | `NumericAudit.lean` (`dkw_at_brief_sample_size_is_vacuous_refutes_B4_number`, `dkw_needs_more_than_1_8_million`, `dkw_two_million_suffice`) |
| E8 | B5 | `n ≥ ln(1/δ)/(2p²)` "for frequency estimation" | That Hoeffding bound gives absolute accuracy `p`, which cannot distinguish `p` from `0` or `2p`; relative accuracy needs a multiplicative Chernoff bound | calculation; guide `numeric-rigor.md` |
| E9 | B5 | at-least-one-hit `n ≥ ln(1/δ)/p` "by union bound" | Follows from independence, `(1−p)ⁿ ≤ e^{−np}`, not from a union bound. The 63 % figure for `p = 10⁻⁴, n = 10⁴` is right | `NumericAudit.lean` (`miss_probability_le_exp`, `miss_probability_le_delta`, `miss_probability_ge_exp`, `miss_probability_ten_thousand`) |
| E10 | B5 | Importance weights averaging to 1 verify the Radon–Nikodym factor | Necessary, not sufficient: wrong weights can average to 1 | `LogicAudit.lean` (`likelihood_ratio_mean_is_covered_mass`, `average_one_does_not_certify_likelihood_ratio_refutes_B5_check`) |
| E11 | A4 | If value cannot be created, conservation implies non-negativity | False: a value-conserving transfer can drive one balance negative | `LogicAudit.lean` (`conservation_does_not_imply_nonnegativity_refutes_A4_example`, `nonnegativity_does_not_imply_conservation`) |
| E12 | C1 | "combine with A5 (conjunct liveness)" | Cross-reference error: conjunct liveness is A4. The restricted-step totality condition is exactly deadlock-freedom (proved) | `LogicAudit.lean` (`restricted_step_total_iff_deadlock_free`) |
| E13 | C2 conjecture | A complete observation set needs one query per conserved quantity | False: one full-state query is complete, and a query per conserved quantity can be incomplete | `LogicAudit.lean` (`one_full_state_query_is_complete_refutes_C2_conjecture`, `conserved_quantity_query_is_not_complete`) |
| E14 | C3 | Chunking invariance tests the system | For a fold-based replay it is definitional (`List.foldl_append`); it tests the harness only when replay is not a plain fold. Disjoint events commute on balances but not on a full state that carries a log | `LogicAudit.lean` (`replay_chunking_is_definitional`, `disjoint_events_commute_on_balances_not_on_full_state_refutes_C3`) |
| E15 | D2 conjecture | Monotone α, γ make boundary probes sufficient | The Galois-connection equivalence holds, but a monotone round-trip can fail off any finite probe set | `LogicAudit.lean` (`galois_iff_monotone_and_roundtrip_theorem`, `monotone_roundtrip_can_fail_off_probe_set_refutes_D2_corollary`) |
| E16 | E1 conjecture | No order-1-adequate suite detects a masked double fault | False as worded universally: masking holds for any *given* finite suite, but a suite containing the masking point detects it | `LogicAudit.lean` (`double_fault_masked_on_any_finite_suite`, `suite_containing_the_masking_point_detects_the_double_fault`) |
| E17 | B4 caution | TV-close marginals, different process | Correct; proved with equal marginals and different joint laws | `LogicAudit.lean` (`equal_marginals_different_process_theorem`) |
| E18 | A1 | `(solveWitness x).exists fun w => Checker x w` | Correct in direction: an incomplete solver raises false alarms, never hides a violation, provided the checker is sound | `LogicAudit.lean` (`sound_checker_rejects_every_violation`, `incomplete_solver_raises_false_alarm`, `failures_at_least_violations`) |
| E19 | A3 | A finite horizon cannot establish liveness | Correct; proved | `LogicAudit.lean` (`finite_horizon_cannot_separate_liveness`) |
| E20 | F1 | `native_decide` "finds" counterexamples to reify | `native_decide` fails without producing a witness; the witness has to come from a separate search (`#eval` with `List.find?`) and is then checked by `decide` | guide `lean-mechanics.md` |
| E21 | F2 | A monad law closed by `rfl` tests the definition against itself | A kernel-checked `rfl` is a proof of the law for that instance, stronger than a test; the real concern (an interpreter different from the instance) needs the interpreter in the statement | guide `lean-mechanics.md` |
| E22 | A5 axiom audit | Allowed axioms are exactly `{Classical.choice, propext, Quot.sound}` | This repository also admits the `native_decide` axioms at documented sites; guide aligned with `docs/specs/lean-guide/` | guide `lean-mechanics.md` |
| E23 | "Guard against vacuity" | Treating Plausible's `gaveUp` as failure guards against vacuity | Necessary, not sufficient: a guard Plausible cannot see (inside `decide`, a conjunct, or a `Bool` `if … then … else true`) is counted as a pass, so `gaveUp` stays 0 | §2.2 O1; `vacuity-and-coverage.md` |

The earlier written review of the same brief is kept at
docs/archive/reviews/TESTING_GUIDELINES_A_TO_G_REVIEW.md (deleted); the table above supersedes it where
they differ.

### 2.2 Omissions in the brief (added to the guide)

| # | Omission | Added where |
|---|---|---|
| O1 | **Decorated guards**: Plausible discards a case only if the precondition is a visible `→` binder. A guard inside `decide (...)`, a `Bool` `if`, or a conjunction is evaluated as an ordinary result, so vacuous inputs count as passes | `vacuity-and-coverage.md` §"Guards are discarded only when Plausible can see them"; checker rule TG1 |
| O2 | **Lean purity makes self-comparison vacuous**: `f x == f x` and `gen seed n == gen seed n` are true by referential transparency; "make replay an asserted equality" needs a congruence (prefix, chunking, observation) to have content | `state-and-traces.md`; checker TG2 |
| O3 | **Filler conjuncts** (`x < x + 1`, `e ≤ e`) added to make a law look non-trivial | checker TG2 |
| O4 | **Absolute tolerances on scaled quantities** | `numeric-rigor.md`; checker TG3 |
| O5 | **Undisplayed demo `#eval`**: a printed value is not a check; pin with `#guard_msgs` or gate with a theorem | `lean-mechanics.md`; checker TG5 |
| O6 | **Declared valid-rate floors**: a counted runner needs a stated floor per law, with a reason when below the default | `vacuity-and-coverage.md`; `RequestProject/TestSupport/Counted.lean` |
| O7 | **Every exemption is a ledger row with a reason, and a stale row fails** | `docs/standards/LEAN_TEST_STYLE.md` |

### 2.3 Second pass against the Lean proof-writing guide

* Rule ids renamed `LT*` → `TG*`: the proof guide already uses `LT.n`.
* Kernel `decide` preferred over `native_decide`; `native_decide` only with a written trust note,
  matching the proof guide's axiom policy.
* Test helpers named and documented like library code (docstrings, no `_`-prefixed unused binders).
* `#guard_msgs` used for pinned output rather than comments that restate it.
* SKILL entry point kept short, with detail in references, as in `docs/specs/lean-guide/SKILL.md`.

## 3. Guide and enforcement

* `docs/specs/lean-testing-guide/SKILL.md` — entry point, rule index, checklist.
* References: `requirements-first.md` (the workflow from the brief's last section),
  `vacuity-and-coverage.md` (A2, A4, B5, decorated guards), `falsifiability.md` (mutation, E1, G1),
  `oracles-and-laws.md` (D1–D3, round-trips, metamorphic laws), `state-and-traces.md` (C1–C4),
  `numeric-rigor.md` (B1–B5), `lean-mechanics.md` (A5, F1–F3), `process-and-reporting.md`
  (E3, G2, G3), `anti-patterns.md` (catalogue plus "Claims not to cite as rules", see §2.1).
* `docs/standards/LEAN_TEST_STYLE.md` — the mechanical rules:
  TG1 undiscarded guard, TG2 self-comparison / filler, TG3 absolute tolerance, TG4 unpinned
  `native_decide`, TG5 bare demo `#eval`.
* `scripts/check_lean_test_style.py` — the checker (with `--selftest`), wired into
  `scripts/run_checks.sh`; exemptions in `docs/standards/LEAN_TEST_STYLE_LEDGER.tsv`.
* `RequestProject/TestSupport/Counted.lean` — counted Plausible runner (`checkCounted`,
  `requireValidRate`, decorated variants) reporting total / valid / discarded and failing below a
  declared floor.

## 4. Findings and fixes

"Rule" is the guide rule the site violated.

### 4.1 Vacuous replay / self-comparison (TG2, state-and-traces)

| # | Site | Finding | Fix |
|---|---|---|---|
| F1–F8 | `DetSim/Applied/{Gateway,BatchClearing,Enclosure,ASPSettlement,FeeModelRational,EngineModel,FeeModel,FeedSimulator}Suite.lean` | Replay check `gen.corpus seed n == corpus` compares a pure function with itself | Replaced by `gen.chunkReplayAgrees seed caseCount`: the corpus generated in one call equals the concatenation of two separately generated chunks. Added `corpusFrom_append`, `chunkReplayAgrees`, `chunkReplayAgrees_eq_true` in `DetSim/Gen.lean`; L1 docstring in `DetSim/Evidence.lean` updated |
| F9 | `DetSim/Applied/ASPSettlementSuite.lean` `stateKeyDeterministic` | `k s == k s` | The key must factor through the observation (`specObs`): distinct-key count equals distinct-observation count on the corpus |
| F10 | `DetSim/Applied/FeedSimulatorSuite.lean` `keyDeterministic` | same | same, through new `behaviourOf` |
| F11 | `Fame/Testing/SeedStability.lean` `regenerationIsReferential` | Regenerating a corpus and comparing it to itself | Prefix congruence: the first `k` cases of a length-`n` corpus equal the length-`k` corpus (`prefixReplayAgreesWith`, `matchingCaseFingerprint`, `prefixReplayAgreesAt`). New mutant `generator-depends-on-corpus-length` (`lengthStratifiedCorpus`) that the old check accepted and the new one rejects; `property_registry.json` updated |

### 4.2 Guards Plausible could not see, filler, and weak laws (TG1/TG2, vacuity-and-coverage)

| # | Site | Finding | Fix |
|---|---|---|---|
| F12 | `ASP/Phase10/Properties.lean` `refusalIsNoopLaw`, `replayLaw` | Precondition inside `decide (…)` | Guard moved to a visible `→`, run under the counted runner's floor; dependent proofs adjusted |
| F13 | `ASP/Phase9/Properties.lean` `refusalIsNoopLaw` | same | same |
| F14 | `Fame/Testing/POLSuitePlausible.lean` | Guards embedded as conjuncts | Split into separate claims `DrawdownExactWhenCovered`, `SeniorOnlyAfterJunior`, `NotePrincipalIsNotRewritten` (seeds 20260818–20) with visible guards |
| F15 | `Fame/Testing/POLPlausible.lean` sufficiency law | Conjunct guard | Split; new `claimGainIsSafe` with declared floor `minValidPct 30` |
| F16 | `PaperTests/EpochOperationsTests.lean` | Filler conjunct `x < x + 1 ∧ x ≤ x`, and one claim bundling three findings | Filler replaced by the ack/commit-window iff law; `operational_findings` split into three `runClaim`s |
| F17 | `PaperTests/VenueObligationsTests.lean` | One-way implication where the requirement is an equivalence (an always-true implementation passes) | Stated as iff |
| F18 | `GEX/Tests/Meaningful.lean` (exec-bonus law) | Guard met by ≈20 % of cases, below the floor | Replaced by an exact oracle `execBonus = decide (Stabilising …)` checked on every case |
| F19 | `CLF/Meaningful.lean` antitone and P3 laws | Below the 50 % default floor with no stated floor | Floors declared at 25 % and 20 %, with the observed rates (35 %, 29 %) in comments |
| F20 | 23 suite modules (ASP phases 2/4/6/7/9/10/11, ASP base, Sim, SWC ×3, Venue ×4, Governance, Production/ADL, PaperTests harness, V5 harness, GEX Strict, DecimalNames, StyleRefactor) | Runners treated "no counterexample" as a pass without counting discards | Migrated to the counted runner (`TestSupport/Counted.lean`) with a 50 % default floor and total / valid / discarded reporting |

### 4.3 Unpinned demonstrations (TG5, lean-mechanics)

| # | Site | Fix |
|---|---|---|
| F21–F22 | `ClaimA.lean` (2 `#eval`) | Pinned with `/-- info: … -/ #guard_msgs in` |
| F23 | `Exposure.lean` | same |
| F24–F26 | `Recompute.lean` (3) | same |
| F27 | `Fame/MemeMarkets/SettlementPriceHoare.lean` | same |
| F28 | `PropertyAudit.lean` (2), `SWC/InvariantRegistry.lean` (2) | Kept: ledger rows record that each is gated by a theorem or throws on failure |

### 4.4 Absolute tolerances (TG3)

| # | Site | Disposition |
|---|---|---|
| F29 | `TestMethod/FloatAudit.lean`, `TestingHarness.lean` | Kept as negative demonstrations (they show an absolute ε lets a leaking mutant through, which is why the gates use scaled tolerances); ledger rows with reasons |

### 4.5 Registry and tooling

| # | Finding | Fix |
|---|---|---|
| F30 | `registry-exempt` markers not adjacent to their `#eval` in `CLF/Tests.lean`, `GEX/Tests/Properties.lean` | Moved directly above the command |
| F31 | `TestSupport/Counted.lean` self-checks unregistered | Marked registry-exempt; `selfCheckAbbrevLaw` renamed `selfCheckAbbrevProp` (it is a `Prop` abbreviation) |
| F32 | Checker rule ids collided with the proof guide's `LT.n` | Renamed `TG*` |
| F33 | Checker TG1 flagged laws whose guards the counted runner does see | Resolution added (type-ascription erasure, `let` stripping, spine / `decide` / conjunct / undecorated-∀ detection, abbreviations run through `runClaim`/`lawSucceeds`); extended self-tests |
| F34 | Checker TG2 missed `e ≤ e`, `e < e + k` filler | Added |
| F35 | `requireGuardRate` name did not match the runner | Renamed `requireValidRate` |

### 4.6 Floors measured by the test executable

Running the test executable after §4.1–4.5 showed that making guards visible (F12–F20) exposed
laws that had been passing on few non-vacuous cases. Each was fixed by aiming the generator at the
guarded region (the guard stays in the law, so a miss is still a discard) or, where the guard rate is
fixed by design, by a declared floor with its reason.

| # | Site | Measured | Fix | After |
|---|---|---|---|---|
| F36 | `ASP/Phase10/Properties.lean` `replayLaw` | 5 % valid (a random offer is admitted one time in twenty) | New `ReplayCase` and `genReplayCase`: sequence number and attestation set from the session state, up to 32 draws until admitted | 99 % |
| F37 | `Fame/Testing/POLPlausible.lean` `claimSufficiencySafety` | 31 % | New decoder `fundedDragOf`: one draw in four generic, three in four a loss of `k/20` of owned + insurance (`k = 20` is the funding boundary) | 68 % |
| F38 | `Fame/Testing/POLSuitePlausible.lean` `claimTrancheSeniorOnlyAfterJunior` | 34 % | New decoder `seniorReachingLossOf`: one in four generic, three in four exhaust junior and take `k/8` of senior | 81 % |
| F39 | `PaperTests/ProductionScoreTests.lean` `productionBefore_trans` | 34 % (and the third event was a fixed constant) | Three sampled events sorted by `chain3` (a sorting network on `orient`) | 68 % |
| F40 | same, `productionBefore_asymm` | 40 % | Pair oriented by `orient` | 84 % |
| F41 | same, `worst_bucket_dominates` | 34 % | Pair oriented by worst-bucket score (`byWorst`) | 65 % |
| F42 | same, `aggregate_breaks_worst_bucket_tie` | 9 % | `worstTiedPair` builds two events with the same worst bucket and independent VEX tails, ordered by aggregate | 75 % |
| F43 | same, `event_id_breaks_remaining_tie` | 37 % | Identifiers ordered by `min`/`max` | 90 % |
| F44 | same, `adl_triggered_of_le` | 31 % | Backstop and field ordered by `max`/`min` | 87 % |
| F45 | same, file header | Claimed "Expected valid rate: 100 %" for sampled claims that were guarded | Header corrected | — |
| F46 | `Governance/SignoffProperties.lean` `planExistsLaw` | 49 % against a 50 % floor | The guard `c .dgD4 = .one` holds with probability exactly 1/2 (`Opt` has two values); floor declared at 40 % with that reason (4.5 standard deviations below the mean at 500 cases) | 49 %, floor 40 % |
| F47 | `DetSim/Applied/ASPSettlementSuite.lean`, `FeedSimulatorSuite.lean`, `Fame/Testing/POLSuitePlausible.lean` | Three docstrings written in F9, F10, F14 failed the repository's documentation lint (ended in a parenthesis) | Reworded | — |

## 5. Verification

* Full build of the default targets (`lake build`, 9091 jobs): succeeds, including every file
  listed in §4 and `RequestProject/TestMethod/*`.
* `python3 scripts/check_lean_test_style.py`: passes, `TG1=0 TG2=0 TG3=2 TG4=0 TG5=4`, every
  remaining site a ledger row with a reason. `--selftest`: passes (5 planted violations rejected;
  exemptions, stale rows and missing labels handled).
* `python3 scripts/audit_property_registry.py`: exit 0.
* No `sorry` in any file changed by this audit.
* Test executable (`lake build request_project_tests`, 17 200 jobs, then
  `.lake/build/bin/request_project_tests`): exit 0, `[gate] all 55 components passed`. Before the
  §4.6 fixes the same run failed 5 of 55 components (documentation lint, the FAME production gate,
  paper tests, ASP phase 10 intake, governance sign-off), all for the reasons listed in §4.6.
* `python3 scripts/lint_lean_docs.py`: passes.

## 6. Residual risks (not fixed)

1. The checker matches syntax; a self-comparison through an alias spread across definitions is
   not detected. Review remains responsible for it.
2. Some sampled laws restate theorems proved in the same module; per G3 they could be removed, but
   they are kept as executable regression checks until the theorem and the sampled statement are
   the same `Law` object (F3).
3. `CLF/Meaningful.lean` P3 runs at a 20 % floor; a targeted generator for its precondition would
   raise coverage and is the right long-term fix.
4. Per-module mutation-adequacy reporting (E1/G2) exists only for suites registered in
   `property_registry.json`; other suites have per-law mutants but no module score.
5. As the brief's closing paragraph says, none of this checks that the specification itself is
   right; that remains a review obligation.
