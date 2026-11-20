# Lean proof-style audit and blocking-watch remediation — 2026-10-14

This report covers two inputs: the Trail of Bits Lean proof-writing guide, and the review note
on the blocking-watch anti-pattern (§3.11–§3.13). The standards these produced are
`docs/standards/LEAN_PROOF_STYLE.md` and `docs/standards/SHELL_PROCESS_STYLE.md`. This report is
the measured state of the repository against them, with the changes made.

Scope: the 1,078 tracked `.lean` files (331,341 lines). Lean's own linters were run over the 1,043
library modules of the default build targets (`RequestProject`, `AgentHandoff`, `HandoffV3`,
`DetSim`, `DecisionMap`).

## 1. Summary

| Rule | Check | Before | After | Change |
|---|---|---:|---:|---|
| R4 unproved obligations | kernel axiom audit (§4) | 0 `sorryAx` | 0 `sorryAx` | audit byte-identical after edits |
| R4 `sorry` in source text | text audit (cross-check only) | 0 | 0 | — |
| R3 one focused goal | `linter.style.multiGoal` | **0** | 0 | already clean |
| R8 honest `show` | `linter.style.show` | 254 | 3 | 251 `show` → `change` |
| R10b non-terminal `simp` | `linter.flexible`, distinct sites | 69 | 14 | 54 squeezed (§2.2) |
| R10b non-terminal `simp`, text heuristic | `audit_lean_proof_style.py` | 153 | 129 | see note below table |
| R10 unnecessary `simpa` | `linter.unnecessarySimpa` | 2 | 0 | `simpa … using h` → `simp …` |
| R1a/R16 `erw` | text | 0 | 0 | — |
| R22 global `Fact` instance | text | 0 | 0 | — |
| R17 `@[irreducible]` / `irreducible_def` | text | 0 | 0 | — |
| R4/R18 `axiom`, `@[implemented_by]` | text | 0 / 0 | 0 / 0 | — |
| R4 `native_decide` (widens trust) | text | 122 in 44 files | 122 | review item; tiers in §4 |
| R1a/R16 `rfl` right after `rw`/`simp` | text, heuristic | 232 in 125 files | 232 | review item (§5) |
| R7 untyped `have h := …` | text, heuristic upper bound | 2,316 in 481 files | 2,316 | not a gate (§5) |
| R26 theorem name starting upper-case | text | 96 in 16 files | 96 | documented exception (§5) |
| R13 declarations > 150 lines | text | 32 in 26 files | 32 | review item |
| R13 files > 1000 lines | text | 7 | 7 | review item |
| Shell PW1–PW4 (§3.9–§3.13) | `check_process_waits.py` | 1 | 0 | `devnet.sh` fixed |

The text heuristic for non-terminal `simp` counts every bare `simp` followed by another tactic,
including tactics that do not depend on it. It therefore falls by less than the linter count, and
the linter count is the authoritative one.

"Before" is the tree as delivered at the start of this session (`f1140f2`). Every Lean change
listed was checked by a full `lake build` (9,077 jobs, exit 0) after it was made.

## 2. Lean changes made

All changes are proof-internal. No statement, definition, name or import changed, so by R15
nothing downstream can be affected. The build confirms this.

### 2.1 R8 — 251 goal-changing `show` → `change`

`linter.style.show` flags a `show` whose target differs from the goal beyond reducible defeq,
which makes the `show` misleading about what the step does. All 251 flagged sites under
`RequestProject/` (73 files) were rewritten mechanically by
`tools/show_to_change.py`. It touches only the reported line and column, and only when the text
there is exactly the token `show`. The full build passed with every site rewritten. None needed
reverting, although `show` can select a non-main goal and `change` cannot.

Not changed: three sites in `HandoffV3/` (`Obligations/QuantPolicyV2.lean:425`,
`Obligations/QuantRounding.lean:294`, `Research/QuantClosures.lean:108`). `HandoffV3` is checked
against the frozen v3.0 text by `scripts/v3_landing_check.py`, so edits there need their own
review. These three are the remaining `show` findings.

### 2.2 R10b/R10d — 54 non-terminal `simp` squeezed

`linter.flexible` reported 139 warnings at 69 distinct sites. A site is reported once for each
later tactic that depends on what the `simp` produced.

- **First attempt, reverted.** The linter's warnings sometimes carry a `Try this: simp only [...]`.
  Applying those 22 suggestions verbatim broke the build in 13 of 17 files. In one-line proofs the
  suggestion belonged to a *different* `simp` on the same line, and some lists dropped a lemma the
  site needed. This is the failure Rule 10d predicts, so linter suggestions are not used as a
  source of lists.
- **What was kept.** At each site, the `simp` was turned into `simp?` *in place*. The list it
  reported at that exact site was read either from the editor's code action or, where the editor
  gave none (a `simp` inside a nested `by` term), from the `Try this` info that `lake build`
  prints, keyed by line and column. Where `simp?` reported several different lists for one call
  (a `simp` under `<;>`, inside `repeat'`/`first`, or run in several branches), the site was left
  alone, because no single list is correct. 51 sites were squeezed this way. 3 more came from the
  first attempt and were kept because the build confirmed them. On re-linting, the distinct
  flexible sites fell from 69 to 14: the 54 squeezed, plus one more that stopped being reported
  after an edit next to it.
- **Remaining 14 sites** (`data/linter_sites_after.tsv`, linter `flexible`):
  - several lists per call (9): `ASP/Phase7/CallV2.lean:524`, `Fame/Evm/Gas.lean:70`,
    `Feeds/EthFeed.lean:109`, `Governance/Signoff.lean:105`, `Main.lean:502`, `Sim/Hash.lean:66`,
    `Sim/Hash.lean:81`, `Sim/Rigor.lean:479`, `Venue/Obligations.lean:85`;
  - `TestReportingInvariants.lean:145`: a `simp` inside a `<;>` chain across 8 cases;
  - `HandoffV3/Proofs/Corpus.lean:136–139` (4): not edited (see §2.1).

  For each of these, the guide's alternative to squeezing applies: state the simplified form
  with `suffices`/`have`, or split the `<;>` chain into named cases.

### 2.3 Unnecessary `simpa`

`ASP/Phase11/Properties.lean:326` and `SignSortedOrder.lean:331`: `simp` alone closes the goal,
so the `using` term was dead. Both are now `simp`.

## 3. Shell changes made (blocking-watch note)

| Item | What |
|---|---|
| `scripts/run_logged.sh` | detached launch in its own session/process group; writes `TAG.log`, `TAG.pid`, and `TAG.rc` (atomic); removes a stale `.rc`; refuses a duplicate live tag |
| `scripts/wait_for_pid.sh` | `--check` (instant), `--for SECONDS` (caller patience, never kills), `PIDFILE SECONDS` (job budget, kills the group, returns 124); reads the exit code from `.rc`, reports `lost` (125) for a job killed from outside, checks orphans only in the job's own process group |
| `scripts/check_process_waits.py` | lint PW1 sentinel polling, PW2 `timeout` status not captured, PW3 marker without `rc=`, PW4 `wait` on a PID read from a file |
| `scripts/test_process_waits.py` | runs all the selftests plus the tree lint under `unittest` |
| `scripts/run_checks.sh` | the battery now runs the three selftests, the tree lint, and the Lean text-audit selftest |
| `scripts/devnet.sh` | `cmd_down` waited with `wait "$pid"` on an anvil started by an earlier call; it now waits on the PID with `kill -0` for up to 5 s, then sends `SIGKILL` |

Problems found in the note's own sketches, and fixed in the committed helpers:

1. `wait "$pid"` in a shell that did not start the job returns 127 at once. Under
   `set -Eeuo pipefail` the script exits before `rc=$?`. The selftest demonstrates this.
2. `pgrep -f 'lake|lean'` matches unrelated Lean processes. During this session it would have
   matched the editor's language server.
3. A single timeout conflates the caller's patience with the job's budget. In this session a
   540 s wait, chosen to fit the per-call limit, killed a healthy full build. `--for` was added as
   a result, and every later wait in the session used it.

The proposed one-line greps were not adopted: `rg 'timeout\s+[0-9]+' -A1 | rg -v 'rc=\$\?'` flags
every `--timeout 60` option in this repository's own selftests. The lint's selftest includes those
forms as must-not-flag cases.

## 4. R4 — kernel axiom footprint

The audit was regenerated from the compiled environment after all the changes, with a full
`lake build` and then `python3 scripts/check_axiom_audit_fresh.py --regenerate`, which runs
`scripts/AxiomAudit.lean`. The regenerated `docs/latex/axiom_audit.tsv` is **byte-identical** to
the committed one. None of the 307 proof-site edits changed any declaration's axiom footprint.

| Fact (from the regenerated audit) | Value |
|---|---|
| audited theorems / modules | 24,136 / 862 |
| declarations depending on `sorryAx` | **0** |
| axioms that appear | `propext`, `Quot.sound`, `Classical.choice`; plus `Lean.ofReduceBool` and `Lean.trustCompiler` on exactly 109 declarations |
| `check_axiom_budget.py` | passed: 109 tier-2 (compiler-trusted) facts against a ceiling of 109, 43 tier-1 invariant/ARI declarations, no tier-3 dependency |
| `check_no_axioms.py` | passed: 984 sources, no `axiom`, no `@[implemented_by]` |

This is the R4 gate as the guide requires: the kernel's per-declaration footprint is asserted
against an expected set, and grep plays no part in it. The text audit's `sorry` count (0) is only a
cross-check. Its first version counted 97 "sorry/admit" tokens, every one of them a function named
`admit`, which is the guide's point about grep.

## 5. Review items (not changed, with reasons)

- **`rfl` straight after `rw`/`simp` (232 sites, heuristic).** Under R1a/R16 this is the
  missing-API smell. Most sites unfold a `def` or reduce a `match` on a constructor after a
  `rw [h]`. The fix is an equation lemma per definition, which is an API decision for each module
  owner. It is not a mechanical edit. `python3 scripts/audit_lean_proof_style.py --list
  trailing_rfl` lists them. The files with the most sites are the best candidates for a
  `@[simp]` equation lemma.
- **Untyped `have h := …` (2,316, heuristic).** R7 asks for a stated type only "when the type is
  not obvious". The count is an upper bound that includes `have := foo x` where the type is plain.
  It is not a gate.
- **Upper-case theorem names (96 in 16 files).** These carry specification identifiers, for
  example `SWC/Falsification.lean` (`F1_…`, 43 names) and the `*/Hoare.lean` files (`HL_…`).
  `LEAN_PROOF_STYLE.md` R26 records this as a deliberate exception: the property registry, the
  claim index and the axiom audit key on these names.
- **`native_decide` (122).** This is allowed only for the Tier-2 declarations that
  `check_axiom_budget.py` names. That check reads the compiled footprint and is the gate.
- **Long declarations (32 over 150 lines) and long files (7 over 1000 lines).** These are R13
  candidates for extraction. The files are `ASP/Phase7/Meaning.lean`,
  `DetSim/Applied/ASPSettlementSuite.lean`, `DetSim/Applied/FeedSimulatorSuite.lean`,
  `Production/Absorption/Tests.lean`, `Sim/Properties.lean`, `Venue/BatchClearing.lean` and
  `scripts/ICACensus.lean`.
- **Rules applied in review only:** R6 (`calc`), R9 (line layout), R11 (structure at decisions),
  R12 (golfing), R14/R15/R19–R25 (library design and naming). No mechanical check can decide
  these, and none was invented.

## 5a. Build-time lint policy (completed in a follow-up session)

The session that produced this report also added a `[leanOptions]` table to `lakefile.toml` that
turns on five Mathlib style linters (`linter.style.maxHeartbeats`, `setOption`, `refine`, `cases`,
`induction`). Its comment named a policy document, a policy table and a gate that had not been
written, so the source-path gate failed. The follow-up session wrote them:

- `docs/standards/LEAN_LINT_POLICY.md` and `docs/standards/LEAN_LINT_POLICY.tsv`: the choice, one
  row per lakefile key.
- `scripts/check_lean_lint_options.py`, in the battery: lakefile keys and table rows match both
  ways (LP1); Mathlib keys carry `weak.` (LP2); each name is declared by `register_option` in
  the pinned Mathlib, because `weak.` silently ignores an unknown name (LP3); the Mathlib
  house-style set stays off (LP4); a ratchet on unscoped `set_option` (LP5). The selftest plants
  9 violations and requires all 9 to be rejected.

A full `lake build` with these options (9,077 jobs, exit 0) gives 10 warnings from
`linter.style.setOption` and none from the other four. The 10 are file-level
`set_option maxHeartbeats` lines in the EVM bytecode proofs under `RequestProject/Fame/Evm/`. They
are recorded as residue in the gate and as backlog in `LEAN_LINT_POLICY.md`. They are not scoped
here, because each file needs its heartbeat budget measured per declaration and a full rebuild.

## 6. Reproducing

```bash
python3 scripts/audit_lean_proof_style.py --tsv /tmp/text.tsv            # text metrics (§1)
lake build                                                               # ~50 min cold
bash scripts/run_logged.sh lint bash scripts/lean_style_linters.sh /tmp/lint 7
bash scripts/wait_for_pid.sh --for 540 /tmp/lint.pid                     # repeat until "done"
python3 scripts/check_axiom_audit_fresh.py --regenerate                  # §4
python3 scripts/check_process_waits.py                                   # §3
```

The linter pass over all 1,043 modules took 89 minutes with 7 parallel jobs on this machine.

## Files

- `data/linter_summary.tsv`, `data/linter_sites_before.tsv`: every linter report before the
  changes, by file, line and linter.
- `data/linter_sites_after.tsv`: the same after the changes. Unchanged files keep their before
  rows; every changed file was re-linted after its last edit
  (`data/linter_sites_changed_files_after.tsv` holds the first re-lint batch of 94 files).
- `data/text_summary_{before,after}.txt`, `data/text_metrics_{before,after}.tsv`: text audit.
- `tools/show_to_change.py`, `tools/flexible_to_simp_only.py`: the rewrite tools. The second one
  applies linter suggestions and is kept as the record of the reverted first attempt (§2.2);
  do not reuse it.

## Update 2026-10-15

A second pass is recorded in `audit/2026-10-15-lean-proof-style/REPORT.md`. It removed the ten
residue lines of §5a (every declaration in those files fits the default heartbeat budget), the
three `show` sites and 13 of the 14 `flexible` sites of §2.1–§2.2, and the 112 dead `simp`/`grind`
arguments and other core warnings that this report did not count.
