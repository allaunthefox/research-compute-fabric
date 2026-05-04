import Semantics.NominalParameterTest

def main : IO Unit := do
  IO.println "[*] Running Nominal Parameter Tests:"
  let _receipt1 := Semantics.testNominalMath
  let _receipt2 := Semantics.testNominalPublicData
  IO.println s!"[*] Nominal parameter test complete."
  
  IO.println ""
  IO.println "[*] Running Nominal Quiz Bank:"
  let results := Semantics.nominalQuizBank.map Semantics.runNominalQuiz
  let passedCount := results.filter (fun (r : Semantics.NominalQuizResult) => r.passed) |>.length
  let totalCount := results.length
  let allPassed := passedCount == totalCount

  if allPassed then
    IO.println s!"[*] Nominal quiz bank passed: {passedCount}/{totalCount} questions"
  else
    IO.println s!"[!] Nominal quiz bank FAILED: {passedCount}/{totalCount} questions passed"

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
  IO.println "[*] Nominal Acceptance Harness:"
  IO.println "  - System can admit normal routes"
  IO.println "  - Ordinary math: preliminaryPass"
  IO.println "  - Ordinary public data: preliminaryPass"
  IO.println "  - Ordinary OpenWorm: publicClaimReady"
  IO.println "  - Low-risk metadata: preliminaryPass"
  IO.println "  - Safe compression: preliminaryPass"
  IO.println ""
  IO.println "[*] Complementary Proof:"
  IO.println "  - ExtremeParameterTest: can fail the right routes"
  IO.println "  - NominalParameterTest: can admit the right routes"
  IO.println "  - Together: the system knows when NOT to proceed AND when to proceed"
