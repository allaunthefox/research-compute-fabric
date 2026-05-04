import Semantics.PhysicsScalar
import Semantics.RegimeCore
import Semantics.OrderedFieldTokens

namespace Semantics.Errors

-- Explicitly use hardware-native scalar type throughout
open Semantics.PhysicsScalar
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
  if PhysicsScalar.Q16_16.gt field.magnitude PhysicsScalar.Q16_16.three then
    if PhysicsScalar.Q16_16.gt field.persistence PhysicsScalar.Q16_16.two then ErrorAttention.emergency else ErrorAttention.directAttention
  else if PhysicsScalar.Q16_16.gt field.persistence PhysicsScalar.Q16_16.one && PhysicsScalar.Q16_16.gt field.coherence PhysicsScalar.Q16_16.half then
    ErrorAttention.scaffold
  else if PhysicsScalar.Q16_16.gt field.magnitude PhysicsScalar.Q16_16.one then
    ErrorAttention.monitor
  else
    ErrorAttention.ignore

def classifyScaffoldingRole (field : ErrorField) : ErrorScaffoldingRole :=
  if PhysicsScalar.Q16_16.gt field.persistence PhysicsScalar.Q16_16.one && PhysicsScalar.Q16_16.gt field.coherence PhysicsScalar.Q16_16.half then
    match field.kind with
    | ErrorKind.dimensionalDrift => ErrorScaffoldingRole.dimensionalScaffold
    | ErrorKind.boundaryLeak => ErrorScaffoldingRole.boundaryScaffold
    | ErrorKind.causalConflict => ErrorScaffoldingRole.causalScaffold
    | ErrorKind.criticalOverflow => ErrorScaffoldingRole.criticalScaffold
    | _ => ErrorScaffoldingRole.none
  else
    ErrorScaffoldingRole.none

def classifyUrgency (field : ErrorField) : ErrorUrgency :=
  if PhysicsScalar.Q16_16.gt field.magnitude PhysicsScalar.Q16_16.three then
    ErrorUrgency.immediate
  else if PhysicsScalar.Q16_16.gt field.magnitude PhysicsScalar.Q16_16.two || PhysicsScalar.Q16_16.gt field.criticalLoad PhysicsScalar.Q16_16.two then
    ErrorUrgency.high
  else if PhysicsScalar.Q16_16.gt field.magnitude PhysicsScalar.Q16_16.one then
    ErrorUrgency.medium
  else
    ErrorUrgency.low

def stableForScaffolding (field : ErrorField) : Bool :=
  PhysicsScalar.Q16_16.gt field.persistence PhysicsScalar.Q16_16.one &&
  PhysicsScalar.Q16_16.gt field.coherence PhysicsScalar.Q16_16.half &&
  PhysicsScalar.Q16_16.le field.magnitude PhysicsScalar.Q16_16.three

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
  , magnitude := PhysicsScalar.Q16_16.one
  , coherence := PhysicsScalar.Q16_16.three
  , persistence := PhysicsScalar.Q16_16.two
  , regionId := regionId
  , fluidity := PhysicsScalar.Q16_16.half
  , criticalLoad := PhysicsScalar.Q16_16.one }

def directAttentionError (regionId : Semantics.RegimeCore.RegionId) : ErrorField :=
  { errorId := 2
  , kind := ErrorKind.criticalOverflow
  , magnitude := PhysicsScalar.Q16_16.four
  , coherence := PhysicsScalar.Q16_16.quarter
  , persistence := PhysicsScalar.Q16_16.one
  , regionId := regionId
  , fluidity := PhysicsScalar.Q16_16.three
  , criticalLoad := PhysicsScalar.Q16_16.four }

def aliasError (regionId : Semantics.RegimeCore.RegionId) : ErrorField :=
  { errorId := 3
  , kind := ErrorKind.identityAlias
  , magnitude := PhysicsScalar.Q16_16.four
  , coherence := PhysicsScalar.Q16_16.zero
  , persistence := PhysicsScalar.Q16_16.one
  , regionId := regionId
  , fluidity := PhysicsScalar.Q16_16.zero
  , criticalLoad := PhysicsScalar.Q16_16.zero }

end Semantics.Errors
