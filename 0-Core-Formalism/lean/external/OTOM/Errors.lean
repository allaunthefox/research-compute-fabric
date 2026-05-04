import Semantics.PhysicsScalar
import Semantics.RegimeCore
import Semantics.BoundaryDynamics
import Semantics.CriticalityDynamics

namespace Semantics.Errors

open Semantics.PhysicsScalar
open Semantics.RegimeCore
open Semantics.BoundaryDynamics
open Semantics.CriticalityDynamics

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
  magnitude : Q16_16
  coherence : Q16_16
  persistence : Q16_16
  regionId : RegionId
  fluidity : Q16_16
  criticalLoad : Q16_16
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
  if Q16_16.gt field.magnitude Q16_16.three then
    if Q16_16.gt field.persistence Q16_16.two then ErrorAttention.emergency else ErrorAttention.directAttention
  else if Q16_16.gt field.persistence Q16_16.one && Q16_16.gt field.coherence Q16_16.half then
    ErrorAttention.scaffold
  else if Q16_16.gt field.magnitude Q16_16.one then
    ErrorAttention.monitor
  else
    ErrorAttention.ignore


def classifyScaffoldingRole (field : ErrorField) : ErrorScaffoldingRole :=
  if Q16_16.gt field.persistence Q16_16.one && Q16_16.gt field.coherence Q16_16.half then
    match field.kind with
    | ErrorKind.dimensionalDrift => ErrorScaffoldingRole.dimensionalScaffold
    | ErrorKind.boundaryLeak => ErrorScaffoldingRole.boundaryScaffold
    | ErrorKind.causalConflict => ErrorScaffoldingRole.causalScaffold
    | ErrorKind.criticalOverflow => ErrorScaffoldingRole.criticalScaffold
    | _ => ErrorScaffoldingRole.none
  else
    ErrorScaffoldingRole.none


def classifyUrgency (field : ErrorField) : ErrorUrgency :=
  if Q16_16.gt field.magnitude Q16_16.three then
    ErrorUrgency.immediate
  else if Q16_16.gt field.magnitude Q16_16.two || Q16_16.gt field.criticalLoad Q16_16.two then
    ErrorUrgency.high
  else if Q16_16.gt field.magnitude Q16_16.one then
    ErrorUrgency.medium
  else
    ErrorUrgency.low


def stableForScaffolding (field : ErrorField) : Bool :=
  Q16_16.gt field.persistence Q16_16.one &&
  Q16_16.gt field.coherence Q16_16.half &&
  Q16_16.le field.magnitude Q16_16.three


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


def dimensionalScaffoldError (regionId : RegionId) : ErrorField :=
  { errorId := 1
  , kind := ErrorKind.dimensionalDrift
  , magnitude := Q16_16.one
  , coherence := Q16_16.three
  , persistence := Q16_16.two
  , regionId := regionId
  , fluidity := Q16_16.half
  , criticalLoad := Q16_16.one }


def directAttentionError (regionId : RegionId) : ErrorField :=
  { errorId := 2
  , kind := ErrorKind.criticalOverflow
  , magnitude := Q16_16.four
  , coherence := Q16_16.quarter
  , persistence := Q16_16.one
  , regionId := regionId
  , fluidity := Q16_16.three
  , criticalLoad := Q16_16.four }



def aliasError (regionId : RegionId) : ErrorField :=
  { errorId := 3
  , kind := ErrorKind.identityAlias
  , magnitude := Q16_16.four
  , coherence := Q16_16.zero
  , persistence := Q16_16.one
  , regionId := regionId
  , fluidity := Q16_16.zero
  , criticalLoad := Q16_16.zero }

end Semantics.Errors
