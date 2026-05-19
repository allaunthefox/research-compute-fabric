import Std

open Std

namespace Semantics
namespace SemanticLinter

/-- Severity for semantic lint findings. -/
inductive Severity where
  | info
  | warning
  | error
  deriving Repr, BEq, DecidableEq

/-- A structured semantic lint finding. -/
structure Finding where
  ruleId : String
  severity : Severity
  message : String
  evidence : List String := []
  deriving Repr, BEq

/-- Simple claim profile inferred from text/code artifacts. -/
structure ClaimProfile where
  mentionsVerified : Bool := false
  mentionsCompliant : Bool := false
  mentionsProof : Bool := false
  mentionsAttestation : Bool := false
  mentionsHeuristic : Bool := false
  deriving Repr, BEq

/-- Lightweight implementation profile inferred from code artifacts. -/
structure ImplProfile where
  hasConsistentPrevHashSemantics : Bool := false
  hasExplicitConformanceCheck : Bool := false
  hasPureMerkleRoot : Bool := false
  hasCanonicalDigestSerialization : Bool := false
  preMarksVerified : Bool := false
  usesEmptyCryptoFallback : Bool := false
  heuristicClearlyLabeled : Bool := false
  runtimeDepsAtModuleScope : Bool := false
  deriving Repr, BEq

/-- General semantic rule interface. -/
structure Rule where
  id : String
  description : String
  run : ClaimProfile → ImplProfile → List Finding

private def containsAny (s : String) (needles : List String) : Bool :=
  needles.any (fun n => s.contains n)

/-- Crude text scan for rhetoric/claims. Useful as a baseline over generated code or docs. -/
def inferClaims (text : String) : ClaimProfile :=
  let lower := text.toLower
  {
    mentionsVerified := containsAny lower ["verified", "integrity", "attested", "verification_status"]
    mentionsCompliant := containsAny lower ["compliant", "spec compliant", "vdp-compliant", "per spec"]
    mentionsProof := containsAny lower ["proof", "theorem", "guarantee", "proves"]
    mentionsAttestation := containsAny lower ["attestation", "merkle", "manifest", "provenance"]
    mentionsHeuristic := containsAny lower ["heuristic", "approximation", "simplified", "rough approximation"]
  }

/-- Minimal implementation-profile extractor from source text.
This is intentionally conservative and string-based so it can lint generated code
from many languages before deeper parsers are added. -/
def inferImpl (text : String) : ImplProfile :=
  let lower := text.toLower
  let hasPrevOutput := lower.contains "expected_prev = self.manifests[i-1].output_digest"
  let hasPrevState := lower.contains "prev_manifest_hash=self.current_state_hash"
  let hasPrevDigest := lower.contains "if current_manifest.prev_manifest_hash != expected_prev"
    && lower.contains "self.compute_digest({"
  let mutatesMerkleInput := lower.contains "leaves.append(leaves[-1])"
  let usesStrFallback := lower.contains "canonical = str(data)"
  let preMarksVerified := lower.contains "verification_status=\"verified\""
  let usesEmptyCryptoFallback := lower.contains "record.get(\"content_hash\", \"\")"
  let mathImportedOnlyInMain := lower.contains "def main():" && lower.contains "import math"
  let heuristicClearlyLabeled := containsAny lower ["heuristic", "simplified implementation", "rough approximation"]
  {
    hasConsistentPrevHashSemantics := !(hasPrevOutput && hasPrevState) && !(hasPrevOutput && hasPrevDigest) && !(hasPrevState && hasPrevDigest)
    hasExplicitConformanceCheck := containsAny lower ["conformance", "spec_version", "validate_spec", "schema check"]
    hasPureMerkleRoot := !mutatesMerkleInput
    hasCanonicalDigestSerialization := !usesStrFallback
    preMarksVerified := preMarksVerified
    usesEmptyCryptoFallback := usesEmptyCryptoFallback
    heuristicClearlyLabeled := heuristicClearlyLabeled
    runtimeDepsAtModuleScope := !mathImportedOnlyInMain
  }

/-- SEM001: do not mix predecessor semantics. -/
def rulePrevHashConsistency : Rule := {
  id := "SEM001"
  description := "Predecessor semantics must use one notion of previous hash.",
  run := fun _ impl =>
    if impl.hasConsistentPrevHashSemantics then [] else
      [{ ruleId := "SEM001", severity := .error,
         message := "Inconsistent provenance predecessor semantics.",
         evidence := ["mixed previous-output / previous-state / previous-manifest notions detected"] }]
}

/-- SEM002: do not overclaim verification. -/
def ruleVerificationOverclaim : Rule := {
  id := "SEM002"
  description := "Verification language must not exceed implemented verification.",
  run := fun claims impl =>
    if (claims.mentionsVerified || claims.mentionsAttestation) && impl.preMarksVerified && !impl.hasConsistentPrevHashSemantics then
      [{ ruleId := "SEM002", severity := .error,
         message := "Verification claim exceeds implemented verification semantics.",
         evidence := ["artifact is pre-marked verified while chain semantics appear inconsistent"] }]
    else []
}

/-- SEM004: Merkle/root helpers should be pure over inputs. -/
def ruleMerklePurity : Rule := {
  id := "SEM004"
  description := "Attestation root computation should not mutate source state.",
  run := fun _ impl =>
    if impl.hasPureMerkleRoot then [] else
      [{ ruleId := "SEM004", severity := .error,
         message := "Merkle/root computation mutates caller-owned input state.",
         evidence := ["detected append-on-input pattern in root computation"] }]
}

/-- SEM005: empty sentinels must not enter crypto-critical paths. -/
def ruleCryptoFallback : Rule := {
  id := "SEM005"
  description := "Cryptographic fallbacks should compute digests, not use empty sentinels.",
  run := fun _ impl =>
    if impl.usesEmptyCryptoFallback then
      [{ ruleId := "SEM005", severity := .error,
         message := "Cryptographic fallback uses empty sentinel instead of computed digest.",
         evidence := ["found empty-string fallback in attestation-critical path"] }]
    else []
}

/-- SEM006: compliance claims need explicit conformance checks. -/
def ruleComplianceEvidence : Rule := {
  id := "SEM006"
  description := "Compliance claims should be backed by explicit conformance checks.",
  run := fun claims impl =>
    if claims.mentionsCompliant && !impl.hasExplicitConformanceCheck then
      [{ ruleId := "SEM006", severity := .warning,
         message := "Compliance claim lacks explicit conformance check.",
         evidence := ["spec/compliance language present without machine-checkable validation"] }]
    else []
}

/-- SEM008: heuristic metrics should be labeled as heuristic. -/
def ruleHeuristicLabeling : Rule := {
  id := "SEM008"
  description := "Heuristic metrics should be clearly labeled as heuristic.",
  run := fun claims impl =>
    if !impl.heuristicClearlyLabeled && (claims.mentionsProof || claims.mentionsVerified) then
      [{ ruleId := "SEM008", severity := .warning,
         message := "Heuristic metric is framed too close to a formal measure.",
         evidence := ["formal/verification rhetoric present without clear heuristic labeling"] }]
    else []
}

/-- SEM009: core methods should not depend on imports hidden in main/entrypoint. -/
def ruleEntrypointDeps : Rule := {
  id := "SEM009"
  description := "Runtime dependencies for core methods should live at module scope.",
  run := fun _ impl =>
    if impl.runtimeDepsAtModuleScope then [] else
      [{ ruleId := "SEM009", severity := .error,
         message := "Core method depends on import only available in entrypoint.",
         evidence := ["detected likely runtime dependency hidden in main()"] }]
}

/-- SEM010: provenance hashing should use canonical serialization. -/
def ruleCanonicalDigest : Rule := {
  id := "SEM010"
  description := "Provenance digest paths should use canonical serialization.",
  run := fun _ impl =>
    if impl.hasCanonicalDigestSerialization then [] else
      [{ ruleId := "SEM010", severity := .error,
         message := "Non-canonical serialization detected in provenance digest path.",
         evidence := ["string fallback found for digest computation"] }]
}

/-- Default rule pack for generated-code semantic checks. -/
def defaultRules : List Rule :=
  [ rulePrevHashConsistency
  , ruleVerificationOverclaim
  , ruleMerklePurity
  , ruleCryptoFallback
  , ruleComplianceEvidence
  , ruleHeuristicLabeling
  , ruleEntrypointDeps
  , ruleCanonicalDigest
  ]

/-- Run the semantic linter over raw source text. -/
def lintText (text : String) (rules : List Rule := defaultRules) : List Finding :=
  let claims := inferClaims text
  let impl := inferImpl text
  rules.flatMap (fun r => r.run claims impl)

/-- Pretty printer for findings. -/
def renderFinding (f : Finding) : String :=
  let sev := match f.severity with
    | .info => "INFO"
    | .warning => "WARN"
    | .error => "FAIL"
  let ev := if f.evidence.isEmpty then "" else s!"\n  evidence: {String.intercalate "; " f.evidence}"
  s!"{sev} {f.ruleId} {f.message}{ev}"

/-- Example invocation helper for REPL/manual use. -/
def renderReport (text : String) : String :=
  let findings := lintText text
  if findings.isEmpty then
    "PASS semantic lint"
  else
    String.intercalate "\n" (findings.map renderFinding)

end SemanticLinter
end Semantics
