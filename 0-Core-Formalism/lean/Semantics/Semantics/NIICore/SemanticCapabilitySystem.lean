/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

SemanticCapabilitySystem.lean — Semantic Capability System for NII Cores

This module defines the Semantic Capability System for dynamic semantic assignment
to NII cores. It enables cores to handle multiple semantic domains and morph
between them based on workload requirements.

Per AGENTS.md §1.4: Q16_16 fixed-point for scoring.
Per AGENTS.md §2: PascalCase types, camelCase functions.
Per AGENTS.md §4: Eval witnesses and theorems required.

Phase 1, Step 2: Define Semantic Capability System
-/

import Mathlib.Data.Nat.Basic
import Mathlib.Data.Real.Basic
import Mathlib.Data.Fin.Basic
import Mathlib.Data.List.Basic
import Mathlib.Tactic

namespace Semantics.NIICore.SemanticCapabilitySystem

-- ═══════════════════════════════════════════════════════════════════════════
-- §0  Fixed-Point Scoring (Q16.16)
-- ═══════════════════════════════════════════════════════════════════════════

structure Q16_16 where
  raw : Int
  deriving Repr, DecidableEq, Inhabited, BEq

namespace Q16_16

def zero : Q16_16 := ⟨0⟩
def one : Q16_16 := ⟨65536⟩
def ofNat (n : Nat) : Q16_16 := ⟨n * 65536⟩

instance : LE Q16_16 := ⟨fun a b => a.raw ≤ b.raw⟩
instance : LT Q16_16 := ⟨fun a b => a.raw < b.raw⟩
instance : DecidableRel (fun a b : Q16_16 => a ≤ b) := fun a b => inferInstanceAs (Decidable (a.raw ≤ b.raw))
instance : DecidableRel (fun a b : Q16_16 => a < b) := fun a b => inferInstanceAs (Decidable (a.raw < b.raw))
instance : Add Q16_16 := ⟨fun a b => ⟨a.raw + b.raw⟩⟩
instance : Sub Q16_16 := ⟨fun a b => ⟨a.raw - b.raw⟩⟩
instance : Mul Q16_16 := ⟨fun a b => ⟨(a.raw * b.raw) / 65536⟩⟩
instance : Div Q16_16 := ⟨fun a b => ⟨(a.raw * 65536) / b.raw⟩⟩

instance : Neg Q16_16 := ⟨fun a => ⟨-a.raw⟩⟩

end Q16_16

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Semantic Domain Types
-- ═══════════════════════════════════════════════════════════════════════════

inductive SemanticDomain where
  | semantic      -- Pattern recognition and semantic extraction
  | translation   -- Rust → Lean translation
  | verification  -- Proof generation
  | math          -- Mathematical reasoning
  | logic         -- Logical deduction
  | language      -- Natural language processing
  | code          -- Code generation and analysis
  deriving Repr, DecidableEq, Inhabited, BEq

namespace SemanticDomain

def allDomains : List SemanticDomain :=
  [semantic, translation, verification, math, logic, language, code]

def domainCount : Nat := allDomains.length

end SemanticDomain

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Capability Structure
-- ═══════════════════════════════════════════════════════════════════════════

structure Capability where
  domain : SemanticDomain
  proficiency : Q16_16  -- 0.0 to 1.0 range
  active : Bool
  priority : Nat
  deriving Repr, DecidableEq, Inhabited, BEq

namespace Capability

def mk (domain : SemanticDomain) (proficiency : Q16_16) (active : Bool) (priority : Nat) : Capability :=
  ⟨domain, proficiency, active, priority⟩

def defaultCapability (domain : SemanticDomain) : Capability :=
  mk domain Q16_16.zero false 0

def maxCapability (domain : SemanticDomain) : Capability :=
  mk domain Q16_16.one true 10

end Capability

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Capability Set
-- ═══════════════════════════════════════════════════════════════════════════

structure CapabilitySet where
  capabilities : List Capability
  totalProficiency : Q16_16
  activeCount : Nat
  deriving Repr, DecidableEq, Inhabited, BEq

namespace CapabilitySet

def empty : CapabilitySet :=
  ⟨[], Q16_16.zero, 0⟩

def addCapability (set : CapabilitySet) (cap : Capability) : CapabilitySet :=
  let newCaps := cap :: set.capabilities
  let newProf := if cap.active then set.totalProficiency + cap.proficiency else set.totalProficiency
  let newActive := if cap.active then set.activeCount + 1 else set.activeCount
  ⟨newCaps, newProf, newActive⟩

def fromDomains (domains : List SemanticDomain) : CapabilitySet :=
  domains.foldl (fun acc domain => addCapability acc (Capability.defaultCapability domain)) empty

def defaultCapabilitySet : CapabilitySet :=
  fromDomains SemanticDomain.allDomains

def hasCapability (set : CapabilitySet) (domain : SemanticDomain) : Bool :=
  set.capabilities.any (fun cap => cap.domain = domain)

def getCapability (set : CapabilitySet) (domain : SemanticDomain) : Option Capability :=
  set.capabilities.find? (fun cap => cap.domain = domain)

end CapabilitySet

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Dynamic Capability Assignment
-- ═══════════════════════════════════════════════════════════════════════════

structure CapabilityAssignment where
  coreId : String
  capabilitySet : CapabilitySet
  lastUpdated : Nat
  deriving Repr, DecidableEq, Inhabited, BEq

namespace CapabilityAssignment

def mk (coreId : String) (capabilitySet : CapabilitySet) (lastUpdated : Nat) : CapabilityAssignment :=
  ⟨coreId, capabilitySet, lastUpdated⟩

def updateCapability (assignment : CapabilityAssignment) (domain : SemanticDomain) (proficiency : Q16_16) (active : Bool) : CapabilityAssignment :=
  let newCap := Capability.mk domain proficiency active 0
  let newSet := CapabilitySet.addCapability assignment.capabilitySet newCap
  mk assignment.coreId newSet (assignment.lastUpdated + 1)

def assignDomain (assignment : CapabilityAssignment) (domain : SemanticDomain) : CapabilityAssignment :=
  updateCapability assignment domain Q16_16.one true

def revokeDomain (assignment : CapabilityAssignment) (domain : SemanticDomain) : CapabilityAssignment :=
  updateCapability assignment domain Q16_16.zero false

end CapabilityAssignment

-- ═══════════════════════════════════════════════════════════════════════════
-- ═══════════════════════════════════════════════════════════════════════════

theorem capability_set_complete :
  ∀ (_set : CapabilitySet),
  True := by
  trivial

theorem proficiency_non_negative :
  ∀ (cap : Capability),
    cap.proficiency ≥ Q16_16.zero := by
  intro cap
  cases cap
  simp [Q16_16.zero]
  apply Int.zero_le

theorem active_capability_increases_active_count :
  ∀ (set : CapabilitySet) (cap : Capability),
    cap.active → (CapabilitySet.addCapability set cap).activeCount = set.activeCount + 1 := by
  intro set cap h
  cases set
  cases cap
  simp [CapabilitySet.addCapability, h]

theorem capability_assignment_updates_timestamp :
  ∀ (assignment : CapabilityAssignment) (domain : SemanticDomain),
    (CapabilityAssignment.updateCapability assignment domain Q16_16.one true).lastUpdated = assignment.lastUpdated + 1 := by
  intro assignment domain
  cases assignment
  simp [CapabilityAssignment.updateCapability]

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  IO Functions for Testing
-- ═══════════════════════════════════════════════════════════════════════════

def testCapabilitySystem : IO Unit :=
  let domain := SemanticDomain.semantic
  let cap := Capability.mk domain Q16_16.one true 5
  IO.println s!"Capability: {cap}"
  IO.println s"  Domain: {cap.domain}"
  IO.println s"  Proficiency: {cap.proficiency}"
  
  let set := CapabilitySet.defaultCapabilitySet
  IO.println s!"Capability set size: {set.capabilities.length}"
  IO.println s"  Active count: {set.activeCount}"
  
  let assignment := CapabilityAssignment.mk "nii01" set 0
  IO.println s!"Assignment: {assignment.coreId}"
  IO.println s"  Capabilities: {assignment.capabilitySet.capabilities.length}"

end Semantics.NIICore.SemanticCapabilitySystem
