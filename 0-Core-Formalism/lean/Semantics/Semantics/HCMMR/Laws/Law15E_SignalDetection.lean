/-
Law 15E — Signal Detection Gate.

A sub-law of Field Recovery (Law 15) that gates whether a projected
electromagnetic field contains a detectable signal rather than mere noise.

The gate uses SNR ratio thresholds mapped to typed verdicts:
  Signal ≥ signal_threshold  →  admit  (candidate signal present)
  Signal in ambiguous band   →  hold   (integrate longer)
  Signal ≤ noise_floor       →  reject (noise only)

Pattern matching adds typed classification:
  - narrowband spike: high SNR in tight bin (SETI candidate, artifact)
  - broadband rise: elevated background (thermal, natural, environmental)
  - periodic pulsar: repeating narrowband spikes (rotating source)
  - flicker/transient: short-duration spike (RFI, burst, scintillation)
  - Doppler drift: frequency-shifting narrowband (moving source)

This sits after Law 15C (wave propagation) and before 15D (coupling):
  First detect a signal, then test whether it couples to a source.

Conventions:
  PascalCase types, camelCase functions.
  `structure` for domain concepts, `inductive` for enumerations.
  `def` needs `#eval` witness or `theorem`.
  Q16_16 for all numeric fields.
  Namespace: Semantics.HCMMR.Law15E
  Import: Semantics.HCMMR.Core, Semantics.HCMMR.Kernels.SNRAnomalyDetector, Semantics.FixedPoint
-/

import Semantics.HCMMR.Core
import Semantics.HCMMR.Kernels.SNRAnomalyDetector
import Semantics.FixedPoint

namespace Semantics.HCMMR.Law15E

open Semantics.HCMMR.Core
open Semantics.HCMMR.Kernels.SNRAnomalyDetector
open Semantics.FixedPoint (Q16_16)

-- ═══════════════════════════════════════════════════════════════════
-- §1  Signal Detection Configuration
-- ═══════════════════════════════════════════════════════════════════

/--
Configuration for the signal detection gate.
τ_signal: minimum SNR to claim a detection (e.g., 10x noise floor).
τ_noise: maximum SNR that is clearly noise (e.g., 3x noise floor).
minIntegrationTime: seconds needed before a hold can become admit.
dopplerSearchEnabled: enable frequency-shift pattern matching.
-/
structure SignalDetectionConfig where
  tauSignal          : Q16_16
  tauNoise           : Q16_16
  minIntegrationTime : Q16_16
  dopplerSearchEnabled : Bool
  deriving Repr, BEq, DecidableEq, Inhabited

/--
Default SETI-style configuration: 10σ detection, 3σ noise floor,
60-second minimum integration, Doppler enabled.
-/
def setiDefaultConfig : SignalDetectionConfig :=
  { tauSignal := Q16_16.ofInt 10
  , tauNoise := Q16_16.ofInt 3
  , minIntegrationTime := Q16_16.ofInt 60
  , dopplerSearchEnabled := true
  }

/--
Quick-scan configuration: 5σ detection, shorter integration, no Doppler.
Used for RFI surveys and environment characterization.
-/
def quickScanConfig : SignalDetectionConfig :=
  { tauSignal := Q16_16.ofInt 5
  , tauNoise := Q16_16.ofInt 2
  , minIntegrationTime := Q16_16.ofInt 10
  , dopplerSearchEnabled := false
  }

-- ═══════════════════════════════════════════════════════════════════
-- §2  Signal Detection Gate
-- ═══════════════════════════════════════════════════════════════════

/--
The signal detection gate evaluates a list of SNR bins against the
configured thresholds.

Logic:
  1. Find the strongest SNR bin across the spectrum
  2. Classify SNR zone (signal/noise/ambiguous)
  3. If signal zone: classify pattern, admit narrowband spikes, hold broadband
  4. If ambiguous zone: hold, check if integration time allows upgrade
  5. If noise zone: reject, no signal present

The gate is required in the multiplicative chain — no signal means
no downstream coupling test is meaningful.
-/
def signalDetectionGate (config : SignalDetectionConfig) (bins : List SNRBin) : Gate :=
  let strongest := findStrongestSpike bins
  let snrGate := snrDetectionGate strongest config.tauSignal config.tauNoise
  let sufficientIntegration :=
    Q16_16.le config.minIntegrationTime strongest.integrationTime
  match snrGate.verdict with
  | GateVerdict.admit =>
      { name := snrGate.name
      , required := true
      , score := if sufficientIntegration then Q16_16.one else Q16_16.ofRatio 8 10
      , verdict := if sufficientIntegration then GateVerdict.admit else GateVerdict.hold
      }
  | GateVerdict.hold =>
      if Q16_16.lt strongest.integrationTime config.minIntegrationTime then
        { name := "SignalDetection:integrating"
        , required := true
        , score := Q16_16.ofRatio 3 10
        , verdict := GateVerdict.hold
        }
      else
        snrGate
  | GateVerdict.reject =>
      { name := "SignalDetection:noise"
      , required := true
      , score := Q16_16.zero
      , verdict := GateVerdict.reject
      }

-- ═══════════════════════════════════════════════════════════════════
-- §3  Multi-Pattern Detection Report
-- ═══════════════════════════════════════════════════════════════════

/--
A full detection report: the dominant pattern found, its SNR bin,
the gate verdict, and per-bin diagnostic receipts for all anomalies.
-/
structure DetectionReport where
  dominantBin    : SNRBin
  dominantPattern : SignalPattern
  gateVerdict    : GateVerdict
  detectionCount : Nat
  receipts       : List DiagnosticReceipt
  deriving Repr, BEq, Inhabited

/--
Generate a full detection report from a config and bin list.
Scans all bins, identifies the dominant pattern, emits receipts for
every bin that exceeds the noise threshold.
-/
def generateDetectionReport (config : SignalDetectionConfig) (bins : List SNRBin) (ts : Nat) : DetectionReport :=
  let strongest := findStrongestSpike bins
  let pattern := classifyPattern bins config.tauSignal
  let gate := signalDetectionGate config bins
  let receipts := bins.filterMap fun b =>
    if Q16_16.le config.tauSignal b.snrValue then
      some (emitAnomalyReceipt b (classifyPattern [b] config.tauSignal) ts)
    else
      none
  { dominantBin := strongest
  , dominantPattern := pattern
  , gateVerdict := gate.verdict
  , detectionCount := countDetections bins config.tauSignal
  , receipts := receipts
  }

-- ═══════════════════════════════════════════════════════════════════
-- §4  Doppler Drift Detection
-- ═══════════════════════════════════════════════════════════════════

/--
Detect Doppler drift: compare narrowband spike positions across time
windows. If the peak frequency shifts, report drift rate as Q16_16.
driftRate = (f1 - f0) / (t1 - t0), positive = approaching, negative = receding.
-/
def detectDopplerDrift (f0 f1 t0 t1 : Q16_16) : Q16_16 :=
  let dt := Q16_16.sub t1 t0
  if dt.val == 0 then Q16_16.zero
  else Q16_16.div (Q16_16.sub f1 f0) dt

/--
Doppler detection gate: admits if a narrowband spike shows frequency drift
consistent with a moving source (non-zero, bounded rate).
-/
def dopplerGate (f0 f1 t0 t1 : Q16_16) (maxPhysicallyPlausibleDrift : Q16_16) : Gate :=
  let drift := detectDopplerDrift f0 f1 t0 t1
  let absDrift := Q16_16.abs drift
  if absDrift.val == 0 then
    { name := "DopplerDetection:stationary"
    , required := false  -- optional sub-gate
    , score := Q16_16.ofRatio 5 10
    , verdict := GateVerdict.hold
    }
  else if Q16_16.le absDrift maxPhysicallyPlausibleDrift then
    { name := "DopplerDetection:drift_detected"
    , required := false
    , score := Q16_16.ofRatio 8 10
    , verdict := GateVerdict.admit
    }
  else
    { name := "DopplerDetection:implausible_drift"
    , required := false
    , score := Q16_16.zero
    , verdict := GateVerdict.reject
    }

-- ═══════════════════════════════════════════════════════════════════
-- §5  Fixtures
-- ═══════════════════════════════════════════════════════════════════

def cleanSignalFixture : List SNRBin :=
  [ { frequencyHz := Q16_16.ofInt 1420
    , bandwidthHz := Q16_16.ofInt 1
    , signalPower := Q16_16.ofInt 1000
    , noiseFloor := Q16_16.one
    , snrValue := Q16_16.ofInt 1000
    , integrationTime := Q16_16.ofInt 120
    }
  ]

def ambiguousSignalFixture : List SNRBin :=
  [ { frequencyHz := Q16_16.ofInt 1662
    , bandwidthHz := Q16_16.ofInt 5
    , signalPower := Q16_16.ofInt 20
    , noiseFloor := Q16_16.ofInt 5
    , snrValue := Q16_16.ofInt 4
    , integrationTime := Q16_16.ofInt 30
    }
  ]

-- ═══════════════════════════════════════════════════════════════════
-- §6  Theorems
-- ═══════════════════════════════════════════════════════════════════

theorem seti_config_admits_strong_signal :
    (signalDetectionGate setiDefaultConfig cleanSignalFixture).verdict = GateVerdict.admit := by
  native_decide

theorem seti_config_holds_ambiguous :
    (signalDetectionGate setiDefaultConfig ambiguousSignalFixture).verdict = GateVerdict.hold := by
  native_decide

theorem quick_scan_admits_ambiguous_above_noise :
    (signalDetectionGate quickScanConfig ambiguousSignalFixture).verdict = GateVerdict.hold := by
  native_decide

theorem doppler_zero_drift_holds :
    (dopplerGate (Q16_16.ofInt 1420) (Q16_16.ofInt 1420) Q16_16.zero (Q16_16.ofInt 60) (Q16_16.ofInt 10)).verdict
    = GateVerdict.hold := by
  native_decide

theorem doppler_valid_drift_admits :
    (dopplerGate (Q16_16.ofInt 1420) (Q16_16.ofInt 1421) Q16_16.zero (Q16_16.ofInt 60) (Q16_16.ofInt 10)).verdict
    = GateVerdict.admit := by
  native_decide

theorem detection_report_counts_correctly :
    (generateDetectionReport setiDefaultConfig cleanSignalFixture 0).detectionCount = 1 := by
  native_decide

-- ═══════════════════════════════════════════════════════════════════
-- §7  #eval Witnesses
-- ═══════════════════════════════════════════════════════════════════

#eval signalDetectionGate setiDefaultConfig cleanSignalFixture
#eval signalDetectionGate setiDefaultConfig ambiguousSignalFixture
#eval signalDetectionGate quickScanConfig ambiguousSignalFixture

#eval generateDetectionReport setiDefaultConfig cleanSignalFixture 0
#eval generateDetectionReport setiDefaultConfig ambiguousSignalFixture 1

#eval detectDopplerDrift (Q16_16.ofInt 1420) (Q16_16.ofInt 1421)
  Q16_16.zero (Q16_16.ofInt 60)

#eval dopplerGate (Q16_16.ofInt 1420) (Q16_16.ofInt 1421)
  Q16_16.zero (Q16_16.ofInt 60) (Q16_16.ofInt 10)

#eval dopplerGate (Q16_16.ofInt 1420) (Q16_16.ofInt 1500)
  Q16_16.zero (Q16_16.ofInt 60) (Q16_16.ofInt 10)

end Semantics.HCMMR.Law15E
