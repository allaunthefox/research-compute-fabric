import Semantics.FixedPoint
import Semantics.RegimeCore
import Semantics.OrderedFieldTokens
import Semantics.PhysicsScalarBridge

namespace Semantics.Errors

-- Explicitly use hardware-native scalar type throughout
open Semantics.FixedPoint
open Semantics.RegimeCore
open Semantics.OrderedFieldTokens

abbrev ErrorId := UInt16

inductive ErrorKind
| sensorNoise
| carrierMismatch
| boundaryLeak
| temporalSkew
| causalConflict
| dimensionalDrift
| criticalOverflow
| regimeMismatch
| unresolvedTransition
| identityAlias
  deriving Repr, DecidableEq

inductive ErrorAttention
| ignore
| monitor
| scaffold
| directAttention
| emergency
  deriving Repr, DecidableEq

inductive ErrorScaffoldingRole
| none
| dimensionalScaffold
| boundaryScaffold
| causalScaffold
| criticalScaffold
  deriving Repr, DecidableEq

inductive ErrorUrgency
| low
| medium
| high
| immediate
  deriving Repr, DecidableEq

structure ErrorField where
  errorId : ErrorId
  kind : ErrorKind
  magnitude : PhysicsScalar.Q16_16
  coherence : PhysicsScalar.Q16_16
  persistence : PhysicsScalar.Q16_16
  regionId : Semantics.RegimeCore.RegionId
  fluidity : PhysicsScalar.Q16_16
  criticalLoad : PhysicsScalar.Q16_16
  deriving Repr, DecidableEq

structure ErrorClassification where
  attention : ErrorAttention
  scaffoldingRole : ErrorScaffoldingRole
  urgency : ErrorUrgency
  stableForReuse : Bool
  deriving Repr, DecidableEq

structure ErrorResponse where
  field : ErrorField
  classification : ErrorClassification
  requiresImmediateAction : Bool
  deriving Repr, DecidableEq

def classifyErrorAttention (field : ErrorField) : ErrorAttention :=
  if Semantics.PhysicsScalarBridge.gt field.magnitude Semantics.PhysicsScalarBridge.three then
    if Semantics.PhysicsScalarBridge.gt field.persistence Semantics.PhysicsScalarBridge.two then ErrorAttention.emergency else ErrorAttention.directAttention
  else if Semantics.PhysicsScalarBridge.gt field.persistence Semantics.PhysicsScalarBridge.one && Semantics.PhysicsScalarBridge.gt field.coherence Semantics.PhysicsScalarBridge.half then
    ErrorAttention.scaffold
  else if Semantics.PhysicsScalarBridge.gt field.magnitude Semantics.PhysicsScalarBridge.one then
    ErrorAttention.monitor
  else
    ErrorAttention.ignore

def classifyScaffoldingRole (field : ErrorField) : ErrorScaffoldingRole :=
  if Semantics.PhysicsScalarBridge.gt field.persistence Semantics.PhysicsScalarBridge.one && Semantics.PhysicsScalarBridge.gt field.coherence Semantics.PhysicsScalarBridge.half then
    match field.kind with
    | ErrorKind.dimensionalDrift => ErrorScaffoldingRole.dimensionalScaffold
    | ErrorKind.boundaryLeak => ErrorScaffoldingRole.boundaryScaffold
    | ErrorKind.causalConflict => ErrorScaffoldingRole.causalScaffold
    | ErrorKind.criticalOverflow => ErrorScaffoldingRole.criticalScaffold
    | _ => ErrorScaffoldingRole.none
  else
    ErrorScaffoldingRole.none

def classifyUrgency (field : ErrorField) : ErrorUrgency :=
  if Semantics.PhysicsScalarBridge.gt field.magnitude Semantics.PhysicsScalarBridge.three then
    ErrorUrgency.immediate
  else if Semantics.PhysicsScalarBridge.gt field.magnitude Semantics.PhysicsScalarBridge.two || Semantics.PhysicsScalarBridge.gt field.criticalLoad Semantics.PhysicsScalarBridge.two then
    ErrorUrgency.high
  else if Semantics.PhysicsScalarBridge.gt field.magnitude Semantics.PhysicsScalarBridge.one then
    ErrorUrgency.medium
  else
    ErrorUrgency.low

def stableForScaffolding (field : ErrorField) : Bool :=
  Semantics.PhysicsScalarBridge.gt field.persistence Semantics.PhysicsScalarBridge.one &&
  Semantics.PhysicsScalarBridge.gt field.coherence Semantics.PhysicsScalarBridge.half &&
  Semantics.PhysicsScalarBridge.le field.magnitude Semantics.PhysicsScalarBridge.three

def classifyErrorField (field : ErrorField) : ErrorClassification :=
  { attention := classifyErrorAttention field
  , scaffoldingRole := classifyScaffoldingRole field
  , urgency := classifyUrgency field
  , stableForReuse := stableForScaffolding field }

def requiresImmediateAction (field : ErrorField) : Bool :=
  match classifyErrorAttention field with
  | ErrorAttention.directAttention => true
  | ErrorAttention.emergency => true
  | _ => false

def respondToError (field : ErrorField) : ErrorResponse :=
  { field := field
  , classification := classifyErrorField field
  , requiresImmediateAction := requiresImmediateAction field }

def dimensionalScaffoldError (regionId : Semantics.RegimeCore.RegionId) : ErrorField :=
  { errorId := 1
  , kind := ErrorKind.dimensionalDrift
  , magnitude := Semantics.PhysicsScalarBridge.one
  , coherence := Semantics.PhysicsScalarBridge.three
  , persistence := Semantics.PhysicsScalarBridge.two
  , regionId := regionId
  , fluidity := Semantics.PhysicsScalarBridge.half
  , criticalLoad := Semantics.PhysicsScalarBridge.one }

def directAttentionError (regionId : Semantics.RegimeCore.RegionId) : ErrorField :=
  { errorId := 2
  , kind := ErrorKind.criticalOverflow
  , magnitude := Semantics.PhysicsScalarBridge.four
  , coherence := Semantics.PhysicsScalarBridge.quarter
  , persistence := Semantics.PhysicsScalarBridge.one
  , regionId := regionId
  , fluidity := Semantics.PhysicsScalarBridge.three
  , criticalLoad := Semantics.PhysicsScalarBridge.four }

def aliasError (regionId : Semantics.RegimeCore.RegionId) : ErrorField :=
  { errorId := 3
  , kind := ErrorKind.identityAlias
  , magnitude := Semantics.PhysicsScalarBridge.four
  , coherence := Semantics.PhysicsScalarBridge.zero
  , persistence := Semantics.PhysicsScalarBridge.one
  , regionId := regionId
  , fluidity := Semantics.PhysicsScalarBridge.zero
  , criticalLoad := Semantics.PhysicsScalarBridge.zero }

end Semantics.Errors
