# Implementation plan — `LEVERAGE_HANDOFF_COMPLETE_2026-10-19.md`

Status: **plan written before any code; executed in the order of §3.** What was done, how it was
checked, and what stayed open is in `REPORT.md` next to this file.

## 1. Line-by-line reading: what each section asks, and what the tree already has

| § | Ask | Tree today | Gap |
|---|---|---|---|
| §0 | skeleton first; no statement changes; standard axioms only; every check can fail; heartbeats measured | conventions live (`LeverageAudit.lean` pins + sweep, `check_leverage_conjectures.py`) | applies to every item below |
| §1 | snapshot: C-MAP0–3 PROVED | confirmed: `lake build RequestProject.Venue.LeverageAudit` green, register rows PROVED | none |
| §2 | C-MAP4: `Bounded`, `gstep`, five theorems, reachability induction, transparency, boundary counterexample, N1 clamp mutant, N2 guard absence | `Projection.Bounded` (C-MAP1) exists; `HaltMonitor.guardedStep` is the template of a guarded wrapper; no bound guard | **all of it** |
| §3 | C-AD1/C-AD2 abstract adapter, reference instance over the local tape format, ported counterexamples, swallow and retag mutants | `TapeReplay` (tape = op-tagged answers, `record`, `divergence`); `DetSim.Divergence` (zip and last-mismatch counterexamples) | **all of it** (concrete DST instance stays BLOCKED-EXTERNAL) |
| §4 | memo keyed by source hash with soundness invariant, freshness on every hit, stale fixture, hit/miss counts | `scripts/AxiomAuditMemo.lean` memoises *within* one run (by `Name`); no cross-run cache | Lean soundness model + Python cache over the existing freshness hash |
| §5 | reference/fast pair with universal equality | `Book.levels` / `Book.levelsCore` / `levelsCore_eq_levels` already exist (core-Lean form) | a reduction-friendly single-pass `levelsFast` and its universal equality |
| §6 | fusion A/Bs ×6 with statement-invariance diff and median-of-3 timings | I1 (SeamCorpus) is the precedent | statement-diff script + fixture; per-suite fusion and measurement |
| §7 | F1 four `split_ifs` chains → named lemmas; F2 39 `maxRecDepth`; F3 opportunistic | sites listed in `NEXT_STEPS…` §7 | F1, F2 |
| §8 | pairing linter; coverage-matrix linter; FC-GATE (live) | Python pairing via `check_leverage_conjectures.py`; `register/new1_coverage_matrix.tsv` | Lean-side environment checks with planted fixtures |
| §9 | battery with fixtures | — | run at the end |
| §10 | order P* | — | §3 below |

## 2. Statement adaptations (surfaced, per §0 "a wrong statement is a design change via the register")

The handoff's Lean blocks are *shapes* written against an API that differs from the tree. They do
not elaborate as written. Each adaptation below keeps the claim and changes only what the real API
forces; each is recorded in `register/leverage_conjectures.tsv` (`discharge` column) and in
`REPORT.md` §2.

| Handoff text | Why it cannot elaborate | Adapted statement |
|---|---|---|
| `Venue.step s e : State` | `step : Config → State → Event → State × Observation` | `gstep cfg s e : State × Observation` (the `HaltMonitor.StepFn` shape, so tapes, monitors and mutants apply unchanged) |
| `Bounded (s : State) : Bool` | the projection (C-MAP1's domain) contains the step's published `Observation`, which is not part of `State` | `State.Bounded : Prop` (decidable) for the state fields; the guard checks `(project s' ob).Bounded` (C-MAP1's own predicate) and `project_bounded_iff` splits it. `Prop` + `Decidable` is the library convention for predicates; `decide` gives the `Bool` |
| `Venue.WF s` | name is `State.WF`; only `Book.WF` is needed | `Book.WF s.book`, only where used |
| `Venue.OrderMass.conserved s s' (Venue.published s e)` | neither name exists | the equation of `OrderMass.step_order_mass`, with `gstep` in place of `step` |
| hypotheses `hwf`, `hb` of `step_preserves_bounded_or_halts`, `hb` of `gstep_preserves_order_mass` | unused by any proof | dropped where unused (a statement with fewer hypotheses is stronger); the strongest form, `project_gstep_bounded`, is proved alongside |
| `gstep_transparent_of_bounded` (single step, `hb` unused) | identical to `gstep_eq_step_of_bounded_result` | stated over runs: if every raw step of a run stays inside the domain, the guarded tape *is* the raw tape |
| `project s₁ ≠ project s₂ → bookDigest s₁ ≠ bookDigest s₂` | false without `Bounded` (`encode_collides_unbounded`, C-MAP2); `project` takes an observation | `Bounded` hypotheses added; the corollary over guarded runs discharges them (C-MAP4) |
| `memo.find? h = some rows → regenerate (sourcesOf h) = rows` | `sourcesOf` would invert a hash (the collision class) | the memo stores the full source set with the key, a hit re-checks it, and `memo_sound` is stated for that lookup |
| `levels : Book → List Level` | `levels : Book → Side → List Price` | `levelsFast_eq_levels : @levelsFast = @levels` (universal, hypothesis-free) |

## 3. Execution order (P* of §10, dependency graph)

```
CanonicalProjection (C-MAP0–3, done) ──► BoundedGuard (C-MAP4a/b/c) ──► BoundedGuardTests (drill)
OrderMass, HaltMonitor ───────────────┘          │
TapeReplay, DetSim.Divergence ──────────────────►└─► Adapter (C-AD1, C-AD2) ──► AdapterTests (drills)
                                                                    │
                       LeverageAudit (pins + sweep + pairing/coverage checks) ◄─┘
AuditMemo (Lean model, memo_sound) ─► scripts/axiom_audit_cache.py (+ --selftest)
LevelsFast (levelsFast_eq_levels)
scripts/check_statement_invariance.py (+ --selftest) ─► fusion A/Bs
F1 split_ifs lemmas; F2 maxRecDepth scoping
```

1. **C-MAP4 skeleton** (`RequestProject/Venue/BoundedGuard.lean`), all statements `sorry`, build.
2. Prove bottom-up: `project_bounded_iff` → single-step lemmas → run induction → transparency →
   order-mass → monitor composition → reachable C-MAP2 corollary.
3. **Drill** (`BoundedGuardTests.lean`): boundary witness (`2^63 − 1` amended by `+2`), clock
   overflow, two pass-through witnesses, N1 clamp mutant, N2 guard absence; all `decide`.
4. **C-AD skeleton → proof** (`Adapter.lean`), **drills** (`AdapterTests.lean`).
5. Register rows (C-MAP4, C-AD1, C-AD2 → PROVED when paired), pins and sweep in `LeverageAudit.lean`,
   `check_leverage_conjectures.py` sources extended.
6. Memo: Lean model + Python cache + fixture.
7. `levelsFast`.
8. Statement-invariance script; fusion A/Bs as compute allows (LMMGovernance first).
9. F1, F2.
10. Pairing and coverage-matrix checks with planted fixtures.
11. Battery (§9), report.

## 4. Done criteria

* every new theorem: no `sorry`, footprint ⊆ {propext, Classical.choice, Quot.sound}, pinned;
* no `native_decide`, no new `maxHeartbeats`/`maxRecDepth` in new modules;
* each new gate has a planted violation that it catches;
* register statuses are current statuses (OPEN stays OPEN where not done).
