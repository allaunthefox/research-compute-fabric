import Semantics.VideoPhysics
import Semantics.MereotopologicalSheafHypergraph

namespace Semantics.MereotopologicalVideo

open Semantics.VideoPhysics
open Semantics.MereotopologicalSheafHypergraph

/-- 
  A VideoRegion represents a spatial-temporal segment of the 120Hz HDMI stream.
  It is treated as a component of the larger manifold.
-/
structure VideoRegion where
  id : Nat
  frame_range : Nat × Nat
  pixel_bounds : (Nat × Nat) × (Nat × Nat)
  state : VWMState

/-- 
  VideoSection: Data associated with multiple video regions.
-/
structure VideoSection where
  regions : List VideoRegion
  global_sigma : Scalar

/--
  Mereotopological Video Consistency:
  Ensures that part-whole relations in the video stream match
  the physical connectivity of the manifold topological model.
-/
structure VideoConsistency where
  mereo : Mereology
  topo  : Topology
  isConsistent : Prop

end Semantics.MereotopologicalVideo
