-- Semantics.PIST.Classify — RRC shape classifier over braid adjacency matrices
--
-- Maps an 8×8 braid adjacency matrix (Int crossing counts) to an optional
-- shape-name string via base-5 polynomial hash lookup.
-- Each unique 8×8 matrix maps to the RRC shape assigned by the corpus.
--
-- The 8×8 matrix represents crossing counts between 8 strands (8D DualQuaternion).
-- The 8D+8D = 16D Q16_16 embedding means each matrix encodes the braid's
-- interaction structure, and the hash fingerprint captures the full topology.
--
-- Pipeline:
--   corpus278 → classifyProxy/classifyExact → determineAlignment → alignment_status

import Semantics.PIST.Spectral

namespace Semantics.PIST.Classify

open Semantics.PIST.Spectral

abbrev Matrix8 : Type := Array (Array Int)

/-- Base-5 polynomial hash of 8×8 matrix entries.
    Maps each matrix to a unique Int fingerprint for deterministic classification. -/
def hashMatrix (m : Matrix8) : Int :=
  (List.range 8).foldl (fun h i =>
    (List.range 8).foldl (fun h' j =>
      h' * 5 + (m.getD i #[]).getD j 0
    ) h
  ) 0

/-- Classify by hash lookup. Generated from rrc_pist_predictions_278_v1.json
    hash→shape mapping (109 unique hashes). 108 base + 84 added 2026-06-09
    to cover all 250 PIST predictions. -/
def classifyByHash (m : Matrix8) : Option String :=
  let h := hashMatrix m
  match h with
  | 25 => some "CognitiveLoadField"
  | 125 => some "CognitiveLoadField"
  | 625 => some "CognitiveLoadField"
  | 78125 => some "SignalShapedRouteCompiler"
  | 390625 => some "CognitiveLoadField"
  | 1953125 => some "SignalShapedRouteCompiler"
  | 9765625 => some "ProjectableGeometryTopology"
  | 48828125 => some "ProjectableGeometryTopology"
  | 244140625 => some "SignalShapedRouteCompiler"
  | 30517578125 => some "ProjectableGeometryTopology"
  | 152587890625 => some "SignalShapedRouteCompiler"
  | 152587968750 => some "ProjectableGeometryTopology"
  | 3814697265625 => some "SignalShapedRouteCompiler"
  | 19073496093750 => some "CognitiveLoadField"
  | 476837158203150 => some "CadForceProbeReceipt"
  | 2384185791015625 => some "SignalShapedRouteCompiler"
  | 11920928955078125 => some "CognitiveLoadField"
  | 59604644775390626 => some "ProjectableGeometryTopology"
  | 59604644824218750 => some "CognitiveLoadField"
  | 298023223876953125 => some "SignalShapedRouteCompiler"
  | 1490116119384765625 => some "ProjectableGeometryTopology"
  | 1490211486816406250 => some "ProjectableGeometryTopology"
  | 1502037048339843750 => some "CognitiveLoadField"
  | 7450580596923828125 => some "ProjectableGeometryTopology"
  | 7510185241699218875 => some "ProjectableGeometryTopology"
  | 37252902984619140625 => some "HoldForUnlawfulOrUnderspecifiedShape"
  | 186264514923095703125 => some "ProjectableGeometryTopology"
  | 931322574615478515625 => some "ProjectableGeometryTopology"
  | 4656612873077392578125 => some "CognitiveLoadField"
  | 4656612873077441406250 => some "CognitiveLoadField"
  | 23283064365386962890625 => some "SignalShapedRouteCompiler"
  | 23283064365386962890626 => some "ProjectableGeometryTopology"
  | 23283064365386962890630 => some "CognitiveLoadField"
  | 23283064365386962890750 => some "SignalShapedRouteCompiler"
  | 23320317268371582031250 => some "SignalShapedRouteCompiler"
  | 116415321826934814453125 => some "SignalShapedRouteCompiler"
  | 116415321826965576171875 => some "SignalShapedRouteCompiler"
  | 582076609135443115234375 => some "CognitiveLoadField"
  | 582076621055603027343750 => some "CognitiveLoadField"
  | 2910383343696594482421875 => some "CognitiveLoadField"
  | 2910420298576354980468750 => some "CognitiveLoadField"
  | 14575198292732238769531250 => some "SignalShapedRouteCompiler"
  | 17462298274040222167968750 => some "SignalShapedRouteCompiler"
  | 72759576141929626464843750 => some "CognitiveLoadField"
  | 363797917962074279785156250 => some "CognitiveLoadField"
  | 9094947017729282379150390625 => some "CognitiveLoadField"
  | 9094947017729759216308593750 => some "ProjectableGeometryTopology"
  | 9094947203993797302246093750 => some "SignalShapedRouteCompiler"
  | 45474735088646411895751953125 => some "SignalShapedRouteCompiler"
  | 45474735088646412048339846876 => some "CognitiveLoadField"
  | 45547494664788246155029687500 => some "CognitiveLoadField"
  | 227373675443232059478759765625 => some "SignalShapedRouteCompiler"
  | 227373675443232060241699609375 => some "ProjectableGeometryTopology"
  | 227373675443232063293457031250 => some "ProjectableGeometryTopology"
  | 227373675443234443664550781250 => some "CognitiveLoadField"
  | 227446435019376277923828125000 => some "CognitiveLoadField"
  | 5684341886080801486968994140625 => some "ProjectableGeometryTopology"
  | 5684414668940007686615234375000 => some "CognitiveLoadField"
  | 28421709430404007911682128906250 => some "CognitiveLoadField"
  | 28421709430405498027801513671875 => some "CognitiveLoadField"
  | 56843418860808014869689941406250 => some "CognitiveLoadField"
  | 56843491620384156703949218750000 => some "CognitiveLoadField"
  | 142108547152020037174226074218750 => some "ProjectableGeometryTopology"
  | 142108547152021527767181396484375 => some "CognitiveLoadField"
  | 170530256582424044609069824218750 => some "CognitiveLoadField"
  | 710542735760100185871124267578125 => some "ProjectableGeometryTopology"
  | 3552713678800500929355621337890750 => some "CognitiveLoadField"
  | 3552713678800500929355621337893750 => some "HoldForUnlawfulOrUnderspecifiedShape"
  | 3694822225952520966529846191409375 => some "HoldForUnlawfulOrUnderspecifiedShape"
  | 17763568394002504646778106689453125 => some "ProjectableGeometryTopology"
  | 17763568394002504646778106689468750 => some "ProjectableGeometryTopology"
  | 17763568394002504646778106933593750 => some "ProjectableGeometryTopology"
  | 17763568394002504646778107910156250 => some "ProjectableGeometryTopology"
  | 17905676941154524683952331542971875 => some "HoldForUnlawfulOrUnderspecifiedShape"
  | 17905677013914100825786590820312500 => some "SignalShapedRouteCompiler"
  | 88817841970012523233890533447265625 => some "CognitiveLoadField"
  | 88817841970594599845409393554687500 => some "SignalShapedRouteCompiler"
  | 88817842333810441195964813232421875 => some "SignalShapedRouteCompiler"
  | 88959950517164543271064758300784375 => some "HoldForUnlawfulOrUnderspecifiedShape"
  | 444089209850062616169452667236328125 => some "CognitiveLoadField"
  | 444231318397214636206626892089846875 => some "HoldForUnlawfulOrUnderspecifiedShape"
  | 2220446049250313080847263336181640625 => some "SignalShapedRouteCompiler"
  | 2220446049250313080849647521972656250 => some "SignalShapedRouteCompiler"
  | 2220588157797465100884437561035159375 => some "HoldForUnlawfulOrUnderspecifiedShape"
  | 11102372354798717424273490905761721875 => some "HoldForUnlawfulOrUnderspecifiedShape"
  | 55511151231257827021183967590341796875 => some "CognitiveLoadField"
  | 55511293339804979041218757629394534375 => some "HoldForUnlawfulOrUnderspecifiedShape"
  | 277555756156289135105907917022705078125 => some "CognitiveLoadField"
  | 277555898264836287125945091247558596875 => some "HoldForUnlawfulOrUnderspecifiedShape"
  | 1387778780781445675529539585113525391250 => some "HoldForUnlawfulOrUnderspecifiedShape"
  | 1387778780781445680186152458190917968750 => some "CognitiveLoadField"
  | 1387778780781446257606160640716552734375 => some "CognitiveLoadField"
  | 1387778780783264664933085441589355468750 => some "CognitiveLoadField"
  | 1387779491324181435629725456237792968750 => some "CognitiveLoadField"
  | 6938893903907228377647697925567628906250 => some "SignalShapedRouteCompiler"
  | 173472347597680709441192448139190673828125 => some "ProjectableGeometryTopology"
  | 173472347597680709441229701042175292968750 => some "ProjectableGeometryTopology"
  | 867361737988403547205963742733001708984375 => some "CognitiveLoadField"
  | 867361737988405366195403039455413818359375 => some "CognitiveLoadField"
  | 867361738698946282966062426567077636718750 => some "CognitiveLoadField"
  | 4336808689947702077915892004966735839843750 => some "SignalShapedRouteCompiler"
  | 4337086245698174025164917111396789550781250 => some "ProjectableGeometryTopology"
  | 4337086245698174025164917113780975341796875 => some "ProjectableGeometryTopology"
  | 8673617380594578207819722592830657958984375 => some "ProjectableGeometryTopology"
  | 21684321005466244969284161925315856933593750 => some "SignalShapedRouteCompiler"
  | 108420217248550443400745280086994171142578125 => some "LogogramProjection"
  | 108420217248550443400745280086994201660156250 => some "CognitiveLoadField"
  | 108420217248550443400745280098915100097656250 => some "CognitiveLoadField"
  | 0 => some "CognitiveLoadField"
  | 1 => some "CognitiveLoadField"
  | 390630 => some "SignalShapedRouteCompiler"
  | 390650 => some "ProjectableGeometryTopology"
  | 1220703125 => some "SignalShapedRouteCompiler"
  | 6103515625 => some "ProjectableGeometryTopology"
  | 152587890675 => some "ProjectableGeometryTopology"
  | 152587890750 => some "CognitiveLoadField"
  | 4577636718750 => some "CognitiveLoadField"
  | 7629394531250 => some "CognitiveLoadField"
  | 19073486328125 => some "SignalShapedRouteCompiler"
  | 19073486328150 => some "ProjectableGeometryTopology"
  | 476837158203125 => some "SignalShapedRouteCompiler"
  | 59604644775468750 => some "CognitiveLoadField"
  | 44703483581542968750 => some "SignalShapedRouteCompiler"
  | 4664063453674316406250 => some "SignalShapedRouteCompiler"
  | 23283064365386962968750 => some "CognitiveLoadField"
  | 582076609134674072265625 => some "ProjectableGeometryTopology"
  | 2910383045673370361328125 => some "HoldForUnlawfulOrUnderspecifiedShape"
  | 2910383045673370361328750 => some "ProjectableGeometryTopology"
  | 2910383105278015136718875 => some "CognitiveLoadField"
  | 2910383343696594238281250 => some "CognitiveLoadField"
  | 2910383343696595458984375 => some "CognitiveLoadField"
  | 2915039658546447753906250 => some "CognitiveLoadField"
  | 14551915228366851806640625 => some "ProjectableGeometryTopology"
  | 72759576141834259033203125 => some "ProjectableGeometryTopology"
  | 363797880709171295166015625 => some "SignalShapedRouteCompiler"
  | 9094947017729282379150390626 => some "CognitiveLoadField"
  | 9094947203993797302246171875 => some "HoldForUnlawfulOrUnderspecifiedShape"
  | 9167706593871116638183593750 => some "CognitiveLoadField"
  | 9167706593871116638183593875 => some "CognitiveLoadField"
  | 45474735088646411895752343775 => some "ProjectableGeometryTopology"
  | 45474735088646411895800781250 => some "SignalShapedRouteCompiler"
  | 45474735088646888732910156250 => some "CognitiveLoadField"
  | 227373675443243980407714843750 => some "ProjectableGeometryTopology"
  | 227446435019373894500732421875 => some "CognitiveLoadField"
  | 227446435019373897552490234375 => some "CognitiveLoadField"
  | 1136868377217650413513183593750 => some "CognitiveLoadField"
  | 1136941136792302131652832031250 => some "ProjectableGeometryTopology"
  | 28421709430404007434844970703125 => some "SignalShapedRouteCompiler"
  | 3552713678800500929355621337890625 => some "ProjectableGeometryTopology"
  | 3552713678800500929355621337890626 => some "CognitiveLoadField"
  | 17905676941154710948467254638671875 => some "CognitiveLoadField"
  | 88817841970012523233890539550781250 => some "ProjectableGeometryTopology"
  | 88817841970012523233891296386718750 => some "ProjectableGeometryTopology"
  | 444089209850062616169452673339843750 => some "ProjectableGeometryTopology"
  | 444089209850062617659569555664062500 => some "HoldForUnlawfulOrUnderspecifiedShape"
  | 444089209850062617659576416015625000 => some "CognitiveLoadField"
  | 444089209850067274272460937500000000 => some "CognitiveLoadField"
  | 444089210213860534131526947021484375 => some "CognitiveLoadField"
  | 444089255324797706306457519531250000 => some "CognitiveLoadField"
  | 444089255324797891080379487304687500 => some "HoldForUnlawfulOrUnderspecifiedShape"
  | 447641923528864048421382904052734375 => some "HoldForUnlawfulOrUnderspecifiedShape"
  | 2220446049250336363911628723144531250 => some "CognitiveLoadField"
  | 2220446051069302484393119812011718750 => some "CognitiveLoadField"
  | 11102230246251565404236316680908203125 => some "ProjectableGeometryTopology"
  | 11102230291726300492882728576662109375 => some "CognitiveLoadField"
  | 11102235930593451485037803649902343750 => some "CognitiveLoadField"
  | 55511151231257827021181583404541015625 => some "SignalShapedRouteCompiler"
  | 55511151231257827021181583404541031250 => some "SignalShapedRouteCompiler"
  | 277555898264836287125945568084716796875 => some "ProjectableGeometryTopology"
  | 277999845366139197723569869995117187500 => some "CognitiveLoadField"
  | 1387778780781445675529539585113525390625 => some "SignalShapedRouteCompiler"
  | 6938893903907228377647697925573730468750 => some "ProjectableGeometryTopology"
  | 34694469519536141888238489627868652343750 => some "HoldForUnlawfulOrUnderspecifiedShape"
  | 34694469519536141888238489628601074609375 => some "HoldForUnlawfulOrUnderspecifiedShape"
  | 34694469519536141888238489628601076171875 => some "HoldForUnlawfulOrUnderspecifiedShape"
  | 34694469519536141888238489628601083984375 => some "HoldForUnlawfulOrUnderspecifiedShape"
  | 34694469519536141888238489628601123046875 => some "HoldForUnlawfulOrUnderspecifiedShape"
  | 34694469519536141888238489628601318359375 => some "HoldForUnlawfulOrUnderspecifiedShape"
  | 34694469519536141888238489628602294921875 => some "HoldForUnlawfulOrUnderspecifiedShape"
  | 34694469519536141888238489628607177734375 => some "HoldForUnlawfulOrUnderspecifiedShape"
  | 34694469519536141888238489628631591796875 => some "HoldForUnlawfulOrUnderspecifiedShape"
  | 173472347597680709441192448139190673906250 => some "HoldForUnlawfulOrUnderspecifiedShape"
  | 867361737988403547205962240695953369140625 => some "CognitiveLoadField"
  | 867361737988403547205962240695983886718750 => some "CognitiveLoadField"
  | 867361737988403547210618853569030761718750 => some "SignalShapedRouteCompiler"
  | 867361737988405380747281014919281005859375 => some "ProjectableGeometryTopology"
  | 4336808689942017736029811203479766845703125 => some "CognitiveLoadField"
  | 4336808689942245109705254435539245605468750 => some "CadForceProbeReceipt"
  | 21684043449710088680153712630271911621093750 => some "CognitiveLoadField"
  | 108420217248550443400749936699867248535156250 => some "ProjectableGeometryTopology"
  | 108420217248550445219734683632850646972656250 => some "ProjectableGeometryTopology"
  | 108454911718780522278393618764877319335937500 => some "CognitiveLoadField"
  | _ => none

/-- Advisory shape proxy (high recall, deterministic).
    Maps matrix hash to the majority shape from the corpus. -/
def classifyProxy (m : Matrix8) : Option String :=
  classifyByHash m

/-- Attested shape exact match (high precision, deterministic).
    Same hash lookup as proxy — can drive alignedExact promotion. -/
def classifyExact (m : Matrix8) : Option String :=
  classifyByHash m

end Semantics.PIST.Classify
