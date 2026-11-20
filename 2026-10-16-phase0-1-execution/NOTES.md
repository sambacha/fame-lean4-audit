# Scratch notes — execution of Phases 0 and 1 of the 2026-10-16 style review

Working notes, kept while reading `audit/2026-10-16-lean-style-review/REPORT.md` line by line.
They are deliberately terse; the self-contained account is `REPORT.md` in this folder.

## Pass 1 — reading notes, section by section

### §0 Scope
- Guide lives in `docs/specs/lean-guide/` (no `rules/` dir). D-1 open. Not a code item.
- Precedence: guide is the rule; a departure is valid only if recorded in
  `docs/standards/LEAN_PROOF_STYLE.md` with a reason. → Phase 0.6 edits that file.
- Classes C / D / N / I. Severity High/Medium/Low/Info.

### §1 Method
- 1,088 `.lean` files, 1,054 library modules; full build 9,088 jobs.
- Linters were run per module with `-D` options (`tools/run_linters.sh`).
- Fixtures stored as `.lean.txt` so file-count checks are not disturbed. **Keep that convention**
  for any fixture we add outside a `lean_lib`.

### §2 Headline
- Build: 5 warnings, all in byte-pinned `HandoffV3/FreerBridgeChecks.lean`. Must not rise.
- Linters full tree: multiGoal 0, show 0, unnecessarySimpa 0, missingEnd 0, openClassical 0,
  flexible 2, unusedDecidableInType 16, unusedFintypeInType 14.

### §3 Corpus (23 items) — only those touched by Phases 0–1 noted
- #5 `ASP.Vault.Step.totalDeposits_mono` (LedgerCap.lean:293), #6
  `price_reference_is_written_only_by_settlement_and_seed` (Frame.lean:413): 16 identical arms.
  → Phase 1.3.
- #10 the 13 reflexive theorems → Phase 0.5.
- #15 `replay_append` family; `V3Proofs.replay_*` duplicates `Handoff.replay_*` → Phase 1.2.
- #16 fold max/min helpers, 40 copies in 17 files → Phase 1.1.
- #17 `Fame.Operator.Chain` API: `wset` = `Function.update`; simp lemmas for `decodeState`/`upd`
  live in `Refinement.lean` → Phase 1.4.
- #22 `ASP.PlanA.sequenced_admits` flexible site `:223`, unused `[DecidableEq ι]` → 0.3, 0.4.
- #23 `Fame.Evm.execOp_gasUsed_le` flexible site (`Gas.lean:70`) → 0.3.

### §4 Findings relevant to Phases 0–1
- SR-01 reflexive (0.5). SR-09 lint profile (0.1/0.2). SR-10 dotted-identifier blind spot
  (`Fame/Operator/Chain.lean:147`, `ASP/Phase5/Watchdog.lean:240`) (0.3). SR-11 30 unused instance
  binders (0.4). SR-23 2 flexible sites (0.3). SR-02/SR-33/SR-42/SR-43 policy records (0.6).
- SR-06 duplicates (1.1, 1.2). SR-13 API placement (1.2, 1.4). SR-14 vault API (1.3). SR-16 API not
  used (1.4). SR-18 constants (1.6). SR-19 `wset` (1.4). SR-20 `@[ext]` (1.5). SR-04 downstream
  unfold (1.7).

### §6 Plan — the steps to execute
- 0.1 promote multiGoal/show into lakefile (`weak.`) + TSV rows (LP1 needs both; LP3 needs the
  declaring Mathlib file).
- 0.2 gate on those warnings + vacuity anchor fixture.
- 0.3 fix 2 + 2 sites; flexible ratchet 0; extend `nonterminal_simp` to dotted identifiers.
- 0.4 remove 30 binders; enable `unused*InType`.
- 0.5 reflexive theorems: restate or annotate; fix create2 docstring.
- 0.6 record decisions.
- 0.7 ratchet metrics.
- 1.1–1.7 as listed.
- §6.6 verification after every phase: build exits 0 / warnings ≤ 5; linters; axiom audit;
  audit script ratchets; registry/claim index regeneration on statement or name change.

### §7 Open decisions D-1..D-7 — D-2, D-3, D-4, D-5, D-7 are *decided* by executing Phase 0 the
way the report recommends; D-1 and D-6 are untouched (ownership questions).

### Unused-instance sites (from `data/linter_outputs/*.out`, 30)
Dependency 181, 415 (DecidableEq ι); Red 264 (Fintype ι); AdmissionBranch 194, 223 (Fintype);
AnnualizedYieldBracket 331, 342 (DecidableEq); BucketDecomposition 306 (Fintype);
EpochFeasibility 109,116,122,132,146,154,164 (Fintype); EpochPipeline 314 (Fintype);
GEX/Match/Invariance 39 (DecidableEq α #6); Deputies 93 (Fintype), 128,153,205,245 (DecidableEq);
SingleBucketEvents 122 (DecEq), 175 (Fintype + DecEq), 185,195,205 (DecEq);
UniformInstanceValue 102 (DecEq); Venue/AdjudicationDelta 69 (DecEq).
Caveat to check: a binder unused in the *type* may still be used in the *proof*, and may come
from a section `variable` (then the fix is `omit … in`, not deletion).

## Pass 1 — dependency graph (draft)

- 0.1 before 0.2 (the gate reads promoted options); 0.4 before enabling unused*InType; 0.3 before
  the flexible ratchet; 0.5 before 3.1; 0.6 (D-2/D-4/D-7) before 2.x `show`, 3.2 and 4.1/4.2;
  0.7 guards Phases 1-3.
- 1.4 and 1.5 before 2.1; 1.6 before 2.2; 1.5 before 2.3/2.5; 2.1-2.5 before 2.6.
- Final, corrected version: REPORT.md §2.

## Pass 2 — corrections to beliefs

- Phase 0.1-0.5 already landed (lakefile, policy TSV, gate script, sites, docstrings). 0.6/0.7 not.
- StyleRefactorTests.lean never compiled: scoped notations `Amount`/`Address` (use `open scoped
  ASP`), an `if` left by `simp [deposit]`, uninferable bucket type, `prefixHeadroom` namespace.
  Also not run by `lake test`, no registry row.
- ListFold `#guard`s unregistered -> registry audit fails. Use kernel-checked `example`s.
- ABI `hmod` was read implicitly by a later `omega`; supply it at the call.
- Promoted-linter PL1 needs a log in which every module was elaborated: build 1 (1,053 modules).
- 0.7 metrics reproduce the review exactly (147 / 38 / 3 / 13); baseline them.
- New theorem modules must be imported by scripts/AxiomAudit.lean (check_axiom_budget coverage).
- Full account: REPORT.md §3.

## Cross-cutting concerns (summary)

- Never touch the pin; exclude it from duplicate counting.
- Every linter claim paired with a vacuity anchor (fixtures stay `.lean.txt`).
- New declarations: docstrings, registry row for compile-time checks, axiom-audit coverage.
- Warning budget stays at 5.
