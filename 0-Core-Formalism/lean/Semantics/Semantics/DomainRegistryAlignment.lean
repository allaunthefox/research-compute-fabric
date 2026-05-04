/- DOMAIN REGISTRY ALIGNMENT — Research Stack ↔ MOIM
   ═══════════════════════════════════════════════════════════════════════════════
   Aligns Research Stack's equation domains with MOIM's 16 domain registries
   for unified classification and cross-referencing.

   MOIM's 16 Domain Registries:
     1. Mathematics (12 subdomains)
     2. Physics  
     3. Chemistry
     4. Biology
     5. Medicine
     6. Neuroscience
     7. Psychology
     8. Anthropology
     9. Political Science
     10. Social Systems
     11. Engineering
     12. Materials Science
     13. Computer Science
     14. Earth / Cosmology
     15. Music / Acoustics
     16. Uncategorized

   Research Stack Domain Types (from MATH_MODEL_MAP.tsv):
     - LAYER_C_TOPOLOGY (geometric topology)
     - LAYER_A_COMPRESSION (informational compression)
     - LAYER_G_ENERGY (thermodynamic/energy)
     - LAYER_D_INVARIANTS (geometric invariants)
     - LAYER_K_SIGNAL (control/signal processing)
     - geometric_bind, informational_bind, thermodynamic_bind, physical_bind, control_bind
     - MD_EXTRACT (extracted from other domains)

   ═══════════════════════════════════════════════════════════════════════════════ -/

import Mathlib

namespace DomainAlignment

-- ═══════════════════════════════════════════════════════════════════════════════
-- MOIM DOMAINS — 16 domain registry structure
-- ═══════════════════════════════════════════════════════════════════════════════

inductive MOIMDomain
  | mathematics
  | physics
  | chemistry
  | biology
  | medicine
  | neuroscience
  | psychology
  | anthropology
  | political_science
  | social_systems
  | engineering
  | materials_science
  | computer_science
  | earth_cosmology
  | music_acoustics
  | uncategorized
  deriving Repr, BEq

instance : ToString MOIMDomain where toString
  | .mathematics => "Mathematics"
  | .physics => "Physics"
  | .chemistry => "Chemistry"
  | .biology => "Biology"
  | .medicine => "Medicine"
  | .neuroscience => "Neuroscience"
  | .psychology => "Psychology"
  | .anthropology => "Anthropology"
  | .political_science => "Political Science"
  | .social_systems => "Social Systems"
  | .engineering => "Engineering"
  | .materials_science => "Materials Science"
  | .computer_science => "Computer Science"
  | .earth_cosmology => "Earth / Cosmology"
  | .music_acoustics => "Music / Acoustics"
  | .uncategorized => "Uncategorized"

-- ═══════════════════════════════════════════════════════════════════════════════
-- RESEARCH STACK DOMAINS — Current classification system
-- ═══════════════════════════════════════════════════════════════════════════════

inductive ResearchStackDomain
  | layer_c_topology        -- Geometric topology
  | layer_a_compression     -- Informational compression
  | layer_g_energy          -- Thermodynamic/energy
  | layer_d_invariants      -- Geometric invariants
  | layer_k_signal          -- Control/signal processing
  | geometric_bind
  | informational_bind
  | thermodynamic_bind
  | physical_bind
  | control_bind
  | md_extract              -- Extracted from other domains
  | unknown
  deriving Repr, BEq

instance : ToString ResearchStackDomain where toString
  | .layer_c_topology => "LAYER_C_TOPOLOGY"
  | .layer_a_compression => "LAYER_A_COMPRESSION"
  | .layer_g_energy => "LAYER_G_ENERGY"
  | .layer_d_invariants => "LAYER_D_INVARIANTS"
  | .layer_k_signal => "LAYER_K_SIGNAL"
  | .geometric_bind => "geometric_bind"
  | .informational_bind => "informational_bind"
  | .thermodynamic_bind => "thermodynamic_bind"
  | .physical_bind => "physical_bind"
  | .control_bind => "control_bind"
  | .md_extract => "MD_EXTRACT"
  | .unknown => "unknown"

-- ═══════════════════════════════════════════════════════════════════════════════
-- DOMAIN ALIGNMENT MAPPING — Research Stack → MOIM
-- ═══════════════════════════════════════════════════════════════════════════════

/-- Maps Research Stack domains to MOIM domains based on semantic alignment. -/
def alignDomain (rs_domain : ResearchStackDomain) : MOIMDomain :=
  match rs_domain with
  | .layer_c_topology => .mathematics  -- Topology is mathematical
  | .layer_a_compression => .computer_science  -- Information theory/CS
  | .layer_g_energy => .physics  -- Energy/thermodynamics
  | .layer_d_invariants => .mathematics  -- Geometric invariants
  | .layer_k_signal => .engineering  -- Signal processing/engineering
  | .geometric_bind => .mathematics  -- Geometry
  | .informational_bind => .computer_science  -- Information theory
  | .thermodynamic_bind => .physics  -- Thermodynamics
  | .physical_bind => .physics  -- Physical laws
  | .control_bind => .engineering  -- Control theory
  | .md_extract => .uncategorized  -- Extracted, needs classification
  | .unknown => .uncategorized

-- ═══════════════════════════════════════════════════════════════════════════════
-- REVERSE MAPPING — MOIM → Research Stack (when applicable)
-- ═══════════════════════════════════════════════════════════════════════════════

/-- Maps MOIM domains back to Research Stack domains (many-to-one where needed). -/
def reverseAlignDomain (moim_domain : MOIMDomain) : List ResearchStackDomain :=
  match moim_domain with
  | .mathematics => [.layer_c_topology, .layer_d_invariants, .geometric_bind]
  | .physics => [.layer_g_energy, .thermodynamic_bind, .physical_bind]
  | .computer_science => [.layer_a_compression, .informational_bind]
  | .engineering => [.layer_k_signal, .control_bind]
  | .chemistry => []
  | .biology => []
  | .medicine => []
  | .neuroscience => []
  | .psychology => []
  | .anthropology => []
  | .political_science => []
  | .social_systems => []
  | .materials_science => []
  | .earth_cosmology => []
  | .music_acoustics => []
  | .uncategorized => [.md_extract, .unknown]

-- ═══════════════════════════════════════════════════════════════════════════════
-- DOMAIN COMPATIBILITY CHECK
-- ═══════════════════════════════════════════════════════════════════════════════

/-- Check if two Research Stack domains map to the same MOIM domain (compatible). -/
def domainsCompatible (d1 d2 : ResearchStackDomain) : Bool :=
  alignDomain d1 = alignDomain d2

/-- Check if alignment is bidirectional (exact mapping). -/
def alignmentIsBidirectional (rs_domain : ResearchStackDomain) : Bool :=
  let moim := alignDomain rs_domain
  rs_domain ∈ reverseAlignDomain moim

-- ═══════════════════════════════════════════════════════════════════════════════
-- DOMAIN STATISTICS
-- ═══════════════════════════════════════════════════════════════════════════════

/-- Count how many Research Stack domains map to each MOIM domain. -/
def countMappingsToMOIM (moim_domain : MOIMDomain) : Nat :=
  let all_rs := [
    .layer_c_topology, .layer_a_compression, .layer_g_energy, .layer_d_invariants,
    .layer_k_signal, .geometric_bind, .informational_bind, .thermodynamic_bind,
    .physical_bind, .control_bind, .md_extract, .unknown
  ]
  all_rs.count (λ d => alignDomain d = moim_domain)

/-- Check alignment coverage: how many RS domains have bidirectional mapping. -/
def bidirectionalCoverage : Nat :=
  let all_rs := [
    .layer_c_topology, .layer_a_compression, .layer_g_energy, .layer_d_invariants,
    .layer_k_signal, .geometric_bind, .informational_bind, .thermodynamic_bind,
    .physical_bind, .control_bind, .md_extract, .unknown
  ]
  all_rs.count alignmentIsBidirectional

-- ═══════════════════════════════════════════════════════════════════════════════
-- VERIFICATION EXAMPLES
-- ═══════════════════════════════════════════════════════════════════════════════

#eval alignDomain .layer_c_topology  -- Should be mathematics
#eval alignDomain .layer_g_energy  -- Should be physics
#eval alignDomain .layer_a_compression  -- Should be computer_science

#eval domainsCompatible .layer_c_topology .layer_d_invariants  -- Should be true (both mathematics)
#eval domainsCompatible .layer_g_energy .thermodynamic_bind  -- Should be true (both physics)

#eval countMappingsToMOIM .mathematics  -- Should count topology, invariants, geometric_bind
#eval countMappingsToMOIM .physics  -- Should count energy, thermodynamic, physical

#eval bidirectionalCoverage  -- Should count domains with exact reverse mapping

end DomainAlignment
