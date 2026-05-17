import Semantics.Omindirection

/-!
# Symbology Borrowing Gate

This module formalizes the safe quarry rule for dense symbolic systems:
borrow compression principles and visual grammar, not protected glyph identity.

A symbology-derived logogram is lawful only when it is reissued as an original
Omindirection atom with explicit payload identity, orientation, placement,
residual policy, and receipt evidence.
-/

namespace Semantics.SymbologyBorrowing

/-! ## Source classes and borrowable principles -/

/-- Dense notation families that can inspire logogram design. -/
inductive SourceClass where
  | arrayLanguage
  | codeGolfLanguage
  | mathNotation
  | shorthandSystem
  | logographicSystem
  | syllabaryOrFeaturalScript
  | ancientScript
  | constructedScript
  | specialistSymbolSystem
  deriving DecidableEq, Repr

/-- What may be borrowed: structural compression principles, not literal identity. -/
inductive BorrowedPrinciple where
  | denseOperator
  | modifierFamily
  | customCodePage
  | residualOmission
  | radicalComposition
  | syllablePacket
  | semanticDeterminative
  | phaseChiralityGrammar
  | domainNotation
  deriving DecidableEq, Repr

/-- One proposed symbology-derived atom, before or after promotion. -/
structure BorrowReceipt where
  sourceClass : SourceClass
  principle : BorrowedPrinciple
  originalAtomDeclared : Bool
  protectedGlyphCopied : Bool
  payloadHashDeclared : Bool
  directionDeclared : Bool
  chiralityPhaseDeclared : Bool
  placementDeclared : Bool
  residualPolicyDeclared : Bool
  receiptHashDeclared : Bool
  byteSavingsWitnessed : Bool
  deriving Repr

/-- The extraction is lawful only after reissuing the idea as an original atom. -/
def borrowedSymbologyLawful (r : BorrowReceipt) : Bool :=
  r.originalAtomDeclared &&
  !r.protectedGlyphCopied &&
  r.payloadHashDeclared &&
  r.directionDeclared &&
  r.chiralityPhaseDeclared &&
  r.placementDeclared &&
  r.residualPolicyDeclared &&
  r.receiptHashDeclared

/-- Promotion to compression use additionally needs a byte-savings witness. -/
def borrowedSymbologyPromotable (r : BorrowReceipt) : Bool :=
  borrowedSymbologyLawful r &&
  r.byteSavingsWitnessed

/-! ## Byte law -/

/--
The logogram is useful only when the total route cost is lower than baseline.
This is an accounting predicate, not a benchmark claim.
-/
def byteLawHolds
    (atomBytes dictionaryBytes thresholdBytes residualBytes receiptBytes baselineBytes : Nat) : Bool :=
  atomBytes + dictionaryBytes + thresholdBytes + residualBytes + receiptBytes < baselineBytes

/-! ## Canonical examples -/

def aplOperatorBorrow : BorrowReceipt :=
  { sourceClass := SourceClass.arrayLanguage
    principle := BorrowedPrinciple.denseOperator
    originalAtomDeclared := true
    protectedGlyphCopied := false
    payloadHashDeclared := true
    directionDeclared := true
    chiralityPhaseDeclared := true
    placementDeclared := true
    residualPolicyDeclared := true
    receiptHashDeclared := true
    byteSavingsWitnessed := true }

def copiedFictionalGlyph : BorrowReceipt :=
  { aplOperatorBorrow with
    sourceClass := SourceClass.constructedScript
    principle := BorrowedPrinciple.phaseChiralityGrammar
    protectedGlyphCopied := true }

def aestheticOverheadBorrow : BorrowReceipt :=
  { aplOperatorBorrow with
    byteSavingsWitnessed := false }

/-! ## Executable witnesses -/

theorem apl_operator_borrow_lawful :
    borrowedSymbologyLawful aplOperatorBorrow = true := by
  native_decide

theorem copied_glyph_is_not_lawful :
    borrowedSymbologyLawful copiedFictionalGlyph = false := by
  native_decide

theorem aesthetic_overhead_not_promotable :
    borrowedSymbologyPromotable aestheticOverheadBorrow = false := by
  native_decide

theorem copied_glyph_not_promotable :
    borrowedSymbologyPromotable copiedFictionalGlyph = false := by
  native_decide

theorem compact_route_beats_baseline :
    byteLawHolds 1 2 1 3 1 16 = true := by
  native_decide

theorem aesthetic_route_fails_byte_law :
    byteLawHolds 4 8 2 6 4 16 = false := by
  native_decide

/-- Any promotable borrow has already passed the lawful atomization gate. -/
theorem promotable_borrow_is_lawful (r : BorrowReceipt) :
    borrowedSymbologyPromotable r = true -> borrowedSymbologyLawful r = true := by
  unfold borrowedSymbologyPromotable
  intro h
  cases hLaw : borrowedSymbologyLawful r
  · simp [hLaw] at h
  · simp

/-- Literal protected glyph copying can never satisfy the borrowing law. -/
theorem copied_glyph_blocks_lawful_borrow (r : BorrowReceipt) :
    r.protectedGlyphCopied = true -> borrowedSymbologyLawful r = false := by
  intro hCopy
  unfold borrowedSymbologyLawful
  simp [hCopy]

#eval borrowedSymbologyLawful aplOperatorBorrow
#eval borrowedSymbologyLawful copiedFictionalGlyph
#eval borrowedSymbologyPromotable aestheticOverheadBorrow
#eval byteLawHolds 1 2 1 3 1 16

end Semantics.SymbologyBorrowing
