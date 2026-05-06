/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

SocialCognitiveDynamics.lean — Laws of social brain scaling and information capacity.

This module formalizes the informational laws of social groups and cognitive limits:
1. Social: Dunbar's Number and the neocortex ratio regression.
2. Capacity: Social channel capacity and the quadratic growth of relationships.
3. Scaling: Brain-body metabolic trade-offs and expensive tissue scaling.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.SocialCognition

open Semantics
open Semantics.Q16_16

/-! ## 1. Social Brain (Dunbar) -/

/-- Dunbar's Social Group Law (N).
    log10(N) = 0.093 + 3.389 * log10(CR)
    N: Mean group size, CR: Neocortex ratio.
    Formalizes the cognitive limit on stable social relationships. -/
def dunbarGroupSize (neocortex_ratio : Q16_16) : Q16_16 :=
  -- Returns log10(N)
  -- 0.093 + 3.389 * log10(CR)
  let log_cr := neocortex_ratio -- simplified log
  Q16_16.add (Q16_16.mk 0x000017CE) (Q16_16.mul (Q16_16.mk 0x00036395) log_cr) -- constants in Q16.16

/-- Social Cohesion Time (Grooming).
    G = -0.772 + 0.287 * N
    Models the time investment required for social maintenance. -/
def socialMaintenanceTime (group_size : Q16_16) : Q16_16 :=
  Q16_16.add (Q16_16.ofInt (-1)) (Q16_16.mul (Q16_16.mk 0x00004978) group_size) -- simplified

/-! ## 2. Social Channel Capacity -/

/-- Total Bilateral Relationships (R).
    R = N * (N - 1) / 2
    Models the quadratic explosion of informational links in a group. -/
def bilateralRelationshipCount (n : Nat) : Nat :=
  n * (n - 1) / 2

/-- Social Stability Condition.
    R must be less than the brain's social channel capacity. -/
def isSociallyStable (relationship_count : Nat) (capacity_limit : Nat) : Bool :=
  relationship_count ≤ capacity_limit

/-! ## 3. Metabolic Brain Scaling -/

/-- Brain-Body Curvilinear Scaling.
    log(Brain) = alpha + beta*log(Body) + gamma*(log(Body))^2
    Models the diminishing returns of brain size growth. -/
def brainScalingLog (log_body alpha beta gamma : Q16_16) : Q16_16 :=
  let log_body2 := Q16_16.mul log_body log_body
  Q16_16.add alpha (Q16_16.add (Q16_16.mul beta log_body) (Q16_16.mul gamma log_body2))

end Semantics.Biology.SocialCognition
