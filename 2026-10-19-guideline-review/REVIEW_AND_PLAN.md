# Guideline review of the 2026-10-19 leverage-list work: findings and refactor plan

Status: **review complete, plan proposed, no code changed.** Fixes wait for the answers to the
clarifying questions in §4.

Scope: the outputs of "the work just completed", as listed in `ARISTOTLE_SUMMARY.md` and
`audit/2026-10-19-next-steps-falsification/REPORT.md`.

| Artefact | Kind |
|---|---|
| `RequestProject/Venue/CanonicalProjection.lean` (691 lines) | new Lean: definitions, C-MAP0–3 theorems, witnesses, mutants |
| `RequestProject/Venue/LeverageAudit.lean` (149 lines) | new Lean: axiom-footprint pins |
| `scripts/check_leverage_conjectures.py`, `scripts/check_fc_gate.py` | new gates |
| item-5 module-lookup hoist in 7 Lean metaprograms (`DetSim/Audit.lean`, `HandoffV3/Audit.lean`, `scripts/NativeDecideTcb.lean`, `scripts/DeclarationNames.lean`, `scripts/ICACensus.lean`, `scripts/AxiomAuditMemo.lean`, `audit/2026-10-17-lean-profiling/tools/ProfEnv.lean`) | perf refactor |
| `register/*.tsv`, `register/FC_GATE.md` | registers |

The rules are the ones you supplied: `SKILL.md` and its eight references. The repository already
adopts the same guide as authoritative (`docs/standards/LEAN_GUIDE.md`, `LEAN_PROOF_STYLE.md`), and
records some departures from it (D-2, R10a, D-4). Where a finding depends on whether those
departures apply, the finding says so (see Q1).

## 1. How each finding was established

* `lake build RequestProject.Venue.LeverageAudit` succeeded (8034 jobs). The promoted linters
  (`multiGoal`, `show`, `unused*InType`, `setOption`, `maxHeartbeats`, `refine`, `cases`,
  `induction`) report **nothing** on either new file.
* I ran `lake env lean` on `CanonicalProjection.lean` with every other registered Mathlib style
  linter forced on: `flexible`, `unnecessarySimpa`, `hashCommand`, `longLine`, `cdot`,
  `openClassical`, `missingEnd`, `lambdaSyntax`, `dollarSyntax`, `oldObtain`, `whitespace`,
  `emptyLine`, `nativeDecide`, `docString`. Only 5 warnings came back: 3 × `hashCommand` (the
  `#guard`s) and 2 × `longLine` (lines 437 and 545).
* A fixture confirmed that `linter.flexible` is live: `simp at h` followed by `exact h` is flagged.
  So when the linter is silent on this file, the silence means something. It still **misses**
  finding P-1 below, because it treats `tauto` as a "flexible" tactic.
* `scripts/audit_lean_proof_style.py --list <metric>` on the tree: `untyped_have` reports 4 sites
  in `CanonicalProjection.lean`. `nonterminal_simp` reports 0, which is a second miss of P-1. The
  `simp` call wraps onto two lines, so the heuristic's "next line" is the continuation line.
* `#count_heartbeats in` on the heaviest proofs: the `decide` proofs on `2^64`-sized witnesses
  report 7–26 (in `#count_heartbeats` units) against a 200000 limit. No budget override exists
  and none is needed.
* `rg register_option` in the pinned Mathlib checkout lists which linters exist at this revision.

## 2. Findings, rule by rule

Severity: **V** = a violation of the rule as written; **G** = a gap, something the rule asks for
that is missing; **N** = a note (compliant), recorded so it is not re-checked.

### 2.1 `proof-style.md`

| ID | Rule | Site | Finding | Sev |
|---|---|---|---|---|
| P-1 | Non-terminal `simp` → `simp only [...]` derived by `simp?` at that site | `Projection.toCanonical_wf_iff` (l. 437–440): `simp [..6 defs..]` then `tauto` | A bare non-terminal `simp`. Neither `linter.flexible` nor the text proxy flags it (see §1), so this is a blind spot in the gates. `simp?` at the site yields a 30-lemma list. The guide's alternative, stating the intermediate goal with `suffices`, is better | V |
| P-2 | `have` with an explicit type when it is not obvious | l. 149 `have h := List.pairwise_mergeSort …`; l. 622 `have := Projection.ofCanonical?_toCanonical p`; l. 641 `have he := congrArg …`; l. 441 `have := r.code_lt` | The first three hide a non-obvious type. The type at l. 441 is obvious, so that one is only a note | V (×3), N |
| P-3 | One tactic per line, except a one-line closing proof | l. 150 `fun … => by simp only [decide_eq_true_eq] at *; exact hab.trans hbc` | Two state-changing tactics on one line, inside a term. `at *` also hides which hypotheses get rewritten | V |
| P-4 | Announce goals with `show` at decision points | `Reason.toCVal_wf` (the `cases r with` arms), `not_surjective_toCanonical` (witness choice `.null`), `not_mutantIgnoreTag_sound` (witness choice) | No `show` or comment at the risky steps. **Compliant** under the repo's departure D-2, which covers only the load-bearing corpus and proofs of 30 lines or more; every proof here is shorter. **Violation** under a strict reading of the guide | V/N (Q1) |
| P-5 | Terminal `simp` stays unsqueezed | `Resting.canonKey_injective` uses `simp only … at h` *non-terminally*, followed by `obtain` | Compliant: it is non-terminal and squeezed | N |
| P-6 | Layout | `toCanonical_not_wf_time_overflow` and `toCanonical_not_wf_cash_underflow` put `:=` at the end of one line and `by rw […]; decide` on the next | Unidiomatic layout: `by` belongs right after `:=`. The two tactics on one line are fine, because the line is a one-line closing proof | V (minor) |
| P-7 | Long proofs | — | No declaration exceeds 25 lines. The file is 691 lines, under 1000 | N |

### 2.2 `library-design.md` (definitions and their API)

| ID | Rule | Site | Finding | Sev |
|---|---|---|---|---|
| D-1 | No downstream unfolding; `rw [def]` = missing API | `Book.canonical_witness_seq`, `Book.canonical_witness_price`: `rw [..., Book.canonical, List.mergeSort_of_pairwise …]` | They unfold `Book.canonical`. Missing API: `Book.canonical_eq_self_of_pairwise` (a sorted book is its own canonical form). `project_book_perm` unfolds `project`, so the `@[simp]` projection lemmas for `project` (`project_book`, `project_halted`, …) are also missing | V |
| D-2 | Every definition ships its API **in its own file** | `CList.ofList`, `CList.toList`, `CVal.toNat?/toInt?/toBool?` and their simp lemmas are declared in `CanonicalProjection.lean` by re-opening `namespace JournalFormat` | These are API for `JournalFormat`'s types, but they live in a consumer file. A second consumer would have to re-derive them or import an unrelated module. They belong in `RequestProject/Venue/JournalFormat.lean` (Q4) | V |
| D-3 | One canonical spelling per concept (simp-normal form) | The optional-reason encoding `(r.map fun r => CVal.int r.code).getD .null` is spelled out 3 times (`Observation.toCVal`, `Reason.ofCVal?_toCVal`, `Reason.toCVal_wf`) | It needs a definition (`Reason.optToCVal`) with round-trip and `WF` lemmas. Today the two lemmas fire only if someone reproduces the inline term exactly | V |
| D-4 | Same | `InI64 z` and the right-hand side of `CVal.wf_int_iff` are the same predicate, spelled two ways. Every proof bridges them by unfolding `InI64` inside `simp` | Make `InI64` canonical: `@[simp] CVal.wf_int_iff : (CVal.int z).WF ↔ InI64 z`, and unfold `InI64` nowhere downstream | V |
| D-5 | Numeral spelling | `9223372036854775808` and `4294967296` are literals here and in `JournalFormat` | Consistent with `JournalFormat.CVal.WF`, so there is one spelling. The docstrings say `2^63` and `2^32`, but only in prose | N |
| D-6 | Decidable instances | 5 anonymous `instance … := by unfold X; infer_instance` | Works, but `inferInstanceAs` is the idiomatic tactic-free form and does not depend on `unfold` | V (minor) |
| D-7 | `ext`/injectivity API for new structures | `Projection` has `DecidableEq` but no `@[ext]` | The guide asks for one. No current proof needs it, so the value is low | G (minor) |
| D-8 | Search before deriving a helper | `private mapM_some_eq` | `exact?` fails on it, but core's `List.mapM_pure` closes it in one line (`simpa using List.mapM_pure (m := Option) (f := id)`, checked). The helper re-derives library content | V (minor) |
| D-9 | Optimised definition keeps a readable reference | — | n/a: no fast form was introduced | N |

### 2.3 `naming-conventions.md`

| ID | Site | Finding | Sev |
|---|---|---|---|
| N-1 | `Projection.encode_injective : p.Bounded → q.Bounded → p.encode = q.encode → p = q` | The name claims `Function.Injective Projection.encode`, which is **false**: the same file proves the negation, `not_forall_encode_injective`. A name must be computed from the conclusion and the hypotheses. Idiomatic options: restate as `Set.InjOn Projection.encode {p \| p.Bounded}`, named `Projection.encode_injOn_bounded`; or keep the statement and name it `Projection.eq_of_encode_eq` (Q2) | V |
| N-2 | `encode_project_injective` | The same defect, at `project` | V |
| N-3 | `Projection.encode_ne_of_ne` | The name drops the two `Bounded` hypotheses. That is acceptable under the main-hypothesis convention, but the computed name is `encode_ne_of_bounded_of_ne` | N |
| N-4 | Mutant and witness definitions (`mutantDropHalted`, `witnessResting`, …) | `lowerCamelCase` for terms complies with R26. D-4/SR-43 also allows the role word as a component | N |
| N-5 | `InI64`, `*.Bounded` | `Prop`s in `UpperCamelCase`, as required for new code | N |
| N-6 | `Book.canonical_perm`, `Book.pairwise_canonical` | Mirror Mathlib's `mergeSort_perm` / `pairwise_mergeSort` | N |

### 2.4 `linting.md`

| ID | Site | Finding | Sev |
|---|---|---|---|
| L-1 | `LeverageAudit.lean` l. 149 `#check @Venue.Projection.encode_injective` | A leftover debugging probe. It prints an `info:` on every build of the default target | V |
| L-2 | `LeverageAudit.lean` as a gate | It enumerates 33 names by hand. A theorem **added** to `CanonicalProjection.lean` is not pinned, so coverage is only what someone remembered to list. The guide's form is a `collectAxioms` sweep over every declaration of the module, asserting the allowed footprint, with a `checked > 0` vacuity anchor (Q5). The pins themselves are kernel-derived, which is good | G |
| L-3 | `check_leverage_conjectures.py` | It reads declaration statements by regex over the source (via `check_b5_pt03_conjectures.declarations`), so a comment or a reformatting can fool its `[NEGATION]` rule. The guide prefers checks against the elaborated declaration. This is the house pattern it inherits from `check_beta_conjectures.py`, not something new | G (inherited) |
| L-4 | 5 of the 7 hoisted metaprograms (`HandoffV3/Audit.lean`, `NativeDecideTcb.lean`, `ProfEnv.lean`, `DeclarationNames.lean`, `ICACensus.lean`) | No vacuity anchor: if the module filter matched nothing, they would print an empty census and exit 0. `DetSim/Audit.lean` and `AxiomAuditMemo.lean` have one. This comes from a text heuristic (grep for `== 0` / `isEmpty … throw`), to be confirmed when fixed | G |
| L-5 | Project lint profile (`lakefile.toml`) | The guide's profile starts with `linter.auxLemma`, but **that option does not exist at the pinned Mathlib**: `rg register_option` finds no such declaration, and plain `-Dlinter.auxLemma` is rejected. As `weak.linter.auxLemma` it would be silently ignored, which is exactly the trap the guide warns about. Do **not** add it; record that it is unavailable at this pin | N (important) |
| L-6 | Project lint profile | `linter.flexible` is not in `[leanOptions]`; it runs only on demand. The guide recommends it for maintained artefacts. It is clean on these files, but P-1 shows it is not a complete check for R10b | G (project-wide, Q3) |
| L-7 | `#guard` lines in `CanonicalProjection.lean` | `hashCommand` flags them. The guide says to omit `hashCommand` for exactly this reason, since a `#guard` is an assertion. Compliant under the project profile. Their natural home may be a test module (Q3) | N |

### 2.5 `performance.md`

| ID | Finding | Sev |
|---|---|---|
| F-1 | No `maxHeartbeats` or `maxRecDepth` override was added, and measured costs are tiny (§1) | N |
| F-2 | The item-5 timings are one run per side on a shared host, labelled "indicative" in the report. They are whole-program wall-clock times, so they only partly follow the guide's advice to measure per declaration rather than by build wall-clock. The load-bearing claim, byte-identical output, was checked | N |
| F-3 | The guide says to land performance changes separately from functional ones. Here the hoist and the new proofs landed in one session, and the history is a single commit. Splitting it now would mean rewriting pushed history, which we will not do. Future performance changes get their own commit | G (process) |

### 2.6 `tactics.md` (metaprograms touched by item 5)

| ID | Finding | Sev |
|---|---|---|
| T-1 | `moduleNames[i.toNat]!` (a panicking index) at 9 sites. The index comes from `getModuleIdxFor?`, so it is valid by construction, but the guide prefers `?` destructors with a clear error | V (minor) |
| T-2 | No speculative state, `evalTactic` or metavariable assignment in these programs | N |

### 2.7 `llm-techniques.md`, `anti-patterns.md`

* No `native_decide` in the new files. Every footprint is within {propext, Classical.choice, Quot.sound} (N).
* No global `Fact`, `erw`, `irreducible`, `@[implemented_by]` or `axiom` (N).
* No heavyweight closer is used to skip structure, except `tauto` in P-1, which the plan replaces
  with a stated intermediate goal.

## 3. Refactor plan (ordered; each step builds and passes the gates before the next)

Statements are the interface (R15). Steps 1–5 change proofs and add lemmas only. Step 6 is the only
step that changes registered names, and it waits for the answer to Q2.

1. **Remove scaffolding.** Delete the `#check` (L-1). Fix the P-6 layout and wrap the two long
   lines.
2. **Add the missing API, in the owning files** (D-1, D-2, D-3, D-4, D-6, D-8):
   * move `CList.ofList/toList`, `CVal.toNat?/toInt?/toBool?` and their lemmas into
     `JournalFormat.lean` (Q4), with `@[simp]` constructor-case lemmas;
   * add `Reason.optToCVal` with its round-trip and `WF` lemmas, and use it in `Observation.toCVal`;
   * restate `CVal.wf_int_iff` in terms of `InI64`, and move `InI64` beside `CVal.WF`;
   * add `Book.canonical_eq_self_of_pairwise` and `project_*` simp lemmas (via `@[simps]` or by
     hand), and use them in the witnesses and in `project_book_perm` instead of
     `rw [Book.canonical]`;
   * replace `mapM_some_eq` with core `List.mapM_pure`, and write the instances with
     `inferInstanceAs`.
3. **Restructure the proofs** (P-1, P-2, P-3, P-4):
   * P-1: use a `suffices` that states the per-field conjunction, or a `simp only` derived with
     `simp?`;
   * P-2: give the three `have`s explicit types;
   * P-3: move the lambda into a named `have`, one tactic per line;
   * P-4: add a `show` or a comment at each case split and witness choice under a strict reading of
     the guide, or none under D-2 (Q1).
4. **Fix the gates** (L-2, L-4, T-1):
   * add a `collectAxioms` sweep over every `Venue.*` declaration of
     `RequestProject.Venue.CanonicalProjection`, asserting the allowed footprint, with a
     `checked > 0` anchor and a planted-failure fixture;
   * add vacuity anchors to the 5 metaprograms and replace `!` with `?` plus an error;
   * re-run the item-5 byte-identity comparison afterwards.
5. **Close the P-1 blind spot** in `audit_lean_proof_style.py`: make `nonterminal_simp` join a
   wrapped `simp` call before inspecting the next tactic. Add a self-test fixture with exactly this
   shape, so the gate can be shown to fail on it.
6. **Rename** N-1 and N-2, per Q2. Update `register/leverage_conjectures.tsv`,
   `LeverageAudit.lean`, `property_registry.json`, `docs/latex/axiom_audit.tsv` and the Properties
   table in the same commit, with `@[deprecated] alias` entries if wanted.
7. **Project-wide items**, only if in scope (Q3):
   * measure the full-tree backlog for `linter.flexible`, then add it to `[leanOptions]` with a
     table row (LP1–LP3) and a trigger fixture;
   * record in `LEAN_LINT_POLICY.md` that `linter.auxLemma` is unavailable at this pin;
   * move the witnesses, mutants and `#guard`s into a test module.
8. **Verify:**
   * `lake build` of the touched targets, and `#print axioms` for every registered result;
   * `check_leverage_conjectures.py` and its `--selftest`;
   * `check_promoted_linters.py` and `audit_lean_proof_style.py --selftest`;
   * the on-demand `linter.flexible` run, which must report zero.

## 4. Clarifying questions (asked before any change)

* **Q1 (precedence).** Should the guide apply verbatim, overriding the repository's recorded
  departures (D-2 on `show` presence, R10a, D-4)? Or should it apply as amended by them?
* **Q2 (renames).** For the registered theorems in N-1 and N-2: rename with deprecated aliases,
  rename outright, or keep the names and document the mismatch?
* **Q3 (scope).** Only the artefacts of the last run, or also the project-wide lint profile and a
  split of the test fixtures into their own module?
* **Q4 (helper location).** May the `CVal`/`CList` helpers move into
  `RequestProject/Venue/JournalFormat.lean`, an existing module that other files import?
* **Q5 (axiom gate).** Replace the hand-listed pins with a module-wide `collectAxioms` sweep, or
  keep the pins (the register checker reads them) and add the sweep beside them?

## 5. Execution

The plan was carried out under the answers Q1 = verbatim, Q2 = rename outright, Q3 = full scope,
Q4 = yes, Q5 = keep pins and add sweep. Results, measurements and corrections to the findings above
are in `REPORT.md` in this directory.
