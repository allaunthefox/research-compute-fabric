import Semantics.CanonicalInterval
import Semantics.LocalDerivative
import Semantics.LocalExpansion
import Semantics.MetricCore
import Semantics.ComputationProfile
import Semantics.SurfaceCore
import Semantics.RaycastField
import Semantics.DomainState
import Semantics.HyperFlow

namespace Semantics.EquationTranslation

open Semantics.CanonicalInterval
open Semantics.LocalDerivative
open Semantics.LocalExpansion
open Semantics.MetricCore
open Semantics.ComputationProfile
open Semantics.SurfaceCore
open Semantics.RaycastField
open Semantics.DomainState
open Semantics.HyperFlow

abbrev Scalar := Float

inductive EquationFamily
| diat
| dNat
| bracketedDiat
| spectral
| qubo
| canal
| channel
| mimo
| observedChannel
| plasma
| plasmaManifold
deriving Repr, DecidableEq

structure TranslationResult where
  canonicalInterval : CanonicalInterval
  localDerivative : LocalDerivative
  localExpansion : LocalExpansion
  metric : Metric
  surface : Surface
  domainState : DomainState
deriving Repr

def mkTranslationResult
  (canonicalInterval : CanonicalInterval)
  (localDerivative : LocalDerivative)
  (metric : Metric)
  (surface : Surface) : TranslationResult :=
  { canonicalInterval := canonicalInterval
  , localDerivative := localDerivative
  , localExpansion := fromLocalDerivative canonicalInterval.width localDerivative
  , metric := metric
  , surface := surface
  , domainState := resolveMetricOrReject canonicalInterval (some metric) (some surface) localDerivative }

def translateDiat
  (position width : Scalar)
  (substrateProfile : SubstrateProfile) : TranslationResult :=
  let interval := mkCanonicalInterval position width
  let derivative := zeroDerivative 2
  let metric := mkMetric .nLocal .inferred 1.0 width 0.0
  let surface : Surface :=
    { canonicalInterval := interval
    , metric := metric
    , substrateProfile := substrateProfile
    , localDerivative := derivative }
  mkTranslationResult interval derivative metric surface

def translateDNat
  (position width growth : Scalar)
  (substrateProfile : SubstrateProfile) : TranslationResult :=
  let interval := mkCanonicalInterval position width
  let derivative := mkLocalDerivative [[growth, 0.0], [0.0, width]] [[0.0, 0.0], [0.0, growth]]
  let metric := inferMetric derivative
  let surface : Surface :=
    { canonicalInterval := interval
    , metric := metric
    , substrateProfile := substrateProfile
    , localDerivative := derivative }
  mkTranslationResult interval derivative metric surface

def translateSpectral
  (eigenvalues : List Scalar)
  (substrateProfile : SubstrateProfile) : TranslationResult :=
  let derivative := mkLocalDerivative (zeroMatrix eigenvalues.length) (List.range eigenvalues.length |>.map (fun i =>
    List.range eigenvalues.length |>.map (fun j => if i = j then matrixEntryOrZero [eigenvalues] 0 i else 0.0)))
  let metric := inferMetric derivative
  let interval := mkCanonicalInterval 0.5 (meanOrZero (eigenvalues.map Float.abs))
  let surface : Surface :=
    { canonicalInterval := interval
    , metric := metric
    , substrateProfile := substrateProfile
    , localDerivative := derivative }
  mkTranslationResult interval derivative metric surface

def translateQubo
  (quadraticWeights : List (List Scalar))
  (linearWeights : List Scalar)
  (substrateProfile : SubstrateProfile) : TranslationResult :=
  let derivative := mkLocalDerivative [linearWeights] quadraticWeights
  let metric := mkMetric .nLocal .qubo (meanOrZero (linearWeights.map Float.abs)) (matrixFrobeniusNorm quadraticWeights) 0.0
  let interval := mkCanonicalInterval 0.5 (metric.weightWidth)
  let surface : Surface :=
    { canonicalInterval := interval
    , metric := metric
    , substrateProfile := substrateProfile
    , localDerivative := derivative }
  mkTranslationResult interval derivative metric surface

def translateCanal
  (flow gradient curvatureValue : Scalar)
  (substrateProfile : SubstrateProfile) : TranslationResult :=
  let derivative := mkLocalDerivative [[flow, gradient], [-gradient, flow]] [[curvatureValue, 0.0], [0.0, curvatureValue]]
  let metric := inferMetric derivative
  let interval := mkCanonicalInterval flow (Float.abs gradient + Float.abs curvatureValue)
  let surface : Surface :=
    { canonicalInterval := interval
    , metric := metric
    , substrateProfile := substrateProfile
    , localDerivative := derivative }
  mkTranslationResult interval derivative metric surface

def translateChannelMatrix
  (matrix : ChannelMatrix)
  (substrateProfile : SubstrateProfile) : TranslationResult :=
  let derivative := inferLocalDerivative matrix
  let metric := inferMetric derivative
  let interval := inferCanonicalInterval matrix
  let surface := inferSurface matrix substrateProfile
  mkTranslationResult interval derivative metric surface

def translateMimoChannel
  (channel : MultiPathChannel)
  (time : Scalar)
  (substrateProfile : SubstrateProfile) : TranslationResult :=
  let matrix := foldMultiPathChannel channel time
  let derivative := inferLocalDerivativeFromMultiPath channel time
  let metric := inferMetric derivative
  let interval := inferCanonicalInterval matrix
  let surface := inferSurfaceFromMultiPath channel time substrateProfile
  mkTranslationResult interval derivative metric surface


def fluidGasOrPlasmaRegime
  (matrix : ChannelMatrix)
  (substrateProfile : SubstrateProfile)
  (field : ChannelField := exampleChannelField)
  (time : Scalar := 0.0) : MediumRegime :=
  let derivative := inferLocalDerivative matrix
  let metric := inferMetric derivative
  let state := mkHyperFlowState derivative metric field time
  state.mediumRegime

def fluidGasOrPlasmaRegimeFromMultiPath
  (channel : MultiPathChannel)
  (time : Scalar)
  (substrateProfile : SubstrateProfile)
  (field : ChannelField := exampleChannelField) : MediumRegime :=
  let derivative := inferLocalDerivativeFromMultiPath channel time
  let metric := inferMetric derivative
  let state := mkHyperFlowState derivative metric field time
  state.mediumRegime

def plasmaRegimeFromChannelField
  (field : ChannelField)
  (time : Scalar)
  (metric : Metric := exampleMetric) : MediumRegime :=
  let derivative := inferLocalDerivativeFromMultiPath (field.channelAt time) time
  plasmaRegime derivative metric field time


def plasmaManifoldRegimeFromChannelField
  (field : ChannelField)
  (time : Scalar)
  (metric : Metric := exampleMetric) : PlasmaManifoldRegime :=
  let derivative := inferLocalDerivativeFromMultiPath (field.channelAt time) time
  plasmaManifoldRegime derivative metric field time

def translateObservedChannel
  (sources targets : List ObservedPoint)
  (correlation : SpatialCorrelation)
  (time : Scalar)
  (substrateProfile : SubstrateProfile) : TranslationResult :=
  let channel := constructObservedMultiPathChannel sources targets correlation
  translateMimoChannel channel time substrateProfile

end Semantics.EquationTranslation
