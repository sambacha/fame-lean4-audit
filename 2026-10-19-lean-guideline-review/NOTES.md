# Scratch notes — guideline digest
Core: design top-down, prove bottom-up; statements = interface.
Perf rules: measure per-decl (#count_heartbeats), every maxHeartbeats override = unproven claim (bisect),
 scoped `in` only; rfl/decide => kernel replays; count reduction paths; left-nested ++ exponential;
 keep readable ref def + fast def + eq theorem.
Tactic rules: terminal simp unsqueezed; non-terminal simp -> simp only (derive w/ simp? at site);
 `·` focus per goal (multiGoal); show must not change goal; calc for rw chains; typed have;
 no downstream unfold / erw / trailing rfl (missing API); no unscoped set_option maxHeartbeats/ debug;
 one tactic per line generally; Fact local; simpNF; maxDischargeDepth; @[simp ↓].
Gate: collectAxioms not grep; linters by role: auxLemma, maxHeartbeats, multiGoal, setOption, show (+ flexible etc for libs).

## Measurement facts (this host, serial runs)
- M1 [TESTED] decls in one file are kernel-checked SEQUENTIALLY: 1 decide = 8.5/8.5/8.5 s wall, 3 decides = 22.1/22.5/22.2 s (user ~= wall).
  => trace.profiler Elab.async times are CUMULATIVE; per-decl cost = successive deltas.
- SeamCorpus per-decl (deltas): boundary 18.4, one_sided 1.8, fifty 54.7, fifty_one 50.3, reaches 17.5, preflight 138.9  (sum ~282 s)
- Earlier scratch numbers re-read as deltas: clear(50 fifty cases) 6.1; ledger +6.3; Mathlib dedup accounts +17.6;
  preflight(fiftyCases) 54.5 (orig) vs 48.5 (dedupLast) => dedup swap alone ~11%.
  netCash over fiftyCases ~22 s, netFee ~27 s (each incl. recompute of clear/ledger/accounts ~8 s) => bucketSum dominates.
- Retraction: "Int lacks GMP" wrong mechanism. Leaves are GMP Nat; cost = instance unfolding in List.sum/foldr + Int ctor matching.
- 64us/op = [ESTIMATED], op count unvalidated.
- #count_heartbeats in reported 27 (k) for CallV2 proof that actually times out at 200k => does NOT measure async proof body here. Use compile-at-budget test instead.
- CallV2: settleGuardsV2_none_imp at default 200k budget => TIMEOUT (needs override); iff-lemma via simp only [ite_some_eq_none_iff] => whole file 6.6 s wall incl import, no decl >50 ms.
- FUSE test (fiftyCases, import baseline 10.9s median): separate 2 decls 76.6s net, fused 52.6s net (-31%). spread<=3.1s.
- IMPROVEMENT 1 SeamCorpus fusion: before 296.0/287.5/286.9 (med 287.5) -> after 151.0/147.8/146.9 (med 147.8): -48.6%, 1.95x. Statements/names unchanged; +1 decl corpus_measurements.
- CallV2 before: 48.8/47.4/46.9 wall (med 47.4), user 84 => tactic bodies DO run in parallel (user/wall 1.8); M1 sequential finding is specific to decide +kernel kernel checks. Two split_ifs decls ~60s cumulative each, overlapping.
- IMPROVEMENT 2 CallV2: removed 2x maxHeartbeats 1e6; split_ifs(11 clauses) -> settleGuardsV2_eq_none_iff via simp only [ite_some_eq_none_iff,...]. wall 48.8/47.4/46.9 -> 8.2/7.8/7.7 (6.1x), user 84->7.9 (10.7x). Search: exact? found no Mathlib lemma for (if c then some a else x)=none ↔ ¬c ∧ x=none.
- CAVEAT C1: [Elab.command] times of commands that read the checked env (structure, example, #detsim_*, getEnv) include WAITING for earlier async kernel checks. DetSim.Conformance #detsim_runtime_checked 233.6s, Selectors example 190s, SupplyManifest structure 118.8s => NOT own cost (Tiers.lean elab is O(1) lookups + one collect). Only count after direct timer.
- IMPROVEMENT 3 root cause [TESTED with in-process timers]: EnvironmentHeader.moduleNames = header.modules.map (·.module) (Lean/Environment.lean:203) recomputed per constant. NumericFootprint enumerate 222.3s vs hoisted-free loop 0.53s vs moduleData route 6 ms; 53 axiom collections 3.0s (initial hypothesis "fresh collect state" REFUTED).
- IMPROVEMENT 3 confirmed: interleaved user-CPU A/B NumericFootprint 241.2 -> 13.5 s (17.9x); generated C: moduleNames call moved from forIn loop spec to enclosing fn in all 4 modules.
- Full rebuild after: rc 0, 9040 jobs, 0 warnings, 2101 s wall; edited modules 1263 -> 294 s job time; unchanged +423 s (noise).
- Axiom audit regen: +3 rows, 6 SeamCorpus rows propext -> propext,Quot.sound (projection of fused conj incl. preflight), -1 pre-existing duplicate gexPlus.eq_1 row.
- I4 AxiomAudit.lean hoist: 1865 -> 1627 s, n=1, byte-identical output; remaining cost = per-theorem CollectAxioms.
