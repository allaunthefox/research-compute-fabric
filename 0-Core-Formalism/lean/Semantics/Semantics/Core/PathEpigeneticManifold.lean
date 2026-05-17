/-
PathEpigeneticManifold.lean — 1D regulatory path over a 16D manifold

This module models the "circuit path as epigenetic control strand" idea:
the 1D path is stable carrier geometry, while finite regulatory marks on that
path determine which dimensions of a 16D manifold are expressed, damped,
receipted, or routed to quarantine.

The claim boundary is intentionally narrow. This is not a biological
equivalence, fabrication rule, or compression claim. It is a receipt-bearing
state update law.
-/

import Semantics.FixedPoint

namespace Semantics.PathEpigeneticManifold

open Semantics.FixedPoint

/-- The 16 addressable dimensions of the manifold packet. -/
inductive Dim16 where
  | identity
  | route
  | scale
  | phase
  | torsion
  | curvature
  | energy
  | velocity
  | residual
  | semanticMass
  | confidence
  | density
  | topology
  | witness
  | underverse
  | time
  deriving Repr, BEq, DecidableEq

/-- Finite regulatory mark actions carried by a 1D path site. -/
inductive MarkerAction where
  | activate
  | damp
  | gateWitness
  | quarantine
  deriving Repr, BEq, DecidableEq

/-- Terminal decision for a path-regulated manifold update. -/
inductive PathDecision where
  | admit
  | hold
  | quarantine
  deriving Repr, BEq, DecidableEq

/-- One regulatory marker attached to a path site. -/
structure RegulatoryMarker where
  target : Dim16
  action : MarkerAction
  strength : Q0_16
  receiptPresent : Bool
  deriving Repr, BEq, DecidableEq

/-- One 1D carrier-site. `layoutClear` is the circuit/route design-rule gate. -/
structure PathSite where
  siteId : UInt16
  marker : RegulatoryMarker
  layoutClear : Bool
  deriving Repr, BEq, DecidableEq

/-- The 16D manifold state. All fields use Q0.16 because they are normalized
dimensionless expression levels in this first receipt surface. -/
structure Manifold16 where
  identity : Q0_16
  route : Q0_16
  scale : Q0_16
  phase : Q0_16
  torsion : Q0_16
  curvature : Q0_16
  energy : Q0_16
  velocity : Q0_16
  residual : Q0_16
  semanticMass : Q0_16
  confidence : Q0_16
  density : Q0_16
  topology : Q0_16
  witness : Q0_16
  underverse : Q0_16
  time : Q0_16
  deriving Repr, BEq, DecidableEq

namespace Manifold16

def zero : Manifold16 :=
  { identity := Q0_16.zero
  , route := Q0_16.zero
  , scale := Q0_16.zero
  , phase := Q0_16.zero
  , torsion := Q0_16.zero
  , curvature := Q0_16.zero
  , energy := Q0_16.zero
  , velocity := Q0_16.zero
  , residual := Q0_16.zero
  , semanticMass := Q0_16.zero
  , confidence := Q0_16.zero
  , density := Q0_16.zero
  , topology := Q0_16.zero
  , witness := Q0_16.zero
  , underverse := Q0_16.zero
  , time := Q0_16.zero }

def get (s : Manifold16) : Dim16 → Q0_16
  | Dim16.identity => s.identity
  | Dim16.route => s.route
  | Dim16.scale => s.scale
  | Dim16.phase => s.phase
  | Dim16.torsion => s.torsion
  | Dim16.curvature => s.curvature
  | Dim16.energy => s.energy
  | Dim16.velocity => s.velocity
  | Dim16.residual => s.residual
  | Dim16.semanticMass => s.semanticMass
  | Dim16.confidence => s.confidence
  | Dim16.density => s.density
  | Dim16.topology => s.topology
  | Dim16.witness => s.witness
  | Dim16.underverse => s.underverse
  | Dim16.time => s.time

def set (s : Manifold16) (d : Dim16) (v : Q0_16) : Manifold16 :=
  match d with
  | Dim16.identity => { s with identity := v }
  | Dim16.route => { s with route := v }
  | Dim16.scale => { s with scale := v }
  | Dim16.phase => { s with phase := v }
  | Dim16.torsion => { s with torsion := v }
  | Dim16.curvature => { s with curvature := v }
  | Dim16.energy => { s with energy := v }
  | Dim16.velocity => { s with velocity := v }
  | Dim16.residual => { s with residual := v }
  | Dim16.semanticMass => { s with semanticMass := v }
  | Dim16.confidence => { s with confidence := v }
  | Dim16.density => { s with density := v }
  | Dim16.topology => { s with topology := v }
  | Dim16.witness => { s with witness := v }
  | Dim16.underverse => { s with underverse := v }
  | Dim16.time => { s with time := v }

end Manifold16

/-- A regulatory marker is admissible only if its local layout and receipt close. -/
def markerAdmissible (site : PathSite) : Bool :=
  site.layoutClear && site.marker.receiptPresent

/-- Apply one marker. Missing receipt leaves the manifold unchanged; the decision
gate records HOLD separately. Layout failure routes to quarantine. -/
def applyMarker (s : Manifold16) (site : PathSite) : Manifold16 :=
  if !site.layoutClear then
    (s.set Dim16.underverse site.marker.strength).set Dim16.residual site.marker.strength
  else if !site.marker.receiptPresent then
    s
  else
    match site.marker.action with
    | MarkerAction.activate =>
        s.set site.marker.target site.marker.strength
    | MarkerAction.damp =>
        s.set site.marker.target Q0_16.zero
    | MarkerAction.gateWitness =>
        s.set Dim16.witness Q0_16.one
    | MarkerAction.quarantine =>
        (s.set Dim16.underverse site.marker.strength).set Dim16.residual site.marker.strength

/-- Fold a 1D path over the 16D manifold. -/
def applyPath (s : Manifold16) (path : List PathSite) : Manifold16 :=
  path.foldl applyMarker s

def anyLayoutViolation : List PathSite → Bool
  | [] => false
  | site :: rest => (!site.layoutClear) || anyLayoutViolation rest

def anyMissingReceipt : List PathSite → Bool
  | [] => false
  | site :: rest => (site.layoutClear && !site.marker.receiptPresent) || anyMissingReceipt rest

def anyQuarantineMarker : List PathSite → Bool
  | [] => false
  | site :: rest => (site.marker.action == MarkerAction.quarantine && site.marker.receiptPresent) || anyQuarantineMarker rest

/-- Path-level decision: physical/layout violation or explicit quarantine wins;
otherwise missing receipts HOLD; fully receipted paths ADMIT. -/
def decidePath (path : List PathSite) : PathDecision :=
  if anyLayoutViolation path || anyQuarantineMarker path then .quarantine
  else if anyMissingReceipt path then .hold
  else .admit

/-- One completed path-regulated update receipt. -/
structure PathReceipt where
  before : Manifold16
  after : Manifold16
  siteCount : Nat
  decision : PathDecision
  deriving Repr, BEq, DecidableEq

def runPath (s : Manifold16) (path : List PathSite) : PathReceipt :=
  { before := s
  , after := applyPath s path
  , siteCount := path.length
  , decision := decidePath path }

def qSmall : Q0_16 := ⟨1⟩
def qMedium : Q0_16 := ⟨0x0100⟩

def torsionSite : PathSite :=
  { siteId := 0
  , marker :=
      { target := Dim16.torsion
      , action := MarkerAction.activate
      , strength := qMedium
      , receiptPresent := true }
  , layoutClear := true }

def dampResidualSite : PathSite :=
  { siteId := 1
  , marker :=
      { target := Dim16.residual
      , action := MarkerAction.damp
      , strength := qSmall
      , receiptPresent := true }
  , layoutClear := true }

def witnessSite : PathSite :=
  { siteId := 2
  , marker :=
      { target := Dim16.witness
      , action := MarkerAction.gateWitness
      , strength := Q0_16.one
      , receiptPresent := true }
  , layoutClear := true }

def missingReceiptSite : PathSite :=
  { torsionSite with marker := { torsionSite.marker with receiptPresent := false } }

def layoutViolationSite : PathSite :=
  { torsionSite with layoutClear := false }

def admittedPath : List PathSite := [torsionSite, witnessSite]
def holdPath : List PathSite := [missingReceiptSite]
def quarantinePath : List PathSite := [layoutViolationSite]

theorem admittedPathActivatesTorsion :
    (runPath Manifold16.zero admittedPath).after.torsion = qMedium := by
  native_decide

theorem admittedPathClosesWitness :
    (runPath Manifold16.zero admittedPath).after.witness = Q0_16.one := by
  native_decide

theorem admittedPathDecision :
    (runPath Manifold16.zero admittedPath).decision = .admit := by
  native_decide

theorem holdPathLeavesTorsionUnchanged :
    (runPath Manifold16.zero holdPath).after.torsion = Q0_16.zero := by
  native_decide

theorem holdPathDecision :
    (runPath Manifold16.zero holdPath).decision = .hold := by
  native_decide

theorem quarantinePathRoutesResidual :
    (runPath Manifold16.zero quarantinePath).after.residual = qMedium := by
  native_decide

theorem quarantinePathDecision :
    (runPath Manifold16.zero quarantinePath).decision = .quarantine := by
  native_decide

#eval (runPath Manifold16.zero admittedPath).decision
#eval (runPath Manifold16.zero admittedPath).after.torsion
#eval (runPath Manifold16.zero holdPath).decision
#eval (runPath Manifold16.zero quarantinePath).after.underverse

end Semantics.PathEpigeneticManifold
