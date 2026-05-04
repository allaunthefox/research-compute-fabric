import Semantics.ExtremeParameterTest

def main : IO Unit := do
  IO.println "[*] Running extreme parameter tests:"
  let _receipt1 := Semantics.testExtremeInformationalBind
  let _receipt2 := Semantics.testExtremeGeometricBind
  let _receipt3 := Semantics.testExtremeThermodynamicBind
  let _receipt4 := Semantics.testExtremePhysicalBind
  let _receipt5 := Semantics.testExtremeControlBind
  let maxVal := Semantics.testMaxQ16_16Boundary
  let minVal := Semantics.testMinQ16_16Boundary
  IO.println s!"[*] Extreme parameter test complete. Q16_16 range: {repr minVal} to {repr maxVal}"
  
  IO.println ""
  IO.println "[*] Running Sigma Protocol Quiz Bank:"
  let results := Semantics.quizBank.map Semantics.runQuiz
  let passedCount := results.filter (fun (r : Semantics.QuizResult) => r.passed) |>.length
  let totalCount := results.length
  let allPassed := passedCount == totalCount

  if allPassed then
    IO.println s!"[*] Quiz bank passed: {passedCount}/{totalCount} questions"
  else
    IO.println s!"[!] Quiz bank FAILED: {passedCount}/{totalCount} questions passed"

  for result in results do
    let status := if result.passed then "[PASS]" else "[FAIL]"
    let receipt := result.receipt
    let observedSigma := receipt.sigma.observedSigma
    let dagNodeCount := receipt.mathDAG.steps.length
    let metacodeSummary := receipt.sigma.metacode.constraint
    let receiptHash := s!"{receipt.routeId}:{repr receipt.decision}:{receipt.inputHash}"
    IO.println ""
    IO.println s!"  {status} {repr result.question.caseType}:"
    IO.println s!"    Expected: {repr result.expectedDecision}"
    IO.println s!"    Actual: {repr result.actualDecision}"
    IO.println s!"    Sigma target: {repr result.question.sigmaTarget}"
    IO.println s!"    Observed sigma: {repr observedSigma}"
    IO.println s!"    DAG nodes: {dagNodeCount}"
    IO.println s!"    Metacode: {metacodeSummary}"
    IO.println s!"    Receipt hash: {receiptHash}"
    IO.println s!"    Reason: {result.question.reason}"

  IO.println ""
  IO.println "[*] Tiered sigma confidence system for statistical deltas:"
  IO.println "  - 3σ = interesting (hypothesis only)"
  IO.println "  - 4σ = internally credible (internal review)"
  IO.println "  - 5σ = public statistical benchmark-delta claim"
  IO.println "  - 6σ = live-voltage / safety-critical gate"
  IO.println ""
  IO.println "[*] Sigma-based routing rules:"
  IO.println "  - 5σ can support a statistical claim"
  IO.println "  - 6σ can support a statistical safety gate"
  IO.println "  - No sigma can replace ethics"
  IO.println "  - If unsure about claim truth: HOLD_REVIEW"
  IO.println "  - If unsure about route safety: REFUSE_OR_CONTAIN"
  IO.println ""
  IO.println "[*] Keeper Law:"
  IO.println "  - The model is real only when it can fail the route correctly"
  IO.println "  - Receipt hash provides auditable trail"
  IO.println "  - Reproducible executable ensures formal verification"
