# Falsification of `NEXT_STEPS_BY_LEVERAGE_2026-10-19.md` — report and second pass (2026-10-19)

Method: every claim of revision 1 of the plan was read line by line and tested against the tree
(first-pass notes: `NOTES.md` in this folder). Four clarifying questions went to the owner before
anything was implemented, plus one follow-up about the FC rows. Their answers are recorded below.
Each invalidated claim was then fixed at its root, along with the concern it shares with the others.
The plan is now at revision 2; revision 1 is kept verbatim in its Appendix A.

## 1. Verdicts (first pass)

| Item | Claim | Verdict | Evidence |
|---|---|---|---|
| hdr | "Merged from Q7/Q8 adjudication" | untraceable | no such document in the tree |
| 1 | C-MAP1–3 "PROVED, kernel, standard axioms" | **false at the time** | `toCanonical`/`encode_injective` had 0 hits in `*.lean`; only a 2026-10-11 plan "[PROVED target]" |
| 1 | C-MAP1 "total" | vacuous as worded | every Lean `def` is total; the real content is "inside the encoder's domain", which needs a bound |
| 1 | C-MAP2 unconditional | false | `i64` wraps mod 2^64: `encode_collides_unbounded` |
| 1 | "Counterexamples: … must not exist" | not a counterexample | it restates C-MAP2; 0 counterexamples against the plan's own rule |
| 1 | "DST-signed field-list row", "FC-3" | missing | no register row; `FC-*` undefined in the tree |
| 2 | "five rows", C-FC1–3 | undefined | no `FC-GATE`, no `C-FC*` anywhere |
| 2 | "sign-off via existing hash-chain" | conflation | the hash chain is the venue journal (event log); the sha256 *manifest* is `register/session_artifact_hashes.tsv` |
| 3 | last-mismatch detector "one witness" | undercount | two: `lastDivergence_not_first`, `lastDivergence_prefix_late` |
| 3 | C-AD1 adapter | blocked | no `Harness` adapter, no DST API version (gap G-07) |
| 4 | C-AUD1 notify | mostly existed | `--review` named changed rows; the hole was `--allow-module` dropping them silently |
| 4 | C-AUD2 key `(module, name)`; gexPlus.eq_1 is the witness | **self-refuting** | the duplicate was one name under two modules, so two distinct `(module, name)` pairs. The key must be the name |
| 5 | "biggest single CI number: the 1,865 s step" | wrong lever | hoist already applied (1,627 s); ≈1,600 s is per-theorem `CollectAxioms` |
| 5 | "AxiomAudit first, then the remaining nine" | wrong count, missing constraint | AxiomAudit done; 10 sites remain; one is in frozen `AgentHandoff/` |
| 6 | suite list | omission | drops LMMGovernance, the report's strongest candidate |
| 6 | "NOT additive (22.2 s vs 8.5 s)" | wrong reason | M1 is within-module serialization, which makes in-module savings add to job time; non-additivity holds only for whole-build wall time |
| 7 | "I2 pattern (lemma + heartbeat-override deletion)" for 4 chains | half false | the four files hold no `maxHeartbeats` override |
| 7 | 38 `maxRecDepth`, 68 `show … from rfl` | validated | regenerated counts match |
| 8 | "unblocked … no owner signature" | contradicted a recorded rule | profiling-audit Q3 escalates definition rewrites |
| x | "G-04 pairing", "guarantee 7", "invariant 1" | collision / undefined | G-04 means three different things in the tree; the other two name nothing |

**Induction over the failures.** Every invalidated claim falls into one of three classes. (1) A
status label with no artefact behind it: a *target* status printed where the current status belongs.
(2) A count or list copied from its source with drift. (3) An identifier or rule that is undefined
or collides with another. The cross-cutting fix makes each class mechanically detectable: a status
vocabulary, a register row for every id, and a gate that ties the plan's text to the register
(§3).

## 2. Owner answers (closed decisions)

* **Q-A (item 1).** "PROVED" was a vocabulary error: target ≠ status. Projection = book (canonical
  order: price, then sequence), nextSeq, ledger, halted, logical time, the step's published results;
  journal excluded. C-MAP2 is conditional on a decidable `Bounded`. Overflow must halt the engine.
  The field list goes in first as PROPOSED, pending the DST countersign.
* **Q-B (item 8).** Profiling-audit Q3 is *refined*, not superseded: a kernel-checked equality is the
  approval. Recorded as `register/decision_clarifications.tsv` DC-1. The `levels` swap stays OPEN as a
  sequencing item.
* **Q-C (item 5).** Waiver rule: a pure refactor needs byte-identical output plus one indicative
  timing. `AgentHandoff/Audit.lean` is deferred (frozen), recorded as DC-2.
* **Q-D (item 2).** FC-1…FC-5 + FC-0 defined by the owner (registered verbatim in
  `register/FC_GATE.md`). FC-5 is narrowed to connection-run evidence. FC-2 produces the outputs and
  FC-3 diffs them.

## 3. What was changed

| Invalidated claim | Root fix | Artefact |
|---|---|---|
| C-MAP1–3 "PROVED" without artefacts | built and pinned them, with two witnesses, two counterexamples and two non-vacuous negations each | `RequestProject/Venue/CanonicalProjection.lean`, `RequestProject/Venue/LeverageAudit.lean` |
| "same book, two encodings" not addressed | canonical book order with a proved spec (C-MAP0) | `Venue.Book.canonical_eq_of_perm`, `…_iff_perm` |
| unconditional C-MAP2 | conditional on `Bounded`, proved *exactly* the encoder's domain (`toCanonical_wf_iff`) | C-MAP1 |
| field-list row missing | PROPOSED rows PF-1.* pending DST countersign | `register/projection_field_list.tsv` |
| overflow behaviour | recorded as OPEN (engine statement change) | C-MAP4, DC-5 |
| target status in a status column | status vocabulary + register + plan-consistency gate | `register/leverage_conjectures.tsv`, `scripts/check_leverage_conjectures.py` (10 planted defects) |
| FC rows undefined | owner's definition registered; lint with the five fixtures plus an unknown-status fixture; fail-closed verdict printed | `register/FC_GATE.{md,tsv}`, `register/fc_gate_classification.tsv`, `scripts/check_fc_gate.py` |
| C-AUD2 key | key = name; `read_rows` no longer overwrites silently; in every mode | `scripts/check_axiom_audit_fresh.py` |
| C-AUD1 hole | allowed changes printed as named notices | same script; self-test plants an allowed footprint change |
| item 5 count/lever/frozen | nine non-frozen sites hoisted; AgentHandoff deferred (DC-2); plan corrected | §4 |
| item 6 list / reason | plan corrected (six suites; additivity stated per module vs whole build) | plan §6 |
| item 7 heartbeat deletion | plan corrected (lemma half only) | plan §7 |
| item 8 rule | DC-1 recorded; plan cites it; note added to the profiling plan | `register/decision_clarifications.tsv`, `audit/2026-10-17-lean-profiling/PLAN.md` |
| G-04 / Q3 / "guarantee 7" / "invariant 1" | qualified names in the plan; collision row | DC-4 |
| item 3 witness count | plan corrected | plan §3 |

**C-MAP evidence.** All 33 named declarations are pinned with `#guard_msgs`. The footprints are
`propext`, `Classical.choice` and `Quot.sound`, or a subset of them; there is no `native_decide`
(`lake build RequestProject.Venue.LeverageAudit`). Non-vacuity: each negation refutes a statement
whose hypotheses hold at the witness. For example, `not_mutantDropHalted_injective` uses two
`Bounded` projections, and `not_forall_int_wf_of_lt_two_pow_64` uses `2^63 < 2^64`.

## 4. Item 5 measurements (waiver rule: byte-identical output, one indicative run per side)

Filled from `raw/item5_ab.tsv`. The runs were contended (8-way host, other jobs running), so the
timings are indicative only. One run per side, old file first.

Round 2 (warm cache, old side first, one run per side on a shared machine, so the timings are **indicative only**). Outputs were compared byte for byte after replacing the script path in diagnostic lines with a placeholder. The round-1 timings agree with round 2 to within 10%, so a cold cache did not explain the gap. Raw data: `raw/item5_ab.tsv`.

| Site | Outputs compared | Byte-identical | Old (s) | New (s) | Old/New |
|---|---|---|---|---|---|
| `DetSim/Audit.lean (2 sites)` | stdout | yes | 13.7 | 4.9 | 2.8x |
| `HandoffV3/Audit.lean` | stdout | yes | 78.3 | 27.1 | 2.9x |
| `scripts/NativeDecideTcb.lean` | stdout | yes | 350.0 | 13.7 | 25.5x |
| `audit/2026-10-17-lean-profiling/tools/ProfEnv.lean` | stdout + axioms.tsv, imports.tsv, used.tsv | yes | 172.4 | 11.8 | 14.7x |
| `scripts/DeclarationNames.lean` | stdout + DECL_NAMES_OUT (65955 lines) | yes | 184.0 | 21.8 | 8.5x |
| `scripts/ICACensus.lean` | stdout + docs/ica/ica_decl_census.tsv (39406 lines) | yes | 185.2 | 18.0 | 10.3x |
| `scripts/AxiomAuditMemo.lean` | audit rows (309), round 1 only | yes | – | – | – |

## 5. Second pass — belief updates after the answers

1. *Before:* C-MAP was "implement against a guess or wait". *After:* the owner's field list makes it
   implementable now. The only external dependency left is the countersign, which affects the
   *status of the field list* (PROPOSED), not the proofs. A changed list changes the proofs
   mechanically.
2. *Before:* I read C-MAP1 "total" as vacuous. *After:* the meaningful version is stronger than
   planned: an *iff* (`toCanonical_wf_iff`), which shows that `Bounded` is neither too weak nor too
   strong. That matters because the engine will check it on every event (C-MAP4).
3. *Before:* the plan's counterexample list for item 1 was empty. *After:* writing the decoder
   exposed two failure modes the plan did not name. A lossy `Int.toNat` decoder breaks the round trip
   (`ofCanonical?_negative_nat`), and a tag-blind decoder accepts foreign-domain bytes
   (`not_mutantIgnoreTag_sound`). A sort keyed only on price is not canonical when two orders share
   a price (`mutantSortByPrice_distinguishes`). "Price, then sequence" is canonical only if no two
   resting orders share both, which the book invariant does not state. The key therefore continues
   over every field, so the order is total without that assumption (`Resting.canonKey_injective`).
4. *Before:* I suspected C-AUD1 was entirely new work. *After:* it mostly existed. The real defect
   was the silent `--allow-module`, and it explains a documented miss (guideline review §6.1).
5. *Before:* I believed item 8 contradicted Q3. *After:* the owner reads Q3 as refined. The
   contradiction was in the *register*, now fixed by DC-1, not in the practice.
6. *Before:* item 5 was "nine sites". *After:* ten. Nine were done under the waiver rule and one
   (frozen) is deferred with its estimate on record. The CI lever for the 1,600 s audit step is still
   the memoized audit, which this plan does not schedule (open recommendation R2 of the guideline
   review).
7. *New finding from the gate itself.* While writing revision 2, the plan-consistency gate rejected
   a line that put PROVED next to C-AD2 (OPEN). The rule caught exactly the error class it was built
   for.
8. *New finding.* G-12 was not covered by the owner's FC-0 list, so it would have been an
   unclassified P\* gap. It is classified FC-0 *by the agent* and flagged for owner review (DC-3).

## 6. Open items and blockers (not done here)

* C-MAP4: halt-on-overflow guard in `Venue.step` plus the step-preserves-`Bounded`-or-halts theorem
  (statement change; owner rule).
* C-AD1, C-AD2, FC-2: no adapter. C-FC4 / FC-4: F-1 date (external). FC-1, FC-3: DST version name and
  criterion (external). C-FC1: the soundness argument for "five rows suffice" is not yet written.
* Items 6, 7, 8 execution (fusion A/Bs, guard-chain lemmas, `maxRecDepth` scoping, `@[csimp]` swaps):
  not attempted in this pass; the plan rows are corrected.
* DC-2 (AgentHandoff hoist, deferred), DC-3 (G-12 classification, owner review).
* Battery state: `scripts/run_checks.sh --source-only` has 36 failing checks on the unmodified tree in
  this environment (missing tool dependencies and pre-existing registry gaps, e.g. `ica_audit.py
  --check`). The battery found one new failure from this work: `audit_property_registry.py`, for the
  three new `#guard` lines. It is fixed by registry rows. The `asp_console.py --selftest` finding
  list is now empty: the new script was unclassified, and so were two older ones, and all three are
  now classified. The net is 33 failing checks against 34 comparable baseline failures. The baseline
  had 36, but two of them failed only because the baseline worktree was unbuilt. Each fix was re-run
  on its own, not in a full battery re-run. Details are in `raw/battery_diff.txt`.
