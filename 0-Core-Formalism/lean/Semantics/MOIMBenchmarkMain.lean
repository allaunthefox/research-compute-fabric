import Semantics.MOIMBenchmark

def main : IO Unit := do
  IO.println "=== MOIM Integration Benchmark Suite ==="
  IO.println ""
  IO.println "Running benchmarks for Genus3TopologyMetaprobe MOIM integration..."
  IO.println ""
  
  let results := Semantics.MOIMBenchmark.runAllBenchmarks
  let overallUplift := Semantics.MOIMBenchmark.calculateOverallUplift results
  let successful := Semantics.MOIMBenchmark.countSuccessful results
  let total := results.length
  let targetOverall := Semantics.MOIMBenchmark.targetOverallUplift
  let overallSuccess := Semantics.MOIMBenchmark.meetsTarget overallUplift targetOverall
  
  IO.println s!"Benchmark Summary:"
  IO.println s!"  Overall Uplift: {overallUplift}x"
  IO.println s!"  Successful Benchmarks: {successful}/{total}"
  IO.println s!"  Target Overall Uplift: {targetOverall}x (geometric mean of benchmark targets)"
  IO.println s!"  Overall Success: {overallSuccess}"
  IO.println ""
  
  IO.println "=== Detailed Results ==="
  let rec printResult (idx : Nat) (r : Semantics.MOIMBenchmark.BenchmarkResult) : IO Unit := do
    IO.println s!"Benchmark {idx + 1}: {r.testName}"
    IO.println s!"  Baseline Ops:  {r.baselineOps}"
    IO.println s!"  Enhanced Ops:  {r.enhancedOps}"
    IO.println s!"  Uplift Factor: {r.upliftFactor}x"
    IO.println s!"  Target Uplift: {r.targetUplift}x"
    IO.println s!"  Success: {r.success}"
    IO.println ""
  
  let rec printAll (idx : Nat) (rs : List Semantics.MOIMBenchmark.BenchmarkResult) : IO Unit :=
    match rs with
    | [] => pure ()
    | r :: rest => do
      printResult idx r
      printAll (idx + 1) rest
  
  printAll 0 results
  
  IO.println "=== End of Benchmark Report ==="
