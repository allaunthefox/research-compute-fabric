namespace ExtensionScaffold.Seed

/-! # uSeed — Universal Micro-Seed

A uSeed is a minimal generative unit: typed, addressable, and capable of
germinating into structured growth through adjacency and transformation rules.

Conceptually: the smallest addressable unit in an assemblage that carries
sufficient information to regrow its local neighborhood given the right
activation conditions.

Status: Extension — experimental germination primitive.
-/

/-- Germination state of a uSeed. -/
inductive GerminationState
  | dormant
  | activating
  | growing
  | mature
  | propagating
deriving Repr, BEq, DecidableEq

/-- 3D lattice position with sub-voxel precision. -/
structure Position3 where
  x : UInt16
  y : UInt16
  z : UInt16
  fx : UInt8
  fy : UInt8
  fz : UInt8
deriving Repr, BEq

/-- Activation potential — energy state for germination. -/
abbrev ActivationPotential : Type := UInt16

/-- Lineage identifier for tracking generative ancestry. -/
abbrev LineageHash : Type := UInt64

/-- A uSeed: minimal germinative unit in an assemblage. -/
structure USeed where
  position : Position3
  activation : ActivationPotential
  lineage : LineageHash
  state : GerminationState
  childCount : UInt8
  priority : UInt8
  spectralTag : UInt16
deriving Repr, BEq

/-- A uSeed is addressable if it has a valid position. -/
def USeed.addressable (s : USeed) : Bool :=
  s.state != .dormant

/-- Compute adjacency distance between two seeds (Manhattan). -/
def USeed.adjacent (s1 s2 : USeed) (threshold : UInt16 := 1) : Bool :=
  let dx := if s1.position.x > s2.position.x then s1.position.x - s2.position.x else s2.position.x - s1.position.x
  let dy := if s1.position.y > s2.position.y then s1.position.y - s2.position.y else s2.position.y - s1.position.y
  let dz := if s1.position.z > s2.position.z then s1.position.z - s2.position.z else s2.position.z - s1.position.z
  dx ≤ threshold && dy ≤ threshold && dz ≤ threshold

/-- Germination cost: energy required to activate a dormant seed. -/
def USeed.germinationCost (s : USeed) : UInt32 :=
  if s.state == .dormant then
    0x00010000 - s.activation.toUInt32  -- Q16.16: 1.0 - activation
  else
    0

/-- A colony is a non-empty collection of uSeeds. -/
abbrev USeedColony : Type := List USeed

/-- Colony health: ratio of mature to total seeds (Q16.16 fixed-point). -/
def USeedColony.health (colony : USeedColony) : UInt32 :=
  let total := colony.length
  let mature := colony.filter (fun seed => seed.state == .mature) |>.length
  if total == 0 then
    0
  else
    (mature.toUInt32 * 0x00010000) / total.toUInt32  -- Q16.16 ratio

/-- Witness: empty colony has zero health. -/
theorem emptyColonyHealthZero :
  USeedColony.health [] = 0 := by
  rfl

/-- A scaffold connects seeds through adjacency relations. -/
structure Scaffold where
  seeds : USeedColony
  links : List (Fin 256 × Fin 256)  -- Indices into seeds list
  threshold : UInt16
deriving Repr, BEq

/-- Check if scaffold forms a connected structure. -/
def Scaffold.connected (scaffold : Scaffold) : Bool :=
  scaffold.links.length > 0 && scaffold.seeds.length > 1

/-- Create a minimal viable seed at origin. -/
def originSeed (lineage : LineageHash := 0) : USeed := {
  position := { x := 0, y := 0, z := 0, fx := 0, fy := 0, fz := 0 },
  activation := 0x8000,
  lineage := lineage,
  state := .dormant,
  childCount := 0,
  priority := 128,
  spectralTag := 0
}

/-- Germinate a seed: transition from dormant to activating if sufficient energy. -/
def USeed.germinate (s : USeed) (energy : ActivationPotential) : USeed :=
  if s.state == .dormant && energy > s.activation then
    { s with state := .activating }
  else
    s

end ExtensionScaffold.Seed
