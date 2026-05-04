import Semantics.Adaptation
import Lean.Data.Json

namespace Semantics.Ingestion

open Semantics.Swarm
open Lean (Json)

/-- 
  Master Ingestion Mapping:
  Decomposes IA metadata into the 6D Sovereign Genome.
-/
def mapToGenome (j : Json) : Genome :=
  let metadataCount := match j.getObj? with | .ok obj => obj.toArray.size | _ => 0
  let downloads := match j.getObjVal? "downloads" with
    | .ok (.num n) => n.toFloat.toUInt64.toNat
    | _ => 0
  let identSize := match j.getObjVal? "identifier" with
    | .ok (.str s) => s.length
    | _ => 10
  let week_trending := match j.getObjVal? "week" with
    | .ok (.num n) => n.toFloat.toUInt64.toNat
    | _ => 0

  -- 1. mu_bin (Mutation): Inverse completeness
  let mu := (20 - metadataCount).toUInt8 / 2
  
  -- 2. rho_bin (Refresh Rate): Based on trending status
  let rho := if week_trending > 100 then 7 else if week_trending > 10 then 4 else 1

  -- 3. c_bin (Connectance): Path density
  let c := (identSize / 5).toUInt8

  -- 4. m_bin (Modularity): Format diversity
  let m := 3 

  -- 5. ne_bin (Observer Mass): Raw download scale
  let ne := if downloads > 1000 then 7 else if downloads > 100 then 4 else 1

  -- 6. sig_bin (Selection): Hardened significance
  let sig := 4

  { mu_bin  := if mu > 7 then 7 else mu
  , rho_bin := rho.toUInt8
  , c_bin   := if c > 7 then 7 else c
  , m_bin   := m.toUInt8
  , ne_bin  := ne.toUInt8
  , sig_bin := sig.toUInt8 }

def isRecordLawful (j : Json) : Bool :=
  isScaleCoherent (mapToGenome j)

end Semantics.Ingestion
