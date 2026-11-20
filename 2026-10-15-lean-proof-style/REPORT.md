# Lean proof-style audit, second pass — 2026-10-15

Input: the Trail of Bits Lean 4 proof-writing guide (27 rules), supplied again. The repository
adopted that guide on 2026-10-14 as `docs/standards/LEAN_PROOF_STYLE.md`, and the first measured
pass is `audit/2026-10-14-lean-proof-style/REPORT.md`. This report re-measures the tree against
the same rules, works down the backlog that report left, and records what remains and why.

The supplied text matches the adopted standard rule for rule. Rule 9 ("one tactic invocation per
line, in general", applied as readability guidance) and Rule 4 (gate unproved obligations through
the kernel's per-declaration axiom footprint, never through grep) are already worded this way in
`LEAN_PROOF_STYLE.md`. The standard therefore needed no rule changes; §6 lists the two
clarifications that were added.

Scope: the 1,078 tracked `.lean` files. Every Lean edit below was checked by building the edited
modules, and the whole set by a full `lake build` (9,077 jobs, exit 0; §5).

## 1. Summary

| Rule | Check | 2026-10-14 after | 2026-10-15 before | 2026-10-15 after |
|---|---|---:|---:|---:|
| R4 unproved obligations | kernel axiom audit | 0 `sorryAx` | 0 | 0 (§5) |
| R4 / lint policy: build warnings | full `lake build` log | — | **130** | **5** |
| — of which dead `grind` parameters | core `grind` warning | — | 84 | 0 |
| — of which unused `simp` arguments | `linter.unusedSimpArgs` | — | 28 | 0 |
| — of which unscoped `set_option maxHeartbeats` | `linter.style.setOption` | 10 | 10 | 0 |
| — of which `<;>` where `;` suffices | `linter.style` (seq focus) | — | 2 | 0 |
| — of which unused variables | `linter.unusedVariables` | — | 6 | 5 (pinned file, §4) |
| R8 honest `show` | `linter.style.show` | 3 | 3 | **0** |
| R10b non-terminal `simp` | `linter.flexible`, distinct sites | 14 | 14 | **1** |
| R10b non-terminal `simp`, text heuristic | `audit_lean_proof_style.py` | 129 | 46 | 8 (§3.4) |
| R1a/R16 `rfl` right after `simp` | text heuristic | — | 24 | **7** (§3.3) |
| R1a/R16 `rfl` right after `rw` | text heuristic | 232 | 196 | 194 |
| R3 one focused goal | `linter.style.multiGoal` | 0 | 0 | 0 |
| R1a `erw`; R17 `irreducible`; R22 global `Fact` | text | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| R4/R18 `axiom`, `@[implemented_by]` | text | 0 / 0 | 0 / 0 | 0 / 0 |

"2026-10-15 before" is the tree as delivered to this session (`2fe6487`). The text heuristic for
`rfl`-after-`simp` was split from `rfl`-after-`rw` after the first report, so it has no 2026-10-14
column. The 2026-10-14 report counted the build's linter warnings only for the five opt-in
linters (10); the core warnings in the first rows had not been counted before.

## 2. Build warnings (R4 "verify mechanically", R10d)

The full build printed 130 warnings. They are all Lean's own diagnostics, so each one names its
site exactly and the build confirms the fix. Per-site lists: `data/build_warnings_before.tsv` and
`data/build_warnings_after.tsv`.

- **112 dead tactic arguments (38 files).** 84 `grind [...]` parameters were already `@[grind]`
  lemmas in the environment, and 28 `simp [...]` arguments were never used. These are lists
  copied between look-alike goals, which R10d warns against. `tools/remove_dead_args.py` removes
  only the argument printed at the reported line and column, and only when the text there matches.
  It skips `HandoffV3/` and leaves anything it cannot match (nothing was left). All 112 were
  removed, and the build passed with no other change.
- **10 file-level `set_option maxHeartbeats`** in the EVM bytecode proofs
  (`RequestProject/Fame/Evm/AnyCalldata.lean`, `Exec.lean`, and `Full/{Dispatch, ExecCollateral,
  ExecDispatch, ExecEscrow, ExecLifecycle, ExecRisk, ExecValue, Gas}.lean`). The first report left
  these as backlog because it expected each file to need a per-declaration budget. Measured: with
  all ten lines removed, all ten modules elaborate within the default budget (build times 10–194 s
  per module). So no declaration needed `set_option … in`, and the lines were deleted. The
  `maxRecDepth` lines next to them are not governed by the linter and were kept, with an updated
  comment. `UNSCOPED_RESIDUE` in `scripts/check_lean_lint_options.py` is now empty. LP5 still
  rejects any new unscoped site, and the self-test still plants a stale residue entry (9 planted
  violations rejected).
- **2 `tac <;> exact …` chains** in `RequestProject/Sim/Hash.lean`, where the first tactic leaves at
  most one goal. Each injectivity proof is now one terminal `simp_all` that is given the
  injectivity fact (`boolToNat_injective.eq_iff`, `encodeRefusal_injective.eq_iff`). This also
  removed the two `linter.flexible` sites there.
- **1 unused hypothesis.** `Venue.Recovery.netting_recovers_exactly_once` took
  `(hnet : completes .netting sched = true)` and never used it. It was removed, so the theorem is
  now more general: nothing in the tree passed it, and the only other references are by name (the
  task register's anchor). The docstring now says that the recorded batch alone is enough. This
  is the one statement change in this pass (R15: a statement is an interface).
- **Remaining 5:** unused variables in `HandoffV3/FreerBridgeChecks.lean`. That file must stay
  byte-identical to §11 of `IMPLEMENTATION_DOCUMENT_v3_FINAL.md` (`scripts/v3_landing_check.py`),
  so it can only change through that document.

## 3. Proof-style changes

### 3.1 R8: the last three goal-changing `show`s

`HandoffV3/Obligations/QuantPolicyV2.lean:425`, `HandoffV3/Obligations/QuantRounding.lean:294`
and `HandoffV3/Research/QuantClosures.lean:108` now use `change`. The first report left them
because `HandoffV3/` is checked against the frozen v3.0 text. That check byte-pins only `Kernel`,
`FreerBridgeChecks` and `Resolutions`, so these three files can be edited. `linter.style.show` now
reports nothing on the linted files.

### 3.2 R10b: the remaining `linter.flexible` sites

Of the 14 distinct sites left on 2026-10-14, 13 were restructured. Where squeezing was impossible
(several `simp?` lists per call), each was rewritten in one of the two forms the guide allows: a
rigid case analysis, or a single terminal flexible call.

| Site | Change |
|---|---|
| `ASP/Phase7/CallV2.lean` `run_eq_liftVault_of_unchanged` | `cases c <;> cases hd <;> first \| rfl \| cases hu`; no `simp_all` |
| `Feeds/EthFeed.lean` `selectPrice_source` | four focused cases, `cases h` on the equation; `simp only [selectPrice]` before `split_ifs` |
| `Governance/Signoff.lean` `surjective_of_three` | the `simp_all` step dropped; contradictory branches closed by `absurd` on the distinctness hypotheses |
| `Main.lean` `descending_take_sum_ge_subperm`, `cons₂` | `rcases` split into two focused cases with `simpa … using` |
| `Sim/Hash.lean` (2) | see §2 |
| `Sim/Rigor.lean` `shrink_event_preserves_domain` | the trailing `subst; trivial` replaced by a terminal `simp [he', Event.inDomain]` |
| `Venue/Obligations.lean` amend case | `repeat' split` first, then one terminal `simp` per branch |
| `TestReportingInvariants.lean` `counterexampleWellFormed_iff_db` | the 18 concrete cases closed by `rfl`; no `simp` before it |
| `HandoffV3/Proofs/Corpus.lean` (4) | `by simp [depth]; exact …` → `by simpa [depth] using …` |

Left: `Fame/Evm/Gas.lean:70` (`execOp_gasUsed_le`). Its `all_goals try simp_all` feeds a
`rcases m.stack` across every opcode branch. Folding the `simp_all` into the terminal chain was
tried, and `omega` then failed on the `SWAPn` branches, so the edit was reverted. Fixing it means
stating the per-branch stack facts as lemmas, which is an API decision for the EVM module owner.

### 3.3 R1a/R16: `rfl` closing straight after `simp` (missing-API smell)

24 sites before, 7 after. The 17 fixes:

- **New API lemmas (8), each in the same file as its definition:**
  - `Prog.lift_bind` (`DetSim/Log/Freer.lean`): `lift c >>= f = Prog.bind c f`.
  - `runAlg_str_emitF`, `runAlg_str_setVarF`, `runAlg_str_getVarF` (`DetSim/Log/InitialAlgebra.lean`):
    the three clauses of the interpreter algebra.
  - `emit_eq_emitF`, `emit_eq_lift`, `setVar_eq_lift`, `getVar_eq_lift` (`DetSim/Log/Tagless.lean`):
    the `MonadSimLog` operations of the syntax and Freer instances.

  All are `@[simp]`, proved by `rfl`, and have docstrings. With them, `runF_eq_cata`,
  `interpret_prog`, `hom_eq_cata` and `ofChurch_nonParametric` close by rewriting, without
  unfolding.
- **Missing simp lemmas at the call site:**
  - `Function.comp_def` (`Fame/LMM/Flow.lean`, `PaperTests/BoundedLevelCeilingTests.lean`,
    `Production/Absorption/Tests.lean`, `RelayCycleValue.lean`).
  - `Bool.false_eq_true, if_false` (`DetSim/Schema/Fields.lean`).
  - The full `bindF`/`runF`/`DetSim.bind` set that the sibling cases already used
    (`DetSim/Log/Free.lean`).
- **List sum versus `Finset.sum`** (`RelayCycleValue.lean`, `HandoffV3/Research/QuantClosures.lean`):
  the closing `rfl` relied on `∑ x ∈ Finset.range n` reducing to a list sum. It is now the explicit
  rewrite `Finset.sum_eq_multiset_sum, Finset.range_val, ← Multiset.coe_range, Multiset.map_coe,
  Multiset.sum_coe`.
- `GEX/Match/Translation.lean`: a typed `have hqty`, matching the existing `hside`.
- `Venue/Mutants.lean` `refParts_rests`: `cases t <;> decide`.

The 7 left are legitimate uses of `rfl`:

| Site | Why `rfl` is right |
|---|---|
| `DetSim/Log/TaglessLog.lean:64`, `DetSim/Log/Tagless.lean:199` | the goal is `pure x = x` in `Id`, an identity that holds by definition and that no `simp` lemma states |
| `Fame/Foundation/Numeric.lean:114,127,138` | evaluation of a closed parser run on a literal string |
| `Venue/IntakeExport.lean:231`, `HandoffV3/Obligations/QuantPolicyV2Tests.lean:224` | the two sides print identically but use different compiler-generated `match` functions; `rfl` sees through them and `simp` cannot (tried, and reverted) |

### 3.4 R10b in modules the linter cannot see

`linter.flexible` is a Mathlib linter, which `scripts/lean_style_linters.sh` passes with `weak.`.
The core-only libraries (`DetSim`, `DecisionMap`) do not load Mathlib, so the option is silently
ignored there. The 2026-10-14 linter pass therefore could not report any site in those libraries.
The text heuristic found 46 candidate sites:

- **27 squeezed** with `tools/squeeze_sites.py`, which uses the `simp?` list printed for each site
  (R10d), keyed by file, line and column. Every site had exactly one list. They are in
  `DetSim/{Canonical, Clock, Fault, Merge, Seed}.lean` and in five `RequestProject` files where the
  linter does not flag `simp … at h` followed by `subst`.
- `SWC/Step.lean` `gate_eq_some`: `cases b <;> simp [gate, eq_comm]`.
- **The 7 sites left are all in `ASPModel.lean`** (repository root). That file is in no
  `lean_lib`, so it is never built, linted or axiom-audited. It is an older copy of
  `RequestProject/ASP/WholeContract/Skeleton.lean`, which is built and in which the same seven
  sites were squeezed. **Open decision:** delete `ASPModel.lean` or archive it outside the Lean
  tree. It was not deleted here because it is tracked content and appears in the handover baseline.
  *Resolved later on 2026-10-15:* the file was moved out of the Lean tree to
  docs/archive/root/ASPModel.lean.v420 (deleted) with an archive banner, and the handover baseline was
  re-recorded.

## 4. Not changed, with reasons

- **R7 untyped `have h := …` (2,316)**, **R26 upper-case theorem names (96)**, **`native_decide`
  (122)**: unchanged from the first report, with the reasons it gives (heuristic upper bound;
  specification identifiers that the registry keys on; tier-2 footprint gated by
  `check_axiom_budget.py`).
- **R13: 32 declarations over 150 lines, 7 files over 1000 lines.** The same list as the first
  report. Splitting a file moves declarations between modules, which changes the module column
  that the axiom audit, property registry and claim index key on. It needs an owner decision per
  file.
- **R1a/R16 `rfl` after `rw` (194).** As the first report says, this is mostly a `rw [h]` that
  leaves a definitional unfolding. It is informational only.
- **`HandoffV3/FreerBridgeChecks.lean`**: five unused variables. The file is byte-pinned (§2).

## 5. Verification

- Full `lake build`: 9,077 jobs, exit 0, 5 warnings (all in the pinned file of §2).
- `scripts/lean_style_linters.sh` over every Lean file edited in this pass plus the files of the
  remaining 2026-10-14 sites: 0 elaboration failures. `show`: 0. `multiGoal`: 0. `flexible`: the
  single `Fame/Evm/Gas.lean:70` site.
- Kernel axiom audit regenerated from the compiled environment (`scripts/AxiomAudit.lean`,
  `docs/latex/axiom_audit.tsv`): 24,144 theorems, 0 depending on `sorryAx`.
  `check_axiom_budget.py` passes (109 tier-2 facts against a ceiling of 109, no tier-3
  dependency), and `check_no_axioms.py` passes. Compared with the committed audit:
  - 8 rows were added, one for each new API lemma of §3.3.
  - 9 existing rows changed, all within {`propext`, `Quot.sound`}:
    - 6 footprints shrank. `selectPrice_source`, `selectPrice_pos`, `surjective_of_three` and
      `refParts_rests` are now axiom-free. `step_journal_is_appended` and
      `replay_journal_is_appended` no longer use `Quot.sound`.
    - 1 grew: `interpret_prog` now also uses `propext`, through `simp only`.
    - 2 compiler-generated equation lemmas (`SWC.gate.eq_1`, `Venue.Mutants.refParts.eq_1`) moved,
      with unchanged empty footprints, to the module that now generates them first.
- `python3 scripts/check_lean_lint_options.py` and `--selftest` pass.
- Repository check battery:
  - `--source-only`: 377 passed and 2 failed out of 392.
    - The D-14 signer date is overdue, and only its named signer can record or re-date it.
    - The handover baseline was re-recorded afterwards, and `handover_baseline.py --check` now
      reports a lossless handover.
  - Derived artefacts that the Lean edits made stale were regenerated with the repository's own
    generators (`scripts/regen.py`, `audit_test_census.py --write`). This covered the axiom audit,
    the stated counts in `DOCUMENTATION.md`, `docs/reviews/VERIFICATION_STATUS.md` and
    `docs/demo/claims_manifest.json`, and one source hash in
    `roadmap_artifacts/matching_dependency_closure.json`.
  - `--post-build`, after the non-default executables were built: everything that depends on the
    Lean tree passes. Two checks fail on drift that this pass did not cause; neither file nor its
    inputs was touched.
    - `run_seam_differential.py --check`: regenerating would turn an `agreed` row into `skipped`,
      because this machine has no Foundry build output.
    - `generate_roadmap_evidence.py --check`: the stored registry-audit headline predates rows
      added in earlier sessions.

## Files

- `tools/remove_dead_args.py`: removes `simp`/`grind` arguments that the build reports as dead.
- `tools/squeeze_sites.py`: replaces a non-terminal `simp` with its own `simp?` list.
- `data/build_warnings_{before,after}.tsv`: every build warning, by file, line and kind.
- `data/text_metrics_{before,after}.tsv`: the text audit before and after.
- `data/nonterminal_simp_heuristic_after.txt`: the heuristic sites before §3.4 was applied.
