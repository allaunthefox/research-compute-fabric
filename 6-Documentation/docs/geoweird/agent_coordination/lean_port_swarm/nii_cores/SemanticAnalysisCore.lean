/-
  SemanticAnalysisCore.lean - NII-01 Pattern Recognition
  
  Extracts semantic patterns from Rust source code:
  - Enum variants and discriminants
  - Decoder function structure
  - Memory layout patterns
  - Control flow graphs
-/  

import NIICore

namespace NIICore.SemanticAnalysis

open NIICore

/-- Source code location -/
structure SourceLoc where
  file : String
  lineStart : Nat
  lineEnd : Nat
  deriving Repr, DecidableEq

/-- Extracted enum variant -/
structure EnumVariant where
  name : String
  discriminant : Option UInt8
  payloadType : Option String
  loc : SourceLoc
  deriving Repr, DecidableEq

/-- Complete enum extraction -/
structure EnumExtraction where
  name : String
  variants : List EnumVariant
  totalVariants : Nat
  loc : SourceLoc
  deriving Repr

/-- Decoder match arm pattern -/
structure MatchArm where
  pattern : String
  body : String
  complexity : UInt8  -- Estimated complexity 0-255
  loc : SourceLoc
  deriving Repr

/-- Extracted decoder function -/
structure DecoderExtraction where
  name : String
  signature : String
  matchArms : List MatchArm
  totalArms : Nat
  complexity : UInt8
  loc : SourceLoc
  deriving Repr

/-- Memory layout field -/
structure LayoutField where
  name : String
  offset : Nat
  size : Nat
  alignment : Nat
  deriving Repr

/-- Complete memory layout -/
structure MemoryLayout where
  totalSize : Nat
  alignment : Nat
  fields : List LayoutField
  deriving Repr

/-- Semantic extraction result from Rust source -/
structure ExtractionResult where
  enums : List EnumExtraction
  decoders : List DecoderExtraction
  layouts : List MemoryLayout
  sourceFile : String
  extractionTime : UInt32  -- ms
  deriving Repr

/-- Pattern recognition function type -/
def PatternRecognizer := String → Option ExtractionResult

/-- Count total variants across all enums -/
def totalVariantCount (result : ExtractionResult) : Nat :=
  result.enums.foldl (λ acc e => acc + e.totalVariants) 0

/-- Calculate average decoder complexity -/
def averageDecoderComplexity (result : ExtractionResult) : UInt8 :=
  if result.decoders.isEmpty then 0
  else
    let total := result.decoders.foldl (λ acc d => acc + d.complexity.toNat) 0
    (total / result.decoders.length).toUInt8

/-
  Example witnesses
-/

def exampleVariant : EnumVariant := {
  name := "Push",
  discriminant := some 0,
  payloadType := some "UInt64",
  loc := {
    file := "bytecode.rs",
    lineStart := 25,
    lineEnd := 27
  }
}

def exampleEnum : EnumExtraction := {
  name := "Opcode",
  variants := [exampleVariant],
  totalVariants := 1,
  loc := {
    file := "bytecode.rs",
    lineStart := 20,
    lineEnd := 30
  }
}

def exampleMatchArm : MatchArm := {
  pattern := "0x01 =>",
  body := "Some((Opcode::Push(val), 9))",
  complexity := 10,
  loc := {
    file := "bytecode.rs",
    lineStart := 45,
    lineEnd := 47
  }
}

def exampleDecoder : DecoderExtraction := {
  name := "decode_opcode",
  signature := "fn(&[u8]) -> Option<(Opcode, usize)>",
  matchArms := [exampleMatchArm],
  totalArms := 1,
  complexity := 10,
  loc := {
    file := "bytecode.rs",
    lineStart := 40,
    lineEnd := 50
  }
}

def exampleExtraction : ExtractionResult := {
  enums := [exampleEnum],
  decoders := [exampleDecoder],
  layouts := [],
  sourceFile := "bytecode.rs",
  extractionTime := 150
}

#eval exampleVariant
#eval exampleEnum
#eval totalVariantCount exampleExtraction
#eval averageDecoderComplexity exampleExtraction

/-
  Theorems
-/

/-- Total variant count is sum of all enum variant counts -/
theorem totalVariantCountCorrect (r : ExtractionResult) :
    totalVariantCount r = (r.enums.map (·.totalVariants)).sum := by
  simp [totalVariantCount, List.foldl]

/-- Empty extraction has zero variants -/
theorem emptyExtractionZeroVariants :
    totalVariantCount { exampleExtraction with enums := [] } = 0 := by
  simp [totalVariantCount]

end NIICore.SemanticAnalysis
