/-!
# Logogram Substitution Gate

This module is the Lean law surface for math/logogram substitution receipts.
Python shims may generate audit JSON, but admission decisions reduce to these
finite gates: payload bound, token-stream completeness, inverse uniqueness,
residual declaration, and quarantine routing.
-/

namespace Semantics.LogogramSubstitution

/-! ## Finite substitution facts -/

/-- Token classes observed by the current math logogram surface. -/
inductive TokenClass where
  | knownCommand
  | knownSymbol
  | singleCharLiteral
  | hashedMulticharResidual
  deriving DecidableEq, Repr

/-- Receipt decision for a substitution test fixture. -/
inductive SubstitutionDecision where
  | accept
  | hold
  | quarantine
  deriving DecidableEq, Repr

/-- Structured sidecar operations used to rehydrate non-payload-only atoms. -/
inductive SidecarOp where
  | selectCandidate
  | literalToken
  | appendTruncatedCell
  deriving DecidableEq, Repr

/-- A bounded substitution receipt, independent of any renderer or shim. -/
structure SubstitutionReceipt where
  tokenCount : Nat
  payloadLen : Nat
  payloadBound : Bool
  tokenStreamComplete : Bool
  payloadOnlyInjective : Bool
  residualDeclared : Bool
  semanticTear : Bool
  compressionRatioDeclared : Bool
  roundTripDeclared : Bool
  deriving Repr

/-- Multi-character hash substitutions are residual-bearing by construction. -/
def tokenClassNeedsResidual (c : TokenClass) : Bool :=
  c == TokenClass.hashedMulticharResidual

/-- Every sidecar operation is a recovery operation, never an ordinary accept proof. -/
def sidecarOpDeclaresResidual (_op : SidecarOp) : Bool :=
  true

/-- The GCCL-shaped receipt minimum for substitution tests. -/
def gcclReceiptShapeComplete (r : SubstitutionReceipt) : Bool :=
  r.compressionRatioDeclared &&
  r.roundTripDeclared &&
  (r.residualDeclared || r.payloadOnlyInjective)

/-- Payload-only round trip is stricter than sidecar-assisted round trip. -/
def payloadOnlyRoundTrip (r : SubstitutionReceipt) : Bool :=
  r.payloadBound &&
  r.tokenStreamComplete &&
  r.payloadOnlyInjective &&
  r.roundTripDeclared

/-- Sidecar-assisted round trip still requires complete token coverage. -/
def sidecarRoundTrip (r : SubstitutionReceipt) : Bool :=
  r.payloadBound &&
  r.tokenStreamComplete &&
  r.roundTripDeclared

/-- A substitution receipt is accepted only when glyph bytes are enough. -/
def substitutionAccepted (r : SubstitutionReceipt) : Bool :=
  payloadOnlyRoundTrip r &&
  gcclReceiptShapeComplete r &&
  !r.semanticTear

/-- HOLD means the compiler detected a recoverable residual. -/
def substitutionHeld (r : SubstitutionReceipt) : Bool :=
  !r.semanticTear &&
  r.payloadBound &&
  r.residualDeclared &&
  gcclReceiptShapeComplete r &&
  !substitutionAccepted r

/-- Semantic tears are routed out of the ordinary tokenbook lane. -/
def substitutionQuarantined (r : SubstitutionReceipt) : Bool :=
  r.semanticTear &&
  r.residualDeclared &&
  gcclReceiptShapeComplete r

/-- Deterministic decision order for a substitution fixture. -/
def decideSubstitution (r : SubstitutionReceipt) : SubstitutionDecision :=
  if substitutionAccepted r then
    SubstitutionDecision.accept
  else if substitutionQuarantined r then
    SubstitutionDecision.quarantine
  else
    SubstitutionDecision.hold

/-! ## Executable witnesses matching the shim audit classes -/

def literalAtomReceipt : SubstitutionReceipt :=
  { tokenCount := 1
    payloadLen := 1
    payloadBound := true
    tokenStreamComplete := true
    payloadOnlyInjective := true
    residualDeclared := false
    semanticTear := false
    compressionRatioDeclared := true
    roundTripDeclared := true }

def knownCommandSidecarReceipt : SubstitutionReceipt :=
  { literalAtomReceipt with
    tokenCount := 7
    payloadLen := 7
    payloadOnlyInjective := false
    residualDeclared := true }

def hashedIdentifierReceipt : SubstitutionReceipt :=
  { literalAtomReceipt with
    tokenCount := 3
    payloadLen := 3
    payloadOnlyInjective := false
    residualDeclared := true }

def truncatedPayloadReceipt : SubstitutionReceipt :=
  { literalAtomReceipt with
    tokenCount := 22
    payloadLen := 16
    tokenStreamComplete := false
    payloadOnlyInjective := false
    residualDeclared := true }

def semanticTearReceipt : SubstitutionReceipt :=
  { literalAtomReceipt with
    tokenCount := 12
    payloadLen := 12
    payloadOnlyInjective := false
    residualDeclared := true
    semanticTear := true }

theorem hashed_multichar_requires_residual :
    tokenClassNeedsResidual TokenClass.hashedMulticharResidual = true := by
  native_decide

theorem sidecar_ops_declare_residual :
    sidecarOpDeclaresResidual SidecarOp.selectCandidate = true ∧
    sidecarOpDeclaresResidual SidecarOp.literalToken = true ∧
    sidecarOpDeclaresResidual SidecarOp.appendTruncatedCell = true := by
  native_decide

theorem literal_atom_is_payload_only_accepted :
    decideSubstitution literalAtomReceipt = SubstitutionDecision.accept := by
  native_decide

theorem known_command_collision_is_held :
    decideSubstitution knownCommandSidecarReceipt = SubstitutionDecision.hold := by
  native_decide

theorem hashed_identifier_is_held :
    decideSubstitution hashedIdentifierReceipt = SubstitutionDecision.hold := by
  native_decide

theorem truncated_payload_is_held :
    decideSubstitution truncatedPayloadReceipt = SubstitutionDecision.hold := by
  native_decide

theorem semantic_tear_is_quarantined :
    decideSubstitution semanticTearReceipt = SubstitutionDecision.quarantine := by
  native_decide

/-- Every accepted substitution has a payload-only round trip witness. -/
theorem accepted_substitution_has_payload_round_trip (r : SubstitutionReceipt) :
    substitutionAccepted r = true -> payloadOnlyRoundTrip r = true := by
  unfold substitutionAccepted
  intro h
  cases hRound : payloadOnlyRoundTrip r
  · simp [hRound] at h
  · simp

#eval decideSubstitution literalAtomReceipt
#eval decideSubstitution knownCommandSidecarReceipt
#eval decideSubstitution hashedIdentifierReceipt
#eval decideSubstitution truncatedPayloadReceipt
#eval decideSubstitution semanticTearReceipt

end Semantics.LogogramSubstitution
