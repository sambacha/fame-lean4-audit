# Execution of Phases 0 and 1 of the 2026-10-16 Lean style review — before/after report

This document stands on its own. It records how
`audit/2026-10-16-lean-style-review/REPORT.md` (the *review*) was read, the dependency graph that
was built for its Phases 0–4, the corrections made in a second pass, how the cross-cutting concerns
were handled, what was executed for Phases 0 and 1, the tests that were added or updated, and the
measured state before and after. The working notes are in `NOTES.md` in this folder; the battery
result taken before any change is `data/checks_before.txt`.

Status words used below: **done** (landed and verified by a build or a check), **partial** (some of
the step landed; the rest is listed), **open** (not started in this execution).

---

## 1. How the review was read

The review was read section by section (§0–§8 and Appendices A–E) and each section was reduced to
the facts that a later step depends on. The terse reading notes are in `NOTES.md` §"Pass 1". The
items that matter for Phases 0 and 1:

* Scope and precedence (§0): the guide lives in `docs/specs/lean-guide/`; a departure from it is
  valid only when `docs/standards/LEAN_PROOF_STYLE.md` records it with a reason. So the "policy"
  steps (0.6) are edits to that file, not to the guide.
* Ground rules (§6): the byte-pinned files (`HandoffV3/Kernel.lean`,
  `HandoffV3/FreerBridgeChecks.lean`, `HandoffV3/Resolutions.lean`) and the v2.1 regression pin
  (`AgentHandoff/`) are out of scope. A statement or name change goes through the registry, claim
  index and axiom-audit regeneration of §6.6.
* Verification after every phase (§6.6): build exits 0 with no more than the 5 known warnings;
  linters show no new sites and the fixture still triggers them; the axiom audit passes; the text
  audit and its ratchets move only the right way; derived documents are regenerated after statement
  or name changes.

## 2. Dependency graph, Phases 0–4

An arrow `A → B` means "B needs A first". Nodes are the review's step numbers (§6.1–§6.5).

```
                 ┌──────────── 0.6 policy records (D-2, D-4, D-7) ───────────┐
                 │                    │                       │               │
                 ▼                    ▼                       ▼               ▼
0.1 promote ──► 0.2 gate +       2.1/2.6 `show` at       3.2 Prop-def      4.1/4.2 measure
multiGoal/show   vacuity anchor  decisions (needs D-2)   names (needs D-4) and scope budgets
     ▲                                                                       (needs D-7)
0.4 drop 30 unused binders ──► enable unused*InType (lives in the 0.1 lakefile block)
0.3 fix 2+2 flexible sites ──► flexible ratchet at 0, dotted-identifier heuristic
0.5 reflexive theorems ──────► 3.1 rename `*_deterministic`
0.7 ratchets ────────────────► guards every step of Phases 1–3 (1.7, 2.4 and 3.x read its metrics)

1.1 shared fold lemmas            (independent)
1.2 drop V3Proofs.replay_*        (independent)
1.3 vault acceptance API ──► 2.x vault proofs; shrinks theorems #5 and #6
1.4 Operator API in Chain.lean ──► 2.1 simulation square split
1.5 @[ext] on compared states ──► 2.1, 2.3, 2.5
1.6 canonical constants ──► 2.2 entry_gas_le/entry_never_fails (the `change` steps spell `320`)
1.7 equation lemmas ──► (measured by the 0.7 downstream-unfold ratchet)

2.1 ← 1.4, 1.5        2.2 ← 1.6        2.3 ← 1.5        2.4 ← 0.7 (rename_i)       2.5 ← 1.5
2.6 ← 2.1 … 2.5
3.1 ← 0.5 + registry migration window      3.2 ← 0.6 (D-4)      3.3, 3.4 independent
4.1, 4.2 ← 0.6 (D-7)      4.3, 4.4, 4.5, 4.6 independent
```

Necessary and sufficient for "Phase 0 done": 0.1–0.7 with the §6.6 checks. For "Phase 1 done":
1.1–1.7 with the §6.6 checks, including the registry/axiom-audit regeneration for every new or
renamed declaration.

## 3. Second pass: errors, omissions and corrected beliefs

Each belief from the first pass was checked against the tree, a build or a script run.

| # | First-pass belief | What the check showed | Effect |
|---:|---|---|---|
| 1 | Phase 0 had not started. | Most of Phase 0 was already in the tree: the four linters were promoted in `lakefile.toml` with rows in `LEAN_LINT_POLICY.tsv`, `scripts/check_promoted_linters.py` existed and was wired into `run_checks.sh`, the 2+2 flexible sites and the 30 unused binders were gone, and the reflexive theorems carried the tautology note. 0.6 and 0.7 had not been done. | Work was redirected to verifying 0.1–0.5 and doing 0.6 and 0.7. |
| 2 | The new regression suite `RequestProject/StyleRefactorTests.lean` compiled. | It had never been built. A full `lake build` failed on it: `open ASP (Amount Address)` names scoped *notations*, not constants; a `simp [deposit]` left an `if` goal; `SolventOrder`'s bucket type could not be inferred; `prefixHeadroom` lives in `VectorPrefixDomination`. | Fixed (§5.3). The suite also was not run by `lake test`; it is now. |
| 3 | `RequestProject/Util/ListFold.lean` was finished. | Its four `#guard` checks were not in `property_registry.json`, so `scripts/audit_property_registry.py` failed ("unregistered compile-time check"). | Turned into kernel-checked `example … := by decide`, which needs no registry row and is stronger evidence. |
| 4 | Removing the local `hmod : (wordModulus : Int) = 2 ^ 256` (step 1.6) is a pure rename. | An `omega` call three lines later had been using `hmod` silently from the context; the build broke. | The fact is now supplied explicitly at that call (`have := cast_wordModulus; omega`). |
| 5 | A promoted-linter-clean log proves the tree is clean. | Only if every module was actually elaborated with the lakefile options. The first full build of this execution rebuilt 1,053 library modules, so its log covers the tree; later builds rebuilt only changed modules. | PL1 was run on both logs (§6). |
| 6 | The 0.7 metrics could be approximated loosely. | They reproduce the review's figures exactly when implemented carefully: `rename_i` 147, unscoped `maxRecDepth` 38, `show`-opened bullets 3, reflexive statements 13 (the same 13 sites as Appendix B). | Used as the baseline of the ratchet file. |
| 7 | New declarations need no bookkeeping. | `scripts/check_axiom_budget.py` requires every `RequestProject.*` module that declares a theorem to be imported by `scripts/AxiomAudit.lean`. `RequestProject.Util.ListFold` and `RequestProject.StyleRefactorTests` were not. | Both added; the audit TSV was regenerated (§6). |

## 4. Cross-cutting concerns and how they were handled

* **Pinned files.** Nothing under `AgentHandoff/` or in the three byte-pinned `HandoffV3` files was
  touched. The `duplicate_statement` ratchet excludes them, so their copies are not counted as debt.
* **Silently ignored options.** `weak.` options that Lean does not know are dropped without a
  message (the core-only libraries `DetSim` and `DecisionMap` never see Mathlib linters). Every
  linter claim in this report is paired with a vacuity anchor: the promoted-linter fixture
  (`--fixture`) and the review's `LinterTriggerFixture` for the on-demand profile.
* **Fixtures outside a `lean_lib`** stay `.lean.txt`, so the repository's file-count checks do not
  move.
* **Statement and name changes.** Phase 1 added declarations but renamed or restated none. Every new
  declaration has a docstring (`lint_lean_docs.py`), the new test suite has a registry row, and the
  axiom audit was regenerated.
* **Warnings budget.** The full build still prints exactly the 5 known warnings, all in the pinned
  `HandoffV3/FreerBridgeChecks.lean`.
* **Idiom.** New lemmas are stated once over the most general structure that the callers need
  (`LinearOrder` for the folds), use dot-notation namespaces (`List.*`, `ASP.Vault.*`), are named
  from their statements, carry `@[simp]` only when their left-hand side is in simp-normal form, and
  are proved in term mode or with short `simp only`/`rw` steps.

## 5. What was executed

### 5.1 Phase 0

| Step | Status | What is in the tree now | Verified by |
|---|---|---|---|
| 0.1 Promote `multiGoal`, `show` (and, after 0.4, `unusedDecidableInType`, `unusedFintypeInType`) | done | `lakefile.toml` `[leanOptions]` and four rows in `docs/standards/LEAN_LINT_POLICY.tsv` | `check_lean_lint_options.py`; full build |
| 0.2 Gate + vacuity anchor | done | `scripts/check_promoted_linters.py` (PL1 clean log, PL2 live options via `scripts/lint_fixtures/PromotedLinterTrigger.lean.txt`, PL3 coverage), wired into `run_checks.sh` | `--selftest`, `--fixture`, `--log` (§6) |
| 0.3 Fix 2 flexible + 2 dotted-identifier sites; heuristic for dotted identifiers | done | the four sites (`ASP/PlanA/Dependency.lean`, `Fame/Evm/Gas.lean`, `Fame/Operator/Chain.lean`, `ASP/Phase5/Watchdog.lean`) no longer trip `linter.flexible`; `nonterminal_simp` reads dotted heads | on-demand `linter.flexible` run on those files (silent) with the trigger fixture firing; text audit `nonterminal_simp` = 0 |
| 0.4 Remove the 30 unused `DecidableEq`/`Fintype` binders | done | binders gone (`classical` / `omit … in` where needed); both linters enabled | a full build with the linters on: 0 warnings from them |
| 0.5 Reflexive theorems | done | all 13 carry the "tautology, kept verbatim" docstring; `create2_address_deterministic` no longer claims nonce independence | reading; `reflexive_statement` ratchet = 13 |
| 0.6 Record decisions | done (this execution) | `LEAN_PROOF_STYLE.md`: R8 scoped `show` departure (D-2); R26 departures for `Prop`-def casing (SR-42) and `snake_case` guards/mutants (SR-43) (D-4); new R20a (unused instance binders); new Part V / R28 budget policy for `maxHeartbeats`/`maxRecDepth` (D-7); the "coverage gap" paragraph and the checks table now describe the promoted linters | reading |
| 0.7 Ratchet metrics | done (this execution) | `scripts/audit_lean_proof_style.py` gains `rename_i`, `unscoped_maxRecDepth`, `show_open_bullet`, `reflexive_statement` (per file) and `downstream_unfold`, `duplicate_statement` (tree-wide, pin excluded); `--ratchet` / `--write-ratchet`; baseline `docs/standards/lean_style_ratchet.tsv`; `run_checks.sh` runs `--ratchet` | `--selftest` (each metric located at an exact line, each direction enforced, a missing row rejected); `--ratchet` passes |

Decisions D-2, D-3, D-4, D-5 and D-7 of the review are therefore **closed** (recorded as above).
D-1 (a second copy of the guide at `rules/writing-lean-proofs/`) and D-6 (owner of the vault API)
are ownership questions and stay **open**.

### 5.2 Phase 1

| Step | Status | What is in the tree now | Remaining |
|---|---|---|---|
| 1.1 Shared fold lemmas | done | `RequestProject/Util/ListFold.lean`: `List.le_foldr_max`, `le_foldr_max_of_mem`, `foldr_max_le_iff`, `foldr_max_le`, `foldr_max_mem`, `foldr_max_eq_or_mem`, the `min` duals, `foldl_max_eq_foldr`, `foldl_min_eq_foldr`, `le_foldl_max`, `le_foldl_max_of_mem`, `perm_pair_cases`; 17 files import it in place of their private copies. This execution replaced its `#guard`s by kernel-checked examples. | — |
| 1.2 Drop `V3Proofs.replay_*` | done | `HandoffV3/Proofs/Merge.lean` uses `Handoff.replay_*` through `open Handoff` | the per-module `replay_append` copies of Appendix C outside the pin |
| 1.3 Vault acceptance API | partial | `ASP.Vault.*_eq_ok_iff` for all 14 guarded entry points (`Phase7/Transitions.lean`); the arms of `Step.totalDeposits_mono` and `price_reference_is_written_only_by_settlement_and_seed` use them. This execution added `@[simp]` price-reference projection lemmas (`payOut_lastGoodPrice`, `depositState_lastGoodPrice`, `withdrawInstantState_lastGoodPrice`, `claimState_lastGoodPrice`) and removed the four trailing `rfl`s they replace in `Frame.lean`. `Outcome.ok.injEq] at` fell from 93 to 68. | projection lemmas for the other fields; the remaining 68 `injEq` sites (mostly the unguarded `setLimit`-style entry points and `Catalogue.lean`/`Invariants.lean`) |
| 1.4 Operator API in `Chain.lean` | partial | the `decodeState` simp lemmas live in `Chain.lean`; `wset_hit`, `wset_miss`, `wset_eq_update` | `Wf.upd_wset…` preservation lemmas and replacing the 111 `simp [wset]` calls (this overlaps 2.1) |
| 1.5 `@[ext]` on compared states | partial (this execution) | `@[ext]` on `Fame.RotationFSM.State`; the eight `simp only [decodeState, State.mk.injEq]; refine ⟨?_, ?_, ?_, ?_, ?_, ?_⟩` blocks of `simulation_square` became `apply State.ext` with named `case store => …`, `case externalIn => …`, … goals | the other state records (`ASP.Vault.State`, Venue `State`, `Concrete`) and the remaining `.mk.injEq` sites (`Fame/Evm/Write.lean`, `Slots.lean`, `Observe.lean`, `Venue/Adopted.lean`) |
| 1.6 Canonical constants | partial (this execution) | `ASP.ABI.wordModulus_eq` and `ASP.ABI.cast_wordModulus` next to the definition; `decodeInt_wordInt` no longer re-spells `2 ^ 256` | `fuel` vs `320` in `Fame/Evm/Full/*` (88 sites); one spelling of `2 ^ 64`/`2 ^ 32` per module |
| 1.7 Equation lemmas for downstream `unfold` | open | baseline recorded: `downstream_unfold` = 997 | all of it |

### 5.3 Tests (new and updated)

`RequestProject/StyleRefactorTests.lean` is the regression net around everything Phase 1 touched.
It follows the project's property-suite shape (header block, laws proved first and then sampled
with Plausible at pinned seeds, negative controls, unit pins, a fail-closed runner):

* **Five Plausible property laws**, each also a theorem: `foldr max` bounds its seed and every
  element; `foldr max` is the seed or an element; `foldl max = foldr max`; `foldr min` bounds its
  seed and every element; the deposit gate accepts exactly when its three guards hold (the last one
  is `ASP.Vault.deposit_eq_ok_iff` read as a Boolean). 200 cases each.
* **Two negative controls** the sampler must falsify, each also refuted by a kernel-checked
  theorem: a fold that forgets its seed (`seedIgnoredControl_false`) and a deposit gate without the
  ledger cap (`noCapControl_false`).
* **Two counterexamples** (`∃ …` witnesses showing a hypothesis is needed):
  `foldr_max_le_needs_seed_bound` (the seed bound of `List.foldr_max_le`) and
  `deposit_needs_exact_transfer` (the exact-transfer guard of `deposit_eq_ok_iff`; this execution
  reproved it through that lemma).
* **Three negations** (`¬ ∀ …`): `not_forall_foldr_max_mem` (the seed disjunct cannot be dropped),
  `not_forall_withdrawInstant_ok` (withdrawal guards are load-bearing) and
  `not_forall_solventOrder_append_of_solvent` (the second block is judged from the depleted
  headroom).
* **Unit tests** at the boundaries: the empty list, a seed above every element, `amount = 0`,
  `totalDeposits + amount = maxLedger` exactly and one past it, `moved ≠ amount`; plus the evaluated
  pins `styleRefactorPins`.

Changes made in this execution: the four compile errors of §3 row 2 were fixed; the suite was wired
into `RequestProject/TestingPlan.lean` as `style-refactor-properties`, so `lake test` runs it; the
compile-time pins got a row in `property_registry.json` (`style-refactor.compile.pins`); the
`ListFold` checks became kernel-checked examples. Every test theorem has the standard axiom
footprint (`propext`, `Classical.choice`, `Quot.sound` or fewer).

Tests touching changed code were re-run: every module that imports a changed file was rebuilt by the
full build (its `#guard`s, `example`s and theorem tests included), and `audit_lean_proof_style.py
--selftest` covers the new metrics.

## 6. Verification (§6.6 of the review)

| Check | Result |
|---|---|
| `lake build` (default targets) | exit 0, 9,090 jobs, **5 warnings** — the same five unused-variable warnings in the pinned `HandoffV3/FreerBridgeChecks.lean` |
| Promoted linters, PL1 | `check_promoted_linters.py --log` clean on the full-tree log (1,053 modules elaborated with the lakefile options) and on the final incremental log |
| Promoted linters, PL2/PL3 | `--fixture`: all four promoted linters warn on the trigger fixture; `--selftest` passes |
| `linter.flexible` (on demand) | silent on the four 0.3 files and on every file changed in this execution; the trigger fixture makes `flexible`, `multiGoal` and `show` fire under the same flags |
| Style suite | `StyleRefactor.Tests.run` → `true`: 5 laws succeed at 200 cases, both controls falsified, all pins true |
| Axioms | `#print axioms` on the test theorems, `simulation_square`, `price_reference_is_written_only_by_settlement_and_seed`, `decodeInt_wordInt`: standard footprint only; axiom audit regenerated with the two new modules in its import list |
| Text audit | `--selftest` passes; `--ratchet` passes with the baseline below |
| Registry | `audit_property_registry.py` passes (1,225 rows) |

## 7. Before and after, in numbers

"Before" is the review's measurement (its Appendix D and §2) unless stated otherwise.

| Measure | Before | After |
|---|---:|---:|
| Build warnings | 5 | 5 |
| Linters in the build (`lakefile.toml`) | 5 (`style.maxHeartbeats`, `style.setOption`, `style.refine`, `style.cases`, `style.induction`) | the same 5 + `multiGoal`, `show`, `unusedDecidableInType`, `unusedFintypeInType` |
| `linter.flexible` sites | 2 (+2 dotted-identifier blind-spot sites) | 0 |
| Unused `DecidableEq`/`Fintype` binders | 30 | 0 |
| Reflexive theorems without the tautology note | 10 | 0 |
| Private fold-max/min copies | 40 (+4 two-element permutation lemmas) | 0 (one shared module) |
| `V3Proofs.replay_*` duplicates | 3 | 0 |
| `Outcome.ok.injEq] at` | 93 | 68 |
| `@[ext]` attributes | 5 | 6 |
| `State.mk.injEq` + positional six-hole `refine` in `simulation_square` | 8 | 0 |
| Trailing `rfl` after `simp` in `Frame.lean`'s price-reference theorem | 4 (this execution's starting point) | 0 |
| Recorded departures in `LEAN_PROOF_STYLE.md` | 1 (spec-identifier names) | 4 (+ scoped `show`, `Prop`-def casing, `snake_case` guards/mutants) and new rules R20a, R28 |
| Ratchet metrics | none | 6, baselined: `rename_i` 147, `unscoped_maxRecDepth` 38, `show_open_bullet` 3, `reflexive_statement` 13, `downstream_unfold` 997, `duplicate_statement` 264 |
| Property suites run by `lake test` | — | + `style-refactor-properties` |
| `sorry` / `axiom` / `@[implemented_by]` | 0 / 0 / 0 | 0 / 0 / 0 |

## 8. Files changed

Changed in this execution:
`docs/standards/LEAN_PROOF_STYLE.md` (0.6), `scripts/audit_lean_proof_style.py` and
`docs/standards/lean_style_ratchet.tsv` (0.7), `scripts/run_checks.sh` (ratchet in the battery),
`RequestProject/StyleRefactorTests.lean` (compile fixes; counterexample via the new API),
`RequestProject/TestingPlan.lean` (suite wired in), `property_registry.json` (suite row),
`RequestProject/Util/ListFold.lean` (kernel-checked examples), `RequestProject/ASP/Phase4/ABI.lean`
(1.6), `RequestProject/ASP/Phase7/Transitions.lean` and `RequestProject/ASP/Phase7/Frame.lean`
(1.3), `RequestProject/Fame/Rotation/Machine.lean` and `RequestProject/Fame/Operator/Refinement.lean`
(1.5), `scripts/AxiomAudit.lean` and `docs/latex/axiom_audit.tsv` (audit coverage), this report and
`NOTES.md`.

Already in the tree when this execution started and verified here: the Phase 0.1–0.5 changes and
Phase 1.1, 1.2 and the first part of 1.3/1.4 listed in §5.

## 9. Outstanding work and blockers

* **Phase 1, remaining:** 1.3 (other projection lemmas, 68 `injEq` sites), 1.4 (`Wf` preservation
  lemmas), 1.5 (other state records), 1.6 (`fuel`, `2 ^ 64`/`2 ^ 32`), 1.7 (equation lemmas; 997
  downstream `unfold`s).
* **Phases 2–4:** not started; their prerequisites from Phases 0–1 are marked in §2.
* **Open decisions:** D-1 (second copy of the guide), D-6 (owner of the vault API).
* **Operational:** see §10.4 for the battery result after the follow-up pass and the exact cause
  of every remaining failure.

## 10. Follow-up pass: answers to the review of this execution

A review of the session log raised eight points and seven recommended actions. Each is answered
below with the evidence that settles it; every file named is in `data/` unless a path is given.

### 10.1 Point by point

| # | Point raised | Finding | Evidence |
|---:|---|---|---|
| 1 | `-Dweak.linter.X=true` only enables a warning; the gate was never shown to catch a violation. | The gate catches violations. `scripts/check_promoted_linters.py --log` on a log of a file that violates each of the four promoted linters exits 1 and names all four sites; the same file under `-DwarningAsError=true` fails with four errors. On the tree, `lakefile.toml` keeps the linters at warning level by design (they must not break the core-only libraries), and enforcement is the log gate PL1, which is in `run_checks.sh`. | `enforcement_violation_lean.txt`, `enforcement_violation_gate.txt` (`gate=1`), `enforcement_warningAsError.txt` (`wae=1`) |
| 2 | Lake replays cached warnings, so "5 warnings" is unsupported. | A from-scratch build (`rm -rf .lake/build && lake build`) was run: 9,090 jobs, 1,060 modules compiled, 0 errors, exactly 5 warnings, all unused variables in the pinned `HandoffV3/FreerBridgeChecks.lean`. PL1 is clean on that log. The incremental builds after the follow-up edits print the same 5 (replayed for the unchanged pinned file) and PL1 is clean on them too. | `clean_build_summary.txt`, `promoted_linters_clean_build.txt`, `final_build_summary.txt` |
| 3 | `StyleRefactorTests.lean` "never compiled". | True before §3 row 2; fixed. The from-scratch build compiled `RequestProject.StyleRefactorTests` as part of the default target (`RequestProject` glob `RequestProject.+`), and `RequestProject.TestingPlan` runs it under `lake test`. Re-run in this pass: 5 laws succeed at 200 cases, both negative controls are falsified, `run` returns `true`. | `clean_build_summary.txt` (the `Built RequestProject.StyleRefactorTests` line), `suite_run.txt` |
| 4 | The axiom audit was stale and its regeneration unconfirmed. | Regenerated and compared as sets of axioms per declaration: 24,485 → 24,547 rows, 62 added (the `ListFold`/`StyleRefactorTests` declarations, the `*_lastGoodPrice` lemmas, and Phase 0.1–0.5 declarations missing from the stale file), 0 removed, 1 changed and that one got smaller (`Fame.Evm.execOp_gasUsed_le` lost `Classical.choice`). No declaration uses `sorryAx`; the axioms used anywhere are `propext`, `Classical.choice`, `Quot.sound`, and the `Lean.ofReduceBool`/`Lean.trustCompiler` pair from pre-existing `native_decide` sites. The follow-up edit to `decodeInt_wordInt` leaves its footprint unchanged (`propext`, `Classical.choice`, `Quot.sound`), so the TSV is still current. | `axiom_audit_diff_summary.txt`, `axiom_audit.diff` |
| 5 | The `#print axioms` output was never shown. | Archived. All eleven spot-checked theorems use `propext`, `Classical.choice`, `Quot.sound` or fewer; none uses `sorryAx`. | `axioms.txt` |
| 6 | Re-adding `cast_wordModulus` before `omega` is a per-site band-aid. | Agreed, and fixed. `decodeInt_wordInt` now states `wordModulus = 2 ^ 256` once, as `have hW := wordModulus_eq` at the top of the proof, and every arithmetic step is a plain `omega` that reads it from the context. The five `rw [wordModulus_eq]; omega` steps, the `cast_wordModulus` rewrite and three of the five auxiliary `have`s are gone. A global `wordModulus_lt` lemma was not added: no bound is shared between sites (each `omega` proves a different inequality), and `wordModulus_eq` is already the single fact they all need. `cast_wordModulus` stays as public API next to the definition. | `RequestProject/ASP/Phase4/ABI.lean`; build and strict-lint rows below |
| 7 | `simpNF` on the new `_lastGoodPrice` lemmas was never checked. | Checked with `#lint only simpNF simpVarHead simpComm` on every module whose simp set changed: `Transitions` (where the four lemmas live), `Frame`, `ABI`, `Rotation.Machine`, `Operator.Chain`, `Util.ListFold`. 0 errors in each. | `simp_lint.lean.txt` (the command file), `simp_lint.txt` |
| 8 | `tail -2`/`tail -5` hide most of the selftest and fixture output. | The gate prints a one-line summary with counts; the archived lines are the whole output: selftest "4 planted log warnings, 4 silent linters, 8 coverage gaps rejected; clean log and full fixture output accepted"; fixture "all 4 promoted linters warn". | `promoted_linters_selftest.txt`, `promoted_linters_fixture.txt` |

Smaller observations: the `.lean.txt` fixture needs no manual copy step, because
`check_promoted_linters.py --fixture` copies it to a temporary `.lean` file itself
(`shutil.copyfile` into a `TemporaryDirectory`); line lengths were measured in characters, not
bytes.

### 10.2 Strict lint of every changed file

Every Lean file changed by this execution was elaborated with the promoted linters, `flexible`,
`unnecessarySimpa` and `style.longLine` switched on **and** `warningAsError=true`, so any hit is an
error and a non-zero exit. Six files exited 0. `Fame/Operator/Refinement.lean` failed on two
lines longer than 100 columns (a quoted formula in the module docstring and a `have` type); both
were wrapped and the re-run exited 0. (`style.longLine` is not part of the project's lint profile,
which does not enable the Mathlib standard set; it was included here because the request asked for
Mathlib-quality code.) File: `strict_lint_changed_files.txt`.

### 10.3 Lean changes in the follow-up pass

* `RequestProject/ASP/Phase4/ABI.lean`: the proof of `decodeInt_wordInt` (point 6). Statement
  unchanged, axiom footprint unchanged.
* `RequestProject/Fame/Operator/Refinement.lean`: two lines wrapped (10.2). No statement changed.

Both changes were followed by a full default-target `lake build` (exit 0, 9,090 jobs) and PL1 on
its log (clean). Derived documents that depend on line numbers or line counts were regenerated and
their checks pass: `docs/latex/properties.json` and `docs/latex/generated_catalogue.tex`
(`extract_properties.py --check`, `generate_properties_tex.py --check`); the `lean_lines` figure in
`DOCUMENTATION.md` and `docs/reviews/VERIFICATION_STATUS.md` with
`docs/reviews/GENERATED_COUNTS.md` (`generate_counts.py --check` and `--selftest`; the documents said
310,262 lines while the tree had 310,240 before this pass's edits; the tree now has 310,238); `docs/analysis/cvp/placeholder_census.tsv` and
`PLACEHOLDER_COUNT_FIXES_DRAFT.md`, which hash `DOCUMENTATION.md` (`tooling/cvp/check_all.sh`).

### 10.4 Source-only battery, before and after

`bash scripts/run_checks.sh --source-only` was run to completion (397 checks). Full output:
`checks_after.txt`; the run before any change of this execution: `checks_before.txt`.

| | Before | After this pass |
|---|---:|---:|
| Failed | 13 | 11 |
| Fixed | — | `generate_counts.py --selftest`, `generate_counts.py --check` |
| New failures | — | none |

The 11 that remain all failed before this execution, and none involves a Lean file:

| Check | Cause | Kind |
|---|---|---|
| `check_commit_bypass.py`, `check_hooks_location.py` | `core.hooksPath` is not set to `ci/hooks` in this clone and `ci/hooks/pre-commit` is recorded as mode `100644`, so git runs no committed hook. The local half is fixed by `bash scripts/setup_dev_env.sh`; the mode bit needs `git update-index --chmod=+x ci/hooks/pre-commit`, which also changes a row of the handover baseline, so it is left to the repository owner. | operational (clone set-up) |
| `handover_baseline.py --check`, and the one failing unit test (`test_dev_env_setup.py`, inside `run_unit_suites.py`) | The tree differs from the recorded handover baseline `ci/handover/baseline.tsv` (files added since it was recorded, including the audit folders), and the unit test expects a clean configured clone. Re-recording the baseline is an owner action (`docs/design/HANDOVER_INTEGRITY_2026_10_12.md`). | operational |
| `check_signer_dates.py` | Decision D-14 has a hard date of 2026-10-09 that has passed and is not recorded as met. A named signer must record `met YYYY-MM-DD` or re-date it. | governance decision (open) |
| `build_spec_omnibus.py --check`, `decision_map/run_decision_map.py --check` | `docs/SPECIFICATION_OMNIBUS.md` and `docs/analysis/decision_map/SCRATCHPAD.md` are stale against their sources. | derived documents owned by the specification process |
| `ica_audit.py --check`, `rsv_probes.py --check`, `rsv_audit.py --check` | The ICA and RSV generated views differ from what the tree regenerates; the scripts say this is a hand edit or stale inputs. | derived documents needing owner review |
| `regen.py --check` | Aggregates the five derived-document failures above. | follows from them |

The derived documents were deliberately not regenerated here: the scripts cannot tell a stale
input from a hand edit, and overwriting a hand edit to a specification view would destroy
information that only its owner can adjudicate.

### 10.5 Decisions after the follow-up pass

* **Closed:** D-2, D-3, D-4, D-5, D-7 (recorded in `docs/standards/LEAN_PROOF_STYLE.md`, §5.1).
* **Open:** D-1 (second copy of the guide), D-6 (owner of the vault API). Outside the style
  review, the battery also reports project decision D-14 as past its hard date (10.4).
* **Open, new — D-8, axiom-audit cadence.** A full regeneration of `docs/latex/axiom_audit.tsv`
  elaborates about 24,500 declarations and runs for tens of minutes, too slow for every commit.
  Recommendation: full regeneration and `check_axiom_budget.py` nightly; on pull requests, run
  `scripts/AxiomAuditMemo.lean --module <M>` for each changed module and fail on any new axiom or
  `sorryAx`. The battery already runs this per-module form once. Needs CI-owner sign-off.

### 10.6 The seven recommended actions

| # | Action | Status |
|---:|---|---|
| 1 | `StyleRefactorTests` builds in the default target | done (10.1 #3) |
| 2 | Tree-wide fresh lint with errors, exit code archived | done for the four promoted linters (from-scratch build + PL1, exit 0) and for every changed file with `warningAsError` (10.2). A tree-wide `linter.flexible` run with errors was not repeated (about 1.5 h at 8 jobs per the review); the changed files are covered. |
| 3 | Finish the axiom regeneration, diff, archive `#print axioms` | done (10.1 #4, #5) |
| 4 | Decide on `hmod`; one fact, no per-site band-aid | done (10.1 #6) |
| 5 | `simpNF` on `Transitions` and `Frame` | done, and on four more modules (10.1 #7) |
| 6 | `run_checks.sh` to completion, diff against before | done (10.4) |
| 7 | Full-output selftest/fixture runs | done (10.1 #8) |
