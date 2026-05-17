import Semantics.HCMMR.Core
import Semantics.FixedPoint

namespace Semantics.HCMMR.Kernels.SNRAnomalyDetector

open Semantics.HCMMR.Core
open Semantics.FixedPoint (Q16_16)

inductive SignalPattern where
  | narrowbandSpike
  | broadbandRise
  | dopplerDrift
  | flickerTransient
  | periodicPulsar
  | unknownAnomaly
  deriving Repr, BEq, DecidableEq, Inhabited

instance : ToString SignalPattern where
  toString
    | SignalPattern.narrowbandSpike => "narrowbandSpike"
    | SignalPattern.broadbandRise   => "broadbandRise"
    | SignalPattern.dopplerDrift    => "dopplerDrift"
    | SignalPattern.flickerTransient => "flickerTransient"
    | SignalPattern.periodicPulsar  => "periodicPulsar"
    | SignalPattern.unknownAnomaly  => "unknownAnomaly"

inductive SNRZone where
  | signalZone
  | noiseZone
  | ambiguousZone
  deriving Repr, BEq, DecidableEq, Inhabited

structure SNRBin where
  frequencyHz : Q16_16
  bandwidthHz : Q16_16
  signalPower : Q16_16
  noiseFloor  : Q16_16
  snrValue    : Q16_16
  integrationTime : Q16_16
  deriving Repr, BEq, DecidableEq, Inhabited

def computeSNR (signal noise : Q16_16) : Q16_16 :=
  if noise.val == 0 then Q16_16.zero
  else Q16_16.div signal noise

def classifySNRZone (snr tauSignal tauNoise : Q16_16) : SNRZone :=
  if Q16_16.le tauSignal snr then SNRZone.signalZone
  else if Q16_16.le snr tauNoise then SNRZone.noiseZone
  else SNRZone.ambiguousZone

def isNarrowband (bin : SNRBin) : Bool :=
  let frac := Q16_16.div bin.bandwidthHz bin.frequencyHz
  Q16_16.lt frac (Q16_16.ofRatio 1 100)

def isBroadband (bin : SNRBin) : Bool :=
  let frac := Q16_16.div bin.bandwidthHz bin.frequencyHz
  Q16_16.lt (Q16_16.ofRatio 10 100) frac

def classifyPattern (bins : List SNRBin) (tauSignal : Q16_16) : SignalPattern :=
  let narrowSpikes := bins.filter fun b =>
    Q16_16.le tauSignal b.snrValue && isNarrowband b
  let broadRises := bins.filter fun b =>
    Q16_16.le tauSignal b.snrValue && isBroadband b
  if narrowSpikes.length > 0 then
    if narrowSpikes.length == 1 then SignalPattern.narrowbandSpike
    else SignalPattern.periodicPulsar
  else if broadRises.length > 0 then
    SignalPattern.broadbandRise
  else if bins.any fun b => Q16_16.le tauSignal b.snrValue then
    SignalPattern.unknownAnomaly
  else
    SignalPattern.flickerTransient

def anomalyScore (bin : SNRBin) (baselineSNR : Q16_16) : Q16_16 :=
  let delta := Q16_16.abs (Q16_16.sub bin.snrValue baselineSNR)
  if delta.val == 0 then Q16_16.zero
  else Q16_16.log2 (Q16_16.add Q16_16.one delta)

def narrowbandSpikeFixture : SNRBin :=
  { frequencyHz := (Q16_16.ofInt 1420)
  , bandwidthHz := (Q16_16.ofInt 1)
  , signalPower := (Q16_16.ofInt 100)
  , noiseFloor := Q16_16.one
  , snrValue := (Q16_16.ofInt 100)
  , integrationTime := (Q16_16.ofInt 60)
  }

def broadbandRiseFixture : SNRBin :=
  { frequencyHz := (Q16_16.ofInt 1500)
  , bandwidthHz := (Q16_16.ofInt 500)
  , signalPower := (Q16_16.ofInt 50)
  , noiseFloor := (Q16_16.ofInt 5)
  , snrValue := (Q16_16.ofInt 10)
  , integrationTime := (Q16_16.ofInt 30)
  }

def noiseFloorFixture : SNRBin :=
  { frequencyHz := (Q16_16.ofInt 1000)
  , bandwidthHz := (Q16_16.ofInt 10)
  , signalPower := Q16_16.one
  , noiseFloor := (Q16_16.ofInt 10)
  , snrValue := Q16_16.ofRatio 1 10
  , integrationTime := (Q16_16.ofInt 10)
  }

def multiBinFixture : List SNRBin :=
  [ narrowbandSpikeFixture, broadbandRiseFixture, noiseFloorFixture ]

def snrDetectionGate (bin : SNRBin) (tauSignal tauNoise : Q16_16) : Gate :=
  let zone := classifySNRZone bin.snrValue tauSignal tauNoise
  match zone with
  | SNRZone.signalZone =>
      if isNarrowband bin then
        { name := "SNRDetection:narrowbandSpike"
        , required := true
        , score := Q16_16.one
        , verdict := GateVerdict.admit
        }
      else
        { name := "SNRDetection:broadbandRise"
        , required := true
        , score := Q16_16.ofRatio 5 10
        , verdict := GateVerdict.hold
        }
  | SNRZone.ambiguousZone =>
      { name := "SNRDetection:ambiguous"
      , required := true
      , score := Q16_16.ofRatio 3 10
      , verdict := GateVerdict.hold
      }
  | SNRZone.noiseZone =>
      { name := "SNRDetection:noise"
      , required := true
      , score := Q16_16.zero
      , verdict := GateVerdict.reject
      }

def emitAnomalyReceipt (bin : SNRBin) (pattern : SignalPattern) (ts : Nat) : DiagnosticReceipt :=
  let route := match pattern with
    | SignalPattern.narrowbandSpike => "reobserve_drift_correct"
    | SignalPattern.broadbandRise   => "thermal_environmental_check"
    | SignalPattern.dopplerDrift    => "doppler_compensation"
    | SignalPattern.flickerTransient => "rfi_exclusion"
    | SignalPattern.periodicPulsar  => "periodicity_followup"
    | SignalPattern.unknownAnomaly  => "Underverse"
  { object := "freq_bin"
  , failedGate := "SNRDetection:anomaly"
  , alternateRoute := route
  , timestamp := ts
  , residual :=
      { domain := "snr_anomaly"
      , value := anomalyScore bin Q16_16.one
      , source := "SNRAnomalyDetector"
      }
  }

def findStrongestSpike (bins : List SNRBin) : SNRBin :=
  bins.foldl (fun best b =>
    if Q16_16.lt best.snrValue b.snrValue then b else best)
    { frequencyHz := Q16_16.zero, bandwidthHz := Q16_16.one
    , signalPower := Q16_16.zero, noiseFloor := Q16_16.one
    , snrValue := Q16_16.zero, integrationTime := Q16_16.one
    }

def countDetections (bins : List SNRBin) (tauSignal : Q16_16) : Nat :=
  (bins.filter fun b => Q16_16.le tauSignal b.snrValue).length

theorem narrowband_spike_admits :
    (snrDetectionGate narrowbandSpikeFixture (Q16_16.ofInt 10) Q16_16.one).verdict = GateVerdict.admit := by
  native_decide

theorem noise_floor_rejects :
    (snrDetectionGate noiseFloorFixture (Q16_16.ofInt 10) Q16_16.one).verdict = GateVerdict.reject := by
  native_decide

theorem broadband_rise_holds :
    (snrDetectionGate broadbandRiseFixture (Q16_16.ofInt 5) Q16_16.one).verdict = GateVerdict.hold := by
  native_decide

theorem narrowband_is_narrowband :
    isNarrowband narrowbandSpikeFixture = true := by
  native_decide

theorem anomaly_score_self_delta :
    anomalyScore narrowbandSpikeFixture narrowbandSpikeFixture.snrValue = Q16_16.zero := by
  native_decide

theorem detection_count_multi_bin :
    countDetections multiBinFixture (Q16_16.ofInt 5) = 2 := by
  native_decide

#eval computeSNR (Q16_16.ofInt 200) (Q16_16.ofInt 20)
#eval computeSNR (Q16_16.ofInt 5) Q16_16.zero

#eval classifySNRZone narrowbandSpikeFixture.snrValue (Q16_16.ofInt 10) Q16_16.one
#eval classifySNRZone broadbandRiseFixture.snrValue (Q16_16.ofInt 20) (Q16_16.ofInt 5)
#eval classifySNRZone noiseFloorFixture.snrValue (Q16_16.ofInt 10) Q16_16.one

#eval isNarrowband narrowbandSpikeFixture
#eval isBroadband broadbandRiseFixture

#eval classifyPattern [narrowbandSpikeFixture] (Q16_16.ofInt 10)
#eval classifyPattern [broadbandRiseFixture] (Q16_16.ofInt 5)
#eval classifyPattern multiBinFixture (Q16_16.ofInt 10)

#eval anomalyScore narrowbandSpikeFixture Q16_16.one
#eval anomalyScore noiseFloorFixture Q16_16.one

#eval snrDetectionGate narrowbandSpikeFixture (Q16_16.ofInt 10) Q16_16.one
#eval snrDetectionGate broadbandRiseFixture (Q16_16.ofInt 5) (Q16_16.ofInt 5)
#eval snrDetectionGate noiseFloorFixture (Q16_16.ofInt 10) Q16_16.one

#eval emitAnomalyReceipt narrowbandSpikeFixture SignalPattern.narrowbandSpike 42

#eval findStrongestSpike multiBinFixture
#eval countDetections multiBinFixture (Q16_16.ofInt 5)

end Semantics.HCMMR.Kernels.SNRAnomalyDetector
