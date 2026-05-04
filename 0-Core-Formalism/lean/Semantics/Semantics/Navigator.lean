import Semantics.FixedPoint
import Semantics.UnifiedSchema

namespace Semantics.Navigator

open Semantics.UnifiedSchema

def selectModel (models : List ModelNode) (threshold : UInt32) : Option ModelNode :=
  let adequate := models.filter (fun m => m.fitScore >= threshold)
  adequate.foldl (fun acc m =>
    match acc with
    | none => some m
    | some best => if m.complexity < best.complexity then some m else some best) none

def canReachSwerve (models : List ModelNode) : Bool :=
  models.any (fun m => m.modelId == "patamathematical_swerve")

#eval selectModel [{modelId := "a", complexity := 10, fitScore := 0x00010000, reachability := "high"}] 0x00008000

end Semantics.Navigator
