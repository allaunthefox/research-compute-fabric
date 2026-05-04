import Semantics.GenomicCompression
import Mathlib.Data.Fin.Basic
import Mathlib.Data.Nat.Basic

namespace Semantics.ASCIIGen

/-- ASCII art entry in the database -/
structure ASCIIArtEntry where
  id : String  -- Unique identifier
  name : String  -- Human-readable name
  art : String  -- ASCII art content
  width : Nat
  height : Nat
  kotCost : UInt32  -- Cost in KOT tokens
  category : String  -- Category (e.g., "animals", "fractals", "text")
  encodingHash : String  -- Hash for uniqueness verification
  deriving Repr

/-- Public domain ASCII art database -/
def asciiArtDatabase : List ASCIIArtEntry :=
  [
    {
      id := "ascii-001",
      name := "Simple Smile",
      art := "  /\\\n /  \\\n/ () \\\n \\  /\n  \\/",
      width := 6,
      height := 5,
      kotCost := 100,
      category := "faces",
      encodingHash := "a1b2c3d4"
    },
    {
      id := "ascii-002",
      name := "Heart",
      art := "  __  __\n /  \\/  \\\n|        |\n \\      /\n  \\____/",
      width := 10,
      height := 5,
      kotCost := 150,
      category := "shapes",
      encodingHash := "e5f6g7h8"
    },
    {
      id := "ascii-003",
      name := "Star",
      art := "    /\\\n   /  \\\n  /    \\\n /      \\\n/        \\\n\\        /\n \\      /\n  \\    /\n   \\  /\n    \\/",
      width := 10,
      height := 10,
      kotCost := 200,
      category := "shapes",
      encodingHash := "i9j0k1l2"
    },
    {
      id := "ascii-004",
      name := "Cat",
      art := "  /\\_/\\\n ( o.o )\n  > ^ <",
      width := 9,
      height := 3,
      kotCost := 250,
      category := "animals",
      encodingHash := "m3n4o5p6"
    },
    {
      id := "ascii-005",
      name := "Tree",
      art := "    /\\\n   /  \\\n  /    \\\n /      \\\n/________\\\n    ||",
      width := 10,
      height := 6,
      kotCost := 180,
      category := "nature",
      encodingHash := "q7r8s9t0"
    },
    {
      id := "ascii-006",
      name := "Diamond",
      art := "    /\\\n   /  \\\n  /    \\\n  \\    /\n   \\  /\n    \\/",
      width := 8,
      height := 6,
      kotCost := 120,
      category := "shapes",
      encodingHash := "u1v2w3x4"
    },
    {
      id := "ascii-007",
      name := "Fish",
      art := "  /\\\n <  <\n  \\/",
      width := 6,
      height := 3,
      kotCost := 130,
      category := "animals",
      encodingHash := "y5z6a7b8"
    },
    {
      id := "ascii-008",
      name := "House",
      art := "   /\\\n  /  \\\n /    \\\n/______\\\n|      |\n|______|",
      width := 8,
      height := 6,
      kotCost := 160,
      category := "buildings",
      encodingHash := "c9d0e1f2"
    },
    {
      id := "ascii-009",
      name := "Sierpinski Triangle (Small)",
      art := "   /\\\n  /__\\\n /\\  /\\\n/__\\/__\\",
      width := 8,
      height := 4,
      kotCost := 300,
      category := "fractals",
      encodingHash := "g3h4i5j6"
    },
    {
      id := "ascii-010",
      name := "Spiral",
      art := "*****\n*   *\n* * *\n* * *\n*****",
      width := 5,
      height := 5,
      kotCost := 140,
      category := "patterns",
      encodingHash := "k7l8m9n0"
    }
  ]

/-- Lookup ASCII art by ID -/
def lookupASCIIArt (id : String) : Option ASCIIArtEntry :=
  asciiArtDatabase.find? (fun entry => entry.id = id)

/-- Lookup ASCII art by category -/
def lookupASCIIArtByCategory (category : String) : List ASCIIArtEntry :=
  asciiArtDatabase.filter (fun entry => entry.category = category)

/-- Get all available categories -/
def getASCIICategories : List String :=
  asciiArtDatabase.map (fun entry => entry.category) |>.eraseDups

/-- Purchase ASCII art with KOT (returns entry if sufficient KOT) -/
def purchaseASCIIArt (agentKOT : UInt32) (id : String) : Option (ASCIIArtEntry × UInt32) :=
  match lookupASCIIArt id with
  | none => none
  | some entry =>
    if agentKOT ≥ entry.kotCost then
      some (entry, agentKOT - entry.kotCost)
    else
      none

/-- ASCII art encoding analysis: accumulate data about ASCII patterns -/
structure ASCIIEncodingData where
  charFrequency : HashMap Char UInt32  -- Frequency of each character
  lineLengths : List Nat  -- Length of each line
  density : Q16_16  -- Overall density (non-space characters / total characters)
  deriving Repr

/-- Analyze ASCII art encoding patterns -/
def analyzeASCIIEncoding (entry : ASCIIArtEntry) : ASCIIEncodingData :=
  let lines := entry.art.splitOn "\n"
  let charFreq := lines.foldl (fun acc line =>
    line.foldl (fun innerAcc c =>
      let current := innerAcc.find! c
      innerAcc.insert c (current + 1)
    ) acc
  ) HashMap.empty
  let lineLens := lines.map (fun line => line.length)
  let totalChars := lines.foldl (fun acc line => acc + line.length) 0
  let nonSpaceChars := lines.foldl (fun acc line =>
    line.foldl (fun inner c => if c = ' ' then inner else inner + 1) 0
  ) 0
  let density := if totalChars = 0 then 0x000000 else
    (nonSpaceChars.toQ16_16 * 0x010000) / totalChars.toQ16_16
  {
    charFrequency := charFreq,
    lineLengths := lineLens,
    density := density
  }

/-- Accumulate encoding data across multiple ASCII art purchases -/
structure ASCIIDataAccumulator where
  totalPurchases : UInt32
  accumulatedEncoding : List ASCIIEncodingData
  uniqueChars : HashSet Char
  deriving Repr

/-- Empty accumulator -/
def emptyASCIIDataAccumulator : ASCIIDataAccumulator :=
  {
    totalPurchases := 0,
    accumulatedEncoding := [],
    uniqueChars := HashSet.empty
  }

/-- Update accumulator with new ASCII art purchase -/
def updateASCIIDataAccumulator (acc : ASCIIDataAccumulator) (entry : ASCIIArtEntry) : ASCIIDataAccumulator :=
  let encoding := analyzeASCIIEncoding entry
  let newUniqueChars := acc.uniqueChars ∪ encoding.charFrequency.toList.map (fun p => p.1) |>.toHashSet
  {
    totalPurchases := acc.totalPurchases + 1,
    accumulatedEncoding := encoding :: acc.accumulatedEncoding,
    uniqueChars := newUniqueChars
  }

end Semantics.ASCIIGen
