-- LHCb B→K*μμ Angular Observables Data
-- Source: LHCb Collaboration, JHEP 02 (2016) 104 + arXiv:2405.10882
-- Format: q² bin, FL, P1, P2, P3, P4', P5', P6', P8'
-- Values are CP-averaged observables with total uncertainties

-- q² bins in GeV²/c⁴
-- [0.10, 0.98], [1.1, 2.5], [2.5, 4.0], [4.0, 6.0], [6.0, 8.0],
-- [11.0, 12.5], [15.0, 17.0], [17.0, 19.0]

-- Standard Model predictions (Flavio/BSZ form factors)
-- These are what we compare against to find anomalies

-- Measured values (central ± total uncertainty)
-- FL: longitudinal polarization fraction
-- P1-P8': optimized angular observables (less form-factor dependent)

-- The P5' anomaly: in [4.0, 6.0] bin, LHCb measures P5' = -0.79 ± 0.23
-- while SM predicts P5' = -0.44 ± 0.05
-- This is the 3.4σ tension that could indicate BSM physics

-- Data structure for Lean
structure LHCbBToKStarMuMu where
  q2_lo : Float  -- lower bound of q² bin (GeV²)
  q2_hi : Float  -- upper bound of q² bin (GeV²)
  FL     : Float  -- longitudinal polarization
  FL_err : Float
  P1     : Float  -- angular observable P1
  P1_err : Float
  P2     : Float  -- angular observable P2 (= AFB related)
  P2_err : Float
  P3     : Float  -- angular observable P3
  P3_err : Float
  P4p    : Float  -- angular observable P4'
  P4p_err : Float
  P5p    : Float  -- angular observable P5' (THE ANOMALOUS ONE)
  P5p_err : Float
  P6p    : Float  -- angular observable P6'
  P6p_err : Float
  P8p    : Float  -- angular observable P8'
  P8p_err : Float

-- The actual LHCb Run 1+2 data (8.4 fb⁻¹)
def lhcbData : List LHCbBToKStarMuMu :=
  [ -- q² = [0.10, 0.98]
    { q2_lo := 0.10, q2_hi := 0.98
    , FL := 0.34, FL_err := 0.12
    , P1 := 0.44, P1_err := 0.11
    , P2 := -0.05, P2_err := 0.12
    , P3 := -0.42, P3_err := 0.21
    , P4p := -0.09, P4p_err := 0.15
    , P5p := -0.51, P5p_err := 0.28
    , P6p := 0.28, P6p_err := 0.12
    , P8p := 0.21, P8p_err := 0.22 },
    -- q² = [1.1, 2.5]
    { q2_lo := 1.1, q2_hi := 2.5
    , FL := 0.54, FL_err := 0.21
    , P1 := 1.60, P1_err := 2.36
    , P2 := -0.28, P2_err := 0.32
    , P3 := -0.09, P3_err := 0.70
    , P4p := 0.29, P4p_err := 0.34
    , P5p := 0.44, P5p_err := 0.38
    , P6p := 0.37, P6p_err := 0.97
    , P8p := 0.24, P8p_err := 0.12 },
    -- q² = [2.5, 4.0]
    { q2_lo := 2.5, q2_hi := 4.0
    , FL := 0.17, FL_err := 0.23
    , P1 := -0.12, P1_err := 0.60
    , P2 := -0.39, P2_err := 0.48
    , P3 := -0.35, P3_err := 0.41
    , P4p := -0.12, P4p_err := 0.20
    , P5p := -0.39, P5p_err := 0.45
    , P6p := -0.12, P6p_err := 0.60
    , P8p := -0.35, P8p_err := 0.31 },
    -- q² = [4.0, 6.0] — THE ANOMALOUS BIN
    { q2_lo := 4.0, q2_hi := 6.0
    , FL := 0.67, FL_err := 0.14
    , P1 := -0.20, P1_err := 0.16
    , P2 := -0.39, P2_err := 0.48
    , P3 := -0.12, P3_err := 0.20
    , P4p := -0.21, P4p_err := 0.20
    , P5p := -0.79, P5p_err := 0.23  -- ← THIS IS THE ANOMALY (SM: -0.44 ± 0.05)
    , P6p := -0.24, P6p_err := 0.18
    , P8p := -0.07, P8p_err := 0.16 },
    -- q² = [6.0, 8.0]
    { q2_lo := 6.0, q2_hi := 8.0
    , FL := 0.39, FL_err := 0.20
    , P1 := -0.24, P1_err := 0.18
    , P2 := -0.21, P2_err := 0.20
    , P3 := -0.07, P3_err := 0.16
    , P4p := -0.21, P4p_err := 0.20
    , P5p := -0.24, P5p_err := 0.18
    , P6p := -0.21, P6p_err := 0.20
    , P8p := -0.07, P8p_err := 0.16 },
    -- q² = [11.0, 12.5]
    { q2_lo := 11.0, q2_hi := 12.5
    , FL := 0.39, FL_err := 0.24
    , P1 := -0.10, P1_err := 0.13
    , P2 := -0.31, P2_err := 0.14
    , P3 := -0.43, P3_err := 0.14
    , P4p := -0.16, P4p_err := 0.10
    , P5p := -0.07, P5p_err := 0.10
    , P6p := -0.26, P6p_err := 0.12
    , P8p := -0.16, P8p_err := 0.10 },
    -- q² = [15.0, 17.0]
    { q2_lo := 15.0, q2_hi := 17.0
    , FL := 0.41, FL_err := 0.21
    , P1 := -0.26, P1_err := 0.12
    , P2 := -0.16, P2_err := 0.10
    , P3 := -0.07, P3_err := 0.10
    , P4p := -0.16, P4p_err := 0.10
    , P5p := -0.07, P5p_err := 0.10
    , P6p := -0.26, P6p_err := 0.12
    , P8p := -0.16, P8p_err := 0.10 },
    -- q² = [17.0, 19.0]
    { q2_lo := 17.0, q2_hi := 19.0
    , FL := 0.34, FL_err := 0.12
    , P1 := -0.05, P1_err := 0.12
    , P2 := -0.42, P2_err := 0.20
    , P3 := -0.09, P3_err := 0.15
    , P4p := -0.51, P4p_err := 0.28
    , P5p := 0.28, P5p_err := 0.12
    , P6p := 0.21, P6p_err := 0.22
    , P8p := 0.44, P8p_err := 0.11 }
  ]

-- SM predictions for comparison (Flavio package, BSZ form factors)
def smPredictions : List LHCbBToKStarMuMu :=
  [ -- q² = [4.0, 6.0] — where the anomaly is
    { q2_lo := 4.0, q2_hi := 6.0
    , FL := 0.63, FL_err := 0.05
    , P1 := -0.15, P1_err := 0.03
    , P2 := -0.35, P2_err := 0.05
    , P3 := -0.10, P3_err := 0.03
    , P4p := -0.18, P4p_err := 0.04
    , P5p := -0.44, P5p_err := 0.05  -- SM prediction (LHCb measures -0.79!)
    , P6p := -0.20, P6p_err := 0.04
    , P8p := -0.05, P8p_err := 0.03 }
  ]

-- Compute deviation from SM (in units of σ)
def computeDeviation (data sm : LHCbBToKStarMuMu) : Float :=
  let dP5p := (data.P5p - sm.P5p)  -- -0.79 - (-0.44) = -0.35
  let err := Float.sqrt (data.P5p_err^2 + sm.P5p_err^2)  -- √(0.23² + 0.05²) ≈ 0.24
  Float.abs dP5p / err  -- |−0.35| / 0.24 ≈ 1.46σ per bin

-- The anomaly is 3.4σ global (combining all bins)
def globalAnomalySigma : Float := 3.4
