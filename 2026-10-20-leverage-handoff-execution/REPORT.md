# Execution report — `LEVERAGE_HANDOFF_COMPLETE_2026-10-19.md`

Companion to `PLAN.md` (same folder), which was written before any code. This report records what
was built, how each item was checked, and what is still open. Raw outputs are in `raw/`. A timing
in this file cites a raw TSV or log in `raw/`; no other timing claims are made.

## 1. Status by handoff section

| § | Item | Status | Artefact | Check |
|---|---|---|---|---|
| §2 | C-MAP4 guarded wrapper `Venue.gstep`: single-step, run induction, transparency, order mass, monitor composition | **PROVED** | `RequestProject/Venue/BoundedGuard.lean` | pins + sweep in `RequestProject/Venue/LeverageAudit.lean` |
| §2 | boundary drill (`2^63 − 1` amended by `+2` halts), clock overflow, N1 clamp mutant, N2 guard absence | **PROVED** (`decide`) | `RequestProject/Venue/BoundedGuardTests.lean` | same |
| §3 | C-AD1 abstract `AdapterInterface` (laws as fields), forward simulation, reference instance `tapeAdapter` | **PROVED** | `RequestProject/Venue/Adapter.lean` | same |
| §3 | C-AD2 digest detects divergence (Bounded form, lawful-adapter form, reachable form) | **PROVED** | same | same |
| §3 | ported zip/last-mismatch counterexamples; swallow and retag mutants | **PROVED** | `RequestProject/Venue/AdapterTests.lean`, `DetSim/Divergence.lean` | same |
| §3 | concrete DST instance of `AdapterInterface` | **BLOCKED-EXTERNAL** (DST API version) | — | — |
| §4 | `memo_sound` (Lean model) | **PROVED** | `RequestProject/Audit/MemoSound.lean`, `…/MemoSoundTests.lean` | pins + sweep |
| §4 | memoized audit over the shared freshness hash, planted stale entry refused, hit/miss counts printed | **CHECKED** | `scripts/axiom_audit_memo_cache.py` | `--selftest` (5 planted defects) |
| §5 | `levelsFast` with universal, hypothesis-free `levelsFast_eq_levels` | **PROVED**; admitted, not adopted | `RequestProject/Venue/LevelsFast.lean` | pins; probe in `raw/levels_decide_probe.*` |
| §6 | fusion A/Bs: LMMGovernance, LMM, TokenLedger, POLSuiteRisk, DivergenceRate | **DONE** (5 of 6) | §3 below | statement diff + median-of-3 interleaved |
| §6 | fusion A/B: DetSim.Conformance | **NOT APPLICABLE as specified** | §3 below | — |
| §7 F1 | `split_ifs` guard chains replaced by named `_eq_…_iff` lemmas | **DONE** | `ASP/Lemmas.lean`, `ASP/Phase6/Adapter.lean`, `ASP/Phase10/Intake.lean`, `ASP/Phase7/BatchInvariants.lean` (`applyPayment_eq_ok_iff`, `settleGuards_eq_none_iff`, `withdrawalGuards_eq_none_iff`) | `raw/f1_statement_invariance.out`; `check_statement_invariance.py` on BatchInvariants |
| §7 F2 | `maxRecDepth` settings measured by removal | **DONE** | 38 probed: 15 removed (build stays green), 23 annotated `Load-bearing, measured 2026-10-20 (F2)` with the error each one prevents | `raw/f2_maxrecdepth_probe.tsv` |
| §7 F3 | `show … from rfl` | **NOT STARTED** (opportunistic, no gate, per the handoff) | — | — |
| §8.1 | pairing linter (environment-level) | **DONE** | `RequestProject/Venue/RegisterLint.lean` | planted fixtures in `RegisterLintTests.lean` (missing mutant; near-miss mutant without a separation) |
| §8.2 | coverage-matrix linter | **DONE** | same | phantom-constructor fixture |
| §8.3 | FC-GATE consistency | **LIVE** (unchanged) | `scripts/check_fc_gate.py` | `--selftest` (6 planted defects) |

## 2. Statement adaptations

Listed in `PLAN.md` §2 and in the `discharge` column of `register/leverage_conjectures.tsv`. In
short: the handoff's Lean blocks were shapes against an API that differs from the tree (`step` takes
a `Config` and returns `State × Observation`; there is no `Event.nop`; `levels` takes a `Side`).
Unused hypotheses were dropped, which makes each statement stronger. One handoff statement is
**false as written**: `adapter_digest_detects` without `Bounded` hypotheses. It is refuted by
`Venue.Adapter.not_forall_digest_detects` (64-bit wrap collision). The proved form carries the
hypotheses, and the reachable-state corollary `emitTape_digest_ne_of_reachable` discharges them
through C-MAP4.

## 3. Fusion A/Bs (§6)

Method. `scripts/fuse_kernel_checks.py` adds one `*_measurements` theorem per suite. Its statement
is the conjunction of the sibling certificates over the same corpus, proved by a single
`decide +kernel`. Each original certificate becomes a projection of it, with name and statement
unchanged. `scripts/fusion_ab.py HEAD FILE -n 3` elaborates the pre-fusion file (A) and the fused file
(B) alternately, A B A B A B. Times are wall-clock seconds per module elaboration.

(a) **Statement invariance.** `raw/fusion_statement_invariance.out` shows all five files OK.
A statement change planted in `LMMTests` is rejected: `raw/fusion_planted_statement_change.out`,
rc=1.

(b) **Measured per suite.** Raw rows are in `raw/fusion_ab_session2.tsv`, and each suite has a
`raw/fusion_ab_<suite>.log`.

| Suite | Fused certificates | median A (s) | median B (s) | delta |
|---|---|---|---|---|
| `Fame/Workflow/DivergenceRate` | 3 (array, live, truncating shells) | 105.7 | 61.6 | −41.8 % |
| `Fame/Testing/TokenLedgerTests` | 3 (suite report, dust-leak, fee mutant) | 93.2 | 74.9 | −19.7 % |
| `Fame/Testing/LMMTests` | 3 (suite report, mode and risk branch coverage) | 87.9 | 68.7 | −21.8 % |
| `Fame/Testing/POLSuiteRiskTests` | 10 (suite report and every corpus certificate) | 120.8 | 68.1 | −43.7 % |
| `Fame/Testing/LMMGovernanceTests` | 3 (suite report, governance and quote coverage) | 96.7 | 80.8 | −16.4 % |

These are per-module deltas. They are not summed into a build-wide claim: per the handoff, kernel
checks serialize within a module but modules build in parallel. Machine: 8 cores, 64 GB. Other
work was minimal during the runs (light Python checks only). The earlier single-suite measurement
of LMMGovernance from the previous session (`raw/fusion_ab.tsv`, −21.8 %) has a different
baseline and is kept as a historical record.

(c) **Heartbeats.** No `maxHeartbeats` or `maxRecDepth` override was added by the fusions.

**DetSim.Conformance: not applicable as specified.** `RequestProject/DetSim/Conformance.lean` has
exactly one `decide +kernel` certificate (`every_invariant_class_covered`). Its other portfolio
certificates use `native_decide`, so they cost the kernel nothing and fusion has nothing to share.
The root `DetSim/Conformance.lean` has no decision procedure at all. Fusing would first require
moving those certificates from `native_decide` to the kernel, which changes their trust footprint
(`NATIVE_DECIDE_TCB_REGISTER.md`). That is an owner decision, not a proof-only refactor. Recorded
as open decision OD-L3 below.

## 4. Items found and fixed during this continuation

* `RequestProject.Venue.RegisterLintTests` declares theorems, but nothing reached it from the import
  list of `scripts/AxiomAudit.lean`. `check_axiom_audit_fresh.py` failed on this. The import was
  added and the check passes.
* `register/decision_clarifications.tsv` DC-5 still read OPEN ("not implemented: it changes
  `Venue.step`"). The guarded-wrapper design discharges it without changing `Venue.step`, so it is now
  RECORDED. The operational residue, that the deployed engine must run the guarded step, is stated
  in the row.
* F1 completion: two `split_ifs` chains remained in `ASP/Phase7/BatchInvariants.lean`
  (`settleGuards_none`, `withdrawalGuards_none`). Each now goes through a named iff lemma. The
  statement diff is OK.

* `docs/latex/axiom_audit.tsv` was stale against the new modules. It was regenerated through the
  memoized wrapper (`memo: hit 0 miss 1 stale 0`, 969-file source set, 21 min on this machine). The
  review against the previous TSV (`raw/axiom_audit_review.out`, rc=0 with the touched modules
  allowed, every change printed as a notice) shows:
  * 136 rows added: the new modules, the F1 lemmas and the five `*_measurements` theorems;
  * no row removed;
  * no axiom set changed. The other notices are an axiom-order change in the printed list and
    the module attribution of two generated `.eq_1` equation lemmas. A first version of
    `withdrawalGuards_eq_none_iff` pulled `Classical.choice` into `withdrawalGuards_none`; it now
    uses `Decidable.not_not`, so the footprint stays `propext`.
  * Every footprint lies in {propext, Classical.choice, Quot.sound, Lean.ofReduceBool,
    Lean.trustCompiler}, and no row has `sorryAx`.

## 5. Verification battery (§9)

| Check | Result |
|---|---|
| `lake build` (default targets) | green, 9124 jobs, no `sorry` |
| `lake build RequestProject.Venue.LeverageAudit` (pins plus sweep over 9 modules, sweep anchor reached, sweep fails on an empty allow-list) | green |
| `python3 scripts/check_leverage_conjectures.py` / `--selftest` | 15 rows (PROVED 8, CHECKED 5, OPEN 1, BLOCKED-EXTERNAL 1); 10 planted defects caught |
| `python3 scripts/check_statement_invariance.py --selftest` | OK |
| `python3 scripts/axiom_audit_memo_cache.py --selftest` | 5 planted defects caught, 4 behaviour checks, 969-file source set |
| `python3 scripts/check_fc_gate.py` / `--selftest` | verdict NOT CONNECTED (fail-closed); 6 planted defects caught |
| `python3 scripts/check_axiom_audit_fresh.py` | OK after the import fix in §4 |
| `native_decide` in the new modules (BoundedGuard*, Adapter*, MemoSound*, LevelsFast, RegisterLint*) | none |

### Full battery (`bash scripts/run_checks.sh`, built tree)

`raw/battery_final.log`: **454 checks; 420 passed, 23 failed, 11 skipped by the check itself.**
At the start of this continuation the same battery gave 398 passed and 44 failed. Each of those 44
failures also fails at the delivered base commit, so none was introduced here. The failures fixed in
this continuation are:

* leverage-file hygiene: the `RegisterLintTests` header, live examples, a missing docstring, and the
  runner/console coverage of the new scripts;
* generated views regenerated to a fixed point with `regen.py`, and prose counts rebound;
* documentation index rows for the leverage documents;
* executables built for the vector and differential checks;
* the test census and the roadmap baseline refreshed.

The 23 remaining failures are registered with cause, next act and owner:

| Rows | Cause |
|---|---|
| CD-1/2/3/5 | environment: hooks, handover, dev-env |
| CD-4 | owner dates |
| CD-13 | 17 root documents without an ICA classification. This blocks the decision map, the RSV audit, the signing-evidence sweep and `regen.py --check` |
| CD-14 | session-artifact write-once violation, from an earlier session |
| CD-15 | two artifacts without a schema row |
| CD-16 | halt-drill skip not in the census, plus its unit test |
| CD-17 | style findings on the domain term "last occurrence" |
| CD-18 | citation and demo copy stale against the grown audit |
| CD-19 | seam differential needs Foundry |

All rows are in `register/check_debt.tsv`.

## 6. Open decisions and blockers raised by this work

| Id | Kind | Item |
|---|---|---|
| OD-L1 | decision (owner) | `@[csimp]` adoption of `levelsFast`: admitted by equality (DC-1), but the probe shows the right fold exceeding the default `maxRecDepth` under `decide` on 40 orders. No proof is repointed. Adopt only with a tail-recursive form, or not at all |
| OD-L2 | decision (owner) | PF-1 field list (C-MAP1) is still PROPOSED pending the DST countersign. All C-MAP/C-AD results are relative to it |
| OD-L3 | decision (owner) | DetSim.Conformance fusion requires moving certificates off `native_decide` (TCB change) |
| OD-L4 | decision (owner) | DC-2 (`AgentHandoff/Audit.lean` moduleNames hoist deferred, frozen tree) and DC-3 (G-12 classified FC-0 by the agent) remain OPEN |
| BL-L1 | blocker (external) | concrete DST `AdapterInterface` instance, FC-1/FC-3/FC-4: DST API version and F-1 delivery date |
| BL-L2 | blocker (operational) | the deployed engine must run the guarded step (`gstep`). The Lean model proves the wrapper, not the deployment |
| BL-L3 | open conjecture | C-FC1 (FC rows plus FC-0 suffice for a sound connection verdict) stays OPEN; its sufficiency document rides the next signature packet (S*) |
