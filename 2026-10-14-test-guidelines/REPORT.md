# Testing-guideline review — 2026-10-14

This review checks every test in the repository against four anti-patterns:

| Code | Anti-pattern | What it looks like in code |
|---|---|---|
| **G1** | Hard-coding to pass tests | Production code returns the expected output for known test inputs instead of applying the rule |
| **G2** | Mistaking examples for rules | One test value, ID or witness is treated as the whole requirement |
| **G3** | Circular debugging | Each failure gets a patch for that one case, and nobody steps back to the requirement |
| **G4** | No generalisation | The code or the test only works on the suite's own inputs |

For each violation found, the requirement was written down in abstract terms (no test values). The
test was then extended with **two counterexamples** and **two negations**:

* **Counterexample**: an input deliberately far from the original witnesses (other IDs, accounts,
  prices, screens, keys, operating points), or a randomised family of such inputs. The general rule
  must still hold there. An implementation fitted to the old examples fails it.
* **Negation**: a check that the rule can actually fail. Either an overfitted or unguarded
  implementation is shown to break the new property, or an input the rule says must *not* fire is
  shown not to fire. Without this, a property that is always true would also pass.

Where a counterexample exposed a real gap in production code, the code was fixed against the
requirement, not against the test.

---

## 1. Method (step by step)

### Step 1 — Inventory
`scans/inventory.py` classifies every code file outside `.lake/` and `docs/archive/`:

| | Count |
|---|---|
| Test files (all languages) | **425** (≈128 k lines including fixtures) |
| — Lean (`RequestProject/**/Testing`, `PaperTests`, `*Tests.lean`, …) | 190 |
| — Node (`services/*/test`) | 123 |
| — Python (`scripts/test_*.py`, `tests/v3`, `test_reporting`) | 74 |
| — Solidity (`contracts/test`) | 38 |
| Production code files | 1 320 |

The list is in `scans/inv.json`. A cross-check found no file with test functions that the
classifier missed. The two files it flagged define test helpers, not tests.

### Step 2 — Baseline run (before any change)
| Suite | Result |
|---|---|
| Node: api-gateway / asp-client / asp-operator / demo-screens / mvp-wal / test-support / transport-auth / venue-engine | 56 / 106 / 319 / 15 / 139 / 8 / 15 / 260 — all pass |
| Python (`scripts/run_unit_suites.py`, 70 modules) | 1 356 tests, **1 failure** (`test_dev_env_setup`, see §5) |
| pol-suite (Miniflare) | **not runnable here**: no `node_modules` |
| Solidity (Foundry) | **not runnable here**: no `forge` |

### Step 3 — G1 scan: do test values leak into production code?
* **Test-mode branches**: production sources under `services/*/src|bin` and `contracts/src` were
  searched for `NODE_ENV`, `process.env.*TEST*`, `isTest`, `__TEST__`, `TEST_MODE` and
  `PYTEST_CURRENT_TEST`. **None found.**
* **Literal overlap** (`scans/leak.py`): 384 ID-like literals were taken from test files (strings
  with letters and digits, hex values, long numbers). Each one was looked up in all production code
  (`services`, `contracts/src`, `reference`, `scripts`, `tooling`, `perf/tools`). **134** appear in
  both. Every one was inspected (`scans/literal_overlap.txt`). All 134 are one of the following:
  specification constants (error selectors, schema names such as `venue-conformance-v1`, decision
  IDs such as `DG-D-10`, pinned commit hashes, header names), documentation comments, or planted
  fixtures inside the checkers' own `--selftest` routines. **None is used to decide behaviour on a
  test input.**
* **Special-casing on values**: production runtime code was searched for comparisons against
  numeric literals other than 0 and 1, and against string literals. Every hit is enum dispatch
  (`kind`, `severity`, `posture`, …) or a format rule (for example, `space !== 8` is the CRC-32 hex
  width). **None found.**

**G1 verdict: no hard-coding to pass tests was found in production code.**

### Step 4 — G2/G4 scan: which tests rest on examples only?
`scans/metrics.py` scores each Node, Python and Solidity test file
(`scans/test_file_metrics.csv`). It counts test cases, assertions, equality checks against
literals, negative checks (throws, refusals, reverts), generated inputs (seeded PRNGs, fuzzing,
`requireHits`) and mutation or planted-fault checks.
* 15 files have **no generated inputs and no negative checks**.
* 23 more have no generated inputs and assert mostly against literals.

Each of these 38 files was then read. So were the Lean test layers: 190 files, about 1 077
declarations, with quantifiers or `Plausible` in almost every file and an independent reference
model in the generator suites.

### Step 5 — G3 scan: patch-per-case history
Searched tests and checkers for dated "added after / passed the earlier / one per defect" notes. The
clearest case is `scripts/check_cd_gate.py`, W7: *"each of these passed the earlier lint"*. Its test
enumerates five specific bypass strings. That lint is a deny-list grown one finding at a time
(violation V6). `services/mvp-wal/bin/mutation-matrix.mjs` also has rows added "one per defect
fixed". That is a mutation catalogue, which is a legitimate use of per-defect rows, so it was not
rewritten.

### Step 6 — Deep read, probing, rewriting
For each candidate, the requirement was stated abstractly. Inputs outside the examples were then
probed against the real code *before* any test was written. That is how the four production gaps in
§3 were found. They were found by asking "what does the rule say about an input the tests never
used?", not by reading test failures.

---

## 2. Verdict by area

| Area | Files | Verdict |
|---|---|---|
| Lean test layers (`Fame/Testing`, `PaperTests`, `GEX/Tests`, …) | 190 | **Compliant.** They test theorems that are proved for all inputs. Generator suites compare against an independent reference engine. Golden cases are labelled as golden. Minor note: `PaperTests` sample over small token domains (`natBelow 9 t`). That is acceptable because the proofs, not the samples, carry the general claim. |
| venue-engine | 37 | Mostly compliant (corpus differentials, mutation kill sets, properties). **V1, V2** rewritten. Observation O1. |
| asp-operator | 33 | Compliant: property suites with `requireHits` budgets, stub-RPC tests with distinct values, planted faults. |
| asp-client | 10 | **V3** (production gap fixed). |
| demo-screens | 3 | **V4** (production gap fixed). |
| mvp-wal | 23 | **V8** rewritten. Everything else is property or mutation based. |
| api-gateway, transport-auth | 8 | Compliant. Literal-heavy, but the literals are status codes from the contract, each with negative controls. |
| pol-suite | 7 | **V9** rewritten (could not be executed here). |
| Python gate tests (`scripts/test_*.py`) | 70 | Mostly compliant: many use exhaustive small domains, randomised mutants, or a "this repository is clean" check. **V5, V6** (production gaps fixed) and **V7** rewritten. |
| Solidity (`contracts/test`) | 38 | Compliant by reading: fuzz and invariant handlers plus mutant contracts (`NaiveAccess`). Not executable here. |

---

## 3. Violations, requirements, and the counterexamples and negations added

Legend: **Prod gap** = a counterexample failed on the real code, and the code was fixed against the
stated requirement.

### V1 — `services/venue-engine/test/authorization.test.mjs` (G2, G4)
* **Evidence:** every witness uses one book holding order `1`, owned by account `1`, with account
  `2` as the stranger. A guard that refused "sender 2 on order 1" would pass the whole file.
* **Requirement R-AUTH:** for every state, sender and event, a cancel or amend of a resting order
  whose owner is not the sender is refused with `unauthorized` and leaves the state unchanged.
  Every other message behaves exactly like the unguarded step.
* **Counterexamples:** (1) the roles are swapped: account 1 is the stranger, account 37 owns order
  4711, and account 2 is a stranger to account 8's order. (2) R-AUTH is checked over 3 000 random
  books, owners, senders and identifiers, with both branches required to be exercised.
* **Negations:** (1) an overfitted guard that reproduces every original witness is rejected by
  R-AUTH. (2) The unguarded step is shown to violate R-AUTH on a generated case.
* **Prod gap:** none. `authorization.mjs` is already general.

### V2 — `services/venue-engine/test/nocross.test.mjs` (G2)
* **Evidence:** the test "the book is uncrossed at every state of a repaired run" is named after
  the universal theorem `venue_book_is_never_crossed`. It replays only three fixed traces, under
  one configuration, at prices 98–110.
* **Requirements:** R-NOCROSS: every state the repaired engine reaches from genesis has no crossing
  pair, for any configuration and any events. R-PRICE: an amendment that becomes marketable trades
  at the resting price.
* **Counterexamples:** (1) the audit's amend-through-the-offer shape is replayed at price 1000/990,
  amended to 1200, with accounts 31/32 and another configuration. The book stays uncrossed and the
  notional is 4 × 1000. (2) 400 random runs of up to 25 mixed events under random configurations
  are checked at every prefix. The generator is also required to cross the *shipped* engine at
  least once, so the check is not vacuous.
* **Negations:** (1) the same generator finds a crossed book under the shipped engine. (2) The
  predicate is not trivially true: a hand-built cross is reported, while same-account pairs and
  exhausted orders are not.
* **Prod gap:** none.

### V3 — `services/asp-client/test/assurance.test.mjs` (G2, G4) — **Prod gap fixed**
* **Evidence:** the only negative control is one sentence that spells two forbidden phrases exactly
  as listed. Probing showed the detector missed `"formally verified\n contract"` (copy wrapped over
  a line), double spaces, tabs, and `"risk free"`.
* **Requirement R-CLAIM:** a forbidden claim is detected whatever its letter case, whitespace or
  line wrapping, and whether its words are joined by a hyphen or a space. Text that makes no such
  claim is not reported.
* **Counterexamples:** (1) a claim wrapped across a line break. (2) Every listed phrase in five
  spelling variants. **Both failed on the old code.**
* **Negations:** (1) near-miss copy ("design is formally verified; the contract is tested", "returns
  are not guaranteed") is not reported. (2) The client's own assurance texts stay clean under the
  wider matcher.
* **Fix:** `forbiddenClaimsIn` (in `src/assurance.mjs`) now collapses case, whitespace runs and
  hyphens before matching. The Python twin gate `scripts/check_asp_client_honesty.py` got the same
  normalisation, so the two implementations agree.

### V4 — `services/demo-screens/test/symmetry.test.mjs` (G2, G4) — **Prod gap fixed**
* **Evidence:** both planted faults sit on `screen-6` and keep the exact `class="card
  falsification…"` prefix that the checker searched for. A card with its classes written in another
  order was never counted as a falsification card at all, so a softened card escaped.
* **Requirement R-SYMMETRY:** every `<article>` whose class list holds `card` and `falsification`,
  in any order and on any screen, must have the same style signature.
* **Counterexamples:** (1) a softened card on each screen other than Screen 6. (2) A reordered and
  softened card on Screen 3. **(2) failed on the old code.**
* **Negations:** (1) the unmodified render has no symmetry problem. (2) Reordering classes alone,
  without changing style, is not reported.
* **Fix:** `articles()` in `src/checks.mjs` now matches on the class *token set*, not a string
  prefix.

### V5 — `scripts/test_check_naming.py` (G2, G4) — **Prod gap fixed**
* **Evidence:** every example declares with a bare `def` and no attribute. Probing showed
  `@[simp] def x` outside a namespace was **not** caught. The pattern accepted an attribute only
  when a modifier such as `private` followed it. `axiom` was not treated as a declaration at all.
* **Requirement:** NM-L1 and NM-L2 apply to every declaration, however it is decorated.
* **Counterexamples:** (1) `@[simp] def`, `@[simp, inline] theorem` and `@[reducible] abbrev`
  outside a namespace. (2) Collisions declared with `@[simp] theorem` and with `axiom`. **Both
  failed on the old code.**
* **Negations:** (1) `@[simp] private` helpers may still share a name. (2) `@[inline] def main` and
  code inside a block comment are not findings.
* **Fix:** `DECL_RE` in `scripts/check_naming.py` accepts an attribute list with or without a
  following modifier, and includes `axiom`. The repository-wide check (`test_this_repository_is_clean`)
  still passes.

### V6 — `scripts/test_cd_gate.py` / `scripts/check_cd_gate.py` workflow lint (G3, G4) — **Prod gap fixed**
* **Evidence:** the lint grew a clause for each finding: W7 says *"each of these passed the earlier
  lint"*. The tests list five specific bypass strings. Probing with job keys no finding had named
  showed two gaps. `container:` on the gate or deploy job was **accepted**; the image would decide
  what `python3` runs. Job-level `permissions: {contents: write}` was also **accepted**.
* **Requirement R-CD:** a job is accepted only if every key it sets is on an allowlist of keys whose
  effect on the authorisation is understood. This replaces a deny-list of keys that have already
  been abused.
* **Counterexamples:** (1) `container` on each job. (2) Job-level write permissions. **Both failed
  on the old code.**
* **Negations:** (1) the committed workflow is still accepted. (2) Harmless allowed edits (`name`,
  `timeout-minutes`) are still accepted.
* **Fix:** new rule **W8** with `JOB_KEYS_ALLOWED` in `scripts/check_cd_gate.py`. The checker's own
  selftest and lint both pass.

### V7 — `scripts/test_asp_register_reconciliation.py` (G2)
* **Evidence:** the two mutation tests break exactly one row each (review row `C-01`, appendix row
  `A-07`).
* **Requirement R-RECON:** for every reconciled label, dropping its appendix row or renumbering its
  review row is reported. Edits that touch neither are not.
* **Counterexamples:** (1) every appendix row is dropped in turn. (2) Every reconciled review row is
  renumbered in turn.
* **Negations:** (1) renumbering review rows the appendix does not reconcile (first and last) gives
  no error. (2) An edit that keeps every row gives no error.
* **Prod gap:** none. The gate is general.

### V8 — `services/mvp-wal/test/capacity.test.mjs` (G2)
* **Evidence:** every figure is pinned at the review's own operating point (100/s, 10 ms, 1.5 ms).
  A lookup table returning those numbers would pass.
* **Requirements R-CAP-1..4:** linearity of the counting quantities; the fixed-window bounds
  `fsync rate ≤ min(λ, 1/T)` (rising with λ) and `batch ≥ max(1, λT)`; saturation exactly when
  `λ·S ≥ 1`; pipelining never longer; the P-K wait rising with ρ; refusal of every input outside the
  domain.
* **Counterexamples:** (1) closed forms at operating points the review never used, including the
  M/M/1 special case. (2) 2 000 random parameter sets, with bounds compared one representable step
  away (`nextUp`/`nextDown`, as the repository's rule J4 requires).
* **Negations:** (1) a lookup table that reproduces the pinned figure is exposed by R-CAP-1.
  (2) NaN, ±∞ and negative inputs are refused by every function, not only the three original spot
  checks.
* **Prod gap:** none. Observation: `recommendFsyncPolicy().policy` is a constant by design, so the
  "all rates → group-commit" assertion cannot fail. It records a decision rather than testing a
  rule.

### V9 — `services/pol-suite/test/concurrency.test.mjs` (G2)
* **Evidence:** one instrument, one batch of 16, amounts 1..16 with the total `"136/1"` written in,
  and one retry fan-out of 6.
* **Requirements:** R-SERIAL: any batch is journalled once each, at sequence numbers 1..n, with
  replayed total = Σ amounts. R-IDEMP: a fan-out of k retries gives one application and k − 1
  replays.
* **Counterexamples:** (1) a seeded instrument, batch size and uneven amounts, with the total
  computed from the amounts. (2) Fan-outs of 2 and 11.
* **Negations:** (1) distinct keys are *not* deduplicated. (2) Two instruments do not share a
  sequence or a total.
* The four tests were registered in `proofs/pol/pol_suite_deployment_manifest.json`, which the
  traceability gate requires. **Not executed in this environment** (no Miniflare). The file passes
  `node --check`.

---

## 4. Observations (not rewritten)
* **O1** `venue-engine/test/differential.test.mjs`: "replay composes" and "the engine is a pure
  function" are general properties checked only over the committed corpus. Low risk, because
  `properties.test.mjs`-style generators exist elsewhere. A random-trace version would be the
  natural next step.
* **O2** `check_cd_gate.py` does not restrict `runs-on` (for example `self-hosted`). Whether a
  self-hosted runner is acceptable is a policy decision. It is left open in §6.
* **O3** Several checker scripts embed self-test fixtures that reuse IDs such as `A-99`, `D-0` or
  `screen-6`. These are planted sentinels by design (`docs/standards/SENTINEL_IDS.txt`), not
  hard-coding.

## 5. Results after the changes
| Suite | Before → after |
|---|---|
| venue-engine | 260 → **268** pass |
| asp-client | 106 → **110** pass |
| demo-screens | 15 → **19** pass |
| mvp-wal | 139 → **143** pass |
| test-support | 8 → **9** pass (new `seededRandom` helper and its test) |
| api-gateway / asp-operator / transport-auth | unchanged, all pass |
| Python modules | 1 356 → **1 368** tests. The only failure is the same one as in the baseline. |
| Gates re-run: `check_test_rigor`, `check_naming`, `check_cd_gate`, `check_asp_client_honesty`, `check_demo_claims`, `check_asp_register_reconciliation`, `audit_pol_suite_deployment`, `check_repo_hygiene`, `check_script_coverage`, `check_source_headers` | all pass |

**Pre-existing failure, not caused by this work:** `scripts/test_dev_env_setup.py ::
test_a_clean_commit_is_accepted`. The delivered tree has no `scripts/.gitignore`, so the hygiene
pre-commit hook refuses a commit inside the test's scratch clone. It failed identically before any
change.

## 6. Next steps
1. **Run the suites this environment could not run:** pol-suite (`npm ci && npm test`, for V9) and
   Foundry (`forge test`).
2. **Decide O2:** whether `runs-on` must be a GitHub-hosted label. If so, extend W8 with a
   `runs-on` allowlist.
3. **Restore `scripts/.gitignore`** (rules `__pycache__/` and `*.pyc`), or run
   `bash scripts/bootstrap_layer0.sh`, so `test_dev_env_setup` passes again.
4. **Turn the review into a standing rule:** add a guideline to `docs/standards/TEST_RIGOR_STYLE.md`.
   Any test named after a universal property (or citing a universal theorem) must carry at least
   one generated or off-witness case, plus a negation (a mutant or an overfit implementation it
   rejects). `scripts/check_test_rigor.py` could enforce this mechanically by flagging files with
   `gen = 0` and `neg = 0` in `scans/test_file_metrics.csv`.
5. **Address O1** with a random-trace version of the composition and purity properties.
6. **Re-run `scans/leak.py`** whenever new fixtures are added. It is the mechanical check that no
   literal test input reaches production logic.

## 7. Files changed
* Tests: `services/venue-engine/test/{authorization,nocross}.test.mjs`,
  `services/asp-client/test/assurance.test.mjs`, `services/demo-screens/test/symmetry.test.mjs`,
  `services/mvp-wal/test/capacity.test.mjs`, `services/pol-suite/test/concurrency.test.mjs`,
  `scripts/test_check_naming.py`, `scripts/test_cd_gate.py`,
  `scripts/test_asp_register_reconciliation.py`, `services/test-support/test/rigor.test.mjs`.
* Production fixes, each driven by a stated requirement: `services/asp-client/src/assurance.mjs`,
  `scripts/check_asp_client_honesty.py`, `services/demo-screens/src/checks.mjs`,
  `scripts/check_naming.py`, `scripts/check_cd_gate.py`.
* Support: `services/test-support/rigor.mjs` (`seededRandom`),
  `proofs/pol/pol_suite_deployment_manifest.json` (traceability of the new pol-suite tests).
* Evidence: `audit/2026-10-14-test-guidelines/scans/` (scanner scripts, inventory, literal-overlap
  list, per-file metrics).
