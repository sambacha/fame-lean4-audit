# Scratch notes — line-by-line falsification of `NEXT_STEPS_BY_LEVERAGE_2026-10-19.md`

Pass 1 (before clarifying questions). Each claim is tried against the tree; "V" = validated,
"X" = invalidated, "~" = partly true / needs qualification. Evidence is a command or file:line.

## Header (lines 1–4)
- L3 "Merged from Q7/Q8 adjudication; Lean guideline review adjudication." ~ The guideline review
  exists (`audit/2026-10-19-lean-guideline-review/REPORT.md`). No document in the tree is titled or
  tagged as a "Q7/Q8 blockers-unblockers adjudication"; untraceable source.
- L4 "no gate closes on a label, a finite test, or a citation alone." Rule, not a claim. It is the
  yardstick for everything below; several items below violate it (see X marks).

## §1 Projection-field agreement + canonical map (L6–14)
- L6 "gates FC-3 + semantics branch". X `FC-3` is defined nowhere in the tree
  (`rg '\bFC-[0-9]\b'` → only an unrelated `FC-4` string in `docs/demo/findings/FAME-CORE-04.json`).
- L7–9 "C-MAP1/2/3 … PROVED, kernel, standard axioms." **X (false).**
  `rg 'toCanonical|encode_injective' -g '*.lean'` → 0 hits. No `toCanonical`, no state-level
  `encode_injective`, no round-trip theorem exists. The only mention outside this file is a
  2026-10-11 archive plan (`docs/archive/design/BLOCKERS_5_6_7_PLAN_REVIEW_2026_10_11.md:222,573`)
  marking it "[PROVED target]" — a target, not a proof. Violates L4.
  - Reusable infrastructure that *does* exist: `Venue.JournalFormat.CVal.enc_injective`
    (`RequestProject/Venue/JournalFormat.lean`, injective on `CVal.WF` values: ints within i64,
    lengths < 2^32), `DetSim.decodeTrace_encodeTrace` (DetSim event codec round-trip).
  - Falsification of C-MAP1 as worded: "total" is vacuous for a Lean function (every `def` is
    total). The meaningful version is "the image is inside the canonical domain"
    (`(toCanonical s).WF`), which is FALSE for unbounded `Nat`/`Int` fields (`Venue.State` uses
    both) — needs a bound precondition. Hence C-MAP2 also needs it: the i64 encoder is not injective
    on all of `Int` (values congruent mod 2^64 collide).
- L10–11 "Counterexamples: two distinct projection states sharing an encoding — must not exist". X
  This restates C-MAP2; "eliminated by … C-MAP2 itself" is circular. The item has 0 counterexamples,
  against its own cross-cutting rule (L58).
- L12–13 Negations (dropped-field / unordered / domain-confusion mutants). ~ Reasonable shapes; none
  exist. "GEX bytes in book domain rejected" presumes a domain tag; none exists in the Venue/DetSim
  encoders (`rg -i 'domain.?sep|domainTag'` → 0).
- L14 "owner/DST-signed field-list register row". X No such row in `register/*.tsv`.

## §2 FC-GATE lint (L16–21)
- L17 "C-FC1 five rows suffice". X The five rows are not defined anywhere (no `FC-GATE`, `C-FC*`).
- L21 "signed via the established sha256-manifest mechanism" / title "existing hash-chain". ~ Two
  mechanisms are conflated. The *hash chain* is the venue journal (`JournalFormat`, `ChainAnchor`),
  an event log, not a sign-off mechanism. A sha256 *manifest* exists for session artefacts
  (`register/session_artifact_hashes.tsv`, `scripts/check_session_artifacts.py`). Sign-offs live in
  `register/beta_signoffs.tsv` / `register/adjudications.tsv` with role-only signers.

## §3 Adapter forward simulation (L23–30)
- C-AD1 "adapter run = Venue.step run". ~ No adapter exists (`CONNECTIVITY_READINESS_OPTIONS.md:326,391`:
  no `Harness`, no DST API version in the repo). Blocked on external input.
- C-AD2 "rests on C-MAP2". V as a dependency — but C-MAP2 did not exist (§1).
- L26–27 "zip-detector misses prefixes (two witnesses); last-mismatch detector breaks 'first' (one
  witness)". ~ Zip: V (`DetSim/Divergence.lean:180,184`). Last-mismatch: X undercount — two
  witnesses exist (`lastDivergence_not_first`, `lastDivergence_prefix_late`), plus two negations each.
- L28–29 op-tag blind spot as dated risk-acceptance. V the blind spot is proved
  (`tickRetag_undetected`, `RequestProject/Venue/TapeReplay.lean`); F-1 is queued and unsigned.

## §4 Footprint-diff notify + duplicate-row lint (L32–37)
- C-AUD1 "every footprint change appears as a named diff row". ~ Mostly ALREADY implemented:
  `scripts/check_axiom_audit_fresh.py --review` prints `row changed: <name>: old -> new`, with a
  self-test. **Real hole:** `--allow-module M` *silently* drops every change in `M`. This is how the
  six SeamCorpus `propext → propext,Quot.sound` changes were first missed (guideline review §6.1).
- C-AUD2 "TSV free of duplicate (module, name) pairs" + "gexPlus.eq_1 is the witness". **X (the
  proposed key would not have caught the witness).** The duplicate was
  `Fame.Economics.gexPlus.eq_1` under `…OrderFlow` AND under `…GEX.FixedPoint.Conjectures`: two
  *different* (module, name) pairs. The key must be the name alone. Root cause of the silence:
  `read_rows` builds `rows[name] = …`, so a second row with the same name silently overwrites the
  first. (Guideline review §4 item 7 recommends "deduplicate by (name, module)" — same error.)
- L37 "both gates in run_checks.sh". V target: `run_checks.sh:499–501` already runs the script.

## §5 moduleNames loops outside RequestProject/ (L39–41)
- "biggest single CI number: the 1,865 s step". ~ One measured pre-hoist run. The hoist is
  **already applied** (I4: 1,627 s after), and moduleNames is "a small share": ≈1,600 s is
  per-theorem `CollectAxioms`. The lever is the memoized audit, not moduleNames. X framing.
- "AxiomAudit step first, then the remaining nine". X (a) AxiomAudit is done; (b) 10 sites in 9
  files: `scripts/NativeDecideTcb.lean:72`, `scripts/AxiomAuditMemo.lean:204`,
  `scripts/ICACensus.lean:1005`, `scripts/DeclarationNames.lean:933`, `DetSim/Audit.lean:35,71`,
  `AgentHandoff/Audit.lean:31`, `HandoffV3/Audit.lean:30`,
  `audit/2026-10-17-lean-profiling/tools/ProfEnv.lean:137,142–143`. (c) `AgentHandoff/` is FROZEN
  (profiling audit Q3, guideline review §7) — the plan does not say so. (d) `DetSim/Audit` and
  `HandoffV3/Audit` are default build targets (build cost, not a separate CI step).

## §6 Per-suite fusion (L43–46)
- "~700 s; LMM, TokenLedger, POLSuiteRisk, DivergenceRate, DetSim". X list mismatch: the report's
  fusion rows are LMMGovernance, LMM, TokenLedger, POLSuiteRisk, DivergenceRate, DetSim.Conformance.
  The plan drops **LMMGovernance, the report's "strongest next candidate"**. All six ≈ 745–780 s;
  the five named ≈ 600–640 s. [estimated] in the source (one serial profile run).
- "fusion gains are NOT additive … (serialization lesson: 22.2 s vs 8.5 s)". ~ M1 shows kernel
  checks within ONE file are sequential, which makes within-file savings *add* to that module's
  time. Across modules, job-time deltas add; whole-build wall deltas do not. The cited lesson does
  not support the stated reason.
- "statements and names unchanged per suite" V consistent with Q3.

## §7 Backlog (L48–50)
- "4 split_ifs chains: I2 pattern (lemma + heartbeat-override deletion)". X the four sites contain
  **no** `maxHeartbeats` override (`rg maxHeartbeats` on the four files → 0).
- "38 file-level maxRecDepth" V (38 in `RequestProject`; +1 in DetSim).
- "68 show…from rfl" V (68 sites, 21 files, 26 in `Fame/Evm/Full/Refine.lean`).

## §8 Faster definitions (L52–55)
- "unblocked … No owner signature in the loop". **X contradicts a recorded owner decision.**
  Profiling audit Q3 (`audit/2026-10-17-lean-profiling/PLAN.md:43`) and guideline review §7:
  definition rewrites are escalated for owner approval; `docs/decisions/ELEVEN_ANSWERS_2026-10-19.md:66`:
  the `@[csimp]` swap of `levels` is **OPEN**.
- "levelsCore_eq_levels pattern" V (`RequestProject/Venue/LevelsOrder.lean:83`).
- "invariant 1 forbids statement changes" X "invariant 1" is undefined in the tree.

## Cross-cutting (L57–59)
- "G-04 pairing". X label collision (DST admission in `CONNECTIVITY_READINESS_OPTIONS.md:431`; ASP
  reentrancy in ASP registers); already flagged in `register/adjudications/DA-1-FALSIFICATION.md:49`.
- "guarantee 7" (L41) undefined in the tree.
- "Standard axioms only, pinned" V (`scripts/check_axiom_budget.py`).

## Induction step (pattern across items)
Every X is one of three kinds: (1) a status label with no artefact (§1 PROVED, §2 five rows), (2) a
count/list copied with drift from its source (§3, §5, §6, §7), (3) an identifier or rule that is
undefined or collides (FC-*, G-04, guarantee 7, invariant 1, §8). Cross-cutting fix: every
identifier in a plan must resolve to a file:line or register row, and every count must be
regenerated by a command, not copied.

## Pass 2 (after the owner's answers)
Belief updates are in `REPORT.md` §5. Status changes against pass 1: C-MAP0–3 are now PROVED (built,
pinned, paired); C-MAP4 OPEN; C-FC2/C-FC3/C-AUD1/C-AUD2 CHECKED; C-FC1, C-AD1, C-AD2 OPEN; C-FC4
BLOCKED-EXTERNAL. Item 5 count corrected to 10 (9 done, 1 frozen and deferred). Item 8 is reconciled
by DC-1, not by overriding Q3.
