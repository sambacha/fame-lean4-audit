# Guideline review of the 2026-10-19 leverage-list work: execution report

Companion to `REVIEW_AND_PLAN.md` in this directory, which records the findings (P-, D-, N-, L-, F-
and T- ids) and the plan. This report records what was changed, how each change was checked, and
which corrections to the review came out of the work.

## 0. Decisions that governed the work

| Question | Answer |
|---|---|
| Q1 precedence | The guide applies **verbatim**. The repository's recorded departures (D-2, R10a, D-4) were set aside for this work |
| Q2 renames | Rename **outright**, with no deprecated aliases. Every register is updated in the same change |
| Q3 scope | **Full**: the project-wide lint profile, plus a split of the fixtures into their own test module |
| Q4 helpers | The `CVal`/`CList` helpers move into `RequestProject/Venue/JournalFormat.lean` |
| Q5 axiom gate | **Keep** the `#print axioms` pins and add a module-wide `collectAxioms` sweep beside them |

Later instructions from the user:
* `encode_ne_of_ne` and `project_eq_of_encode_eq` keep their `Bounded` hypotheses.
* A negative control is required: `not_forall_encode_ne_of_ne`.
* The Property/Evidence-tier header block on test files stays. It is the house convention.
* The registers are kept in sync with every rename.

## 1. Disposition of every finding

| ID | Status | What was done |
|---|---|---|
| P-1 | Fixed | `Projection.Bounded` is reordered to follow the field order of the encoding. `Projection.toCanonical_wf_iff` is now a single **terminal** `simp`, with no trailing `tauto` |
| P-2 | Fixed | The `have`s with a non-obvious type are gone, either typed explicitly or replaced by API lemmas (`Book.canonical_eq_self_of_pairwise`, `project_*`) |
| P-3 | Fixed | No line in the library module holds two state-changing tactics |
| P-4 | Fixed (verbatim, per Q1) | `show` lines now open the case arms and the witness choices |
| P-5, P-7 | Note | No change needed |
| P-6 | Fixed | `by` follows `:=`, and the long lines are wrapped |
| D-1 | Fixed | Added `Book.canonical_eq_self_of_pairwise` and the `project_*` simp lemmas. No downstream proof unfolds `Book.canonical` or `project` |
| D-2 | Fixed (Q4) | `CList.ofList/toList`, `CVal.toNat?/toInt?/toBool?` and their lemmas now live in `JournalFormat.lean`, together with `@[simp]` WF constructor lemmas (`CVal.wf_null/bool/int_iff/str_iff/arr_iff`, `CList.wf_nil/wf_cons_iff`, `count_nil/cons`) |
| D-3 | Fixed | `Reason.optToCVal` / `Reason.optOfCVal?` added, with their round-trip and WF lemmas |
| D-4 | Fixed | `InI64` sits beside `CVal.WF`, with a `Decidable` instance and `inI64_natCast_iff`. `CVal.wf_int_iff` is stated with `InI64` |
| D-6 | Fixed | The instances use `inferInstanceAs` |
| D-7 | Fixed | `Projection` has `@[ext]` |
| D-8 | Fixed | `mapM_some_eq` is gone. The one private helper left, `mapM_map_eq_some`, states a different fact: a left inverse mapped over `l.map g` |
| N-1 | Fixed | `Projection.encode_injective` was renamed `Projection.eq_of_encode_eq` |
| N-2 | Fixed | `encode_project_injective` was renamed `project_eq_of_encode_eq` |
| N-3 | Kept | The `Bounded` hypotheses stay, per the user's instruction |
| L-1 | Fixed; see correction C-4 | The leftover `#check` is removed. Silent `#guard` assertions now satisfy the project's rule that every file has a live check |
| L-2 | Fixed (Q5) | `Venue.LeverageAudit.leverageSweep`: a `collectAxioms` sweep over every declaration of the library and test modules |
| L-3 | Not changed | The checker reads statements by regex. This is inherited from the house checker family and is out of scope |
| L-4 | Fixed; see correction C-3 | Vacuity anchors added to `DeclarationNames`, `ICACensus`, `NativeDecideTcb` and `ProfEnv` |
| L-5 | Recorded | `linter.auxLemma` does not exist at Mathlib `8f9d9cff`, and a `weak.` prefix would silently ignore it. `LEAN_LINT_POLICY.md` records this |
| L-6 | Fixed (Q3) | `weak.linter.flexible = true` is in `lakefile.toml` |
| L-7 | Fixed (Q3) | The fixtures, mutants, witnesses and `#guard`s moved to `RequestProject/Venue/CanonicalProjectionTests.lean` |
| F-1, F-2 | Note | No change needed |
| F-3 | Not changed (process) | Pushed history is not rewritten. Future performance changes get their own commit |
| T-1 | Fixed; see correction C-2 | `!` replaced by `?` with an error message |
| T-2 | Note | No change needed |

Details of the gate changes:
* **L-2 sweep.** It asserts the footprint `{propext, Classical.choice, Quot.sound}`, with `sorryAx` never allowed. It has three guards against passing vacuously: a `checked == 0` anchor, an anchor on `Venue.Projection.eq_of_encode_eq`, and a control run with an empty allow-list that must report offenders. A planted `sorry` was caught and then reverted.
* **L-6 flexible linter.** A full-tree build showed **zero** flexible warnings before promotion. The linter is listed in `scripts/check_promoted_linters.py` with a `trigger_flexible` fixture, and has a row in `LEAN_LINT_POLICY.tsv`.

## 2. Corrections to the review

* **C-1 (P-1 cause).** `audit_lean_proof_style.py` missed P-1 because `tauto` is in its flexible-tactic set, so a bare `simp` followed by `tauto` was not counted as non-terminal. Line wrapping of the `simp` call was not the cause. The new advisory metric `nonterminal_simp_strict` counts a bare `simp` followed by *any* tactic in its block. It has a self-test fixture, which was shown to fail when strict mode is disabled.
* **C-2 (T-1 count).** The panicking index occurred at **6** sites, not 9: `NativeDecideTcb`, `ProfEnv` (2 sites), `DeclarationNames`, `ICACensus` and `AxiomAuditMemo`. `DetSim/Audit` and `HandoffV3/Audit` already used `?`.
* **C-3 (L-4).** `HandoffV3/Audit` already had a floor of 400, so it needed no anchor. The text heuristic used in the review produced a false positive there.
* **C-4 (L-1).** The removed `#check` was a leftover probe, but it was also what satisfied the project's own `scripts/lint_lean_docs.py` rule: every file needs a live `#check`, `#eval` or `#guard`. Two silent `#guard`s now replace it:
  * in `CanonicalProjection.lean`, a decode round-trip of the initial state's projection;
  * in `LeverageAudit.lean`, the sweep covers both modules.

  Both are registered in `property_registry.json` (`compile-cmap3-roundtrip-initial`, `compile-leverage-sweep-modules`).
* **C-5 (naming).** `scripts/check_naming.py` (NM-L1) requires every declaration to be inside a namespace. The sweep definitions are therefore in `namespace Venue.LeverageAudit`.

## 3. Measurements

* **Sweep cost.** The first draft of the sweep took **406 s**, because it read `env.header.moduleNames` (which rebuilds an array) for each constant. Resolving the module indices once before the loop made the cost negligible. This is the guide's "no expensive per-constant work" rule, confirmed by measurement.
* **Metaprogram A/B.** The old and new versions of the hoisted metaprograms produced byte-identical stdout and output files: tcb, prof, `dn` (65,955 lines), `ica` (39,433 lines) and axmemo (96 lines). The new `NativeDecideTcb` and `ProfEnv` anchors fail closed (exit 1) when their filter matches nothing. The old versions exited 0.
* **Axiom audit.** `docs/latex/axiom_audit.tsv` was regenerated (about 22 min). The review with `--allow-module` and the budget check both pass.
* **Advisory backlog.** `nonterminal_simp_strict` reports **454 sites in 163 files** tree-wide. It is advisory, not a gate. Per the guide, it can be promoted only once it reaches zero. The count is recorded here so that the backlog stays actionable.

## 4. Gates run at the end

All of the following pass:
* a full `lake build` (9115 jobs) and targeted builds of the three touched modules;
* `check_promoted_linters --log`;
* `check_lean_lint_options`;
* `check_naming`;
* `lint_lean_docs`;
* `audit_property_registry`;
* `check_leverage_conjectures` and its self-test;
* `check_lean_test_style`;
* `check_axiom_audit_fresh` and its self-test;
* `check_no_axioms`.

The only build warnings are the unused-variable warnings in `HandoffV3/FreerBridgeChecks`, which were there before this work.

## 5. Known gaps left open

* `scripts/ICACensus.lean` does not import `RequestProject.Venue.CanonicalProjection`, so the ICA census has no rows for that module. The gap predates this work and is recorded here only. The census gained 27 rows for the new `JournalFormat` declarations.
* The `#guard_msgs` pins in `LeverageAudit.lean` are kernel-generated `info:` text, and several are longer than 100 characters. `linter.style.longLine` is not in the project profile, and the pins are left exactly as Lean prints them.
* L-3 (regex statement reading in the register checker) and F-3 (history not split) are unchanged, as recorded above.
* The open leverage items (C-MAP4 and the other `OPEN` or `BLOCKED-EXTERNAL` rows of `register/leverage_conjectures.tsv`) are unchanged by this work.
