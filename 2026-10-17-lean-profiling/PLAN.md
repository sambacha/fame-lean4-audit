# Lean 4 build-profiling audit — dependency-ordered execution plan (v2, after answers Q1–Q5)

Scope: the Lean 4 code only. Toolchain `leanprover/lean4:v4.28.0`, Mathlib pinned at
`8f9d9cff6bd728b17a24e163c9402775d9e6a365`, baseline commit recorded in `baseline/commit.txt`.
Source: the handoff "Agentic Handoff: Performance Profiling and Improvement Plan", read line by
line, as revised by the owner's answers to Q1–Q5 (§2). v1 of this plan, written before the
answers, is in the git history.

All paths below are relative to `audit/2026-10-17-lean-profiling/` unless they start with a
repository directory. Status of each node: see `REPORT.md` §0.

---

## 1. Line-by-line reading: what the handoff assumes vs. what this checkout has

| # | Handoff says | Found here (2026-10-17) | Plan consequence |
|---|---|---|---|
| R1 | `lean_prof` "(existing)" | No file, script, target or document in the repo mentions it | Removed from the plan. Phase 1 is replaced by the three-layer stack (Q1) |
| R2 | 0.1 `lake exe cache get && lake build` | No network. Mathlib `.olean` files (7,655) present; **0** compiled project modules at start | `cache get` skipped (Q2). Baseline is "project cold, Mathlib warm" (Q5) |
| R3 | 0.4 `/usr/bin/time -v` | Not installed | `timed_run.py` records wall, child user/sys CPU and peak RSS through `getrusage` |
| R4 | `jixia` | Not installed, not cloneable | `#count_heartbeats in` + bisection (Q2) |
| R5 | `lean-training-data`, LeanGraph, lean-atlas | Absent | `getUsedConstantsAsSet` extractor + transitive closure in Python (Q2) |
| R6 | `importGraph` | Package present (rev `85b59af4…`). The repo also has `perf/tools/ImportGraphFromSource.lean` | Source mode: header parse. Compiled mode: imports read from the built `.olean` files |
| R7 | 0.3 expected footprint `[propext, Classical.choice, Quot.sound]` | 74 declarations in `docs/latex/axiom_audit.tsv` also use `Lean.ofReduceBool`, `Lean.trustCompiler` | Gate = per-declaration set non-growth. New declarations must stay within the three standard axioms. The 74 are a debt register (Q4) |
| R8 | 3B "`decide` / `native_decide` → kernel reduction" | `native_decide` is compiled evaluation, not kernel reduction | `native_decide` gets its own class |
| R9 | Phase 2 kernel class tested by `#count_heartbeats` | Heartbeats count elaborator work. Whether kernel checking ticks them is tested on the sentinel (P1.1), not assumed | The kernel class uses the profiler's `type checking` category; heartbeats are the elaborator metric |
| R10 | "sentinel cross-check" undefined | — | A sentinel comment before every `#count_heartbeats in`; parse sentinel → count pairs, never a positional zip (Q1) |
| R11 | `expected_time_saved × unblocking_value` | Zero for every off-critical-path fix | `score = saved_s × (1 + unblocked_cp_modules)` (P4.3) |
| R12 | Flatness stop at 1% | About 1,070 modules | Checked at P2.0 |
| R13 | Acceptance 7: gates shown able to fail | A linter fixture exists (`scripts/lint_fixtures/PromotedLinterTrigger.lean.txt`); no others | P0.6 adds the build, axiom, heartbeat, frozen-file and critical-path fixtures |
| R14 | Phase 5 fixes | Frozen: `HandoffV3/Kernel.lean`, `HandoffV3/FreerBridgeChecks.lean`, `HandoffV3/Resolutions.lean`, `AgentHandoff/` | Proof bodies and imports only; frozen files byte-checked; the rest escalated (Q3) |
| R15 | `#count_heartbeats` units | `Mathlib/Util/CountHeartbeats.lean` prints `Used N heartbeats, which is less/greater than the current maximum of M.` N is `IO.getNumHeartbeats` delta ÷ 1000, the same unit as `maxHeartbeats` (default 200000). It wraps the command in `set_option maxHeartbeats 0` | The parser reads N as printed (no further conversion) |
| R16 | `getUsedConstantsAsSet` | `Lean/Util/FoldConsts.lean`: `ConstantInfo.getUsedConstantsAsSet : ConstantInfo → NameSet` (type ∪ value; ctors for inductives) | Used as-is in `tools/UsedConstants.lean` |
| R17 | Per-job timing | `lake build` output, when not on a TTY, prints one line per finished job: `✔ [i/N] Built Mod (12s)` (`ℹ`/`⚠` when the job logged output) | Layer 1, first repeat: parse the clean-build log (Q1 allows "parse lake build output for per-job timing") |
| R18 | `import_s`, `elab_s` | `lean -Dprofiler=true` prints a `cumulative profiling times:` block with categories `import`, `elaboration`, `tactic execution`, `simp`, `typeclass inference`, `type checking`, `linting`, …; per-event lines carry no declaration name (probe, 2026-10-17) | Layer 1 repeats run `lean` with the profiler; categories give `import_s` / `elab_s` / `kernel_s` |

## 2. Owner decisions (answers to the clarifying questions)

| Q | Decision (summarized; the full text is kept in `NOTES.md`) |
|---|---|
| Q1 | Phase 1 does not depend on `lean_prof`. **Layer 1**: per-module wall clock for all modules. **Layer 2**: per-declaration `#count_heartbeats in` with sentinel comments, top-20 modules only. All declarations if a module has < 20; otherwise a random sample of 5, and all declarations in the top 3 modules. **Layer 3**: compiled import DAG + Layer 1 medians gives the critical path. Raw heartbeat counts, as printed. If `lean_prof` is added later, it must reproduce the sentinel cross-check |
| Q2 | Fallbacks approved: jixia → `#count_heartbeats in` + bisection; lean-training-data / LeanGraph / lean-atlas → `getUsedConstantsAsSet` extractor + Python closure; `cache get` skipped. Phase 0 gets a local tool inventory (§4 P0.3); the reproducibility section gets a substitution ledger |
| Q3 | Measure everything. Apply only proof-body and import changes; statements and names never change. Frozen files are read-only, and the protection is transitive: after every change, full `lake build` (frozen + non-frozen + tests) exits 0, the three pinned files are byte-identical (sha256), `AgentHandoff` builds, and the per-declaration axiom audit plus the full test suite are re-run. Definition rewrites (3C), DAG reordering and module splits (3D) are deferred and **escalated** with target, rewrite, scratch A/B heartbeat delta and expected critical-path impact |
| Q4 | Baseline = per-declaration map (`docs/latex/axiom_audit.tsv` + a fresh audit of the build) in `baseline/axioms.tsv`. Gate: `new ⊆ old` per declaration; new declarations ⊆ {propext, Classical.choice, Quot.sound}; any new `native_decide` is a flagged widening. The 74 are "already widened at baseline", reported under residual risk |
| Q5 | Scope: `RequestProject`, `AgentHandoff`, `HandoffV3`, `DetSim`, `DecisionMap`, `handoff_kernel_oracle`, plus `request_project_tests`. `scripts/`, `perf/tools/`, `test-fixtures/` only as gate fixtures. Repeats: baseline full build 1×; Layer 1 3× median (reduced to 3× top-20, 1× rest if not feasible, stated); Layer 2 1×; per-fix A/B 3× per side (mandatory). Warm `.lake` between repeats; the cold build is reported separately. Noise floor per module in `baseline/noise_floor.tsv`; a delta < 2 × noise floor is not a finding |

*Q3 refined 2026-10-19 (owner):* a definition rewrite that comes with a kernel-checked equality to the original needs no signature; see `register/decision_clarifications.tsv` row DC-1.

## 3. Dependency graph

`A → B` means B consumes A's output. ⏱ = timed node: it runs with nothing else heavy on the host.

```
P0.1 provenance ──────────────────────────────────────────────────────────────┐
P0.3 tool inventory ──────────────────────────────────────────────────────────┤
P3A.0 source import graph (no build) ──────────────────────────────┐          │
P0.2⏱ clean lake build (cold-project baseline, per-job log) ──┬────┼──────────┤
                                                               │    │          │
        ┌──────────────────────┬────────────────────┬─────────┤    │          │
        ▼                      ▼                    ▼         ▼    │          │
 P0.4 axiom baseline   P0.6 gate fixtures      P1.1 Layer1/r1  P0.7 tests  │   │
 (fresh audit +        must FAIL, then         (parse log)     build+run   │   │
  audit.tsv)           pass on baseline             │           (gate)     │   │
        │                      │                    ▼                      │   │
        │                      │      P1.2⏱ Layer1 repeats r2,r3 (profiler)│   │
        │                      │        + P0.5 noise floor ◄───────────────┘   │
        │                      │                    │                          │
        │                      │      P1.3 modules.tsv, P1.6 import fraction   │
        │                      │                    │                          │
        │                      │   P3A.1 compiled DAG ──► P1.5 critical path ◄─┘
        │                      │                    │
        │                      │      P2.0 flatness stop ─(flat)─► P6 (import/config only)
        │                      │                    ▼
        │                      │      P1.4 Layer 2 heartbeats (top-20, sentinels)
        │                      │                    ▼
        │                      │      P2.1 classify top-20 (class + owner + measurement)
        │                      │        ┌──────────┬──────────┬─────────┐
        │                      │        ▼          ▼          ▼         ▼
        │                      │     P3A.2      P3B       P3C A/B    P3D DAG
        │                      │     #min_imp   bisection (scratch)  analysis
        │                      │        └──────────┴────┬─────┴─────────┘
        │                      │                        ▼
        │                      │   P4.0 used-constants extractor → P4.1 blast radius
        │                      │      → P4.2 unblocking value → P4.3 ranking
        │                      │                        ▼
        └──────────────────────┴──────► P5.k per fix: apply → build → frozen sha256 →
                                         AgentHandoff → axiom gate → linter gate → tests →
                                         A/B 3×/side → heartbeat gate → critical path → keep/revert
                                                        ▼
                                         P5.Z⏱ final clean build + full audit + Layer 1
                                                        ▼
                                         P6 REPORT.md
```

### Topological order

| Wave | Nodes | Needs |
|---|---|---|
| W0 | P0.1, P0.3, P3A.0, P0.2⏱ | — |
| W1 | P1.1 (parse log), P0.4 axiom baseline, P0.6 gate fixtures, P0.7 test build + run | P0.2 |
| W2 | P1.2⏱ Layer 1 repeats + P0.5 noise floor | P0.2 (all `.olean` present); nothing else running |
| W3 | P1.3, P1.6, P3A.1 compiled DAG | P1.2 |
| W4 | P1.5 critical path; P2.0 flatness | P1.3 + P3A.1 |
| W5 | P1.4 Layer 2 heartbeats on top-20 | P2.0 (not flat) |
| W6 | P2.1 classification | P1.3–P1.6 |
| W7 | P3A.2 / P3B / P3C / P3D per class | P2.1 |
| W8 | P4.0 → P4.1 → P4.2 → P4.3 | W7 candidate list |
| W9 | P5.1…P5.n, one at a time, in rank order | P4.3, P0.4, P0.6 |
| W10 | P5.Z⏱ | all P5 |
| W11 | P6 report | all |

## 4. Node specifications

### Phase 0 — baseline and reproducibility

- **P0.1 provenance**: `baseline/toolchain.txt`, `baseline/manifest.json`, `baseline/commit.txt`,
  `baseline/tree_status.txt` (empty = clean tree).
- **P0.2 ⏱ clean build**: `timed_run.py baseline/clean_build -- lake build`, starting from 0
  project `.olean` files with Mathlib warm. Acceptance: exit 0; wall, user and sys times recorded.
- **P0.3 tool inventory (local)**, in `baseline/tool_inventory.tsv`. Present: lean/lake v4.28.0;
  Mathlib (`#count_heartbeats`, `#min_imports`); importGraph; core `getUsedConstantsAsSet`;
  `collectAxioms`; python3. Absent: jixia, lean-training-data, LeanGraph, lean-atlas, network,
  `/usr/bin/time`.
- **P0.4 axiom baseline**: `lake env lean scripts/AxiomAudit.lean` (the repo's
  `Lean.collectAxioms` audit) → `baseline/axioms.tsv` with columns `declaration`, `module`,
  `axiom_set` (sorted, comma-separated); `baseline/axioms_widened.tsv` lists the widened
  declarations; a cross-check against `docs/latex/axiom_audit.tsv` (set equality per row).
- **P0.5 noise floor**: for each module that is re-timed 3× in P1.2, spread = max − min →
  `baseline/noise_floor.tsv`.
- **P0.6 gates first shown able to fail**: each gate runs on a fixture made to fail it (exit
  must be non-zero), then on the baseline (exit must be 0). Results go to
  `tables/gate_selftest.tsv`.
  - build: a fixture `.lean` with a type error.
  - axiom: one declaration's set grows; one new declaration adds `Lean.ofReduceBool`.
  - linter: `scripts/check_promoted_linters.py --fixture`.
  - heartbeat: a declaration's heartbeats rise above the threshold, max(+10%, +1,000).
  - frozen-file: a modified copy of a pinned file fails the sha256 check.
  - critical path: a synthetic DAG whose path got longer.
- **P0.7 tests**: `lake build request_project_tests` (timed) and `lake exe request_project_tests`
  (exit 0) are the baseline for the Q3 test gate.

### Phase 1 — measurement (three layers, Q1)

- **P1.1 Layer 1, repeat 1**: parse every `Built <Module> (<t>)` line of
  `baseline/clean_build.log`, restricted to project modules in scope. Acceptance: every in-scope
  module appears exactly once; the module list is cross-checked against the source file list.
- **P1.2 ⏱ Layer 1, repeats 2–3**: per module, `lake env lean -Dprofiler=true <file>` against
  the built environment, timed (`build_s` = wall clock of the process; the profiler block gives
  `import_s`, `elab_s` = everything except `import` and `type checking`, and `kernel_s` =
  `type checking`). Run with bounded parallelism (and the parallelism is recorded). The median of
  the 3 repeats is taken where all 3 exist. If time does not allow 3× everywhere, the fallback is
  3× for the top-20 and 1× for the rest, stated in the report.
- **P1.3** `tables/modules.tsv`, sorted by median `build_s`, with the top-20 marked.
- **P1.4 Layer 2**: for each top-20 module, a scratch copy (under `/tmp`, never in the tree) gets
  `-- SENTINEL <idx> <decl>` + `#count_heartbeats in` before each selected declaration, following
  Q1's selection rule with a fixed RNG seed. `lake env lean` runs the copy; the output is parsed
  as sentinel → `Used N heartbeats` pairs. Acceptance: every inserted sentinel gets exactly one
  count. Output: `tables/declarations.tsv`, sorted by heartbeats and by elapsed time.
- **P1.5 Layer 3** `tables/critical_path.tsv`: the longest path in the compiled import DAG,
  weighted by median `build_s`. Reported with its length, path ÷ baseline wall, each module's
  share, and the bound `max(path, CPU/8)`.
- **P1.6** import fraction = Σ`import_s` ÷ Σ`build_s` (denominator stated), with the elab and
  kernel fractions beside it.

### Phase 2 — classification

- **P2.0** If no module is ≥ 1% of Σ`build_s`, stop hotspot work (decision point).
- **P2.1** Each top-20 module gets one class, tested in order (first match wins), with its owner
  and the measurement that decided it:
  1. kernel: `kernel_s > 0.5 × build_s`;
  2. compiled evaluation (`native_decide` / `#eval`, R8);
  3. single command: one declaration > 50% of the module's heartbeats or elaboration time;
  4. elaboration: `elab_s > 0.5 × build_s`;
  5. import: `import_s > 0.5 × build_s`;
  6. dependency: on the critical path with own `build_s` below the median;
  7. otherwise mixed, with the split shown.

### Phase 3 — root cause and candidate fixes → `tables/candidates.tsv`

- **P3A.0** source import graph: `python3 perf/tools/write_profiling_artifacts.py --crosscheck`.
- **P3A.1** compiled DAG: imports read from each built module's `.olean` header (importGraph's
  compiled mode, the same data `lake exe graph` reads). Cross-checked with P3A.0, edge for edge.
- **P3A.2** for import-dominated modules: `#min_imports` in a scratch copy; the reduced header is
  verified by a compile. Load-bearing broad imports (aggregators, `TestingMain`, audit scripts)
  are recorded as blocked.
- **P3B** for elaboration or single-command modules: bisection within the owning proof, in a
  scratch copy, with `#count_heartbeats in`. The expensive tactic is classified (`simp` →
  `simp only`; `grind` / `aesop` / `simp_all` → bounded; `linarith` / `nlinarith` → pruned
  hypotheses). `simp` terminal vs. non-terminal uses tier 3 only (the syntactic heuristic).
- **P3C** for kernel or compiled modules: one hypothesis at a time, A/B in scratch. Any rewrite of
  a definition is escalated, not applied (Q3).
- **P3D** for dependency modules: the import is forced if the module uses a constant from the
  blocking import (P4.0); otherwise it is a layout artifact. Any split is escalated (Q3).

### Phase 4 — prioritization

- **P4.0** `tools/UsedConstants.lean`: for every project constant, its
  `ConstantInfo.getUsedConstantsAsSet` restricted to project constants, plus constant → module.
- **P4.1** blast radius = |reverse transitive closure| in declarations, plus the modules that
  must rebuild (reverse import closure).
- **P4.2** `unblocked_cp_modules` = number of modules on the critical path whose earliest finish
  time moves earlier when the target's `build_s` is replaced by its measured "after" value.
- **P4.3** `score = saved_s × (1 + unblocked_cp_modules)`, where `saved_s` = the median-before
  minus median-after `build_s` of the target module (3× each). Ties are broken by smaller blast
  radius. A candidate whose `saved_s` < 2 × noise floor gets score 0 and is not a finding.

### Phase 5 — apply, verify, re-measure (Q3 gates, in this order)

5.1 apply the change (proof body or import only) on a branch →
5.2 full `lake build` exits 0 →
5.2a sha256 of the three pinned files is unchanged →
5.2b `lake build AgentHandoff` exits 0 (the v2.1 regression pin) →
5.2c `lake build request_project_tests && lake exe request_project_tests` exits 0 →
5.3 per-declaration axiom gate →
5.3a linter gate (no new warning lines; promoted-linter check) →
5.4 A/B, 3× per side, on the affected module(s): `import_s`, `elab_s`, `build_s`, heartbeats →
5.5 critical path recomputed →
5.6 keep if the delta is ≥ 2 × noise floor and no metric or the critical path regresses;
otherwise revert, with the reason recorded in `tables/fixes.tsv`.
**P5.Z ⏱** final clean build, timed like P0.2; full axiom audit diffed against P0.4; Layer 1 run
again.

### Phase 6 — report (`REPORT.md`)

Sections: baseline (cold-project wall and CPU; warm-cache Layer 1; critical path; top-20 modules
and declarations; import fraction with its denominator; axiom map); findings, each citing a
table row; fixes applied; fixes deferred and escalations; known widened declarations (the 74);
residual risk; reproducibility with a substitution ledger (per phase: tool used, primary tool,
reason).

## 5. Stop conditions → nodes

| Condition | Node | Action |
|---|---|---|
| No module ≥ 1% of build time | P2.0 | Skip P1.4–P3; report import and configuration levers |
| Narrowing blocked by load-bearing imports | P3A.2 | Record as blocked; no edit |
| A rewrite changes the axiom footprint | P3C / 5.3 | Revert; not a perf fix |
| LeanGraph unavailable | P4.0 | Extractor fallback (the case here) |
| Target improves but the critical path regresses | 5.5 | Revert |
| Fix requires a definition, DAG or split change | P3C / P3D | Escalate (Q3); do not apply |
