import Semantics.BitcoinRGFlow

open Semantics

/-! # BitcoinRGFlow Test File

#eval examples for BitcoinRGFlow functions per AGENTS.md §4.1.
-/

-- #eval: Informational bind
#eval bitcoinInformationalBind { position := 0, price := Q1616.one, sigma_q := ⟨131072⟩, mu_q := ⟨32768⟩ } Q1616.one

-- #eval: Rolling window
#eval rollingWindowQ16 [⟨65536⟩, ⟨98304⟩, ⟨131072⟩] 1 2

-- #eval: Sigma computation
#eval computeSigmaQQ16 [⟨65536⟩, ⟨98304⟩, ⟨131072⟩, ⟨163840⟩] 2 2

-- #eval: Mu computation
#eval computeMuQQ16 [⟨65536⟩, ⟨98304⟩, ⟨131072⟩, ⟨163840⟩] 2 2

-- #eval: RGFlow invariant check
#eval isLawfulRGFlowQ16 ⟨131072⟩ ⟨32768⟩

-- #eval: Full RGFlow analysis
#eval bitcoinRGFlowAnalysisQ16 [⟨65536⟩, ⟨98304⟩, ⟨131072⟩, ⟨163840⟩] 2

-- #eval: Batch RGFlow analysis
#eval batchBitcoinRGFlowQ16 [⟨65536⟩, ⟨98304⟩, ⟨131072⟩, ⟨163840⟩] 2
