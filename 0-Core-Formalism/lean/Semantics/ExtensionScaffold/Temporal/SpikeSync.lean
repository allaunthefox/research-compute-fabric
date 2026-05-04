import Semantics.Temporal.TemporalVariantIndex

namespace Semantics.Temporal.SpikeSync

open Semantics.Temporal.TemporalVariantIndex

/-
  Spike Sync Adapter for TVI Kernel
  ---------------------------------
  Maps neural spike domain into TVI framework.

  Purpose:
  - Demonstrate TVI kernel works for spike trains
  - Define admissibility for spike synchronization
  - Expose failure axes (timing, rate, pattern, collapse)
-/

/-- A single spike event: neuron index and time bin. -/
structure SpikeEvent (nNeurons : Nat) where
  neuron : Fin nNeurons
  time   : Nat
deriving Repr, DecidableEq

/-- A finite spike train over a fixed neuron count. -/
structure SpikeTrain (nNeurons : Nat) where
  events : List (SpikeEvent nNeurons)
deriving Repr

/-- Coarse-graining rule for observation / synchronization. -/
structure CoarseGrain where
  timeBin : Nat        -- bin width in ticks
  maxTimeJitter : Nat  -- tolerated nearest-spike timing mismatch
deriving Repr, DecidableEq

/-- Quantize a time into the chosen bin. -/
def quantizeTime (cg : CoarseGrain) (t : Nat) : Nat :=
  if cg.timeBin = 0 then t else t / cg.timeBin

/-- Coarse-grain a spike event. -/
def coarseEvent {nNeurons : Nat} (cg : CoarseGrain) (e : SpikeEvent nNeurons) :
    SpikeEvent nNeurons :=
  { neuron := e.neuron, time := quantizeTime cg e.time }

/-- Coarse-grain a spike train. -/
def coarseTrain {nNeurons : Nat} (cg : CoarseGrain) (s : SpikeTrain nNeurons) :
    SpikeTrain nNeurons :=
  { events := s.events.map (coarseEvent cg) }

/-- Count spikes in a train. -/
def spikeCount {nNeurons : Nat} (s : SpikeTrain nNeurons) : Nat :=
  s.events.length

/-- Count spikes for a given neuron. -/
def spikeCountFor {nNeurons : Nat} (i : Fin nNeurons) (s : SpikeTrain nNeurons) : Nat :=
  (s.events.filter (fun e => e.neuron = i)).length

/-- Map a spike train to a temporal profile. -/
def trainToProfile {nNeurons : Nat} (cg : CoarseGrain) (s : SpikeTrain nNeurons) : TemporalProfile :=
  let coarseS := coarseTrain cg s
  { eventCount := spikeCount coarseS
    meanGap :=
      if coarseS.events.length ≤ 1 then 0
      else
        let times := coarseS.events.map (·.time)
        let sumDiffs := times.zip (times.drop 1) |>.foldl (fun acc (t₁, t₂) => acc + (t₂ - t₁)) 0
        sumDiffs / (coarseS.events.length - 1)
    patternCount := nNeurons
    collapseBudget :=
      let original := spikeCount s
      let coarse := spikeCount coarseS
      if original > coarse then original - coarse else 0 }

/-- Calculate TVI between two spike trains. -/
def spikeTvi {nNeurons : Nat} (cg : CoarseGrain) (s₁ s₂ : SpikeTrain nNeurons) : TviVector :=
  fromProfiles (trainToProfile cg s₁) (trainToProfile cg s₂)

/-- Dominant error axis for spike sync. -/
def dominantSpikeAxis {nNeurons : Nat} (cg : CoarseGrain) (s₁ s₂ : SpikeTrain nNeurons) : TviAxis :=
  dominantAxis (spikeTvi cg s₁ s₂)

/-- Spike sync admissibility using TVI policy. -/
def spikeSyncAdmissible {nNeurons : Nat} (policy : TviPolicy) (cg : CoarseGrain)
    (s₁ s₂ : SpikeTrain nNeurons) : Prop :=
  admissible policy (spikeTvi cg s₁ s₂)

/-
  Example witnesses
-/

def exampleTrainA : SpikeTrain 2 :=
  { events :=
    [ { neuron := ⟨0, by decide⟩, time := 0 }
    , { neuron := ⟨1, by decide⟩, time := 3 }
    , { neuron := ⟨0, by decide⟩, time := 5 } ] }

def exampleTrainB : SpikeTrain 2 :=
  { events :=
    [ { neuron := ⟨0, by decide⟩, time := 0 }
    , { neuron := ⟨1, by decide⟩, time := 4 }
    , { neuron := ⟨0, by decide⟩, time := 5 } ] }

def exampleCoarse : CoarseGrain :=
  { timeBin := 1, maxTimeJitter := 1 }

def exampleSpikePolicy : TviPolicy :=
  { maxTiming := qOfNat 2
    maxRate := qOfNat 1
    maxPattern := qOfNat 2
    maxCollapse := qOfNat 1
    maxTotal := qOfNat 6 }

-- TVI decomposition for two spike trains
#eval spikeTvi exampleCoarse exampleTrainA exampleTrainB

-- Total TVI cost
#eval total (spikeTvi exampleCoarse exampleTrainA exampleTrainB)

-- Dominant failure axis
#eval dominantSpikeAxis exampleCoarse exampleTrainA exampleTrainB

-- Admissibility check
#eval spikeSyncAdmissible exampleSpikePolicy exampleCoarse exampleTrainA exampleTrainB

/-
  Theorems
-/

/-- A train compared to itself has zero TVI. -/
theorem spikeTvi_self {nNeurons : Nat} (cg : CoarseGrain) (s : SpikeTrain nNeurons) :
    spikeTvi cg s s = zero := by
  simp [spikeTvi, trainToProfile, fromProfiles_self]

end Semantics.Temporal.SpikeSync
