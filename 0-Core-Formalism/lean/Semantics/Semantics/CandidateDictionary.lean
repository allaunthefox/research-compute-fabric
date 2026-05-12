import Semantics.GCCL
import Semantics.LogogramSubstitution

/-!
# Candidate Dictionary Commit Surface

This module formalizes the vectorless, external-store dictionary used by the
logogram sidecar path. The dictionary is a committed token table: sidecar
references may select ranges from it, but promotion still requires GCCL-Rep
verification and replay evidence.

The core stays finite and symbolic. `SidecarOp` remains the finite operation
kind from `LogogramSubstitution`; `CandidateSidecarRef` carries the concrete
range metadata used by a database-backed encoder.
-/

namespace Semantics.CandidateDictionary

open Semantics.GCCL
open Semantics.LogogramSubstitution

/-! ## Dictionary entries -/

/-- A retained canonical token payload in the external dictionary. -/
structure CandidateEntry where
  payloadHash : String
  canonicalPayload : String
  payloadDeclared : Bool
  hashDeclared : Bool
  deriving Repr, DecidableEq

/-- Entry admission is declaration-based; hashing is witnessed by receipts. -/
def candidateEntryDeclared (e : CandidateEntry) : Bool :=
  e.payloadDeclared &&
  e.hashDeclared &&
  e.canonicalPayload != "" &&
  e.payloadHash != ""

/-- A vectorless dictionary is an ordered table, not an embedding index. -/
structure CandidateDict where
  dictId : String
  entries : List CandidateEntry
  deriving Repr, DecidableEq

/-- Every retained entry must declare payload and hash evidence. -/
def candidateDictEntriesDeclared (d : CandidateDict) : Bool :=
  d.entries.all candidateEntryDeclared

/-- Dictionary payload count is the range universe for candidate references. -/
def candidateDictSize (d : CandidateDict) : Nat :=
  d.entries.length

/-! ## Sidecar references -/

/--
A concrete reference to a candidate range. `kind` must be `selectCandidate` for
dictionary replay; the other finite sidecar kinds remain legal elsewhere but
are not dictionary selections.
-/
structure CandidateSidecarRef where
  kind : SidecarOp
  start : Nat
  length : Nat
  deriving Repr, DecidableEq

/-- Range bound used by database, packet, and decompressor adapters. -/
def candidateRangeInBounds (d : CandidateDict) (r : CandidateSidecarRef) : Bool :=
  r.length > 0 && r.start + r.length <= candidateDictSize d

/-- A dictionary selection is legal only for a bounded `selectCandidate` range. -/
def candidateRefAdmissible (d : CandidateDict) (r : CandidateSidecarRef) : Bool :=
  r.kind == SidecarOp.selectCandidate &&
  candidateRangeInBounds d r

/-- Replay a candidate reference as the exact ordered payload range. -/
def replayCandidateRef (d : CandidateDict) (r : CandidateSidecarRef) : Option (List CandidateEntry) :=
  if candidateRefAdmissible d r then
    some ((d.entries.drop r.start).take r.length)
  else
    none

/-! ## Commit and GCCL-Rep bridge -/

/-- Commit witness for the external dictionary state. -/
structure CandidateDictCommit where
  baselineHash : String
  dictHash : String
  receiptHash : String
  entryCount : Nat
  dictionary : CandidateDict
  baselineDeclared : Bool
  dictHashDeclared : Bool
  receiptAttached : Bool
  replayDeclared : Bool
  residualChecked : Bool
  kotAccounted : Bool
  committed : Bool
  deriving Repr

/-- The external dictionary commit is verified before any select reference promotes. -/
def candidateDictCommitVerified (c : CandidateDictCommit) : Bool :=
  c.baselineDeclared &&
  c.dictHashDeclared &&
  c.receiptAttached &&
  c.replayDeclared &&
  c.residualChecked &&
  c.kotAccounted &&
  c.committed &&
  c.baselineHash != "" &&
  c.dictHash != "" &&
  c.receiptHash != "" &&
  c.entryCount == candidateDictSize c.dictionary &&
  candidateDictEntriesDeclared c.dictionary

/-- Candidate dictionary commits project into the existing GCCL-Rep event gate. -/
def toGcclRepEvent (c : CandidateDictCommit) : GcclRepEvent :=
  { baselineDeclared := c.baselineDeclared
    representativeDeclared := c.dictHashDeclared && candidateDictEntriesDeclared c.dictionary
    replayAvailable := c.replayDeclared
    residualChecked := c.residualChecked
    kotAccounted := c.kotAccounted
    receiptAttached := c.receiptAttached
    committed := c.committed }

/-- A dictionary-backed reference promotes only with both dictionary and GCCL gates. -/
def candidateRefPromotable (c : CandidateDictCommit) (t : Transition)
    (r : CandidateSidecarRef) : Bool :=
  candidateDictCommitVerified c &&
  candidateRefAdmissible c.dictionary r &&
  GCCL.repPromotable (toGcclRepEvent c) t

/-! ## Canonical witnesses -/

def gammaEntry : CandidateEntry :=
  { payloadHash := "sha256:gamma"
    canonicalPayload := "Gamma_i"
    payloadDeclared := true
    hashDeclared := true }

def betaEntry : CandidateEntry :=
  { payloadHash := "sha256:beta"
    canonicalPayload := "Beta_j"
    payloadDeclared := true
    hashDeclared := true }

def emptyPayloadEntry : CandidateEntry :=
  { payloadHash := "sha256:empty"
    canonicalPayload := ""
    payloadDeclared := true
    hashDeclared := true }

def exampleDict : CandidateDict :=
  { dictId := "dict.example"
    entries := [gammaEntry, betaEntry] }

def exampleSelectGamma : CandidateSidecarRef :=
  { kind := SidecarOp.selectCandidate
    start := 0
    length := 1 }

def exampleSelectPair : CandidateSidecarRef :=
  { kind := SidecarOp.selectCandidate
    start := 0
    length := 2 }

def outOfBoundsSelect : CandidateSidecarRef :=
  { kind := SidecarOp.selectCandidate
    start := 1
    length := 2 }

def literalNotDictionarySelect : CandidateSidecarRef :=
  { kind := SidecarOp.literalToken
    start := 0
    length := 1 }

def exampleCommit : CandidateDictCommit :=
  { baselineHash := "sha256:baseline"
    dictHash := "sha256:dict"
    receiptHash := "sha256:receipt"
    entryCount := candidateDictSize exampleDict
    dictionary := exampleDict
    baselineDeclared := true
    dictHashDeclared := true
    receiptAttached := true
    replayDeclared := true
    residualChecked := true
    kotAccounted := true
    committed := true }

def badCountCommit : CandidateDictCommit :=
  { exampleCommit with entryCount := 3 }

def badEntryCommit : CandidateDictCommit :=
  { exampleCommit with
    dictionary := { dictId := "dict.bad-entry", entries := [gammaEntry, emptyPayloadEntry] }
    entryCount := 2 }

/-! ## Executable theorems -/

theorem example_entry_declared :
    candidateEntryDeclared gammaEntry = true := by
  native_decide

theorem empty_payload_entry_not_declared :
    candidateEntryDeclared emptyPayloadEntry = false := by
  native_decide

theorem example_dictionary_entries_declared :
    candidateDictEntriesDeclared exampleDict = true := by
  native_decide

theorem select_gamma_replays_single_entry :
    replayCandidateRef exampleDict exampleSelectGamma = some [gammaEntry] := by
  native_decide

theorem select_pair_replays_two_entries :
    replayCandidateRef exampleDict exampleSelectPair = some [gammaEntry, betaEntry] := by
  native_decide

theorem out_of_bounds_select_replays_none :
    replayCandidateRef exampleDict outOfBoundsSelect = none := by
  native_decide

theorem literal_token_is_not_dictionary_select :
    replayCandidateRef exampleDict literalNotDictionarySelect = none := by
  native_decide

theorem example_commit_verified :
    candidateDictCommitVerified exampleCommit = true := by
  native_decide

theorem bad_count_commit_not_verified :
    candidateDictCommitVerified badCountCommit = false := by
  native_decide

theorem bad_entry_commit_not_verified :
    candidateDictCommitVerified badEntryCommit = false := by
  native_decide

/-- A verified dictionary commit always has a verified GCCL-Rep carrier. -/
theorem verified_commit_implies_verified_gccl_rep (c : CandidateDictCommit) :
    candidateDictCommitVerified c = true -> GCCL.repVerified (toGcclRepEvent c) = true := by
  unfold candidateDictCommitVerified GCCL.repVerified toGcclRepEvent
  intro h
  cases hBase : c.baselineDeclared
  · simp [hBase] at h
  cases hDictHash : c.dictHashDeclared
  · simp [hBase, hDictHash] at h
  cases hReceipt : c.receiptAttached
  · simp [hBase, hDictHash, hReceipt] at h
  cases hReplay : c.replayDeclared
  · simp [hBase, hDictHash, hReceipt, hReplay] at h
  cases hResidual : c.residualChecked
  · simp [hBase, hDictHash, hReceipt, hReplay, hResidual] at h
  cases hKot : c.kotAccounted
  · simp [hBase, hDictHash, hReceipt, hReplay, hResidual, hKot] at h
  cases hCommitted : c.committed
  · simp [hBase, hDictHash, hReceipt, hReplay, hResidual, hKot, hCommitted] at h
  cases hEntries : candidateDictEntriesDeclared c.dictionary
  · simp [hEntries] at h
  · rfl

/-- Any replayed candidate range came from an admissible dictionary reference. -/
theorem replay_some_implies_candidate_ref_admissible
    (d : CandidateDict) (r : CandidateSidecarRef) (xs : List CandidateEntry) :
    replayCandidateRef d r = some xs -> candidateRefAdmissible d r = true := by
  unfold replayCandidateRef
  intro h
  cases hRef : candidateRefAdmissible d r
  · simp [hRef] at h
  · simp

/-- Any promotable candidate reference carries a verified dictionary commit. -/
theorem candidate_ref_promotion_implies_commit_verified
    (c : CandidateDictCommit) (t : Transition) (r : CandidateSidecarRef) :
    candidateRefPromotable c t r = true -> candidateDictCommitVerified c = true := by
  unfold candidateRefPromotable
  intro h
  cases hCommit : candidateDictCommitVerified c
  · simp [hCommit] at h
  · simp

/-- Candidate references do not bypass the existing GCCL transition gate. -/
theorem candidate_ref_promotion_implies_lawful_transition
    (c : CandidateDictCommit) (t : Transition) (r : CandidateSidecarRef) :
    candidateRefPromotable c t r = true -> GCCL.lawfulSurfaceAdmissible t = true := by
  unfold candidateRefPromotable GCCL.repPromotable
  intro h
  cases hCommit : candidateDictCommitVerified c
  · simp [hCommit] at h
  cases hRef : candidateRefAdmissible c.dictionary r
  · simp [hCommit, hRef] at h
  cases hRep : GCCL.repVerified (toGcclRepEvent c)
  · simp [hCommit, hRef, hRep] at h
  cases hLaw : GCCL.lawfulSurfaceAdmissible t
  · simp [hCommit, hRef, hRep, hLaw] at h
  · rfl

#eval candidateDictCommitVerified exampleCommit
#eval replayCandidateRef exampleDict exampleSelectGamma
#eval replayCandidateRef exampleDict outOfBoundsSelect
#eval candidateRefPromotable exampleCommit GCCL.lawfulExample exampleSelectGamma

end Semantics.CandidateDictionary
