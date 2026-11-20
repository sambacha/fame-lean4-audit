/-
Environment extractor for the 2026-10-17 profiling audit (Phases 0.4, 3A.1, 4.0).

    lake env lean --run audit/2026-10-17-lean-profiling/tools/ProfEnv.lean MODLIST SCOPELIST OUTDIR

MODLIST is a file with one module name per line; SCOPELIST lists every in-scope module (use edges
are kept when the used constant is owned by a SCOPELIST module). The MODLIST modules are imported
into one environment (libraries that redefine the same names, e.g. `AgentHandoff` and
`HandoffV3`, or executable roots that each define `main`, go in separate groups; see
`envgroups.py`), which is read from the built `.olean` files only, so nothing is
elaborated. Three files are written to OUTDIR:

* `axioms.tsv`: `declaration  module  axiom_set` for every constant owned by a listed module
  whose name is not `Name.isInternal` (so equation lemmas `f.eq_1` are included, as in
  `scripts/AxiomAudit.lean`). `axiom_set` is sorted and comma-separated. It uses the same successor relation as
  `Lean.CollectAxioms.collect` (the engine of `#print axioms`), memoized per strongly connected
  component (Tarjan); only the *set* is kept, so discovery order does not matter.
* `axioms_all.tsv` (only when the environment variable `PROFENV_ALL` is set): the same, for every
  constant owned by a listed module, internal names (`_proof_`, `match_`, `_aux`, native-decide
  auxiliaries, …) included.
* `imports.tsv`: `importer  imported` for every direct import of a listed module, read from the
  module headers stored in the `.olean` files (the compiled import graph).
* `used.tsv`: `declaration  used` for every pair where a listed module's non-internal constant
  mentions another constant (`ConstantInfo.getUsedConstantsAsSet`) owned by a listed module.
  Internal names (`_proof_`, `match_`, `_aux` helpers) are resolved to their nearest
  non-internal prefix, so edges that pass through helpers are kept.
-/
import Lean
open Lean

namespace ProfEnv

def succs (env : Environment) (c : Name) : Array Name :=
  match env.find? c with
  | some (.axiomInfo v) => v.type.getUsedConstants
  | some (.defnInfo v) => v.type.getUsedConstants ++ v.value.getUsedConstants
  | some (.thmInfo v) => v.type.getUsedConstants ++ v.value.getUsedConstants
  | some (.opaqueInfo v) => v.type.getUsedConstants ++ v.value.getUsedConstants
  | some (.quotInfo _) => #[]
  | some (.ctorInfo v) => v.type.getUsedConstants
  | some (.recInfo v) => v.type.getUsedConstants
  | some (.inductInfo v) => v.type.getUsedConstants ++ v.ctors.toArray
  | none => #[]

def isAxiom (env : Environment) (c : Name) : Bool :=
  match env.find? c with
  | some (.axiomInfo _) => true
  | _ => false

structure St where
  memo : NameMap NameSet := {}
  index : NameMap Nat := {}
  low : NameMap Nat := {}
  onStack : NameSet := {}
  stack : Array Name := #[]
  next : Nat := 0

abbrev M := ReaderT Environment (StateM St)

def getN (m : NameMap Nat) (k : Name) : Nat := (m.find? k).getD 0

/-- Tarjan. Inside a strongly connected component every member reaches the same constants, so all
members get one set: the component's own axioms plus the memoized sets of the components it
points to (already finished, since Tarjan finishes components in reverse topological order). -/
partial def strong (v : Name) : M Unit := do
  let env ← read
  let i := (← get).next
  modify fun s => { s with index := s.index.insert v i, low := s.low.insert v i, next := i + 1,
                           stack := s.stack.push v, onStack := s.onStack.insert v }
  for w in succs env v do
    match (← get).index.find? w with
    | none =>
      strong w
      modify fun s => { s with low := s.low.insert v (min (getN s.low v) (getN s.low w)) }
    | some iw =>
      if (← get).onStack.contains w then
        modify fun s => { s with low := s.low.insert v (min (getN s.low v) iw) }
  let s ← get
  if getN s.low v == i then
    let mut stack := s.stack
    let mut members : Array Name := #[]
    let mut onStack := s.onStack
    repeat
      let w := stack.back!
      stack := stack.pop
      onStack := onStack.erase w
      members := members.push w
      if w == v then break
    let comp : NameSet := members.foldl (·.insert ·) {}
    let mut acc : NameSet := {}
    for x in members do
      if isAxiom env x then acc := acc.insert x
      for d in succs env x do
        unless comp.contains d do
          for a in ((s.memo.find? d).getD {}).toList do acc := acc.insert a
    let mut memo := s.memo
    for x in members do memo := memo.insert x acc
    set { s with stack, onStack, memo }

def axiomsOf (c : Name) : M NameSet := do
  if (← get).index.find? c |>.isNone then strong c
  return ((← get).memo.find? c).getD {}

/-- Nearest non-internal prefix (`foo._proof_1` ↦ `foo`, `foo.match_1` ↦ `foo`). -/
partial def publicOwner (n : Name) : Name :=
  if n.isInternal || n.isInternalDetail then
    match n with
    | .str p _ => publicOwner p
    | .num p _ => publicOwner p
    | .anonymous => n
  else n

def sortedNames (s : NameSet) : List String :=
  (s.toList.map toString).toArray.qsort (· < ·) |>.toList

/-- Sort and drop adjacent duplicates. -/
def sortUniq (a : Array String) : Array String := Id.run do
  let s := a.qsort (· < ·)
  let mut out : Array String := #[]
  for x in s do
    if out.back? != some x then out := out.push x
  return out

def readNames (path : String) : IO (List Name) := do
  return ((← IO.FS.readFile path).splitOn "\n").filter (· ≠ "") |>.map String.toName

def run (modlist scopelist outdir : String) : IO UInt32 := do
  let mods ← readNames modlist
  let scope ← readNames scopelist
  initSearchPath (← findSysroot)
  let env ← importModules (mods.toArray.map fun m => { module := m }) {} (trustLevel := 1024)
    (loadExts := true)
  let modSet : NameSet := mods.foldl (·.insert ·) {}
  let scopeSet : NameSet := scope.foldl (·.insert ·) {}
  -- Read once: `EnvironmentHeader.moduleNames` rebuilds an array over every imported module on each
  -- call (Lean 4.28), so reading it inside the per-constant loop is quadratic.
  let moduleNames := env.header.moduleNames
  let ownerIn (s : NameSet) (n : Name) : Option Name := do
    let mi ← env.getModuleIdxFor? n
    let m ← moduleNames[mi.toNat]?
    if s.contains m then some m else none
  let ownerMod := ownerIn modSet
  let inScope := ownerIn scopeSet
  let mut imps : Array String := #[]
  for i in [:moduleNames.size] do
    let some m := moduleNames[i]? | continue
    let some d := env.header.moduleData[i]? | continue
    if modSet.contains m then
      for im in d.imports do
        imps := imps.push s!"{m}\t{im.module}"
  IO.FS.writeFile (outdir ++ "/imports.tsv")
    ("importer\timported\n" ++ String.intercalate "\n" (sortUniq imps).toList ++ "\n")
  let all := (← IO.getEnv "PROFENV_ALL").isSome
  let mut st : St := {}
  let mut axRows : Array String := #[]
  let mut allRows : Array String := #[]
  let mut usedRows : Array String := #[]
  for (n, ci) in env.constants.toList do
    let some mod := ownerMod n | continue
    let o := publicOwner n
    if all || !n.isInternal then
      let (axs, st') := ((axiomsOf n).run env).run st
      st := st'
      let row := s!"{n}\t{mod}\t{String.intercalate "," (sortedNames axs)}"
      if !n.isInternal then axRows := axRows.push row
      if all then allRows := allRows.push row
    if (ownerMod o).isNone then continue
    for u in ci.getUsedConstantsAsSet.toList do
      let u' := publicOwner u
      if u' != o && (inScope u').isSome then usedRows := usedRows.push s!"{o}\t{u'}"
  -- Vacuity anchor: no declaration in the requested modules means the filter matched nothing.
  if axRows.isEmpty then
    IO.eprintln "ProfEnv: no declaration found in the requested modules"
    return 1
  IO.FS.writeFile (outdir ++ "/axioms.tsv")
    ("declaration\tmodule\taxiom_set\n" ++ String.intercalate "\n" (axRows.qsort (· < ·)).toList ++ "\n")
  if all then
    IO.FS.writeFile (outdir ++ "/axioms_all.tsv")
      ("declaration\tmodule\taxiom_set\n" ++ String.intercalate "\n" (allRows.qsort (· < ·)).toList ++ "\n")
  let used := sortUniq usedRows
  IO.FS.writeFile (outdir ++ "/used.tsv")
    ("declaration\tused\n" ++ String.intercalate "\n" used.toList ++ "\n")
  IO.eprintln s!"ProfEnv: {mods.length} modules, {axRows.size} declarations, {imps.size} import edges, {used.size} use edges"
  return 0

end ProfEnv

def main (args : List String) : IO UInt32 := do
  match args with
  | [modlist, scopelist, outdir] => ProfEnv.run modlist scopelist outdir
  | _ => IO.eprintln "usage: ProfEnv.lean MODLIST SCOPELIST OUTDIR"; return 2
